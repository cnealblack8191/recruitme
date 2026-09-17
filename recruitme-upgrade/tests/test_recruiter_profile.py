import json
from pathlib import Path
import unittest
from recruitme.autonomous import new_state,screen
from recruitme.profiles import validate,next_plan,apply_screen

class RecruiterProfile(unittest.TestCase):
    def setUp(self):
        self.p=validate(json.loads((Path(__file__).parents[1]/'profiles/covington-electrical-talent-acquisition.json').read_text()))
    def packet(self,text):
        return apply_screen(screen({'url':'https://example.org/jane','title':'Jane Doe','text':text}),self.p)
    def test_local_broader_trades_eligible_without_electrical(self):
        p=self.packet('Skilled trades recruiter\nAtlanta Georgia\n## About\nI am open to work. HVAC construction recruiting.')
        self.assertEqual(p['classification'],'C — Provisional')
        self.assertFalse(p['signal_date_confirmed'])
    def test_hiring_ad_is_not_personal_interest(self):
        p=self.packet('Electrical recruiter Atlanta Georgia. We are hiring electricians. Candidates open to work apply now.')
        self.assertEqual(p['classification'],'Rejected')
        self.assertFalse(p['possible_recruiting_signal'])
    def test_out_of_area_not_accepted_by_employer_boilerplate(self):
        p=self.packet('Construction recruiter\nDallas Texas\n## About\nOpen to work. Skilled trades.\n## Experience\nCompany has an Atlanta office.')
        self.assertEqual(p['classification'],'Rejected')
    def test_explicit_atlanta_relocation_exception(self):
        p=self.packet('Construction recruiter\nDallas Texas\n## About\nI am relocating to Atlanta. Open to work recruiting skilled trades.')
        self.assertEqual(p['classification'],'C — Provisional')
        self.assertIsNotNone(p['relocation_excerpt'])
    def test_generic_relocation_not_exception(self):
        p=self.packet('Construction recruiter\nDallas Texas\n## About\nOpen to work. Skilled trades. Willing to relocate nationwide.')
        self.assertEqual(p['classification'],'Rejected')
    def test_relocation_alone_not_job_seeking(self):
        p=self.packet('Construction recruiter\nDallas Texas\n## About\nI am moving to Atlanta. Skilled trades recruiter.')
        self.assertFalse(p['possible_recruiting_signal'])
        self.assertNotEqual(p['classification'],'C — Provisional')
    def test_negation(self):
        self.assertFalse(self.packet('Construction recruiter Atlanta. Not open to work. Skilled trades.')['possible_recruiting_signal'])
    def test_all_queries_local_and_recruiter_specific(self):
        s=new_state();s.update(job_profile=self.p,search_as_of='2026-09-10')
        places=[x.removesuffix(' Georgia').lower() for x in self.p['locations']]+['atlanta']
        for i in range(240):
            s['discovery_index']=i;s['queries']=[{}]*i
            q=next_plan(s);text=q['query'].lower()
            self.assertTrue(any(x in text for x in ('recruit','staffing','talent acquisition')))
            self.assertTrue(any(x in text for x in places))
            self.assertNotIn('nationwide',text)
            self.assertNotIn('roadtechs',text)
            if q['options'].get('start_date'):self.assertEqual(q['options']['start_date'],'2026-08-11')
    def test_followup_targets_source_without_using_url_as_search_term(self):
        s=new_state();s.update(job_profile=self.p,search_as_of='2026-09-10',queries=[{'query':'a'},{'query':'b'}])
        p=self.packet('Construction recruiter Atlanta. Open to work. Skilled trades.')
        s['packets'][p['source_url']]=p
        q=next_plan(s)
        self.assertEqual(q['target'],p['source_url'])
        self.assertNotIn(p['source_url'],q['query']);self.assertIn(p['name_hint'],q['query'])
        # With a content route covering the host, the first follow-up fetches the page itself.
        s['content_routes']={'exa_contents':['example.org']}
        q=next_plan(s)
        self.assertEqual((q['query'],q['content_provider'],q['strategy']),(p['source_url'],'exa_contents','profile_content'))
