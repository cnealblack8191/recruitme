# RecruitMe — A/B candidate sourcing review

Independent review prepared September 16, 2026 for Charles Black / ECI, in response to
`RecruitMe-Claude-Review-Brief.md`. Scope: the review brief, the worker source in
`recruitme-upgrade/`, the web/Central contracts, and the saved profiles. Basis: reading the
committed source on this branch and running the worker suite (263 tests, 262 passed,
1 Linux-systemd skip). No live provider, AWS, or account state was inspected. Statements
about third-party services are hypotheses to verify before purchase.

---

## 1. What the product does and where it is stuck

RecruitMe is a bounded, auditable research worker that asks public web indexes
(Exa, Tavily, Brave, Google via SerpAPI) for pages where a metro-Atlanta electrician, or a
Southeast electrician-turned-recruiter, personally says they want a new job. It screens
pages with regexes, stores them as unverified packets, and refuses to call anyone an A/B
candidate until a human attests to identity, a positive job-seeking statement, and that
statement's original date within 30 days.

**The bottleneck is not provider count or query volume. It is the target population.**
Metro-Atlanta electricians almost never publish a dated, first-person "I'm looking for
work" statement on the indexed public web. They update an Indeed résumé, mark
"Open to Work" on LinkedIn (visible only to recruiters with paid seats), post in private
Facebook groups, text a foreman, or apply to a job. None of that is reachable by
`site:` queries. Zero verified A/B after three runs is therefore the *correct* output of
the current design, not a defect Codex failed to debug. Adding Brave, SerpAPI, PDL, or
Coresignal to the same strategy will not change it.

The dual-experience recruiter search has the same problem with a smaller population.
"Recruiter" plus "electrician" on the open web returns recruiters *recruiting*
electricians. The people you want are found by career-history filters (past title
electrician, current title recruiter), which is a structured-data query, not a web search,
and the worker currently cannot route to any structured-data provider (Section 3.1).

Everything below follows from that diagnosis.

---

## 2. Where the A/B candidates actually are

A/B by your own definition requires a **dated, attributed, first-party** seeking signal.
These are the channels that produce that signal natively, ranked by expected yield per
dollar for each role. "Discovery" finds people; "enrichment" adds facts about people you
already found. Check the items in the last column before spending money.

### 2.1 Electricians (Doraville / metro Atlanta, 3–10+ years)

| # | Channel | Type | Why it beats web search | Cost model (verify) | Check before use |
|---|---|---|---|---|---|
| 1 | **Inbound applications to a posted job**, routed to the existing Candidate Portal | Discovery, produces A/B directly | An application *is* the attributed, dated, local, positive signal. Verification collapses to "did they apply." | Indeed free/sponsored post; ZipRecruiter plan; Employ Georgia free; Craigslist Atlanta jobs fee; trade-school boards free | Portal intake must capture consent + timestamp (fields already specified in `recruitme-upgrade/EMPLOYER-MATERIALS.md`). Employer name, site, pay floor still missing from the draft ad. |
| 2 | **Indeed Smart Sourcing** (résumé database) | Discovery | Filter: title electrician, 25 mi of Doraville, résumé updated/active in last 30 days. The update date is the candidate's own action. | Subscription; check ECI's Indeed employer plan | Confirm plan includes résumé search; confirm the UI exposes "last updated"; export/TOS limits. Manual review only. |
| 3 | **LinkedIn Recruiter Lite** on ECI's existing account | Discovery | The **Open to Work** filter is the single strongest public-ish signal for this role and is invisible to every index the worker uses. Add geography + current title. | ~monthly seat; verify | Whether an ECI seat exists; Open to Work is recruiter-only visibility; no scraping, manual review with pasted URL + date. |
| 4 | **Employ Georgia** (Georgia DOL) employer résumé search | Discovery | Free for registered Georgia employers. UI claimants must register with Employ Georgia; many post résumés with dates. This is the state's own "recently unemployed, local" list. | Free | Employer registration status; which search filters/dates are exposed. `recruitme/channels.py` already links DOL employer registration but not résumé search. |
| 5 | **ZipRecruiter résumé DB**, **PostJobFree** (direct site search, not `site:`), **Craigslist Atlanta résumés** | Discovery | All three show post dates and are first person. PostJobFree is already in the registry but only via public index; go to its own search. Craigslist résumés section is dated and local. | ZipRecruiter bundled with posting; PostJobFree free; Craigslist free to browse | Craigslist TOS forbids scraping: manual browse + reviewed import only. |
| 6 | **Transitioning military** with separation dates: Hire Heroes USA (HQ Alpharetta, GA), DoD SkillBridge employer program, RecruitMilitary Atlanta fairs, Helmets to Hardhats, GA National Guard employment support | Discovery | Separation date is a hard, dated availability signal. Dobbins ARB is in Marietta; Fort Eisenhower, Fort Stewart, Fort Moore, Robins AFB are in-state. MOS 12R, 12P, Navy CE/EM, AF 3E0X1, USMC 1141 are electricians. | Free / partnership | Program eligibility for a direct employer; lead times. |
| 7 | **Local pipelines**: Construction Ready / CEFGA (Atlanta), IEC Atlanta apprenticeship, ABC Georgia, Gwinnett Tech / Atlanta Tech / Chattahoochee Tech electrical programs, WorkSource Georgia | Discovery (junior track mostly) | Graduation/completion dates are attributable and recent. Placement coordinators want employers. | Free | Direct-employer eligibility; who at ECI owns the relationship. WorkSource is already in `channels.py`. |
| 8 | **Georgia SOS electrical contractor license roster** (Class I/II individuals with city) | Fit-pool discovery, not seekers | The only public, verified list of experienced electricians in metro Atlanta. Perfect "D / fit prospect" pool. | Roster purchase from SOS | Roster format/fields; contact policy (Section 4.2). |

Channels 1–4 alone should produce more verifiable A/B in one week than the web worker has
in three runs, because each record arrives with the signal date attached.

### 2.2 Electrical recruiter / talent acquisition (Covington, dual experience)

| # | Channel | Type | Why | Check |
|---|---|---|---|---|
| 1 | **LinkedIn Recruiter Lite / Recruiter**: past title *electrician* AND current title *recruiter / talent acquisition / HR / workforce development*, geography Southeast, Open to Work | Discovery | This is literally the dual-experience query. Past-title filtering is the feature the worker lacks. | Seat; past-title filter availability on the plan. |
| 2 | **Structured people data** (People Data Labs, Coresignal, Apollo) with `experience.title = electrician` AND `job_title = recruiter…`, `location_region` in Southeast | Discovery | The adapters exist but are unreachable from profile-driven runs (Section 3.1). Fix the routing bug and this becomes a cheap, precise pass. | PDL per-record paid pricing; Coresignal trial in config ended 2026-09-19; Apollo `q_keywords` is weak, needs title/location fields. |
| 3 | **Former military recruiters with electrical MOS**: Army 79R, Navy NC, USMC 8412, AF 8R who were 12R/12P/CE/EM/3E0X1/1141 | Discovery | The brief already observed military combos in results. This is the largest natural population of "hands-on electrician + recruiter." Separation dates give the seeking signal. | Add MOS codes and "military recruiter" to vocabulary; Hire Heroes USA as partner. |
| 4 | **Adjacent titles at electrical contractors and trades staffing firms**: workforce development manager, craft/field recruiter, manpower coordinator, labor coordinator, field HR, training/apprenticeship coordinator, safety-and-workforce | Discovery | Many hold field backgrounds. The dual-experience planner never searches these titles (`dual_experience.py:11-14`). | Vocabulary change only. |
| 5 | **Trade-school instructors and apprenticeship coordinators** (IEC Atlanta, Gwinnett Tech, Construction Ready) | Discovery | Electricians who already evaluate other electricians. Not recruiters by title, but closest real-world match for "can assess a candidate's field skill and pay." | Whether Charles accepts "instructor/coordinator" as satisfying the recruiting/HR half. |

---

## 3. Loopholes and defects in the current code that suppress A/B

These are observations from source, each reproduced with a script during this review.
Line references are to this branch.

### 3.1 Structured-people providers are unreachable from every profile-driven query (high)

`source_registry.apply_route` always writes `options['exclude_domains'] = []`
(`recruitme-upgrade/recruitme/source_registry.py:63`). After `validate_options`, that is a
non-empty dict. `ProviderRouter.search` then calls each plugin's `accepts_options`
(`routing.py:32-33`). Exa People, PDL, Apollo, and Coresignal all declare
`accepts_options = not options` (`plugins.py:58-60`, `:132-133`, `:197-198`, `:222-223`),
so they are skipped for every route the registry produces, including the dual-experience
and Covington recruiter planners, which both call `apply_route`. Forcing `provider=` does
not help because the accepts check still runs.

Reproduced: `apply_route(...)` on the open-web route yields `{'exclude_domains': []}`;
`ExaPeople/PDLFree/ApolloPeople/Coresignal.accepts_options(...)` all return `False`.

Effect: "Apollo returned no matches" and "PDL request failed" in the brief are consistent
with these providers only ever being hit by hand-built test jobs, never by a real run.
The one provider class that answers "past title electrician, current title recruiter" is
dead in production planning.

Fix: drop empty lists before the accepts check (`validate_options` should remove
`exclude_domains: []`), or make the four adapters accept options that contain only empty
lists. Then give the dual-experience planner an explicit structured branch that emits the
JSON filter form PDL already parses (`plugins.py:146-155`).

### 3.2 Three of four electrician discovery branches only reach Exa and Tavily (high)

`discovery.plan` applies a 30/90/180-day `start_date` on branches 0–2
(`discovery.py:48-51`). `Plugin.accepts_options` rejects any dated request
(`plugins.py:43-45`), so Brave and SerpAPI/Google see only the undated branch and
follow-ups. Reproduced: Brave and SerpAPI return `False` for the 30-day options.

Meanwhile Exa's `startPublishedDate` is unreliable for profile pages, so the "recent"
branches skew toward news and job ads. Net: the recency filter mostly removes the pages
you want and routes the rest to the two providers least suited to keyword `site:` work.

Fix: stop using publication-date filters as a recency proxy for people pages. Search
undated on all providers and let the screen record freshness. Keep the dated branch
only for `/posts/` and résumé URLs where the publish date is the statement date.

### 3.3 Verified positive statements are discarded by a narrow regex (high)

`qualification.POSITIVE` (`qualification.py:17-18`) accepts only five phrasings.
Reproduced misses: `#OpenToWork`, `Actively seeking new opportunities`,
`Looking for a new opportunity`, `Available immediately`, `Looking for my next project`,
`Just got laid off, looking`. A reviewer who has confirmed identity, date, and subject on
one of these still gets `job_change = 0`, `RESEARCH_ONLY`, and a score cap of 69.

`NEGATIVE` (`:19-20`) contains bare `no longer`, so "No longer with ABC Electric as of
Friday" (a *positive* availability statement) blocks qualification. Reproduced.

Fix: the reviewer selects a controlled `signal_polarity` (`POSITIVE_SEEKING`,
`NEGATIVE_NOT_SEEKING`, `AMBIGUOUS`) when attesting. Regexes should only propose, never
gate, once a human has attested.

### 3.4 Geography gate rejects half of the saved profile localities (high)

`qualification.METRO` (`qualification.py:13-15`) lacks Chamblee, Brookhaven, Dunwoody,
Johns Creek, Snellville, Loganville, Lithia Springs, McDonough, Monroe, Social Circle,
Cumming, Oxford, and every county name. Reproduced: 16 of the localities in
`profiles/atlanta-electricians.json` and `profiles/covington-dual-experience-search.json`
fail the gate. Chamblee and Brookhaven border Doraville. A verified Chamblee electrician
scores 0/15 on geography and is blocked from `FULLY_QUALIFIED`.

Fix: derive the metro list from the active profile's `locations` plus county names, not a
hard-coded regex in the scorer.

### 3.5 Experience over 10 years is a disqualifier (medium, policy)

`qualification.py:148` blocks `FULLY_QUALIFIED` unless `3 <= years <= 10`. A 14-year
journeyman is capped at 69. The brief says the target is "3–10 relevant years," but the
latest instruction "prioritized experienced workers." Confirm whether the upper bound is a
preference (score) or a gate (block). Recommendation: preference only.

### 3.6 Four different recency rules for the same word "recent" (medium)

- Profiles: 30 days (`profiles/*.json` `maximum_signal_age_days`).
- Commercial scorer: 90 days for `PROVISIONAL`/full credit (`qualification.py:114`).
- Governor A/B gate: 365 days, or 180 without "compelling" evidence (`governors.py:159`).
- Dual-experience planner: 30-day date filter on one query in eight (`dual_experience.py:55-58`).

Make `maximum_signal_age_days` on the run manifest the single source and have scorer and
governor read it.

### 3.7 Follow-up queries embed a URL as a search term (medium, wasted budget)

`dual_experience.py:39`, `recruiter_profile.py:42`, `autonomous.py:165` build queries like
`"Jane Doe" https://linkedin.com/in/janedoe technical interviews…`. Neural and keyword
engines treat the URL as noise. Roughly a third of paid requests go to these. Replace with
the already-built single-URL content adapters (`exa_contents`, `tavily_extract`,
`bright_data`) to fetch the actual profile text and dates, then one name+locality search.

### 3.8 Over-constrained discovery queries (medium)

`discovery.plan` emits `commercial electrician "looking for work" Doraville Georgia
commercial construction` and `… resume … "5 years"` (`discovery.py:41-46`). Four or five
simultaneous constraints on a keyword engine return near-zero; on a neural engine they
return job ads. Simpler queries with the screen doing the filtering will return more
people pages per dollar. Measure with the benchmark in Section 6.

### 3.9 Registry routes that cannot produce the signal (low, budget)

`source_registry.SOURCES` rotates equally through Facebook, Instagram, Threads, X,
Bluesky, Medium, Substack, WordPress, Ladders, About.me, ERE, Recruiting Daily,
Recruiting Brainfood. Public indexes hold essentially no dated, first-person electrician
availability statements from these. Recruiter publications return articles. Remove them
from the default rotation; keep LinkedIn posts, PostJobFree, Jobcase, Indeed, ZipRecruiter,
Roadtechs, ElectricianTalk, Reddit r/electricians, Craigslist, open web.

### 3.10 A/B is unreachable from the product UI (high, product)

`server/recruitme.ts` exposes `setCandidateStatus`, `connectApollo`, `workspace`,
`saveProfile`, `launch`, `stop`, `status`. There is no mutation that creates a reviewed
candidate or attests evidence. The only path to `FULLY_QUALIFIED` is a hand-written
`channel_import` JSON job on the AWS host (`channels.validate_import`,
`data.import_candidate`). Workflow stages in Central explicitly cannot promote verification.
So even if a recruiter finds an A/B person on Indeed today, there is no screen to record
it. This is the largest single reason the dashboards show zero.

### 3.11 Smaller items

- `dual_experience.apply_screen` requires the HR term in the page *header* and the
  electrical term in a chronology line with a year (`dual_experience.py:85-103`). Exa
  returns 4,000 characters (`exa_keyed.py:56`), so long LinkedIn profiles are truncated
  before the Experience section. Raise `maxCharacters` for LinkedIn `/in/` results or fetch
  via the content adapter.
- `autonomous.name_hint` bans the word "available" (`autonomous.py:73`), so a title like
  "Marcus Available Electrician" loses its name hint; harmless but note it.
- `autonomous.screen` treats any PostJobFree résumé URL as `has_signal` but never extracts
  the "Posted" date it displays; that date is the one attributable date those pages offer.
- `governors.record_qualification` accepts `A/B/C/PASSIVE_RESEARCH_POOL/REJECT`;
  `qualification.py` emits `FULLY_QUALIFIED/PROVISIONAL/RESEARCH_ONLY`; the dual screener
  emits `A/B/C/D` hints. Three contracts for one concept. Pick one and map the others.

---

## 4. Product decisions to make

### 4.1 Separate "fit prospect" from "active seeker" (brief question 1)

Yes. Keep A/B strictly as verified seekers with dated signals; that label is trustworthy
and should stay. Add a first-class **Fit Pool** (currently the ad hoc "D" and
"Passive Research Pool") with its own review queue and metrics. Most real electrician hires
in a tight market come from calling a good fit and asking, not from waiting for a post.

### 4.2 Decide the outreach policy explicitly

Every module says `outreach_enabled: False`. That is a research-tool safeguard, not a
recruiting strategy. Recruiting *is* outreach. Decide, in writing, which pools a human at
ECI may contact (for example: any applicant; any Open to Work; any Fit Pool person via
a public professional route only), and log the contact as an event. The system already
records contact routes; it just forbids using them.

### 4.3 Keep, simplify, stop, postpone

- **Keep**: budget ledger and reservations; immutable runs; evidence/attestation model;
  VERIFIED / INFERRED / UNKNOWN; refusal to auto-merge same-name pages; Central auth.
- **Simplify**: one recency rule; one classification contract; profile-derived geography;
  reviewer-selected signal polarity; undated discovery on all providers.
- **Stop**: social/publishing `site:` routes; URL-in-query follow-ups; 30/90/180 publication
  filters as a recency proxy; treating "more providers" as the fix.
- **Postpone**: Coresignal, Bright Data, cross-run identity consolidation, async bridge
  hardening, shared transactional store. None of these change A/B yield this month.

---

## 5. A better workflow for each role

### Electricians
1. Post the experienced opening (Indeed, ZipRecruiter, Employ Georgia, Craigslist Atlanta,
   IEC Atlanta board). Point applications at the Candidate Portal with the voluntary
   intake fields. Each applicant lands as a reviewed import with `availability_signal =
   applied`, `original_date = submission timestamp`, `source_type = first_party`.
2. Daily 20-minute pass: Indeed Smart Sourcing and LinkedIn Recruiter Lite filtered to
   Open to Work / updated ≤30 days within 25 miles of Doraville. Reviewer records URL,
   excerpt, date, polarity in the review form (Section 5.3). These become A/B same day.
3. Weekly: Employ Georgia résumé search; PostJobFree and Craigslist résumés browse.
4. Worker runs become the **Fit Pool feeder**: undated LinkedIn `/in/`, Roadtechs,
   ElectricianTalk, Reddit, plus the SOS license roster import. Score for fit; no seeking
   claim.
5. Monthly: Construction Ready, IEC, tech-college placement contacts for the junior track.

### Electrical recruiter
1. LinkedIn Recruiter Lite: past title electrician + current title recruiter/TA/HR/
   workforce development, Southeast, Open to Work first.
2. Fix Section 3.1 and run PDL/Apollo structured queries for the same career transition.
3. Add military vocabulary (MOS codes, "military recruiter," "career counselor") and
   adjacent titles (Section 2.2 #4) to `dual_experience.ROLES` / `FIELD_ROLES`.
4. Contact Hire Heroes USA (Alpharetta) about placing a transitioning recruiter with an
   electrical MOS; a separation date is a dated availability signal.
5. Accept instructor/apprenticeship-coordinator backgrounds into the Fit Pool for this
   role pending Charles's decision (Section 7).

### 5.3 Smallest useful human-review queue (brief question 3)

One form in Central, one mutation on the server, writing to the existing
`data.import_candidate`:

| Field | Required | Notes |
|---|---|---|
| Source URL | yes | validated with `public_url` |
| Verbatim excerpt | yes | the exact statement |
| Statement date | yes | date the person made it, not retrieval |
| Date basis | yes | enum: `post_timestamp`, `resume_updated`, `application`, `stated_in_text`, `unknown` |
| Signal polarity | yes | enum, replaces regex gating |
| Identity confidence | yes | enum: `confirmed`, `probable`, `namesake_risk` |
| Contradictions checked | yes | checkbox + note |
| Locality (from profile list) | yes | drop-down from active profile |
| Role, years, commercial (y/n) | yes | each with its own source URL/excerpt |
| Reviewer decision | yes | `A`, `B`, `Fit Pool`, `Reject` |
| Reviewer, timestamp | auto | audit |

The server maps this onto the evidence records `import_candidate` already expects, with
`reviewed_by_human = true` and per-evidence `human_verified = true`. No other new storage.

---

## 6. Improving yield without pretending (brief questions 4–6)

- **Build a 60-page labeled benchmark** from existing run output: 20 true positives (dated
  personal statements), 20 hiring ads, 10 stale profiles, 5 same-name collisions,
  5 military. Score every query/provider change against it before spending on runs.
  Metric: labeled-positive pages per dollar and per query, by provider and route.
- **Report per run**: unique person-pages, pages with any signal phrase, pages with an
  *extractable date*, reviewer minutes, cost per page-with-date. "Pages with extractable
  date" is the leading indicator for A/B; it is currently not reported.
- **Provider selection**: run the benchmark queries once through each provider with
  identical undated text and compare cost per labeled positive. Expect Google via SerpAPI
  to win on `site:` résumé boards and Exa on LinkedIn `/in/`; verify rather than assume.
- **Measure a channel before buying it**: for Indeed Smart Sourcing and Recruiter Lite, a
  one-month seat plus a tally sheet (people found, with date ≤30 days, within radius,
  contacted, responded) is the whole evaluation.

---

## 7. Engineering, reliability, security, data quality (brief question 5)

- Section 3 items 3.1–3.4 are correctness defects with tests missing; each is a
  one-file change plus a regression test.
- Snapshot/dashboard: `export_web_snapshot.py` truncates at 20 kB; the UI discloses it.
  Acceptable for now.
- Bridge: synchronous subprocess control noted in the integration report remains open.
  Not a yield issue; fix before a multi-user trial.
- Security posture (credential files, ledger, admin-only tRPC, scrypt sessions) is sound
  for a POC. No secrets found in the reviewed source.
- Data quality: `page_key` dedup is URL-only, so one person's `/in/` and `/posts/` pages
  are separate packets; identity clusters by normalized name are reported honestly as
  unverified. Fine, but the review form (5.3) should let the reviewer link packets to one
  identity key.
- Documentation drift: `recruitme-upgrade/README.md` says the planner excludes LinkedIn,
  Facebook, Reddit, Craigslist, PostJobFree; `improved_search.RESTRICTED` is empty and the
  registry includes them. Reconcile in writing.

---

## 8. Next two weeks (brief question 6)

| Day | Work | Acceptance criterion |
|---|---|---|
| 1 | Decide outreach policy and Fit Pool (Sections 4.1–4.2) | One paragraph signed off by Charles |
| 1–2 | Post experienced electrician opening on Indeed, ZipRecruiter, Employ Georgia; route to Candidate Portal | ≥1 application recorded with timestamp and consent |
| 2–3 | Fix 3.1 (options), 3.3 (polarity enum), 3.4 (profile geography), 3.6 (single recency); add tests | Worker suite green; new tests for each; a synthetic verified "Chamblee, #OpenToWork" candidate reaches `FULLY_QUALIFIED` |
| 3–5 | Reviewer form + server mutation (5.3) writing to `import_candidate` | Recruiter records one real Indeed/LinkedIn find end-to-end in Central and it appears as A/B in the dashboard |
| 4–6 | Stand up Indeed Smart Sourcing or Recruiter Lite (whichever ECI already has) and run the daily pass | Tally sheet: ≥10 people with signal date ≤30 days inside 25 mi |
| 6–8 | Vocabulary update for dual-experience (MOS codes, adjacent titles); PDL structured branch | One PDL/Apollo run returns ≥5 past-electrician/current-recruiter records in the Southeast |
| 8–10 | Prune registry routes (3.9); undated discovery on all providers (3.2); content-adapter follow-ups (3.7) | Cost per page-with-extractable-date improves vs. the September 15 runs on the benchmark |
| 10–12 | Employ Georgia employer registration; Hire Heroes USA and Construction Ready contact | Registration confirmed; two conversations logged |
| 12–14 | Benchmark (Section 6) and per-run yield report | Report shows pages-with-date, reviewer minutes, cost per A/B |

Success milestone that is not "the search ran": **five A/B candidates for the electrician
role, each with a first-party dated signal ≤30 days, recorded through the Central review
form, and at least one recruiter conversation for the Covington role from a structured
past-title query.**

---

## 9. Questions only Charles can answer

1. May ECI staff contact Fit Pool people (no seeking signal) through public professional
   routes? If yes, which routes and with what script?
2. Is 10 years a hard ceiling or a preference for electricians?
3. Does ECI already pay for Indeed employer features, LinkedIn Recruiter Lite, or
   ZipRecruiter? Which accounts, who holds them?
4. Is ECI registered as an employer with Employ Georgia / WorkSource? Is ECI a direct
   employer for BlueRecruit's free tier?
5. For the Covington role, do trade-school instructors or apprenticeship coordinators
   satisfy the "recruiting/HR experience" half, or must the title be recruiter/HR?
6. Is ECI union-signatory (IBEW Local 613 referral) or open shop? This changes the
   electrician channel list.
7. Will you accept a transitioning service member with a separation date 30–90 days out
   as A/B, given the explicit availability date?
8. Who at ECI will do the 20-minute daily review pass, and does the current dashboard need
   to be that person's tool, or is a simple form enough for now?

---

## Appendix — reproduction used for Section 3

```python
from recruitme.search_options import validate_options
from recruitme.source_registry import apply_route
from recruitme.plugins import ExaPeople, PDLFree, ApolloPeople, Coresignal, Brave, SerpAPI
from recruitme.qualification import POSITIVE, METRO, NEGATIVE
plan = apply_route(dict(query='electrician recruiter Georgia', purpose='discovery',
                        target=None, provider='exa_keyed', options={}), 0, 'recruiter')
o = validate_options(plan['options'])            # {'exclude_domains': []}  -> truthy
[c.accepts_options(o) for c in (ExaPeople, PDLFree, ApolloPeople, Coresignal)]  # all False
dated = validate_options({'exclude_domains': [], 'start_date': '2026-08-17', 'end_date': '2026-09-16'})
[c.accepts_options(dated) for c in (Brave, SerpAPI)]                          # all False
bool(POSITIVE.search('#OpenToWork')), bool(POSITIVE.search('Looking for a new opportunity'))  # False, False
bool(NEGATIVE.search('No longer with ABC Electric as of Friday'))              # True
[p for p in ('Chamblee Georgia','Brookhaven Georgia','DeKalb County Georgia') if not METRO.search(p)]  # all three
```
