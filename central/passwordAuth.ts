import { randomBytes, scrypt, createHash, timingSafeEqual } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import type { Express, Request, Response } from 'express';

const cookieName='__Host-eci-central-session';
const lifetime=12*60*60*1000;
const digest=(value:string)=>createHash('sha256').update(value).digest('hex');
const normalize=(value:unknown)=>typeof value==='string'?value.trim().toLowerCase():'';
const passwordValid=(value:unknown):value is string=>typeof value==='string'&&value.length>=8&&Buffer.byteLength(value)<=1024;
type Account={id:number;email:string;name:string;salt:string;hash:string};
type AuthState={accounts:Account[];sessions:{hash:string;email:string;expires:number}[]};
type Invite={hash:string;email:string;id:number;name:string;expires:number};
function derive(password:string,salt:string):Promise<Buffer>{return new Promise((resolve,reject)=>scrypt(password,salt,64,{N:32768,r:8,p:1,maxmem:64*1024*1024},(err,key)=>err?reject(err):resolve(key)));}
export function createPasswordAuth(directory:string){
 fs.mkdirSync(directory,{recursive:true,mode:0o700});
 const stateFile=path.join(directory,'password-auth.json'),inviteFile=path.join(directory,'password-invite.json');
 function read():AuthState {return fs.existsSync(stateFile)?JSON.parse(fs.readFileSync(stateFile,'utf8')):{accounts:[],sessions:[]};}
 function write(state:AuthState){state.sessions=state.sessions.filter(s=>s.expires>Date.now());fs.writeFileSync(stateFile+'.next',JSON.stringify(state),{mode:0o600});fs.renameSync(stateFile+'.next',stateFile);}
 function sessionToken(req:Request){return (req.headers.cookie||'').split(';').map(s=>s.trim()).find(s=>s.startsWith(cookieName+'='))?.slice(cookieName.length+1)||'';}
 function user(req:Request){const state=read();const session=state.sessions.find(s=>s.hash===digest(sessionToken(req))&&s.expires>Date.now());const account=session&&state.accounts.find(a=>a.email===session.email);return account?{id:account.id,email:account.email,name:account.name,role:'admin' as const,openId:'central:'+account.email,loginMethod:'password',createdAt:new Date(0),updatedAt:new Date(0),lastSignedIn:new Date()}:null;}
 function issue(res:Response,email:string){const state=read(),token=randomBytes(32).toString('base64url');state.sessions=state.sessions.filter(s=>s.email!==email);state.sessions.push({hash:digest(token),email,expires:Date.now()+lifetime});write(state);res.cookie(cookieName,token,{httpOnly:true,secure:true,sameSite:'strict',path:'/',maxAge:lifetime});}
 function logout(req:Request,res:Response){const state=read();state.sessions=state.sessions.filter(s=>s.hash!==digest(sessionToken(req)));write(state);res.clearCookie(cookieName,{httpOnly:true,secure:true,sameSite:'strict',path:'/'});}
 const attempts=new Map<string,{count:number;expires:number}>();let active=0;
 function limited(req:Request){const now=Date.now();attempts.forEach((item,key)=>{if(item.expires<=now)attempts.delete(key);});if(attempts.size>10000)return true;const keys=['ip:'+req.ip,'email:'+normalize(req.body?.email)];const blocked=keys.some(k=>(attempts.get(k)?.count||0)>=10);for(const k of keys){const previous=attempts.get(k);attempts.set(k,{count:(previous?.count||0)+1,expires:previous?.expires||now+15*60*1000});}return blocked||active>=4;}
 function invite(token:unknown):Invite|null{if(typeof token!=='string'||token.length!==43||!fs.existsSync(inviteFile))return null;const value:Invite=JSON.parse(fs.readFileSync(inviteFile,'utf8'));return value.expires>Date.now()&&value.hash===digest(token)?value:null;}
 function install(app:Express){
  app.post('/api/password/:action',async(req,res)=>{
   res.setHeader('Cache-Control','no-store');
   if(!['login','setup'].includes(req.params.action)){res.sendStatus(404);return;}
   if(limited(req)){res.status(429).json({error:'Too many attempts. Please wait 15 minutes and try again.'});return;}
   if(!passwordValid(req.body?.password)){res.status(400).json({error:'Use a password of at least 8 characters (maximum 1,024 bytes).'});return;}
   active++;
   try{
    const email=normalize(req.body.email);
    if(req.params.action==='setup'){
     const allowed=invite(req.body.token);
     if(!allowed||allowed.email!==email||read().accounts.some(a=>a.email===email)){res.status(401).json({error:'This setup link is invalid, expired, or already used.'});return;}
     const salt=randomBytes(32).toString('hex'),hash=(await derive(req.body.password,salt)).toString('hex');
     // Recheck after the async hash: concurrent requests cannot reuse an invite.
     const current=read();if(!invite(req.body.token)||current.accounts.some(a=>a.email===email)){res.status(401).json({error:'This setup link has already been used.'});return;}
     current.accounts.push({id:allowed.id,name:allowed.name,email,salt,hash});write(current);fs.unlinkSync(inviteFile);issue(res,email);res.json({success:true});return;
    }
    const account=read().accounts.find(a=>a.email===email);
    const computed=await derive(req.body.password,account?.salt||'eci-central-dummy-salt');
    if(!account||!timingSafeEqual(computed,Buffer.from(account.hash,'hex'))){res.status(401).json({error:'Email or password is incorrect.'});return;}
    issue(res,email);res.json({success:true});
   }catch{res.status(503).json({error:'Sign-in is temporarily unavailable. Please try again.'});}finally{active--;}
  });
 }
 return {install,user,logout};
}
