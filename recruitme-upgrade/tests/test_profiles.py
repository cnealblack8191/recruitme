import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_foundation import configuration
from recruitme.budget import Ledger,StopRun
from recruitme.profiles import validate,next_plan,apply_screen
from recruitme.autonomous import new_state,screen

class Profiles(unittest.TestCase):
    def profile(self):return json.loads((Path(__file__).parents[1]/'profiles/atlanta-electricians.json').read_text())

    def test_paired_queries_and_sequential_provider_plan(self):
        s=new_state();s.update(job_profile=validate(self.profile()),search_as_of='2026-09-09')
        for i in range(20):
            a=next_plan(s);s['queries'].append(a)
            b=next_plan(s);s['queries'].append(b)
            self.assertEqual(a['query'],b['query']);self.assertEqual(a['options'],b['options'])
            self.assertEqual((a['provider'],b['provider']),('exa_keyed','tavily'))

    def test_another_occupation_requires_no_code_change(self):
        p=self.profile();p.update(id='accountants',locations=['Atlanta'],fit_terms=['general ledger'],tracks=[{'id':'experienced','roles':['accountant']}])
        s=new_state();s.update(job_profile=validate(p),search_as_of='2026-09-09')
        self.assertIn('accountant',next_plan(s)['query']);self.assertNotIn('electrician',next_plan(s)['query'])
        packet=screen({'url':'https://example.org/person','title':'Jane Doe','text':'Accountant, general ledger, seeking employment'})
        packet=apply_screen(packet,p)
        self.assertEqual(packet['classification'],'C — Provisional')
        self.assertEqual(packet['readiness']['pay_acceptance'],'UNKNOWN')

    def test_junior_never_automatically_promoted(self):
        p=apply_screen(screen({'url':'https://example.org/person','title':'Jane Doe','text':'Electrical apprentice commercial construction available for work'}),self.profile())
        self.assertIn('junior',p['track_hints']);self.assertEqual(p['classification'],'C — Provisional')

    def test_invalid_profile_fails_closed(self):
        with self.assertRaises(StopRun):validate({'version':1,'id':'test'})

class Dispatch(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.c=configuration()
        self.c['session']={'id':'s','limit_usd':'25','high_value_only_after_usd':'20','ends_at':'2099-01-01T00:00:00+00:00'}
        self.l=Ledger(Path(self.tmp.name)/'db',self.c);self.l.create_run('r','1.25')
    def tearDown(self):self.l.db.close();self.tmp.cleanup()
    def reserve(self):return self.l.reserve('r','fake','small','one')
    def test_exact_cap_dispatches_once_without_new_headroom(self):
        op=self.reserve();deadline=self.l.runtime_for('r')['session_deadline']
        self.l.dispatch('r',op)
        with self.assertRaises(StopRun):self.l.dispatch('r',op)
        with self.assertRaises(StopRun):self.l.reserve('r','fake','small','two')
        self.assertEqual(self.l.total(),1250000);self.assertEqual(self.l.runtime_for('r')['session_deadline'],deadline)
    def test_deadline_still_blocks_reserved_dispatch(self):
        op=self.reserve()
        with patch('recruitme.budget.time.time',return_value=99999999999):
            with self.assertRaises(StopRun):self.l.dispatch('r',op)
    def test_disabled_provider_blocks_dispatch(self):
        op=self.reserve();self.c['providers']['fake']['enabled']=False
        with self.assertRaises(StopRun):self.l.dispatch('r',op)
    def test_price_freeze_blocks_dispatch(self):
        op=self.reserve();self.l.event('r','PRICE_BREACH','fixture')
        with self.assertRaises(StopRun):self.l.dispatch('r',op)
    def test_resource_guard_remains_active(self):
        op=self.reserve()
        with patch.object(self.l,'check_resources',side_effect=StopRun('DISK_LIMIT_REACHED')):
            with self.assertRaises(StopRun):self.l.dispatch('r',op)
    def test_restart_does_not_redispatch_or_reset_spend(self):
        op=self.reserve();self.l.dispatch('r',op);self.l.db.close()
        self.l=Ledger(Path(self.tmp.name)/'db',self.c)
        with self.assertRaises(StopRun):self.l.dispatch('r',op)
        self.assertEqual(self.l.total(),1250000)
