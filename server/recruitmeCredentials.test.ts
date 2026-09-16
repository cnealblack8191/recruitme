import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import type { TrpcContext } from './_core/context';
const { spawn } = vi.hoisted(() => ({ spawn: vi.fn() }));
vi.mock('node:child_process', () => ({ spawnSync: spawn }));
import { recruitmeRouter } from './recruitme';
let dir: string;
beforeEach(() => {
  dir=fs.mkdtempSync(path.join(os.tmpdir(),'recruitme-key-'));
  vi.stubEnv('RECRUITME_WEB_STATE_DIR',dir);
  vi.stubEnv('RECRUITME_BRIDGE_ENABLED','true');
  vi.stubEnv('RECRUITME_BRIDGE_CONNECT_CMD',JSON.stringify(['bridge','activate_apollo']));
  spawn.mockReset();
});
afterEach(() => { fs.rmSync(dir,{recursive:true,force:true}); vi.unstubAllEnvs(); });
const caller=(admin=true) => recruitmeRouter.createCaller({ user:admin ? { id:1,role:'admin' } : null,req:{},res:{} } as TrpcContext);
it('stores an encrypted key without including it in command arguments or worker payloads',async () => {
  const key='synthetic-apollo-key';
  spawn.mockImplementation((command,args,options) => {
    expect(JSON.stringify(args)).not.toContain(key);
    if(command==='aws') {
      const filename=args[args.indexOf('--cli-input-json')+1].slice(7);
      expect(JSON.parse(fs.readFileSync(filename,'utf8'))).toMatchObject({Value:key,Type:'SecureString',Name:'/recruitme/providers/apollo/api-key'});
      return {status:0,stdout:'{}'};
    }
    expect(options.input).not.toContain(key);
    expect(fs.readdirSync(dir)).toEqual([]);
    return {status:0,stdout:JSON.stringify({connected:true,provider:'apollo'})};
  });
  expect(await caller().connectApollo({apiKey:key})).toEqual({connected:true,provider:'apollo'});
  expect(fs.readdirSync(dir)).toEqual([]);
});
it('removes temporary credentials on failure and hides provider diagnostics',async () => {
  spawn.mockReturnValue({status:1,stderr:'synthetic-apollo-key'});
  await expect(caller().connectApollo({apiKey:'synthetic-apollo-key'})).rejects.toThrow('Could not store the encrypted Apollo credential');
  expect(fs.readdirSync(dir)).toEqual([]);
});
it('rejects anonymous credential changes before invoking the cloud',async () => {
  await expect(caller(false).connectApollo({apiKey:'synthetic-apollo-key'})).rejects.toMatchObject({code:'FORBIDDEN'});
  expect(spawn).not.toHaveBeenCalled();
});
