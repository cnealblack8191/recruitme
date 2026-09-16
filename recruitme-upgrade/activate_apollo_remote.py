"""Install Apollo from its encrypted parameter; never include the key in output."""
import fcntl,json,os,pathlib,pwd,subprocess
from recruitme.plugins import disabled_config
root=pathlib.Path('/etc/recruitme')
with pathlib.Path('/var/lib/recruitme/launch.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if subprocess.getoutput('systemctl is-active recruitme.service').strip() in ('active','activating','deactivating'):
        raise SystemExit('Finish or stop the active search before connecting Apollo.')
    result=subprocess.run(['aws','ssm','get-parameter','--region','us-east-2','--name','/recruitme/providers/apollo/api-key','--with-decryption','--output','json'],capture_output=True,text=True)
    if result.returncode:raise SystemExit('Encrypted Apollo credential could not be read.')
    key=json.loads(result.stdout)['Parameter']['Value'].strip()
    if not 8<=len(key)<=512 or any(c.isspace() for c in key):raise SystemExit('Invalid Apollo key format.')
    owner=pwd.getpwnam('recruitme')
    temp=root/'apollo-api-key.new'
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as file:
        file.write(key+'\n');file.flush();os.fsync(file.fileno());os.fchown(file.fileno(),0,owner.pw_gid);os.fchmod(file.fileno(),0o640)
    temp.replace(root/'apollo-api-key')
    cfg=json.loads((root/'config.json').read_text())
    p=cfg['providers'].get('apollo',disabled_config()['apollo'])
    p.update(enabled=True,approved=True)
    cfg['providers']['apollo']=p
    temp=root/'config.apollo.new'
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as file:
        json.dump(cfg,file);file.flush();os.fsync(file.fileno());os.fchown(file.fileno(),0,owner.pw_gid);os.fchmod(file.fileno(),0o640)
    temp.replace(root/'config.json')
    print(json.dumps({'connected':True,'provider':'apollo'}))
