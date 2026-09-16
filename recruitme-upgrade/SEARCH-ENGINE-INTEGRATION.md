# Search engine handoff — 2026-09-13

## Follow-up verification: reported integration failures resolved

This update supersedes the open-failure status recorded below. Following the user's
request to finish resolving the failures, the current shared worker suite was rerun:
255 tests, 250 passed, 5 skipped, zero failures/errors. Parallel agents had already
updated the scoring expectations and budget/router exception expectations to their
new contracts; no production controls were weakened to make tests pass.

The preserved `codex/search-engine` worktree was also verified with the entire
255-test suite: 250 passed, 5 skipped, zero failures/errors. Its foundation fixture
was aligned with the shared checkout's current observation date so a synthetic
contact freshness test does not expire with calendar time. This follow-up changed
only that test fixture in the preserved worktree and these handoff notes.

All four previously listed failures are closed for the tested snapshots. Platform
skips still require the appropriate Linux/environment validation before deployment.
No branches were merged and no deployment or live provider request was performed.
The original search-only patch remains unchanged; it does not bundle other agents'
scoring/security updates or this fixture-date correction.

## Scope and behavior

Only discovery/search changed. No UI, scoring, qualification gates, provider prices,
budget ledger, limits, approval configuration, deployment, live API requests or outreach.

- Electrical searches rotate local availability, relevant-year resume, transition,
  and undated-review queries. Default geography stays in Metro Atlanta after the
  first batch; saved profile geography and roles remain authoritative.
- The years branch covers 3–10 years without making an exact duration mandatory
  for every retrieval. Commercial tasks accompany the queries.
- Existing 30/90/180-day retrieval filters remain distinct from signal dates.
- Free-first queries vary; explicitly selected source domains are retained and
  must be supported by the approved provider. Pending requests resume unchanged.
- Follow-ups include observed locality alongside the name to reduce namesakes.
- Known tracking URL variants collapse into one page packet. Identity-bearing
  query parameters and Apollo record fragments remain distinct. Different pages
  with the same name are NOT automatically merged into a verified person.
- Additive `discovery_evidence` contains locality mentions, explicit electrical
  duration claims, commercial-construction mentions, publication freshness, and
  explicitly labelled professional-email/source-page routes. Ownership, geography,
  and signal dates remain unverified. These fields do not influence scores.
- Every observation retains original URL, provider/source family when available,
  query, raw evidence path, retrieval date, publication metadata, signal excerpt
  and discovery evidence. Historical observations and contradiction handling remain.

## Changed files

- `recruitme/autonomous.py`: consumption, URL deduplication, web-policy planning.
- `recruitme/profiles.py`: electrical query planning and local follow-up anchors.
- `recruitme/improved_search.py`: delegates intent planning; preserves old planner as `legacy_plan`.
- `recruitme/discovery.py`: new pure planning/evidence helpers.
- `tests/test_discovery.py`: 17 new regression tests.
- This handoff and `SEARCH-ENGINE-CHANGES.patch` are integration artifacts.

The patch represents only this task's delta against the initial untracked worker
files. Apply from the repository root to that baseline; do not blindly apply it
again to the shared checkout, where the changes are already present.

## Validation

Initial baseline: 198 tests, 193 passed, 5 skipped. The sandbox initially blocked
Python temporary databases; the successful run used normal Windows temp access.

Final complete worker suite: 215 tests, 206 passed, 5 skipped, 2 failures and 2 errors.
Files outside this task changed concurrently between baseline and final execution:

1. `test_foundation.Foundation.test_evidence_contacts_scoring_and_deduplication`:
   expected qualification score 30, received 0.
2. `test_hardening.Hardening.test_new_batch_cannot_reset_search_attempt_limit`:
   expected message `Attempt limit`, received `LOCAL_REQUEST_LIMIT_REACHED`.
3. `test_hardening.Hardening.test_router_fallback_only_approved_and_budgeted`:
   expected ProviderLimitReached, received StopRun with `NO_ELIGIBLE_PROVIDER`.
4. `test_search_policy.SearchPolicy.test_brave_monthly_cap_counts_unknown_requests_across_runs`:
   BudgetLimitReached now raised for the Brave rolling allowance.

Focused suite: 142 tests, 140 passed, 2 platform skips, zero failures/errors.
Includes all 17 new discovery tests plus autonomous, options, profiles, broad,
source registry, Exa keyed and plugin tests, including hard spending controls.

Commands (from `recruitme-upgrade`, using the bundled Python runtime):

```text
python -m unittest discover -s tests -v
PYTHONPATH=tests python -m unittest test_discovery test_autonomous test_options test_profiles test_broad test_source_registry test_exa_keyed test_plugins -v
```

Linux signal-timer coverage still needs the worker's Linux environment. No live
search-yield claims are made from these synthetic tests. Source-registry defaults
and its existing approval assumptions were not expanded or independently certified.
The README's older restricted-source description differs from the current registry;
the source-policy owner should reconcile that documentation/configuration.

## Git and integration

Initial branch: `codex/search-engine`, HEAD `7fc4ce0`. All 539 entries accounted for:
320 output artifacts, 94 worker files, 84 dependency-link files, 25 central files,
and 16 other entries. Only three tracked files were modified. Existing worker code
was untracked, so ordinary Git diffs cannot separate it from this task's changes.
No files were cleaned/reset/discarded and no existing work was staged or committed.

Another process switched the shared checkout to `codex/codex/integration-qa` while
this task ran. The search branch is preserved in `worktrees/search-engine-completed`
with a worker source/test/profile snapshot and the change-only patch. Snapshot
dependencies include concurrent changes; only the five files above are owned by
this task. Work remains uncommitted; nothing was merged into development or main.

Integrate the pure helper module together with all caller changes. Keep new evidence
fields unverified; promotion or scoring changes belong to their respective owners.
Resolve the four full-suite integration failures before release.
