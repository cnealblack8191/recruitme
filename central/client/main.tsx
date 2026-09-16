import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { httpLink } from '@trpc/client';
import superjson from 'superjson';
import { ArrowUpRight, ArrowRight, Clock3, Users, ShieldCheck, Warehouse, Search, LogOut, LockKeyhole, ChevronLeft, Wrench } from 'lucide-react';
import { trpc } from '@/lib/trpc';
import RecruitMe from '@/pages/RecruitMe';
import { Toaster } from '@/components/ui/sonner';
import '@/index.css';
import './central.css';
import eciLogo from './eci-logo.png';

const queryClient=new QueryClient({defaultOptions:{queries:{retry:false,refetchOnWindowFocus:false}}});
const client=trpc.createClient({links:[httpLink({url:'/api/trpc',transformer:superjson})]});
const applications=[
 {name:'RecruitMe',label:'RECRUITING',description:'Find the right people. Review their experience, evidence, and fit in one place.',icon:Search,tone:'green',ready:true},
 {name:'Timex',label:'TIME & ATTENDANCE',description:'A clearer view of time. Keep your workday and timekeeping together.',icon:Clock3,tone:'blue',ready:false},
 {name:'DevPool',label:'YOUR PORTAL',description:'Your connection to development, shared projects, and the tools you need.',icon:Users,tone:'purple',ready:false},
 {name:'Safety Admin',label:'SAFETY & TRAINING',description:'Help your teams stay prepared, trained, and ready for the field.',icon:ShieldCheck,tone:'orange',ready:false},
 {name:'Warehouse',label:'TOOLS & MATERIALS',description:'Keep equipment and materials organized, from the warehouse to the job.',icon:Warehouse,tone:'slate',ready:false},
 {name:'Service 1',label:'SERVICE',description:'Your starting point for the new Service 1 app.',icon:Wrench,tone:'blue',ready:false},
];
async function staffCall(procedure:string,input:unknown) {
 const res=await fetch('/api/trpc/staffAuth.'+procedure,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({json:input})});
 const body=await res.json();
 if(!res.ok || body.error) throw new Error(body.error?.json?.message || body.error?.message || 'Sign-in is temporarily unavailable. Please try again.');
 return body.result.data.json;
}
function Central() {
 const [setupToken]=useState(()=>new URLSearchParams(window.location.hash.slice(1)).get('setup')||'');
 const [password,setPassword]=useState('');const [confirmation,setConfirmation]=useState('');
 const [useCode,setUseCode]=useState(false);
 useEffect(()=>{if(setupToken)history.replaceState(null,'',window.location.pathname+window.location.search);},[setupToken]);
 const me=trpc.auth.me.useQuery();
 const utils=trpc.useUtils();
 const logout=trpc.auth.logout.useMutation({onSuccess:()=>{queryClient.clear();window.location.assign('/');}});
 const [email,setEmail]=useState('');const [code,setCode]=useState('');const [challenge,setChallenge]=useState<string|null>(null);
 const [busy,setBusy]=useState(false);const [message,setMessage]=useState('');const [filter,setFilter]=useState('');
 const route=window.location.pathname;
 const returnTo=route==='/recruitme'||new URLSearchParams(window.location.search).get('next')==='/recruitme'?'/recruitme':'/';
 const signedIn=me.data?.role==='admin';
 async function submit(e:React.FormEvent) {e.preventDefault();setBusy(true);setMessage('');try {
   if(!useCode){
    if(setupToken&&password!==confirmation)throw new Error('The passwords do not match.');
    const response=await fetch('/api/password/'+(setupToken?'setup':'login'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password,...(setupToken?{token:setupToken}:{})})});
    const result=await response.json();if(!response.ok)throw new Error(result.error||'Sign-in failed.');
    setPassword('');setConfirmation('');window.location.assign(returnTo);
   }else if(!challenge){const r=await staffCall('requestCode',{email});setChallenge(r.challengeId);setMessage(r.message);}
   else {await staffCall('verifyCode',{email,code,challengeId:challenge});await utils.auth.me.invalidate();window.location.assign(returnTo);}
 }catch(e){setMessage(e instanceof Error?e.message:'Please retry.');}finally{setBusy(false);}}
 function openRecruitMe(){window.location.assign(signedIn?'/recruitme':'/login?next=/recruitme');}
 if(route==='/recruitme' && signedIn) return <><a className="central-back" href="/"><ChevronLeft size={16}/>ECI Central</a><RecruitMe/><Toaster/></>;
 if(route==='/login' || (route==='/recruitme' && !signedIn)) return <div className="central-shell"><main className="central-login-page"><section className="central-login" aria-labelledby="login-title"><a className="central-login-home" href="/"><ChevronLeft size={16}/>Back to Central</a><img className="central-login-logo" src={eciLogo} alt="Electrical Contractor Incorporated"/><h2 id="login-title">{setupToken?'Create your password':'Welcome to ECI Central'}</h2><p>{setupToken?'Set your password to access ECI Central.':useCode?'Use your authorized staff email to request a one-time code.':'Sign in with your work email and password.'}</p><form onSubmit={submit}><label>Work email<input autoFocus type="email" autoComplete="email" required value={email} disabled={!!challenge} onChange={e=>setEmail(e.target.value)}/></label>{!useCode&&<label>Password<input type="password" autoComplete={setupToken?'new-password':'current-password'} minLength={8} maxLength={1024} required value={password} onChange={e=>setPassword(e.target.value)}/></label>}{setupToken&&<label>Confirm password<input type="password" autoComplete="new-password" required value={confirmation} onChange={e=>setConfirmation(e.target.value)}/></label>}{useCode&&challenge&&<label>Six-digit code<input inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} required value={code} onChange={e=>setCode(e.target.value)}/></label>}<button className="central-submit" disabled={busy}>{busy?'Please wait…':setupToken?'Create password and sign in':!useCode||challenge?'Sign in':'Email my sign-in code'}<ArrowRight size={17}/></button>{message&&<p role="status" className="central-login-message">{message}</p>}{challenge&&<button className="central-reset" type="button" onClick={()=>{setChallenge(null);setCode('');setMessage('');}}>Use a different email or request a new code</button>}</form>{!setupToken&&<button type="button" className="central-reset" onClick={()=>{setUseCode(!useCode);setChallenge(null);setMessage('');setPassword('');setCode('');}}>{useCode?'Use a password instead':'Use an email code instead'}</button>}<small>Existing ECI staff permissions apply. Additional application permissions are managed separately.</small></section></main></div>;
 return <div className="central-shell">
  <header className="central-header"><a href="/" className="central-brand"><img className="central-logo" src={eciLogo} alt="Electrical Contractor Incorporated"/><span className="central-brand-word">Central<small>ELECTRICAL CONTRACTOR INCORPORATED</small></span></a><div className="central-header-actions"><span className="central-internal"><LockKeyhole size={13}/> Employee workspace</span>{signedIn?<button className="central-sign" onClick={()=>logout.mutate()} disabled={logout.isPending}><LogOut size={16}/>Sign out</button>:<a className="central-sign" href="/login">Staff sign in <ArrowRight size={16}/></a>}</div></header>
  <main className="central-main">
  <section id="applications" className="central-applications"><div className="central-section-heading"><div><span className="central-kicker dark">YOUR WORKSPACE</span><h2>{signedIn?'Welcome back. Let’s get to work.':'Everything starts here.'}</h2><p>{signedIn?'Choose an application to continue.':'Sign in to access your ECI applications.'}</p></div><label className="central-search"><Search size={17}/><input aria-label="Find an application" placeholder="Find an application…" value={filter} onChange={e=>setFilter(e.target.value)}/></label></div><div className="central-cards">{applications.filter(a=>(a.name+' '+a.label).toLowerCase().includes(filter.toLowerCase())).map(a=>{const Icon=a.icon;return <article className={'central-card '+a.tone} key={a.name}><div className="central-card-top"><span className="central-app-icon"><Icon size={25}/></span><span className={'central-status '+(a.ready?'available':'')}>{a.ready?'Staff access':'Coming soon'}</span></div><span className="central-card-category">{a.label}</span><h3>{a.name}</h3><p>{a.description}</p><button disabled={!a.ready} onClick={openRecruitMe}>{a.ready?(signedIn?'Open RecruitMe':'Sign in to open'):'Link coming soon'}<ArrowUpRight size={18}/></button></article>})}</div>{!applications.some(a=>(a.name+' '+a.label).toLowerCase().includes(filter.toLowerCase()))&&<p className="central-no-results">No applications match that name. Try another search.</p>}</section>
  <aside className="central-support"><ShieldCheck size={24}/><div><strong>Your ECI workspace, in one place.</strong><p>Access is managed by ECI. Application links will appear here as each service becomes available.</p></div><span>CONNECTED WITH PURPOSE</span></aside></main><footer className="central-footer"><span>© {new Date().getFullYear()} Electrical Contractor Incorporated</span><span>ECI Central · Staff workspace</span></footer>

 </div>;
}
createRoot(document.getElementById('root')!).render(<trpc.Provider client={client} queryClient={queryClient}><QueryClientProvider client={queryClient}><Central/></QueryClientProvider></trpc.Provider>);
