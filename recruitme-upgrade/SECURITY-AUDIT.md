# RecruitMe security and spending audit — 2026-09-13

Scope: worker accounting, request dispatch, termination reporting, bridge failure handling and synthetic tests. No paid requests, provider activation, deployment, IAM change, frontend redesign, search planning or scoring change was performed.

## Safeguards audited

- SQLite integer-microdollar reservation before transport; BEGIN IMMEDIATE serializes competing spend. Unknown charges survive restart. Existing run/session deadlines and budgets cannot be increased by resume. POC ceiling is $100; session ceiling $25; web run ceiling $5; the final $5 session allocation restricts ordinary enrichment.
- Provider/run request counters include reservations, failures and setup calls. Provider limits, bounded attempts, fixed endpoints, disabled redirects, bounded responses and pinned expiring prices were inspected. No model API client is present in the worker flow audited; unknown/unpriced operations fail closed.
- Worker and launch file locks, manifest binding, immutable shared runtime, autonomous alarm, evidence checkpoints, disk/storage limits and durable provider health were inspected. Existing systemd deployment documentation specifies 512 MiB RAM, 25% CPU, 1800-second runtime and Restart=no.
- Provider credential readers require root ownership, the recruitme group, restrictive permissions, regular files and no symlink traversal. Keyed transport redacts reflected keys before saving responses. Web endpoints require administrator authorization. Apollo uses SSM SecureString via a restricted temporary file with cleanup.

## Problems found and changes made

1. Router exhaustion falsely reported PROVIDER_LIMIT_REACHED for local request allocations, local budgets and absent routes. It now preserves per-source blocking reasons, uses LOCAL_REQUEST_LIMIT_REACHED / BUDGET_LIMIT_REACHED / NO_ELIGIBLE_PROVIDER, and only reports a provider limit following provider health evidence or a provider-limit exception. Routing between approved source allocations remains intact; a global/run budget rejection never triggers fallback.
2. Brave's local rolling $5 allowance was mislabeled as a provider limit. It now stops as a budget limit; explicit resume is required after the allowance becomes available.
3. Free MCP transport bypassed dispatch validation and audit. It now uses the same atomic, single-use dispatch gate as paid clients.
4. Cache lookup and reservation were separate, allowing competing requests for the same search. Duplicate search detection now occurs inside the reservation transaction across a shared runtime. Existing successful receipts remain reusable. Uncertain requests are not resent automatically. This also covers content adapters using the common search operation.
5. NaN/non-integer request ceilings could undermine comparisons. Reservation now rejects malformed request/attempt ceilings before transport.
6. Connector exception handlers erased runtime/budget guard reasons. They now preserve StopRun exceptions while retaining unknown liability. Runtime expiry is distinct from monetary exhaustion.
7. Added structured RUN_TERMINATION audit events and latest terminations in ledger summaries; CLI errors include a code. Existing string reasons remain compatible and now carry explicit codes. Finishing all requested work exactly at a money cap is normal completion, without checking for headroom for a nonexistent next request.
8. Bridge subprocess diagnostics could expose secrets to the browser. Public failures now use bounded generic messages. AWS CLI children now have a 30-second timeout and 2 MiB output bound, with instructions to inspect status before retrying an uncertain launch.

## Automated verification

Final worker suite: **255 run, 250 passed, 5 skipped, 0 failures**. Final web suite: **17 passed, 0 failures**. Bridge JavaScript syntax check passed. Earlier discovery/scoring failures disappeared as the other agents updated their work; this task did not change scoring expectations.

New focused suite: **14 passed**. It deliberately attempts 100 concurrent $1.25 reservations against $5: exactly 4 succeed, total $5. Exact $1.25 cap allows one dispatch and rejects repeated dispatch and further requests. Competing identical searches reserve once. Unknown $1.25 liability survives reopening. Local request/budget stops, missing routes, provider 429, runtime expiry, malformed limits, free dispatch audit and normal completion codes are checked. The 429 test makes one fake transport call across two runs even with Retry-After present.

Existing spending tests also pass: $100 across runs, $25 session, $20 enrichment cutoff, session overshoot refusal, $5 Brave rolling allowance including unknown operations, provider allocations, expired pricing, price-breach freeze, and free requests blocked after paid budget exhaustion. The new web test confirms a synthetic secret in child stderr does not reach a launch error.

Logs in the original workspace: output/security-tests/focused.log, tests-final.log and web.log. All transports in these tests are synthetic. Five skipped tests require Linux worker execution/systemd isolation; they must run during integration staging.

## Files changed by this task

- recruitme-upgrade/recruitme/budget.py
- recruitme-upgrade/recruitme/governors.py
- recruitme-upgrade/recruitme/connectors.py
- recruitme-upgrade/recruitme/exa_keyed.py
- recruitme-upgrade/recruitme/routing.py
- recruitme-upgrade/recruitme/worker.py
- recruitme-upgrade/recruitme-worker-bridge.js
- recruitme-upgrade/tests/test_security_controls.py (new)
- recruitme-upgrade/tests/test_hardening.py (two revised stop expectations)
- recruitme-upgrade/tests/test_search_policy.py (local budget expectation and explicit resume)
- server/recruitme.ts (two sanitized error messages)
- server/recruitme.test.ts (secret-redaction test)
- recruitme-upgrade/SECURITY-AUDIT.md (this report)

## Integration and remaining operational limits

- The shared checkout was switched externally from codex/security-budget to codex/codex/integration-qa during testing. Delivery is preserved on codex/security-budget in an isolated worktree. No merge is performed. RecruitMe source was untracked in the starting repository: the delivery necessarily contains whole-file snapshots of the listed files, including their pre-existing content. Integrate the scoped changes above against the complete RecruitMe source, retaining other agents' work; this is not a standalone application release.
- No live AWS IAM policy, security group, metadata configuration, deployed service sandbox or provider billing account was queried or changed. Their effective isolation is unverified here. The bridge defaults to AWS-RunShellScript, which is a privileged control surface; integration must verify the actual role is restricted to the intended worker and approved SSM document, and cannot administer unrelated applications. The worker must remain unable to access metadata/Hermes credentials or modify its config/code.
- Application caps enforce ledger-managed liability, not independent account subscriptions, requests made outside RecruitMe, or EC2 costs. Provider prices remain pinned assumptions: a provider charging above the reservation triggers a persistent freeze after the response, but cannot undo that charge. Account caps and no-overage settings require separate operational verification.
- Generic provider failures preserve reservations and do not retry automatically. Provider health stays blocked until operator review; Retry-After is deliberately not an automatic resumption instruction. A bridge timeout is an uncertain launch, not permission to create another job.
- Ledger summaries include additive termination data. Existing snapshots expose string reasons; integration can use the new audit codes without changing search/scoring or redesigning the frontend. Mixed source exhaustion retains each source reason; the top-level code prioritizes budget, then local request, then provider limitation.
- Existing cumulative limits are trusted operator configuration, while persistent run/session budget bindings cannot increase. Preserve the production database, config ownership and original runtime when staging or deploying; never replace the ledger with a test database. Run the skipped Linux/systemd checks before deployment. No provider price refresh or account activation is included.
