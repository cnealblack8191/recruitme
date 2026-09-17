from pdfkit import *
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.lib import colors as C

def cost_chart():
    """Horizontal bar chart: monthly list price at 40 field workers (single hue, recommendation highlighted)."""
    data = [
        ("Make Safety Easy (safety, $39/user)", 1560),
        ("SiteDocs (~$29/worker)", 1160),
        ("SafetyCulture Premium (~$24/user)", 960),
        ("Raken Basic (~$15/user)", 600),
        ("Safety CoPilot 'Company' tier (flat)", 149),
    ]
    W, H = CONTENT_W, 2.35 * inch
    d = Drawing(W, H)
    left = 2.55 * inch
    bar_h = 0.24 * inch
    gap = 0.13 * inch
    top = H - 0.28 * inch
    maxv = 1600.0
    scale = (W - left - 0.75 * inch) / maxv
    d.add(String(0, H - 0.12 * inch, "Monthly list price for a 40-person field crew (USD)", fontName="Body-Bold", fontSize=8.6, fillColor=INK))
    y = top - bar_h
    for label, v in data:
        highlight = "CoPilot" in label
        d.add(String(left - 6, y + 6, label, fontName="Body", fontSize=8, fillColor=SLATE, textAnchor="end"))
        d.add(Rect(left, y, v * scale, bar_h, fillColor=RED if highlight else C.HexColor("#9CA3AF"), strokeColor=None))
        d.add(String(left + v * scale + 5, y + 6, "$%s" % format(v, ","), fontName="Body-Bold", fontSize=8.3, fillColor=INK))
        y -= bar_h + gap
    d.add(Line(left, y + gap - 2, left, top, strokeColor=LINE, strokeWidth=0.6))
    return d

def build():
    s = []
    s += [Kicker("Section 3"), H1("The business idea, assessed honestly", 3)]
    s += [Lead("Safety CoPilot is a good idea aimed at the right customer at the right time. It is also entering a crowded field. This section sets out why it can win, what could sink it, and how to shape the offer so a small contractor sees it as the obvious choice.")]

    s += [H2("3.1 What the product is, in one paragraph")]
    s += [P("Safety CoPilot (safety1.ecinc.us) is a web application that gives a small specialty contractor the safety department it cannot afford to hire. At launch it should cover the whole compliance loop: a written safety program tailored to the trade, weekly toolbox talks with sign-in, training and certification records with expiry reminders, job hazard analyses and site-specific safety plans, inspections, incident and near-miss reporting, OSHA 300/300A recordkeeping, and a one-click packet of everything a general contractor or insurer asks for. An AI assistant does the drafting, translating and reminding. The company behind it, Electrical Contractor Inc. (ECI), has run commercial electrical crews since 1984 and is its own first customer.")]
    s += [Callout("Working assumption", "Your answer to my question was that, at launch, the product should be a complete process for assisting and promoting safety compliance. Everything below is built on that scope, with the small specialty contractor as the first paying customer. If the launch scope is narrower, start with the toolbox talk plus records core and keep the rest as the roadmap you show on the site.", "tip")]

    s += [H2("3.2 Why the timing is good: the pressures on a 5 to 100 person contractor")]
    s += [P("Small contractors do not buy safety software because they love paperwork. They buy it when a general contractor, an insurer, an inspector, or an injury forces the issue. Several of those forces got stronger in 2026.")]
    s += Tbl(["Pressure", "What is true in 2026", "What it means for the buyer"], [
        ["OSHA penalties", "Maximum $16,550 per serious violation and $165,514 per willful or repeated violation. Amounts carried over from 2025 because the fall 2025 shutdown blocked the inflation adjustment. Penalty reductions for small employers were expanded (70% for 11 to 25 employees; 80% on serious-willful for 20 or fewer).", "One citation can exceed a month of payroll for a small crew. Documented programs and training are exactly what earns the good-faith reductions."],
        ["Georgia workers' comp", "As of January 1, 2026 Georgia requires coverage at 3 or more employees (previously 5), officers count, and fines run up to $2,500 plus $100 per uninsured employee per day. Electrical contractors sit at the high end of construction rates ($3.00 to $8.50 per $100 of payroll).", "Thousands of very small Georgia contractors now carry a policy, an experience modification rate (EMR), and a reason to care about claims history."],
        ["GC prequalification", "ISNetworld runs about $875 per year baseline; Avetta $450 to $900 for basic tiers and $1,200 or more for higher ones. Hiring clients demand written programs, training certificates, EMR letters, 300A logs and site-specific safety plans before mobilization.", "The paperwork burden lands on an office manager with no safety background. A tool that produces the packet is worth real money."],
        ["EMR thresholds", "Many owners and GCs require an EMR at or below 1.00, some at or below 0.90. Above 1.0 can disqualify a bid outright.", "Safety is a bidding issue, not just a compliance issue. The pitch is revenue protection."],
        ["Recordkeeping", "Form 300A must be posted February 1 to April 30 and, for construction establishments with 20 to 249 employees, filed electronically by March 2. Employers with 10 or fewer are exempt from routine logs but must still report fatalities and hospitalizations.", "Seasonal, deadline-driven demand every January to March that your marketing calendar should own."],
        ["Heat rule", "OSHA's heat injury and illness prevention standard (proposed August 2024) is not final, but OSHA says it intends to finalize it and issued a revised Heat National Emphasis Program on April 10, 2026. Proposed triggers: heat index 80°F and 90°F, written plan, acclimatization, breaks, training.", "Southeast contractors need a written heat plan now. This is a ready-made content series and a template feature."],
        ["Injury reality", "1,032 construction and extraction fatalities in 2024 (BLS). Falls remain the largest cause (370). Electrocution is roughly 8% of construction deaths, and electricians are among the top trades for electrical fatalities. Nonfatal electrical injuries with days away rose 59% across 2023 to 2024 versus the prior two years (ESFI).", "The emotional case is real and specific to your trade. Use it carefully and factually."],
    ], widths=[1.15 * inch, 3.05 * inch, CONTENT_W - 4.2 * inch])
    s += [P("Sources for this table are listed in Appendix C (OSHA 2026 penalty memo, Georgia workers' compensation guides, ISNetworld and Avetta pricing guides, OSHA recordkeeping FAQs, the OSHA heat rulemaking page, BLS Census of Fatal Occupational Injuries 2024, and ESFI).", "small")]

    s += [H2("3.3 Who buys, and what makes them buy this week")]
    s += [H3("Ideal customer profile")]
    s += Bullets([
        "**Company:** a specialty trade contractor (NAICS 238) with 5 to 100 field workers. Electrical and low-voltage first, then HVAC, plumbing and fire protection. Georgia and the Southeast first.",
        "**Situation:** bids commercial work through general contractors, carries workers' comp and therefore has an EMR, has no full-time safety manager, and runs the business from a phone as much as a laptop.",
        "**Crews:** Spanish-speaking workers are common. Bilingual talks, quizzes and sign-ins are a feature, not a nice-to-have.",
        "**Not the customer (yet):** one to three person residential outfits (no external pressure), firms above 250 employees (they have safety staff and want Procore or HammerTech integrations), and general contractors (a different product, though they are your best referrers).",
    ])
    s += [H3("Three people inside the account")]
    s += Tbl(["Person", "What they care about", "What the product must do for them"], [
        ["Owner / operator", "Winning bids, insurance cost, not getting the call about an injury, not doing paperwork at 9 pm.", "Show the bid-readiness and EMR story. One dashboard. Flat price. A guarantee."],
        ["Office manager / bookkeeper", "Getting the GC's safety submittal done, chasing expired cards, uploading to ISNetworld or Avetta.", "One-click packet, expiry reminders, a place where every record already lives."],
        ["Working foreman / superintendent", "Running the Tuesday talk in three taps, in Spanish if needed, without a laptop or signal.", "Phone-first, offline-tolerant, QR sign-in, talk of the week ready to go."],
    ], widths=[1.35 * inch, 2.6 * inch, CONTENT_W - 3.95 * inch])
    s += [H3("Buying triggers to build the marketing around")]
    s += Bullets([
        "A GC asks for a site-specific safety plan, OSHA 30 competent person, training records or weekly toolbox talk logs before mobilization.",
        "Registration on ISNetworld, Avetta or a similar hiring-client network.",
        "Insurance renewal, an EMR above 1.0, or a broker asking for a written program.",
        "An injury, a near miss, or a competitor's OSHA fine in the local news.",
        "A hiring wave that needs onboarding and orientation records (your candidate portal already does this for ECI).",
        "Heat season (May to September) and the January to March 300A season.",
        "Public-owner work, especially K-12 school projects, where safety submittals are strict. ECI's 30 years in that market is a credibility asset.",
    ])

    s += [H2("3.4 The competitive landscape and the gap you can own")]
    s += Tbl(["Category", "Examples and price signals (2026)", "Where they fall short for a 5 to 100 person contractor"], [
        ["Enterprise EHS suites", "Procore Safety, KPA, J.J. Keller, Intelex. Quote-based, per-user, modular.", "Too heavy and too expensive. Built for safety departments, not for an owner and a foreman."],
        ["Inspection and checklist apps", "SafetyCulture Premium about $24 per user per month with a free tier. Safesite from about $4 per user with a free tier. 1st Reporting $10 per user.", "Generic and build-it-yourself. No written program, no trade content, no GC packet. Per-user pricing grows with the crew."],
        ["Field reporting tools", "Raken Basic about $15 per user. SiteDocs about $29 to $30 per worker.", "Form-centric. At 40 workers the bill is $600 to $1,200 a month."],
        ["AI point tools", "AxionSite (AI job hazard analyses), Site Safety AI ($29.99 flat, photo hazard scan), OSHA Scan, SafetyBuilder.ai and SmarterRisk (program generators), Turner's SafeT Coach (a free AI safety coach opened to the industry in 2026).", "Each does one job. None is a system of record. The free coaches teach buyers that advice is free; records, workflow and accountability are what they will pay for."],
        ["Safety consultants", "Monthly safety management retainers, typically several hundred to a few thousand dollars a month.", "Trusted humans, but out of reach for most small shops. A partner and referral channel more than a competitor."],
        ["Trade associations", "IEC, ABC, AGC, NECA safety programs and libraries.", "Excellent content, no software and no records. Partner with them."],
    ], widths=[1.25 * inch, 2.75 * inch, CONTENT_W - 4.0 * inch])
    s += [Callout("The gap", "Nobody in this list offers, at a flat company price, an all-in-one system that is trade-specific, bilingual, produces the GC submittal packet in one click, keeps inspection-proof records, and is run every day by the contractor who built it. That combination is the position to take.", "do")]

    s += [H2("3.5 Positioning: the sentence the whole site should say")]
    s += [P("**Safety CoPilot is the safety department for contractors too small to have one.** It drafts your program, runs your toolbox talks, keeps your records inspection-ready, and hands your GC the packet, built and used every day by a Georgia electrical contractor that has been on job sites since 1984.", "quote")]
    s += [P("Category name to use in copy and search: **safety compliance system for small trade contractors**. Avoid 'EHS software' (nobody in this market searches for it) and avoid leading with 'AI' (it invites the free-chatbot comparison). AI is how it works, not what it is.")]
    s += [H3("Proof points you can legitimately use")]
    s += Bullets([
        "Electrical Contractor Inc., est. 1984, Covington, Georgia. Commercial electrical, service department, and more than 30 years of K-12 school projects.",
        "Member of the Independent Electrical Contractors (IEC) with an in-house apprenticeship program taught by ECI's own people.",
        "'Our own crews run their safety program on it' once that is true. Make it true before launch by using it at ECI for at least 30 days.",
        "Aligned to 29 CFR 1926 (construction) and NFPA 70E electrical safe work practices. Say 'aligned to', never 'OSHA approved' or 'OSHA certified'. OSHA does not approve software.",
        "A named qualified person who reviews the content (a CHST, CSP, or OSHA 500-authorized trainer, in-house or fractional). If you do not have one, this is the single most valuable hire or advisor for credibility and liability.",
    ])

    s += [H2("3.6 Offer and pricing recommendation")]
    s += [P("Recommendation: **flat pricing per company, in three tiers by crew size, unlimited crew logins, annual discount, and founding-member pricing for the first 20 customers.** Small contractors dislike per-seat pricing for field workers who log in once a week, and per-seat pricing punishes the very behaviour you want, which is every worker signed in to every talk.")]
    s += Tbl(["Tier", "Crew size", "Price (validate)", "What is included"], [
        ["Crew", "Up to 15 field workers", "$79 per month, or $790 per year", "Trade-specific written safety program, toolbox talk library with a scheduled weekly talk and phone or QR sign-in, training and certification records with expiry reminders, incident and near-miss log, basic inspections, English and Spanish."],
        ["Company", "16 to 50", "$149 per month, or $1,490 per year", "Everything in Crew plus AI job hazard analyses and pre-task plans, site-specific safety plan generator, OSHA 300 log and 300A summary, multi-site, and the one-click GC submittal packet (program, training matrix, toolbox log, 300A, EMR letter and COI slots)."],
        ["Pro", "51 to 100", "$249 per month, or $2,490 per year", "Everything in Company plus a quarterly program review call with a qualified person, prequalification upload support (ISNetworld, Avetta), exports and API, priority support."],
        ["Add-ons", "Any", "$499 one-time; coach credits", "Done-with-you setup (program customized, crews loaded, first talk run together). Human review credits for AI-drafted plans on unusual work."],
    ], widths=[0.8 * inch, 1.05 * inch, 1.35 * inch, CONTENT_W - 3.2 * inch])
    s += [P("The headline value is simple: at 40 field workers the per-user tools cost six to ten times more than the Company tier. Put that comparison on the pricing page with the competitors' own published numbers and the date you checked them.")]
    s += [cost_chart(), Sp(2)]
    s += [P("List prices as published in 2026 pricing guides (SafetyCulture, SiteDocs, Raken, Make Safety Easy). Annual billing and view-only seats can change the real totals; re-check before publishing and cite the date.", "tiny")]
    s += [Sp(6)]
    s += [H3("Free things that feed the funnel")]
    s += Bullets([
        "**Toolbox Talk Tuesday:** a free weekly bilingual talk by email. This is the marketing engine's spine (Section 5).",
        "**OSHA Readiness Checklist for Electrical Contractors** (PDF) and a five-minute **Bid-Readiness Score** on the site.",
        "**Site-specific safety plan starter:** enter a project and get a draft outline. The full generator is the paid feature.",
        "**Guarantee:** 'Inspection-ready records in 30 days or we work with you free until you are.' It is bold, cheap to honor, and nobody else says it.",
    ])

    s += [H2("3.7 Differentiators that actually matter, ranked")]
    s += Numbered([
        "**Contractor-built and contractor-run.** Show ECI crews using it: photos, a 60-second video of a foreman running a talk, the founder's story. Nobody can copy 40 years of job sites.",
        "**Electrical-first depth.** NFPA 70E-aligned safe work practices, lockout/tagout, arc-flash PPE categories, GFCI and assured grounding, aerial lifts and ladders, trenching for underground feeders. Then HVAC, plumbing and low-voltage packs. Generic tools cannot match this and free chatbots will not be trusted for it.",
        "**The GC packet in one click.** The document set GCs, owners and prequalification networks ask for, current and dated. Add a bid-readiness score so the owner sees progress.",
        "**Bilingual by default.** Talks, quizzes, sign-ins and reminders in English and Spanish. In Georgia construction this alone can win the deal.",
        "**Flat price, unlimited crew.** Everyone signs in, so records are complete, so the packet is complete.",
        "**Records that survive an inspection.** Timestamped, signed, versioned, retained. Your candidate portal already stores every quiz attempt with a full audit trail; reuse that pattern. Keep 300 logs five years and training records at least as long as each standard requires.",
        "**A human in the loop.** AI drafts, a qualified person reviews. Offer the quarterly coach call, and refer customers to Georgia Tech's free, confidential OSHA On-Site Consultation program. It costs you nothing and borrows enormous credibility.",
        "**Phone-first and offline-tolerant for foremen.** Your QC field app already solved offline photo queues and installable web apps; reuse it.",
        "**The insurance angle.** Track leading indicators and produce an underwriter packet at renewal. Insurance agents become a referral channel because they want lower-EMR clients.",
    ])

    s += [H2("3.8 Risks and honest concerns, with mitigations")]
    s += Tbl(["Risk", "Why it matters", "Mitigation"], [
        ["Crowded market and free AI coaches", "Turner opened a free AI safety coach to the industry in 2026; SafetyCulture and Safesite have free tiers.", "Compete on the system, the records, the trade depth and local trust, not on chat. Say plainly on the site what the free tools do not do."],
        ["Liability for AI-generated safety content", "A wrong control in a JHA can hurt someone and expose ECI.", "Qualified-person review before anything is marked final; standards citations on every generated document; version history; clear terms of service and disclaimers; errors-and-omissions insurance for the software business; never imitate OSHA Outreach 10/30 cards, partner with authorized trainers instead."],
        ["The name", "'Copilot' is Microsoft's brand and a search black hole; 'SafetyPro' is already used by a consulting firm, an enterprise platform and a machine-safety app.", "Pick a distinctive product name before public launch, keep 'by ECI' as the trust suffix, and check USPTO, domains and app stores first. Section 6 lists candidates."],
        ["Worker data privacy", "Names, dates of birth, training records and injury details are sensitive; OSHA 301 privacy-concern cases have special handling.", "Role-based access, encryption, a written retention policy, a privacy policy on the site, and a promise never to sell data."],
        ["Churn and support load", "Small customers churn when onboarding stalls.", "Templates, a done-with-you setup product, a 30-day activation checklist, annual plans, a monthly customer webinar."],
        ["Founder bandwidth", "ECI is a contractor first; the product competes for your time.", "Automate marketing (Section 4), hire or contract a part-time safety product lead, and keep the roadmap short."],
        ["Regulatory drift", "Penalties, rules and dates change every year.", "Quarterly content review on the calendar; subscribe to OSHA QuickTakes; date-stamp every regulatory statement on the site."],
        ["Domain and brand", "safety1.ecinc.us reads as an internal ECI tool.", "Fine for a pilot. Move to a product domain before selling to other contractors; redirect the old address."],
        ["GC platform lock-in", "Some GCs require Procore or HammerTech for their projects.", "Position as the subcontractor's own system that exports to whatever the GC uses. Build PDF and CSV exports first, integrations later."],
    ], widths=[1.35 * inch, 2.2 * inch, CONTENT_W - 3.55 * inch])

    s += [H2("3.9 What 'stands out and attractive' looks like in practice")]
    s += Bullets([
        "**A five-minute proof.** A free bid-readiness score, or a draft site-specific safety plan for a real project, before anyone talks to sales.",
        "**Show, don't tell.** One 60-second video: a foreman runs a talk in Spanish on a phone, the office manager downloads the GC packet, the owner sees the score go up.",
        "**Local proof.** Georgia contractor logos, the IEC relationship, the school projects, a Newton County address and a real phone number.",
        "**Numbers on the homepage.** '$16,550 per serious citation' next to '$79 a month'. 'ISNetworld costs $875 a year just to register; the packet it asks for is one click here.'",
        "**A named human.** Photo, name and credential of the person who reviews the content and answers the phone.",
        "**Founding-member pricing and the guarantee**, both with an end date.",
    ])

    s += [H2("3.10 Validate before you scale: a 90-day business plan")]
    s += Numbered([
        "**Days 1 to 30:** run ECI's own program on the product end to end. Interview ten electrical and low-voltage contractors (owners and office managers) using the script in Appendix A. Ask what a GC asked them for last month and what it cost them in hours.",
        "**Days 15 to 60:** sign five pilot customers at no charge for 90 days in exchange for weekly feedback, a testimonial and permission to use their logo. Pick two with Spanish-speaking crews.",
        "**Days 30 to 90:** track activation (first toolbox talk logged within 7 days), weekly active foremen, time to first GC packet, pilot-to-paid conversion, and support hours per customer. Convert at least three pilots to founding-member pricing before spending on paid marketing.",
    ])
    s += Tbl(["Metric", "Target at day 90", "Why"], [
        ["Activation (first talk logged within 7 days)", "80% of new accounts", "Predicts retention better than anything else"],
        ["Weekly active foremen per account", "Over 60% of crews", "Records are only complete if crews use it"],
        ["Time to first GC packet", "Under 14 days from signup", "This is the moment the owner sees the value"],
        ["Pilot to paid conversion", "3 of 5", "Proves willingness to pay at your price"],
        ["Support hours per account per month", "Under 1 hour", "Protects your bandwidth"],
    ], widths=[2.6 * inch, 1.6 * inch, CONTENT_W - 4.2 * inch])

    s += [H2("3.11 Questions only you can answer")]
    s += Bullets([
        "Is ECI already running its own safety program on Safety CoPilot every week? If not, when?",
        "Who is the qualified person reviewing the content, and are they willing to be named on the site?",
        "Will the product live under ECI, or under a separate company for liability and future investment? A separate LLC is common and cheap.",
        "What is the product name you actually want, and have you checked it for conflicts?",
        "What is the price you would be comfortable charging a 30-person electrical contractor, and how did you arrive at it?",
        "Do you have Spanish-language content or a translator you trust?",
        "How much of your own time per week can go to this for the next six months?",
    ])
    return s
