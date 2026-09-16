"""Deterministic commercial-trade lead assessment; no discovery, network or hiring decisions."""
import datetime as dt
import json
import math
import ipaddress
import re
from urllib.parse import urlsplit

VERSION = 'commercial-atlanta-v1'
WEIGHTS = {'trade_fit': 25, 'experience': 15, 'geography': 15,
           'job_change': 20, 'freshness': 10, 'contact': 5, 'source_quality': 10}
FIELDS = ('name', 'role', 'commercial_experience', 'years_experience', 'location', 'availability_signal')
METRO = re.compile(r'\b(atlanta|marietta|decatur|doraville|lawrenceville|conyers|covington|'
                   r'roswell|alpharetta|sandy springs|smyrna|duluth|norcross|dunwoody|'
                   r'kennesaw|tucker|lithonia|peachtree corners)\b', re.I)
TRADE = re.compile(r'\b(electrician|wireman|electrical (foreman|superintendent|apprentice|installer))\b', re.I)
POSITIVE = re.compile(r'\b(open to work|seeking employment|looking for (work|a job|a new role)|'
                      r'available for (work|hire)|seeking (a |my )?(new|next) (role|job|opportunity))\b', re.I)
NEGATIVE = re.compile(r'\b(not (currently )?(open|looking|seeking|available)|no longer|'
                      r'accepted .*?(offer|job|position)|got hired|started .*?new (job|position))\b', re.I)
QUALITY = {'first_party': 1.0, 'official_record': 1.0, 'professional_profile': .8,
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


def assess_candidate(facts, evidence=(), contacts=(), *, as_of=None):
    """Only per-evidence human attestations establish VERIFIED_FACT.

    Legacy CLAIMED/CORROBORATED rows remain inferences. Independence and repeated
    snippets never turn an inference into a verified fact. Scores are policy
    indicators, not calibrated probabilities of job acceptance.
    """
    today = date(as_of) if as_of is not None else dt.datetime.now(dt.timezone.utc).date()
    if today is None: raise ValueError('Invalid assessment date')
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
        e['knowledge'] = ('VERIFIED_FACT' if e.get('human_verified') is True
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
    trade = bool(TRADE.search(role)) and not bool(re.search(r'\b(not|never|recruiting|hiring)\b', role, re.I))
    commercial = str(claims['commercial_experience']['value']).lower() in ('yes', 'true')
    add('trade_fit', 1 if trade and commercial else 0, ('role', 'commercial_experience'),
        'Requires an electrical field role AND commercial construction experience; generic electrical titles are insufficient.')
    years = claims['years_experience']['value']
    valid_years = type(years) in (int, float) and math.isfinite(years) and 0 <= years <= 80
    experience = (1 if 3 <= years <= 10 else .6 if 2 <= years < 3 or 10 < years <= 12 else .25) if valid_years else 0
    add('experience', experience, ('years_experience',), 'Relevant trade years: 3–10 full credit; 2–<3 or >10–12 partial; other valid years limited credit. Never infer years from seniority.')
    location = str(claims['location']['value'])
    local = bool(METRO.search(location)) and bool(re.search(r'\b(GA|Georgia|Metro Atlanta|Greater Atlanta|Atlanta Metropolitan)\b', location, re.I))
    add('geography', int(local), ('location',), 'Requires an explicit Metro Atlanta locality in Georgia; Georgia alone, missing location, or ambiguous city names do not establish commute fit.')

    signals = [e for e in rows if e.get('field') == 'availability_signal']
    negative = any(NEGATIVE.search(str(e.get('value')) + ' ' + str(e.get('excerpt'))) for e in signals)
    eligible = [e for e in signals if e.get('subject_confirmed') is True and e.get('original_date_verified') is True
                and e['knowledge'] == 'VERIFIED_FACT' and POSITIVE.search(str(e.get('value')))
                and date(e.get('original_date')) is not None
                and date(e['original_date']) <= date(e['retrieved_at']) <= today]
    signal = max(eligible, key=lambda e: date(e['original_date']), default=None)
    age = (today - date(signal['original_date'])).days if signal else None
    recent = age is not None and 0 <= age <= 90 and not negative
    # The signal's own original date is required; retrieval dates and separate,
    # unrelated signal_date rows never make an undated statement current.
    signal_fraction = 1 if recent else .25 if signal and not negative else 0
    add('job_change', signal_fraction, ('availability_signal',),
        'Requires a person-attributed, human-verified statement of job-change interest. Negative evidence blocks qualification until reviewed.')
    freshness = 1 if recent and age <= 30 else .6 if recent else 0
    add('freshness', freshness, ('availability_signal',), 'Original signal age: 0–30 days full credit, 31–90 reduced credit, >90 stale; missing/invalid/future dates receive zero.')
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
    if not trade or not commercial: blockers.append('Commercial electrical trade fit not established')
    if not valid_years or not 3 <= years <= 10: blockers.append('Relevant experience outside target or unknown')
    if not local: blockers.append('Metro Atlanta location not established')
    if not recent: blockers.append('No sufficient verified job-change signal within 90 days')
    if not routes: blockers.append('No recent legitimate public professional contact route evidenced')
    if any(c['conflict'] for c in claims.values()): blockers.append('Contradictory evidence requires resolution')
    if any(c['knowledge_status'] != 'VERIFIED_FACT' for c in claims.values()): blockers.append('Required claims still inferred or unknown')
    raw_score = round(sum(c['score'] for c in components.values()), 2)
    confidence = round(100 * sum(c['source_quality'] * {'VERIFIED_FACT': 1, 'REASONABLE_INFERENCE': .5, 'UNKNOWN': 0}[c['knowledge_status']] for c in claims.values()) / len(FIELDS))
    confidence = min(confidence, 49) if not recent else confidence
    classification = 'FULLY_QUALIFIED' if not blockers else ('PROVISIONAL' if recent else 'RESEARCH_ONLY')
    return {'version': VERSION, 'assessed_as_of': today.isoformat(), 'classification': classification,
            'score': min(raw_score, 69) if blockers else raw_score, 'raw_score': raw_score,
            'score_cap_reason': 'Unmet qualification gates cap score at 69' if blockers else None,
            'confidence_score': confidence, 'confidence_note': 'Evidence support index, not a probability; without recent verified interest capped at 49.',
            'components': components, 'claims': claims, 'blockers': blockers, 'signal_age_days': age,
            'human_review_required': True, 'outreach_enabled': False}


def ranking_key(candidate):
    q = candidate['qualification']
    return ({'FULLY_QUALIFIED': 0, 'PROVISIONAL': 1, 'RESEARCH_ONLY': 2}[q['classification']],
            -q['score'], -q['confidence_score'], candidate['id'])
