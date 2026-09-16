import express from 'express';
import { createServer } from 'node:http';
import path from 'node:path';
import { createExpressMiddleware } from '@trpc/server/adapters/express';
import { router } from '../server/_core/trpc';
import { recruitmeRouter } from '../server/recruitme';
import type { TrpcContext } from '../server/_core/context';
import { createPasswordAuth } from './passwordAuth';

const app = express();
app.disable('x-powered-by');
app.set('trust proxy','loopback');
const passwordAuth=createPasswordAuth(path.join(process.env.RECRUITME_WEB_STATE_DIR||'.recruitme-web','auth'));
const portal = 'http://127.0.0.1:3000';
const allowedAuth = new Set(['auth.me','auth.logout','staffAuth.requestCode','staffAuth.verifyCode']);
app.use((req,res,next) => {
  res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Referrer-Policy','same-origin');
  res.setHeader('X-Frame-Options','DENY');
  if (req.path.startsWith('/api/')) res.setHeader('Cache-Control','no-store');
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    const expected = process.env.CENTRAL_ORIGIN || 'https://central.ecinc.us';
    if (req.headers.origin !== expected) { res.status(403).json({error:'Unrecognized request origin'}); return; }
  }
  next();
});
app.use(express.json({limit:'64kb'}));
passwordAuth.install(app);
// Reuse the existing staff identity service; no production secret or database copy.
app.all('/api/trpc/:procedure', async (req,res,next) => {
  if (!allowedAuth.has(req.params.procedure)) return next();
  if ((req.params.procedure==='auth.me' && req.method!=='GET') || (req.params.procedure!=='auth.me' && req.method!=='POST')) {res.sendStatus(405);return;}
  if(req.params.procedure==='auth.me') {const local=passwordAuth.user(req);if(local){res.json({result:{data:{json:local}}});return;}}
  if(req.params.procedure==='auth.logout')passwordAuth.logout(req,res);
  try {
    const upstream=await fetch(portal+req.originalUrl,{method:req.method,redirect:'error',signal:AbortSignal.timeout(8000),headers:{'Content-Type':'application/json',cookie:req.headers.cookie||'', 'x-forwarded-proto':'https'},...(req.method==='POST'?{body:JSON.stringify(req.body)}:{})});
    for (const cookie of upstream.headers.getSetCookie()) res.append('Set-Cookie',cookie);
    res.status(upstream.status).type('application/json').send(await upstream.text());
  } catch {res.status(503).json({error:'Staff sign-in is temporarily unavailable. Please retry.'});}
});
app.use('/api/trpc', createExpressMiddleware({router:router({recruitme:recruitmeRouter}),createContext:async({req,res}) => {
  let user=passwordAuth.user(req);
  try {
   if(!user){
    const response=await fetch(portal+'/api/trpc/auth.me',{headers:{cookie:req.headers.cookie||''},signal:AbortSignal.timeout(4000),redirect:'error'});
    const body=await response.json();
    const candidate=body?.result?.data?.json;
    if (response.ok && candidate && candidate.role==='admin' && Number.isInteger(candidate.id)) user=candidate;
   }
  } catch { /* Authentication failure is closed by adminProcedure. */ }
  return {req,res,user} as TrpcContext;
}}));
app.get('/healthz',(_req,res)=>res.json({service:'eci-central',status:'ok'}));
app.use('/api',(_req,res)=>res.status(404).json({error:'Unknown API route'}));
const dist=path.resolve(process.env.CENTRAL_PUBLIC_DIR || 'central-dist/public');
app.use(express.static(dist,{index:false}));
app.get('*',(_req,res)=>{res.setHeader('Cache-Control','no-store');res.sendFile(path.join(dist,'index.html'));});
createServer(app).listen(Number(process.env.PORT || 3100),'127.0.0.1',()=>console.log('ECI Central listening on loopback'));
