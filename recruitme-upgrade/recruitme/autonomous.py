"""Standalone deterministic discovery. No Codex/model calls or automatic A/B claims.

Retrieved pages are data only. Evidence packets require subsequent qualification review.
"""
import datetime
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
from .budget import StopRun, money
from .governors import stop_code
from .connectors import ExaFree
from .exa_keyed import ExaKeyed
from .tavily import Tavily
from .routing import ProviderRouter
from .plugins import DISCOVERY_PLUGINS, CONTENT_PLUGINS
from .data import canonical_url
from .discovery import annotate, page_key, followup_plan

ROLES=('commercial electrician','journeyman electrician','electrical foreman','electrical superintendent',
       'electrical project manager','journeyman wireman','lead electrician','industrial electrician',
       'service electrician','shutdown outage electrician','commissioning electrician',
       'construction electrician','project electrician','electrical project engineer')
SIGNALS=('looking for work','open to work','seeking employment','available for work','looking for next project',
         'laid off','project ending','relocating','who is hiring','resume','seeking another employer',
         'assignment ending','demobilized','moving','ready for a new opportunity','project completed','job completed',
         'seeking my next employer')
GEORGIA=('Atlanta Georgia','Doraville Georgia','Chamblee Georgia','Sandy Springs Georgia','DeKalb County Georgia',
         'Gwinnett County Georgia','Decatur Georgia','Smyrna Georgia','Alpharetta Georgia','Macon Georgia',
         'Savannah Georgia','Augusta Georgia')
REGIONS=('Tennessee','Alabama','North Carolina','South Carolina','Florida','traveling willing to relocate Southeast')
SOURCES=(('open_web',''),
         ('professional_posts','site:linkedin.com/posts'),
         ('public_resumes','site:postjobfree.com/resume'),
         ('trade_forums','site:electriciantalk.com electrician'),
         ('public_social','site:reddit.com/r/electricians'),
         ('availability_boards','site:roadtechs.com electrician'),
         ('professional_pages','site:linkedin.com/in'),
         ('regional_boards','site:indeed.com/resumes electrician'),
         ('regional_boards','site:craigslist.org electrician'),
         ('trade_forums','site:jobspresso.com electricians'),
         ('regional_boards','site:monster.com electrician'),
         ('regional_boards','site:careerbuilder.com electrician'),
         ('public_resumes','site:ziprecruiter.com'),
         ('public_resumes','site:jobcase.com electrician'),
         ('public_social','site:reddit.com/r/trades'),
         ('regional_boards','site:careerarc.com electrician'))
TRADE=re.compile(r'\b(electrician|wireman|electrical (?:foreman|superintendent|project manager|construction))\b',re.I)
FIT=re.compile(r'\b(commercial|industrial|conduit|switchgear|motor controls|commissioning|electrical construction)\b',re.I)
SIGNAL=re.compile(r'\b(open to work|opentowork|looking for (?:work|a job|my next|another|a new|next project)|'
                  r'seeking (?:employment|work|a new|another)|available for (?:work|hire)|laid off|layoff|'
                  r'project (?:ending|ended|completed)|assignment ending|demobiliz\w*|relocat\w*|who.?s hiring|'
                  r'ready for (?:a )?new opportunit\w*)\b',re.I)
ADS=re.compile(r'\b(we are hiring|we.re hiring|apply now|apply today|job description|we are seeking|we.re seeking)\b',re.I)
BLOCKED=('whitepages.com','spokeo.com','beenverified.com','truepeoplesearch.com','fastpeoplesearch.com')


def new_state():
    return dict(version=1,queries=[],pending=None,discovery_index=0,followups={},packets={},
                result_appearances=0,duplicates=0,irrelevant=0,signal_hits=0,followup_evidence=0,
                source_coverage={},checkpoints=[],status='RUNNING',stop_reason=None)


def name_hint(result):
    # Hints are not identity verification and never merge different source URLs.
    title=str(result.get('title',''))
    author=str(result.get('author') or '').strip()
    if author and re.fullmatch(r"[A-Za-z][A-Za-z .'-]{3,75}",author) and 2<=len(author.split())<=4:
        return author
    value=re.split(r'\s+(?:-|\||on LinkedIn:)\s*',title,maxsplit=1)[0].strip()
    banned=set('electrician electrical commercial industrial resume technician manager foreman superintendent maintenance job jobs career linkedin available north south carolina georgia atlanta'.split())
    words=value.split()
    if 2<=len(words)<=4 and not any(w.lower().strip('.,') in banned for w in words) and re.fullmatch(r"[A-Za-z][A-Za-z .'-]{3,75}",value):return value
    return None


def screen(result):
    try:url=canonical_url(result.get('url',''))
    except (StopRun,TypeError,ValueError):return None
    host=urlsplit(url).hostname or ''
    if any(host==d or host.endswith('.'+d) for d in BLOCKED):return None
    text='\n'.join(str(result.get(k,'') or '') for k in ('title','author','text'))
    trade=bool(TRADE.search(text));fit=bool(FIT.search(text));ad=bool(ADS.search(text))
    signal_text=re.split(r'## (?:Comments|Social)\b',text,maxsplit=1)[0]
    match=SIGNAL.search(signal_text)
    if match and match.group().lower().startswith(('relocat','demobiliz')):
        nearby=signal_text[max(0,match.start()-30):match.end()+100]
        if re.search(r'\b(?:gear|equipment|power|conduits?|generators?|cables?|systems?)\b',nearby,re.I):match=None
    resume=('postjobfree.com' in host and '/resume/' in url) or bool(re.search(r'\bmy (?:resume|résumé)\b',text,re.I))
    has_signal=bool(match) or resume
    # Explicit negative/superseding statements cannot support active interest.
    excluded_signal=bool(re.search(r"\b(?:not (?:currently )?(?:seeking|looking|available|open)|no longer (?:looking|seeking|available)|I (?:was just|have been|got|was) hired|accepted (?:a |an |the |my )?(?:new )?(?:job|offer|position)|started (?:a |my )?new (?:job|position))\b",text,re.I))
    third_party=bool(re.search(r"\b(?:my (?:friend|son|brother|colleague)(?: is)?|he is|she is|they are) (?:looking|seeking|available)|\b(?:reposted|shared this post)\b",signal_text,re.I))
    if third_party:has_signal=False
    if excluded_signal:has_signal=False
    name=name_hint(result)
    published=result.get('publishedDate')
    age=None
    if published:
        try:age=(datetime.datetime.now(datetime.timezone.utc).date()-datetime.date.fromisoformat(published[:10])).days
        except (ValueError,TypeError):pass
    context=None
    if match:context=text[max(0,match.start()-150):match.end()+300]
    elif resume:context='Public resume result; posting date and ownership require review.'
    score=(30 if trade else 0)+(25 if fit else 0)+(25 if has_signal else 0)+(5 if name else 0)
    dated_source=('/posts/' in url or resume) and bool(re.search(r'\b202\d-\d\d-\d\d\b|Posted:\s*\n',signal_text))
    score+=10 if dated_source and age is not None and 0<=age<=90 else (5 if dated_source and age is not None and 90<age<=180 else 0)
    if ad:score-=35
    classification='C — Provisional' if trade and fit and has_signal and not ad else ('Passive Research Pool' if trade and not ad else 'Rejected')
    return dict(source_url=url,title=result.get('title'),name_hint=name,classification=classification,
                review_priority=max(0,score),trade_match=trade,commercial_industrial_match=fit,
                possible_recruiting_signal=has_signal,signal_excerpt=context,published_date_metadata=published,
                metadata_age_days=age,signal_date_confirmed=False,identity_confirmed=False,
                hiring_ad_flag=ad,evidence_status='CLAIMED/UNVERIFIED',text=text[:14000],
                contradiction_flag=excluded_signal,third_party_signal_flag=third_party,
                signal_subject_confirmed=False,signal_date_basis='UNKNOWN; publication metadata is not the signal date',
                contact_route_candidates=[url] if name else [],independent_corroboration='UNKNOWN',
                human_review_required=True,observations=[])


def extract_results(response):
    if isinstance(response.get('provider_response',{}).get('results'),list):return response['provider_response']['results']
    # Compatibility for previously approved free MCP route; preserve link/text only.
    results=[]
    for c in response.get('content',[]):
        if c.get('type')!='text':continue
        for block in c.get('text','').split('\n---\n'):
            m=re.search(r'^URL: (https?://\S+)',block,re.M)
            title=re.search(r'^Title: (.*)',block,re.M)
            if m:results.append({'url':m[1],'title':title.group(1) if title else '', 'text':block})
    return results


def next_query(state):
    if state['pending']:return state['pending']
    if state.get('job_profile'):
        from .profiles import next_plan
        candidate = next_plan(state)
        if not candidate.get('target') and not candidate.get('source_family'):
            from .source_registry import apply_route
            return apply_route(candidate, state['discovery_index'], 'field', state['job_profile'])
        return candidate
    if state.get('improved'):
        from .improved_search import plan,followup_options
        if len(state['queries'])%3==2 and any(p['classification']=='C — Provisional' for p in state['packets'].values()):
            candidate=focused_query(state)
            if candidate['target']:
                candidate['options']=followup_options(state);return candidate
        from .source_registry import apply_route
        candidate = plan(state)
        candidate['query'] = __import__('re').sub(r'site:\S+\s*', '', candidate['query'])
        return apply_route(candidate, state['discovery_index'], 'field')
    if state.get('focused'):return focused_query(state)
    count=len(state['queries'])
    # Approximately one third follows actual promising source pages/identity hints.
    if count%3==2:
        pool=sorted((p for p in state['packets'].values() if p['classification']=='C — Provisional'),
                    key=lambda p:-p['review_priority'])
        for p in pool:
            used=state['followups'].get(p['source_url'],0)
            if used>=3:continue
            terms=('electrician experience employment availability','electrician commercial industrial employer work history',
                   'electrician "open to work" professional contact location')[used]
            candidate=followup_plan(state,p,used,terms)
            if not candidate or candidate['query'] in {r['query'] for r in state['queries']}:continue
            return candidate
    i=state['discovery_index'];block=count//20
    strategy,source=SOURCES[block%len(SOURCES)]
    location=GEORGIA[i%len(GEORGIA)] if count<60 or i%3==0 else REGIONS[(i//3)%len(REGIONS)]
    role=ROLES[i%len(ROLES)];signal=SIGNALS[(i//len(ROLES)+i*3)%len(SIGNALS)]
    # The space is generated on demand, never exhausted after a prepared batch.
    variation=('2026','recent','resume availability','next employer')[i//(len(ROLES)*len(SIGNALS))%4]
    q=f'{source} "{role}" "{signal}" {location} {variation}'.strip()
    return dict(query=q,purpose='discovery',strategy=strategy,target=None)


def focused_query(state):
    """Bounded deterministic query generation; dates are query intent, not verified signal dates."""
    count=len(state['queries']);seen={q['query'] for q in state['queries']}
    if count%3==2:
        pool=sorted((p for p in state['packets'].values() if p['classification']=='C — Provisional'),
                    key=lambda p:(p['source_url'] in state.get('prior_urls',[]),-p['review_priority']))
        for p in pool:
            used=state['followups'].get(p['source_url'],0)
            if used>=3:continue
            suffix=(str(state.get('seed_locations',{}).get(p['source_url'],''))+' electrician commercial projects employer work history',
                    'electrician latest "looking for work" "hired" '+state['focus_month'],
                    'electrician professional contact availability location')
            candidate=followup_plan(state,p,used,suffix[used].strip())
            if candidate and candidate['query'] not in seen:return candidate
    i=state['discovery_index'];block=count//20
    roles=('commercial electrician','working electrical foreman','journeyman electrician','lead electrician','service electrician','journeyman wireman')
    signals=('I am looking for work','available to start','laid off','looking for another company','my project ends','available Monday','seeking employment','looking for my next project','open to work','who is hiring electricians')
    sources=(('professional_posts','site:linkedin.com/posts'),('public_resumes','site:postjobfree.com/resume'),('open_web',''),('regional_boards','site:craigslist.org'),('availability_boards','site:roadtechs.com'),('trade_forums','site:electriciantalk.com'))
    strategy,source=sources[block%len(sources)]
    locations=('Atlanta Georgia','Marietta Georgia','Alpharetta Georgia','Gwinnett Georgia','Jonesboro Georgia','Savannah Georgia','Augusta Georgia')
    location=locations[i%len(locations)] if count<80 or i%3 else REGIONS[(i//3)%len(REGIONS)]
    period=state['focus_month'] if count<60 else state['focus_range']
    q=f'{source} "{roles[i%len(roles)]}" "{signals[(i//len(roles)+i*3)%len(signals)]}" {location} {period}'
    return dict(query=q,purpose='discovery',strategy=strategy,target=None)


def consume(state,plan,response,stamp,raw_path):
    results=extract_results(response)
    page_index={page_key(url):url for url in state['packets']}
    for r in results:
        state['result_appearances']+=1
        p=screen(r)
        if state.get('job_profile'):
            from .profiles import apply_screen
            p=apply_screen(p,state['job_profile'])
        if not p:state['irrelevant']+=1;continue
        p=annotate(p,r,stamp)
        host=urlsplit(p['source_url']).hostname
        state['source_coverage'][host]=state['source_coverage'].get(host,0)+1
        observation=dict(query=plan['query'],retrieved_at=stamp,raw_evidence_path=str(raw_path),
                         purpose=plan['purpose'],target=plan['target'],
                         provider=response.get('provider',plan.get('provider')),
                         source_family=plan.get('source_family'),source_url=p['source_url'],
                         original_url=r.get('url'),published_date_metadata=p['published_date_metadata'],
                         signal_excerpt=p['signal_excerpt'],
                         discovery_evidence=p['discovery_evidence'])
        # Canonical URL equivalence only: names/contact values never merge people.
        key=page_key(p['source_url'])
        existing=page_index.get(key)
        if existing:p['source_url']=existing
        else:page_index[key]=p['source_url']
        if p['source_url'] in state['packets']:
            state['duplicates']+=1
            old=state['packets'][p['source_url']]
            if p['text']!=old['text'] and plan['target']:state['followup_evidence']+=1
            old['observations'].append(observation)
            if p['contradiction_flag'] or p['third_party_signal_flag'] or (p['review_priority']>old['review_priority'] and not old.get('contradiction_flag')):
                p['observations']=old['observations'];state['packets'][p['source_url']]=p
        else:
            p['observations']=[observation];state['packets'][p['source_url']]=p
            if p['classification']=='Rejected':state['irrelevant']+=1
            if p['possible_recruiting_signal'] and p['trade_match'] and not p['hiring_ad_flag']:state['signal_hits']+=1
            if plan['target'] and p['trade_match']:state['followup_evidence']+=1
    state['queries'].append(dict(plan,retrieved_at=stamp,result_count=len(results)))
    if plan['target']:state['followups'][plan['target']]=state['followups'].get(plan['target'],0)+1
    else:state['discovery_index']+=1
    state['pending']=None


def structured_providers(config):
    """Enabled, approved, credentialed people-data routes a planner may address directly.

    Computed once per run so a planner never targets a route the router would refuse.
    """
    names=[]
    for name,p in config.get('providers',{}).items():
        cls=DISCOVERY_PLUGINS.get(name)
        if not cls or not p.get('enabled') or not p.get('approved') or 'search' not in p.get('operations',{}):continue
        if getattr(cls,'capability','')!='structured_people' and name!='exa_people':continue
        if money(p['operations']['search']) and not config.get('paid_enabled'):continue
        ready=getattr(cls,'credentials_available',None)
        if ready and not ready(p):continue
        names.append(name)
    return names


def content_routes(config):
    """Enabled, approved, priced, credentialed single-URL adapters and their operator allowlists.

    Cheapest first. Coresignal is excluded here: its collect route is structured, not a page fetch.
    """
    routes=[]
    today=datetime.date.today()
    for name,cls in CONTENT_PLUGINS.items():
        p=config.get('providers',{}).get(name,{})
        if name=='coresignal' or not p.get('enabled') or not p.get('approved') or 'search' not in p.get('operations',{}):continue
        try:version,expires=cls.name+'-2026-09-12',datetime.date.fromisoformat(__import__('recruitme.plugins',fromlist=['EXPIRES']).EXPIRES)
        except ValueError:continue
        if p.get('price_version')!=version or today>=expires:continue
        cost=money(p['operations']['search'])
        if cost and not config.get('paid_enabled'):continue
        domains=[d for d in p.get('allowed_domains',[]) if isinstance(d,str) and d]
        if not domains:continue
        ready=getattr(cls,'credentials_available',None)
        if ready and not ready(p):continue
        routes.append((cost,name,domains))
    return {name:domains for _,name,domains in sorted(routes)}


def web_policy_plan(state, candidate, config):
    """Free-first planning keeps variation and resumes exact pending requests."""
    if state.get('pending'):
        return state['pending']
    if candidate.get('source_family') in ('structured_people','profile_content'):
        # Provider-specific plans: free-first substitution would send JSON or a bare URL to a web index.
        return dict(candidate)
    candidate=dict(candidate)
    candidate.pop('provider',None)
    if len(state['queries']) < 3 or not config.get('paid_enabled'):
        from .discovery import electrical_profile, plan as discovery_plan
        profile=state.get('job_profile')
        if profile and electrical_profile(profile):
            candidate=discovery_plan(state,profile=profile,undated=True)
            # Explicit selected sources still require enforceable domain filters.
            if profile.get('source_ids'):
                from .source_registry import apply_route
                candidate=apply_route(candidate,state['discovery_index'],'field',profile)
        elif profile:
            index=state['discovery_index']
            roles=[r for t in profile['tracks'] for r in t['roles']]
            candidate=dict(query=(roles[index % len(roles)]+' '+profile['locations'][index % len(profile['locations'])]+' '+profile['fit_terms'][index % len(profile['fit_terms'])])[:350],
                           purpose='discovery',strategy='free_first_profile_discovery',target=None,options={})
    return candidate


def evaluate_yield(state):
    previous=state['checkpoints'][-1] if state['checkpoints'] else dict(provisional_total=0,signal_total=0,followup_total=0,appearances_total=0,duplicates_total=0,irrelevant_total=0)
    provisional=sum(p['classification']=='C — Provisional' for p in state['packets'].values())
    delta=max(1,state['result_appearances']-previous['appearances_total'])
    cp=dict(searches=len(state['queries']),strategy=next((q['strategy'] for q in reversed(state['queries']) if q.get('purpose')=='discovery'), 'unknown'),
            provisional_total=provisional,new_provisional=provisional-previous['provisional_total'],
            signal_total=state['signal_hits'],new_signal_pages=state['signal_hits']-previous['signal_total'],
            followup_total=state['followup_evidence'],new_followup_evidence=state['followup_evidence']-previous['followup_total'],
            appearances_total=state['result_appearances'],duplicates_total=state['duplicates'],irrelevant_total=state['irrelevant'],
            duplicate_rate=(state['duplicates']-previous['duplicates_total'])/delta,
            irrelevant_rate=(state['irrelevant']-previous['irrelevant_total'])/delta,
            new_verified_ab=0,verified_contact_routes='Pending evidence review')
    cp['low_yield']=cp['new_provisional']==0 and cp['new_signal_pages']==0 and cp['new_followup_evidence']==0 and max(cp['duplicate_rate'],cp['irrelevant_rate'])>=0.9
    state['checkpoints'].append(cp)
    recent=state['checkpoints'][-3:]
    return len(state['checkpoints'])>=6 and len({c['strategy'] for c in recent})==3 and all(c['low_yield'] for c in recent)


def execute(ledger,run_id,state_path,job,guard,client=None,sleep=time.sleep):
    from .worker import atomic_json
    ledger.db.execute('CREATE TABLE IF NOT EXISTS autonomous_checkpoints(run_id TEXT PRIMARY KEY,state_json TEXT NOT NULL)')
    saved=ledger.db.execute('SELECT state_json FROM autonomous_checkpoints WHERE run_id=?',(run_id,)).fetchone()
    state=json.loads(saved[0]) if saved else new_state()
    if not saved and job.get('job_profile'):
        from .profiles import validate
        now=datetime.datetime.now(datetime.timezone.utc).date()
        state.update(job_profile=validate(job['job_profile']),improved=True,search_as_of=now.isoformat(),
                     structured_providers=structured_providers(ledger.config),content_routes=content_routes(ledger.config))
    if not saved and job.get('search_version',ledger.config.get('search_version'))=='intent-v2':
        now=datetime.datetime.now(datetime.timezone.utc).date()
        state.update(improved=True,search_as_of=now.isoformat(),focus_month=now.strftime('%B %Y'),focus_range='last 180 days')
    if not saved and 'content_routes' not in state:
        state['content_routes']=content_routes(ledger.config)
    if not saved and job.get('focus')=='recent_jobseekers':
        now=datetime.datetime.now(datetime.timezone.utc).date()
        state.update(focused=True,focus_month=now.strftime('%B %Y'),
                     focus_range=(now-datetime.timedelta(days=90)).strftime('%B %Y')+' through '+now.strftime('%B %Y'),
                     prior_urls=job.get('prior_urls',[]),seed_locations={})
        for seed in job.get('seed_prospects',[]):
            packet=screen(seed)
            if packet:
                packet['name_hint']=seed['name'];packet['seed_from_prior_run']=True
                state['packets'][packet['source_url']]=packet
                state['seed_locations'][packet['source_url']]=seed['location']
    root=Path(state_path);evidence=root/'evidence'/run_id;output=root/'results'
    evidence.mkdir(parents=True,exist_ok=True,mode=0o700);output.mkdir(exist_ok=True,mode=0o700)
    runtime=ledger.runtime_for(run_id)
    # Stop the whole job at the immutable deadline even if an HTTP read stalls.
    import signal
    termination=[]
    def expired(signum,frame):
        reason='RUNTIME_LIMIT_REACHED' if signum==signal.SIGALRM or time.time()>=runtime['session_deadline']-5 else 'SERVICE_TERMINATED'
        termination.append(reason)
        raise StopRun(reason)
    old_handler=signal.signal(signal.SIGALRM,expired)
    old_term=signal.signal(signal.SIGTERM,expired)
    signal.setitimer(signal.ITIMER_REAL,max(0.001,runtime['session_deadline']-time.time()))
    client=client or ProviderRouter(ledger,run_id,guard,DISCOVERY_PLUGINS)
    content_clients={}
    def fetch_content(plan):
        name=plan['content_provider']
        if name not in content_clients:
            content_clients[name]=CONTENT_PLUGINS[name](ledger,run_id,guard)
        receipt=content_clients[name].search(plan['query'],1)
        return receipt,getattr(content_clients[name],'last_observed_at',None)
    def checkpoint():
        ledger.db.execute('INSERT INTO autonomous_checkpoints VALUES(?,?) ON CONFLICT(run_id) DO UPDATE SET state_json=excluded.state_json',(run_id,json.dumps(state)))
        packets=sorted(state['packets'].values(),key=lambda p:-p['review_priority'])
        report=dict(run_id=run_id,status=state['status'],stop_reason=state['stop_reason'],
                    started_at=runtime['created'],session_deadline=runtime['session_deadline'],
                    runtime_seconds=round(time.time()-runtime['created'],2),completed_searches=len(state['queries']),
                    actual_provider_requests=ledger.db.execute('SELECT COUNT(*) FROM operations WHERE run_id=?',(run_id,)).fetchone()[0],
                    result_appearances=state['result_appearances'],unique_pages=len(packets),duplicates=state['duplicates'],
                    source_coverage=state['source_coverage'],checkpoints=state['checkpoints'],queries=state['queries'],
                    rankings=packets,verified_a=0,verified_b=0,review_required=True,
                    classification_note='Automated evidence screening only. No A/B without subsequent identity, trade and dated recruiting-signal review.',
                    budget=ledger.summary(),codex_or_model_api_calls=0)
        from .source_registry import coverage, VERSION
        report['source_plan_coverage']=coverage(state['queries'])
        report['source_registry_version']=VERSION
        report['source_access_note']='Public-index discovery only; completed queries are not proof of authenticated access or candidate availability.'
        if state.get('job_profile',{}).get('screening_version') == 'dual-experience-2026-09-11':
            from .dual_experience import summary as dual_summary
            report['candidate_target_progress']=dual_summary(packets)
        report['job_profile']=state.get('job_profile')
        report['network_dispatch_attempts']=ledger.db.execute("SELECT COUNT(*) FROM audit WHERE run_id=? AND event='NETWORK_DISPATCH'",(run_id,)).fetchone()[0]
        report['provider_yield']={provider:dict(searches=sum(q.get('provider')==provider for q in state['queries']),result_appearances=sum(q['result_count'] for q in state['queries'] if q.get('provider')==provider)) for provider in ledger.config['providers']}
        report['track_packet_counts']={t['id']:sum(t['id'] in p.get('track_hints',[]) and p['classification']=='C — Provisional' for p in packets) for t in state.get('job_profile',{}).get('tracks',[])}
        report['track_count_note']='Overlapping unverified page hints, not distinct qualified people.'
        atomic_json(output/(run_id+'.json'),report)
        lines=['# RecruitMe standalone research checkpoint',f"Status: {state['status']}",f"Stop reason: {state['stop_reason']}",
               f"Completed searches: {len(state['queries'])}; unique pages: {len(packets)}; duplicates: {state['duplicates']}.",
               'A/B classification requires subsequent evidence review. These are provisional page packets, not verified people.','']
        for p in packets:
            lines.extend([f"## {p['name_hint'] or p['title'] or 'Unidentified page'}",p['classification'],p['source_url'],
                          'Possible signal: '+str(p['signal_excerpt']),
                          'Publication metadata (signal date unconfirmed): '+str(p['published_date_metadata']),
                          'Review priority: '+str(p['review_priority']),''])
        temp=output/(run_id+'.md.tmp');temp.write_text('\n'.join(lines));temp.replace(output/(run_id+'.md'))
    try:
        checkpoint()
        while True:
            guard()
            plan=next_query(state)
            if ledger.config.get('web_search_policy'):
                plan=web_policy_plan(state,plan,ledger.config)
            state['pending']=plan;checkpoint()
            observed=None
            if plan.get('content_provider'):
                response,observed=fetch_content(plan)
                plan['provider']=plan['content_provider']
            elif state.get('improved'):
                response=client.search(plan['query'],10,options=plan.get('options'),provider=plan.get('provider',job.get('provider')))
            else:response=client.search(plan['query'],5)
            if ledger.config.get('web_search_policy') and not plan.get('content_provider'):
                plan['provider']=response.get('provider','exa_free')
            stamp=datetime.datetime.fromtimestamp(observed or getattr(client,'last_observed_at',None) or time.time(),datetime.timezone.utc).isoformat()
            raw_path=evidence/('search-'+str(len(state['queries']))+'.json')
            atomic_json(raw_path,{'query':plan['query'],'retrieved_at':stamp,'response':response,'untrusted_data':True})
            consume(state,plan,response,stamp,raw_path)
            diminishing=False
            if len(state['queries'])%20==0:
                diminishing=evaluate_yield(state)
                ledger.event(run_id,'AUTONOMOUS_YIELD_CHECK',json.dumps(state['checkpoints'][-1]))
            checkpoint()
            if diminishing:raise StopRun('DIMINISHING_RETURNS: three materially different low-yield strategies after >=120 searches')
            sleep(min(3,max(0,runtime['session_deadline']-time.time())))
    except BaseException as error:
        state['status']='STOPPED'
        state['stop_reason']=termination[-1] if termination else ('RUNTIME_LIMIT_REACHED' if time.time()>=runtime['session_deadline'] else (str(error) if isinstance(error,StopRun) else type(error).__name__))
        if not termination and time.time()<runtime['session_deadline'] and isinstance(error,StopRun) and stop_code(error) != 'GUARD_STOP':
            state['stop_reason']=stop_code(error)+': '+str(error)
        ledger.stop(run_id,state['stop_reason'])
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old_handler);signal.signal(signal.SIGTERM,old_term)
        checkpoint()
