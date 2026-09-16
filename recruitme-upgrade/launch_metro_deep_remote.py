"""Launch the saved UI profile without changing provider/account configuration."""
import fcntl
import json
import os
import pathlib
import pwd
import re
import shutil
import subprocess
import sys
import uuid
from recruitme.search_policy import apply_search_policy

root = pathlib.Path('/etc/recruitme')
payload = json.load(sys.stdin)
profile = payload['profile']
if payload.get('action') != 'launch' or profile.get('id') != payload.get('profileId'):
    raise SystemExit('Invalid launch request')
with pathlib.Path('/var/lib/recruitme/launch.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state = subprocess.check_output(['systemctl','show','recruitme','-p','ActiveState','--value'],text=True).strip()
    if state in ('active','activating','deactivating'):
        raise SystemExit('A search is already running')
    if subprocess.check_output(['systemctl','show','recruitme-selftest','-p','ExecMainStatus','--value'],text=True).strip() != '0':
        raise SystemExit('Worker selftests failed')
    cfg = json.loads((root/'config.json').read_text())
    apply_search_policy(cfg, profile)
    run = 'web-' + uuid.uuid4().hex
    split = lambda name: [s.strip() for s in re.split('[,;]',profile.get(name,'')) if s.strip()]
    if not split('roles') or not split('locations') or not split('fitTerms'):
        raise SystemExit('Roles, locations and fit terms are required')
    job_profile = {
        'version':1, 'id':profile['id'], 'title':profile['title'],
        'locations':split('locations'), 'fit_terms':split('fitTerms'),
        'tracks':[{'id':'experienced','roles':split('roles'),'minimum_years':profile['minimumYears']}],
        'compensation':{'currency':'USD','unit':'year' if profile.get('maximumAnnualPay') else 'hour',
                        'maximum':profile.get('maximumAnnualPay') or profile.get('maximumHourlyPay'), 'minimum':None},
        'start':profile.get('startDate',''), 'travel_pay':profile.get('travelPay',False),
        'relocation':profile.get('relocation',''), 'employer_name':None, 'jobsite':None,
        'schedule':None, 'employment_arrangement':None, 'search_center':profile['locations'],
    }
    job = {'run_id':run,'budget_usd':str(profile['runCap']),'mode':'autonomous',
           'search_version':'intent-v2','job_profile':job_profile,'web_profile':profile}
    from recruitme.profiles import validate
    validate(job_profile)
    if shutil.disk_usage('/var/lib/recruitme').free < 2147483648:
        raise SystemExit('Insufficient worker disk space')
    target = root/'first-search.json'
    if target.exists():
        backup = root/'launch-backups'
        backup.mkdir(mode=0o700,exist_ok=True)
        shutil.copy2(target,backup/(run+'.json'))
    temp = root/(run+'.tmp')
    temp.write_text(json.dumps(job))
    os.chown(temp,0,pwd.getpwnam('recruitme').pw_gid)
    temp.chmod(0o640)
    temp.replace(target)
    subprocess.run(['systemctl','start','recruitme.service'],check=True,timeout=15)
    print(json.dumps({'accepted':True,'runId':run,'status':'QUEUED','profileId':profile['id'],
                      'message':'Saved search budget and provider allocations submitted to worker.'}))
