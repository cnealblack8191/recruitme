"""Install an allowlisted encrypted credential without enabling API calls."""
import fcntl,json,os,pathlib,pwd,subprocess,sys,tempfile

def main():
    provider=sys.argv[1] if len(sys.argv)==2 else ''
    if provider not in ('brave','serpapi','pdl','brightdata','coresignal'):
        raise SystemExit('Unsupported provider')
    root=pathlib.Path('/etc/recruitme')
    with pathlib.Path('/var/lib/recruitme/launch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if subprocess.getoutput('systemctl is-active recruitme.service').strip() in ('active','activating','deactivating'):
            raise SystemExit('An active search must finish before credentials change.')
        result=subprocess.run(['aws','ssm','get-parameter','--region','us-east-2','--name',
            '/recruitme/providers/'+provider+'/api-key','--with-decryption','--output','json'],capture_output=True,text=True)
        if result.returncode:raise SystemExit('Encrypted credential could not be read.')
        key=json.loads(result.stdout)['Parameter']['Value'].strip()
        if not 8<=len(key)<=512 or any(c.isspace() for c in key):raise SystemExit('Invalid credential format.')
        owner=pwd.getpwnam('recruitme')
        fd,name=tempfile.mkstemp(prefix=provider+'-',dir=root)
        try:
            with os.fdopen(fd,'w') as file:
                file.write(key+'\n');file.flush();os.fsync(file.fileno())
                os.fchown(file.fileno(),0,owner.pw_gid);os.fchmod(file.fileno(),0o640)
            os.replace(name,root/(provider+'-api-key'))
        finally:
            if os.path.exists(name):os.unlink(name)
        print(json.dumps({'connected':True,'provider':provider,'credentialInstalled':True,
                          'apiVerified':False,'searchStarted':False}))

if __name__=='__main__':main()
