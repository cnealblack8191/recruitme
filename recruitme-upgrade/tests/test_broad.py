import unittest
from recruitme.profiles import next_plan
from recruitme.autonomous import new_state
class Broad(unittest.TestCase):
 def state(self):
  s=new_state();s.update(search_as_of='2026-09-09',job_profile={'broad_search':True,'locations':['Atlanta','Doraville'],'followup_names':['Jane Doe']});return s
 def test_followup_starts_third_operation(self):
  s=self.state();s['queries']=[{},{}];p=next_plan(s);self.assertEqual(p['purpose'],'corroboration/contact');self.assertIn('Jane Doe',p['query'])
 def test_diverse_sources_languages(self):
  s=self.state();strategies=set();queries=[]
  for i in range(8):
   s['discovery_index']=i;p=next_plan(s);strategies.add(p['strategy']);queries.append(p['query'])
  self.assertEqual(len(strategies),8);self.assertTrue(any('busco trabajo' in q for q in queries))
 def test_pending_preserved(self):
  s=self.state();s['pending']={'query':'pending'};self.assertEqual(next_plan(s),s['pending'])
