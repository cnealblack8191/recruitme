import unittest
from recruitme.source_registry import routes, apply_route, coverage
from recruitme.search_options import validate_options

class SourceRegistryTests(unittest.TestCase):
    def test_every_recruiter_route_both_providers_and_local_scope(self):
        selected=routes('recruiter'); seen={}
        for i in range(len(selected)*2):
            p=apply_route(dict(query='construction recruiter open to work Atlanta',provider='exa_keyed',options={'exclude_domains':['linkedin.com','facebook.com'],'start_date':'2026-08-11','end_date':'2026-09-10'}),i,'recruiter')
            self.assertIn('Atlanta',p['query'])
            self.assertEqual(p['options']['start_date'],'2026-08-11')
            self.assertEqual(p['options']['exclude_domains'],[])
            validate_options(p['options'])
            seen.setdefault(p['source_family'],set()).add(p['provider'])
        self.assertTrue(all(len(v)==2 for v in seen.values()))
        self.assertIn('linkedin',seen)
        self.assertNotIn('roadtechs',seen)
    def test_config_selects_and_rejects_invalid_sources(self):
        self.assertEqual(routes('recruiter',['linkedin'])[0][0],'linkedin')
        for value in ([],['missing'],['roadtechs'],'linkedin'):
            with self.assertRaises(ValueError):routes('recruiter',value)
    def test_coverage_counts_empty_results_without_claiming_access(self):
        self.assertEqual(coverage([{'source_family':'linkedin','result_count':0},{'source_family':'linkedin','result_count':2}]),{'linkedin':{'completed_queries':2,'returned_pages':2}})

    def test_open_web_route_leaves_structured_people_adapters_eligible(self):
        from recruitme.plugins import ExaPeople, PDLFree, ApolloPeople, Coresignal
        p=apply_route(dict(query='former electrician recruiter Georgia',provider='exa_keyed',options={}),0,'recruiter')
        o=validate_options(p['options'])
        self.assertEqual(o,{})
        for cls in (ExaPeople,PDLFree,ApolloPeople,Coresignal):
            self.assertTrue(cls.accepts_options(o),cls.name)
        domain=apply_route(dict(query='q',provider='exa_keyed',options={}),1,'recruiter')
        self.assertEqual(list(validate_options(domain['options'])),['include_domains'])
        self.assertTrue(ExaPeople.accepts_options({'include_domains':['linkedin.com']}))
        self.assertFalse(ExaPeople.accepts_options({'include_domains':['postjobfree.com']}))
        self.assertFalse(PDLFree.accepts_options({'include_domains':['linkedin.com']}))
