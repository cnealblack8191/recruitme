import copy
import unittest

from recruitme.autonomous import consume, new_state, next_query, screen, web_policy_plan
from recruitme.discovery import annotate, date_status, page_key, plan, PLACES
from recruitme.profiles import discovery, broad_plan, next_plan
from recruitme.search_options import validate_options
import datetime


class DiscoveryTests(unittest.TestCase):
    def state(self):
        s=new_state()
        s.update(improved=True,search_as_of='2026-09-13',focus_month='September 2026')
        return s

    def profile(self):
        return dict(id='atlanta-test',version=1,locations=['Doraville Georgia','Atlanta Georgia'],
                    fit_terms=['commercial'],tracks=[dict(id='experienced',roles=['commercial electrician'])])

    def result(self, **kw):
        result=dict(url='https://example.org/person',title='Jane Doe - Electrician',
                    text='Commercial electrician with 8 years. Looking for work in Doraville Georgia. '
                         'Business email: jane@example.org',publishedDate='2026-09-01')
        result.update(kw)
        return result

    def packet(self, **kw):
        r=self.result(**kw)
        return annotate(screen(r),r,'2026-09-13T12:00:00+00:00')

    def test_local_diverse_bounded_queries_beyond_initial_batch(self):
        s=self.state();queries=[];strategies=set()
        for i in range(240):
            s['discovery_index']=i
            p=next_query(s);queries.append(p['query']);strategies.add(p['strategy'])
            self.assertTrue(any(place+' Georgia' in p['query'] for place in PLACES))
            self.assertLessEqual(len(p['query']),500)
            validate_options(p['options'])
            self.assertNotIn('hiring for immediate start',p['query'])
            s['queries'].append(p)
        self.assertEqual(len(set(queries)),240)
        self.assertEqual(len(strategies),4)

    def test_year_branch_covers_target_without_requiring_years_everywhere(self):
        queries=[plan(self.state(),i)['query'] for i in range(32)]
        for year in range(3,11):self.assertTrue(any(f'"{year} years"' in q for q in queries))
        self.assertEqual(sum('years' in q for q in queries),8)

    def test_date_windows_and_undated_branch(self):
        s=self.state()
        for i,days in enumerate((30,90,180,None)):
            options=plan(s,i)['options']
            if days is None:self.assertNotIn('start_date',options)
            else:
                self.assertEqual(options['end_date'],'2026-09-13')
                self.assertEqual(options['start_date'],(datetime.date(2026,9,13)-datetime.timedelta(days=days)).isoformat())

    def test_profile_and_broad_search_use_saved_geography(self):
        s=self.state();s['job_profile']=self.profile()
        s['job_profile']['locations']=['Savannah Georgia']
        for i in range(12):
            s['discovery_index']=i
            self.assertIn('Savannah Georgia',discovery(s,i)['query'])
            self.assertIn('Savannah Georgia',broad_plan(s,'tavily')['query'])

    def test_free_queries_vary_and_have_no_paid_provider_override(self):
        s=self.state();s['job_profile']=self.profile();queries=[]
        for i in range(40):
            s['discovery_index']=i
            p=web_policy_plan(s,next_query(s),{'paid_enabled':False})
            self.assertNotIn('provider',p);self.assertEqual(p['options'],{})
            queries.append(p['query']);s['queries'].append(p)
        self.assertGreater(len(set(queries)),30)

    def test_free_selected_source_is_not_silently_broadened(self):
        s=self.state();s['job_profile']=self.profile();s['job_profile']['source_ids']=['roadtechs']
        p=web_policy_plan(s,next_query(s),{'paid_enabled':False})
        self.assertEqual(p['options']['include_domains'],['roadtechs.com'])
        self.assertIn('site:roadtechs.com',p['query'])

    def test_pending_request_and_configuration_unchanged(self):
        s=self.state();s['pending']=dict(query='saved',provider='tavily',options={'start_date':'2026-01-01'})
        config={'paid_enabled':False,'default_run_limit_usd':'5'};before=copy.deepcopy(config)
        self.assertIs(web_policy_plan(s,{},config),s['pending'])
        self.assertEqual(config,before)

    def test_followups_use_observed_locality_without_confirming_identity(self):
        s=self.state();s['job_profile']=self.profile()
        packet=self.packet();s['packets'][packet['source_url']]=packet
        s['queries']=[{'query':'previous'}]*41
        p=next_plan(s)
        self.assertIn('"Jane Doe" Doraville Georgia',p['query'])
        self.assertEqual(p['target'],packet['source_url'])
        self.assertFalse(packet['identity_confirmed'])

    def test_annotations_do_not_change_scoring_or_classification(self):
        r=self.result();p=screen(r);before=copy.deepcopy(p)
        annotate(p,r,'2026-09-13')
        for key in before:self.assertEqual(before[key],p[key])
        evidence=p['discovery_evidence']
        self.assertIn('Doraville',evidence['local_place_mentions'])
        self.assertFalse(evidence['geography_confirmed'])
        self.assertTrue(evidence['electrical_experience_claims'][0]['target_range_hint'])
        self.assertEqual(evidence['signal_freshness'],'UNCONFIRMED')

    def test_year_claims_are_relevant_not_generic_tenure(self):
        for text in ('Commercial electrician. 8 years at a restaurant.',
                     'Commercial electrician. Founded in 2018.', 'Commercial electrician since 2019.'):
            self.assertEqual(self.packet(text=text)['discovery_evidence']['electrical_experience_claims'],[])
        for text in ('3-10 years electrical construction','10+ years electrical construction','12 years electrician'):
            claims=self.packet(text=text)['discovery_evidence']['electrical_experience_claims']
            self.assertEqual(claims[0]['target_range_hint'],text.startswith('3-10'))

    def test_freshness_missing_invalid_future_and_stale(self):
        today=datetime.date(2026,9,13)
        for value,status in ((None,'UNKNOWN'),('bad','UNKNOWN'),('2027-01-01','FUTURE'),
                             ('2025-01-01','STALE'),('2026-09-12','RECENT')):
            self.assertEqual(date_status(value,today)['status'],status)

    def test_explicit_contact_route_preserves_source_and_ownership_uncertainty(self):
        routes=self.packet()['discovery_evidence']['contact_routes']
        email=next(r for r in routes if r['route_type']=='public_professional_email')
        self.assertEqual(email['value'],'jane@example.org')
        self.assertEqual(email['source_url'],'https://example.org/person')
        self.assertFalse(email['ownership_confirmed'])
        self.assertIn('Business email',email['excerpt'])

    def test_unlabelled_ad_and_third_party_contacts_not_extracted(self):
        for suffix in ('jane@example.org','We are hiring. Contact me at hr@example.org',
                       'My friend is looking for work. Contact me at friend@example.org'):
            routes=self.packet(text='Commercial electrician. '+suffix)['discovery_evidence']['contact_routes']
            self.assertFalse(any(r['route_type']=='public_professional_email' for r in routes))

    def test_apollo_provenance_not_a_contact_route_or_shared_identity(self):
        a='https://api.apollo.io/api/v1/mixed_people/api_search#person1'
        b=a.replace('person1','person2')
        self.assertNotEqual(page_key(a),page_key(b))
        self.assertEqual(self.packet(url=a)['discovery_evidence']['contact_routes'],[])

    def test_tracking_duplicates_preserve_each_observation(self):
        s=self.state();p=next_query(s)
        a=self.result(url='https://example.org/person?utm_source=search')
        b=self.result(url='https://example.org/person?fbclid=123')
        consume(s,p,{'provider':'tavily','provider_response':{'results':[a,b]}},'2026-09-13','raw.json')
        self.assertEqual(len(s['packets']),1);self.assertEqual(s['duplicates'],1)
        obs=next(iter(s['packets'].values()))['observations']
        self.assertEqual([o['original_url'] for o in obs],[a['url'],b['url']])
        self.assertEqual(obs[0]['provider'],'tavily')
        self.assertIn('discovery_evidence',obs[1])

    def test_distinct_identity_parameters_and_same_names_never_merge(self):
        s=self.state();p=next_query(s)
        results=[self.result(url='https://example.org/profile?id='+str(i)) for i in range(2)]
        consume(s,p,{'provider_response':{'results':results}},'2026-09-13','raw.json')
        self.assertEqual(len(s['packets']),2)

    def test_old_checkpoint_tracking_alias_merges_and_contradiction_survives(self):
        s=self.state();p=next_query(s)
        old=self.result(url='https://example.org/person?utm_source=old')
        packet=screen(old);packet['observations']=[];s['packets'][old['url']]=packet
        new=self.result(text='Commercial electrician. Looking for work. I got hired.')
        consume(s,p,{'provider_response':{'results':[new]}},'2026-09-13','new.json')
        self.assertEqual(len(s['packets']),1)
        self.assertTrue(s['packets'][old['url']]['contradiction_flag'])
        self.assertEqual(s['packets'][old['url']]['classification'],'Passive Research Pool')


if __name__ == '__main__':unittest.main()
