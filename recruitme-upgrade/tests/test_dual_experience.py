import unittest
from recruitme.autonomous import new_state,screen
from recruitme.dual_experience import apply_screen,next_plan,summary,VERSION

class DualExperience(unittest.TestCase):
    def setUp(self):
        self.profile={'id':'covington-electrical-talent-acquisition','locations':['Atlanta Georgia','Covington Georgia'],
                      'discovery_provider':'exa_keyed','screening_version':VERSION}
    def packet(self,body,name='Jane Smith'):
        return apply_screen(screen({'url':'https://www.linkedin.com/in/jane-smith','title':name+' - Recruiter','text':body}),self.profile)
    def test_local_field_then_hr_no_availability_is_d_hint(self):
        p=self.packet('Human resources manager\nAtlanta Georgia\n## Experience\nElectrician\n2010-2016\nHR Manager\n2016-present')
        self.assertEqual(p['candidate_grade_hint'],'D')
        self.assertFalse(p['grade_verified'])
    def test_electrical_recruiting_alone_not_field_experience(self):
        p=self.packet('Recruiter Atlanta Georgia\n## About\nI recruit electricians. Open to work.')
        self.assertFalse(p['dual_experience_hint'])
        self.assertIsNone(p['candidate_grade_hint'])
    def test_experience_recruiting_electricians_not_field_work(self):
        p=self.packet('Recruiter Atlanta Georgia\n## Experience\nRecruiter hiring electricians 2020-2026')
        self.assertFalse(p['dual_experience_hint'])
    def test_local_active_does_not_auto_confirm_date(self):
        p=self.packet('Recruiter Atlanta Georgia. Former electrician. Open to work.')
        self.assertEqual(p['candidate_grade_hint'],'B')
        self.assertIsNone(p['candidate_grade'])
        self.assertFalse(p['signal_date_confirmed'])
    def test_technical_and_pay_support_a_review_hint(self):
        p=self.packet('Recruiter Atlanta Georgia. Former electrician. Open to work. Technical interviews and pay rates.')
        self.assertEqual(p['candidate_grade_hint'],'A')
        self.assertFalse(p['grade_verified'])
    def test_southeast_general_relocation(self):
        p=self.packet('Recruiter Florida. Former electrician. Willing to relocate.')
        self.assertEqual(p['candidate_grade_hint'],'C')
    def test_outside_southeast_not_c(self):
        self.assertIsNone(self.packet('Recruiter California. Former electrician. Willing to relocate.')['candidate_grade_hint'])
    def test_header_employer_location_not_local_residence(self):
        p=self.packet('Recruiter California\n## About\nFormer electrician. Open to work.\n## Experience\nEmployer office Atlanta Georgia')
        self.assertIsNone(p['candidate_grade_hint'])
    def test_company_page_not_candidate(self):
        p=apply_screen(screen({'url':'https://example.org/company','title':'Example Staffing','text':'Recruiter Atlanta Georgia. Former electrician. Open to work.'}),self.profile)
        self.assertIsNone(p['candidate_grade_hint'])
    def test_counts_deduplicate_name_and_never_claim_verification(self):
        p=self.packet('Recruiter Atlanta Georgia. Former electrician.')
        q=dict(p,source_url='https://www.linkedin.com/in/other')
        s=summary([p,q]);self.assertEqual(s['unverified_identity_clusters'],1)
        self.assertEqual(s['verified_candidate_count'],0);self.assertFalse(s['target_met'])
    def test_queries_provider_scope_and_undated_background(self):
        s=new_state();s.update(job_profile=self.profile,search_as_of='2026-09-11')
        regional_sources=set();undated=0
        for i in range(128):
            s['discovery_index']=i;s['queries']=[]
            p=next_plan(s,'tavily')
            self.assertEqual(p['provider'],'exa_keyed')
            self.assertNotIn('nationwide',p['query'])
            if p['strategy']=='dual_southeast':regional_sources.add(p['source_family'])
            if not p['options'].get('start_date'):undated+=1
        self.assertIn('linkedin',regional_sources);self.assertGreater(undated,64)
    def test_structured_branch_only_when_run_lists_eligible_people_providers(self):
        import json
        s=new_state();s.update(job_profile=self.profile,search_as_of='2026-09-11')
        for i in range(16):
            s['discovery_index']=i;s['queries']=[]
            self.assertNotEqual(next_plan(s,'tavily')['strategy'],'dual_structured_transition')
        s['structured_providers']=['pdl_free','apollo','exa_people']
        plans={}
        for i in range(48):
            s['discovery_index']=i;s['queries']=[]
            p=next_plan(s,'tavily')
            if p['strategy']=='dual_structured_transition':
                plans.setdefault(p['provider'],[]).append(p)
                self.assertEqual(p['options'],{});self.assertEqual(p['source_family'],'structured_people')
                self.assertIsNone(p.get('target'))
        self.assertEqual(set(plans),{'pdl_free','apollo','exa_people'})
        pdl=json.loads(plans['pdl_free'][0]['query'])
        self.assertIn('experience.title.name',pdl);self.assertIn('location_region',pdl)
        self.assertTrue({'job_title','job_title_sub_role'}&set(pdl))
        apollo=json.loads(plans['apollo'][0]['query'])
        self.assertEqual(set(apollo),{'person_titles','person_locations','q_keywords'})
        self.assertIn('former',plans['exa_people'][0]['query'])
        # Web queries continue between structured slots.
        self.assertEqual(sum(len(v) for v in plans.values()),12)
    def test_structured_records_screen_as_dual_experience_fit_not_seekers(self):
        text='Senior Recruiter\natlanta, georgia, united states\n## Experience\n### Senior Recruiter\nTrades Staffing\n2021-03 - Present\n### Electrician\nMetro Electric\n2012-01 - 2021-02'
        p=self.packet(text,'Alex Rivera')
        self.assertTrue(p['dual_experience_hint']);self.assertEqual(p['candidate_grade_hint'],'D')
        self.assertFalse(p['possible_recruiting_signal'])
    def test_military_electrical_rating_counts_as_field_history(self):
        p=self.packet('Military Recruiter Atlanta Georgia\n## About\nServed as a Navy Construction Electrician before recruiting duty. Open to work.')
        self.assertTrue(p['dual_experience_hint']);self.assertEqual(p['candidate_grade_hint'],'B')
        q=self.packet('Talent Acquisition Partner Atlanta Georgia\n## Experience\n### Interior Electrician (12R)\nUS Army\n2014 - 2019')
        self.assertTrue(q['dual_experience_hint'])
    def test_followup_never_pastes_url_into_query(self):
        s=new_state();s.update(job_profile=self.profile,search_as_of='2026-09-11',queries=[{'query':'a'},{'query':'b'}])
        p=self.packet('Recruiter Atlanta Georgia. Former electrician. Open to work.')
        s['packets'][p['source_url']]=p
        q=next_plan(s,'tavily')
        self.assertEqual(q['strategy'],'dual_experience_review');self.assertEqual(q['target'],p['source_url'])
        self.assertNotIn('http',q['query']);self.assertIn('Jane Smith',q['query']);self.assertIn('Atlanta',q['query'])
        nameless=dict(p,name_hint=None,source_url='https://www.linkedin.com/in/unknown')
        s['packets']={nameless['source_url']:nameless}
        self.assertNotEqual(next_plan(s,'tavily')['purpose'],'corroboration/contact')
