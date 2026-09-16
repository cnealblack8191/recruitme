# Permanent public source coverage

Registry: `recruitme/source_registry.py`, version 2026-09-10.1.

30 discovery routes: 27 available to the Covington recruiting profile; 24 to field profiles. One route replaces each scheduled discovery query; there is no request fan-out, new provider subscription, budget increase, or automatic next run. A limited run may stop before all routes are attempted. Each route rotates across Exa and Tavily on subsequent cycles. Open-web discovery also covers independent sites.

Routes include LinkedIn, Facebook, Reddit, PostJobFree, Jobcase, Atlanta Craigslist, X, Instagram, Threads, Bluesky, Indeed, Monster, CareerBuilder, ZipRecruiter, Ladders, Resume Library, beBee, About.me, Medium, Substack and WordPress. Recruiter-specific routes add SHRM-Atlanta, Recruiting Brainfood, ERE, Recruiting Daily and iHireHR. Field-specific routes add Roadtechs, ElectricianTalk and ContractorTalk.

These are explicit public-index queries, **not authenticated integrations**. A provider may index little or no usable content on a site. Employer advertisements, articles, community membership and profiles alone do not establish personal job-seeking intent. No private groups, logins, paywalls or candidate database controls are bypassed. LinkedIn Recruiter, Indeed Smart Sourcing, paid resume databases, private Facebook/Slack communities and association member directories remain outside automated access. No accounts, subscriptions or outreach are created.

Optional profile field `source_ids` selects a nonempty subset of registry IDs for the appropriate audience. Unknown IDs fail validation during planning. Without the field, the audience's complete default rotation is used. The Covington profile retains local geography and explicit Atlanta relocation intent, immediate start preference, flexible $70,000 target, and the 30-day personal-signal standard. Source selection does not promote candidates to A/B or change original URLs and dates.

Each completed query records source_family, source_registry_version, source_access, provider and exact filters. JSON reports add `source_plan_coverage` with completed logical queries and returned-page counts. These counts include cache hits and are not paid API counts or proof of authenticated access. Existing `source_coverage` records actual returned domains; compare both before claiming site coverage. Old reports are not rewritten. Pending queries in existing checkpoints are preserved.

Source context: [Jobcase community](https://www.jobcase.com/about-us/), [SHRM-Atlanta resources](https://www.shrmatlanta.org/resources/), [Recruiting Brainfood](https://www.recruitingbrainfood.com/). Association and publishing routes are experimental discovery surfaces, not verified candidate databases.

Deployment uses a tested overlay against the actual AWS code hashes because local files contain unrelated earlier changes. Those differences are preserved; do not deploy the entire local directory blindly. Configuration and the cumulative ledger are unchanged. This patch does not authorize or launch another search.
