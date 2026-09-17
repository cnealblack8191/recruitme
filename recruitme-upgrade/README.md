# RecruitMe options 1-4 integration

Maintained upgrade source in the Candidate Portal workspace. Installed target: `/opt/recruitme` on `i-00d4af5fb05831699`, us-east-2. The older `Recruit me` workspace is the pre-upgrade reference snapshot.

## Implemented

- Exa standard search: 1-10 results at the pinned $0.007 maximum, explicit date/domain filters, filter-aware cache identity, excluded-source result removal before persistence. No unpriced summaries, deep mode or content endpoint has been enabled.
- Tavily official basic search: $0.008 conservative reservation before each request, even when free credits are available. No automatic depth selection, purchases, retries or outreach. Quota HTTP statuses 402/429/432/433 and known quota notices stop the provider and preserve the operation/time. Missing keys fail closed.
- New autonomous jobs default to `intent-v2`: Georgia-first generated intent queries, date-filtered and separate undated branches, ten results, candidate-specific follow-ups, approximately 2/3 discovery and 1/3 follow-up when promising packets exist. Old resumed checkpoints retain their original behavior/state and deadline.
- Third-party interest and negated/superseded availability do not support active interest. Later contradictory evidence downgrades a packet. A/B qualification requires explicit signal-subject, signal-date and contradiction-review confirmations in addition to existing qualification evidence. No automated A/B promotion.
- WorkSource Atlanta and BlueRecruit: employer referral preparation, official URLs, eligibility/registration state and a `channel_import` worker mode requiring reviewed, consented records and retention permission. There is no scraping, registration, messaging or connection-activation client for either site.
- `recruitme-worker-bridge.js` and `status/stop/launch` bridge scripts are now available for one-click RecruitMe control launches.

## RecruitMe web bridge controls

The server now expects three JSON-array commands, plus an optional fourth for storing reviewed candidates:

```bash
RECRUITME_BRIDGE_LAUNCH_CMD
RECRUITME_BRIDGE_STOP_CMD
RECRUITME_BRIDGE_STATUS_CMD
RECRUITME_BRIDGE_REVIEW_CMD   # ["node","/path/to/recruitme-worker-bridge.js","review"]
```

The same `review` command carries Candidate Portal applications. `importApplicants` on the web server reads new portal registrations (past a stored watermark) and forwards each as a `candidate_portal` submission with decision `APPLICANT`; `recruitme/applicants.py` marks only the seeking signal verified (the portal's own timestamp) so applicants land as PROVISIONAL until a recruiter confirms fit in the review form. It needs `RECRUITME_PORTAL_BASE_URL` (public portal address used as the evidence URL) and the portal `DATABASE_URL`; applicant emails never leave the portal.

`review` runs `review_import_remote.py` on the worker. It takes one recruiter-form submission (see `shared/recruitmeReview.ts` and `recruitme/review.py`), converts it into a reviewed import with per-evidence human attestations, stores it under a zero-budget `review-*` run, associates it with the discovery run the reviewer was viewing, and returns the qualification result. An A or B decision is stored only when every gate passes; otherwise the worker rolls back and returns the failing gates so the reviewer can downgrade to `FIT_POOL`. Identity confidence below `confirmed` keeps every claim an inference. The active job's profile (`/etc/recruitme/first-search.json`) supplies the localities, signal window and role kind; a submission may narrow them.

Recommended runtime wiring:

```bash
RECRUITME_BRIDGE_ENABLED=true
RECRUITME_BRIDGE_LAUNCH_CMD=["node","/path/to/recruitme-upgrade/recruitme-worker-bridge.js","launch"]
RECRUITME_BRIDGE_STOP_CMD=["node","/path/to/recruitme-upgrade/recruitme-worker-bridge.js","stop"]
RECRUITME_BRIDGE_STATUS_CMD=["node","/path/to/recruitme-upgrade/recruitme-worker-bridge.js","status"]
```

Remote actions are driven by:

- `launch_metro_deep_remote.py`
- `stop_metro_deep_remote.py`
- `status_metro_deep_remote.py`

Set script/cluster context with:

- `WORKER_INSTANCE_ID`
- `RECRUITME_AWS_REGION` (or `AWS_REGION`)
- `AUTH_METHOD` (`aws_profile` or `access_keys`)
- `AWS_PROFILE` when using profile auth
- `RECRUITME_WORKER_SCRIPT_ROOT` to the worker workspace root (defaults to `/opt/recruitme`)

## Activation still required

Tavily is approved as a connector but **disabled**. Obtain a free account/key at https://app.tavily.com/ and confirm free capacity and that paid upgrades/automatic charging are not enabled. Do not paste the key into a chat, source file or SSM command.

In the existing interactive EC2 terminal:

```sh
sudo /opt/recruitme/venv/bin/python -B /opt/recruitme/configure_tavily_key.py
```

The hidden prompt saves `/etc/recruitme/tavily-api-key` as root:recruitme, mode 0640. It does not enable the provider or call its API. Use `--replace` only for an intentional rotation. After installation, perform an explicitly authorized, governed minimal test and then enable the connector. The existing Exa API key is untouched.

Before a research run: explicitly approve a new immutable runtime and a bounded increment to the exhausted 500-operation Exa limit. Preserve prior operations and cumulative money; do not reuse or renew the expired session automatically. Provider routing is `exa_free -> tavily (when enabled) -> exa_keyed`. Filtered queries skip any connector that cannot honor filters. A failed hard money/runtime/local request guard does not silently bypass itself through routing.

## WorkSource and BlueRecruit

Generate a local employer packet (no network activity):

```sh
sudo -u recruitme /opt/recruitme/venv/bin/python -B -m recruitme.channels --output /var/lib/recruitme/employer-packet.json
```

Run from `/opt/recruitme`, or set `PYTHONPATH=/opt/recruitme`. Existing output files are not overwritten. The prepared JSON lists missing employer name, work location, pay range, role, commercial tasks, experience, schedule, start date and travel radius. A completed JSON brief can be supplied with `--brief`.

WorkSource: https://worksourceatlanta.org/programs-and-services-for-employers/ . Confirm employer/service-area eligibility and consented referrals through normal employer services.

BlueRecruit: https://bluerecruit.us/employers/ . Its free tier lists three connections monthly for eligible direct employers; staffing firms, recruiters and RPOs are excluded. RecruitMe does not consume connections automatically. Account access does not itself authorize exports.

`channel_import` jobs require `channel`, `access_confirmed_by_human=true`, `retention_permission_confirmed=true` and standard reviewed candidate records. BlueRecruit additionally requires `direct_employer=true` and `free_plan_confirmed=true`. Every record requires `reviewed_by_human=true`, `consented_referral=true`, `source_record_id`, stable `identity_key` and the normal matching fact/evidence fields. Normal budget/runtime/resource guards remain applicable. Neither import nor research sends outreach.

## Budget and access safeguards

Default run cap is lowered to $5; $25 maximum session/$100 maximum POC and the final-$5 high-value restriction remain. The prior session's lower residual cap/cutoff is preserved. Tavily additionally has 40 requests/$1 per run and 100 cumulative requests/$5 provider allowance. All operations reserve list-price liability, irrespective of free-credit estimates. Unknown charges remain reserved. Account billing must be reconciled separately.

The new query planner excludes LinkedIn, Facebook, Reddit, Craigslist and PostJobFree pending a separate source collection/retention permission basis. This deliberately trades some indexed coverage for the permission requirements identified in the research. Existing historical evidence is not deleted or modified. Employer platforms use manual/consented workflows; contact is not an A/B gate.

Exa pricing: https://exa.ai/docs/reference/pricing ; API filters: https://exa.ai/docs/reference/search . Tavily pricing: https://docs.tavily.com/documentation/api-credits ; API: https://docs.tavily.com/documentation/api-reference/endpoint/search . Prices are pinned with expiration; unknown settings fail closed.

## Verification and maintenance

Tests use temporary synthetic databases and fake HTTP transports. Staging tests run with networking disabled, CPUQuota=25%, MemoryMax=512M and a bounded runtime. The installed selftest additionally checks the existing production systemd sandbox. Deployment checks the old code hashes, validates the staged test manifest, backs up changed code/config and hashes all production database rows before/after. No production research request or account purchase is part of deployment.

Scripts `build_bundle.py`, `stage_template.py`, `deploy_remote.py` and `verify_remote.py` describe this one-time installation. Do not replay deployment blindly: it intentionally refuses source/config drift. Hermes, IAM, security groups and EC2 resources are unchanged.
