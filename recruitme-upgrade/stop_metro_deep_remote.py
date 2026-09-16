import json
import sys
import subprocess
import pathlib

payload = {}
try:
  payload = json.loads(sys.stdin.read() or "{}")
except Exception:
  payload = {}

run_id = payload.get("runId") or payload.get("run_id") or "unknown"
service = (
    subprocess.check_output(["systemctl", "show", "recruitme", "-p", "ActiveState", "--value"], text=True)
    .strip()
    .lower()
)

if service in {"active", "activating"}:
  current=json.loads(pathlib.Path('/etc/recruitme/first-search.json').read_text())
  if current.get('run_id') != run_id:
    raise SystemExit('Run changed; refresh before stopping')
  subprocess.run(["systemctl", "stop", "recruitme.service"], check=True, timeout=20)
  result_status = "STOPPING"
  accepted = True
else:
  result_status = "NOT_RUNNING"
  accepted = False

print(
    json.dumps(
        {
            "accepted": bool(accepted),
            "runId": run_id,
            "status": result_status,
            "message": "Stop requested." if accepted else "Service was not running.",
        }
    )
)
