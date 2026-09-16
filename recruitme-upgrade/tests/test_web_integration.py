import datetime
import tempfile
import unittest
from pathlib import Path
from recruitme import data
from recruitme.autonomous import new_state, consume
from recruitme.budget import Ledger, StopRun
from recruitme.web_snapshot import discovery_rows, reviewed_rows
from test_foundation import configuration
from test_qualification import record


class WebIntegration(unittest.TestCase):
    def test_discovery_review_ranking_contact_and_budget_pipeline(self):
        today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        with tempfile.TemporaryDirectory() as folder:
            ledger = Ledger(Path(folder) / 'synthetic.db', configuration())
            try:
                ledger.create_run('controlled', '1.25')
                data.initialize(ledger.db)
                operation = ledger.reserve('controlled', 'fake', 'small', 'query-1')
                ledger.dispatch('controlled', operation)
                state = new_state()
                plan = {'query': 'commercial electrician Atlanta Georgia 6 years open to work', 'purpose': 'discovery', 'target': None}
                response = {'results': [{'url': 'https://example.org/person?utm_source=test', 'title': 'Jordan Example - Electrician',
                    'text': 'Commercial electrician with 6 years in Atlanta Georgia. I am open to work.', 'publishedDate': today},
                    {'url': 'https://example.org/person', 'title': 'Jordan Example - Electrician',
                    'text': 'Commercial electrician with 6 years in Atlanta Georgia. I am open to work.', 'publishedDate': today}]}
                consume(state, plan, {'provider_response': response}, today, Path(folder) / 'evidence.json')
                hints = discovery_rows('controlled', list(state['packets'].values()))
                self.assertEqual(len(hints), 1)
                self.assertFalse(hints[0]['verified'])
                self.assertIsNone(hints[0]['signalDate'])
                self.assertIsNone(hints[0]['qualificationScore'])
                self.assertTrue(hints[0]['contactRoutes'])
                self.assertTrue(hints[0]['evidenceLinks'])
                reviewed = record()
                for e in reviewed['evidence']:
                    e['retrieved_at'] = e['original_date'] = today
                reviewed['contacts'][0]['retrieved_at'] = today
                data.import_candidate(ledger.db, reviewed, run_id='controlled')
                data.import_candidate(ledger.db, reviewed, run_id='controlled')
                rows = reviewed_rows(ledger.db, 'controlled')
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['qualificationScore'], 100)
                self.assertEqual(rows[0]['signalDate'], today)
                self.assertTrue(rows[0]['verified'])
                self.assertTrue(rows[0]['contactRoutes'])
                self.assertTrue(any('VERIFIED_FACT' in link['label'] for link in rows[0]['evidenceLinks']))
                self.assertEqual(reviewed_rows(ledger.db, 'unrelated'), [])
                ledger.reconcile(operation, None)
                self.assertEqual(ledger.summary()['committed_usd'], '1.25')
                with self.assertRaises(StopRun):
                    ledger.reserve('controlled', 'fake', 'small', 'query-2')
                self.assertEqual(ledger.summary()['operations'], 1)
            finally:
                ledger.db.close()

    def test_legacy_candidates_are_not_assigned_to_arbitrary_runs(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Ledger(Path(folder) / 'synthetic.db', configuration())
            try:
                data.initialize(ledger.db)
                data.import_candidate(ledger.db, record())
                self.assertEqual(reviewed_rows(ledger.db, 'unrelated'), [])
            finally:
                ledger.db.close()
