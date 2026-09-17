"""Deterministic commercial-trade lead assessment; no discovery, network or hiring decisions."""
import datetime as dt
import json
import math
import ipaddress
import re
from urllib.parse import urlsplit

VERSION = 'commercial-atlanta-v2'
WEIGHTS = {'trade_fit': 25, 'experience': 15, 'geography': 15,
           'job_change': 20, 'freshness': 10, 'contact': 5, 'source_quality': 10}
FIELDS = ('name', 'role', 'commercial_experience', 'years_experience', 'location', 'availability_signal')
# Default metro Atlanta localities: the union of both saved profiles plus the
# original conservative list. A run policy may replace it with its own list.
DEFAULT_LOCALITIES = ('Atlanta', 'Marietta', 'Decatur', 'Doraville', 'Lawrenceville', 'Conyers', 'Covington',
                      'Roswell', 'Alpharetta', 'Sandy Springs', 'Smyrna', 'Duluth', 'Norcross', 'Dunwoody',
                      'Kennesaw', 'Tucker', 'Lithonia', 'Peachtree Corners', 'Chamblee', 'Brookhaven',
                      'Johns Creek', 'Stone Mountain', 'Snellville', 'Loganville', 'Lithia Springs',
                      'McDonough', 'Monroe', 'Social Circle', 'Cumming', 'Oxford', 'DeKalb County',
                      'Gwinnett County', 'Fulton County', 'Cobb County', 'Newton County', 'Rockdale County')
DEFAULT_POLICY = {'localities': None, 'maximum_signal_age_days': 90,
                  'years_minimum': 3, 'years_maximum': 10, 'years_maximum_is_gate': True,
                  'role_kind': 'commercial_electrician'}
ROLE_KINDS = ('commercial_electrician', 'electrical_recruiter')
HR_TITLE = re.compile(r'\b(recruiter|recruiting|recruitment|talent acquisition|human resources|HR (?:manager|generalist|specialist|coordinator|business partner)|staffing manager|workforce development)\b', re.I)
POLARITIES = ('POSITIVE_SEEKING', 'NEGATIVE_NOT_SEEKING', 'AMBIGUOUS')


def metro_pattern(localities=None):
    names = set()
    for loc in (localities or DEFAULT_LOCALITIES):
        name = re.sub(r'\s*,?\s*(?:Georgia|GA)\s*$', '', str(loc).strip(), flags=re.I)
        if name: names.add(name)
    ordered = sorted((re.escape(n) for n in names), key=len, reverse=True)
    return re.compile(r'\b(' + '|'.join(ordered) + r')\b', re.I)


METRO = metro_pattern()
TRADE = re.compile(r'\b(electrician|wireman|electrical (foreman|superintendent|apprentice|installer))\b', re.I)
# Statements a person makes about wanting work. Layoff, relocation or résumé
# mentions alone stay weak; a reviewer can override with signal_polarity.
POSITIVE = re.compile(r'(?:#\s*)?\b(?:open ?to ?work|seeking (?:employment|work)|actively (?:seeking|looking)|'
                      r'looking for (?:work|a job|(?:a |my )?(?:new |next |another )?(?:role|job|opportunity|position|employer|project|company))|'
                      r'seeking (?:a |my |another )?(?:new |next )?(?:role|job|opportunit(?:y|ies)|position|employer|project)|'
                      r'available (?:for (?:work|hire)|immediately|to start)|ready (?:for|to start) (?:a )?new (?:opportunity|role|job|challenge)|'
                      r'(?:on|in) the (?:job )?market|job (?:hunting|search(?:ing)?)|applied for (?:this|the|your) (?:position|job|role)|'
                      r'interested in (?:this|the|your|new) (?:[a-z-]+ )?(?:position|job|role|opening|opportunit(?:y|ies)))\b', re.I)
NEGATIVE = re.compile(r'\b(?:not (?:currently )?(?:open|looking|seeking|available|interested)|'
                      r'no longer (?:looking|seeking|available|open|interested|on the market)|'
                      r'accepted (?:a |an |the |my )?(?:new )?(?:offer|job|position|role)|got hired|(?:was|been) hired|'
                      r'(?:started|starting) (?:a |my )?new (?:job|position|role)|found (?:a |my )?(?:new )?(?:job|position)|'
                      r'off the market)\b', re.I)
QUALITY = {'first_party': 1.0, 'first_party_submission': 1.0, 'official_record': 1.0, 'professional_profile': .8,
           'secondary': .5, 'search_snippet': .25, 'unknown': .0}


def date(value):
    try:
        if not isinstance(value, str): return None
        return dt.date.fromisoformat(value) if len(value) == 10 else dt.datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(dt.timezone.utc).date()
    except (ValueError, TypeError, OverflowError):
        return None


def public_url(value):
    try:
        u = urlsplit(value)
        host = u.hostname or ''
        if not host or '.' not in host or host.endswith(('.local', '.internal', '.localhost')):
            return False
        try:
            if not ipaddress.ip_address(host).is_global: return False
        except ValueError:
            pass
        return u.scheme in ('https', 'http') and not u.username and not u.password
    except (ValueError, TypeError):
        return False


def normalize_policy(policy=None):
    """Run-specific gates: localities, signal window, relevant-year range."""
    p = dict(DEFAULT_POLICY)
    for k, v in (policy or {}).items():
        if k in p and v is not None: p[k] = v
    if p['localities'] is not None:
        if not isinstance(p['localities'], (list, tuple)) or not p['localities'] or any(not isinstance(x, str) or not x.strip() for x in p['localities']):
            raise ValueError('Policy localities must be a nonempty list of names')
    window = p['maximum_signal_age_days']
    if type(window) is not int or not 1 <= window <= 365: raise ValueError('Signal window must be 1-365 days')
    lo, hi = p['years_minimum'], p['years_maximum']
    if type(lo) not in (int, float) or type(hi) not in (int, float) or not 0 <= lo <= hi <= 80: raise ValueError('Invalid relevant-year range')
    p['years_maximum_is_gate'] = bool(p['years_maximum_is_gate'])
    if p['role_kind'] not in ROLE_KINDS: raise ValueError('Unknown role kind')
    return p


def role_kind_for(profile):
    roles = ' '.join(r for t in (profile.get('tracks') or []) for r in (t.get('roles') or []) if isinstance(r, str))
    return 'electrical_recruiter' if HR_TITLE.search(roles) else 'commercial_electrician'


def policy_from_profile(profile):
    """Read the saved job profile's qualification policy; absent fields keep defaults."""
    if not isinstance(profile, dict): return None
    qp = profile.get('qualification_policy') or {}
    years = qp.get('relevant_years') or {}
    return normalize_policy({'localities': profile.get('locations') or None,
                             'maximum_signal_age_days': qp.get('maximum_signal_age_days'),
                             'years_minimum': years.get('minimum'), 'years_maximum': years.get('maximum'),
                             'years_maximum_is_gate': years.get('maximum_is_gate'),
                             'role_kind': qp.get('role_kind') or role_kind_for(profile)})


def signal_polarity(e):
    """Reviewer-selected polarity wins; regexes only propose when it is absent."""
    explicit = e.get('signal_polarity')
    if explicit in POLARITIES: return explicit
    text = str(e.get('value')) + ' ' + str(e.get('excerpt'))
    if NEGATIVE.search(text): return 'NEGATIVE_NOT_SEEKING'
    if POSITIVE.search(str(e.get('value'))): return 'POSITIVE_SEEKING'
    return 'AMBIGUOUS'


def assess_candidate(facts, evidence=(), contacts=(), *, as_of=None, policy=None):
    """Only per-evidence human attestations establish VERIFIED_FACT.

    Legacy CLAIMED/CORROBORATED rows remain inferences. Independence and repeated
    snippets never turn an inference into a verified fact. Scores are policy
    indicators, not calibrated probabilities of job acceptance.
    """
    today = date(as_of) if as_of is not None else dt.datetime.now(dt.timezone.utc).date()
    if today is None: raise ValueError('Invalid assessment date')
    pol = normalize_policy(policy)
    metro = metro_pattern(pol['localities']) if pol['localities'] else METRO
    window = pol['maximum_signal_age_days']; full_credit = min(30, window)
    lo, hi = pol['years_minimum'], pol['years_maximum']
    rows = []
    seen = set()
    for raw in evidence:
        e = dict(raw)
        key = (e.get('field'), json.dumps(e.get('value'), sort_keys=True), e.get('source_url'), e.get('excerpt'))
        if key in seen: continue
        seen.add(key)
        observed = date(e.get('retrieved_at'))
        if e.get('status') not in ('CLAIMED', 'CORROBORATED') or not public_url(e.get('source_url')) or not e.get('excerpt') or observed is None or observed > today:
            continue
        e['quality'] = QUALITY.get(e.get('source_type'), 0)
        # A human attestation verifies a claim. The one exception: the act of applying,
        # recorded by ECI's own portal with its server timestamp, verifies the seeking
        # signal alone; name, role, years and location stay the applicant's claims.
        system_recorded = (e.get('source_type') == 'first_party_submission' and e.get('system_recorded') is True
                           and e.get('field') == 'availability_signal')
        e['knowledge'] = ('VERIFIED_FACT' if (e.get('human_verified') is True or system_recorded)
                          and e.get('knowledge_status') == 'VERIFIED_FACT' and e['quality'] >= .8
                          else 'REASONABLE_INFERENCE')
        rows.append(e)

    claims = {}
    for field in FIELDS:
        matching = [e for e in rows if e.get('field') == field and e.get('value') is not None]
        values = {json.dumps(e['value'], sort_keys=True) for e in matching}
        conflict = len(values) > 1 and field != 'availability_signal'
        best = max(matching, key=lambda e: (e['knowledge'] == 'VERIFIED_FACT', e['quality']), default=None)
        claims[field] = {'knowledge_status': 'UNKNOWN' if conflict or not best else best['knowledge'],
                         'value': None if conflict or not best else best['value'],
                         'conflict': conflict, 'source_urls': sorted({e['source_url'] for e in matching}),
                         'evidence_ids': [e['id'] for e in matching if 'id' in e],
                         'source_quality': 0 if conflict or not best else best['quality']}
    components = {}

    def add(key, fraction, fields, reason):
        states = [claims[f]['knowledge_status'] for f in fields]
        state = 'UNKNOWN' if 'UNKNOWN' in states else ('REASONABLE_INFERENCE' if 'REASONABLE_INFERENCE' in states else 'VERIFIED_FACT')
        factor = {'UNKNOWN': 0, 'REASONABLE_INFERENCE': .5, 'VERIFIED_FACT': 1}[state]
        components[key] = {'score': round(WEIGHTS[key] * fraction * factor, 2), 'maximum': WEIGHTS[key],
                           'knowledge_status': state, 'reason': reason, 'fields': list(fields)}

    role = str(claims['role']['value'])
    commercial = str(claims['commercial_experience']['value']).lower() in ('yes', 'true')
    if pol['role_kind'] == 'electrical_recruiter':
        # Dual-experience role: a recruiting/HR title, with confirmed hands-on electrical
        # field employment recorded in the commercial_experience claim.
        trade = bool(HR_TITLE.search(role)) and not bool(re.search(r'\b(not|never)\b', role, re.I))
        fit_reason = 'Requires a recruiting/HR role AND confirmed hands-on electrical field employment; recruiting electricians alone is not field experience.'
    else:
        trade = bool(TRADE.search(role)) and not bool(re.search(r'\b(not|never|recruiting|hiring)\b', role, re.I))
        fit_reason = 'Requires an electrical field role AND commercial construction experience; generic electrical titles are insufficient.'
    add('trade_fit', 1 if trade and commercial else 0, ('role', 'commercial_experience'), fit_reason)
    years = claims['years_experience']['value']
    valid_years = type(years) in (int, float) and math.isfinite(years) and 0 <= years <= 80
    experience = (1 if lo <= years <= hi else .6 if lo - 1 <= years < lo or hi < years <= hi + 2 else .25) if valid_years else 0
    add('experience', experience, ('years_experience',), f'Relevant trade years: {lo:g}–{hi:g} full credit; one year under or two over partial; other valid years limited credit. Never infer years from seniority.')
    location = str(claims['location']['value'])
    local = bool(metro.search(location)) and bool(re.search(r'\b(GA|Georgia|Metro Atlanta|Greater Atlanta|Atlanta Metropolitan)\b', location, re.I))
    add('geography', int(local), ('location',), 'Requires an explicit locality from the run policy in Georgia; Georgia alone, missing location, or ambiguous city names do not establish commute fit.')

    signals = [e for e in rows if e.get('field') == 'availability_signal']
    polarities = {id(e): signal_polarity(e) for e in signals}
    negative = any(p == 'NEGATIVE_NOT_SEEKING' for p in polarities.values())
    eligible = [e for e in signals if e.get('subject_confirmed') is True and e.get('original_date_verified') is True
                and e['knowledge'] == 'VERIFIED_FACT' and polarities[id(e)] == 'POSITIVE_SEEKING'
                and date(e.get('original_date')) is not None
                and date(e['original_date']) <= date(e['retrieved_at']) <= today]
    signal = max(eligible, key=lambda e: date(e['original_date']), default=None)
    age = (today - date(signal['original_date'])).days if signal else None
    recent = age is not None and 0 <= age <= window and not negative
    # The signal's own original date is required; retrieval dates and separate,
    # unrelated signal_date rows never make an undated statement current.
    signal_fraction = 1 if recent else .25 if signal and not negative else 0
    add('job_change', signal_fraction, ('availability_signal',),
        'Requires a person-attributed, human-verified statement of job-change interest. Negative evidence blocks qualification until reviewed.')
    freshness = 1 if recent and age <= full_credit else .6 if recent else 0
    add('freshness', freshness, ('availability_signal',), f'Original signal age: 0–{full_credit} days full credit, up to {window} days reduced credit, older stale; missing/invalid/future dates receive zero.')
    if negative:
        claims['availability_signal']['conflict'] = True
        claims['availability_signal']['knowledge_status'] = 'UNKNOWN'
        for key in ('job_change', 'freshness'):
            components[key].update(score=0, knowledge_status='UNKNOWN')

    routes = []
    for raw in contacts:
        c = dict(raw)
        value = c.get('value', '')
        valid = isinstance(value, str) and ((c.get('route_type') == 'professional_profile' and public_url(value))
            or (c.get('route_type') == 'public_professional_email' and re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value))
            or (c.get('route_type') == 'public_business_phone' and re.fullmatch(r'[+\d ().-]+', value) and 10 <= len(re.sub(r'\D', '', value)) <= 15))
        observed = date(c.get('retrieved_at'))
        if valid and c.get('status') in ('CLAIMED', 'CORROBORATED') and public_url(c.get('source_url')) and observed and 0 <= (today-observed).days <= 180:
            routes.append(c)
    components['contact'] = {'score': 5 if routes else 0, 'maximum': 5,
        'knowledge_status': 'REASONABLE_INFERENCE' if routes else 'UNKNOWN',
        'reason': 'Reviewed public professional route observed within 180 days; existence does not verify delivery, consent, or willingness.',
        'source_urls': sorted({c['source_url'] for c in routes})}
    quality = sum(c['source_quality'] for c in claims.values()) / len(FIELDS)
    components['source_quality'] = {'score': round(10 * quality, 2), 'maximum': 10,
        'knowledge_status': 'REASONABLE_INFERENCE', 'reason': 'Mean best source reliability across six required claims, including identity: primary/official 1, professional profile .8, secondary .5, snippet .25, unspecified 0. Duplicates add no weight.'}
    blockers = []
    if not isinstance(claims['name']['value'], str) or not claims['name']['value'].strip(): blockers.append('Candidate identity not established')
    if not trade or not commercial: blockers.append('Commercial electrical trade fit not established' if pol['role_kind'] != 'electrical_recruiter' else 'Recruiting role with hands-on electrical field experience not established')
    if not valid_years or years < lo or (pol['years_maximum_is_gate'] and years > hi): blockers.append('Relevant experience outside target or unknown')
    if not local: blockers.append('Metro Atlanta location not established')
    if not recent: blockers.append(f'No sufficient verified job-change signal within {window} days')
    if not routes: blockers.append('No recent legitimate public professional contact route evidenced')
    if any(c['conflict'] for c in claims.values()): blockers.append('Contradictory evidence requires resolution')
    if any(c['knowledge_status'] != 'VERIFIED_FACT' for c in claims.values()): blockers.append('Required claims still inferred or unknown')
    raw_score = round(sum(c['score'] for c in components.values()), 2)
    confidence = round(100 * sum(c['source_quality'] * {'VERIFIED_FACT': 1, 'REASONABLE_INFERENCE': .5, 'UNKNOWN': 0}[c['knowledge_status']] for c in claims.values()) / len(FIELDS))
    confidence = min(confidence, 49) if not recent else confidence
    classification = 'FULLY_QUALIFIED' if not blockers else ('PROVISIONAL' if recent else 'RESEARCH_ONLY')
    return {'version': VERSION, 'assessed_as_of': today.isoformat(), 'classification': classification, 'policy': pol,
            'score': min(raw_score, 69) if blockers else raw_score, 'raw_score': raw_score,
            'score_cap_reason': 'Unmet qualification gates cap score at 69' if blockers else None,
            'confidence_score': confidence, 'confidence_note': 'Evidence support index, not a probability; without recent verified interest capped at 49.',
            'components': components, 'claims': claims, 'blockers': blockers, 'signal_age_days': age,
            'human_review_required': True, 'outreach_enabled': False}


def ranking_key(candidate):
    q = candidate['qualification']
    return ({'FULLY_QUALIFIED': 0, 'PROVISIONAL': 1, 'RESEARCH_ONLY': 2}[q['classification']],
            -q['score'], -q['confidence_score'], candidate['id'])
