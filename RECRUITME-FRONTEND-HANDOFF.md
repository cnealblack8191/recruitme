# RecruitMe frontend integration

The task started on `codex/dashboard`. The shared checkout was externally changed to `codex/codex/integration-qa` during validation. This frontend task performed no branch switch, merge, reset, or backend edit. Changes remain in the shared working tree and existing local work was retained.

## Experience delivered

- Recruiting overview now prioritizes synchronized candidates, unverified evidence, search history, and recorded spend, with direct review actions.
- Candidate workspace supports all seven workflow stages, stage counts/filtering, name/role/location/experience search, discovery-run filtering, and clear filters.
- Candidate dialogs show role, location, experience years, supplied score and grade, confidence, verification, qualification rationale, electrical/construction evidence, recruiting context, original job-change signal and freshness, sources, contacts, and run-level spending/budget/reservations.
- Missing data remains explicit. Grade is never converted into a numeric score or confidence. Verification and recruiter workflow status are separate.
- Responsive layout, keyboard dialog handling, focus indicators, loading/error/empty states, safe external links, and session-only workflow disclosure.

## Backend contracts to connect

The existing `recruitme.workspace` query and profile, launch, stop, source setup, credit, and report interfaces remain in use. No changes were made to the search/scoring engines or budget/security implementation.

`client/src/pages/recruitme-model.ts` defines an optional frontend `Candidate` extension of the existing tRPC candidate record:

| Field | Expected value |
| --- | --- |
| `currentRole` | Current/most recent role, string or null |
| `yearsExperience` | Reported experience years, number or null |
| `qualificationScore` | Supplied numeric score or null; scale must be agreed with scoring agent |
| `confidence` | Backend confidence label or null |
| `qualificationReason` | Evidence-grounded summary or null; classification is the current fallback |
| `status` | New, Review, Qualified, Contacted, Interview, Rejected, or Hired |
| `evidenceLinks` | Array of `{ label, url }` |
| `contactRoutes` | Array of `{ label, url }`; HTTP(S), mailto, and tel are supported |

The snapshot parser currently strips unsupported fields. The integration agent must extend the backend schema and producer before enrichment can reach this UI. These are optional presentation fields, not an alternative scoring system.

`RecruitMeCandidates` accepts controlled `statuses` and `onStatusChange(key, status)` props. Current state lives in `RecruitMe.tsx` for the mounted workspace session and survives navigation between sections, but resets on reload. Connect an authenticated status mutation with pending/error handling and query reconciliation for durable shared workflows. The temporary key is the JSON-encoded `[runId, candidateId]` pair; agree on a canonical identity across runs before persistence. Session overrides are deliberately excluded from the backend evidence-report export.

Run evidence joins existing `candidate.runId` to `workspace.runs[].id`. Costs are explicitly run-level; reservations are included in committed spend. A job-profile/run association is not currently supplied; connect it for a human-readable discovery profile label.

## Validation

- `pnpm test:frontend`: 10 new tests pass (executed using the existing `output/recruitme-validation/node_modules/.bin/vitest.cmd` binary).
- Existing `vitest run`: 33 pass, 4 fail, 5 skipped. All 16 RecruitMe backend tests pass. Four unrelated assessment tests fail because the database is unavailable.
- Production Vite build and server esbuild bundle pass. Outputs were directed to `output/recruitme-dashboard-build` to preserve existing build artifacts. Existing warnings: unset analytics variables and bundle size above 500 kB.
- `tsc --noEmit --incremental false`: fails with 12 errors in existing `components/ui/chart.tsx`, `components/ui/input-otp.tsx`, and `pages/ComponentShowcase.tsx`; no RecruitMe diagnostics.
- Prettier check passes for edited frontend files/config. No lint script or ESLint configuration is provided by this project.
- Headless Edge checks pass at 1440×1000 and 390×844: open evidence dialog, update status, filter by status, search experience, clear filters, Escape close, no page overflow, dialog inside viewport, no browser page errors.
- Synthetic browser fixture, test script, and inspected screenshots are under `output/recruitme-dashboard-preview`; these are validation artifacts, not production candidate data. Run the preview with Vite using that directory's config and execute `check.cjs` with the bundled Playwright package available.

## Remaining limits

Workflow persistence, missing candidate enrichment, score-scale labeling, and named discovery-profile association require integration. Visual/interaction validation used synthetic data; authenticated live end-to-end validation still requires a working workspace/backend. The page retains the existing 20-second workspace refresh. No outreach is sent by this UI.

