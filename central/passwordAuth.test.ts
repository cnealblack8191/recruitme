import {afterEach,expect,it} from 'vitest';
import express from 'express';
import {createServer, type Server} from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {randomBytes,createHash} from 'node:crypto';
import {createPasswordAuth} from './passwordAuth';
const running:{server:Server;dir:string}[]=[];
afterEach(async()=>{for(const {server,dir}of running.splice(0)){await new Promise<void>(r=>server.close(()=>r()));fs.rmSync(dir,{recursive:true,force:true});}});
async function fixture(expired=false){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'central-auth-')),token=randomBytes(32).toString('base64url');
 fs.writeFileSync(path.join(dir,'password-invite.json'),JSON.stringify({hash:createHash('sha256').update(token).digest('hex'),email:'staff@example.test',id:-1001,name:'Staff',expires:Date.now()+(expired?-1000:60000)}));
 const auth=createPasswordAuth(dir),app=express();app.use(express.json());auth.install(app);
 app.get('/me',(req,res)=>res.json(auth.user(req)));app.post('/logout',(req,res)=>{auth.logout(req,res);res.json({success:true});});
 const server=createServer(app);await new Promise<void>(r=>server.listen(0,'127.0.0.1',r));running.push({server,dir});
 const base='http://127.0.0.1:'+(server.address() as {port:number}).port;
 const call=(action:string,input:unknown)=>fetch(base+'/api/password/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)});
 return {dir,base,call,token};
}
it('allows invited setup once, hashes passwords, and revokes and expires sessions',async()=>{
 const f=await fixture(),password=randomBytes(20).toString('hex'),input={email:'STAFF@example.test',password,token:f.token};
 expect((await f.call('setup',{...input,email:'other@example.test'})).status).toBe(401);
 const setup=await f.call('setup',input);expect(setup.status).toBe(200);
 const setCookie=setup.headers.get('set-cookie')!;expect(setCookie).toContain('HttpOnly');expect(setCookie).toContain('Secure');expect(setCookie).toContain('SameSite=Strict');
 const cookie=setCookie.split(';')[0];
 const stored=fs.readFileSync(path.join(f.dir,'password-auth.json'),'utf8');expect(stored).not.toContain(password);expect(stored).not.toContain(cookie.split('=')[1]);
 expect((await f.call('setup',input)).status).toBe(401);
 expect((await fetch(f.base+'/me',{headers:{cookie}}).then(r=>r.json())).email).toBe('staff@example.test');
 await fetch(f.base+'/logout',{method:'POST',headers:{cookie}});expect(await fetch(f.base+'/me',{headers:{cookie}}).then(r=>r.json())).toBeNull();
 expect((await f.call('login',{email:input.email,password:'incorrect-password'})).status).toBe(401);
 const login=await f.call('login',input);expect(login.status).toBe(200);
 const state=JSON.parse(fs.readFileSync(path.join(f.dir,'password-auth.json'),'utf8'));state.sessions[0].expires=Date.now()-1;fs.writeFileSync(path.join(f.dir,'password-auth.json'),JSON.stringify(state));
 expect(await fetch(f.base+'/me',{headers:{cookie:login.headers.get('set-cookie')!.split(';')[0]}}).then(r=>r.json())).toBeNull();
});
it('rejects expired invitations and limits guesses',async()=>{
 const f=await fixture(true);expect((await f.call('setup',{email:'staff@example.test',password:'random-test-password',token:f.token})).status).toBe(401);
 for(let i=0;i<9;i++)await f.call('login',{email:'staff@example.test',password:'random-test-password'});
 expect((await f.call('login',{email:'staff@example.test',password:'random-test-password'})).status).toBe(429);
});
