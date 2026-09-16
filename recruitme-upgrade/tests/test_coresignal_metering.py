import json,tempfile,unittest,types
from pathlib import Path
from unittest.mock import patch
from recruitme.budget import Ledger,StopRun
from recruitme.plugins import Coresignal
from recruitme.routing import ProviderRouter
from test_foundation import configuration

def provider():
    return dict(enabled=True,approved=True,account_plan='free_trial',credits_per_request=10,
        trial_ends_at='2026-09-19T00:00:00+00:00',price_version='coresignal-2026-09-14',
        operations={'search':'0'},poc_limit_usd='0',run_limit_usd='0',
        poc_query_limit=20,run_query_limit=20,max_attempts=1)

class CoresignalMetering(unittest.TestCase):
    def test_shared_limit_survives_restart_and_unknown_request(self):
        cfg=configuration();cfg['providers']['coresignal']=provider()
        cfg['session']={'id':'core-session','limit_usd':'1','high_value_only_after_usd':'1','ends_at':'2099-01-01T00:00:00+00:00'}
        requests=[]
        class Opener:
            def open(self,request,timeout):
                requests.append(request)
                class Response:
                    def __enter__(self):return self
                    def __exit__(self,*args):pass
                    def read(self,*args):return b'{"id":1,"full_name":"Synthetic","profile_url":"https://www.linkedin.com/in/synthetic"}'
                return Response()
        with tempfile.TemporaryDirectory() as folder,patch('recruitme.plugins.secret',return_value='SYNTHETIC-KEY'):
            path=Path(folder)/'meter.db';ledger=Ledger(path,cfg);ledger.create_run('first','1')
            client=Coresignal(ledger,'first',lambda:None,Opener())
            for i in range(19):
                query=json.dumps({'headline':'synthetic '+str(i)}) if i%2 else 'https://www.linkedin.com/in/synthetic-'+str(i)
                client.search(query,1)
            op=ledger.reserve('first','coresignal','search','uncertain-twentieth');ledger.reconcile(op,None)
            ledger.db.close();ledger=Ledger(path,cfg);ledger.create_run('second','1')
            try:
                with self.assertRaises(StopRun):Coresignal(ledger,'second',lambda:None,Opener()).search('{"headline":"twenty-first"}',1)
                self.assertEqual(len(requests),19)
                self.assertEqual(ledger.db.execute("SELECT COUNT(*) FROM operations WHERE provider='coresignal'").fetchone()[0]*10,200)
                self.assertEqual({r.get_method() for r in requests},{'GET','POST'})
            finally:ledger.db.close()
    def test_shape_and_expiry_guards(self):
        cfg={'providers':{'coresignal':provider()}}
        c=Coresignal(types.SimpleNamespace(config=cfg),None,None)
        for query in ['https://evil.example/in/name','https://www.linkedin.com/in/a?x=1','{"unknown":"value"}','plain text']:
            with self.assertRaises(StopRun):c.request_body(query,1,{})
        cfg['providers']['coresignal']['trial_ends_at']='2099-01-01T00:00:00+00:00'
        with self.assertRaises(StopRun):c.pricing(1)
        c.requested_count=1
        result=c.response_envelope([{'id':1,'full_name':'Synthetic','email':'private','experience':[{'title':'Electrician'}]}]*2)
        self.assertEqual(len(result['results']),1)
        self.assertIn('Electrician',result['results'][0]['text'])
        self.assertNotIn('private',json.dumps(result))
    def test_discovery_requires_explicit_provider(self):
        cfg=configuration();cfg['providers']['coresignal']={**provider(),'explicit_discovery_only':True}
        cfg['provider_priority']={'free_discovery':['coresignal']}
        cfg['session']={'id':'route-session','limit_usd':'1','high_value_only_after_usd':'1','ends_at':'2099-01-01T00:00:00+00:00'}
        with tempfile.TemporaryDirectory() as folder,patch('recruitme.plugins.secret',return_value='SYNTHETIC-KEY'):
            ledger=Ledger(Path(folder)/'meter.db',cfg);ledger.create_run('implicit','1');ledger.create_run('explicit','1')
            try:
                with self.assertRaises(StopRun):ProviderRouter(ledger,'implicit',lambda:None,{'coresignal':Coresignal}).search('generic query')
                router=ProviderRouter(ledger,'explicit',lambda:None,{'coresignal':Coresignal})
                with patch.object(Coresignal,'search',return_value={'synthetic':True}) as search:
                    self.assertEqual(router.search('{"headline":"recruiter"}',1,provider='coresignal'),{'synthetic':True})
                    search.assert_called_once()
            finally:ledger.db.close()

if __name__=='__main__':unittest.main()
