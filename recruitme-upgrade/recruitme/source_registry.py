"""Public-index discovery routes, not authenticated candidate database access.

Only existing metered provider clients dispatch requests. This module does no I/O.
Source selection never relaxes geography, evidence rules, or spending limits.
"""
VERSION = '2026-09-17.1'
# (id, domain, audience, in_default_rotation). Routes outside the default rotation
# stay selectable through an explicit profile source_ids list. Social feeds,
# publishing platforms and recruiter trade press rarely index a dated,
# first-person availability statement, so they no longer consume default budget.
SOURCES = (
    ('open_web', '', 'all', True),
    ('linkedin', 'linkedin.com', 'all', True),
    ('postjobfree', 'postjobfree.com', 'all', True),
    ('jobcase', 'jobcase.com', 'all', True),
    ('craigslist_atlanta', 'atlanta.craigslist.org', 'all', True),
    ('reddit', 'reddit.com', 'all', True),
    ('indeed_public', 'indeed.com', 'all', True),
    ('ziprecruiter_public', 'ziprecruiter.com', 'all', True),
    ('roadtechs', 'roadtechs.com', 'field', True),
    ('electrician_talk', 'electriciantalk.com', 'field', True),
    ('contractor_talk', 'contractortalk.com', 'field', True),
    ('monster_public', 'monster.com', 'all', False),
    ('careerbuilder_public', 'careerbuilder.com', 'all', False),
    ('resume_library_public', 'resume-library.com', 'all', False),
    ('bebee_public', 'bebee.com', 'all', False),
    ('facebook_public', 'facebook.com', 'all', False),
    ('x_public', 'x.com', 'all', False),
    ('instagram_public', 'instagram.com', 'all', False),
    ('threads_public', 'threads.com', 'all', False),
    ('bluesky_public', 'bsky.app', 'all', False),
    ('ladders_public', 'theladders.com', 'all', False),
    ('about_me', 'about.me', 'all', False),
    ('medium', 'medium.com', 'all', False),
    ('substack', 'substack.com', 'all', False),
    ('wordpress', 'wordpress.com', 'all', False),
    ('shrm_atlanta', 'shrmatlanta.org', 'recruiter', False),
    ('recruiting_brainfood', 'recruitingbrainfood.com', 'recruiter', False),
    ('ere', 'ere.net', 'recruiter', False),
    ('recruiting_daily', 'recruitingdaily.com', 'recruiter', False),
    ('ihirehr', 'ihirehr.com', 'recruiter', False),
)
# Domains whose indexed pages are dated posts, so a publication-date window is a
# usable recency proxy. Profile pages (LinkedIn /in/) and the open web are not.
DATED_DOMAINS = frozenset(('postjobfree.com', 'jobcase.com', 'atlanta.craigslist.org', 'reddit.com',
                           'roadtechs.com', 'electriciantalk.com', 'contractortalk.com', 'x.com',
                           'bsky.app', 'threads.com'))


def routes(audience, selected=None):
    available = [s[:3] for s in SOURCES if s[2] in ('all', audience)]
    if selected is None:
        return [s[:3] for s in SOURCES if s[2] in ('all', audience) and s[3]]
    if not isinstance(selected, list) or not selected or any(not isinstance(s, str) for s in selected):
        raise ValueError('source_ids must be a nonempty list of source IDs')
    known = {s[0] for s in available}
    if set(selected) - known:
        raise ValueError('Unknown or inappropriate source_ids')
    return [s for s in available if s[0] in selected]


def apply_route(plan, index, audience, profile=None):
    """One route per existing query; no fan-out or extra provider requests.

    Alternate each route across both providers on subsequent full rotations.
    Source options are explicit so blanket legacy exclusions cannot cancel them.
    """
    candidates = routes(audience, (profile or {}).get('source_ids'))
    source_id, domain, _ = candidates[index % len(candidates)]
    options = dict(plan.get('options', {}))
    options['exclude_domains'] = []
    options.pop('include_domains', None)
    if domain:
        options['include_domains'] = [domain]
        plan['query'] = ('site:' + domain + ' ' + plan['query'])[:500]
    window = plan.get('recency_filter')
    if window and domain in DATED_DOMAINS:
        options.update(start_date=window['start_date'], end_date=window['end_date'])
    else:
        options.pop('start_date', None); options.pop('end_date', None)
    if plan.get('provider') in ('exa_keyed', 'tavily'):
        plan['provider'] = ('exa_keyed', 'tavily')[(index % len(candidates) + index // len(candidates)) % 2]
    plan.update(options=options, source_family=source_id,
                source_registry_version=VERSION, source_access='public_index_only')
    return plan


def coverage(queries):
    """Completed logical queries, not proof of site access or paid API counts."""
    result = {}
    for q in queries:
        key = q.get('source_family', 'legacy_or_followup')
        row = result.setdefault(key, {'completed_queries': 0, 'returned_pages': 0})
        row['completed_queries'] += 1
        row['returned_pages'] += q.get('result_count', 0)
    return result

