"""Pure search planning and unverified discovery evidence; no scoring or I/O."""
import datetime
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .data import canonical_url

PLACES = ('Doraville', 'Atlanta', 'Chamblee', 'Norcross', 'Tucker', 'Decatur',
          'Marietta', 'Smyrna', 'Sandy Springs', 'Duluth', 'Lawrenceville',
          'Peachtree Corners', 'Brookhaven', 'Dunwoody', 'Alpharetta',
          'Kennesaw', 'Stone Mountain', 'DeKalb County', 'Gwinnett County',
          'Fulton County', 'Cobb County', 'Johns Creek')
ROLES = ('commercial electrician', 'journeyman electrician', 'journeyman wireman',
         'lead electrician', 'construction electrician', 'electrical foreman')
SIGNALS = ('looking for work', 'open to work', 'seeking employment',
           'available for work', 'looking for my next project', 'laid off',
           'project ending', 'seeking another employer')
TASKS = ('commercial construction', 'tenant buildout', 'conduit installation',
         'switchgear installation', 'commercial wiring', 'electrical construction')


def electrical_profile(profile):
    return any(re.search(r'\b(?:electrician|wireman|electrical foreman)\b', role, re.I)
               for track in profile.get('tracks', []) for role in track['roles'])


def plan(state, index=None, profile=None, undated=False):
    """Rotate independent dimensions, retaining local intent beyond the first batch.

    Exact years are a recall branch, never a mandatory qualification filter.
    Saved profile geography/roles remain authoritative for other searches.
    """
    i = state['discovery_index'] if index is None else index
    roles = [r for t in profile['tracks'] for r in t['roles']] if profile else ROLES
    places = profile['locations'] if profile else [p + ' Georgia' for p in PLACES]
    role = roles[i % len(roles)]
    place = places[(i // 4 + i % 4) % len(places)]
    signal = SIGNALS[(i // 4) % len(SIGNALS)]
    task = TASKS[(i // 4 + i // len(SIGNALS)) % len(TASKS)]
    branch = i % 4
    queries = (
        f'{role} "{signal}" {place} {task}',
        f'{role} resume {place} {task} "{3 + (i // 4) % 8} years"',
        f'{role} "{signal}" {place} {task} resume',
        f'{role} {place} {task} professional resume "{signal}"',
    )
    # Publication dates are unreliable for profile pages and unsupported by the
    # keyword engines, so the window travels as a hint. The source registry applies
    # it only on domains whose pages are dated posts (see DATED_DOMAINS).
    plan_ = dict(query=queries[branch][:500], purpose='discovery', target=None,
                 strategy=('recent_availability','recent_resumes','transition_180_days','undated_review')[branch],
                 options={})
    if not undated and branch != 3:
        plan_['recency_filter'] = recency_filter(state['search_as_of'], (30,90,180)[branch])
    return plan_


def recency_filter(as_of, days):
    now = datetime.date.fromisoformat(as_of)
    return dict(start_date=(now - datetime.timedelta(days=days)).isoformat(), end_date=now.isoformat(), days=days)


def page_key(url):
    """Remove known tracking only; preserve identity query parameters/API IDs."""
    u = urlsplit(canonical_url(url))
    pairs = parse_qsl(u.query, keep_blank_values=True)
    kept = [(k,v) for k,v in pairs if not k.lower().startswith('utm_')
            and k.lower() not in ('gclid','fbclid','msclkid')]
    # Preserve exact query encoding/order when nothing was removed.
    query = urlencode(kept) if len(kept) != len(pairs) else u.query
    return urlunsplit((u.scheme,u.netloc,u.path,query,u.fragment))


def followup_anchor(packet):
    """Name plus observed locality limits namesake matches; identity stays unverified.

    Without a name hint there is nothing a search engine can anchor on, so the
    caller skips the search follow-up rather than pasting a URL into a query.
    """
    if not packet.get('name_hint'):
        return None
    places=packet.get('discovery_evidence',{}).get('local_place_mentions',[])
    locality=places[0]+' Georgia' if places else (packet.get('location_hint') or packet.get('southeast_location_hint') or '')
    return ('"'+packet['name_hint']+'" '+locality).strip()


def content_route_for(state, url):
    """First enabled single-URL content adapter whose operator allowlist covers this host."""
    host=(urlsplit(url).hostname or '').lower()
    for name,domains in (state.get('content_routes') or {}).items():
        if any(host==d or host.endswith('.'+d) for d in domains):
            return name
    return None


def followup_plan(state, packet, used, terms, strategy='candidate_followup', provider=None):
    """Fetch the page itself first, then anchored name searches; never a URL as a search term.

    Returns None when neither a content route nor a name anchor exists.
    """
    url=packet['source_url']
    if used==0:
        route=content_route_for(state,url)
        if route:
            return dict(query=url,purpose='corroboration/contact',strategy='profile_content',target=url,
                        provider=None,content_provider=route,options={},source_family='profile_content',
                        source_access='public_page_fetch')
    anchor=followup_anchor(packet)
    if not anchor:
        return None
    plan_=dict(query=(anchor+' '+terms)[:500],purpose='corroboration/contact',strategy=strategy,target=url,options={})
    if provider:plan_['provider']=provider
    return plan_


def date_status(value, as_of):
    try:
        date = datetime.date.fromisoformat(value[:10])
        age = (as_of - date).days
        return {'status': 'FUTURE' if age < 0 else 'RECENT' if age <= 180 else 'STALE',
                'age_days': age}
    except (ValueError, TypeError):
        return {'status': 'UNKNOWN', 'age_days': None}


def annotate(packet, result, stamp):
    """Hints are source claims, never verified facts or score inputs."""
    text = packet['text']
    try:
        as_of = datetime.date.fromisoformat(stamp[:10])
    except (ValueError, TypeError):
        as_of = datetime.datetime.now(datetime.timezone.utc).date()
    local = [p for p in PLACES if re.search(r'\b'+re.escape(p)+r'\b', text, re.I)]
    years = []
    # Require explicit electrical context next to duration, excluding generic tenure.
    duration = r'(\d{1,2})(?:\s*[-–]\s*(\d{1,2}))?\s*(\+)?\s*years?'
    trade = r'(?:commercial\s+)?(?:electrician|electrical(?:\s+construction)?|wireman)'
    for pattern in (duration+r'\s+(?:of\s+)?(?:experience\s+(?:in|as)\s+)?'+trade,
                    trade+r'\s+(?:with\s+)?'+duration):
        for match in re.finditer(pattern, text, re.I):
            low = int(match[1]); high = int(match[2] or match[1])
            years.append(dict(minimum=low, maximum=None if match[3] else high,
                              target_range_hint=not match[3] and 3 <= low <= high <= 10,
                              excerpt=match.group()))
    routes = []
    if packet.get('name_hint') and urlsplit(packet['source_url']).hostname != 'api.apollo.io':
        routes.append(dict(route_type='source_profile', value=packet['source_url'],
                           excerpt=packet.get('title') or '', status='UNVERIFIED'))
    # Only explicitly labelled professional contact invitations; no guessed emails.
    for match in re.finditer(r'(?:business email|professional email|contact me(?: at)?|email me(?: at)?)\s*[:\-]?\s*'
                             r'([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})', text, re.I):
        if (not packet['hiring_ad_flag'] and not packet['third_party_signal_flag']
                and urlsplit(packet['source_url']).hostname != 'api.apollo.io'):
            routes.append(dict(route_type='public_professional_email', value=match[1],
                               excerpt=match.group(), status='UNVERIFIED'))
    for route in routes:
        route.update(source_url=packet['source_url'], retrieved_at=stamp,
                     ownership_confirmed=False)
    packet['discovery_evidence'] = dict(
        local_place_mentions=local, geography_confirmed=False,
        electrical_experience_claims=years,
        commercial_construction_mentions=[m.group() for m in re.finditer(
            r'\b(?:commercial (?:electrician|construction|wiring)|tenant buildout|electrical construction)\b', text, re.I)],
        publication_freshness=date_status(result.get('publishedDate'), as_of),
        signal_freshness='UNCONFIRMED', contact_routes=routes,
        human_review_required=True)
    return packet
