from pdfkit import *

SOURCES = [
    ("Regulation and enforcement", [
        ("OSHA, 2026 Annual Adjustments to OSHA Civil Penalties (memo, May 21, 2026)", "https://www.osha.gov/memos/2026-05-21/2026-annual-adjustments-osha-civil-penalties"),
        ("SALUS Safety, OSHA Penalties 2026 (penalty table and small-employer reductions)", "https://www.salussafety.io/us/osha/penalties"),
        ("OSHA, Injury and Illness Recordkeeping FAQs (300A posting and electronic submission)", "https://www.osha.gov/injuryreporting/faqs"),
        ("BasinCheck, 2026 OSHA Deadlines: 300A and ITA filing", "https://basincheck.com/osha-deadlines-2026"),
        ("OSHA, Heat Injury and Illness Prevention rulemaking page", "https://www.osha.gov/heat-exposure/rulemaking/"),
        ("Beveridge & Diamond, OSHA refines heat enforcement while federal rule remains pending (2026)", "https://www.bdlaw.com/publications/osha-refines-heat-enforcement-strategy-while-federal-heat-rule-remains-pending/"),
        ("OSHA, State Plans", "https://www.osha.gov/stateplans"),
        ("OSHA, Recommended Practices for Safety and Health Programs", "https://www.osha.gov/safety-management"),
        ("OSHA, SHARP Frequently Asked Questions", "https://www.osha.gov/sharp/faq"),
        ("Georgia Tech SHES, OSHA 21(d) On-Site Consultation Program", "https://oshainfo.gatech.edu/georgia-tech-safety-health-and-environmental-services/osha-consultation-program/"),
        ("OnPay, Workers' Compensation Insurance for Georgia Employers (3-employee threshold, 2026)", "https://onpay.com/insights/workers-comp-requirements-by-state/georgia/"),
        ("Zorn Insight, Workers' comp cost in Georgia 2026 by industry", "https://www.zorninsight.com/how-much-does-workers-comp-insurance-cost-georgia-2026/"),
    ]),
    ("Injury statistics", [
        ("BLS, Census of Fatal Occupational Injuries Summary, 2024", "https://www.bls.gov/news.release/cfoi.nr0.htm"),
        ("Construction Dive, Construction's deaths and fatality rate declined in 2024", "https://www.constructiondive.com/news/constructions-deaths-fatality-rate-2024-hazards/812666/"),
        ("ESFI, Workplace Injury and Fatality Statistics", "https://www.esfi.org/workplace-safety/workplace-injury-fatality-statistics/"),
    ]),
    ("Prequalification, EMR and GC requirements", [
        ("Billy, Billy vs ISNetworld vs Avetta (subcontractor fees)", "https://billyforinsurance.com/resources/billy-vs-isnetworld-vs-avetta-subcontractor-prequalification/"),
        ("ExpiryEdge, Avetta vs ISNetworld 2026 pricing", "https://expiryedge.com/articles/avetta-vs-isnetworld-comparison/"),
        ("Higginbotham, What is an experience modification rate (EMR)?", "https://www.higginbotham.com/blog/experience-modification-rate/"),
        ("BuildForce, How to improve your EMR for electrical contractors", "https://www.buildforce.com/resource/how-to-improve-your-experience-modification-rate-for-electrical-contractors"),
        ("Power Construction, Subcontractor Site Safety Requirements and Procedures", "https://www.powerconstruction.net/sites/default/files/docs/Sub-Site-Safety-Requirements-11-2019.pdf"),
        ("BigRentz, Creating an Effective Site-Specific Safety Plan", "https://www.bigrentz.com/blog/site-specific-safety-plan"),
    ]),
    ("Competitors and pricing", [
        ("Make Safety Easy, Construction safety software pricing 2026", "https://makesafetyeasy.com/blog/construction-safety-software-pricing-2026"),
        ("Safety Team, SafetyCulture pricing 2026", "https://safetyteamtech.com/blog/safetyculture-pricing"),
        ("BasinCheck, 7 best safety software for small contractors", "https://basincheck.com/resources/best-safety-software-small-contractors"),
        ("Site Safety AI, best construction safety software (LinkedIn roundup)", "https://www.sitesafetyai.com/linkedin/best-construction-safety-software"),
        ("AxionSite, AI JHA and JSA software", "https://axionsite.com/us"),
        ("Westside Construction Group, Turner opens its AI safety tool to the industry (2026)", "https://www.buildwcg.com/blog-posts/turner-construction-safet-coach-ai-safety-tool-industry-2026"),
        ("SafetyPro Resources (name conflict reference)", "https://www.safetyproresources.com/"),
        ("SafetyPro operations platform (name conflict reference)", "https://www.safetypro24.com/"),
    ]),
    ("Marketing and automation tools", [
        ("xAI, Automations in Grok", "https://x.ai/news/grok-automations"),
        ("OpenTweet, Does Grok post to X? (2026)", "https://opentweet.io/blog/does-grok-post-to-x"),
        ("Blotato, X (Twitter) API pricing 2026", "https://www.blotato.com/blog/twitter-api-pricing"),
        ("Buffer, Pricing", "https://buffer.com/pricing"),
        ("Blotato, Buffer pricing 2026: free plan limits", "https://www.blotato.com/blog/buffer-pricing"),
        ("Publer, Plans and pricing", "https://publer.com/plans"),
        ("Metricool, Pricing", "https://metricool.com/pricing/"),
        ("Zapier, The best free email marketing services in 2026", "https://zapier.com/blog/free-email-marketing-software/"),
        ("Digidop, n8n vs Make vs Zapier 2026 comparison", "https://www.digidop.com/blog/n8n-vs-make-vs-zapier"),
        ("OSHA, National Safety Stand-Down to Prevent Falls in Construction", "https://www.osha.gov/stop-falls-stand-down/"),
        ("National Safety Council, Safe + Sound Week (August 10 to 16, 2026)", "https://www.nsc.org/workplace/get-involved/safe-and-sound-week"),
        ("IEC Atlanta and Georgia Chapters, Partner Program", "https://iecatlantaga.org/partners/atlanta/"),
        ("AGC Georgia, Safety Committee", "https://www.agcga.org/safety-committee/"),
    ]),
    ("ECI and project materials", [
        ("Electrical Contractor Inc., company site", "https://electricalcontractorinc.com/"),
        ("ECI training page", "https://electricalcontractorinc.com/training/"),
        ("Repository reviewed: cnealblack8191/safeftypro (commit ef4e164, September 17, 2026)", "https://github.com/cnealblack8191/safeftypro"),
        ("Repository consulted for ECI context: cnealblack8191/recruitme (candidate portal safety module)", "https://github.com/cnealblack8191/recruitme"),
        ("Repository consulted for hosting conventions: cnealblack8191/QC", "https://github.com/cnealblack8191/QC"),
    ]),
]

def build():
    s = [Kicker("Appendix C"), H1("Appendix C. Sources and how far to trust them")]
    s += [P("Figures in this report come from the sources below, checked on September 17, 2026. Government and standards sources (OSHA, BLS, the Federal Register, Georgia agencies) are primary. Pricing figures come from vendors' own pages or 2026 pricing roundups and change without notice; re-check any number before you put it on a web page, and print the date you checked it.")]
    for group, items in SOURCES:
        s += [H3(group)]
        rows = [[name, f"<link href='{url}' color='#1D4ED8'>{url}</link>"] for name, url in items]
        from reportlab.platypus import Paragraph, Table, TableStyle
        data = [[Paragraph(md(n), ST["cell"]), Paragraph(u, ST["cell"])] for n, u in rows]
        t = Table(data, colWidths=[2.9 * inch, CONTENT_W - 2.9 * inch])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, LINE),
                               ("LEFTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        s += [t, Sp(6)]
    s += [H2("Limits of this review")]
    s += Bullets([
        "The live site at safety1.ecinc.us could not be fetched from the environment this review ran in; its network policy blocks that host. Site findings are based on the repository contents that were available, the README, the database schema and seed data, and your description. Anything marked [verify on the live site] should be checked in a browser.",
        "At the time of writing the repository held only the top-level files of the project (16 files). The Django application folders were not present, so page templates, views and static assets were not reviewed line by line.",
        "This is not legal, insurance or OSHA compliance advice. Have the qualified person you name in Section 3 review every regulatory statement before it goes on the site.",
    ])
    return s
