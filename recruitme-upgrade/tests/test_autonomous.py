import datetime
import json
from pathlib import Path
import tempfile
import unittest
import os
from unittest.mock import patch
from recruitme.autonomous import new_state,next_query,screen,consume,evaluate_yield,execute
from recruitme.budget import Ledger,StopRun
from test_foundation import configuration


class Autonomous(unittest.TestCase):
    def test_five_dollar_cap_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            l=Ledger(Path(tmp)/'db',configuration());l.create_run('five','5')
            for i in range(4):l.reserve('five','fake','small',str(i))
            with self.assertRaises(StopRun):l.reserve('five','fake','small','over')
            self.assertEqual(l.total(),5000000);l.db.close()

    def test_negated_and_superseded_interest_not_active(self):
        for s in ['NOT seeking employment','Looking for work. I was just hired by Another Company']:
            self.assertNotEqual(screen(self.fixture(text='Commercial electrician. '+s))['classification'],'C — Provisional')

    def test_liked_posts_not_personal_signal(self):
        self.assertFalse(screen(self.fixture(text='Commercial electrician.\n## Social\nLiked this: looking for work'))['possible_recruiting_signal'])

    def test_relocating_equipment_not_interest(self):
        self.assertFalse(screen(self.fixture(text='Commercial electrician relocating electrical gear room.'))['possible_recruiting_signal'])

    def test_author_name_for_post(self):
        self.assertEqual(screen(self.fixture(title='I want another employer | Jane Doe',author='Jane Doe'))['name_hint'],'Jane Doe')

    def test_profile_metadata_not_freshness_bonus(self):
        a=screen(self.fixture());b=screen(self.fixture(publishedDate=None))
        self.assertEqual(a['review_priority'],b['review_priority'])

    def test_focused_queries_vary_without_exhaustion(self):
        s=new_state();s.update(focused=True,focus_month='September 2026',focus_range='June 2026 through September 2026')
        seen=set()
        for i in range(150):
            q=next_query(s);seen.add(q['query']);s['queries'].append(q);s['discovery_index']+=1
        self.assertEqual(len(seen),150)

    def fixture(self,**kw):
        p={'url':'https://example.org/jane','title':'Jane Doe - Electrician',
           'text':'I am a commercial electrician with 8 years conduit and switchgear installation. Looking for work in Atlanta.',
           'publishedDate':datetime.datetime.now(datetime.timezone.utc).date().isoformat()}
        p.update(kw);return p

    def test_experience_without_signal_never_ab(self):
        p=screen(self.fixture(text='Commercial electrician with 8 years conduit and switchgear.'))
        self.assertEqual(p['classification'],'Passive Research Pool')

    def test_signal_and_fit_still_requires_review(self):
        p=screen(self.fixture())
        self.assertEqual(p['classification'],'C — Provisional')
        self.assertTrue(p['human_review_required']);self.assertFalse(p['signal_date_confirmed'])

    def test_hiring_ad_not_candidate(self):
        p=screen(self.fixture(text='We are hiring a commercial electrician. Open to work? Apply now.'))
        self.assertEqual(p['classification'],'Rejected')

    def test_data_brokers_excluded(self):
        self.assertIsNone(screen(self.fixture(url='https://www.spokeo.com/Jane-Doe')))

    def test_query_generation_continues_past_batch(self):
        state=new_state();seen=set()
        for i in range(100):
            q=next_query(state);seen.add(q['query']);state['queries'].append(q);state['discovery_index']+=1
        self.assertEqual(len(seen),100)
        self.assertIn('Georgia',next_query(new_state())['query'])

    def test_pending_request_resumes_same_query(self):
        s=new_state();p=next_query(s);s['pending']=p;s['discovery_index']=999
        self.assertEqual(next_query(s),p)

    def test_one_third_candidate_followups(self):
        s=new_state();p=screen(self.fixture());s['packets'][p['source_url']]=p
        purposes=[]
        for i in range(9):
            plan=next_query(s);purposes.append(plan['purpose']);s['queries'].append(plan)
            if plan['target']:s['followups'][plan['target']]=s['followups'].get(plan['target'],0)+1
            else:s['discovery_index']+=1
        self.assertEqual(purposes.count('corroboration/contact'),3)

    def test_duplicate_pages_not_new_people(self):
        s=new_state();plan=next_query(s);response={'provider_response':{'results':[self.fixture(),self.fixture()]}}
        consume(s,plan,response,'fixture','raw.json')
        self.assertEqual(len(s['packets']),1);self.assertEqual(s['duplicates'],1)
        self.assertEqual(len(s['packets'][self.fixture()['url']]['observations']),2)

    def test_materially_different_diminishing_returns(self):
        s=new_state()
        for window in range(6):
            s['queries'].extend([{'strategy':'fixture'+str(window),'purpose':'discovery'}]*20);s['result_appearances']+=100;s['irrelevant']+=100
            stop=evaluate_yield(s)
            self.assertEqual(stop,window==5)

    @unittest.skipUnless(os.name=='posix','Requires Linux signal timers; mandatory on EC2')
    def test_standalone_checkpoints_and_stops_without_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=configuration();l=Ledger(Path(tmp)/'db',c);l.create_run('synthetic','2')
            class Fake:
                def search(inner,*a):return {'provider_response':{'results':[self.fixture()]}}
            calls=[]
            def guard():
                if calls:raise StopRun('SYNTHETIC_GUARD')
                calls.append(1)
            execute(l,'synthetic',tmp,{},guard,client=Fake(),sleep=lambda n:None)
            saved=json.loads((Path(tmp)/'results/synthetic.json').read_text())
            self.assertEqual(saved['completed_searches'],1)
            self.assertEqual(saved['codex_or_model_api_calls'],0)
            self.assertEqual(saved['verified_a'],0);self.assertEqual(saved['stop_reason'],'SYNTHETIC_GUARD')
            self.assertEqual(l.db.execute('SELECT COUNT(*) FROM autonomous_checkpoints').fetchone()[0],1)
            l.db.close()

    def test_content_routes_require_price_credentials_and_allowlist(self):
        from recruitme.autonomous import content_routes
        c=configuration()
        c['providers']['exa_contents']={'enabled':True,'approved':True,'price_version':'exa_contents-2026-09-12','operations':{'search':'0.001'},'allowed_domains':['linkedin.com']}
        c['providers']['tavily_extract']={'enabled':True,'approved':True,'price_version':'tavily_extract-2026-09-12','operations':{'search':'0.008'},'allowed_domains':['postjobfree.com']}
        c['providers']['bright_data']={'enabled':True,'approved':True,'price_version':'stale','operations':{'search':'0.0015'},'allowed_domains':['linkedin.com']}
        with patch('recruitme.plugins.ExaContents.credentials_available',return_value=True),patch('recruitme.plugins.TavilyExtract.credentials_available',return_value=False):
            self.assertEqual(content_routes(c),{'exa_contents':['linkedin.com']})
        c['providers']['exa_contents']['allowed_domains']=[]
        with patch('recruitme.plugins.ExaContents.credentials_available',return_value=True):
            self.assertEqual(content_routes(c),{})

    def test_profile_content_followup_dispatches_to_content_adapter_not_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=configuration();l=Ledger(Path(tmp)/'db',c);l.create_run('content','2')
            searched=[];fetched=[]
            class FakeSearch:
                def search(inner,query,*a,**k):
                    searched.append(query);return {'provider_response':{'results':[self.fixture()]},'provider':'fake'}
            class FakeContent:
                last_observed_at=None
                def __init__(inner,*a):pass
                def search(inner,url,count):
                    fetched.append((url,count));return {'provider_response':{'results':[self.fixture(text='Full profile text. Commercial electrician 8 years. Open to work.')]},'provider':'exa_contents'}
            calls=[]
            def guard():
                calls.append(1)
                if len(calls)>4:raise StopRun('SYNTHETIC_GUARD')
            with patch('recruitme.autonomous.CONTENT_PLUGINS',{'exa_contents':FakeContent}),patch('recruitme.autonomous.content_routes',return_value={'exa_contents':['example.org']}):
                execute(l,'content',tmp,{},guard,client=FakeSearch(),sleep=lambda n:None)
            saved=json.loads((Path(tmp)/'results/content.json').read_text())
            self.assertEqual(fetched,[('https://example.org/jane',1)])
            self.assertFalse(any(q.startswith('http') for q in searched))
            fetch=[q for q in saved['queries'] if q.get('content_provider')]
            self.assertEqual(len(fetch),1);self.assertEqual(fetch[0]['provider'],'exa_contents');self.assertEqual(fetch[0]['target'],'https://example.org/jane')
            self.assertGreaterEqual(saved['unique_pages'],1)
            l.db.close()

    @unittest.skipUnless(os.name=='posix','Requires Linux signal timers; mandatory on EC2')
    def test_service_termination_saves_exact_reason(self):
        import signal
        with tempfile.TemporaryDirectory() as tmp:
            l=Ledger(Path(tmp)/'db',configuration());l.create_run('terminated','2')
            class Fake:
                def search(self,*args):signal.raise_signal(signal.SIGTERM)
            execute(l,'terminated',tmp,{},lambda:l.check('terminated'),client=Fake(),sleep=lambda n:None)
            saved=json.loads((Path(tmp)/'results/terminated.json').read_text())
            self.assertEqual(saved['stop_reason'],'SERVICE_TERMINATED')
            self.assertEqual(saved['completed_searches'],0)
            l.db.close()
