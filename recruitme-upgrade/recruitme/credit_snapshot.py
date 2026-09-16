"""Allowlisted balance projection. Never export account responses or keys."""
import json,time,datetime

def credit_rows(root,db):
    try:
        path=root/'provider-balances.json'
        cache=json.loads(path.read_text()) if path.stat().st_size<100000 else {}
    except (OSError,ValueError):cache={}
    providers=cache.get('providers',{})
    checked=cache.get('checkedAt')
    def number(value):
        return value if type(value) in (int,float) and 0<=value<1e12 else None
    rows=[]
    for name in ('serpapi','tavily','brave','apollo','bright_data','pdl_free','coresignal','exa_keyed'):
        p=providers.get({'bright_data':'brightdata'}.get(name,name),{})
        r=dict(id=name,remaining=None,limit=None,unit='credits',basis='unavailable',checkedAt=None,renewsAt=None,note='Balance has not been verified.')
        if name=='serpapi':
            r.update(remaining=number(p.get('total_searches_left')),limit=number(p.get('searches_per_month')),unit='searches',renewsAt=p.get('plan_renewal_date'),note='Shared account search allowance.')
        elif name=='tavily':
            limit,used=number(p.get('plan_limit')),number(p.get('plan_usage'))
            r.update(remaining=max(0,limit-used) if limit is not None and used is not None else None,limit=limit,note='Plan credits; pay-as-you-go balances are separate.')
        elif name=='brave':
            used=db.execute('SELECT COALESCE(SUM(MAX(reserved,COALESCE(actual,0))),0) FROM operations WHERE provider=? AND timestamp>=?',('brave',time.time()-31*86400)).fetchone()[0]/1e6
            r.update(remaining=max(0,5-used),limit=5,unit='USD',basis='local',checkedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),note='RecruitMe allowance over a rolling 31 days. Excludes other apps; not Brave account balance.')
        elif name=='bright_data':
            r.update(remaining=number(p.get('balance')),unit='USD',note='Account dollar balance; pending charges are separate.')
        elif name in ('pdl_free','coresignal'):
            r['note']='Remaining credits can be captured from live API response headers; no balance recorded yet.'
        elif name=='exa_keyed':r['note']='Provider limit recorded. Check the Exa dashboard for its account balance.'
        if p.get('http_status')==403:r.update(checkedAt=checked,note='Balance API permission missing. Data access is separate.')
        if r['remaining'] is not None and r['basis']!='local':r.update(basis='provider',checkedAt=checked)
        rows.append(r)
    return rows
