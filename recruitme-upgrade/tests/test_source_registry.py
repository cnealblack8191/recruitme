import unittest
from recruitme.source_registry import routes, apply_route, coverage
from recruitme.search_options import validate_options

class SourceRegistryTests(unittest.TestCase):
    def test_every_recruiter_route_both_providers_and_local_scope(self):
        selected=routes('recruiter'); seen={}
        for i in range(len(selected)*2):
            p=apply_route(dict(query='construction recruiter open to work Atlanta',provider='exa_keyed',options={'exclude_domains':['linkedin.com','facebook.com'],'start_date':'2026-08-11','end_date':'2026-09-10'}),i,'recruiter')
            self.assertIn('Atlanta',p['query'])
            # Legacy date options are dropped; only a recency_filter hint on a dated-post domain re-applies them.
            self.assertNotIn('start_date',p['options'])
            self.assertEqual(p['options']['exclude_domains'],[])
            validate_options(p['options'])
            seen.setdefault(p['source_family'],set()).add(p['provider'])
        self.assertTrue(all(len(v)==2 for v in seen.values()))
        self.assertIn('linkedin',seen)
        self.assertNotIn('roadtechs',seen)
    def test_default_rotation_excludes_low_yield_routes_but_keeps_them_selectable(self):
        from recruitme.source_registry import SOURCES
        default={s[0] for s in routes('recruiter')}
        for low in ('facebook_public','instagram_public','x_public','medium','substack','ere','shrm_atlanta','recruiting_daily'):
            self.assertNotIn(low,default)
            self.assertEqual(routes('recruiter',[low])[0][0],low)
        for kept in ('open_web','linkedin','postjobfree','jobcase','indeed_public','craigslist_atlanta','reddit'):
            self.assertIn(kept,default)
        self.assertEqual(len(routes('field')),len({s[0] for s in SOURCES if s[3] and s[2] in ('all','field')}))
        with self.assertRaises(ValueError):routes('field',['shrm_atlanta'])
    def test_recency_hint_only_dates_dated_post_domains(self):
        hint={'start_date':'2026-08-18','end_date':'2026-09-17','days':30}
        by_id={s[0]:i for i,s in enumerate(routes('field'))}
        dated=apply_route(dict(query='q',provider='tavily',options={},recency_filter=hint),by_id['postjobfree'],'field')
        self.assertEqual((dated['options']['start_date'],dated['options']['end_date']),('2026-08-18','2026-09-17'))
        for undated_id in ('linkedin','open_web','indeed_public'):
            p=apply_route(dict(query='q',provider='tavily',options={},recency_filter=hint),by_id[undated_id],'field')
            self.assertNotIn('start_date',p['options'],undated_id)
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
