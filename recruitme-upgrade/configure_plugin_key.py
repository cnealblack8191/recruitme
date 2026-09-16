"""Install one new provider credential through a hidden interactive prompt only."""
import argparse,getpass,grp,os,sys
def main():
    p=argparse.ArgumentParser();p.add_argument('provider',choices=('brave','serpapi','pdl','brightdata','apollo'));args=p.parse_args()
    if os.geteuid()!=0 or not sys.stdin.isatty():raise SystemExit('Use sudo in an interactive worker terminal.')
    key=getpass.getpass(args.provider+' API key (hidden): ').strip()
    if not 8<=len(key)<=512 or any(c.isspace() for c in key):raise SystemExit('Invalid key format; nothing saved.')
    destination='/etc/recruitme/'+args.provider+'-api-key'
    try:fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    except FileExistsError:raise SystemExit('Existing credential preserved. Use a separate explicit rotation procedure.')
    with os.fdopen(fd,'w') as f:
        f.write(key+'\n');f.flush();os.fsync(f.fileno());os.fchown(f.fileno(),0,grp.getgrnam('recruitme').gr_gid);os.fchmod(f.fileno(),0o640)
    print('Credential installed. Provider configuration unchanged; no request made.')
if __name__=='__main__':main()
