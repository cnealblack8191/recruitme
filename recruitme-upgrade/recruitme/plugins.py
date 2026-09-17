"""Opt-in fixed-endpoint adapters. All requests use the existing durable ledger.

No registrations, account upgrades, contact enrichment, retries or credential export.
Content adapters accept one approved public URL, never arbitrary batch/crawl jobs.
"""
import os
import stat
import urllib.parse
import urllib.request
from .budget import StopRun, money
from .exa_keyed import ExaKeyed, load_key as exa_key
from .tavily import Tavily, load_key as tavily_key
from .connectors import ExaFree

EXPIRES='2026-10-12'

def secret(name):
    import grp
    try:
        fd=os.open('/etc/recruitme/'+name+'-api-key',os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd) as f:
            s=os.fstat(f.fileno())
            if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_gid!=grp.getgrnam('recruitme').gr_gid or s.st_mode & 0o137:
                raise StopRun('Unsafe provider credential permissions')
            key=f.read(513).strip()
        if not 8<=len(key)<=512 or any(c.isspace() for c in key):raise StopRun('Invalid credential format')
        return key
    except OSError:raise StopRun('Provider credential unavailable') from None

def filtered_query(query,options):
    if options.get('start_date') or options.get('end_date'):
        raise StopRun('This adapter cannot guarantee publication-date filtering')
    includes=options.get('include_domains',[])
    if includes:query+=' ('+' OR '.join('site:'+d for d in includes)+')'
    query+=''.join(' -site:'+d for d in options.get('exclude_domains',[]))
    if len(query)>2000:raise StopRun('Query too long')
    return query

class Plugin(ExaKeyed):
    unit_price='0.005'
    credential_name=None
    capability='discovery'
    @staticmethod
    def accepts_options(options):
        return not options.get('start_date') and not options.get('end_date')
    @classmethod
    def credentials_available(cls,config):
        try:secret(cls.credential_name or cls.name);return True
        except StopRun:return False
    def credential(self):return secret(self.credential_name or self.name)
    def pricing(self,count):
        if type(count) is not int or not 1<=count<=10:raise StopRun('Expected 1-10 results')
        return money(self.unit_price),self.name+'-2026-09-12',EXPIRES
    def headers(self,key):return {'Content-Type':'application/json','Authorization':'Bearer '+key,'User-Agent':'RecruitMe/0.4'}

LINKEDIN_PEOPLE_DOMAINS=('linkedin.com','www.linkedin.com','linkedin.com/in','www.linkedin.com/in')

class ExaPeople(Plugin):
    name='exa_people';unit_price='0.007';credential_name='exa'
    @staticmethod
    def accepts_options(options):
        # People search takes no dates or exclusions; a LinkedIn include filter is fine.
        return set(options)<={'include_domains'} and all(d in LINKEDIN_PEOPLE_DOMAINS for d in options.get('include_domains',[]))
    def credential(self):return exa_key()
    def request_body(self,query,count,options):
        if options.get('start_date') or options.get('end_date') or options.get('exclude_domains'):
            raise StopRun('Exa people search does not support date or excluded-domain filters')
        if any(d not in LINKEDIN_PEOPLE_DOMAINS for d in options.get('include_domains',[])):
            raise StopRun('Unsupported people-search domain')
        return {'query':query,'category':'people','type':'auto','numResults':count,'contents':{'text':{'maxCharacters':12000}}}
    def headers(self,key):return {'Content-Type':'application/json','x-api-key':key}

class Brave(Plugin):
    name='brave';endpoint='https://api.search.brave.com/res/v1/web/search'
    def request_body(self,query,count,options):
        return {'q':filtered_query(query,options),'count':count,'country':'US','search_lang':'en','extra_snippets':'true'}
    def build_request(self,body,key):
        return urllib.request.Request(self.endpoint+'?'+urllib.parse.urlencode(body),headers={'X-Subscription-Token':key,'Accept':'application/json'})
    def normalize(self,result):
        if result.get('error'):raise StopRun('Brave provider error')
        if not isinstance(result.get('web',{}),dict):raise StopRun('Invalid Brave response')
        return {'results':[{'title':r.get('title'),'url':r.get('url'),'text':'\n'.join([r.get('description','')]+r.get('extra_snippets',[]))} for r in result.get('web',{}).get('results',[])]}

class SerpAPI(Plugin):
    name='serpapi';unit_price='0.025';endpoint='https://serpapi.com/search.json'
    def request_body(self,query,count,options):
        # Google may return ten even for smaller requested counts. Bound output below.
        self.requested_count=count
        return {'engine':'google','q':filtered_query(query,options),'num':10,'gl':'us','hl':'en'}
    def build_request(self,body,key):
        return urllib.request.Request(self.endpoint+'?'+urllib.parse.urlencode({**body,'api_key':key}))
    def normalize(self,result):
        if result.get('error'):raise StopRun('SerpAPI provider error')
        return {'results':[{'title':r.get('title'),'url':r.get('link'),'text':r.get('snippet','')} for r in result.get('organic_results',[])[:self.requested_count]]}

class SingleURL(Plugin):
    capability='content'
    def request_body(self,query,count,options):
        if count!=1 or options:raise StopRun('Content retrieval requires exactly one URL and no search filters')
        u=urllib.parse.urlsplit(query)
        allow=self.ledger.config['providers'].get(self.name,{}).get('allowed_domains',[])
        if u.scheme!='https' or u.username or u.password or u.port not in (None,443) or not u.hostname or not any(u.hostname==d or u.hostname.endswith('.'+d) for d in allow):
            raise StopRun('Content URL must match an operator-approved public domain')
        # Explicit host allowlist only; no browser cookies, crawl, images or subpages.
        return self.content_body(query)

class ExaContents(SingleURL):
    name='exa_contents';endpoint='https://api.exa.ai/contents';unit_price='0.001';credential_name='exa'
    def credential(self):return exa_key()
    def headers(self,key):return {'Content-Type':'application/json','x-api-key':key}
    def content_body(self,url):return {'urls':[url],'text':{'maxCharacters':24000},'livecrawl':'fallback','subpages':0}

class TavilyExtract(SingleURL):
    name='tavily_extract';endpoint='https://api.tavily.com/extract';unit_price='0.008';credential_name='tavily'
    def credential(self):return tavily_key()
    def content_body(self,url):return {'urls':[url],'extract_depth':'basic','format':'text','include_images':False,'include_usage':True}
    def normalize(self,result):
        if result.get('error') or result.get('detail'):raise StopRun('Tavily extraction failed')
        rows=result.get('results')
        if not isinstance(rows,list):raise StopRun('Missing extraction results')
        for r in rows:r['text']=r.get('raw_content','')
        credits=result.get('usage',{}).get('credits')
        if credits is not None:result['costDollars']={'total':str(float(credits)*0.008)}
        return result

class PDLFree(Plugin):
    name='pdl_free';credential_name='pdl';unit_price='0';endpoint='https://api.peopledatalabs.com/v5/person/search'
    capability='structured_people'
    @property
    def max_results(self):
        limit=self.ledger.config['providers'].get(self.name,{}).get('max_records_per_request',10)
        if type(limit) is not int or not 1<=limit<=10:
            raise StopRun('Invalid PDL per-request record limit')
        return limit
    @staticmethod
    def accepts_options(options):return not options
    def pricing(self,count):
        p=self.ledger.config['providers'].get(self.name,{})
        if type(count) is not int or not 1<=count<=self.max_results:
            raise StopRun('PDL request exceeds configured record limit')
        # At most ten calls of ten records ever, unless an operator reviews/reset policy.
        if p.get('account_plan')!='free' or p.get('paid_overages_disabled') is not True or not 1<=p.get('poc_query_limit',0)<=10:
            raise StopRun('PDL requires verified free-only account and maximum ten lifetime requests')
        return super().pricing(count)
    def request_body(self,query,count,options):
        if options:raise StopRun('PDL uses structured search, not web publication filters')
        # Explicit exact-field filters use the provider's supported term clauses.
        # Retain the legacy text route for existing saved jobs.
        if query.lstrip().startswith('{'):
            import json
            try:filters=json.loads(query)
            except (TypeError,ValueError):raise StopRun('Invalid PDL field filters') from None
            # Exact-term fields only. Role/sub-role taxonomy keys let a career-transition
            # search ask for current recruiting work plus a past electrical title.
            allowed={'full_name','job_title','job_title_role','job_title_sub_role','location_region','location_country',
                     'location_metro','experience.title.name','experience.title.role','experience.title.sub_role'}
            if (not isinstance(filters,dict) or not filters or not set(filters)<=allowed
                or any(not isinstance(v,str) or not v.strip() or len(v)>300 for v in filters.values())):
                raise StopRun('Unsupported PDL field filters')
            return {'query':{'bool':{'must':[{'term':{k:v.lower().strip()}} for k,v in filters.items()]}},'size':count,'pretty':False}
        return {'query':{'bool':{'must':[{'query_string':{'query':query,'fields':['job_title','experience.title.name','location_name']}}]}},'size':count,'pretty':False}
    def headers(self,key):return {'Content-Type':'application/json','X-Api-Key':key}
    def normalize(self,result):
        if result.get('status')!=200 or not isinstance(result.get('data'),list):raise StopRun('PDL did not return records')
        rows=[]
        for r in result['data']:
            lines=[r.get('job_title') or '',r.get('location_name') or '','## Experience']
            for e in r.get('experience') or []:
                lines+=['### '+((e.get('title') or {}).get('name') or ''),((e.get('company') or {}).get('name') or ''),str(e.get('start_date') or '')+' - '+str(e.get('end_date') or 'Present')]
            url=r.get('linkedin_url') or ''
            if not isinstance(url,str):url=''
            if url and not url.startswith('https://'):url='https://'+url
            rows.append({'title':r.get('full_name') if isinstance(r.get('full_name'),str) else '',
                'url':url,'text':'\n'.join(line if isinstance(line,str) else '' for line in lines),
                'employment_history':r.get('experience') or []})
        return {'results':rows}

class BrightDataProfile(SingleURL):
    name='bright_data';credential_name='brightdata';unit_price='0.0015'
    endpoint='https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_l1viktl72bvl7bjuj0&format=json'
    def content_body(self,url):
        u=urllib.parse.urlsplit(url)
        if u.hostname not in ('linkedin.com','www.linkedin.com') or not u.path.startswith('/in/'):
            raise StopRun('Bright Data adapter accepts public LinkedIn personal-profile URLs only')
        return [{'url':url}]
    def response_envelope(self,result):
        if not isinstance(result,list) or len(result)!=1:
            # Async fallback can complete only the single submitted record. Keep reservation.
            raise StopRun('Synchronous profile not returned; reservation retained; no automatic resubmission')
        row=result[0]
        if row.get('error') or row.get('error_code'):raise StopRun('Profile retrieval failed')
        lines=[row.get('position') or '',row.get('city') or '',row.get('about') or '', '## Experience']
        for e in row.get('experience') or []:
            if not isinstance(e,dict):continue
            lines+=['### '+str(e.get('title') or e.get('position') or ''),str(e.get('company') or e.get('company_name') or ''),str(e.get('start_date') or '')+' - '+str(e.get('end_date') or ''),str(e.get('description') or '')]
        return {'results':[{'url':row.get('url'),'title':row.get('name'),'text':'\n'.join(lines)}]}

class ApolloPeople(Plugin):
    """Apollo's zero-credit search only; partial identities stay unverified."""
    name='apollo';credential_name='apollo';unit_price='0'
    endpoint='https://api.apollo.io/api/v1/mixed_people/api_search'
    capability='structured_people'
    @staticmethod
    def accepts_options(options):return not options
    def headers(self,key):return {'Content-Type':'application/json','x-api-key':key}
    def request_body(self,query,count,options):
        if options:raise StopRun('Apollo discovery does not support web date/domain filters')
        if query.lstrip().startswith('{'):
            import json
            try:filters=json.loads(query)
            except (TypeError,ValueError):raise StopRun('Invalid Apollo field filters') from None
            allowed={'person_titles':list,'person_locations':list,'q_keywords':str}
            if (not isinstance(filters,dict) or not filters or not set(filters)<=set(allowed)
                or any(not isinstance(v,allowed[k]) or not v or len(v)>300 for k,v in filters.items())
                or any(not isinstance(x,str) or not x.strip() or len(x)>100 for k,v in filters.items() if k!='q_keywords' for x in v)):
                raise StopRun('Unsupported Apollo field filters')
            return {**filters,'page':1,'per_page':count}
        return {'q_keywords':query,'page':1,'per_page':count}
    def normalize(self,result):
        if result.get('error') or not isinstance(result.get('people'),list):
            raise StopRun('Apollo did not return people search results')
        rows=[]
        for person in result['people']:
            identifier=person.get('id')
            if not isinstance(identifier,str) or not identifier:continue
            # Link to the API provenance; a free search does not supply a verified
            # full identity, LinkedIn URL, email or telephone number.
            rows.append({'title':str(person.get('first_name') or '')+' (partial Apollo record)',
                'url':self.endpoint+'#'+urllib.parse.quote(identifier,safe=''),
                'text':'Unverified partial identity.\n'+str(person.get('title') or '')+'\n'+str((person.get('organization') or {}).get('name') or '')})
        return {'results':rows,'costDollars':{'total':'0'}}

class Coresignal(Plugin):
    """Base preview and single-profile collect share one 10-credit request ledger."""
    name='coresignal';credential_name='coresignal';unit_price='0'
    capability='structured_people'
    endpoint='https://api.coresignal.com/cdapi/v2/employee_base'
    @staticmethod
    def accepts_options(options):return not options
    def pricing(self,count):
        import datetime
        p=self.ledger.config['providers'].get(self.name,{})
        if (p.get('account_plan')!='free_trial' or p.get('credits_per_request')!=10
            or type(p.get('poc_query_limit')) is not int or not 1<=p['poc_query_limit']<=20
            or p.get('trial_ends_at')!='2026-09-19T00:00:00+00:00'
            or datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(p['trial_ends_at'])):
            raise StopRun('Coresignal free trial allowance requires review')
        super().pricing(count)
        return money('0'),'coresignal-2026-09-14','2026-09-19'
    def request_body(self,query,count,options):
        import json,re
        if options:raise StopRun('Coresignal requires explicit structured filters')
        self.requested_count=count
        if query.startswith('https://'):
            u=urllib.parse.urlsplit(query)
            if (count!=1 or u.hostname not in ('linkedin.com','www.linkedin.com') or u.username or u.password
                or u.port not in (None,443) or u.query or u.fragment or not re.fullmatch(r'/in/[A-Za-z0-9_-]+/?',u.path)):
                raise StopRun('Coresignal collect requires one public LinkedIn profile URL')
            return {'collect_slug':u.path.strip('/').split('/')[1]}
        try:filters=json.loads(query)
        except (ValueError,TypeError):raise StopRun('Coresignal discovery requires a JSON filter object') from None
        allowed={'full_name','headline','location','industry','summary','country','experience_title','experience_company_name'}
        if (not isinstance(filters,dict) or not filters or not set(filters)<=allowed
            or any(not isinstance(v,str) or not v.strip() or len(v)>300 for v in filters.values())):
            raise StopRun('Unsupported Coresignal filters')
        return {'filters':filters}
    def headers(self,key):return {'Content-Type':'application/json','apikey':key}
    def build_request(self,body,key):
        import json
        if 'collect_slug' in body:
            return urllib.request.Request(self.endpoint+'/collect/'+urllib.parse.quote(body['collect_slug'],safe=''),headers=self.headers(key))
        return urllib.request.Request(self.endpoint+'/search/filter/preview',data=json.dumps(body['filters']).encode(),method='POST',headers=self.headers(key))
    def response_envelope(self,result):
        records=result if isinstance(result,list) else [result]
        if len(records)>20 or any(not isinstance(r,dict) or r.get('error') or not r.get('id') for r in records):
            raise StopRun('Unexpected Coresignal employee response; reservation retained')
        rows=[]
        for r in records[:self.requested_count]:
            lines=[str(r.get(k) or '') for k in ('headline','location','summary')]
            for e in r.get('experience') or []:
                if isinstance(e,dict):lines += [str(e.get(k) or '') for k in ('title','company_name','date_from','date_to','description')]
            rows.append({'title':str(r.get('full_name') or ''),'url':str(r.get('profile_url') or ''),'text':'\n'.join(lines)})
        return {'results':rows}


DISCOVERY_PLUGINS={c.name:c for c in (ExaFree,ExaKeyed,Tavily,ExaPeople,Brave,SerpAPI,PDLFree,ApolloPeople,Coresignal)}
CONTENT_PLUGINS={c.name:c for c in (ExaContents,TavilyExtract,BrightDataProfile,Coresignal)}

def disabled_config():
    """Suggestions only. Never merges into a live config or changes past caps."""
    return {c.name:dict(enabled=False,approved=False,price_version=c.name+'-2026-09-12',
            operations={'search':c.unit_price},poc_limit_usd='5',run_limit_usd='1',
            poc_query_limit=10 if c is PDLFree else 100,run_query_limit=10,max_attempts=1,
            operation_purposes={'search':'discovery' if c.capability!='content' else 'enrichment'})
            for c in (ExaPeople,Brave,SerpAPI,PDLFree,ApolloPeople,ExaContents,TavilyExtract,BrightDataProfile)}
