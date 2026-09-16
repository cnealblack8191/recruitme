import json
import unittest
from unittest.mock import patch
from test_exa_keyed import Keyed
from recruitme.plugins import Brave,ExaPeople,SerpAPI,TavilyExtract,PDLFree,BrightDataProfile,disabled_config
from recruitme.budget import StopRun

class Plugins(Keyed):
    def configure(self,cls):
        self.cfg['providers'][cls.name]={**disabled_config()[cls.name],'enabled':True,'approved':True}
    def test_brave_reserved_before_get_and_normalized(self):
        self.configure(Brave);parent=self
        class Opener:
            def open(self,req,timeout):
                parent.assertEqual(parent.l.total(),5000)
                parent.assertTrue(req.full_url.startswith('https://api.search.brave.com/'))
                parent.assertNotIn('SYNTHETIC',req.full_url)
                class Response:
                    def __enter__(self):return self
                    def __exit__(self,*a):pass
                    def read(self,*a):return json.dumps({'web':{'results':[{'title':'A','url':'https://example.com/a','description':'First','extra_snippets':['Second']}]}}).encode()
                return Response()
        with patch('recruitme.plugins.secret',return_value='SYNTHETIC-SECRET'):
            r=Brave(self.l,'keyed',lambda:None,Opener()).search('Atlanta recruiter')
        self.assertIn('Second',r['content'][0]['text']);self.assertEqual(self.l.total(),5000)
    def test_unknown_prices_and_unsupported_filters_never_dispatch(self):
        self.configure(Brave)
        with patch('recruitme.plugins.secret',return_value='SYNTHETIC-SECRET'):
            c=Brave(self.l,'keyed',lambda:None,self.opener())
            with self.assertRaises(StopRun):c.search('test',options={'start_date':'2026-09-01'})
        self.assertEqual(self.l.total(),0);self.assertEqual(self.calls,0)
    def test_people_category_does_not_take_date_or_excluded_domain(self):
        c=ExaPeople(self.l,'keyed',lambda:None)
        self.assertEqual(c.request_body('test',5,{})['category'],'people')
        for o in ({'start_date':'2026-09-01'},{'exclude_domains':['example.com']}):
            with self.assertRaises(StopRun):c.request_body('test',5,o)
    def test_extraction_is_single_allowlisted_https_url(self):
        self.configure(TavilyExtract);c=TavilyExtract(self.l,'keyed',lambda:None)
        self.cfg['providers']['tavily_extract']['allowed_domains']=['linkedin.com']
        self.assertEqual(c.request_body('https://www.linkedin.com/in/test',1,{})['urls'],['https://www.linkedin.com/in/test'])
        for url in ('http://linkedin.com/in/a','https://linkedin.com.evil.test/a','https://127.0.0.1/a','https://user:pw@linkedin.com/a'):
            with self.assertRaises(StopRun):c.request_body(url,1,{})
        with self.assertRaises(StopRun):c.request_body('https://linkedin.com/in/a',2,{})
    def test_pdl_free_requires_verified_plan_and_lifetime_record_bound(self):
        self.configure(PDLFree);c=PDLFree(self.l,'keyed',lambda:None)
        with self.assertRaises(StopRun):c.pricing(10)
        self.cfg['providers']['pdl_free'].update(account_plan='free',paid_overages_disabled=True)
        self.assertEqual(c.pricing(10)[0],0)
        self.cfg['providers']['pdl_free']['poc_query_limit']=11
        with self.assertRaises(StopRun):c.pricing(10)
    def test_defaults_never_enable_sources(self):
        self.assertTrue(all(not p['enabled'] and not p['approved'] for p in disabled_config().values()))
    def test_bright_data_does_not_retry_async_or_import_contacts(self):
        c=BrightDataProfile(self.l,'keyed',lambda:None)
        with self.assertRaises(StopRun):c.response_envelope({'snapshot_id':'pending'})
        r=c.response_envelope([{'url':'https://www.linkedin.com/in/example','name':'Example','email':'private@example.com','experience':[{'title':'Electrician','start_date':'2010','end_date':'2020'}]}])
        self.assertIn('Electrician',r['results'][0]['text']);self.assertNotIn('private@example.com',json.dumps(r))

class CareerRegression(unittest.TestCase):
    def packet(self,text,title='Jane Smith - Recruiter'):
        from recruitme.autonomous import screen
        from recruitme.dual_experience import apply_screen
        return apply_screen(screen({'title':title,'text':text,'url':'https://www.linkedin.com/in/jane-smith'}),{'locations':['Atlanta Georgia']})
    def test_dates_on_separate_lines(self):
        p=self.packet('Recruiter Atlanta Georgia\n## Experience\nRecruiter - ABC Staffing\n2020 - Present\nElectrician - ABC Electric\n2010 - 2020')
        self.assertTrue(p['dual_experience_hint']);self.assertFalse(p['grade_verified'])
    def test_employer_recruiting_word_not_a_job(self):
        p=self.packet('Electrician at Marine Corps Recruiting\nGeorgia\n## Experience\nElectrician\n2010 - 2020','Jane Smith - Electrician')
        self.assertFalse(p['dual_experience_hint'])
    def test_liked_post_does_not_count_as_hr(self):
        p=self.packet('Recruiting Manager needed!\nLiked by Jane Smith\n\n# Jane Smith\nElectrical Foreman Atlanta Georgia\n## Experience\nElectrician\n2010 - 2020','Jane Smith - Foreman')
        self.assertFalse(p['dual_experience_hint'])
