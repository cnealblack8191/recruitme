"""Read-only allowlisted export. Contains no credentials, contact details or raw bodies."""
import datetime,hashlib,json,pathlib,sqlite3,sys
from recruitme.web_snapshot import discovery_rows, reviewed_rows
ROOT=pathlib.Path('/var/lib/recruitme')
db=sqlite3.connect('file:'+str(ROOT/'recruitme.db')+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
def utc(value):return datetime.datetime.fromtimestamp(value,datetime.timezone.utc).isoformat()
runs=[];candidates=[]
for row in db.execute('SELECT * FROM runs ORDER BY created DESC LIMIT 50'):
    r={}
    filename=ROOT/'results'/(row['id']+'.json')
    if filename.is_file():r=json.loads(filename.read_text())
    spend=db.execute('SELECT COALESCE(SUM(COALESCE(actual,reserved)),0) FROM operations WHERE run_id=?',(row['id'],)).fetchone()[0]/1e6
    rows=r.get('rankings',[])
    reserved=db.execute('SELECT COALESCE(SUM(reserved),0) FROM operations WHERE run_id=? AND actual IS NULL',(row['id'],)).fetchone()[0]/1e6
    provider_spend=[dict(id=p['provider'],spend=p['spend']/1e6) for p in db.execute('SELECT provider,SUM(COALESCE(actual,reserved)) AS spend FROM operations WHERE run_id=? GROUP BY provider',(row['id'],))]
    runs.append(dict(id=row['id'],status=row['status'],createdAt=utc(row['created']),spend=spend,cap=row['cap']/1e6,reserved=reserved,providerSpend=provider_spend,pages=len(rows),verified=sum(bool(p.get('grade_verified') and p.get('candidate_grade') in 'ABCD') for p in rows),stopReason=str(r.get('stop_reason') or '')[:500]))
    termination=db.execute("SELECT detail FROM audit WHERE run_id=? AND event='RUN_TERMINATION' ORDER BY id DESC LIMIT 1",(row['id'],)).fetchone()
    if termination:
        detail=json.loads(termination['detail'])
        runs[-1]['stopReason']=(str(detail.get('code',''))+': '+str(detail.get('reason','')))[:500]
    if '--meter' not in sys.argv:
        reviewed=reviewed_rows(db,row['id'])
        candidates.extend(reviewed + discovery_rows(row['id'],rows))
        runs[-1]['verified']=sum(c['verified'] for c in reviewed)
providers=[]
config=json.loads(pathlib.Path('/etc/recruitme/config.json').read_text())
from recruitme.plugins import DISCOVERY_PLUGINS, CONTENT_PLUGINS
for name in dict.fromkeys([*config['providers'],*DISCOVERY_PLUGINS,*CONTENT_PLUGINS]):
    p=config['providers'].get(name,{})
    spend=db.execute('SELECT COALESCE(SUM(COALESCE(actual,reserved)),0) FROM operations WHERE provider=?',(name,)).fetchone()[0]/1e6
    health=db.execute('SELECT status FROM provider_health WHERE provider=?',(name,)).fetchone()
    cls={**DISCOVERY_PLUGINS,**CONTENT_PLUGINS}.get(name)
    ready=getattr(cls,'credentials_available',lambda c: name=='exa_free')(p) if cls else False
    providers.append(dict(id=name,enabled=bool(p.get('enabled')),approved=bool(p.get('approved')),spend=spend,health=health[0] if health else ('Ready for configuration' if ready else 'Credential needed'),credentialReady=ready,unitCost=float(p['operations']['search']) if 'search' in p.get('operations',{}) else None,runLimit=float(p.get('run_limit_usd',0))))
snapshot=dict(generatedAt=utc(__import__('time').time()),pocSpend=db.execute('SELECT COALESCE(SUM(COALESCE(actual,reserved)),0) FROM operations').fetchone()[0]/1e6,runs=runs,candidates=candidates[:1000],providers=providers)
from recruitme.credit_snapshot import credit_rows
snapshot['credits']=credit_rows(ROOT,db)
snapshot['candidateSnapshotIncluded']='--meter' not in sys.argv
snapshot['candidatesTruncated']=len(candidates)>1000
if '--meter' in sys.argv or '--dashboard' in sys.argv:
    snapshot['runs']=snapshot['runs'][:20]
    while len(json.dumps(snapshot).encode())>20000 and snapshot['candidates']:
        snapshot['candidates'].pop()
        snapshot['candidatesTruncated']=True
    while len(json.dumps(snapshot).encode())>20000 and len(snapshot['runs'])>1:snapshot['runs'].pop()
print(json.dumps(snapshot))
