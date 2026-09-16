import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from .budget import Ledger, StopRun
from .governors import stop_code
from .connectors import ExaFree
from .exa_keyed import ExaKeyed
from .tavily import Tavily
from .routing import ProviderRouter
from .plugins import DISCOVERY_PLUGINS, CONTENT_PLUGINS
from . import data


def disk_guard(path, minimum=2147483648):
    if shutil.disk_usage(path).free < max(2147483648, minimum):
        raise StopRun('Disk free space below 2 GiB safety threshold')


def atomic_json(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w',encoding='utf-8') as f:
        json.dump(value,f,indent=2,ensure_ascii=True)
        f.flush(); os.fsync(f.fileno())
    temporary.replace(path)


def run(config_path, state_path, job_path, probe=False):
    import fcntl  # Execution requires Linux locking; pure governor tests are portable.
    state = Path(state_path)
    config = json.loads(Path(config_path).read_text())
    state.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (state/'worker.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise StopRun('Another job is running') from None
        disk_guard(state,config['minimum_disk_free_bytes'])
        if probe:
            job={'run_id':'foundation-capability-check','budget_usd':'2.00','mode':'probe'}
        else:
            job=json.loads(Path(job_path).read_text())
        if job.get('web_profile'):
            from .search_policy import apply_search_policy
            config=apply_search_policy(config,job['web_profile'])
            config['research_window_id']=job['run_id']
        ledger = Ledger(state/'recruitme.db',config,state_root=state)
        data.initialize(ledger.db)
        if job.get('web_profile'):
            from decimal import Decimal
            committed=ledger.total()
            config['session']={'id':'session-'+job['run_id'],
                'limit_usd':str(Decimal(max(0,25000000-committed))/1000000),
                'high_value_only_after_usd':str(Decimal(max(0,20000000-committed))/1000000),
                'ends_at':(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=30)).isoformat()}
        run_id = job['run_id']
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',run_id):
            raise StopRun('Invalid run ID')
        ledger.create_run(run_id,job.get('budget_usd'),resume=job.get('resume',False))
        ledger.bind_manifest(run_id,job)
        if ledger.db.execute('SELECT status FROM runs WHERE id=?',(run_id,)).fetchone()[0]=='COMPLETE':
            return
        evidence_dir = state/'evidence'/run_id
        evidence_dir.mkdir(parents=True,mode=0o700,exist_ok=job.get('resume',False))
        def guard():
            disk_guard(state,config['minimum_disk_free_bytes'])
            ledger.check(run_id)
            # Fixed upper bound on retained POC evidence/results including SQLite.
            if sum(p.stat().st_size for p in state.rglob('*') if p.is_file()) > 1073741824:
                raise StopRun('RecruitMe data allowance exhausted')
        try:
            if job['mode']=='autonomous':
                from .autonomous import execute
                execute(ledger,run_id,state,job,guard)
                return
            elif job['mode'] in ('probe','discovery'):
                if job['mode']=='probe':
                    client=ExaFree(ledger,run_id,guard)
                    client.initialize()
                    tools=client.tools()
                    available=[t.get('name') for t in tools]
                    if 'web_search_exa' not in available:raise StopRun('Search tool unavailable')
                    atomic_json(evidence_dir/'capabilities.json',{'tools':tools,'search_executed':False})
                else:
                    client=ProviderRouter(ledger,run_id,guard,{**DISCOVERY_PLUGINS,'exa_free':ExaFree,'exa_keyed':ExaKeyed,'tavily':Tavily})
                if job['mode']=='discovery':
                    queries=job.get('queries',[])
                    if not 1<=len(queries)<=8:
                        raise StopRun('Expected one to eight operator-configured queries')
                    for i,query in enumerate(queries):
                        guard()
                        result=client.search(query,job.get('results_per_query',10),options=job.get('search_options'),provider=job.get('provider'))
                        stamp=datetime.datetime.fromtimestamp(getattr(client,'last_observed_at',None) or time.time(),datetime.timezone.utc).isoformat()
                        path=evidence_dir/('search-'+str(i)+'.json')
                        atomic_json(path,{'retrieved_at':stamp,'query':query,'response':result,'untrusted_data':True})
                        text='\n'.join(c.get('text','') for c in result.get('content',[]) if c.get('type')=='text')
                        # Parse links only, not names or professional facts. Preserve full source response.
                        urls=list(dict.fromkeys(re.findall(r'https?://[^\s<>\[\]()"\u0000-\u001f]+',text)))[:50]
                        for url in urls:
                            try: url=data.canonical_url(url.rstrip('.,;'))
                            except StopRun: continue
                            ident=hashlib.sha256((run_id+url).encode()).hexdigest()
                            pos=text.find(url)
                            excerpt=text[max(0,pos-100):pos+1900]
                            ledger.db.execute('INSERT OR IGNORE INTO discoveries(id,run_id,query,source_url,title,excerpt,retrieved_at,raw_evidence_path) VALUES(?,?,?,?,?,?,?,?)',
                                              (ident,run_id,query,url,None,excerpt,stamp,str(path)))
                        output=state/'results'; output.mkdir(mode=0o700,exist_ok=True)
                        atomic_json(output/(run_id+'.json'),data.report(ledger.db,run_id))
                        ledger.event(run_id,'DISCOVERY_SAVED','Query '+str(i)+' saved; identity/qualification review pending')
                else:
                    print(json.dumps({'capability_probe':'PASS','tools':available,'candidate_search_executed':False}))
            elif job['mode']=='content_review':
                provider=job.get('provider')
                urls=job.get('urls',[])
                if provider not in CONTENT_PLUGINS or not isinstance(urls,list) or not 1<=len(urls)<=10:
                    raise StopRun('Content review requires one approved adapter and 1-10 public URLs')
                client=CONTENT_PLUGINS[provider](ledger,run_id,guard)
                for i,url in enumerate(dict.fromkeys(urls)):
                    guard()
                    receipt=client.search(url,1)
                    atomic_json(evidence_dir/('full-profile-'+str(i)+'.json'),{
                        'source_url':url,'retrieved_at':client.last_observed_at,
                        'response':receipt,'untrusted_data':True,'grade_verified':False})
                    ledger.event(run_id,'PROFILE_CONTENT_SAVED','Full history preserved; review required')
            elif job['mode'] in ('reviewed_import','channel_import'):
                if job['mode']=='channel_import':
                    from .channels import validate_import
                    validate_import(job)
                for record in job.get('candidates',[]):
                    guard(); data.import_candidate(ledger.db,record,run_id=run_id)
                    if record.get('assessment'):
                        ledger.record_qualification(run_id,record['identity_key'],record['assessment'])
            else:
                raise StopRun('Unsupported mode')
            # No further request is needed. Finishing the final requested operation
            # exactly at its budget is normal completion, not a rejected next call.
            ledger.check_runtime(ledger.db.execute('SELECT * FROM runs WHERE id=?',(run_id,)).fetchone())
            ledger.check_resources(run_id)
            output=state/'results'
            output.mkdir(mode=0o700,exist_ok=True)
            atomic_json(output/(run_id+'.json'),data.report(ledger.db,run_id))
            ledger.stop(run_id,'Completed; further stages require reviewed input','COMPLETE')
            print(json.dumps({'run_id':run_id,'status':'COMPLETE','budget':ledger.summary()}))
        except BaseException as e:
            ledger.stop(run_id,e if isinstance(e,StopRun) else type(e).__name__)
            raise


def main():
    os.umask(0o077)
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=('init','run','probe','selftest'))
    p.add_argument('--config',default='/etc/recruitme/config.json')
    p.add_argument('--state',default='/var/lib/recruitme')
    p.add_argument('--job',default='/etc/recruitme/first-search.json')
    args=p.parse_args()
    try:
        if args.command=='selftest':
            import unittest
            suite=unittest.defaultTestLoader.discover('/opt/recruitme/tests')
            if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
                return 1
        elif args.command=='init':
            state=Path(args.state)
            config=json.loads(Path(args.config).read_text())
            ledger=Ledger(state/'recruitme.db',config,state_root=state)
            data.initialize(ledger.db)
            print(json.dumps(ledger.summary()))
        else:
            run(args.config,args.state,args.job,args.command=='probe')
    except Exception as e:
        print(json.dumps({'status':'STOPPED','code':stop_code(e),'reason':str(e) if isinstance(e,StopRun) else type(e).__name__}),file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
