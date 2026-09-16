"""Opt-in electrical-field plus recruiter/HR discovery, with review-only grades.

No model calls, authenticated LinkedIn access, outreach, or automatic verification.
"""
import datetime
import re
from urllib.parse import urlsplit
from .source_registry import apply_route

VERSION = 'dual-experience-2026-09-11'
ROLES = ('recruiter', 'human resources', 'talent acquisition', 'recruiting manager',
         'HR manager', 'staffing manager', 'talent acquisition specialist', 'HR generalist')
FIELD_ROLES = ('electrician', 'electrical foreman', 'journeyman electrician',
               'electrical superintendent', 'electrical apprentice', 'wireman')
REGIONS = ('Georgia', 'Alabama', 'Florida', 'Tennessee', 'North Carolina', 'South Carolina')
HR = re.compile(r'\b(recruiter|recruiting|recruitment|talent acquisition|human resources|HR (?:manager|generalist|specialist|coordinator|business partner)|staffing manager)\b', re.I)
FIELD = re.compile(r'\b(?:journeyman |master |apprentice |commercial |industrial |lead )?electrician\b|\belectrical (?:foreman|superintendent|apprentice)\b|\b(?:journeyman )?wireman\b', re.I)
PAST_FIELD = re.compile(r'\b(?:worked as (?:an? )?|former |previously (?:an? )?|started (?:my career )?as (?:an? )?|experience as (?:an? )?)(?:journeyman |master |apprentice |commercial |industrial |lead )?(?:electrician|electrical (?:foreman|superintendent|apprentice)|wireman)\b', re.I)
INTENT = re.compile(r'\b(open to work|opentowork|seeking employment|seeking (?:my |a )?(?:next|new) (?:role|opportunity|position)|looking for (?:work|a job|a new role|my next opportunity)|available for (?:work|hire)|laid off)\b', re.I)
RELOCATION = re.compile(r'\b(?:willing|open|able|ready) to (?:relocate|relocation)\b|\b(?:I am |I\x27m )?(?:relocating|moving) to\b', re.I)
NEGATIVE = re.compile(r'\b(?:not (?:currently )?(?:seeking|looking|available|open)|no longer (?:looking|seeking|available)|accepted (?:a |an |my )?(?:new )?(?:job|offer|position)|started (?:a |my )?new (?:job|position))\b', re.I)
TECHNICAL = re.compile(r'\b(?:technical interviews?|skills? assess(?:ment|ments)|assess(?:ing)? (?:electrical |candidate )?skills?|evaluat(?:e|ing) electricians?)\b', re.I)
PAY = re.compile(r'\b(?:pay rates?|wage rates?|compensation|salary recommendations?)\b', re.I)


def next_plan(state, provider):
    p=state['job_profile']; n=len(state['queries']); i=state['discovery_index']
    if n % 3 == 2:
        pool=sorted(state['packets'].values(), key=lambda x:-x['review_priority'])
        for packet in pool:
            if not packet.get('dual_experience_hint') or not packet.get('name_hint'):
                continue
            used=state['followups'].get(packet['source_url'],0)
            if used >= 3:
                continue
            terms=('electrician electrical field work history recruiter human resources',
                   '"open to work" "seeking" original post date current location',
                   'technical interviews skills assessment pay rates relocation')
            query=f'"{packet["name_hint"]}" {packet["source_url"]} {terms[used]}'[:500]
            if any(q.get('query')==query for q in state['queries']):
                continue
            return dict(query=query,purpose='corroboration/contact',strategy='dual_experience_review',
                        target=packet['source_url'],provider=p['discovery_provider'],options={},
                        source_family='person_evidence_followup',source_access='public_index_only')
    role=ROLES[(i//4)%len(ROLES)]; field=FIELD_ROLES[(i//len(ROLES))%len(FIELD_ROLES)]
    # Three local discovery queries for every Southeast query. No national search.
    regional=i%4==3
    place=REGIONS[(i//4)%len(REGIONS)] if regional else p['locations'][(i//4)%len(p['locations'])]
    variant=(i//8)%4
    query=(f'"{role}" "{field}" {place} '+
           ('experience resume','career background','previous experience','work history')[variant])
    options={}
    if regional:
        query += ' '+('"willing to relocate"','"open to work"','"open to relocation"','"seeking employment"')[(i//4)%4]
    elif i%8==2:
        query += ' "open to work"'
        now=datetime.date.fromisoformat(state['search_as_of'])
        options={'start_date':(now-datetime.timedelta(days=30)).isoformat(),'end_date':now.isoformat()}
    # Weight LinkedIn and open web; smaller routes still participate without fan-out.
    weighted=('linkedin','open_web','linkedin','postjobfree','linkedin','open_web','jobcase','shrm_atlanta')
    source=weighted[(i//4+i)%len(weighted)]
    result=apply_route(dict(query=query[:500],purpose='discovery',strategy='dual_southeast' if regional else 'dual_local',
                           target=None,provider=provider,options=options),0,'recruiter',{'source_ids':[source]})
    result['provider']=p['discovery_provider']
    result['screening_version']=VERSION
    return result


def excerpt(text, match):
    return text[max(0,match.start()-100):match.end()+180] if match else None


def apply_screen(packet, profile):
    if packet is None:
        return None
    text=re.split(r'## (?:Comments|Social)\b',packet['text'],maxsplit=1)[0]
    # Indexed activity can precede the actual profile heading. It is not work history.
    name=packet.get('name_hint')
    if name:
        heading=re.search(r'(?im)^#\s+'+re.escape(name)+r'\s*$',text)
        if heading:text=text[heading.start():]
    text=re.sub(r'(?ims)^#{1,3}\s*(?:Activity|Posts)\s*\n.*?(?=^#{1,3}\s*(?:Experience|About|Education)\b|\Z)','',text)
    text='\n\n'.join(p for p in text.split('\n\n') if not re.search(r'\b(?:Liked by|Reposted by|Shared by)\b',p,re.I))
    header=re.split(r'## (?:About|Experience|Education)\b',text,maxsplit=1)[0]
    role_pattern=r'\b(?:recruiter|recruiting manager|recruitment manager|talent acquisition|human resources|HR (?:manager|generalist|specialist|coordinator|business partner)|staffing manager)\b'
    hr=re.search(role_pattern,header,re.I)
    history=re.search(r'(?im)^\s*(?:##?\s*)?(?:work experience|employment history|experience)\s*[:\n]',text)
    history_text=text[history.end():] if history else ''
    # A skills list or "I recruit electricians" is not evidence of field employment.
    field=PAST_FIELD.search(text)
    field_history=None
    if not field:
        lines=history_text.splitlines()
        for index,line in enumerate(lines):
            if re.search(r'\b(?:recruit|hiring|seek|candidate|position available)',line,re.I):
                continue
            if FIELD.fullmatch(line.strip(' #*-\t')):
                field_history=line.strip();break
            if FIELD.search(line) and re.search(r'\b(?:19|20)\d{2}\b',line):
                field_history=line.strip();break
            if re.match(r'^\s*(?:#{1,3}\s*)?(?:journeyman |master |apprentice |commercial |industrial |lead )?(?:electrician|electrical (?:foreman|superintendent|apprentice)|wireman)\b',line,re.I) and re.search(r'\b(?:19|20)\d{2}\b',' '.join(lines[index+1:index+4])):
                field_history='\n'.join(lines[index:index+4]).strip();break
    dual=bool(hr and (field or field_history))
    names=[re.sub(r'\s+Georgia$','',x) for x in profile['locations']]+['Metro Atlanta','Atlanta Metropolitan Area','Greater Atlanta']
    location=next((x for x in names if re.search(r'\b'+re.escape(x)+r'\b',header,re.I)),None)
    region=next((x for x in REGIONS if re.search(r'\b'+re.escape(x)+r'\b',header,re.I)),None)
    signal=INTENT.search(text);relocate=RELOCATION.search(text)
    contradictory=bool(NEGATIVE.search(text) or packet.get('contradiction_flag'))
    personal=bool(signal and not contradictory and not packet.get('third_party_signal_flag') and not packet.get('hiring_ad_flag'))
    host=(urlsplit(packet['source_url']).hostname or '').lower()
    path=urlsplit(packet['source_url']).path
    person_page=bool(packet.get('name_hint') and ((host.endswith('linkedin.com') and path.startswith('/in/')) or
                     (host.endswith('postjobfree.com') and path.startswith('/resume/')) or
                     re.search(r'\bmy (?:resume|career|experience)\b',text,re.I)))
    eligible=dual and person_page and not packet.get('hiring_ad_flag')
    grade=None
    if eligible and location:
        grade=('A' if TECHNICAL.search(text) and PAY.search(text) else 'B') if personal else 'D'
    elif eligible and region and (personal or relocate) and not contradictory:
        grade='C'
    # Hints are explicitly not verified grades. Do not use publication metadata as intent date.
    packet.update(screening_version=VERSION,dual_experience_hint=dual,
        electrical_field_excerpt=excerpt(text,field) if field else field_history,
        recruiting_hr_excerpt=excerpt(header,hr),technical_interview_hint=bool(TECHNICAL.search(text)),
        pay_assessment_hint=bool(PAY.search(text)),local_scope_hint=bool(location),location_hint=location,
        southeast_location_hint=region,relocation_excerpt=excerpt(text,relocate),
        possible_recruiting_signal=personal,signal_excerpt=excerpt(text,signal),
        candidate_grade_hint=grade,candidate_grade=None,grade_verified=False,
        grade_review_reason='Confirm identity, career chronology and residence; A/B also require original personal signal date within 30 days. Interview/pay-setting ability needs assessment.',
        signal_date_confirmed=False,signal_date=None,signal_date_basis='UNKNOWN; verify original statement date',
        identity_confirmed=False,signal_subject_confirmed=False,contradiction_flag=contradictory,
        trade_match=bool(hr),commercial_industrial_match=dual,
        classification='C — Provisional' if grade else ('Passive Research Pool' if dual else 'Rejected'),
        review_priority=(60 if eligible else 20 if dual else 0)+(15 if location else 5 if region else 0)+(10 if personal else 0),
        track_hints=['electrical_recruiting'] if dual else [])
    return packet


def summary(packets):
    # Same normalized name is conservatively one cluster; collisions need manual review.
    clusters={}; hints={g:0 for g in 'ABCD'}
    for p in packets:
        grade=p.get('candidate_grade_hint')
        if grade not in hints or not p.get('name_hint'):
            continue
        key=re.sub(r'[^a-z]','',p['name_hint'].lower())
        if key not in clusters:
            clusters[key]=grade;hints[grade]+=1
    return dict(target_distinct_people=25,unverified_identity_clusters=len(clusters),
                proposed_grade_counts=hints,verified_candidate_count=0,
                target_met=False,note='Pages and name clusters are not verified distinct candidates. No automated claim that 25 candidates were found.')
