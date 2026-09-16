# RecruitMe web workspace

Route: `/recruitme` in the existing React/Express Candidate Portal source. This is a local implementation, not an online deployment.

Implemented: authenticated administrator boundary; responsive navigation; persistent, versioned job profiles; editable roles/fit/geography/compensation/start constraints; $5/30-minute maximum profile preferences; profile JSON export; audit attribution; explicit worker-disconnected state. Other occupations use the same profile editor. Profiles are stored server-side in `RECRUITME_WEB_STATE_DIR` (default `.recruitme-web`, excluded from git). Run one owning web process for this POC file store; use a transactional shared store before multi-process hosting.

Not connected: live ledger, start/stop worker control, historical candidates, run history and report export. The launch API rejects requests until the secure bridge is implemented and verified. The browser does not store keys, start shell commands or invent balances. Empty run/candidate views explicitly describe missing integration rather than asserting no historical records exist.

Production plan: keep staff authentication at the existing web gateway. A separate authenticated server-to-worker bridge must expose allowlisted profile submission, status, evidence/report reads and stop requests. No arbitrary shell interface. The EC2 worker alone owns reservations, immutable runtime, cumulative provider counters and checkpoints. Job submission must be idempotent and preserve a launch receipt. Start/stop must operate through the isolated RecruitMe service, never Hermes. Serve browser traffic over existing TLS; do not expose an unauthenticated worker port.

Publishing requires current AWS access, inspection of the actual hosted portal/auth stack, and the selected address. Do not replace a newer production portal with this checkout. Inspect drift and port only the RecruitMe feature files. No IAM/security-group/resource changes are authorized by these files.

Before release: complete worker bridge and ledger integration; map web profiles to validated worker manifests; import reports with source provenance and qualification review; test authorization, idempotency, stop behavior and budget exhaustion end to end; run Linux worker tests; verify production authentication and mobile layout. There are no automatic purchases or outreach.
