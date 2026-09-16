import json
import pathlib
import subprocess
import datetime

service_state = (
    subprocess.check_output(["systemctl", "show", "recruitme", "-p", "ActiveState", "--value"], text=True)
    .strip()
    .lower()
)

result_dir = pathlib.Path("/var/lib/recruitme/results")
run_files = sorted(result_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if result_dir.exists() else []

active_run = None
status = "IDLE"
running = False
started_at = None
runtime_seconds = None
detail = None

if service_state in {"active", "activating"}:
    running = True
    status = "RUNNING"

if run_files:
    latest = run_files[0]
    try:
        data = json.loads(latest.read_text())
        active_run = data.get("run_id") or latest.stem
        status = data.get("status") or status
        started_at = data.get("created_at") or data.get("start_time")
        runtime_seconds = data.get("runtime_seconds")
        if isinstance(started_at, (int, float)):
            started_at = datetime.datetime.fromtimestamp(started_at, tz=datetime.timezone.utc).isoformat()
    except Exception as exc:
        detail = str(exc)

if running:
    current=json.loads(pathlib.Path('/etc/recruitme/first-search.json').read_text())
    active_run=current['run_id']
    status='RUNNING'
meter = json.loads(subprocess.check_output(['python3',str(pathlib.Path(__file__).with_name('export_web_snapshot.py')),'--dashboard'],text=True,timeout=20))
print(
    json.dumps(
        {
            "online": bool(service_state in {"active", "activating"}),
            "status": status,
            "activeRunId": active_run,
            "startedAt": started_at,
            "running": bool(running),
            "detail": detail or f"recruitme service state: {service_state}",
            "lastUpdated": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "runtime_seconds": runtime_seconds,
            "meter": meter,
        }
    )
)
