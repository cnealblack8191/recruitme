import copy
import tempfile
import unittest
from pathlib import Path
from recruitme.search_policy import apply_search_policy
from recruitme.budget import Ledger, StopRun
from recruitme.routing import ProviderRouter
from recruitme.plugins import ApolloPeople
from test_foundation import configuration


class SearchPolicy(unittest.TestCase):
    def test_brave_monthly_cap_counts_unknown_requests_across_runs(self):
        import time
        from recruitme.governors import BudgetLimitReached
        with tempfile.TemporaryDirectory() as folder:
            cfg=configuration()
            cfg['providers']['brave']=copy.deepcopy(cfg['providers']['fake'])
            p=cfg['providers']['brave']
            p.update(enabled=True,approved=True,poc_limit_usd='100',run_limit_usd='10',
                     operations={'fill':'4.995','next':'0.005'},poc_query_limit=2000,run_query_limit=2000)
            cfg['paid_enabled']=True
            ledger=Ledger(Path(folder)/'monthly.db',cfg)
            try:
                ledger.create_run('first','10')
                op=ledger.reserve('first','brave','fill','first')
                ledger.reconcile(op,None)
                ledger.create_run('second','10')
                ledger.reserve('second','brave','next','second')
                with self.assertRaises(BudgetLimitReached):
                    ledger.reserve('second','brave','next','third')
                self.assertEqual(ledger.total(provider='brave'),5000000)
                ledger.db.execute('UPDATE operations SET timestamp=? WHERE id=?',(time.time()-32*86400,op))
                ledger.create_run('second','10',resume=True)
                ledger.reserve('second','brave','next','after-expiry')
            finally:ledger.db.close()

    def setUp(self):
        self.cfg = configuration()
        template = self.cfg['providers'].pop('fake')
        for name, cost in [('exa_free','0'),('brave','0.005'),('tavily','0.008')]:
            self.cfg['providers'][name] = {**copy.deepcopy(template), 'operations':{'search':cost}}
        self.profile = {'runCap':0.02,'durationMinutes':2,'searchProviders':[
            {'id':'tavily','budget':0.02},{'id':'exa_free','budget':0},{'id':'brave','budget':0.01}]}

    def test_allocations_never_change_account_config(self):
        original = copy.deepcopy(self.cfg)
        cfg = apply_search_policy(self.cfg,self.profile)
        self.assertEqual(self.cfg,original)
        self.assertEqual(cfg['provider_priority']['free_discovery'],['exa_free'])
        self.assertEqual(cfg['provider_priority']['low_cost_paid_discovery'],['brave','tavily'])
        self.assertEqual(cfg['providers']['brave']['run_limit_usd'],'0.01')
        self.assertEqual(cfg['max_run_seconds'],120)

    def test_zero_budget_allows_free_but_never_paid(self):
        self.profile['runCap']=0
        cfg=apply_search_policy(self.cfg,self.profile)
        with tempfile.TemporaryDirectory() as root:
            ledger=Ledger(Path(root)/'db',cfg)
            try:
                ledger.create_run('free',0)
                op=ledger.reserve('free','exa_free','search','one')
                ledger.dispatch('free',op)
                ledger.reconcile(op,0)
                self.assertEqual(ledger.total(),0)
                with self.assertRaises(StopRun):ledger.reserve('free','brave','search','two')
            finally:ledger.db.close()

    def test_exhausted_provider_falls_through_without_exceeding_search_cap(self):
        cfg=apply_search_policy(self.cfg,self.profile)
        cfg['providers']['exa_free']['run_query_limit']=0
        class Fake:
            def __init__(self,ledger,run_id,guard):self.ledger=ledger;self.run=run_id
            def initialize(self):pass
            def tools(self):pass
            def search(self,q,count):
                op=self.ledger.reserve(self.run,self.name,'search',q)
                self.ledger.dispatch(self.run,op)
                self.ledger.reconcile(op,self.ledger.config['providers'][self.name]['operations']['search'])
                return {'provider':self.name}
        registry={name:type(name,(Fake,),{'name':name}) for name in cfg['providers']}
        with tempfile.TemporaryDirectory() as root:
            ledger=Ledger(Path(root)/'db',cfg)
            try:
                ledger.create_run('small',0.02)
                router=ProviderRouter(ledger,'small',lambda:None,registry)
                self.assertEqual(router.search('a')['provider'],'brave')
                self.assertEqual(router.search('b')['provider'],'tavily')
                self.assertEqual(router.search('c')['provider'],'brave')
                with self.assertRaises(StopRun):router.search('d')
                self.assertEqual(ledger.total('small'),18000)
            finally:ledger.db.close()

    def test_unknown_duplicate_and_oversized_allocations_rejected(self):
        for selections in [[{'id':'invented','budget':1}], [{'id':'brave','budget':6}], [{'id':'brave','budget':1}]*2]:
            with self.assertRaises(StopRun):apply_search_policy(self.cfg,{**self.profile,'searchProviders':selections})

    def test_apollo_uses_free_endpoint_and_labels_partial_identity(self):
        client=ApolloPeople(None,None,None)
        self.assertEqual(client.request_body('recruiter Georgia',5,{}),{'q_keywords':'recruiter Georgia','page':1,'per_page':5})
        result=client.normalize({'people':[{'id':'abc','first_name':'Jane','last_name_obfuscated':'S***','title':'Recruiter','email':'private@example.com'}]})
        self.assertEqual(result['costDollars']['total'],'0')
        self.assertIn('partial',result['results'][0]['title'])
        self.assertNotIn('private@example.com',str(result))

    def test_apollo_records_remain_distinct_after_url_normalization(self):
        from recruitme.data import canonical_url
        client=ApolloPeople(None,None,None)
        rows=client.normalize({'people':[{'id':'abc','first_name':'Jane'},
                                        {'id':'def','first_name':'Jane'}]})['results']
        self.assertEqual(len({canonical_url(row['url']) for row in rows}),2)
        self.assertEqual(canonical_url('https://example.com/profile#section'),'https://example.com/profile')
        self.assertEqual(canonical_url('https://api.apollo.io.evil.test/api/v1/mixed_people/api_search#abc'),
                         'https://api.apollo.io.evil.test/api/v1/mixed_people/api_search')
