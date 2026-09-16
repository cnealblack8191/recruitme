# RecruitMe integration and QA — 2026-09-13

**Assessment: integrated and suitable for further controlled validation; not approved for a real recruiting run.** No deployment, live provider request, outreach, push, or change to `main` occurred.

## 1. Branches integrated and recovery provenance

Integration branch: `codex/codex/integration-qa`.

The starting checkout contained modified tracked files and untracked RecruitMe source. Search and dashboard initially pointed to `main` and had no delivery commits. Work was preserved in checkpoint `4b2878c` using an explicit 67-file source manifest. Runtime state, dependencies, generated outputs, credentials/configuration, unrelated Central application files, and historical operations scripts were excluded and retained locally.

| Branch | Delivery | Merge into integration |
| --- | --- | --- |
| `codex/security-budget` | `7cc10f8` | `91e8359` |
| `codex/search-engine` | Recovered `c08b429` | `d06b9ac` |
| `codex/candidate-scoring` | `9fd5456` | `416f615` |
| `codex/dashboard` | Recovered `28dd175` | `4bced9d` |

Search recovery committed only the five search-owned source/test files plus its handoff and patch. Other source files in that worktree were not misattributed to search. Dashboard recovery used `worktrees/dashboard-recovery`, preserving the shared checkout. Each branch's delivered paths matched the checkpoint before merging. The branches depend on the common worker/backend foundation recovered in the integration checkpoint; individual branch checkouts are not standalone release packages.

`main` remained at `7fc4ce0309ee1907a859193e71c113aa6355d7ef`.

## 2. Conflicts and integration fixes

No Git merge conflicts occurred. All four normal `--no-ff` merges used Git's `ort` strategy; no side-selection strategy or history rewrite was used.

Semantic incompatibilities were found and corrected:

- The old exporter admitted only dual electrical/recruiting hints and selected run-name prefixes. Commercial electrical discovery now reaches the dashboard without an HR-experience gate.
- The snapshot schema stripped scores, roles, years, qualification rationale, evidence links, and contact-route links. The allowlisted contract now retains those fields, with score/range and URL validation.
- Status polling previously refreshed only money while preserving old candidate rows indefinitely. The bounded dashboard snapshot now carries candidates, explicitly identifies whether candidates were included, and discloses truncation.
- Reviewed candidates now have an additive run association. Export recomputes qualification and avoids attributing the entire historical candidate database to arbitrary runs. Unassociated legacy candidates are not silently assigned to a search.
- Workflow statuses now persist in the existing single-process staff store through an admin-only mutation, with actor audit and expected-status conflict detection. Recruiter status cannot promote evidence verification.
- A missing/stale snapshot no longer prevents emergency Stop. New launches require a configured stop command. The bridge no longer fabricates successful stop acknowledgements or infers running status from arbitrary text. Active run reporting uses the current launch manifest while the service runs.
- Typed stop reasons survive the worker/autonomous exception boundary and are exported from the termination audit.
- The default profile for an empty store now targets Metro Atlanta commercial electricians. Existing saved profiles are preserved. Numeric experience searches work in the candidate filter.
- Required launch/status/stop scripts were reviewed and brought under source control; no script was executed against a production service.

## 3. Feature and QA coverage

| Area | Result and boundary |
| --- | --- |
| Search/discovery | Planner, discovery, provider adapters, source rotation, and checkpoints pass synthetic tests. No live search-yield claim. |
| Metro Atlanta | Electrical discovery remains local across batches; saved profiles remain authoritative. Qualification requires explicit Georgia/Metro locality evidence. Locality list is conservative, not a complete geocoder. |
| Commercial electrical fit | Electrical field role plus commercial experience required by qualification; generic titles alone do not qualify. |
| 3–10 years | Query rotation covers the range; qualification tests cover boundaries and unsupported tenure. The UI exposes a minimum-years preference; the commercial qualification policy supplies the upper target boundary. |
| Job-change signal/freshness | Original, person-attributed, human-verified signal date required for qualification. Publication/retrieval dates do not become signal dates. Stale, contradictory, negative, missing and future evidence tested. |
| Duplicate handling | Tracking URL variants collapse. Identity-bearing URLs remain distinct. Same-name people are not auto-merged. Reviewed imports are idempotent for stable identity keys. Discovery hints and reviewed identities are not automatically reconciled across different pages. |
| Scoring/ranking | Transparent 0–100 evidence-based policy, conservative caps, fresh reassessment and deterministic ranking pass. Reviewed dashboard rows are ranked within their run; no calibrated hiring probability is claimed. |
| VERIFIED / INFERRED / UNKNOWN | Human attestations are required for verified claims; inference and missing evidence remain explicit. Agent-only evidence cannot spoof verification. |
| Evidence/source tracking | Source URLs, excerpts, observation/provider/query context retained. Dashboard links carry claim labels; raw worker evidence remains in the worker report. |
| Contact routes | Public professional source/profile routes displayed with inference/unverified labels. No guessed contacts, delivery verification, consent inference, or outreach. Email/phone route validation exists in the worker; this dashboard exporter intentionally exposes source/profile links only. |
| Dashboard | Desktop/mobile evidence dialogs, status filtering, search, empty/error states, escaping and safe links tested. |
| Workflow/status | Seven stages persist per candidate/run, with authorization, audit, conflict checks, and refresh/error handling. Same person in another run retains a separate workflow record. |
| Frontend/backend | Shared schema enrichment, status snapshot refresh and persisted workflow tested. Synthetic browser tests exercise the component fixture, not authenticated live AWS control. |
| API/errors | Non-admin access blocked; malformed snapshots fail closed; missing control configuration blocks launch; child-process diagnostics do not leak to browser launch errors. |
| Cost/limits | Reservation accounting, caps, query allocations, duplicate dispatch, runtime, unknown charges and stop reasons tested; details below. |

Synthetic pipeline exercised: reserve a controlled search → consume duplicate provider results → inspect unverified discovery evidence/contact source → explicitly reviewed import → score/rank and export → verify run association → retain unknown cost → reject further spending. Backend tests separately exercise profile creation/launch acknowledgement, candidate synchronization and workflow persistence. Browser checks separately exercise candidate display and interactions. This is component-spanning synthetic coverage, not a single authenticated live-provider end-to-end run.

## 4. Exact automated results

| Check | Result |
| --- | --- |
| Complete Python worker suite, Windows | **257 run: 252 passed, 5 skipped, 0 failed** |
| Complete Python worker suite, local WSL Linux | **257 run: 256 passed, 1 skipped, 0 failed** |
| Complete backend Vitest suite | **48 tests: 39 passed, 4 failed, 5 skipped**; 4 files passed, 1 failed |
| RecruitMe backend subset within that suite | **22 passed, 0 failed** (14 workspace/control, 5 snapshot, 3 credentials) |
| Frontend Vitest suite | **10 passed, 0 failed** |
| Existing headless Edge UI test | **PASS** at 1440×1000 and 390×844: dialog, workflow interaction/filter, experience search, clear filters, Escape, viewport bounds, no page errors |
| Production Vite build | **PASS** |
| Production server esbuild bundle | **PASS** |
| TypeScript `--noEmit --incremental false` | **FAIL: 12 diagnostics**; same shared UI errors seen before stabilization, no RecruitMe diagnostics |
| Prettier, 9 changed TypeScript/TSX files | **PASS** |
| `git diff --check` for stabilization | **PASS** |
| Bridge JavaScript syntax | **PASS** |
| Four Python control/export scripts, AST syntax | **PASS** |
| Lint | **Unavailable**: no lint script or ESLint configuration supplied; formatting is not represented as lint |

The four backend failures are in `server/assessment.test.ts`: unknown-candidate submission, missing-answer submission, coming-soon lesson counting, and disallowed resume file type. Each is blocked by `Database not available`. No tests were weakened or skipped to conceal these failures.

Type diagnostics: 10 in `client/src/components/ui/chart.tsx`, 1 in `client/src/components/ui/input-otp.tsx`, and 1 in `client/src/pages/ComponentShowcase.tsx`. Validation used the already-installed `output/recruitme-validation/node_modules/.bin` tools; module resolution also traverses the existing development dependency tree. A clean lockfile installation remains necessary to establish reproducibility before changing unrelated UI types.

The sole Linux skip is `test_deployed_sandbox`, which requires the installed systemd environment. Local Linux did run signal-timer termination, autonomous checkpointing, competing worker locking and synthetic discovery-to-report tests. No production systemd configuration was changed or assumed verified.

Build warnings: unset analytics variables and a client bundle above 500 kB. Initial sandbox attempts were blocked by Windows temporary-file permissions/esbuild subprocess restrictions; successful reruns used normal local permissions. WSL source validation used a new temporary directory containing only worker source, tests and profiles.

Logs: `output/recovery-20260913/{worker-final,worker-linux,backend-final,frontend-final,typecheck-final,format-final,build-final,server-build-final,browser}.log`. New UI screenshots and harness: `output/recovery-dashboard-preview/`. Existing validation artifacts were retained. The local preview was stopped after checks.

## 5. Security and budget-control results

- $5 web-run, $25 session and $100 POC ceilings remain. Atomic integer-microdollar reservations occur before transport; unknown liability remains counted after reopen.
- The 100-concurrent-attempt test permits exactly four $1.25 reservations against $5. An exact-cap reservation dispatches once; repeat dispatch and further spending are rejected.
- Request ceilings, provider allocations, malformed limits, duplicate-query reservations, frozen/expired configurations, free-provider dispatch auditing, and cumulative limits pass.
- Provider 429 health persists across runs without an automatic retry. Local query exhaustion, budget exhaustion, provider limits, missing routes, runtime expiry and normal completion retain separate reporting.
- Bounded worker deadlines, locks, checkpoint recovery, disk/resource checks and Linux signal termination pass available tests. Deployed service isolation still requires its own check.
- Admin-only access, public URL handling, credential temporary-file cleanup, encrypted credential handoff and browser error redaction pass tests. High-confidence credential-pattern scans of recovery/stabilization source found zero matches; this is not an exhaustive secret audit of unrelated local files.
- No live account balances, current provider billing behavior, source permissions or production credential availability were verified. Pinned prices and fail-closed expiration checks do not constitute an account-level billing guarantee.

## 6. Remaining bugs and technical debt

1. Four database-dependent backend failures and twelve shared UI type errors remain as described above. There is no configured linter.
2. Production bridge calls still use synchronous subprocess execution in the Node server; a slow control/status call can block other API handling until its bounded timeout. Replace this with asynchronous control execution before relying on concurrent emergency controls in a live recruiting trial.
3. Single-process JSON workflow storage is appropriate only for the current POC. It is not a multi-process transactional database. Workflow identity remains scoped to candidate/run.
4. Historical reviewed candidates lack trustworthy run associations. They need explicit reviewed association/import to appear as scored run candidates. No historical attribution was invented.
5. The older `data.report` compatibility output still contains database-wide reviewed candidates; the new dashboard exporter protects run attribution using `candidate_runs`. Consumers of raw legacy reports must not treat every row as discovered by that report's run.
6. No automated discovery-to-human-verification workflow exists. Reviewed import is required to establish verified qualification; source/profile routes do not prove contact delivery or consent.
7. Snapshot size limits can truncate candidate lists; the UI now discloses this. Review the complete worker report for the remainder. Global cross-run ranking/identity consolidation is not supplied.
8. The source registry includes public-index routes that older README language describes as excluded. Source-policy/configuration ownership must reconcile this before real collection. No access permissions were expanded during integration.
9. Existing stored job profiles are preserved, including historical HR/recruiter searches. An operator must select/create the commercial electrical profile for this test; the new default affects an empty store only.
10. Existing handoff documents describe historical snapshots and some superseded gaps. This integration report records the current combined result.

## 7–9. Real-test blockers, readiness and next step

**Not ready for a real recruiting test yet.** The build compiles and synthetic RecruitMe tests pass on both Windows and Linux, but the complete project gates are not green and production control behavior remains unvalidated.

**Exact recommended next step:** keep this integration branch isolated; perform a clean lockfile dependency installation and configure an isolated test database, then resolve the 12 type diagnostics and rerun all web gates. In the same release-blocker pass, make control subprocess execution asynchronous and verify simultaneous status/Stop behavior with a delayed fake worker. Then run the deployed-systemd sandbox check in an explicitly approved test environment and confirm bridge wiring, original budgets/deadlines, source permissions, pinned pricing validity and the commercial-electrical search profile. Do not merge into `main`, deploy, or start a live provider run as part of this recommendation without the separate authorization those steps require.
