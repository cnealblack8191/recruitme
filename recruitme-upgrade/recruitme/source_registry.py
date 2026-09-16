"""Public-index discovery routes, not authenticated candidate database access.

Only existing metered provider clients dispatch requests. This module does no I/O.
Source selection never relaxes geography, evidence rules, or spending limits.
"""
VERSION = '2026-09-10.1'
# Ordered for early coverage of personal intent; open web retains independent sites.
SOURCES = (
    ('open_web', '', 'all'),
    ('linkedin', 'linkedin.com', 'all'),
    ('facebook_public', 'facebook.com', 'all'),
    ('reddit', 'reddit.com', 'all'),
    ('postjobfree', 'postjobfree.com', 'all'),
    ('jobcase', 'jobcase.com', 'all'),
    ('craigslist_atlanta', 'atlanta.craigslist.org', 'all'),
    ('x_public', 'x.com', 'all'),
    ('instagram_public', 'instagram.com', 'all'),
    ('threads_public', 'threads.com', 'all'),
    ('bluesky_public', 'bsky.app', 'all'),
    ('shrm_atlanta', 'shrmatlanta.org', 'recruiter'),
    ('recruiting_brainfood', 'recruitingbrainfood.com', 'recruiter'),
    ('ere', 'ere.net', 'recruiter'),
    ('recruiting_daily', 'recruitingdaily.com', 'recruiter'),
    ('ihirehr', 'ihirehr.com', 'recruiter'),
    ('indeed_public', 'indeed.com', 'all'),
    ('monster_public', 'monster.com', 'all'),
    ('careerbuilder_public', 'careerbuilder.com', 'all'),
    ('ziprecruiter_public', 'ziprecruiter.com', 'all'),
    ('ladders_public', 'theladders.com', 'all'),
    ('resume_library_public', 'resume-library.com', 'all'),
    ('bebee_public', 'bebee.com', 'all'),
    ('about_me', 'about.me', 'all'),
    ('medium', 'medium.com', 'all'),
    ('substack', 'substack.com', 'all'),
    ('wordpress', 'wordpress.com', 'all'),
    ('roadtechs', 'roadtechs.com', 'field'),
    ('electrician_talk', 'electriciantalk.com', 'field'),
    ('contractor_talk', 'contractortalk.com', 'field'),
)


def routes(audience, selected=None):
    available = [s for s in SOURCES if s[2] in ('all', audience)]
    if selected is None:
        return available
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

