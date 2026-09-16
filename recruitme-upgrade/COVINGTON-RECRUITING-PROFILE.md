# Electrical Talent Acquisition Manager — Covington

Prepared from the user's September 10, 2026 posting and refinements. Local profile: `profiles/covington-electrical-talent-acquisition.json`. Status: deployed with an opt-in recruiter-specific planner; authorized AWS run `covington-recruiter-20260910T144957Z` started. See `COVINGTON-SEARCH-LAUNCH-20260910.md` for verified launch, tests and safeguards. The source profile's draft activation metadata is replaced in the immutable active run manifest.

Employer: Electrical Contractor Incorporated. In-person work in Covington, Georgia. Advertised salary up to $70,000; the user clarified that this is somewhat flexible, so $70,000 is a target rather than a firm exclusion ceiling. No higher ceiling is invented. Benefits include 401(k), medical, dental, vision and life insurance, plus paid time off. Immediate start is explicitly confirmed. Relocation assistance is available, with amount and terms unspecified. Routine travel pay remains separate from relocation assistance. Schedule and employment classification were not specified.

Find a skilled-trades recruiting professional who can interview candidates and assess skill-based pay, owns a full recruiting cycle, builds a pipeline, and works with field leadership on manpower planning. Electrical recruiting and commercial electrical knowledge are preferred; broader skilled-trades recruiters remain eligible. Record electrical knowledge and technical-interview gaps rather than automatically excluding them. Include electrical/construction/skilled-trades recruiters, craft recruiters and relevant talent-acquisition or staffing leaders. A manager title is not required. Three years of commercial electrical experience is preferred, not mandatory. Do not invent a degree or license requirement.

Covington is the work location and search center. Search locally in Covington and Metro Atlanta until told otherwise; do not launch a national search or automatically expand geography. A person may currently live anywhere only if their own post or statement explicitly mentions relocating to Metro Atlanta. Preserve that statement's source, excerpt and date; generic willingness to relocate is insufficient. Nearby cities and Metro Atlanta are discovery areas, not proof of a feasible commute. Record actual in-person Covington willingness, relocation timing and commute evidence separately. Relocation intent is not automatically a job-seeking signal; the recent personal job-seeking requirement still applies.

## Evidence and grading

Require both recruiting/industry fit and a credible dated personal job-seeking signal within 30 days for A/B. Record original source URLs, statement excerpts, actual signal dates and retrieval dates separately. Keep unknowns explicit. A recruiter posting "we are hiring electricians" is doing their job; it is not evidence that the recruiter is seeking a new employer. Review contrary availability statements and same-name identity conflicts.

Screen for skilled-trades recruiting, technical interviews, skill/pay assessment, sourcing, pipeline management, field-leadership partnership and measurable hiring results. Prefer electrician/foreman recruiting and commercial electrical understanding. Record salary expectations, Covington commute, earliest start and relocation needs separately; none is established merely by listing a profile in results.

## Proposed discovery and follow-up intent

Examples of the intended local discovery strategy:

- `"skilled trades recruiter" "open to work" "Metro Atlanta"`
- `"construction recruiter" "seeking employment" Atlanta`
- `"electrical recruiter" "looking for a new role" Atlanta`
- `"talent acquisition manager" "electrical construction" Covington`
- `"recruiter" "electricians" "available" Covington`
- `"skilled trades recruiter" "relocating to Atlanta"`
- `"construction recruiter" "moving to Atlanta" "open to work"`

Role-history discovery can find background prospects but cannot establish current job-seeking intent. Candidate follow-ups should anchor the known profile URL, verified employer/history and location, then seek the person's own dated availability statement and recruiting achievements. Do not follow names alone. No candidate outreach is authorized.

## Runtime compatibility and activation

The existing profile validator accepts configurable roles and annual compensation metadata, but validation alone does not make all new requirements operational. A tested `recruiter_profile.py` now handles this profile through opt-in dispatch hooks, bypassing the older electrician planners. It generates recruiter-specific local/Atlanta-relocation queries and source-anchored follow-ups; its screening separates hiring ads from possible personal intent and retains geographical hints for review. All classifications remain provisional until explicit evidence review. `broad_search=false` and empty old follow-up seeds are retained.

Do not run the Doraville or metro electrician launch scripts for this role: they load the old profile and replace active job/configuration state. Use a separately reviewed run manifest and original immutable deadline when a new search is authorized. Preserve the previous electrician profile and all historical result files.

Last verified cumulative search liability: $9.218, including $0.029 unresolved reservations. Previous run: $1.186. No operations occurred after the prior $30 authorization. Existing guards remain $5 default run, $25 maximum session, $100 POC, provider request/money limits, final-$5 high-value restriction and immutable runtime/session deadlines. The last session expired and Exa's cumulative request allowance is exhausted. This profile adds no budget, renews no session and starts no service.
