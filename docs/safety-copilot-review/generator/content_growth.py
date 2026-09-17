from pdfkit import *

def build():
    s = []
    s += [Kicker("Section 4"), H1("The growth model: $10,000 a month, nationwide", 4)]
    s += [Lead("You set the target at $10,000 a month in recurring revenue, sold nationwide, to contractors who need compliance help and want a stronger safety culture. This section turns that into numbers, a twelve-month ramp, and the product gaps that must close before a stranger in Texas can pay you with a credit card.")]

    s += [H2("4.1 The arithmetic")]
    s += [P("Your README already sets the base price at $149 per company per month. With the three tiers from Section 3 and a realistic mix, the blended price lands near $140. Add-ons (setup, expert questions, annual prepay) push effective revenue per customer toward $150.")]
    s += KV([
        ("Blended monthly price", "About $140 (40% Crew at $79, 45% Company at $149, 15% Pro at $249) plus roughly 7% from add-ons, so about $150 per customer."),
        ("Customers needed for $10,000", "About 67 paying companies."),
        ("Monthly churn assumption", "3% (typical for small-business software with real onboarding). At 67 customers that is two lost a month, so you need two new customers a month just to stand still."),
        ("Visitors to trial", "2% of qualified visitors start a trial (industry range 1.5% to 3% for focused B2B sites)."),
        ("Trial to paid", "30% with a human onboarding call; 15% to 20% without one. The call is worth it at this price."),
        ("Visitors per paying customer", "About 170 qualified visitors, so roughly 11,000 to 12,000 qualified visitors across the first year, or about 950 a month on average."),
    ])
    s += [Callout("What this means", "At a $150 blended price you do not need a viral hit. You need about 1,000 qualified visitors a month, a demo or onboarding call for every trial, and a churn rate you actively manage. Partners and referrals shorten the path because their leads convert at two to three times the rate of cold visitors.", "tip")]

    s += [H2("4.2 A twelve-month ramp that reaches $10,000")]
    s += Tbl(["Months", "Paying customers (end)", "Monthly revenue (end)", "What has to be true"], [
        ["1 to 2", "3 to 5", "$450 to $750", "ECI runs its own program on the product daily. Five pilots signed (three free for 90 days, two paying founding-member price). Payments live. Content published, not drafts."],
        ["3 to 4", "10 to 14", "$1,500 to $2,100", "First case study and video published. Toolbox Talk Tuesday email past 300 subscribers. Two partner agreements (an insurance agency and an IEC chapter)."],
        ["5 to 6", "22 to 28", "$3,300 to $4,200", "SEO pages ranking for long-tail compliance searches. Referral program live. First customers outside Georgia. Onboarding call for every trial."],
        ["7 to 9", "40 to 50", "$6,000 to $7,500", "Paid retargeting turned on at $300 to $500 a month because trial-to-paid is proven above 25%. Second trade pack (HVAC or plumbing). Five partners referring."],
        ["10 to 12", "65 to 75", "$9,750 to $11,250", "Annual plans at 30% of the base. Churn under 3%. A part-time customer success person or a well-tuned onboarding sequence."],
    ], widths=[0.75 * inch, 1.35 * inch, 1.35 * inch, CONTENT_W - 3.45 * inch])
    s += [P("If month six lands below 15 customers, the problem is almost always one of three things: the trial does not reach the 'first talk logged' moment in the first week, the site does not say who the product is for, or the price is being sold as software instead of as a safety department. Fix those before spending on ads.", "small")]

    s += [H2("4.3 Where the 67 customers come from")]
    s += Tbl(["Source", "Share of customers at scale", "Why it works for this product", "Cost"], [
        ["Search and content (SEO)", "35%", "Contractors search at the moment of pain: 'site specific safety plan template electrical', 'OSHA 300A construction 20 employees', 'toolbox talks in Spanish', 'what EMR do GCs require'. Fifty well-built pages compound nationwide for years.", "Time; $0 cash"],
        ["Partners and referrals", "30%", "Insurance agents want lower-EMR clients. Trade associations want member benefits. Safety consultants want a system to put clients on. Each partner brings warm, pre-qualified buyers.", "20% recurring referral fee or one free month per referral"],
        ["LinkedIn and social", "20%", "Owners and GC safety directors live on LinkedIn; foremen and crews on Facebook and Instagram. The bot keeps these fed.", "Under $60 a month in tools"],
        ["Paid retargeting and search", "10%", "Only after trial-to-paid is proven. Retarget site visitors and email subscribers; bid on a short list of exact-match compliance terms.", "$300 to $500 a month from month seven"],
        ["Local events and Georgia network", "5%", "Small in number, large in credibility: logos, testimonials, video, and the IEC and AGC relationships.", "Under $100 a month"],
    ], widths=[1.3 * inch, 0.95 * inch, 3.0 * inch, CONTENT_W - 5.25 * inch])

    s += [H2("4.4 Selling nationwide: what changes state by state")]
    s += [P("A web product can take a customer in any state on day one. Safety rules cannot be treated as identical everywhere, and your README is honest that there are no state-plan rule packs yet. The practical path is to launch nationwide for the 29 states and the District of Columbia where federal OSHA covers private employers, and to label the state-plan jurisdictions clearly as 'federal baseline; state differences not yet covered' until you add packs by demand.")]
    s += Tbl(["Topic", "What varies", "What to do"], [
        ["OSHA state plans", "Twenty-one states plus Puerto Rico run their own private-sector programs (Alaska, Arizona, California, Hawaii, Indiana, Iowa, Kentucky, Maryland, Michigan, Minnesota, Nevada, New Mexico, North Carolina, Oregon, South Carolina, Tennessee, Utah, Vermont, Virginia, Washington, Wyoming). Standards must be at least as effective as federal but often add requirements, notably California, Washington and Oregon.", "Store the customer's state on the company record (you already do). Show a banner and a shorter task set in state-plan states. Add California, North Carolina, Tennessee and Virginia packs first because of contractor density and Southeast adjacency."],
        ["Heat rules", "California, Washington, Oregon, Colorado, Maryland, Minnesota and Nevada already have enforceable heat standards; the federal rule is still pending with an active National Emphasis Program.", "Ship the heat plan template with a state selector. It doubles as a marketing series every May."],
        ["Workers' compensation", "Thresholds differ (Georgia moved to three employees in 2026; Texas is elective; several states require coverage from the first employee).", "Keep a one-page 'state facts' table in the product and on the site, dated and sourced. Do not give legal advice; link to each state board."],
        ["Recordkeeping", "Federal Part 1904 is adopted by state plans with small variations in posting and electronic submission portals.", "The 300A tasks you already schedule are fine nationally; add the state portal link where it differs."],
        ["Sales tax on software", "Several states tax subscriptions (for example Texas, New York, Pennsylvania, Ohio, Washington). Georgia currently does not tax most software as a service.", "Use Stripe Tax or a similar service from day one so nationwide billing does not become a bookkeeping problem later."],
        ["Time zones and language", "Reminder timing and Spanish-speaking crews everywhere in the trades.", "Your company model stores a timezone; make Spanish a first-class toggle for talks, sign-ins and reminders."],
    ], widths=[1.15 * inch, 3.0 * inch, CONTENT_W - 4.15 * inch])
    s += [P("State-plan jurisdictions are listed on OSHA's State Plans page; verify the list and the heat-rule states each quarter as part of the content review.", "small")]

    s += [H2("4.5 Product gaps to close before charging strangers")]
    s += [P("These come straight from the README's 'known boundaries' and from the database you uploaded. They are ordered by how much each one blocks revenue.")]
    s += Tbl(["Gap", "Evidence", "Fix", "Effort"], [
        ["No way to pay", "README: no subscription payments. There is no billing table in the schema.", "Stripe Checkout for signup, Stripe Customer Portal for card changes and cancellations, Stripe Tax for state sales tax, webhooks that set the company tier. Founding-member coupon codes.", "1 to 2 weeks"],
        ["No published content", "54 talks in the database, 0 published. 48 are placeholder slots for a licensed book; 6 are original starter drafts. The three written programs are drafts.", "Either sign the license for the playbook or write and review 26 original talks (six months of weekly talks) before launch, in English and Spanish, with the qualified person's sign-off recorded in the program version history you already have.", "3 to 6 weeks of content work"],
        ["Email is not production-grade", "Setup-Gmail.ps1 configures a Gmail app password as the SMTP sender; the outbox has 60 'simulated' notifications and none sent.", "Move to a transactional provider (Amazon SES since you are already on AWS, or Postmark or Resend). Authenticate the sending domain with SPF, DKIM and DMARC. Keep Gmail for human replies only. Severe-incident alerts should never depend on a consumer mailbox.", "2 to 3 days"],
        ["Urgent alerts have one channel", "README: no SMS. Severe incidents carry 8- and 24-hour federal reporting deadlines.", "Add SMS through a provider such as Twilio for the 'URGENT' alert class only, with the email path as the record.", "2 to 3 days"],
        ["Marketing site and app share a codebase", "PUBLIC_PRELAUNCH mode blocks private routes on a marketing-only deployment.", "Fine for now. Give the marketing site its own hostname and the app another (for example www and app) so analytics, SEO and security headers can differ.", "1 day"],
        ["No offline mode for foremen", "README: no offline mode. Job sites lose signal.", "Reuse the QC field app's pattern: installable web app, queued submissions, retry on reconnect, for the talk sign-in flow first.", "1 to 2 weeks"],
        ["Security readiness items open", "README points to docs/SECURITY-READINESS.md for production MFA enrollment, backups and hosting safeguards.", "Complete them before the first paying customer outside ECI. Publish a short security page on the site; buyers' insurers ask.", "1 week"],
        ["State-plan awareness", "README: no state-plan rule packs.", "Banner and reduced task set for state-plan states as described above.", "2 days"],
    ], widths=[1.15 * inch, 1.9 * inch, 2.75 * inch, CONTENT_W - 5.8 * inch])

    s += [H2("4.6 Sell safety culture, not paperwork: use OSHA's own framework")]
    s += [P("OSHA's Recommended Practices for Safety and Health Programs describe seven core elements. Your product already maps to all seven, which is rare for a tool at this price. Put this table on the website and in every sales conversation; it turns 'compliance software' into 'the operating system for a safety culture' and it is accurate.")]
    s += Tbl(["OSHA core element", "What Safety CoPilot already does", "What to add or emphasise"], [
        ["Management leadership", "Monthly leadership safety meeting task with reminders and a monthly leadership draft for approval.", "A one-page monthly scorecard the owner can forward to the GC or insurer."],
        ["Worker participation", "Talks such as 'Speak up about hazards and near misses'; attendance and individual signatures.", "Anonymous near-miss submission from the sign-in screen; recognition of crews with full participation."],
        ["Hazard identification and assessment", "Daily site inspection task; hazard-driven suggested tasks with explicit applicability review.", "Photo-first inspection on a phone (the QC app pattern) and an AI-drafted job hazard analysis."],
        ["Hazard prevention and control", "Corrective actions with assignment, verification, evidence and reminders.", "Overdue-action escalation to the owner; a 'closed on time' metric."],
        ["Education and training", "Training assignments, credentials with expiry, documentation gaps, toolbox talks.", "Bilingual talks; a training matrix export; orientation module reused from your candidate portal."],
        ["Program evaluation and improvement", "Immutable report snapshots, month-end snapshots, program version histories, annual program reviews.", "A bid-readiness score and trend line; quarterly review call on the Pro tier."],
        ["Communication on multi-employer sites", "ZIP exports with structured data and evidence; PDFs.", "The one-click GC submittal packet; a share link a GC safety director can open without an account."],
    ], widths=[1.5 * inch, 2.6 * inch, CONTENT_W - 4.1 * inch])

    s += [H2("4.7 Ways to grow revenue per customer without raising the price")]
    s += Bullets([
        "**Annual prepay** at ten months for twelve. Cash now, churn later.",
        "**Done-with-you setup** at $499: program customized, roster loaded, first talk run together on a call. Most small contractors will pay for this because it is the part they dread.",
        "**Expert questions** (your tier-three feature) sold as a pack for lower tiers when a customer hits an unusual situation.",
        "**GC edition** in year two: a general contractor pays for visibility into its subcontractors' compliance and invites them onto the platform. This is how you reach many small subs at once and it raises contract value tenfold.",
        "**Insurance loss-control partnerships**: carriers and agencies subsidise or bundle safety programs for policyholders. Start with the agents who write your own policies.",
        "**Referral credit**: one free month for each referred customer who pays for two months.",
    ])
    return s
