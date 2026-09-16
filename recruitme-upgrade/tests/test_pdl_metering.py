import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from recruitme.budget import Ledger, StopRun
from recruitme.plugins import PDLFree, disabled_config
from recruitme.routing import ProviderRouter
from test_foundation import configuration


class PDLMetering(unittest.TestCase):
    def test_nine_single_record_reservations_survive_restart_and_unknown_result(self):
        cfg=configuration()
        cfg['session']={'id':'pdl-session','limit_usd':'1','high_value_only_after_usd':'1','ends_at':'2099-01-01T00:00:00+00:00'}
        cfg['providers']['pdl_free']={**disabled_config()['pdl_free'],'enabled':True,'approved':True,
            'account_plan':'free','paid_overages_disabled':True,'max_records_per_request':1,
            'poc_query_limit':9,'run_query_limit':9}
        cfg['provider_priority']={'free_discovery':['pdl_free']}
        bodies=[]
        class Opener:
            def open(self,request,timeout):
                bodies.append(json.loads(request.data))
                class Response:
                    def __enter__(self):return self
                    def __exit__(self,*args):pass
                    def read(self,*args):return b'{"status":200,"data":[]}'
                return Response()
        with tempfile.TemporaryDirectory() as folder, patch('recruitme.plugins.secret',return_value='SYNTHETIC-KEY'):
            path=Path(folder)/'meter.db'
            ledger=Ledger(path,cfg);ledger.create_run('first','1')
            client=PDLFree(ledger,'first',lambda:None,Opener())
            with self.assertRaises(StopRun):client.search('synthetic',10)
            self.assertEqual(bodies,[])
            router=ProviderRouter(ledger,'first',lambda:None,{'pdl_free':PDLFree})
            router.clients['pdl_free']=client
            for i in range(8):router.search('synthetic '+str(i),10)
            op=ledger.reserve('first','pdl_free','search','uncertain-ninth')
            ledger.reconcile(op,None)
            ledger.db.close()
            ledger=Ledger(path,cfg);ledger.create_run('second','1')
            try:
                client=PDLFree(ledger,'second',lambda:None,Opener())
                with self.assertRaises(StopRun):client.search('tenth',1)
                self.assertEqual(len(bodies),8)
                self.assertTrue(all(body['size']==1 for body in bodies))
                self.assertEqual(ledger.db.execute("SELECT COUNT(*) FROM operations WHERE provider='pdl_free'").fetchone()[0],9)
            finally:ledger.db.close()

if __name__=='__main__':unittest.main()
