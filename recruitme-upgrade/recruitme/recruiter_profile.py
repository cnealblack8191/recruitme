"""Opt-in Covington recruiter discovery. No model calls or automatic A/B claims."""
import datetime
import re
from .source_registry import apply_route
RESTRICTED = []

PROFILE_ID = 'covington-electrical-talent-acquisition'
ROLES = ('skilled trades recruiter', 'construction recruiter', 'electrical recruiter',
         'craft recruiter', 'talent acquisition manager', 'staffing recruiter',
         'senior recruiter', 'recruiting manager', 'talent acquisition partner')
SIGNALS = ('open to work', 'seeking employment', 'looking for a new role',
           'seeking my next opportunity', 'laid off', 'available for work',
           'looking for work', 'seeking a new opportunity')
PERSONAL = re.compile(r'\b(open to work|opentowork|seeking (?:employment|work|(?:my |a |the )?(?:next|new) (?:role|opportunity|position))|looking for (?:work|a job|(?:a |my )?(?:new|next) (?:role|opportunity|position))|available for (?:work|hire)|laid off)\b', re.I)
RECRUITING = re.compile(r'\b(recruiter|recruiting|recruitment|talent acquisition|staffing manager)\b', re.I)
TRADES = re.compile(r'\b(skilled[- ]trades|craft|construction|electric(?:al|ian)s?|journeym[ae]n|forem[ae]n|mechanical|plumb(?:ing|er)s?|HVAC)\b', re.I)
NEGATIVE = re.compile(r'\b(not (?:currently )?(?:seeking|looking|available|open)|no longer (?:looking|seeking|available)|accepted (?:a |an |the |my )?(?:new )?(?:job|offer|position)|started (?:a |my )?new (?:job|position))\b', re.I)
THIRD_PARTY = re.compile(r'\b(?:my (?:friend|colleague|client|candidate)|he|she|they) (?:is |are )?(?:looking|seeking|available)\b', re.I)
RELOCATING = re.compile(r'\b(?:I(?:\s+am|\x27m)?\s+(?:planning to |plan to |will |want to |am going to )?(?:relocate|relocating|move|moving)|relocating|moving)\s+to\s+(?:the\s+)?(?:metro\s+)?Atlanta\b', re.I)


def next_plan(state, provider):
    if state['job_profile'].get('screening_version') == 'dual-experience-2026-09-11':
        from .dual_experience import next_plan as dual_plan
        return dual_plan(state, provider)
    p = state['job_profile']; n = len(state['queries'])
    from .discovery import recency_filter
    options = {'exclude_domains': RESTRICTED}
    window = recency_filter(state['search_as_of'], 30)
    if n % 3 == 2:
        for packet in sorted(state['packets'].values(), key=lambda x: -x['review_priority']):
            if packet.get('classification') != 'C — Provisional' or not packet.get('name_hint'):
                continue
            used = state['followups'].get(packet['source_url'], 0)
            if used >= 3:
                continue
            # Preserve the known source as an anchor; same-name hits never merge people.
            terms = ('recruiting work history skilled trades',
                     'personal seeking employment original post date',
                     'Metro Atlanta relocation Covington availability salary')[used]
            q = f'{packet["source_url"]} "{packet["name_hint"]}" {terms}'[:500]
            if any(x['query'] == q for x in state['queries']):
                continue
            return dict(query=q, purpose='corroboration/contact', strategy='recruiter_evidence_review',
                        target=packet['source_url'], provider=provider,
                        options={'exclude_domains': RESTRICTED})
    i = state['discovery_index']; branch = i % 6
    role = ROLES[(i//6) % len(ROLES)]
    places = ['Atlanta Georgia', 'Covington Georgia', 'Metro Atlanta'] + p['locations']
    place = places[(i//3) % len(places)]
    signal = SIGNALS[(i//6+i) % len(SIGNALS)]
    if branch == 0:
        query = f'"{role}" "{signal}" {place}'
    elif branch == 1:
        query = f'recruiter "skilled trades" "{signal}" {place}'
    elif branch == 2:
        query = f'"{role}" "relocating to Atlanta"'
    elif branch == 3:
        query = f'"{role}" "moving to Atlanta" "{signal}"'
    elif branch == 4:
        query = f'recruiter "electrical construction" "{signal}" {place}'
    else:
        query = f'"{role}" resume "{signal}" {place}'
        # Undated discovery is background only; never a confirmed fresh signal.
        window = None
    candidate = dict(query=query[:500], purpose='discovery',
                strategy=('recruiter_local_intent','trades_recruiter_intent','atlanta_relocation_intent',
                          'atlanta_move_intent','electrical_preference','recruiter_undated_background')[branch],
                target=None, provider=provider, options=options)
    if window: candidate['recency_filter'] = window
    return apply_route(candidate, i, 'recruiter', p)


def apply_screen(packet, profile):
    if profile.get('screening_version') == 'dual-experience-2026-09-11':
        from .dual_experience import apply_screen as dual_screen
        return dual_screen(packet, profile)
    if packet is None:
        return None
    text = packet['text']
    own = re.split(r'## (?:Comments|Social)\b', text, maxsplit=1)[0]
    header = re.split(r'## (?:About|Experience|Education)\b', own, maxsplit=1)[0]
    local_names = [re.sub(r'\s+Georgia$', '', x) for x in profile['locations']] + ['Metro Atlanta']
    location_hint = next((x for x in local_names if re.search(r'\b'+re.escape(x)+r'\b', header, re.I)), None)
    relocation = RELOCATING.search(own)
    local = bool(location_hint or relocation)
    trade = bool(RECRUITING.search(header))
    fit = bool(TRADES.search(own))
    signal = PERSONAL.search(own)
    contradiction = bool(packet.get('contradiction_flag') or NEGATIVE.search(own))
    third_party = bool(packet.get('third_party_signal_flag') or THIRD_PARTY.search(own))
    personal = bool(signal and not contradiction and not third_party and not packet.get('hiring_ad_flag'))
    packet.update(profile_id=profile['id'], trade_match=trade,
        commercial_industrial_match=fit, possible_recruiting_signal=personal,
        track_hints=['skilled_trades_recruiting'] if trade and fit else [],
        local_scope_hint=local, location_hint=location_hint,
        relocation_excerpt=relocation.group(0) if relocation else None,
        geographic_scope_status='CLAIMED_REQUIRES_REVIEW' if local else 'UNKNOWN_OR_OUT_OF_SCOPE',
        contradiction_flag=contradiction, third_party_signal_flag=third_party,
        signal_excerpt=own[max(0,signal.start()-120):signal.end()+260] if signal else None,
        signal_date_confirmed=False, signal_date_basis='UNKNOWN; original personal statement date requires review',
        identity_confirmed=False, signal_subject_confirmed=False,
        readiness={'salary_expectation':'UNKNOWN','salary_target_usd':70000,'salary_flexible':True,
                   'start_date':'UNKNOWN','covington_in_person_commute':'UNKNOWN',
                   'relocation_assistance_needs':'UNKNOWN'},
        classification=('C — Provisional' if trade and fit and local and personal else
                        'Passive Research Pool' if trade and local and not packet.get('hiring_ad_flag') else 'Rejected'),
        review_priority=(30 if trade else 0)+(25 if fit else 0)+(25 if personal else 0)+(10 if local else 0))
    return packet
