"""Adversarial controls: synthetic ledgers and transports, no external requests."""
import concurrent.futures
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from recruitme.budget import Ledger, StopRun, money
from recruitme.governors import BudgetLimitReached, LocalRequestLimitReached, RuntimeLimitReached, ProviderLimitReached
from recruitme.connectors import ExaFree
from recruitme.routing import ProviderRouter
from test_foundation import configuration


class SecurityControls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'ledger.db'
        self.cfg=configuration()
        self.cfg['research_window_id']='shared'
        self.cfg['providers']['exa_free']=dict(copy.deepcopy(self.cfg['providers']['fake']),
            operations={'search':'0'},run_limit_usd='0',poc_limit_usd='0')
        self.cfg['provider_priority']={'free_discovery':['exa_free']}
        self.l=Ledger(self.path,self.cfg)
        self.l.create_run('run','5')

    def tearDown(self):
        self.l.db.close()
        self.tmp.cleanup()

    def router(self):
        return ProviderRouter(self.l,'run',lambda:self.l.check('run'),{'exa_free':ExaFree})

    def termination(self):
        return json.loads(self.l.db.execute("SELECT detail FROM audit WHERE event='RUN_TERMINATION' ORDER BY id DESC LIMIT 1").fetchone()[0])

    def test_router_local_cap_is_not_provider_rate_limit(self):
        self.cfg['providers']['exa_free']['run_query_limit']=0
        with self.assertRaises(LocalRequestLimitReached):self.router().search('test')
        self.assertEqual(self.termination()['code'],'LOCAL_REQUEST_LIMIT_REACHED')
        self.assertFalse(self.l.provider_limited('exa_free'))
        self.assertEqual(self.l.total(),0)

    def test_router_budget_is_not_provider_rate_limit(self):
        self.cfg['providers']['exa_free']['operations']['search']='1'
        with self.assertRaises(BudgetLimitReached):self.router().search('test')
        self.assertEqual(self.termination()['code'],'BUDGET_LIMIT_REACHED')
        self.assertFalse(self.l.provider_limited('exa_free'))

    def test_missing_route_is_configuration_stop(self):
        self.cfg['providers']['exa_free']['enabled']=False
        with self.assertRaisesRegex(StopRun,'NO_ELIGIBLE_PROVIDER'):self.router().search('test')
        self.assertEqual(self.termination()['code'],'NO_ELIGIBLE_PROVIDER')

    def test_provider_receipt_is_required_for_provider_limit(self):
        op=self.l.reserve('run','exa_free','search','limited')
        self.l.save_outcome(op,'PROVIDER_LIMIT_REACHED',{'http_status':429})
        with self.assertRaises(ProviderLimitReached):self.router().search('another')
        self.assertEqual(self.termination()['code'],'PROVIDER_LIMIT_REACHED')

    def test_exact_cap_dispatch_once_then_stop(self):
        self.l.create_run('exact','1.25')
        op=self.l.reserve('exact','fake','small','one')
        self.l.dispatch('exact',op)
        with self.assertRaises(StopRun):self.l.dispatch('exact',op)
        with self.assertRaises(BudgetLimitReached):self.l.reserve('exact','fake','free','two')
        self.assertEqual(self.l.total('exact'),money('1.25'))
        self.assertEqual(self.l.db.execute("SELECT COUNT(*) FROM audit WHERE event='NETWORK_DISPATCH'").fetchone()[0],1)

    def test_hundred_concurrent_attempts_cannot_exceed_five_dollars(self):
        def attempt(i):
            ledger=Ledger(self.path,self.cfg)
            try:
                ledger.reserve('run','fake','small',str(i))
                return 1
            except StopRun:return 0
            finally:ledger.db.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(attempt,range(100))),4)
        self.assertEqual(self.l.total(),money('5'))

    def test_racing_duplicate_search_reserves_only_once(self):
        self.l.create_run('other','5')
        def attempt(run):
            ledger=Ledger(self.path,self.cfg)
            try:
                ledger.reserve(run,'exa_free','search','identical')
                return 1
            except LocalRequestLimitReached:return 0
            finally:ledger.db.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(attempt,['run','other'])),1)
        self.assertEqual(self.l.db.execute('SELECT COUNT(*) FROM operations').fetchone()[0],1)

    def test_nan_query_ceiling_fails_closed(self):
        self.cfg['providers']['exa_free']['run_query_limit']=float('nan')
        with self.assertRaisesRegex(StopRun,'Invalid application request ceiling'):
            self.l.reserve('run','exa_free','search','test')
        self.assertEqual(self.l.db.execute('SELECT COUNT(*) FROM operations').fetchone()[0],0)

    def test_runtime_at_dispatch_keeps_original_reason_and_no_network(self):
        class NoNetwork:
            def open(self,*args,**kwargs):raise AssertionError('Must not dispatch')
        with patch.object(self.l,'dispatch',side_effect=RuntimeLimitReached('expired')):
            with self.assertRaises(RuntimeLimitReached):ExaFree(self.l,'run',lambda:None,NoNetwork()).search('test')
        self.assertEqual(self.termination()['code'],'RUNTIME_LIMIT_REACHED')

    def test_free_transport_uses_dispatch_audit(self):
        class Response:
            headers={}
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):return b'{"result":{"content":[]}}'
        class Opener:
            def open(self,*args,**kwargs):return Response()
        ExaFree(self.l,'run',lambda:None,Opener()).search('test')
        self.assertEqual(self.l.db.execute("SELECT COUNT(*) FROM audit WHERE event='NETWORK_DISPATCH'").fetchone()[0],1)

    def test_429_no_retry_persists_across_new_run(self):
        class Limited:
            calls=0
            def open(self,*args,**kwargs):
                self.calls+=1
                raise urllib.error.HTTPError('https://example.org',429,'limited',{'Retry-After':'1'},None)
        opener=Limited()
        with self.assertRaises(ProviderLimitReached):ExaFree(self.l,'run',lambda:None,opener).search('one')
        self.l.create_run('later','5')
        with self.assertRaises(ProviderLimitReached):ExaFree(self.l,'later',lambda:None,opener).search('two')
        self.assertEqual(opener.calls,1)

    def test_unknown_spend_survives_reopen(self):
        op=self.l.reserve('run','fake','small','one')
        self.l.reconcile(op,None)
        other=Ledger(self.path,self.cfg)
        try:self.assertEqual(other.total(),money('1.25'))
        finally:other.db.close()

    def test_normal_completion_has_distinct_audit_code(self):
        self.l.stop('run','All requested work complete','COMPLETE')
        self.assertEqual(self.termination()['code'],'NORMAL_COMPLETION')

    def test_runtime_not_misclassified_as_money(self):
        deadline=self.l.runtime_for('run')['session_deadline']
        with patch('recruitme.governors.time.time',return_value=deadline):
            with self.assertRaises(RuntimeLimitReached):self.l.reserve('run','fake','free','late')
        self.assertEqual(self.termination()['code'],'RUNTIME_LIMIT_REACHED')
