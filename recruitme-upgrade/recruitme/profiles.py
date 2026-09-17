"""Operator-authored reusable job briefs. Never populated from retrieved text."""
import copy
import datetime
import re
from .budget import StopRun
from .improved_search import RESTRICTED

SIGNALS=('available for work','seeking employment','looking for another employer','looking for my next employer','laid off','available immediately',
         'looking for next project','open to work','who is hiring','my resume','relocating',
         'seeking another employer','project ending','assignment ending','demobilized','moving','ready for a new opportunity',
         'project complete','looking for work in Atlanta','starting immediately','job change needed','job change',
         'seeking my next employer','seeking new project')

def validate(profile):
    p=copy.deepcopy(profile)
    if not isinstance(p,dict) or p.get('version')!=1:raise StopRun('Unsupported job profile')
    if not re.fullmatch(r'[a-z0-9_-]{1,64}',p.get('id','')):raise StopRun('Invalid profile ID')
    for field in ('locations','fit_terms','tracks'):
        if not isinstance(p.get(field),list) or not 1<=len(p[field])<=30:raise StopRun('Missing profile '+field)
    for field in ('locations','fit_terms'):
        if any(not isinstance(v,str) or not 1<=len(v)<=100 for v in p[field]):raise StopRun('Invalid profile terms')
    ids=[]
    for t in p['tracks']:
        if not isinstance(t,dict) or not re.fullmatch(r'[a-z0-9_-]{1,40}',t.get('id','')):raise StopRun('Invalid track')
        ids.append(t['id'])
        if not isinstance(t.get('roles'),list) or not 1<=len(t['roles'])<=20 or any(not isinstance(r,str) or not 1<=len(r)<=80 for r in t['roles']):raise StopRun('Invalid roles')
    if len(ids)!=len(set(ids)):raise StopRun('Duplicate tracks')
    return p

def discovery(state,index):
    from .discovery import electrical_profile, plan
    if electrical_profile(state['job_profile']):
        candidate = plan(state, index, state['job_profile'])
        candidate['options']['exclude_domains'] = list(RESTRICTED)
        return candidate
    p=state['job_profile'];roles=[(t['id'],r) for t in p['tracks'] for r in t['roles']]
    track,role=roles[index%len(roles)]
    branch=(index//5)%4
    strategy=('local_availability','task_resume','employer_change','relocation_or_undated')[branch]
    signal=SIGNALS[(index//len(roles)+index*3)%len(SIGNALS)]
    place=p['locations'][(index//len(roles)+index)%len(p['locations'])]
    suffix=('',p['fit_terms'][index%len(p['fit_terms'])],'recent personal availability','public professional resume')[branch]
    options={'exclude_domains':RESTRICTED}
    role_phrase = {
        'local_availability':f'"{role}" "{signal}" "{place}" "{suffix}"',
        'task_resume':'"'+role+'" "recent resume" '+place+' "'+suffix+'"',
        'employer_change':role+' '+signal+' '+place+' "'+suffix+'" "project transition"',
        'relocation_or_undated':role+' '+signal+' '+place+' "'+suffix+'" "mobility signals"',
    }[strategy]
    result=dict(query=role_phrase[:500],purpose='discovery',strategy=strategy,track=track,target=None,options=options)
    if branch!=3:
        from .discovery import recency_filter
        result['recency_filter']=recency_filter(state['search_as_of'],(30,90,180)[branch])
    return result

def next_plan(state):
    if state['pending']:return state['pending']
    n=len(state['queries'])
    # Twenty identical intents sent sequentially to each index, never parallel.
    provider=('exa_keyed','tavily')[n%2]
    if state['job_profile'].get('id')=='covington-electrical-talent-acquisition':
        from .recruiter_profile import next_plan as recruiter_plan
        return recruiter_plan(state,provider)
    if state['job_profile'].get('broad_search'):return broad_plan(state,provider)
    if n<40:return dict(discovery(state,n//2),provider=provider)
    if n%3!=0:
        for packet in sorted(state['packets'].values(),key=lambda p:-p['review_priority']):
            if packet['classification']!='C — Provisional' or not packet.get('name_hint'):continue
            used=state['followups'].get(packet['source_url'],0)
            if used>=3:continue
            terms=('work history experience','current availability seeking employment','public resume and contact recency',
                   'professional contact location earliest start','last 30 days availability update',
                   'Atlanta metro commercial electrical role')[used%6]
            from .discovery import followup_anchor
            q=f'{followup_anchor(packet)} {state["job_profile"]["tracks"][0]["roles"][0]} {terms}'[:500]
            if any(x['query']==q for x in state['queries']):continue
            return dict(query=q,purpose='corroboration/contact',strategy='candidate_followup',target=packet['source_url'],provider=provider,options={'exclude_domains':RESTRICTED})
    return dict(discovery(state,20+state['discovery_index']),provider=provider)

def apply_screen(packet,profile):
    if profile.get('id')=='covington-electrical-talent-acquisition':
        from .recruiter_profile import apply_screen as recruiter_screen
        return recruiter_screen(packet,profile)
    if packet is None:return None
    text=packet['text'].lower()
    tracks=[t['id'] for t in profile['tracks'] if any(re.search(r'\b'+re.escape(r.lower())+r'\b',text) for r in t['roles'])]
    trade=bool(tracks);fit=any(x.lower() in text for x in profile['fit_terms'])
    packet.update(profile_id=profile['id'],track_hints=tracks,trade_match=trade,commercial_industrial_match=fit,
        readiness={'pay_acceptance':'UNKNOWN','start_date':'UNKNOWN','local_commute_or_relocation':'UNKNOWN','travel_pay_acceptance':'UNKNOWN'},
        classification='C — Provisional' if trade and fit and packet['possible_recruiting_signal'] and not packet['hiring_ad_flag'] else ('Passive Research Pool' if trade and not packet['hiring_ad_flag'] else 'Rejected'))
    packet['review_priority']=(30 if trade else 0)+(25 if fit else 0)+(25 if packet['possible_recruiting_signal'] else 0)+(5 if packet['name_hint'] else 0)
    return packet


def broad_plan(state,provider):
    n=len(state['queries']);p=state['job_profile']
    if n%3==2:
        seeds=p.get('followup_names',[])
        slot=n//3
        if slot<len(seeds)*3:
            name=seeds[slot%len(seeds)]
            terms=('electrician Atlanta employment availability','electrical work history commercial Georgia','professional contact seeking work availability date',
                   'Atlanta electrician ready for immediate start','commercial electrician last 90 days update')[slot//len(seeds)]
            return dict(query=f'"{name}" {terms}',purpose='corroboration/contact',strategy='prior_person_review',target=None,provider=provider,options={'exclude_domains':RESTRICTED})
        for packet in sorted(state['packets'].values(),key=lambda x:-x['review_priority']):
            if not packet.get('name_hint') or not packet['classification'].startswith('C '):continue
            used=state['followups'].get(packet['source_url'],0)
            if used>=3:continue
            terms=('Atlanta electrical experience','seeking work availability date','professional contact Georgia',
                   'recent resume update','commercial project completion date','immediate start willingness')[used]
            from .discovery import followup_anchor
            q=f'{followup_anchor(packet)} {terms}'[:500]
            if any(x['query']==q for x in state['queries']):continue
            return dict(query=q,purpose='corroboration/contact',strategy='new_person_review',target=packet['source_url'],provider=provider,options={'exclude_domains':RESTRICTED})
    i=state['discovery_index'];branch=i%8
    from .discovery import electrical_profile, plan
    if electrical_profile(p):
        candidate = plan(state, i, p)
        candidate['options']['exclude_domains'] = list(RESTRICTED)
        candidate['provider'] = provider
        return candidate
    place=p['locations'][(i//8)%len(p['locations'])]
    role=('electrician','journeyman electrician','commercial electrician','journeyman wireman','lead electrician',
          'service electrician','industrial electrician','electrical foreman','commissioning electrician',
          'shutdown outage electrician','project electrician','electrical project manager',
          'electrical superintendent')[(i//3)%12]
    signal=('looking for work','available immediately','laid off','looking for another employer','seeking employment','project transition',
            'ready for a new opportunity','open to work')[((i//8+i)%8)]
    query=(f'"{signal}" {role} {place}',f'{role} resume availability {place}',f'{role} "next project" {place}',f'"busco trabajo" electricista {place}',
           f'"{signal}" electrical conduit {place}',f'{role} forum "available" {place}',f'"{signal}" electrician "disponible" {place}',
           f'{role} relocating to Atlanta to start immediately {place}')[branch]
    # Add source family to every broad query for additional diversity.
    source_family=('site:linkedin.com','site:indeed.com','site:roadtechs.com','site:reddit.com/r/electricians','site:postjobfree.com/resume',
                  'site:monster.com','site:careerbuilder.com','site:ziprecruiter.com')[branch]
    query=f'{source_family} {query}'
    options={'exclude_domains':RESTRICTED}
    if branch in (0,4,5,6):
        now=datetime.date.fromisoformat(state['search_as_of']);options.update(start_date=(now-datetime.timedelta(days=30)).isoformat(),end_date=now.isoformat())
    if branch==2:
        now=datetime.date.fromisoformat(state['search_as_of']);options.update(start_date=(now-datetime.timedelta(days=180)).isoformat(),end_date=now.isoformat())
    if branch==3:
        now=datetime.date.fromisoformat(state['search_as_of']);options.update(start_date=(now-datetime.timedelta(days=90)).isoformat(),end_date=now.isoformat())
    return dict(query=query[:500],purpose='discovery',strategy=('availability_first','resume','project_change','spanish_seeking','task_skills','forum_availability','spanish_available','relocation')[branch],target=None,provider=provider,options=options)
