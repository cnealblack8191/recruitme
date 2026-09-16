"""Explicit approved routes only. No purchases, credential discovery or retries."""
import json
import os
from .budget import StopRun, money
from .governors import ProviderLimitReached, BudgetLimitReached, LocalRequestLimitReached
from .search_options import validate_options,logical_search

PHASES = ('free_discovery','low_cost_paid_discovery','targeted_content','finalist_enrichment')


class ProviderRouter:
    def __init__(self, ledger, run_id, guard, registry):
        self.ledger,self.run_id,self.guard,self.registry=ledger,run_id,guard,registry
        self.clients={}
        self.last_observed_at=None
        self.paid_cursor=0

    def search(self, query, count=5, options=None, provider=None):
        self.guard()
        options=validate_options(options)
        routes=self.ledger.config.get('provider_priority',{'free_discovery':['exa_free']})
        blocked=[]
        for phase in PHASES[:2]:
            names=list(routes.get(phase,[]))
            if phase == 'low_cost_paid_discovery' and names and self.ledger.config.get('web_search_policy'):
                offset=self.paid_cursor % len(names)
                names=names[offset:]+names[:offset]
            for name in names:
                if provider is not None and name!=provider:continue
                p=self.ledger.config['providers'].get(name,{})
                if p.get('explicit_discovery_only') and provider!=name:continue
                if not p.get('enabled') or not p.get('approved') or name not in self.registry:
                    continue
                if options and not getattr(self.registry[name],'supports_options',False):continue
                accepts=getattr(self.registry[name],'accepts_options',lambda o: True)
                if not accepts(options):continue
                if 'search' not in p.get('operations',{}):continue
                cost=money(p['operations']['search'])
                if cost and not self.ledger.config.get('paid_enabled'):continue
                if any(not os.environ.get(k) for k in p.get('credential_env',[])):continue
                ready=getattr(self.registry[name],'credentials_available',None)
                if ready and not ready(p):continue
                logical=logical_search(query,count,options)
                cached=self.ledger.cached_search(self.run_id,name,logical)
                if cached:
                    self.last_observed_at=cached['observed_at']
                    return cached['response']
                if self.ledger.provider_limited(name):
                    blocked.append((name,'provider'));continue
                # An exhausted source allocation must not stop other eligible sources.
                if self.ledger.total(self.run_id,name)+cost > money(p['run_limit_usd']):
                    blocked.append((name,'budget'));continue
                if self.ledger.total(provider=name)+cost > money(p['poc_limit_usd']):
                    blocked.append((name,'budget'));continue
                if self.ledger.db.execute('SELECT COUNT(*) FROM operations WHERE provider=? AND run_id=?',(name,self.run_id)).fetchone()[0] >= p['run_query_limit']:
                    blocked.append((name,'local_request'));continue
                if self.ledger.db.execute('SELECT COUNT(*) FROM operations WHERE provider=?',(name,)).fetchone()[0] >= p['poc_query_limit']:
                    blocked.append((name,'local_request'));continue
                try:
                    if name not in self.clients:
                        client=self.registry[name](self.ledger,self.run_id,self.guard)
                        client.initialize()
                        client.tools()
                        self.clients[name]=client
                    client=self.clients[name]
                    bounded_count=min(count,getattr(client,'max_results',10))
                    result=client.search(query,bounded_count,options=options) if options else client.search(query,bounded_count)
                    self.last_observed_at=getattr(client,'last_observed_at',None)
                    if phase == 'low_cost_paid_discovery':self.paid_cursor+=1
                    return result
                except ProviderLimitReached:
                    blocked.append((name,'provider'))
                    continue
        detail=json.dumps(dict(blocked),sort_keys=True)
        # Preserve each exhausted allocation; never attribute a local cap to an API.
        if any(reason=='budget' for _,reason in blocked):
            error=BudgetLimitReached('No eligible route remains; '+detail)
        elif any(reason=='local_request' for _,reason in blocked):
            error=LocalRequestLimitReached('No eligible route remains; '+detail)
        elif blocked:
            error=ProviderLimitReached('PROVIDER_LIMIT_REACHED: '+detail)
        else:
            error=StopRun('NO_ELIGIBLE_PROVIDER: Check approved routes, credentials and supported filters')
        self.ledger.stop(self.run_id,error)
        raise error
