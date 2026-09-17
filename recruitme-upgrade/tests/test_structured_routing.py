import unittest
from test_foundation import configuration
from recruitme.autonomous import structured_providers, web_policy_plan, new_state

class StructuredRouting(unittest.TestCase):
    def test_only_enabled_approved_credentialed_people_routes(self):
        c=configuration()
        c['providers']['pdl_free']={'enabled':True,'approved':True,'operations':{'search':'0'},'run_limit_usd':'1','poc_limit_usd':'1','run_query_limit':5,'poc_query_limit':5}
        c['providers']['apollo']={'enabled':True,'approved':False,'operations':{'search':'0'}}
        c['providers']['brave']={'enabled':True,'approved':True,'operations':{'search':'0.005'}}
        from unittest.mock import patch
        with patch('recruitme.plugins.PDLFree.credentials_available',return_value=True):
            self.assertEqual(structured_providers(c),['pdl_free'])
        with patch('recruitme.plugins.PDLFree.credentials_available',return_value=False):
            self.assertEqual(structured_providers(c),[])
    def test_web_policy_never_rewrites_structured_plan(self):
        s=new_state();s.update(job_profile={'id':'x','tracks':[{'id':'t','roles':['recruiter']}],'locations':['Atlanta Georgia'],'fit_terms':['electrical']},search_as_of='2026-09-16')
        plan=dict(query='{"job_title":"recruiter"}',purpose='discovery',strategy='dual_structured_transition',target=None,provider='pdl_free',options={},source_family='structured_people')
        out=web_policy_plan(s,plan,{'paid_enabled':False})
        self.assertEqual(out['provider'],'pdl_free');self.assertEqual(out['query'],plan['query'])
        web=dict(query='recruiter Atlanta',purpose='discovery',strategy='x',target=None,provider='exa_keyed',options={})
        self.assertNotIn('provider',web_policy_plan(s,web,{'paid_enabled':False}))

if __name__=='__main__':unittest.main()
