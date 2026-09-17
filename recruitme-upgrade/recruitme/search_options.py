"""Provider-neutral, strictly bounded filters and cache identity."""
import datetime
import json
import re
from .budget import StopRun


def validate_options(options=None):
    o=dict(options or {})
    if set(o)-{'include_domains','exclude_domains','start_date','end_date'}:
        raise StopRun('Unsupported or unpriced search option')
    for k in ('include_domains','exclude_domains'):
        if k not in o:continue
        if not isinstance(o[k],list) or len(o[k])>20 or any(not isinstance(d,str) or not re.fullmatch(r'[A-Za-z0-9.-]+(?:/[A-Za-z0-9_./-]*)?',d) or '.' not in d.split('/')[0] for d in o[k]):
            raise StopRun('Invalid bounded domain filter')
        o[k]=sorted(set(o[k]))
        # An empty domain list is no filter. Dropping it keeps filter-free plans
        # eligible for adapters that accept no web options (structured people data).
        if not o[k]:del o[k]
    for k in ('start_date','end_date'):
        if k not in o:continue
        try:
            if not isinstance(o[k],str) or datetime.date.fromisoformat(o[k]).isoformat()!=o[k]:raise ValueError()
        except (ValueError,TypeError):raise StopRun('Invalid publication date filter') from None
    if o.get('start_date','0000')>o.get('end_date','9999'):raise StopRun('Reversed publication date range')
    return o


def logical_search(query,count,options=None):
    o=validate_options(options)
    if not o:return query if count==5 else json.dumps([query,count])
    return json.dumps({'query':query,'count':count,'options':o},sort_keys=True,separators=(',',':'))
