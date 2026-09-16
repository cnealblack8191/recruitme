import datetime
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_foundation import configuration
from recruitme.budget import Ledger, StopRun, money
from recruitme.governors import ProviderLimitReached
from recruitme.connectors import ExaFree
from recruitme.routing import ProviderRouter


class Hardening(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'db'
        self.cfg=configuration()
        self.cfg['research_window_id']='shared'
        self.cfg['session']={'id':'tonight','limit_usd':'25','high_value_only_after_usd':'20','ends_at':'2099-01-01T00:00:00+00:00'}
        self.cfg['providers']['exa_free']=dict(self.cfg['providers']['fake'],operations={k:'0' for k in ('initialize','initialized','list_tools','search')})
        self.l=Ledger(self.path,self.cfg)
        self.l.create_run('one','10')

    def tearDown(self):
        self.l.db.close();self.tmp.cleanup()

    def test_sql_deadlines_and_bindings_immutable(self):
        for sql in ("UPDATE runtime_sessions SET session_deadline=session_deadline+1",
                    "UPDATE runs SET deadline=deadline+1", "UPDATE sessions SET deadline=deadline+1",
                    "UPDATE sessions SET cap=100000000", "UPDATE runs SET cap=100000000",
                    "UPDATE runtime_bindings SET runtime_id='another'"):
            with self.subTest(sql=sql),self.assertRaises(sqlite3.IntegrityError):self.l.db.execute(sql)

    def test_budget_initialization_never_changes_runtime(self):
        before=dict(self.l.runtime_for('one'))
        self.cfg['session']['limit_usd']='100'
        self.cfg['session']['ends_at']='2099-02-01T00:00:00+00:00'
        self.l.initialize_budget()
        self.assertEqual(before,dict(self.l.runtime_for('one')))
        self.assertEqual(self.l.db.execute('SELECT cap FROM sessions').fetchone()[0],money('25'))

    def test_resume_preserves_original_deadline_and_spend(self):
        self.l.reserve('one','fake','small','x')
        original=self.l.runtime_for('one')['session_deadline']
        self.l.stop('one','synthetic crash')
        other=Ledger(self.path,self.cfg)
        other.create_run('one','10',resume=True)
        self.assertEqual(other.total(),money('1.25'))
        self.assertEqual(other.runtime_for('one')['session_deadline'],original)
        with patch('recruitme.governors.time.time',return_value=original):
            with self.assertRaises(StopRun):other.create_run('one','10',resume=True)
            with self.assertRaises(StopRun):other.create_run('two','10')
        other.db.close()

    def test_resume_cannot_rebind_to_new_runtime(self):
        original=dict(self.l.runtime_for('one'))
        self.cfg['research_window_id']='new-human-run'
        self.l.create_run('one','10',resume=True)
        self.assertEqual(dict(self.l.runtime_for('one')),original)

    def test_provider_initialization_never_resets_usage(self):
        class Response:
            headers={}
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,*a):return b'{"result":{}}'
        class Opener:
            def open(self,*a,**k):return Response()
        self.l.reserve('one','exa_free','search','prior')
        for unused in range(2):ExaFree(self.l,'one',lambda:None,Opener()).initialize()
        self.assertEqual(self.l.db.execute('SELECT COUNT(*) FROM operations').fetchone()[0],5)

    def test_retry_consumes_request_allowance(self):
        self.cfg['providers']['fake']['run_query_limit']=2
        for unused in range(2):
            op=self.l.reserve('one','fake','free','retry');self.l.reconcile(op,'0')
        with self.assertRaises(StopRun):self.l.reserve('one','fake','free','other')
        self.assertEqual(self.l.db.execute('SELECT COUNT(*) FROM operations').fetchone()[0],2)

    def test_response_checkpoint_survives_crash_before_reconciliation(self):
        op=self.l.reserve('one','exa_free','search','synthetic')
        response={'content':[{'type':'text','text':'fixture'}]}
        self.l.save_outcome(op,'SUCCESS',response,123)
        other=Ledger(self.path,self.cfg);other.create_run('two','10')
        cached=other.cached_search('two','exa_free','synthetic')
        self.assertEqual(cached['response'],response)
        self.assertEqual(cached['observed_at'],123)
        self.assertEqual(other.db.execute('SELECT state FROM operations').fetchone()[0],'RESERVED')
        other.db.close()

    def test_uncertain_request_not_repeated(self):
        self.l.reserve('one','exa_free','search','uncertain')
        with self.assertRaisesRegex(StopRun,'UNCERTAIN_REQUEST'):self.l.cached_search('one','exa_free','uncertain')

    def test_manifest_cannot_change_on_resume(self):
        self.l.bind_manifest('one',{'queries':['fixture']})
        self.l.bind_manifest('one',{'queries':['fixture'],'resume':True})
        with self.assertRaises(StopRun):self.l.bind_manifest('one',{'queries':['different']})

    def test_provider_limit_exact_operation_time_and_not_success(self):
        op=self.l.reserve('one','exa_free','search','limited')
        self.l.save_outcome(op,'PROVIDER_LIMIT_REACHED',{'notice':'fixture'},123.5)
        row=self.l.db.execute('SELECT * FROM provider_health').fetchone()
        self.assertEqual((row['first_operation_id'],row['first_observed_at']),(op,123.5))
        self.assertIsNone(self.l.cached_search('one','exa_free','another'))
        with self.assertRaises(ProviderLimitReached):self.l.reserve('one','exa_free','search','other')
        self.assertEqual(self.l.db.execute("SELECT COUNT(*) FROM operation_outcomes WHERE status='SUCCESS'").fetchone()[0],0)

    def test_paid_unapproved_provider_fails_closed(self):
        self.cfg['providers']['fake']['approved']=False
        with self.assertRaises(StopRun):self.l.reserve('one','fake','small','paid')
        self.assertEqual(self.l.total(),0)

    def test_router_fallback_only_approved_and_budgeted(self):
        op=self.l.reserve('one','exa_free','search','limit')
        self.l.save_outcome(op,'PROVIDER_LIMIT_REACHED')
        self.cfg['provider_priority']={'free_discovery':['exa_free'],'low_cost_paid_discovery':['fake']}
        self.cfg['providers']['fake']['operations']['search']='1.25'
        class Fake:
            def __init__(self,l,r,g):self.l,self.r,self.g=l,r,g
            def initialize(self):pass
            def tools(self):return []
            def search(self,q,c):
                self.g();op=self.l.reserve(self.r,'fake','search',q)
                self.l.save_outcome(op,'SUCCESS',{'content':[]});self.l.reconcile(op,'1.25')
                return {'content':[]}
        router=ProviderRouter(self.l,'one',lambda:self.l.check('one'),{'fake':Fake})
        self.assertEqual(router.search('fixture'),{'content':[]})
        self.assertEqual(self.l.total(),money('1.25'))
        self.cfg['providers']['fake']['approved']=False
        with self.assertRaisesRegex(StopRun,'NO_ELIGIBLE_PROVIDER'):router.search('unapproved')
        self.assertEqual(self.l.total(),money('1.25'))

    def test_candidate_stop_independent_of_budget(self):
        today=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        a=dict(classification='B',reviewed=True,trade_fit=True,identified_person=True,geographic_fit=True,
               signal_subject_confirmed=True,signal_date_verified=True,contradictions_checked=True,
               recruiting_signal='synthetic only',signal_date=today,source_urls=['https://example.org'])
        for i in range(10):self.l.record_qualification('one',str(i),a)
        self.assertEqual(self.l.total(),0)
        with self.assertRaisesRegex(StopRun,'CANDIDATE_TARGET'):self.l.reserve('one','fake','free','x')

    def test_trade_experience_without_signal_cannot_count_as_ab(self):
        with self.assertRaises(StopRun):self.l.record_qualification('one','fixture',{'classification':'A','trade_fit':True})

    def test_disk_failure_does_not_change_other_controls(self):
        self.l.state_root=self.tmp.name
        runtime=dict(self.l.runtime_for('one'))
        with patch('recruitme.governors.shutil.disk_usage') as usage:
            usage.return_value.free=1
            with self.assertRaisesRegex(StopRun,'DISK_LIMIT'):self.l.reserve('one','fake','free','x')
        self.assertEqual(dict(self.l.runtime_for('one')),runtime)
        self.assertEqual(self.l.total(),0)
        self.assertEqual(self.l.db.execute('SELECT COUNT(*) FROM operations').fetchone()[0],0)

    def test_failing_governor_does_not_disable_remaining_guards(self):
        op=self.l.reserve('one','exa_free','search','limit');self.l.save_outcome(op,'PROVIDER_LIMIT_REACHED')
        with self.assertRaises(ProviderLimitReached):self.l.reserve('one','exa_free','search','again')
        deadline=self.l.runtime_for('one')['session_deadline']
        with patch('recruitme.governors.time.time',return_value=deadline):
            with self.assertRaisesRegex(StopRun,'RUNTIME'):self.l.reserve('one','fake','free','after-deadline')
        self.assertTrue(self.l.provider_limited('exa_free'))

    def test_state_storage_guard(self):
        self.l.state_root=self.tmp.name;self.cfg['maximum_state_bytes']=1
        with self.assertRaisesRegex(StopRun,'STATE_STORAGE'):self.l.check('one')

    def test_new_batch_cannot_reset_search_attempt_limit(self):
        self.cfg['providers']['exa_free']['max_attempts']=1
        op=self.l.reserve('one','exa_free','search','same');self.l.reconcile(op,'0')
        self.l.create_run('two','10')
        with self.assertRaisesRegex(StopRun,'LOCAL_REQUEST_LIMIT_REACHED'):self.l.reserve('two','exa_free','search','same')

    def test_http429_is_provider_limit_not_retry_or_result(self):
        import urllib.error
        class Opener:
            calls=0
            def open(self,*a,**k):
                self.calls+=1
                raise urllib.error.HTTPError('https://example.org',429,'fixture',{},None)
        opener=Opener()
        with self.assertRaises(ProviderLimitReached):ExaFree(self.l,'one',lambda:None,opener).search('fixture')
        with self.assertRaises(ProviderLimitReached):ExaFree(self.l,'one',lambda:None,opener).search('fixture2')
        self.assertEqual(opener.calls,1)
        self.assertEqual(self.l.db.execute('SELECT status FROM operation_outcomes').fetchone()[0],'PROVIDER_LIMIT_REACHED')

    def test_cached_result_never_contacts_provider(self):
        op=self.l.reserve('one','exa_free','search','cached')
        self.l.save_outcome(op,'SUCCESS',{'content':[]},123);self.l.reconcile(op,'0')
        class NoNetwork:
            def open(self,*a,**k):raise AssertionError('Network must not run')
        self.assertEqual(ExaFree(self.l,'one',lambda:self.l.check('one'),NoNetwork()).search('cached'),{'content':[]})
        self.assertEqual(self.l.db.execute('SELECT COUNT(*) FROM operations').fetchone()[0],1)

    def test_historical_deadline_migration_preserves_accounting(self):
        # Synthetic legacy collision: original shared window 30 minutes, batch overwritten later.
        op=self.l.reserve('one','fake','small','historical')
        before=self.l.total()
        self.l.db.execute('DROP TRIGGER immutable_batch_deadline')
        self.l.db.execute("INSERT INTO research_windows VALUES('deep-search-run3',1000,2800)")
        self.l.db.execute("INSERT INTO runs(id,cap,created,deadline,status) VALUES('run3-fixture',10000000,1000,9999,'COMPLETE')")
        self.l.db.execute("DELETE FROM governor_migrations WHERE id='independent-v1'")
        self.l.initialize_governance()
        self.assertEqual(self.l.db.execute("SELECT deadline FROM runs WHERE id='run3-fixture'").fetchone()[0],2800)
        self.assertEqual(self.l.total(),before)
        self.assertEqual(self.l.db.execute('SELECT id FROM operations').fetchone()[0],op)
        self.assertEqual(self.l.db.execute("SELECT COUNT(*) FROM audit WHERE event='DEADLINE_COLLISION_REPAIRED'").fetchone()[0],1)
        with self.assertRaises(sqlite3.IntegrityError):self.l.db.execute("UPDATE runs SET deadline=9999 WHERE id='run3-fixture'")
