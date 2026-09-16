import datetime,json,tempfile,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
from test_foundation import configuration
from recruitme.budget import Ledger,StopRun,money
from recruitme.exa_keyed import ExaKeyed,PRICE_VERSION
from recruitme.tavily import Tavily,PRICE_VERSION as TV
from recruitme.routing import ProviderRouter
from recruitme.search_options import validate_options,logical_search
from recruitme.channels import prepare,validate_import
from recruitme.autonomous import new_state,next_query,screen,consume

class Options(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.c=configuration()
  self.c['session']={'id':'test','limit_usd':'25','high_value_only_after_usd':'20','ends_at':'2099-01-01T00:00:00+00:00'}
  for name,version,price in [('exa_keyed',PRICE_VERSION,'0.007'),('tavily',TV,'0.008')]:
   self.c['providers'][name]={'approved':True,'enabled':True,'price_version':version,'operations':{'search':price},'run_limit_usd':'5','poc_limit_usd':'25','run_query_limit':100,'poc_query_limit':500,'max_attempts':1}
  self.l=Ledger(Path(self.tmp.name)/'db',self.c);self.l.create_run('test','5');self.sent=[]
  self.patch=patch('recruitme.tavily.load_key',return_value='tvly-SYNTHETIC-ONLY');self.patch.start()
  self.exa=patch('recruitme.exa_keyed.load_key',return_value='EXA-SYNTHETIC-ONLY');self.exa.start()
 def tearDown(self):self.patch.stop();self.exa.stop();self.l.db.close();self.tmp.cleanup()
 def client(self,cls=Tavily,result=None,error=None):
  test=self
  class R:
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self,*a):return json.dumps(result or {'results':[],'usage':{'credits':1}}).encode()
  class O:
   def open(self,req,timeout):
    row=test.l.db.execute('SELECT * FROM operations ORDER BY rowid DESC').fetchone()
    test.assertEqual(row['state'],'RESERVED');test.assertEqual(row['reserved'],8000 if cls==Tavily else 7000)
    test.sent.append(json.loads(req.data))
    if error:raise error
    return R()
  return cls(self.l,'test',lambda:self.l.check('test'),O())
 def test_tavily_fixed_shape_reserved_then_reconciled(self):
  self.client().search('synthetic',10,{'start_date':'2026-06-10','include_domains':['example.org']})
  b=self.sent[0];self.assertEqual(b['search_depth'],'basic');self.assertFalse(b['auto_parameters']);self.assertFalse(b['include_answer']);self.assertFalse(b['include_raw_content']);self.assertEqual(b['start_date'],'2026-06-10');self.assertEqual(self.l.total(),8000)
 def test_exa_supported_filters_ten_results(self):
  self.client(ExaKeyed).search('synthetic',10,{'start_date':'2026-06-10','end_date':'2026-09-08','include_domains':['example.org/resume']})
  b=self.sent[0];self.assertEqual(b['numResults'],10);self.assertEqual(b['startPublishedDate'],'2026-06-10T00:00:00.000Z');self.assertEqual(b['includeDomains'],['example.org/resume']);self.assertNotIn('category',b)
 def test_no_unpriced_settings(self):
  for o in ({'search_depth':'advanced'},{'summary':True},{'category':'people'},{'start_date':'yesterday'},{'include_domains':['https://example.org']},{'start_date':'2026-09-01','end_date':'2026-08-01'}):
   with self.assertRaises(StopRun):self.client().search('synthetic',10,o)
  self.assertFalse(self.sent)
 def test_filter_aware_cache_survives_client_recreation(self):
  self.client().search('synthetic',10,{'start_date':'2026-06-10'})
  deadline=dict(self.l.runtime_for('test'))
  self.client().initialize();self.client().search('synthetic',10,{'start_date':'2026-06-10'})
  self.assertEqual(len(self.sent),1)
  self.client().search('synthetic',10,{'start_date':'2026-07-10'})
  self.assertEqual(len(self.sent),2);self.assertEqual(self.l.total(),16000);self.assertEqual(dict(self.l.runtime_for('test')),deadline)
 def test_normalized_cache_identity(self):
  self.assertEqual(logical_search('q',10,{'include_domains':['b.org','a.org']}),logical_search('q',10,{'include_domains':['a.org','b.org']}))
 def test_timeout_keeps_reservation(self):
  with self.assertRaises(StopRun):self.client(error=TimeoutError()).search('synthetic')
  self.assertEqual(self.l.total(),8000);self.assertEqual(len(self.sent),1)
 def test_http_432_quota_never_retried(self):
  c=self.client(error=urllib.error.HTTPError('https://api.tavily.com/search',432,'synthetic',{},None))
  for q in ('one','two'):
   with self.assertRaises(StopRun):c.search(q)
  self.assertEqual(len(self.sent),1);self.assertTrue(self.l.provider_limited('tavily'))
  row=self.l.db.execute('SELECT * FROM provider_health').fetchone();self.assertIsNotNone(row['first_operation_id']);self.assertGreater(row['first_observed_at'],0)
 def test_body_quota_notice_not_results(self):
  with self.assertRaises(StopRun):self.client(result={'detail':{'error':'This request exceeds your plan limit'}}).search('synthetic')
  self.assertTrue(self.l.provider_limited('tavily'));self.assertEqual(self.l.db.execute("SELECT COUNT(*) FROM operation_outcomes WHERE status='SUCCESS'").fetchone()[0],0)
 def test_overcharge_freezes(self):
  with self.assertRaises(StopRun):self.client(result={'results':[],'usage':{'credits':2}}).search('synthetic')
  self.assertEqual(self.l.total(),16000);self.assertEqual(self.l.db.execute("SELECT COUNT(*) FROM audit WHERE event='PRICE_BREACH'").fetchone()[0],1)
 def test_missing_key_no_operation(self):
  with patch('recruitme.tavily.load_key',side_effect=StopRun('Unavailable')):
   with self.assertRaises(StopRun):self.client().search('synthetic')
  self.assertEqual(self.l.total(),0);self.assertFalse(self.sent)
 def test_key_reflection_redacted(self):
  self.client(result={'results':[{'url':'https://example.org','content':'tvly-SYNTHETIC-ONLY'}]}).search('synthetic')
  self.assertNotIn('tvly-SYNTHETIC-ONLY','\n'.join(self.l.db.iterdump()))
 def test_excluded_response_not_checkpointed(self):
  self.client(result={'results':[{'url':'https://www.linkedin.com/in/fixture','content':'DO-NOT-RETAIN-FIXTURE'}]}).search('synthetic',10,{'exclude_domains':['linkedin.com']})
  self.assertNotIn('DO-NOT-RETAIN-FIXTURE','\n'.join(self.l.db.iterdump()))
 def test_switch_preserves_all_governors(self):
  self.c['provider_priority']={'free_discovery':['tavily'],'low_cost_paid_discovery':['exa_keyed']}
  self.client(error=urllib.error.HTTPError('https://api.tavily.com/search',433,'synthetic',{},None))
  c=self.client(error=urllib.error.HTTPError('https://api.tavily.com/search',433,'synthetic',{},None))
  with self.assertRaises(StopRun):c.search('first')
  before=dict(self.l.runtime_for('test'))
  router=ProviderRouter(self.l,'test',lambda:self.l.check('test'),{'tavily':Tavily,'exa_keyed':lambda l,r,g:self.client(ExaKeyed)})
  router.search('second');self.assertEqual(self.l.total(),15000);self.assertEqual(dict(self.l.runtime_for('test')),before)
 def fill(self,amount,i):
  self.c['providers']['fake']['operations']['fill']=amount;self.c['providers']['fake']['operation_purposes']={'fill':'high_value'}
  self.l.create_run('fill'+str(i),'10');self.l.reserve('fill'+str(i),'fake','fill',str(i))
 def test_25_session_limit(self):
  for i,v in enumerate(('10','10','4.999')):self.fill(v,i)
  with self.assertRaises(StopRun):self.client().search('synthetic')
  self.assertFalse(self.sent)
 def test_100_poc_limit(self):
  for i in range(10):self.c['session']['id']='hist'+str(i//2);self.fill('10',i)
  with self.assertRaises(StopRun):self.client().search('synthetic')
  self.assertFalse(self.sent)
 def test_20_cutoff(self):
  self.fill('10',0);self.fill('10',1)
  with self.assertRaises(StopRun):self.client().search('synthetic')
  self.assertFalse(self.sent)
 def test_5_run_limit(self):
  self.l.db.execute("UPDATE operations SET actual=actual WHERE 0")
  self.c['providers']['fake']['operations']['fill']='4.999'
  self.l.reserve('test','fake','fill','fill')
  with self.assertRaises(StopRun):self.client().search('synthetic')
  self.assertFalse(self.sent)
 def test_no_unfiltered_free_fallback(self):
  self.c['provider_priority']={'free_discovery':['fake']}
  class Legacy:pass
  router=ProviderRouter(self.l,'test',lambda:self.l.check('test'),{'fake':Legacy})
  with self.assertRaises(StopRun):router.search('synthetic',10,{'start_date':'2026-06-10'})
 def test_disabled_tavily_not_activated_by_route(self):
  self.c['providers']['tavily']['enabled']=False;self.c['provider_priority']={'free_discovery':['tavily']}
  router=ProviderRouter(self.l,'test',lambda:self.l.check('test'),{'tavily':Tavily})
  with self.assertRaises(StopRun):router.search('synthetic')
  self.assertFalse(self.sent)
 def test_employer_packet_no_submission(self):
  p=prepare({'employer_name':'Synthetic contractor'});self.assertFalse(p['outreach_enabled']);self.assertFalse(p['automated_site_access']);self.assertIn('pay_range',p['missing_fields']);self.assertEqual(p['channels']['bluerecruit']['monthly_connections'],3)
 def test_channel_import_requires_eligibility_permission(self):
  for channel in ('worksource_atlanta','bluerecruit'):
   with self.assertRaises(StopRun):validate_import({'channel':channel})
 def test_channel_import_requires_worker_consent(self):
  with self.assertRaises(StopRun):validate_import({'channel':'worksource_atlanta','access_confirmed_by_human':True,'retention_permission_confirmed':True,'candidates':[{}]})
 def test_reviewed_channel_import_allowed(self):
  record={'reviewed_by_human':True,'consented_referral':True,'source_record_id':'synthetic'}
  self.assertEqual(validate_import({'channel':'bluerecruit','access_confirmed_by_human':True,'retention_permission_confirmed':True,'direct_employer':True,'free_plan_confirmed':True,'candidates':[record]}),[record])
 def test_stronger_signal_screening(self):
  for text in ('My friend is looking for work','Not currently looking for a job','Looking for work. Accepted a new position.'):
   p=screen({'url':'https://example.org/fixture','title':'Jane Doe','text':'Commercial electrician. '+text})
   self.assertFalse(p['possible_recruiting_signal'])
 def test_new_plans_date_filters_and_diversity(self):
  s=new_state();s.update(improved=True,search_as_of='2026-09-08',focus_month='September 2026')
  seen=set();strategies=set()
  for i in range(120):
   p=next_query(s);seen.add(p['query']);strategies.add(p['strategy']);self.assertIn('exclude_domains',p['options']);s['queries'].append(p);s['discovery_index']+=1
  self.assertEqual(len(seen),120);self.assertEqual(len(strategies),4)
 def test_global_ab_needs_signal_attribution(self):
  a={'classification':'A','reviewed':True,'trade_fit':True,'identified_person':True,'geographic_fit':True,'recruiting_signal':'fixture','signal_date':datetime.date.today().isoformat(),'source_urls':['https://example.org']}
  with self.assertRaises(StopRun):self.l.record_qualification('test','fixture',a)
 def test_later_hired_update_downgrades_prior_packet(self):
  s=new_state();p={'query':'fixture','purpose':'discovery','strategy':'fixture','target':None}
  row={'url':'https://example.org/person','title':'Jane Doe','text':'Commercial electrician looking for work.'}
  consume(s,p,{'provider_response':{'results':[row]}},'first','fixture')
  row['text']='Commercial electrician looking for work. I got hired.'
  consume(s,p,{'provider_response':{'results':[row]}},'later','fixture')
  self.assertTrue(s['packets'][row['url']]['contradiction_flag']);self.assertEqual(s['packets'][row['url']]['classification'],'Passive Research Pool')
