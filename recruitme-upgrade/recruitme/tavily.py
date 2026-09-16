"""Official basic search only. No auto-depth, upgrades, extraction or outreach."""
import os,stat
from .budget import StopRun,money
from .exa_keyed import ExaKeyed

KEY_FILE='/etc/recruitme/tavily-api-key'
PRICE_VERSION='tavily-basic-2026-09-08'
PRICE_VALID_UNTIL='2026-10-08'

def load_key():
    try:
        import grp
        fd=os.open(KEY_FILE,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd) as f:
            s=os.fstat(f.fileno())
            if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_gid!=grp.getgrnam('recruitme').gr_gid or s.st_mode & 0o137:
                raise StopRun('Unsafe Tavily credential permissions')
            key=f.read(513).strip()
        if not key.startswith('tvly-') or not 8<=len(key)<=512 or any(c.isspace() for c in key):raise StopRun('Invalid Tavily credential format')
        return key
    except OSError:raise StopRun('Tavily credential unavailable') from None

class Tavily(ExaKeyed):
    name='tavily'
    endpoint='https://api.tavily.com/search'
    quota_codes=(402,429,432,433)

    @staticmethod
    def credentials_available(config):
        try:load_key();return True
        except StopRun:return False

    def credential(self):return load_key()
    def tools(self):return [{'name':'official_tavily_basic_search'}]
    def pricing(self,count):
        if type(count) is not int or not 1<=count<=10:raise StopRun('Tavily requires 1-10 results')
        # Reserve PAYG maximum even if the account consumes free credits.
        return money('0.008'),PRICE_VERSION,PRICE_VALID_UNTIL

    def request_body(self,query,count,options):
        return dict(query=query,max_results=count,search_depth='basic',auto_parameters=False,
                    topic='general',include_answer=False,include_raw_content=False,
                    include_images=False,include_usage=True,**options)

    def headers(self,key):
        return {'Content-Type':'application/json','Authorization':'Bearer '+key,'User-Agent':'RecruitMe/0.3'}

    def normalize(self,result):
        if result.get('detail') or result.get('error'):
            import json
            from .governors import ProviderLimitReached
            detail=json.dumps(result.get('detail') or result.get('error')).lower()
            if any(s in detail for s in ('exceeds your plan','pay-as-you-go limit','excessive requests','quota exceeded')):
                raise ProviderLimitReached('PROVIDER_LIMIT_REACHED: tavily')
            raise StopRun('Tavily provider error')
        credits=result.get('usage',{}).get('credits')
        if credits is not None:
            if type(credits) not in (int,float) or credits<0:raise StopRun('Invalid Tavily usage')
            # Parent reconciles/freeze on a higher observed charge.
            from decimal import Decimal
            result['costDollars']={'total':str(Decimal(str(credits))*Decimal('0.008'))}
        for row in result.get('results',[]):
            if not isinstance(row,dict):raise StopRun('Invalid Tavily result')
            row['text']=row.get('content','')
            row['publishedDate']=row.get('published_date')
        return result
