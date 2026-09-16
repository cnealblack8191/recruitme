# Recruit Me — product and engineering review brief for Claude

Prepared September 16, 2026 for Charles Black / Electrical Contractor Incorporated (ECI).

## Request to Claude

Please act as an independent product strategist, recruiting-operations adviser, and senior software reviewer. Review the work summarized here and offer candid, practical improvements. Challenge our assumptions. Focus on helping ECI identify useful candidates efficiently, with understandable evidence and controlled costs.

Start by explaining what you believe the product does and its main bottleneck. Then provide:

1. The five highest-impact improvements, ranked by expected benefit, effort, and dependencies.
2. What we should keep, simplify, stop doing, or postpone.
3. A better sourcing and qualification workflow for each of our two recruiting use cases.
4. Specific ways to improve candidate yield without pretending uncertain evidence is verified.
5. Architecture, reliability, security, data-quality, and recruiter-experience issues that deserve attention.
6. A practical next-two-weeks plan with measurable acceptance criteria.
7. The most important unanswered questions for Charles.

Separate observations supported by this brief from hypotheses. Do not assume access to the repository, live application, provider accounts, or linked profiles. If recommending a new provider, distinguish discovery from enrichment, explain the expected incremental value, and identify what must be checked about current access and pricing. Please avoid a generic feature wishlist or an expensive rebuild without evidence it is needed.

## Scope and reliability of this handoff

This is a self-contained synthesis of the local project, implementation reports, and recent project task history. It is not a full source-code archive or a transcript of every conversation. It includes both earlier engineering work and the latest available operational results.

- Local checkout: `codex/codex/integration-qa`, latest commit observed `52b995e` (integration stabilization).
- At preparation time, `recruitme-upgrade/recruitme/plugins.py` and `routing.py` had additional uncommitted changes. Another task was actively working on connections/results. This document is a dated snapshot, not a final freeze of that work.
- Test results below are historical results from the September 13 integration report; this documentation task did not rerun the suites or inspect production directly.
- Older READMEs describe stages that have since changed. In particular, some providers originally described as disabled subsequently returned live results.
- A deployed operational worker, a deployed Central interface, and an integrated local development branch exist. They must not be treated as one identical release.
- Credentials, private candidate contact details, infrastructure identifiers, and raw operational logs are intentionally omitted. This handoff does not authorize outreach, new searches, purchases, or deployment.

## 1. What we are trying to accomplish

Recruit Me is an internal recruiting research and review product for ECI. It discovers potentially suitable people, gathers supporting evidence, separates factual support from inference, and helps staff review and manage candidates. The immediate goal is useful recruiting results, not maximizing the number of search hits.

Charles wants the AWS backend worker to do the search work independently, minimizing Codex/model usage and repetitive monitoring. Recent searches were reported to run without model calls. Provider requests still have their own costs; conversational setup and review still consume assistant usage.

There are two distinct search problems:

| Search | Intended person | Geography and recency |
| --- | --- | --- |
| Experienced electricians | Commercial/industrial electrical field workers; a general qualification policy targets 3–10 relevant years | Metro Atlanta/Doraville; latest operational request used a 30-day personal job-seeking window |
| Electrical recruiter / talent acquisition | Someone with both hands-on electrical experience and recruiting/HR experience, able to help evaluate trade candidates | Originally Covington/Atlanta; latest authorized search expanded to 12 Southeast states and 60-day personal job-seeking evidence |

Historical electrician profiles also included a separate apprentice/helper track, immediate start, up to $35/hour, and no travel pay. Those are saved-profile details, not proof that every later run used them as hard filters. The latest electrician instruction prioritized experienced workers and did not ask us to rework job details.

The Covington talent-acquisition position is in person, with an approximately $70,000 annual target that is somewhat flexible, immediate start, benefits, and relocation assistance with unspecified terms. Earlier recruiter requirements preferred electrical knowledge; later instructions explicitly required electrical field AND recruiting/HR experience. The stricter later requirement governs that dual-experience search.

The expanded Southeast run covered AL, AR, FL, GA, KY, LA, MS, NC, SC, TN, VA, and WV. That discovery scope does not establish willingness to relocate or work in Covington.

## 2. How the product evolved

| Stage | Work completed or recorded |
| --- | --- |
| Candidate Portal foundation | Candidate registration/resume, aptitude assessment, safety lessons and quizzes, progress tracking, administrator results, optional email and resume upload |
| Worker foundation | Python search execution, provider adapters, SQLite evidence persistence, cost reservations, audit trail, resource/runtime limits, checkpointing and reports |
| Reusable searches | Versioned job profiles; saved role, location, compensation, travel and relocation preferences; immutable run manifests |
| September 9–11 | Profile-driven search, intent/follow-up planning, Covington recruiter profile, explicit dual-experience search, public-source registry, deployments and bounded AWS runs recorded in project reports |
| September 12–13 | Additional provider/content adapters, ECI Central interface, staff authentication and password option; four engineering workstreams integrated locally |
| September 13 integration | Search, qualification, dashboard, and security/budget work combined; semantic contract and control defects fixed; remaining release blockers documented |
| September 14–15 operations | Connection troubleshooting, structured-provider request fixes, local recruiter/electrician searches, Southeast recruiter expansion, evidence review and clickable candidate PDFs |
| September 16 | Further connection/results work remained active while this handoff was prepared |

The surrounding Candidate Portal is relevant infrastructure, but a complete automated path from externally sourced lead through application, interview, assessment, and hire has not been demonstrated by the material reviewed.

## 3. Architecture and data flow

```text
Staff member
  -> ECI Central / RecruitMe React interface
  -> authenticated TypeScript server and shared schemas
  -> configured launch / status / stop bridge
  -> AWS-hosted Python worker
  -> governed discovery and selected content providers
  -> SQLite discoveries, evidence, candidates, run links, budgets/audit
  -> allowlisted worker snapshot / reports
  -> recruiter evidence review, workflow status, exports
```

The web stack uses React 19, TypeScript, Vite, Tailwind/Radix UI, Express, tRPC, Zod, and React Query. The surrounding portal uses Drizzle/MySQL and S3-related resume storage. The worker uses Python and SQLite. Central also has single-process file-based state for staff authentication/workflow concerns; these storage systems should not be confused with one shared transactional database.

Central is a separate staff application at `central.ecinc.us`. It can operate separately from the Candidate Portal. Its initial release used timestamped snapshots; bridge launch/status/stop support was subsequently implemented in the local integrated code. Current production bridge behavior and release parity were not freshly verified for this brief.

The intended pipeline is:

1. Select or revise a job profile and create an immutable bounded run.
2. Generate role/location/intent queries and rotate selected sources/providers.
3. Reserve permitted cost before a request, apply limits, and record dispatch.
4. Store search pages and evidence; remove known URL duplicates where possible.
5. Run source-anchored follow-ups on promising packets.
6. Have evidence reviewed before establishing candidate identity and verified claims.
7. Qualify and rank reviewed candidates, associate them with the correct run, and export.
8. Let staff inspect supporting links and manage candidate workflow.

Discovery pages, distinct URLs, name clusters, reviewed people, and qualified candidates are different units. The code and reporting have been tightened to avoid treating them as interchangeable.

## 4. Search and provider work

Implemented capabilities include Georgia-first intent queries, separate date-filtered and undated branches, roughly two-thirds discovery and one-third person-specific follow-up when promising packets exist, filter-aware cache identity, tracking-URL normalization, checkpoints, and per-query provenance. Same-name people are not automatically merged. Cross-page identity resolution remains incomplete.

The source registry documented 30 public discovery routes, with audience-specific subsets. These include professional profiles, public social/community pages, job/resume sites, and trade/recruiting publications. A registry entry is a public-index query route, not a signed-in integration, exhaustive coverage, or proof that useful candidate data was available. Source rotation replaces planned queries rather than creating unlimited fan-out.

| Provider/channel | Most recent evidence reviewed for this brief |
| --- | --- |
| Exa | Standard search, people route, public MCP route, and content-related capabilities appear in the implementation/catalogue. Exa search returned live results after troubleshooting. Earlier provider limits/errors were retained in history. |
| Tavily | Basic search and extraction capabilities; search returned live results. Earlier disabled-status README text is historical. |
| Brave | Search adapter; returned records in the recent multi-provider pass. |
| SerpAPI | Returned records in an earlier pass; later Southeast search stopped its coverage after an error. A working connection on one run does not establish ongoing health. |
| People Data Labs | Earlier live request failed; a subsequent request using simple field filters returned a record. The working approach was reported installed. Complete coverage and ongoing account capacity are not established. |
| Apollo | Responded but returned no matches for the recent tested queries. Zero matches is distinct from connection failure. |
| Bright Data | A delayed profile job completed after the worker stopped waiting; its saved result was retrieved without resubmission. Limited profile data was obtained; automatic delayed-result recovery remained an issue. |
| Coresignal | Local adapter work exists, but latest reviewed operational summary said blocked pending support. Do not treat it as an established working source. |
| WorkSource Atlanta / BlueRecruit | Employer-referral preparation and reviewed, consented import workflow; not automated registrations, messaging, or scraping clients. |

Only-new-result searching is imperfect: supported exclusions and local deduplication can reduce repeats, but cannot guarantee that every billed response contains new people. Completed-query coverage, returned domains, cache hits, paid calls, unique records, and useful candidates should be reported separately.

## 5. Qualification and evidence model

The system deliberately distinguishes `VERIFIED_FACT`, `REASONABLE_INFERENCE`, and `UNKNOWN`. Legacy evidence statuses such as `CLAIMED` and `CORROBORATED` do not automatically establish verification.

Human-reviewed attestations are required for verified claims. An agent cannot simply label its own extraction as human verified. A personal availability statement requires subject attribution and its original date; retrieval, publication metadata, or search-index freshness alone cannot supply that date.

Examples of important negative rules:

- A recruiter saying “we are hiring electricians” does not mean the recruiter wants a new job.
- Working at a staffing company does not by itself prove recruiting experience.
- A job ad, article, layoff mention, relocation, or project completion is not sufficient proof of current personal interest.
- A professional profile URL is a contact route, not verified delivery, consent, or willingness to respond.
- Unresolved contradictory identity or availability evidence blocks full qualification.

The commercial-electrician scoring policy is deterministic and transparent:

| Component | Maximum points |
| --- | ---: |
| Commercial electrical field fit | 25 |
| Relevant experience | 15 |
| Metro Atlanta evidence | 15 |
| Personal job-change interest | 20 |
| Signal freshness | 10 |
| Current professional contact route | 5 |
| Source quality | 10 |
| Total | 100 |

Verified eligible fit evidence earns full points, inference generally half, and unknowns zero. Full qualification additionally requires verified identity and substantive claims, appropriate field fit, 3–10 relevant years, supported local geography, recent attributable positive interest, current contact route, and no unresolved conflicts. Failing a gate caps the final score at 69. Confidence is a separate evidence-support index, not a calibrated hiring probability.

**Important policy mismatch to review:** the general electrician evaluator allows positive signals within 90 days; latest operational requests required 30 days for electricians and 60 days for Southeast recruiters. The original Covington recruiter search also used 30 days. These are distinct policies, not one universal standard. A single profile/run-specific source of truth would reduce confusion.

General qualification classes are `FULLY_QUALIFIED`, `PROVISIONAL`, and `RESEARCH_ONLY`. Historical recruiter A/B/C/D hints are a separate contract. A/B require appropriate fit and recent personal seeking evidence; C/D preserve useful background prospects with different geography/availability gaps. Keyword-based grade hints are not verified grades. Recruiter ranking should not blindly inherit the electrical-trade scoring rubric.

## 6. Recruiter interface and integration improvements

Implemented local work includes editable versioned profiles, run history, conservative spending display, provider/source setup status, candidate search/filtering, evidence dialogs, qualification rationale, safe source links, timestamp/staleness handling, JSON export, and seven persistent workflow stages.

Integration fixed several substantive defects:

- Ordinary electrician discovery was previously filtered through an electrical-plus-HR gate; the integrated exporter removes that inappropriate restriction.
- Snapshot parsing had discarded scores, roles, years, explanations, and evidence/contact links; the schema now preserves validated fields.
- Status refresh could update money while retaining old candidates indefinitely; candidate inclusion and truncation are now explicit.
- Reviewed candidates gain explicit run associations rather than being attributed to arbitrary historical searches.
- Workflow updates persist with administrator authorization, actor audit, and expected-status conflict checks.
- Staff workflow changes cannot promote evidence verification.
- Missing/stale snapshots no longer prevent emergency Stop; launches require stop configuration, and acknowledgements must be real.

Candidate reports with clickable profile links were also produced as PDFs. These are useful review outputs, but their generation does not establish that a complete automated report-download workflow exists in the production UI.

## 7. Actual recent outcomes

These are task-reported results from saved worker output, not a new audit conducted for this document. Costs are recorded run/search amounts, not total infrastructure or account invoices.

| Recent activity | Reported result | Qualification outcome |
| --- | --- | --- |
| Local electrical-recruiter multi-provider work | Four promising dual-experience leads; $0.213 recorded budget use | Availability, compensation, and Covington commute/relocation unconfirmed |
| Metro Atlanta experienced-electrician search | 152 results, 94 new unique records; $0.29 recorded cost | No confirmed A/B candidates with verified personal seeking evidence within 30 days |
| Southeast electrical-recruiter search | 173 new unique search records; $0.27 recorded cost | Five stronger experience matches surfaced, but no verified A/B candidates within the requested 60-day window; SerpAPI coverage incomplete |

The Southeast run had one apparent availability/experience flag that failed review: employment at a staffing company did not establish recruiting experience. This is a concrete example of the gap between keyword matches and useful candidate qualification.

Illustrative recruiter leads from the local work included military electrician/recruiter combinations and an electrical foreman/lead-electrician plus recruiting history. One person's two profiles shared career details but disagreed on current employer. Illustrative electrician leads had credible field experience but lacked a verified recent availability date. Names and profile-level personal information are unnecessary to this product review and are not reproduced here.

**The strongest product hypothesis from these results:** discovery can find relevant work histories cheaply, but reliable, recent personal job-seeking evidence and human verification are limiting qualified yield. This is an inference to test, not proof that more providers or a wider search will solve the problem.

## 8. Cost, security, and operational safeguards

The documented default ceilings are $5 per web run, $25 per session, and $100 for the proof of concept, alongside provider request/money caps and immutable deadlines. Some historical runs had separately authorized allocations; those are not reusable authorization for future runs.

Controls include atomic integer-microdollar reservations before transport, retaining unresolved liability, duplicate-dispatch protection, request limits, provider health stops, price-expiration checks, process locks, runtime/resource guards, checkpoints, and typed stop reasons. Unknown charges remain counted after recovery. Exact-cap spending can dispatch once under a valid reservation; subsequent spending is rejected.

Provider pricing assumptions and verified account allowances need periodic reconciliation. A reserved or estimated cost is not a provider invoice guarantee. Retry behavior must not cause duplicate charges or revive an expired run.

Web controls enforce administrator access. Credential-handling tests cover restricted temporary handling, encrypted handoff, cleanup, and redaction. Central's documented password option uses invitation-based setup, salted scrypt, hashed opaque sessions, secure HTTP-only cookies, expiry, throttling, and logout revocation. There is no public staff enrollment in that design.

The current single-process state architecture is a proof-of-concept limitation. Shared transactional storage, stronger operational monitoring, restore testing, retention/deletion policy, and distributed throttling would need deliberate consideration before broader use. The integration report also notes inconsistent source-policy wording between older documentation and the registry.

## 9. Engineering validation and unresolved issues

Four workstreams were integrated: search engine, candidate scoring, recruiter dashboard, and security/budget controls. Missing search/dashboard delivery commits were recovered before integration; semantic defects were fixed without Git merge conflicts. The September 13 integration did not deploy or change `main`.

Historical combined validation:

| Check | September 13 result |
| --- | --- |
| Python worker, Linux | 256 passed, 1 skipped |
| Python worker, Windows | 252 passed, 5 skipped |
| Full backend | 39 passed, 4 failed, 5 skipped |
| RecruitMe backend subset | 22 passed |
| Frontend suite | 10 passed |
| Desktop/mobile browser component checks | Passed |
| Web and server production builds | Passed |
| TypeScript | 12 existing shared-UI errors |

The four backend failures were blocked by an unavailable database. Type errors were in chart, input-OTP, and component-showcase code. The remaining Linux skip required a deployed systemd environment. Browser checks used a synthetic fixture, not one authenticated live-provider end-to-end transaction. There was no configured lint script. Clean dependency installation remained necessary for reproducibility.

The integrated build was explicitly assessed as **not ready for a real recruiting test** at that checkpoint. Later searches on the operational worker do not prove those integrated-web release gates were cleared.

Other documented limitations:

- Synchronous subprocess control/status execution could delay concurrent Stop handling; an asynchronous implementation and delayed-worker tests were recommended. Closure was not established for this brief.
- There is no complete discovery-to-human-verification product workflow; reviewed imports remain a critical boundary.
- Historical candidate/run attribution is incomplete. A legacy raw report can include database-wide reviewed candidates.
- Cross-run identity consolidation and global ranking are not complete.
- Candidate snapshots can truncate; the UI discloses it and full worker reports may be needed.
- Conservative locality lists are not a complete geocoder or commute model.
- Conflicting evidence can remain blocked without an explicit reviewed resolution workflow.
- Delayed provider jobs and live/local code drift require better lifecycle management.

## 10. Questions where your insights would help most

1. Should recent explicit job-seeking evidence remain a hard gate for all useful leads, or should the product clearly separate “fit prospect” from “active seeker” and offer different human workflows? Preserve truthful labels either way.
2. How should the trade-electrician and dual-experience recruiter policies become independently configurable without duplicating the entire system?
3. What is the smallest useful human-review queue: claim, source excerpt, original date, identity confidence, contradictions, reviewer decision, and audit trail?
4. Which channels are most likely to add incremental recent-intent evidence for these occupations? How would we measure that before purchasing more access?
5. How should query results be evaluated with a small human-labeled benchmark, including recruiter job ads, stale profiles, same-name collisions, and military experience?
6. How should provider selection optimize cost per useful unique person rather than number of returned pages?
7. What UI best communicates zero qualified results while preserving worthwhile prospects and showing exactly what evidence is missing?
8. Which reliability fixes are necessary before the next integrated release, and which scale-related changes can wait?
9. How can the worker finish, persist results, and surface meaningful completion/failure without repeated assistant polling?
10. What would a credible first product-success milestone look like beyond “the search ran”?

Candidate metrics to evaluate: unique reviewed people per run; fit precision among reviewed leads; percentage with valid personal intent/date; reviewer minutes per useful lead; cost per useful person; provider incremental yield; duplicate rate; evidence-age distribution; and run completion/stop reliability. Response, interview, and hire metrics become meaningful only if a separately authorized downstream process actually records them.

## 11. Source map for a deeper follow-up review

The following repository-relative paths identify the underlying work. They are a map for a later source upload, not files Claude can access from this document alone.

| Area | Main files |
| --- | --- |
| Combined engineering findings | `RECRUITME-INTEGRATION-REPORT.md` |
| Earlier frontend handoff | `RECRUITME-FRONTEND-HANDOFF.md` (some gaps superseded by integration) |
| Worker and providers | `recruitme-upgrade/recruitme/{worker,autonomous,discovery,improved_search,routing,connectors,plugins}.py` |
| Search policy and profiles | `recruitme-upgrade/recruitme/{search_policy,search_options,source_registry,profiles,recruiter_profile,dual_experience}.py` |
| Qualification and persistence | `recruitme-upgrade/recruitme/{qualification,data,web_snapshot}.py` |
| Budget/security | `recruitme-upgrade/recruitme/{budget,governors}.py`, `recruitme-upgrade/SECURITY-AUDIT.md` |
| Bridge and snapshot | `recruitme-upgrade/recruitme-worker-bridge.js`, `recruitme-upgrade/export_web_snapshot.py`, launch/status/stop scripts |
| Web contracts/backend | `shared/recruitme.ts`, `shared/recruitmeSources.ts`, `server/recruitme.ts`, `server/recruitmeSnapshot.ts` |
| Recruiter interface | `client/src/pages/RecruitMe.tsx`, `RecruitMeCandidates.tsx`, `RecruitMePanels.tsx`, `recruitme-model.ts` |
| Central and authentication | `central/README.md`, `central/server.ts`, `central/passwordAuth.ts`, `central/client/main.tsx` |
| Profile/coverage rationale | `recruitme-upgrade/COVINGTON-RECRUITING-PROFILE.md`, `DUAL-EXPERIENCE-SEARCH.md`, `SOURCE-COVERAGE.md`, `QUALIFICATION.md` |
| Automated coverage | `recruitme-upgrade/tests/`, `server/recruitme*.test.ts`, `client/src/pages/recruitme.test.tsx`, `central/passwordAuth.test.ts` |

Recent operational context was taken from the project task “Verify connections and check results”; integration context from “Integrate and QA RecruitMe branches.” Completed September 15 results take precedence over older activation notes where explicitly stated. Active September 16 work is not represented as completed.

Please recommend the smallest concrete changes that would help Charles get better recruiting results and confidently understand what the system has actually found.
