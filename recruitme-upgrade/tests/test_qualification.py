import copy
import datetime as dt
import json
import sqlite3
import unittest

from recruitme import data
from recruitme.budget import StopRun
from recruitme.qualification import assess_candidate, ranking_key

TODAY = '2026-09-13'


def record():
    facts = {'name': 'SYNTHETIC PERSON', 'role': 'Commercial electrician',
             'commercial_experience': True, 'years_experience': 6,
             'location': 'Marietta, GA', 'availability_signal': 'I am open to work'}
    return {'identity_key': 'synthetic', 'reviewed_by_human': True, 'facts': facts,
        'evidence': [{'field': f, 'value': v, 'status': 'CLAIMED',
            'source_url': 'https://example.org/person', 'excerpt': f'{f}: {v}',
            'retrieved_at': TODAY, 'independence_group': 'person',
            'knowledge_status': 'VERIFIED_FACT', 'human_verified': True,
            'source_type': 'first_party', 'subject_confirmed': True,
            'original_date': '2026-09-01', 'original_date_verified': True}
            for f, v in facts.items()],
        'contacts': [{'route_type': 'professional_profile', 'value': 'https://example.org/person',
            'source_url': 'https://example.org/person', 'retrieved_at': TODAY,
            'public_professional': True, 'status': 'CLAIMED'}]}


def evaluate(r=None, **kwargs):
    r = r or record()
    return assess_candidate(r['facts'], r['evidence'], r['contacts'], as_of=kwargs.get('as_of', TODAY))


def change(r, field, value):
    r['facts'][field] = value
    next(e for e in r['evidence'] if e['field'] == field)['value'] = value


class Qualification(unittest.TestCase):
    def test_strong_candidate_transparent_total(self):
        q = evaluate()
        self.assertEqual(q['classification'], 'FULLY_QUALIFIED')
        self.assertEqual(q['score'], 100)
        self.assertEqual(q['score'], sum(c['score'] for c in q['components'].values()))
        self.assertEqual(q['confidence_score'], 100)
        self.assertEqual(q['blockers'], [])
        self.assertTrue(q['human_review_required'])
        self.assertFalse(q['outreach_enabled'])

    def test_no_evidence_flat_facts_never_establish_facts(self):
        q = assess_candidate(record()['facts'], as_of=TODAY)
        self.assertEqual(q['score'], 0)
        self.assertTrue(all(c['knowledge_status'] == 'UNKNOWN' for c in q['claims'].values()))

    def test_legacy_claims_and_corroboration_are_not_verified(self):
        for status in ('CLAIMED', 'CORROBORATED'):
            r = record()
            for e in r['evidence']:
                e.pop('human_verified'); e['status'] = status
            q = evaluate(r)
            self.assertEqual(q['classification'], 'RESEARCH_ONLY')
            self.assertTrue(all(c['knowledge_status'] == 'REASONABLE_INFERENCE' for c in q['claims'].values()))

    def test_experience_boundaries_and_invalid_numbers(self):
        for years, expected in [(2, 9), (2.99, 9), (3, 15), (10, 15), (10.01, 9), (12, 9),
                                (13, 3.75), (0, 3.75), (-1, 0), (81, 0), (True, 0),
                                ('6', 0), (None, 0), (float('nan'), 0), (float('inf'), 0)]:
            with self.subTest(years=years):
                r = record(); change(r, 'years_experience', years)
                q = evaluate(r)
                self.assertEqual(q['components']['experience']['score'], expected)
                if expected != 15: self.assertNotEqual(q['classification'], 'FULLY_QUALIFIED')

    def test_trade_requires_commercial_and_field_role(self):
        for role, commercial in [('Electrical engineer', True), ('Electrical recruiter', True),
                                 ('Electrician', False), ('Electrician', None), ('Not an electrician', True)]:
            r = record(); change(r, 'role', role); change(r, 'commercial_experience', commercial)
            self.assertEqual(evaluate(r)['components']['trade_fit']['score'], 0)

    def test_identity_required(self):
        r = record(); r['evidence'] = [e for e in r['evidence'] if e['field'] != 'name']
        self.assertNotEqual(evaluate(r)['classification'], 'FULLY_QUALIFIED')

    def test_missing_ambiguous_and_outside_locations(self):
        for location in (None, '', 'Georgia', 'Savannah, GA', 'Atlanta, TX', 'Decatur, AL', 'Marietta'):
            with self.subTest(location=location):
                r = record(); change(r, 'location', location)
                q = evaluate(r)
                self.assertEqual(q['components']['geography']['score'], 0)
                self.assertNotEqual(q['classification'], 'FULLY_QUALIFIED')

    def test_metro_localities(self):
        for location in ('Atlanta, Georgia', 'Metro Atlanta', 'Covington, GA', 'Norcross, Georgia'):
            r = record(); change(r, 'location', location)
            self.assertEqual(evaluate(r)['components']['geography']['score'], 15)

    def test_recency_boundaries(self):
        for age, points in [(0, 10), (30, 10), (31, 6), (90, 6), (91, 0), (366, 0), (-1, 0)]:
            with self.subTest(age=age):
                r = record(); r['evidence'][-1]['original_date'] = (dt.date.fromisoformat(TODAY)-dt.timedelta(days=age)).isoformat()
                q = evaluate(r)
                self.assertEqual(q['components']['freshness']['score'], points)
                self.assertEqual(q['classification'] == 'FULLY_QUALIFIED', 0 <= age <= 90)
                if not 0 <= age <= 90: self.assertLessEqual(q['confidence_score'], 49)

    def test_missing_invalid_or_unrelated_dates(self):
        for value in (None, '', 'recently', '2026-02-30'):
            r = record(); r['facts']['signal_date'] = TODAY
            r['evidence'][-1]['original_date'] = value
            self.assertEqual(evaluate(r)['components']['freshness']['score'], 0)

    def test_subject_and_date_review_required(self):
        for key in ('subject_confirmed', 'original_date_verified', 'human_verified'):
            r = record(); r['evidence'][-1][key] = False
            self.assertEqual(evaluate(r)['classification'], 'RESEARCH_ONLY')

    def test_no_signal_and_weak_signals(self):
        for signal in (None, '', 'project ending', 'laid off', 'relocating', 'my resume', 'recruiting electricians'):
            r = record(); change(r, 'availability_signal', signal)
            q = evaluate(r)
            self.assertEqual(q['classification'], 'RESEARCH_ONLY')
            self.assertLessEqual(q['score'], 69)

    def test_negation_and_hired_updates(self):
        for text in ('Not open to work', 'No longer looking for work', 'Accepted a new job', 'I got hired'):
            r = record(); e = copy.deepcopy(r['evidence'][-1]); e.update(value=text, excerpt=text, source_url='https://example.org/update')
            r['evidence'].append(e)
            q = evaluate(r)
            self.assertEqual(q['components']['job_change']['score'], 0)
            self.assertTrue(q['claims']['availability_signal']['conflict'])

    def test_duplicate_evidence_does_not_inflate(self):
        r = record(); baseline = evaluate(r)
        r['evidence'] *= 10
        self.assertEqual(evaluate(r), baseline)

    def test_contradictory_claims_block_and_order_does_not_matter(self):
        for field, value in [('location', 'Savannah, GA'), ('years_experience', 1), ('commercial_experience', False)]:
            r = record(); e = copy.deepcopy(next(e for e in r['evidence'] if e['field'] == field))
            e.update(value=value, source_url='https://example.org/conflict'); r['evidence'].append(e)
            q = evaluate(r)
            self.assertTrue(q['claims'][field]['conflict'])
            self.assertNotEqual(q['classification'], 'FULLY_QUALIFIED')
            r['evidence'].reverse()
            self.assertEqual(evaluate(r), q)

    def test_source_quality_downgrades(self):
        for source, maximum in [('professional_profile', 100), ('secondary', 69), ('search_snippet', 69), ('unknown', 69)]:
            r = record()
            for e in r['evidence']: e['source_type'] = source
            q = evaluate(r)
            self.assertLessEqual(q['score'], maximum)
            if source != 'professional_profile': self.assertNotEqual(q['classification'], 'FULLY_QUALIFIED')

    def test_invalid_unknown_future_evidence(self):
        for key, value in [('status', 'UNKNOWN'), ('retrieved_at', 'invalid'), ('retrieved_at', '2099-01-01'),
                           ('source_url', 'javascript:alert(1)'), ('excerpt', '')]:
            r = record()
            for e in r['evidence']: e[key] = value
            q = evaluate(r)
            self.assertEqual(q['confidence_score'], 0)

    def test_contact_validation_and_expiry(self):
        for key, value in [('status', 'UNKNOWN'), ('retrieved_at', '2025-01-01'), ('retrieved_at', '2099-01-01'),
                           ('value', ''), ('source_url', 'file:///secret'), ('route_type', 'personal_phone'),
                           ('source_url', 'http://127.0.0.1/person'), ('value', 'http://localhost/person')]:
            r = record(); r['contacts'][0][key] = value
            q = evaluate(r)
            self.assertEqual(q['components']['contact']['score'], 0)
            self.assertNotEqual(q['classification'], 'FULLY_QUALIFIED')

    def test_ranking_stable_and_qualified_first(self):
        strong = {'id': 'b', 'qualification': evaluate()}
        r = record(); r['evidence'][-1]['original_date'] = '2025-01-01'
        weak = {'id': 'a', 'qualification': evaluate(r)}
        tie = dict(strong, id='a')
        self.assertEqual([x['id'] for x in sorted([strong, weak, tie], key=ranking_key)], ['a', 'b', 'a'])

    def test_evaluation_is_pure(self):
        r = record(); before = copy.deepcopy(r); evaluate(r)
        self.assertEqual(r, before)

    def test_common_seeking_phrasings_qualify(self):
        for signal in ('#OpenToWork', 'opentowork', 'Actively seeking new opportunities', 'Looking for a new opportunity',
                       'Available immediately', 'Looking for my next project', 'Back on the job market', 'Job hunting again',
                       'Interested in your electrician position'):
            with self.subTest(signal=signal):
                r = record(); change(r, 'availability_signal', signal)
                self.assertEqual(evaluate(r)['classification'], 'FULLY_QUALIFIED')

    def test_no_longer_with_employer_is_not_negative(self):
        r = record(); change(r, 'availability_signal', 'No longer with ABC Electric as of Friday, open to work')
        q = evaluate(r)
        self.assertEqual(q['classification'], 'FULLY_QUALIFIED')
        self.assertFalse(q['claims']['availability_signal']['conflict'])

    def test_reviewer_polarity_overrides_regex(self):
        r = record(); change(r, 'availability_signal', 'Just got laid off, looking')
        self.assertEqual(evaluate(r)['classification'], 'RESEARCH_ONLY')
        r['evidence'][-1]['signal_polarity'] = 'POSITIVE_SEEKING'
        self.assertEqual(evaluate(r)['classification'], 'FULLY_QUALIFIED')
        r = record(); r['evidence'][-1]['signal_polarity'] = 'NEGATIVE_NOT_SEEKING'
        q = evaluate(r)
        self.assertEqual(q['components']['job_change']['score'], 0)
        self.assertTrue(q['claims']['availability_signal']['conflict'])
        r = record(); r['evidence'][-1]['signal_polarity'] = 'AMBIGUOUS'
        self.assertEqual(evaluate(r)['classification'], 'RESEARCH_ONLY')

    def test_profile_localities_pass_default_geography(self):
        for location in ('Chamblee, GA', 'Brookhaven, Georgia', 'DeKalb County, Georgia', 'Snellville GA', 'Newton County, GA'):
            with self.subTest(location=location):
                r = record(); change(r, 'location', location)
                self.assertEqual(evaluate(r)['components']['geography']['score'], 15)

    def test_policy_localities_replace_defaults(self):
        policy = {'localities': ['Savannah Georgia', 'Pooler Georgia']}
        r = record(); change(r, 'location', 'Savannah, GA')
        self.assertEqual(assess_candidate(r['facts'], r['evidence'], r['contacts'], as_of=TODAY, policy=policy)['classification'], 'FULLY_QUALIFIED')
        r = record()
        self.assertEqual(assess_candidate(r['facts'], r['evidence'], r['contacts'], as_of=TODAY, policy=policy)['components']['geography']['score'], 0)
        for bad in ({'localities': []}, {'localities': 'Atlanta'}, {'maximum_signal_age_days': 0}, {'maximum_signal_age_days': '30'}, {'years_minimum': 12, 'years_maximum': 10}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                assess_candidate(r['facts'], r['evidence'], r['contacts'], as_of=TODAY, policy=bad)

    def test_policy_signal_window_is_the_gate(self):
        policy = {'maximum_signal_age_days': 30}
        for age, qualified, points in [(30, True, 10), (31, False, 0), (45, False, 0)]:
            with self.subTest(age=age):
                r = record(); r['evidence'][-1]['original_date'] = (dt.date.fromisoformat(TODAY)-dt.timedelta(days=age)).isoformat()
                q = assess_candidate(r['facts'], r['evidence'], r['contacts'], as_of=TODAY, policy=policy)
                self.assertEqual(q['classification'] == 'FULLY_QUALIFIED', qualified)
                self.assertEqual(q['components']['freshness']['score'], points)
                if not qualified: self.assertIn('within 30 days', '; '.join(q['blockers']))

    def test_year_ceiling_can_be_preference_instead_of_gate(self):
        r = record(); change(r, 'years_experience', 15)
        self.assertNotEqual(evaluate(r)['classification'], 'FULLY_QUALIFIED')
        q = assess_candidate(r['facts'], r['evidence'], r['contacts'], as_of=TODAY, policy={'years_maximum_is_gate': False})
        self.assertEqual(q['classification'], 'FULLY_QUALIFIED')
        self.assertEqual(q['components']['experience']['score'], 3.75)
        change(r, 'years_experience', 2)
        self.assertNotEqual(assess_candidate(r['facts'], r['evidence'], r['contacts'], as_of=TODAY, policy={'years_maximum_is_gate': False})['classification'], 'FULLY_QUALIFIED')

    def test_policy_from_saved_profiles(self):
        from recruitme.qualification import policy_from_profile
        import pathlib
        covington = json.loads(pathlib.Path(__file__).resolve().parents[1].joinpath('profiles', 'covington-dual-experience-search.json').read_text())
        pol = policy_from_profile(covington)
        self.assertEqual(pol['maximum_signal_age_days'], 30)
        self.assertIn('Chamblee Georgia', pol['localities'])
        self.assertTrue(pol['years_maximum_is_gate'])
        self.assertIsNone(policy_from_profile(None))
        self.assertEqual(policy_from_profile({'locations': ['Atlanta Georgia']})['maximum_signal_age_days'], 90)


class QualificationStorage(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.db.row_factory = sqlite3.Row
        data.initialize(self.db)

    def tearDown(self):
        self.db.close()

    def test_import_report_and_reassessment_preserve_evidence(self):
        r = record(); cid = data.import_candidate(self.db, r)
        before = list(self.db.execute('SELECT * FROM evidence'))
        self.assertEqual(data.report(self.db, 'test', as_of=TODAY)['candidates'][0]['qualification']['classification'], 'FULLY_QUALIFIED')
        later = data.report(self.db, 'test', as_of='2027-01-01')['candidates'][0]
        self.assertEqual(later['qualification']['classification'], 'RESEARCH_ONLY')
        self.assertEqual(before, list(self.db.execute('SELECT * FROM evidence')))
        data.import_candidate(self.db, r)
        self.assertEqual(len(before), self.db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0])
        self.assertEqual(cid, later['id'])

    def test_agent_cannot_attest_verified_facts(self):
        r = record(); r.pop('reviewed_by_human'); r['reviewed_by_agent'] = True
        cid = data.import_candidate(self.db, r)
        q = data.candidate_assessment(self.db, cid, as_of=TODAY)
        self.assertEqual(q['classification'], 'RESEARCH_ONLY')
        self.assertTrue(all(c['knowledge_status'] == 'REASONABLE_INFERENCE' for c in q['claims'].values()))

    def test_reimport_does_not_hide_prior_conflict(self):
        r = record(); cid = data.import_candidate(self.db, r)
        change(r, 'location', 'Savannah, GA')
        e = next(e for e in r['evidence'] if e['field'] == 'location')
        e['excerpt'] = 'New conflicting residence'; e['source_url'] = 'https://example.org/new'
        data.import_candidate(self.db, r)
        self.assertTrue(data.candidate_assessment(self.db, cid, as_of=TODAY)['claims']['location']['conflict'])

    def test_changed_value_same_excerpt_rolls_back(self):
        r = record(); data.import_candidate(self.db, r)
        change(r, 'location', 'Savannah, GA')
        with self.assertRaises(StopRun): data.import_candidate(self.db, r)
        self.assertEqual(self.db.execute('SELECT location FROM candidates').fetchone()[0], 'Marietta, GA')

    def test_legacy_ab_assessment_cannot_bypass_signal_gate(self):
        r = record(); r['evidence'][-1]['original_date'] = '2025-01-01'
        r['assessment'] = {'classification': 'A'}
        with self.assertRaises(StopRun): data.import_candidate(self.db, r)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM candidates').fetchone()[0], 0)

    def test_policy_persists_and_governs_reassessment(self):
        r = record(); r['evidence'][-1]['original_date'] = (dt.date.fromisoformat(TODAY)-dt.timedelta(days=45)).isoformat()
        cid = data.import_candidate(self.db, r, policy={'maximum_signal_age_days': 30})
        q = data.candidate_assessment(self.db, cid, as_of=TODAY)
        self.assertEqual(q['classification'], 'RESEARCH_ONLY')
        self.assertEqual(q['policy']['maximum_signal_age_days'], 30)
        self.assertEqual(data.report(self.db, 'test', as_of=TODAY)['candidates'][0]['qualification']['classification'], 'RESEARCH_ONLY')
        # Re-import without a policy keeps the stored one rather than reverting to defaults.
        data.import_candidate(self.db, r)
        self.assertEqual(data.candidate_assessment(self.db, cid, as_of=TODAY)['policy']['maximum_signal_age_days'], 30)
        other = record(); other['identity_key'] = 'default-policy'
        other['evidence'][-1]['original_date'] = r['evidence'][-1]['original_date']
        cid2 = data.import_candidate(self.db, other)
        self.assertEqual(data.candidate_assessment(self.db, cid2, as_of=TODAY)['classification'], 'FULLY_QUALIFIED')

    def test_review_annotations_persist(self):
        r = record(); r['evidence'][-1].update(signal_polarity='POSITIVE_SEEKING', date_basis='post_timestamp', identity_confidence='confirmed')
        change(r, 'availability_signal', 'Just got laid off, looking')
        cid = data.import_candidate(self.db, r)
        self.assertEqual(data.candidate_assessment(self.db, cid, as_of=TODAY)['classification'], 'FULLY_QUALIFIED')
        stored = [json.loads(a['metadata_json']) for a in self.db.execute('SELECT metadata_json FROM qualification_annotations')]
        self.assertTrue(any(a.get('date_basis') == 'post_timestamp' and a.get('identity_confidence') == 'confirmed' for a in stored))

    def test_legacy_database_initialization_additive(self):
        r = record()
        for e in r['evidence']:
            for k in ('knowledge_status', 'human_verified', 'source_type'): e.pop(k)
        cid = data.import_candidate(self.db, r)
        data.initialize(self.db)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM candidates').fetchone()[0], 1)
        self.assertNotEqual(data.candidate_assessment(self.db, cid, as_of=TODAY)['classification'], 'FULLY_QUALIFIED')


if __name__ == '__main__': unittest.main()
