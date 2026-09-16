"""Pinned, bounded official Exa /search only. No purchases or automatic retries."""
import datetime
import json
import os
import stat
import time
import urllib.request
import urllib.error
from decimal import Decimal
from .budget import StopRun, money
from .governors import ProviderLimitReached
from .connectors import NoRedirect
from .search_options import validate_options,logical_search

KEY_FILE='/etc/recruitme/exa-api-key'
ENDPOINT='https://api.exa.ai/search'
PRICE_VERSION='exa-search-2026-09-07'
PRICE_VALID_UNTIL='2026-10-07'


def maximum_cost(count):
    # Pinned auto shape, <=10 results, included text; no summaries/subpages.
    if type(count) is not int or not 1<=count<=10:
        raise StopRun('Keyed Exa requires 1-10 results')
    return money('0.007')


def load_key():
    try:
        fd=os.open(KEY_FILE,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd) as f:
            st=os.fstat(f.fileno())
            import grp
            if not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or st.st_gid!=grp.getgrnam('recruitme').gr_gid or st.st_mode & 0o137:
                raise StopRun('Unsafe Exa credential permissions')
            key=f.read(513).strip()
        if not 8<=len(key)<=512 or any(c.isspace() for c in key):
            raise StopRun('Invalid Exa credential format')
        return key
    except OSError:
        raise StopRun('Exa credential unavailable') from None


class ExaKeyed:
    name='exa_keyed'
    supports_options=True
    endpoint=ENDPOINT
    quota_codes=(402,429)

    def credential(self):return load_key()

    def pricing(self,count):return maximum_cost(count),PRICE_VERSION,PRICE_VALID_UNTIL

    def request_body(self,query,count,options):
        body={'query':query,'type':'auto','numResults':count,
              'contents':{'text':{'maxCharacters':4000},'highlights':False,'subpages':0}}
        for key,field in (('include_domains','includeDomains'),('exclude_domains','excludeDomains')):
            if key in options:body[field]=options[key]
        if 'start_date' in options:body['startPublishedDate']=options['start_date']+'T00:00:00.000Z'
        if 'end_date' in options:body['endPublishedDate']=options['end_date']+'T23:59:59.999Z'
        return body

    def headers(self,key):return {'Content-Type':'application/json','x-api-key':key,'User-Agent':'RecruitMe/0.3'}

    def normalize(self,result):return result

    def response_envelope(self,result):return result

    def build_request(self, body, key):
        return urllib.request.Request(self.endpoint,data=json.dumps(body).encode(),method='POST',headers=self.headers(key))

    @staticmethod
    def credentials_available(config):
        try:load_key();return True
        except StopRun:return False

    def __init__(self,ledger,run_id,guard,opener=None):
        self.ledger,self.run_id,self.guard=ledger,run_id,guard
        self.opener=opener or urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())

    def initialize(self):
        # Official REST has no handshake; never reset state or issue setup requests.
        return None

    def tools(self):return [{'name':'official_exa_search'}]

    def search(self,query,count=5,options=None):
        self.guard()
        options=validate_options(options)
        maximum,version,expires=self.pricing(count)
        if not isinstance(query,str) or not 1<=len(query)<=500:raise StopRun('Invalid bounded query')
        p=self.ledger.config['providers'].get(self.name,{})
        if p.get('price_version')!=version or datetime.date.today()>=datetime.date.fromisoformat(expires):
            raise StopRun('Provider pricing requires re-verification')
        if money(p.get('operations',{}).get('search'))!=maximum:
            raise StopRun('Exa reservation does not match pinned maximum')
        if not self.ledger.session_for(self.ledger.check(self.run_id)):
            raise StopRun('Keyed Exa requires a persistent $25 budget session')
        key=self.credential()
        if key in query:raise StopRun('Credential must not appear in query')
        logical=logical_search(query,count,options)
        cached=self.ledger.cached_search(self.run_id,self.name,logical)
        if cached:
            self.last_observed_at=cached['observed_at'];return cached['response']
        body=self.request_body(query,count,options)
        op=self.ledger.reserve(self.run_id,self.name,'search',logical)
        self.last_operation_id=op
        try:
            remaining=self.ledger.dispatch(self.run_id,op)['deadline']-time.time()
            if remaining<=0:raise StopRun('RUNTIME_LIMIT_REACHED')
            req=self.build_request(body,key)
            with self.opener.open(req,timeout=min(25,remaining)) as response:
                raw=response.read(524289)
            if len(raw)>524288:raise StopRun('Exa response too large')
            # Never persist a reflected credential or arbitrary response headers.
            result=json.loads(raw.decode().replace(key,'[REDACTED]'))
            result=self.response_envelope(result)
            if not isinstance(result,dict):raise StopRun('Invalid Exa response')
            result=self.normalize(result)
            if result.get('error'):
                if result.get('tag') in ('RATE_LIMIT_EXCEEDED','INSUFFICIENT_CREDITS','QUOTA_EXCEEDED'):
                    raise ProviderLimitReached('PROVIDER_LIMIT_REACHED: '+self.name)
                raise StopRun('Exa provider error')
            if not isinstance(result.get('results'),list) or len(result['results'])>count:
                raise StopRun('Unexpected Exa result shape')
            estimate=result.get('costDollars',{}).get('total')
            if estimate is not None and money(estimate)>maximum:
                self.ledger.reconcile(op,estimate)
                raise StopRun('Exa price breach; all operations frozen')
            content=[]
            from urllib.parse import urlsplit
            def excluded(row):
                if not isinstance(row,dict):raise StopRun('Invalid provider result')
                host=(urlsplit(str(row.get('url',''))).hostname or '').lower()
                return any(host==d.split('/')[0] or host.endswith('.'+d.split('/')[0]) for d in options.get('exclude_domains',[]))
            # Do not checkpoint bodies that violate explicit source exclusions.
            original_count=len(result['results'])
            result['results']=[r for r in result['results'] if not excluded(r)]
            result['excluded_result_count']=original_count-len(result['results'])
            for r in result['results']:
                if not isinstance(r,dict):raise StopRun('Invalid Exa result')
                content.append({'type':'text','text':'\n'.join(str(r.get(k,'')) if k!='url' else 'URL: '+str(r.get(k,'')) for k in ('title','url','publishedDate','author','text'))})
            receipt={'content':content,'provider_response':result,'provider':self.name,'search_options':options,'accounting_basis':'conservative_list_price_not_invoice'}
            self.last_observed_at=time.time()
            self.ledger.save_outcome(op,'SUCCESS',receipt,self.last_observed_at)
            # Estimated cost and free credits never release budget headroom.
            self.ledger.reconcile(op,str(Decimal(maximum)/1000000))
            return receipt
        except Exception as error:
            limited=isinstance(error,ProviderLimitReached) or (isinstance(error,urllib.error.HTTPError) and error.code in self.quota_codes)
            status='PROVIDER_LIMIT_REACHED' if limited else 'UNKNOWN'
            self.ledger.save_outcome(op,status,{'http_status':error.code} if isinstance(error,urllib.error.HTTPError) else None)
            if self.ledger.db.execute('SELECT state FROM operations WHERE id=?',(op,)).fetchone()[0]=='RESERVED':
                self.ledger.reconcile(op,None)
            if limited:raise ProviderLimitReached('PROVIDER_LIMIT_REACHED: '+self.name) from None
            if isinstance(error,StopRun):
                self.ledger.stop(self.run_id,error)
                raise
            self.ledger.stop(self.run_id,self.name+' failed; reservation retained; no retry')
            raise StopRun(self.name+' failed; reservation retained; no retry') from None
