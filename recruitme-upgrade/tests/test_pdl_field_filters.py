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

    def test_taxonomy_keys_support_career_transition_query(self):
        client=PDLFree.__new__(PDLFree)
        body=client.request_body(json.dumps({'job_title_sub_role':'recruiting','experience.title.name':'Electrician','location_region':'Georgia'}),3,{})
        self.assertEqual(body['size'],3)
        self.assertIn({'term':{'experience.title.name':'electrician'}},body['query']['bool']['must'])
        self.assertIn({'term':{'job_title_sub_role':'recruiting'}},body['query']['bool']['must'])
        with self.assertRaises(StopRun):
            client.request_body(json.dumps({'experience.company.name':'x'}),1,{})


class ApolloFieldFilters(unittest.TestCase):
    def test_structured_titles_and_locations(self):
        from recruitme.plugins import ApolloPeople
        client=ApolloPeople.__new__(ApolloPeople)
        body=client.request_body(json.dumps({'person_titles':['Recruiter'],'person_locations':['Georgia'],'q_keywords':'electrician'}),5,{})
        self.assertEqual(body,{'person_titles':['Recruiter'],'person_locations':['Georgia'],'q_keywords':'electrician','page':1,'per_page':5})
        self.assertEqual(client.request_body('electrician recruiter',5,{})['q_keywords'],'electrician recruiter')
        for bad in ('{"per_page":500}','{"person_titles":"Recruiter"}','{"person_titles":[]}','{}'):
            with self.subTest(bad=bad),self.assertRaises(StopRun):
                client.request_body(bad,5,{})
