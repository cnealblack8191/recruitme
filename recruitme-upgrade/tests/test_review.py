import datetime,json,tempfile,unittest
from pathlib import Path
from recruitme.budget import Ledger,StopRun
from recruitme.review import build_record,import_submission,policy_from_submission
from recruitme import data
from recruitme.web_snapshot import reviewed_rows
from test_foundation import configuration

NOW=datetime.datetime(2026,9,17,12,tzinfo=datetime.timezone.utc)

def submission(**kw):
    s=dict(identity_key='https://www.linkedin.com/in/jane-doe',name='Jane Doe',source_url='https://www.linkedin.com/in/jane-doe',
           source_type='professional_profile',role='Journeyman electrician',location='Chamblee, GA',years_experience=7,
           field_experience_confirmed=True,statement_excerpt='#OpenToWork — looking for my next commercial project',
           statement_date='2026-09-10',date_basis='post_timestamp',signal_polarity='POSITIVE_SEEKING',
           signal_source_url='https://www.linkedin.com/posts/jane-doe_opentowork',identity_confidence='confirmed',
           contradictions_checked=True,contact_url='https://www.linkedin.com/in/jane-doe',decision='A',reviewer='charles',
           channel='linkedin_recruiter',run_id=None)
    s.update(kw);return s

class ReviewForm(unittest.TestCase):
    def test_confirmed_identity_produces_verified_evidence_and_ab_assessment(self):
        r=build_record(submission(),now=NOW)
        self.assertTrue(r['reviewed_by_human'])
        signal=next(e for e in r['evidence'] if e['field']=='availability_signal')
        self.assertEqual((signal['original_date'],signal['signal_polarity'],signal['date_basis']),('2026-09-10','POSITIVE_SEEKING','post_timestamp'))
        self.assertTrue(signal['human_verified'] and signal['subject_confirmed'] and signal['original_date_verified'])
        self.assertEqual(signal['source_url'],'https://www.linkedin.com/posts/jane-doe_opentowork')
        self.assertEqual(r['assessment']['classification'],'A');self.assertEqual(r['assessment']['signal_date'],'2026-09-10')
        self.assertEqual(r['facts']['commercial_experience'],True);self.assertEqual(r['review']['channel'],'linkedin_recruiter')
    def test_probable_identity_keeps_everything_inferred(self):
        r=build_record(submission(identity_confidence='probable',decision='FIT_POOL'),now=NOW)
        self.assertTrue(all(e['human_verified'] is False and e['knowledge_status']=='REASONABLE_INFERENCE' for e in r['evidence']))
        self.assertNotIn('assessment',r)
    def test_validation_fails_closed(self):
        bad=[dict(decision='C'),dict(signal_polarity='yes'),dict(date_basis='guess'),dict(contradictions_checked=False),
             dict(source_url='javascript:alert(1)'),dict(statement_date=None,date_basis='post_timestamp'),dict(statement_date='2099-01-01'),
             dict(years_experience='7'),dict(identity_confidence='sure'),dict(name=''),dict(reviewer=None),dict(channel='fax')]
        for kw in bad:
            with self.subTest(kw=kw),self.assertRaises(StopRun):build_record(submission(**kw),now=NOW)
        r=build_record(submission(statement_date=None,date_basis='unknown',decision='FIT_POOL'),now=NOW)
        self.assertFalse(next(e for e in r['evidence'] if e['field']=='availability_signal')['original_date_verified'])
    def test_policy_override_validated(self):
        self.assertIsNone(policy_from_submission(submission(),None))
        self.assertEqual(policy_from_submission(submission(policy={'maximum_signal_age_days':30}),None)['maximum_signal_age_days'],30)
        with self.assertRaises(StopRun):policy_from_submission(submission(policy={'maximum_signal_age_days':0}),None)

class ReviewImport(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.l=Ledger(Path(self.tmp.name)/'db',configuration())
    def tearDown(self):self.l.db.close();self.tmp.cleanup()
    def test_confirmed_recent_electrician_becomes_verified_a(self):
        today=datetime.datetime.now(datetime.timezone.utc)
        self.l.create_run('discovery-1','1')
        out=import_submission(self.l,submission(statement_date=(today-datetime.timedelta(days=5)).date().isoformat(),run_id='discovery-1'),now=today)
        self.assertTrue(out['accepted'],out);self.assertEqual(out['classification'],'FULLY_QUALIFIED');self.assertEqual(out['blockers'],[])
        rows=reviewed_rows(self.l.db,'discovery-1')
        self.assertEqual(len(rows),1);self.assertTrue(rows[0]['verified']);self.assertEqual(rows[0]['reviewDecision'],'A');self.assertEqual(rows[0]['reviewer'],'charles')
        self.assertEqual(self.l.db.execute("SELECT COUNT(*) FROM qualified_progress WHERE classification='A'").fetchone()[0],1)
        self.assertEqual(self.l.db.execute("SELECT status FROM runs WHERE id=?",(out['runId'],)).fetchone()[0],'COMPLETE')
        self.assertEqual(self.l.total(),0)
    def test_ab_that_fails_gates_rolls_back_with_reasons(self):
        today=datetime.datetime.now(datetime.timezone.utc)
        out=import_submission(self.l,submission(statement_date=(today-datetime.timedelta(days=120)).date().isoformat()),now=today)
        self.assertFalse(out['accepted']);self.assertTrue(any('signal' in e.lower() for e in out['errors']))
        self.assertEqual(self.l.db.execute('SELECT COUNT(*) FROM candidates').fetchone()[0],0)
        out=import_submission(self.l,submission(statement_date=(today-datetime.timedelta(days=120)).date().isoformat(),decision='FIT_POOL'),now=today)
        self.assertTrue(out['accepted']);self.assertNotEqual(out['classification'],'FULLY_QUALIFIED');self.assertEqual(out['decision'],'FIT_POOL')
    def test_profile_policy_governs_review(self):
        today=datetime.datetime.now(datetime.timezone.utc)
        profile={'id':'x','version':1,'locations':['Savannah Georgia'],'fit_terms':['commercial'],'tracks':[{'id':'t','roles':['electrician']}],
                 'qualification_policy':{'maximum_signal_age_days':30}}
        out=import_submission(self.l,submission(statement_date=(today-datetime.timedelta(days=5)).date().isoformat()),profile=profile,now=today)
        self.assertFalse(out['accepted'])  # Chamblee is outside a Savannah profile
        out=import_submission(self.l,submission(location='Savannah, GA',statement_date=(today-datetime.timedelta(days=5)).date().isoformat()),profile=profile,now=today)
        self.assertTrue(out['accepted'],out)
    def test_recruiter_role_kind_uses_hr_title_plus_field_flag(self):
        today=datetime.datetime.now(datetime.timezone.utc)
        recruiter=submission(role='Senior Recruiter',field_experience_confirmed=True,statement_date=(today-datetime.timedelta(days=3)).date().isoformat(),
                             policy={'role_kind':'electrical_recruiter'},location='Covington, GA')
        out=import_submission(self.l,recruiter,now=today)
        self.assertTrue(out['accepted'],out);self.assertEqual(out['classification'],'FULLY_QUALIFIED')
        out=import_submission(self.l,submission(identity_key='k2',role='Senior Recruiter',field_experience_confirmed=False,decision='FIT_POOL',
                                                statement_date=(today-datetime.timedelta(days=3)).date().isoformat(),policy={'role_kind':'electrical_recruiter'}),now=today)
        self.assertTrue(out['accepted']);self.assertIn('hands-on electrical field experience',' '.join(out['blockers']))

if __name__=='__main__':unittest.main()
