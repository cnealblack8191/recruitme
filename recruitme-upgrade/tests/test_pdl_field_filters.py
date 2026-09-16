import json
import unittest
from recruitme.plugins import PDLFree
from recruitme.budget import StopRun

class PDLFieldFilters(unittest.TestCase):
    def test_documented_exact_filters_keep_record_ceiling(self):
        client=PDLFree.__new__(PDLFree)
        body=client.request_body(json.dumps({'location_region':'Georgia','job_title':'Recruiter'}),1,{})
        self.assertEqual(body,{'query':{'bool':{'must':[{'term':{'location_region':'georgia'}},{'term':{'job_title':'recruiter'}}]}},'size':1,'pretty':False})

    def test_filters_cannot_override_size_or_add_arbitrary_query(self):
        client=PDLFree.__new__(PDLFree)
        for query in ('{"size":100}','{"job_title":null}','{"query":{"match_all":{}}}','{}','{invalid'):
            with self.subTest(query=query),self.assertRaises(StopRun):
                client.request_body(query,1,{})
