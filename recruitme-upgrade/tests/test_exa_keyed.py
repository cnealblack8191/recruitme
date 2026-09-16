import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch
from test_foundation import configuration
from recruitme.budget import Ledger,StopRun,money
from recruitme.governors import ProviderLimitReached
from recruitme.exa_keyed import ExaKeyed,maximum_cost,PRICE_VERSION
from recruitme.routing import ProviderRouter


class Keyed(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.cfg=configuration()
        self.cfg['research_window_id']='shared'
        self.cfg['session']={'id':'session','limit_usd':'25','high_value_only_after_usd':'20','ends_at':'2099-01-01T00:00:00+00:00'}
        self.cfg['providers']['exa_keyed']={'enabled':True,'approved':True,'price_version':PRICE_VERSION,
            'operations':{'search':'0.007'},'poc_limit_usd':'25','run_limit_usd':'10',
            'poc_query_limit':500,'run_query_limit':40,'max_attempts':1}
        self.l=Ledger(Path(self.temp.name)/'db',self.cfg);self.l.create_run('keyed','10')
        self.key_patch=patch('recruitme.exa_keyed.load_key',return_value='SYNTHETIC-NOT-A-KEY')
        self.key_patch.start()
        self.calls=0

    def tearDown(self):
        self.key_patch.stop();self.l.db.close();self.temp.cleanup()

    def opener(self,result=None,error=None):
        test=self
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,*a):return json.dumps(result if result is not None else {'results':[],'costDollars':{'total':0.007}}).encode()
        class Opener:
            def open(self,req,timeout):
                test.calls+=1
                row=test.l.db.execute("SELECT * FROM operations WHERE provider='exa_keyed' ORDER BY rowid DESC").fetchone()
                test.assertEqual(row['state'],'RESERVED');test.assertEqual(row['reserved'],7000)
                test.assertEqual(req.full_url,'https://api.exa.ai/search')
                body=json.loads(req.data);test.assertEqual(body['type'],'auto')
                test.assertNotIn('summary',body['contents']);test.assertEqual(body['contents']['subpages'],0)
                test.assertLessEqual(timeout,25)
                if error:raise error
                return Response()
        return Opener()

    def client(self,**kw):return ExaKeyed(self.l,'keyed',lambda:self.l.check('keyed'),self.opener(**kw))

    def fill(self,amount,index):
        p=self.cfg['providers']['fake'];p['operations']['fill']=amount;p['operation_purposes']={'fill':'high_value'}
        run='fill'+str(index);self.l.create_run(run,'10');self.l.reserve(run,'fake','fill',run)

    def test_exact_maximum_and_unsupported_counts(self):
        for count in (1,3,5,6,10):self.assertEqual(maximum_cost(count),7000)
        for count in (0,11,100,True,2.5):
            with self.assertRaises(StopRun):maximum_cost(count)

    def test_reservation_before_network_reconciliation_after(self):
        self.client().search('synthetic')
        row=self.l.db.execute("SELECT * FROM operations WHERE provider='exa_keyed'").fetchone()
        self.assertEqual(row['actual'],7000);self.assertEqual(row['state'],'RECONCILED')
        self.assertEqual(self.l.db.execute('SELECT status FROM operation_outcomes').fetchone()[0],'SUCCESS')
        self.assertEqual(self.calls,1)

    def test_exact_request_cost_can_reach_transport_only_once(self):
        self.l.create_run('exact','0.007')
        c=ExaKeyed(self.l,'exact',lambda:self.l.check('exact'),self.opener())
        c.search('synthetic exact cap')
        self.assertEqual(self.calls,1)
        self.assertEqual(self.l.total('exact'),7000)
        with self.assertRaises(StopRun):c.search('another synthetic')
        self.assertEqual(self.calls,1)

    def test_free_credit_estimate_does_not_release_budget(self):
        self.client(result={'results':[],'costDollars':{'total':0}}).search('synthetic')
        self.assertEqual(self.l.total(),7000)

    def test_missing_cost_estimate_still_counts_full_maximum(self):
        self.client(result={'results':[]}).search('synthetic');self.assertEqual(self.l.total(),7000)

    def test_network_failure_keeps_reservation_and_no_retry(self):
        with self.assertRaises(StopRun):self.client(error=TimeoutError()).search('synthetic')
        self.assertEqual(self.calls,1);self.assertEqual(self.l.total(),7000)
        self.assertEqual(self.l.db.execute('SELECT state FROM operations').fetchone()[0],'UNKNOWN')

    def test_402_quota_persists_and_does_not_repeat(self):
        client=self.client(error=urllib.error.HTTPError('https://api.exa.ai/search',402,'fixture',{},None))
        with self.assertRaises(ProviderLimitReached):client.search('synthetic')
        with self.assertRaises(ProviderLimitReached):client.search('synthetic2')
        self.assertEqual(self.calls,1);self.assertTrue(self.l.provider_limited('exa_keyed'))
        self.assertEqual(self.l.total(),7000)

    def test_429_limit_classification(self):
        with self.assertRaises(ProviderLimitReached):self.client(error=urllib.error.HTTPError('https://api.exa.ai/search',429,'fixture',{},None)).search('synthetic')
        self.assertEqual(self.l.db.execute('SELECT status FROM operation_outcomes').fetchone()[0],'PROVIDER_LIMIT_REACHED')

    def test_underpriced_configuration_cannot_send(self):
        self.cfg['providers']['exa_keyed']['operations']['search']='0'
        with self.assertRaises(StopRun):self.client().search('synthetic')
        self.assertEqual(self.calls,0)

    def test_paid_disabled_cannot_send(self):
        self.cfg['paid_enabled']=False
        with self.assertRaises(StopRun):self.client().search('synthetic')
        self.assertEqual(self.calls,0)

    def test_25_dollar_session_cannot_be_exceeded(self):
        for i,n in enumerate(('10','10','4.999')):self.fill(n,i)
        with self.assertRaises(StopRun):self.client().search('synthetic')
        self.assertEqual(self.calls,0);self.assertEqual(self.l.total(),money('24.999'))

    def test_100_dollar_poc_cannot_be_exceeded(self):
        for i in range(10):
            self.cfg['session']['id']='historical'+str(i//2)
            self.fill('10',i)
        with self.assertRaises(StopRun):self.client().search('synthetic')
        self.assertEqual(self.calls,0);self.assertEqual(self.l.total(),money('100'))

    def test_20_cutoff_blocks_standard_discovery(self):
        self.fill('10',0);self.fill('10',1)
        with self.assertRaises(StopRun):self.client().search('synthetic')
        self.assertEqual(self.calls,0)

    def test_switch_preserves_deadline_budget_and_provider_counters(self):
        self.cfg['providers']['exa_free']=dict(self.cfg['providers']['exa_keyed'],operations={'search':'0'})
        self.cfg['provider_priority']={'free_discovery':['exa_free'],'low_cost_paid_discovery':['exa_keyed']}
        before=dict(self.l.runtime_for('keyed'))
        class Free:
            def __init__(self,l,r,g):self.l,self.r=l,r
            def initialize(self):pass
            def tools(self):return []
            def search(self,q,c):
                op=self.l.reserve(self.r,'exa_free','search',q)
                self.l.save_outcome(op,'PROVIDER_LIMIT_REACHED');self.l.reconcile(op,'0')
                raise ProviderLimitReached('fixture')
        router=ProviderRouter(self.l,'keyed',lambda:self.l.check('keyed'),{'exa_free':Free,'exa_keyed':lambda l,r,g:ExaKeyed(l,r,g,self.opener())})
        router.search('synthetic')
        self.assertEqual(dict(self.l.runtime_for('keyed')),before)
        self.assertEqual(self.l.session_total('session'),7000)
        counts=dict(self.l.db.execute('SELECT provider,COUNT(*) FROM operations GROUP BY provider').fetchall())
        self.assertEqual(counts,{'exa_free':1,'exa_keyed':1})
        router.search('synthetic')
        self.assertEqual(self.calls,1)

    def test_reflected_key_never_checkpointed(self):
        self.client(result={'results':[{'url':'https://example.org','text':'SYNTHETIC-NOT-A-KEY'}]}).search('synthetic')
        self.assertNotIn('SYNTHETIC-NOT-A-KEY','\n'.join(self.l.db.iterdump()))

    def test_price_breach_freezes_further_requests(self):
        with self.assertRaises(StopRun):self.client(result={'results':[],'costDollars':{'total':0.008}}).search('synthetic')
        self.assertEqual(self.l.total(),8000)
        self.assertEqual(self.l.db.execute("SELECT COUNT(*) FROM audit WHERE event='PRICE_BREACH'").fetchone()[0],1)

    def test_missing_credential_stops_before_reservation(self):
        with patch('recruitme.exa_keyed.load_key',side_effect=StopRun('Credential unavailable')):
            with self.assertRaises(StopRun):self.client().search('synthetic')
        self.assertEqual(self.calls,0);self.assertEqual(self.l.total(),0)

    def test_expired_price_schedule_stops_before_reservation(self):
        with patch('recruitme.exa_keyed.PRICE_VALID_UNTIL','2020-01-01'):
            with self.assertRaises(StopRun):self.client().search('synthetic')
        self.assertEqual(self.calls,0);self.assertEqual(self.l.total(),0)
