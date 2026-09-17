from pdfkit import *

def build_summary():
    s = []
    s += [Kicker("Section 1"), H1("Executive summary", 1)]
    s += [Lead("Safety CoPilot is a well-conceived product aimed at a real and growing need: small trade contractors who must prove a safety program to general contractors, insurers and OSHA without a safety manager. The idea can reach $10,000 a month nationwide. Doing so depends less on new features than on publishing the content, taking payment, saying clearly who the product is for, and running a disciplined, mostly automated marketing loop. Two repository problems need fixing today.")]
    s += [H2("What this report contains")]
    s += Bullets([
        "**Section 2** — the site: two urgent repository fixes, the structure and copy for a marketing site that sells nationwide, sixteen numbered technical and content steps with 'done when' checks, and a launch-readiness checklist.",
        "**Section 3** — the business idea assessed: demand drivers with 2026 figures, the buyer, the competitors and the gap, positioning, a flat three-tier pricing recommendation, differentiators, risks and questions.",
        "**Section 4** — the growth model: the arithmetic of $10,000 a month, a twelve-month ramp, where customers come from, what changes state by state, the product gaps that block revenue, and OSHA's seven-element framework as your safety-culture story.",
        "**Section 5** — the marketing engine: budgets from $0 to $60 a month, a channel map for every channel, the weekly rhythm, the bot architecture, fifteen setup steps, a 90-day calendar, partners, search pages, the email sequence, metrics and guardrails.",
        "**Section 6** — name, brand and domain.",
        "**Section 7** — the 30/60/90 day plan on one page.",
        "**Appendix A** — twelve paste-ready prompts and the setup steps for a Claude Code Routine, Grok Automations and Buffer. **Appendix B** — 26 toolbox talk topics to publish first, with Spanish titles and the standard each rests on. **Appendix C** — sources.",
    ])
    s += [H2("The ten things to do first")]
    s += Numbered([
        "**Today:** remove `.local-secret` and `db.sqlite3` from the public repository, rotate the secret, change the three passwords, and make the repository private (Section 2.2).",
        "**Today:** push the complete source from the command line so the application can be reviewed and tested on every commit.",
        "**This week:** decide the product name and register the domain and handles (Section 6). Everything downstream carries the name.",
        "**Weeks 1 to 6:** publish the content. Zero of 54 talks and zero of three programs are published; a trial that opens to an empty library ends. Twenty-six reviewed talks in English and Spanish and three finished programs, signed off by a named qualified person.",
        "**Weeks 1 to 3:** take payment (Stripe with tax handling), move email to a transactional provider with domain authentication, and add SMS for urgent incident alerts (Section 4.5).",
        "**Weeks 2 to 4:** rebuild the marketing site around 'the safety department for contractors too small to have one': home, pricing, trades, free tools, about, security and legal pages (Sections 2.4 and 2.5).",
        "**Weeks 1 to 8:** run ECI's own safety program on the product every week and sign five pilot contractors, two with Spanish-speaking crews (Section 3.10).",
        "**Weeks 2 to 4:** stand up the marketing engine (brand file, Routine, Buffer, Brevo, free tools) and dry-run it for two weeks (Section 5.6).",
        "**Weeks 5 to 6:** launch with founding-member pricing and the 30-day guarantee, announce on every channel the same day, and open the first five partner conversations (Sections 5.7 and 5.8).",
        "**Month 3 onward:** monthly review with Prompt P8, add state pages, and turn on paid retargeting only when trial-to-paid exceeds 25% (Section 4.2).",
    ])
    s += [Callout("The one number to manage", "About 67 paying companies at a blended $150 a month is $10,000. That needs roughly 1,000 qualified visitors a month, an onboarding call for every trial, and churn held under 3%. Partners and search make the visitors cheap; content and onboarding make the trials convert.", "do")]
    return s

def build_plan():
    s = []
    s += [Kicker("Section 7"), H1("The 30/60/90 day plan", 7)]
    s += [Lead("One page to pin above the desk. Each cell is a deliverable, not an activity.")]
    s += Tbl(["Track", "Days 1 to 30", "Days 31 to 60", "Days 61 to 90"], [
        ["Repository and security", "Secrets removed and rotated; repository private and complete; CI running tests and deploy check", "Pre-commit secret scanning; backup restore drill documented", "Quarterly security review scheduled; security page live"],
        ["Product", "Stripe billing; transactional email with SPF, DKIM, DMARC; SMS for urgent alerts; onboarding checklist; state banner", "GC packet PDF; bid-readiness score; Spanish sign-in and reminders; cert expiry to employees", "Photo-first inspection with offline queue; GC share link; data export and deletion"],
        ["Content", "12 talks and 3 programs finished and signed off; Spanish review process set", "26 talks published; heat plan template; first trade pack (electrical) complete", "HVAC or plumbing pack drafted; quarterly content review on the calendar"],
        ["Site", "Name chosen; domain and hostnames split; home, pricing, free tools, about, legal live; analytics and events firing", "Trade pages; five state pages; first two blog articles; comparison pages", "Ten state pages; testimonial and video on home; Lighthouse and accessibility targets met"],
        ["Marketing", "Brand file, calendar, Routine, Grok digest, Buffer, Brevo set up; two-week dry run; five partner outreach emails", "Launch week executed; founding-member offer live; Toolbox Talk Tuesday weekly; two partners signed", "First case study; referral program; monthly review run twice; paid retargeting decision made"],
        ["Business", "ECI running its program weekly; ten discovery interviews; five pilots signed", "Three pilots converted to paying; qualified reviewer named on the site; pricing validated", "15 to 25 paying customers; churn and activation measured; first customer outside Georgia"],
    ], widths=[1.1 * inch, 1.85 * inch, 1.85 * inch, CONTENT_W - 4.8 * inch])
    s += [P("If a cell slips, slip the marketing cells too: promoting a product that cannot take payment or open to a full library wastes the launch.", "small")]
    return s
