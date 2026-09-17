"""Store one reviewer submission from Central in the worker ledger. No provider requests."""
import fcntl
import json
import pathlib
import sys
from recruitme.budget import Ledger, StopRun
from recruitme.review import import_submission

root = pathlib.Path('/etc/recruitme')
state = pathlib.Path('/var/lib/recruitme')
payload = json.load(sys.stdin)
if payload.get('action') != 'review' or not isinstance(payload.get('submission'), dict):
    print(json.dumps({'accepted': False, 'errors': ['Invalid review request']})); raise SystemExit(0)
profile = None
try:
    # The active or last launched job carries the profile whose policy governs review.
    job = json.loads((root / 'first-search.json').read_text())
    profile = job.get('job_profile')
except (OSError, ValueError):
    profile = None
with (state / 'review.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        ledger = Ledger(state / 'recruitme.db', json.loads((root / 'config.json').read_text()), state_root=state)
        result = import_submission(ledger, payload['submission'], profile=profile)
    except StopRun as error:
        result = {'accepted': False, 'errors': [str(error)]}
print(json.dumps(result))
