"""Evidence-oriented plans. Dates constrain retrieval, never prove signal dates."""
import datetime


# Keep social and trade sources enabled; this list is intentionally empty so
# we can evaluate every explicit channel with policy checks downstream.
RESTRICTED=[]
ROLES=('commercial electrician','journeyman electrician','journeyman wireman','lead electrician',
       'service electrician','industrial electrician','electrical foreman','electrical superintendent',
       'electrical project manager','commissioning electrician','shutdown outage electrician',
       'construction electrician','electrical project coordinator','controls electrician',
       'industrial wiring electrician','journeyman electrician')
SIGNALS=('available for work','seeking another employer','looking for another employer',
         'looking for my next project','looking for next employer','looking for next project',
         'project ending','assignment ending','demobilized','relocating','available immediately',
         'seeking employment','open to work','who is hiring','resume posted',
         'looking for work','ready for a new opportunity','hiring for immediate start',
         'project transition','assignment complete','recently completed project')
PLACES=('Doraville Georgia','Atlanta Georgia','Chamblee Georgia','Norcross Georgia','Tucker Georgia',
       'DeKalb County Georgia','Gwinnett County Georgia','Marietta Georgia','Lawrenceville Georgia',
       'Decatur Georgia','Sandy Springs Georgia','Duluth Georgia','Peachtree Corners Georgia',
       'Briarcliff Georgia','Kennesaw Georgia','Stone Mountain Georgia')
REGIONS=('Tennessee','Alabama','North Carolina','South Carolina','Florida','Georgia')
SOURCES=(
    ('open web','',('evidence','resume','availability')),
    ('linkedin','site:linkedin.com',('open to work','job history','profile')),
    ('postjobfree','site:postjobfree.com',('resumes','commercial','hire')),
    ('roadtechs','site:roadtechs.com',('availability board','labor force','electrical')),
    ('trade forum','site:electriciantalk.com',('commercial electrician','job change','forum')),
    ('reddit','site:reddit.com/r/electricians',('looking for work','open to work','resume')),
    ('indeed','site:indeed.com',('electrician','commercial electrician','recently available')),
    ('monster','site:monster.com',('electrical electrician','job change','resume')),
    ('careerbuilder','site:careerbuilder.com',('electrical journeyman','open to work','availability')),
    ('ziprecruiter','site:ziprecruiter.com',('looking for work','commercial electrician','Atlanta')),
    ('jobcase','site:jobcase.com',('looking for work','trade electrician','relocation')),
    ('monster jobs','site:careerarc.com',('resumes','commercial electrical','Georgia')),
    ('trade social','site:reddit.com/r/trades',('electrical electrician','work change','available now')),
)

def plan(state):
    from .discovery import plan as discovery_plan
    candidate = discovery_plan(state)
    candidate['options']['exclude_domains'] = list(RESTRICTED)
    return candidate


def legacy_plan(state):
    i=state['discovery_index'];n=len(state['queries'])
    now=datetime.date.fromisoformat(state['search_as_of'])
    options={'exclude_domains':RESTRICTED}
    # Every fourth group intentionally measures undated coverage, kept provisional.
    branch=(i//10)%4
    if branch!=3:
        days=(30,90,180,None)[branch]
        options.update(start_date=(now-datetime.timedelta(days=days)).isoformat(),end_date=now.isoformat())
    source_name,site,phrases=SOURCES[i%len(SOURCES)]
    place=PLACES[i%len(PLACES)] if i < 72 else REGIONS[(i//3)%len(REGIONS)]
    role=ROLES[i%len(ROLES)];signal=SIGNALS[(i//len(ROLES)+3*i)%len(SIGNALS)]
    extra=(('first person availability','recent resume','next employer project transition','public professional page')[branch]+' '+
          phrases[(i//len(ROLES))%len(phrases)])
    q=f'{site} {role} {signal} {place} {extra}'.strip()
    # Change variants indefinitely without resetting the shared run deadline.
    if i>=120:q+=' '+('construction','commissioning work','commercial field start','project transition')[ (i//120)%4 ]
    return {'query':q[:500],'purpose':'discovery',
            'strategy':('recent_availability','recent_resumes','transition_180_days','undated_review')[branch],
            'source_family':source_name,
            'target':None,'options':options}

def followup_options(state):
    return {'exclude_domains':RESTRICTED}
