"""Interactive root-only credential entry. Does not enable or call any provider."""
import getpass
import grp
import os
import sys
import tempfile
import argparse


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--replace',action='store_true')
    args=parser.parse_args()
    if os.geteuid()!=0 or not sys.stdin.isatty():
        raise SystemExit('Run with sudo in an interactive EC2 terminal.')
    key=getpass.getpass('Tavily API key (hidden): ').strip()
    if not key.startswith('tvly-') or not 8<=len(key)<=512 or any(c.isspace() for c in key):
        raise SystemExit('Invalid key format; nothing saved.')
    os.umask(0o077)
    destination='/etc/recruitme/tavily-api-key'
    if args.replace:
        group=grp.getgrnam('recruitme').gr_gid
        fd,temporary=tempfile.mkstemp(prefix='.tavily-key-',dir='/etc/recruitme')
        try:
            with os.fdopen(fd,'w') as f:
                f.write(key+'\n');f.flush();os.fsync(f.fileno())
                os.fchown(f.fileno(),0,group);os.fchmod(f.fileno(),0o640)
            os.replace(temporary,destination)
        finally:
            if os.path.exists(temporary):os.unlink(temporary)
        print('Credential replaced securely. No API request made; provider settings unchanged.')
        return
    try:
        fd=os.open('/etc/recruitme/tavily-api-key',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    except FileExistsError:
        raise SystemExit('Credential already exists; explicit rotation is required.')
    with os.fdopen(fd,'w') as f:
        f.write(key+'\n');f.flush();os.fsync(f.fileno())
        os.fchown(f.fileno(),0,grp.getgrnam('recruitme').gr_gid)
        os.fchmod(f.fileno(),0o640)
    print('Credential saved securely. Provider remains disabled; no API request made.')


if __name__=='__main__':main()
