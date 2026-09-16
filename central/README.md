# ECI Central

Staff landing page for `central.ecinc.us`, with RecruitMe, Timex, DevPool, Safety Admin and Warehouse. The last four application links intentionally remain “Coming soon” until their addresses are supplied.

## Build and host

From the Candidate Portal workspace:

```powershell
node node_modules/vite/bin/vite.js build --config central/vite.config.ts
node node_modules/esbuild/bin/esbuild central/server.ts --bundle --platform=node --format=esm --packages=external --outfile=central-dist/server.mjs
node node_modules/typescript/bin/tsc -p central/tsconfig.json --noEmit
node node_modules/vitest/vitest.mjs run server/recruitme.test.ts server/recruitmeSnapshot.test.ts
```

The new service owns `/opt/eci/central` and `/var/lib/eci-central`, and binds only to `127.0.0.1:3100` on the Candidate Portal host. Apache routes only the Central hostname. The existing Candidate Portal remains at port 3000; its release, configuration, database and staff allowlist are not replaced. Runtime dependencies are pinned by symlink to the existing portal release `0638a5c`; retain that release until Central dependencies are packaged independently.

The backend relays only four fixed staff-auth procedures to the existing loopback identity service. Every RecruitMe endpoint checks the authenticated administrator role server-side. No identity secret or production database configuration is copied. This initial release uses the existing staff administrator allowlist; it does not enroll all employees or grant access to the other applications. Full sign-in verification requires an authorized staff member to complete the email-code flow.

## DNS and HTTPS

Bluehost record: `A`, host `central`, value `18.119.237.241`, default TTL. This is the existing Candidate Portal Elastic IP. No root, mail or other domain records need changing. `enable-https.py` verifies DNS before requesting a certificate with the existing Certbot account. The HTTP route redirects to HTTPS; authentication is not served over plaintext HTTP.

## RecruitMe scope

The UI edits versioned job profiles and displays timestamped worker snapshots: run history, conservative spending, source setup status and candidate evidence. JSON export preserves provenance. The electrical recruiter is the initial profile, including the annual salary target, dual experience requirement and 30-day A/B signal rule.

The snapshot is read from `/var/lib/eci-central/worker-snapshot.json`. `recruitme-upgrade/export_web_snapshot.py` is a read-only, allowlisted export from AWS; transfer its output through the administrative deployment channel. The initial snapshot is **not** a continuously refreshed live bridge. The UI labels old snapshots and never treats absence of data as zero spending.

Browser search launch remains disabled until a separately validated control bridge exists. Profile preferences cannot raise worker caps. No new search, account purchase, provider activation or candidate contact is performed by installing this release.

## Source integrations

Ten implemented adapter routes: Exa public MCP, Exa Search, Exa People, Tavily Search, Brave Search, SerpAPI Google, PDL free-only structured people, Exa Contents, Tavily Extract and Bright Data public LinkedIn profiles. Discovery and single-URL content adapters are separated. The catalogue also clearly identifies manual workflows and the planned Coresignal integration; those are not described as installed API clients.

New adapters remain disabled. `recruitme.plugins.disabled_config()` produces configuration suggestions only; an operator must reconcile actual account plan, approved scope, immutable run/session limits and persistent provider counters before activation. Prices expire October 12, 2026 for new routes. SerpAPI reserves the amortized Starter-credit cost; it does not purchase a subscription. PDL requires a verified free-only account with overages disabled and no more than ten lifetime requests of at most ten records. Bright Data submits a single public profile; asynchronous fallback preserves the reservation and never resubmits automatically.

Use `sudo python3 /opt/recruitme/configure_plugin_key.py brave` (or `serpapi`, `pdl`, `brightdata`) in an interactive worker terminal. The hidden prompt creates a root-owned, restricted file. It neither enables the provider nor calls an API. Exa and Tavily reuse their existing protected credential files. Never paste keys into chat or SSM command payloads.

`content_review` jobs accept one explicitly selected content adapter and 1–10 HTTPS URLs on configured `allowed_domains`. They preserve full text in evidence files and require review; they do not assign verified grades. New adapters require account-level controlled tests before production use.

## Recovery

Central can be stopped independently with `systemctl stop eci-central`. Disable only its two Apache site files and reload Apache after a successful configuration test if routing must be rolled back. Do not stop or replace the Candidate Portal or Hermes. Worker source backups and a ledger-preservation receipt are stored under `/opt/recruitme/backups/plugins-20260912-v1` after installation.

## Password login (2026-09-13)
Central now has an independent password option for explicitly invited staff. An administrator provisions a 30-minute single-use invitation in /var/lib/eci-central/auth/password-invite.json (hashed token, fixed email/role identity). There is no public registration or public password reset. Setup consumes the invitation; new invitations never overwrite existing password accounts. The account uses salted scrypt (N=32768, r=8, p=1), and sessions use opaque random tokens stored as hashes, with Secure/HttpOnly/SameSite=Strict host-only cookies and 12-hour expiry. Logout revokes the session. Passwords are entered by the user in the browser, never placed in release files. Existing portal email-code authentication remains available. Central password accounts grant no new permissions in other applications.

The production service remains a single process; auth state files are atomic writes inside the private Central state directory. Scale-out would require a shared transactional store and distributed throttling. Login/setup are limited per IP and normalized email; concurrent password hashing is bounded. HTML uses no-store to prevent stale login pages.

Deployment: 20260913-password-v1, rolled forward from 20260913-credits-v1 with all existing release files preserved. Tests: two password security tests and thirteen RecruitMe regression tests pass; production invalid-password and anonymous-workspace checks pass. Full project type checking still has unrelated chart/input-otp/ComponentShowcase errors; no Central diagnostics remain.

Email delivery test: sign-in code request returned 200 with challenge; separate actual Microsoft Graph test returned token 200 and sendMail 202 for Charles@ecinc.us. Acceptance by Microsoft does not confirm inbox delivery. No delivery failure was found in inspected portal log tails. Waiting for recipient confirmation; root cause of the previously missing code is not established.
