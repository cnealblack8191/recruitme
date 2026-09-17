import datetime,tempfile,unittest
from pathlib import Path
from recruitme.applicants import applicant_record,applicant_submission
from recruitme.budget import Ledger,StopRun
from recruitme import data
from recruitme.web_snapshot import reviewed_rows
from test_foundation import configuration

OPENING={'role':'Commercial electrician','title':'Commercial Electrician — Doraville','run_id':None}

def application(**kw):
    a=dict(id=42,full_name='Sam Applicant',email='sam@example.org',resume_url='https://s3.example/resume.pdf',
           created_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    a.update(kw);return a

class Applicants(unittest.TestCase):
    def test_submission_shape_and_validation(self):
        s=applicant_submission(application(),opening=OPENING,portal_base_url='https://hire.ecinc.us/')
        self.assertEqual((s['identity_key'],s['channel'],s['date_basis'],s['decision'],s['source_type']),('portal:42','candidate_portal','application','APPLICANT','first_party_submission'))
        self.assertTrue(s['source_url'].startswith('https://hire.ecinc.us/admin/results#candidate-42'))
        self.assertNotIn('sam@example.org',str(s))
        for bad in (dict(id='42'),dict(full_name=''),dict(created_at='yesterday')):
            with self.subTest(bad=bad),self.assertRaises(StopRun):applicant_submission(application(**bad),opening=OPENING,portal_base_url='https://hire.ecinc.us')
        with self.assertRaises(StopRun):applicant_submission(application(),opening=OPENING,portal_base_url='localhost')
    def test_application_verifies_seeking_signal_only_and_lands_provisional(self):
        with tempfile.TemporaryDirectory() as tmp:
            l=Ledger(Path(tmp)/'db',configuration());l.create_run('intake','0');data.initialize(l.db)
            record=applicant_record(application(),opening=OPENING,portal_base_url='https://hire.ecinc.us')
            cid=data.import_candidate(l.db,record,run_id='intake')
            q=data.candidate_assessment(l.db,cid)
            self.assertEqual(q['classification'],'PROVISIONAL')
            self.assertEqual(q['claims']['availability_signal']['knowledge_status'],'VERIFIED_FACT')
            self.assertEqual(q['claims']['name']['knowledge_status'],'REASONABLE_INFERENCE')
            self.assertEqual(q['components']['freshness']['score'],10)
            self.assertIn('Metro Atlanta location not established',q['blockers'])
            row=reviewed_rows(l.db,'intake')[0]
            self.assertEqual(row['reviewDecision'],'APPLICANT');self.assertFalse(row['verified'])
            self.assertEqual(l.db.execute("SELECT COUNT(*) FROM qualified_progress").fetchone()[0],0)
            l.db.close()
    def test_system_recorded_flag_cannot_verify_other_fields_or_other_sources(self):
        record=applicant_record(application(),opening=OPENING,portal_base_url='https://hire.ecinc.us')
        for e in record['evidence']:
            if e['field']=='role':e.update(system_recorded=True,knowledge_status='VERIFIED_FACT')
        from recruitme.qualification import assess_candidate
        q=assess_candidate(record['facts'],record['evidence'],record['contacts'])
        self.assertEqual(q['claims']['role']['knowledge_status'],'REASONABLE_INFERENCE')
        for e in record['evidence']:
            if e['field']=='availability_signal':e['source_type']='professional_profile'
        q=assess_candidate(record['facts'],record['evidence'],record['contacts'])
        self.assertEqual(q['claims']['availability_signal']['knowledge_status'],'REASONABLE_INFERENCE')

if __name__=='__main__':unittest.main()
