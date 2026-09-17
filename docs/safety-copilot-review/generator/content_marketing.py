from pdfkit import *

def build():
    s = []
    s += [Kicker("Section 5"), H1("A marketing engine a bot can run", 5)]
    s += [Lead("The plan below costs under $60 a month in tools until you choose to add paid promotion, runs on every channel you asked for, and needs about twenty minutes of your attention a week once it is set up. It wins Georgia first for proof and credibility while selling nationwide from day one through search, partners and LinkedIn.")]

    s += [H2("5.1 Principles that keep it cheap and effective")]
    s += Numbered([
        "**One weekly content core, many outputs.** Every week the bot produces one toolbox talk, one compliance-calendar note, one field tip and one business tip. Everything else is a repurposing of those four.",
        "**Helpful beats clever.** Contractors follow accounts that save them from a fine or a form. Teach first, sell in the last line.",
        "**Every post points to one free thing.** The free thing collects an email. The email sequence sells the trial. The trial gets an onboarding call.",
        "**Local proof, national reach.** Georgia logos, faces and events on the site; search and partners carry the message to every state.",
        "**Human approval for the first 90 days.** The bot drafts, you approve in one weekly sitting. After 90 days, let the low-risk posts publish automatically and keep approval for anything regulatory.",
        "**Measure leads, not likes.** The weekly number that matters is trials started; the monthly number is paying customers.",
    ])

    s += [H2("5.2 Three budgets, pick one to start")]
    s += Tbl(["Stack", "Monthly cost", "What you get", "When"], [
        ["Zero-cash stack", "$0", "Buffer free plan (3 channels, 10 queued posts each), Meta Business Suite for Facebook and Instagram, LinkedIn native scheduler, Google Business Profile posts, Brevo free email (300 sends a day), Canva free, a spreadsheet CRM, Grok or Claude on the plans you already pay for.", "Pre-launch and month one"],
        ["Recommended stack", "$45 to $60", "Buffer Essentials for 7 channels at $5 each on annual billing ($35), Brevo free, a free CRM tier (HubSpot or similar), Canva free, your existing AI subscription for drafting. X posting goes through Buffer, so no X API fees.", "Launch through month six"],
        ["Scale stack", "$400 to $600", "Recommended stack plus $300 to $500 in retargeting and exact-match search ads, Brevo Starter for automation on a larger list, and a Publora or Buffer API plan if you want the bot to queue posts without you.", "Month seven onward, only after trial-to-paid is proven"],
    ], widths=[1.2 * inch, 0.95 * inch, 3.3 * inch, CONTENT_W - 5.45 * inch])
    s += [P("Prices are the providers' published 2026 rates at the time of writing and are listed in Appendix C. Re-check before you buy.", "small")]

    s += [H2("5.3 Channel map")]
    s += Tbl(["Channel", "Who it reaches", "Cadence", "Format", "Priority"], [
        ["LinkedIn: company page and your personal profile", "Owners, GC safety directors, insurance agents, consultants, nationwide", "3 posts a week; 1 article a month", "Compliance explainers, the weekly talk, customer wins, founder story", "1"],
        ["Facebook: ECIteam page plus a Safety CoPilot page and contractor groups", "Owners and foremen, local first", "4 posts a week", "Field tips with photos, bilingual talk cards, event invites", "1"],
        ["Email: Toolbox Talk Tuesday", "Everyone who took a free tool; the list you own", "Weekly", "One talk in English and Spanish, one compliance date, one product line", "1"],
        ["Website blog and free tools", "Search traffic nationwide at the moment of need", "2 articles a month; tools ongoing", "State pages, template pages, calculators, checklists", "1"],
        ["Google Business Profile", "Local search, credibility", "1 post a week; ask every customer for a review", "Short updates and photos", "1"],
        ["Instagram and Reels", "Foremen and crews, recruiting", "3 posts a week; 1 reel", "Repurposed Facebook content and 30-second clips", "2"],
        ["YouTube: Shorts and long form", "Owners researching; foremen learning", "1 short a week; 1 long video a month", "Product walk-throughs, talk of the week, how to build a GC packet", "2"],
        ["X", "Industry press, OSHA news watchers, safety professionals", "5 posts a week via Buffer", "News commentary, quick tips, links", "3"],
        ["Reddit, contractor Facebook groups, trade forums", "Peers asking for help", "Manual only, when there is a real question to answer", "Helpful replies with no link unless asked", "3"],
        ["Podcasts and trade newsletters", "National trade audiences", "1 pitch a month", "Guest spots on electrical and contractor shows; sponsor a small newsletter", "3"],
    ], widths=[1.6 * inch, 1.55 * inch, 1.05 * inch, 1.85 * inch, CONTENT_W - 6.05 * inch])

    s += [H2("5.4 Content pillars and the weekly rhythm")]
    s += Tbl(["Day", "Pillar", "Example", "Goes to"], [
        ["Monday", "Compliance calendar and news", "'300A must be posted by February 1. Here is the two-minute version for a 25-person electrical shop.'", "LinkedIn, X, Facebook, GBP"],
        ["Tuesday", "Toolbox Talk Tuesday (bilingual)", "'Check the ladder before the climb' as a one-page card in English and Spanish, with three pre-task questions.", "Email, Facebook, Instagram, LinkedIn, YouTube Short"],
        ["Wednesday", "From the field", "A photo from an ECI job with one lesson: 'Why we lock out at the panel, not the breaker you think is right.'", "Instagram, Facebook, LinkedIn, X"],
        ["Thursday", "Bid and insurance smarts", "'What an EMR of 1.12 costs you on a $2M school project, and the three records that bring it down.'", "LinkedIn, email (monthly), blog"],
        ["Friday", "Product in 30 seconds or a customer win", "A screen recording: foreman runs a talk, owner downloads the GC packet.", "YouTube Short, LinkedIn, Facebook, X"],
        ["Monthly", "Long form", "One LinkedIn article and one blog post from the Thursday pillar; one YouTube walk-through.", "LinkedIn, blog, YouTube"],
        ["Seasonal", "Calendar hooks", "300A season (January to March), National Safety Stand-Down (May 4 to 8, 2026), National Electrical Safety Month (May), National Safety Month (June), heat season (May to September), Safe and Sound Week (August 10 to 16, 2026).", "All channels, planned a month ahead"],
    ], widths=[0.8 * inch, 1.55 * inch, 3.1 * inch, CONTENT_W - 5.45 * inch])

    s += [H2("5.5 The engine: how the bot fits together")]
    s += Tbl(["Stage", "What happens", "Tool"], [
        ["1. Sources", "OSHA QuickTakes and news releases, the Federal Register heat docket, ESFI and BLS statistics, your own field photos and customer questions, the compliance calendar.", "RSS and email subscriptions; a shared photo folder"],
        ["2. Draft", "Once a week the bot runs Prompt P2 and produces the week's batch: every post for every channel, Spanish versions, alt text, hashtags, tracking links, and the newsletter, as one document.", "Claude Code Routine, Grok Automations, or a scheduled ChatGPT task (Appendix A)"],
        ["3. Approve", "You read the batch in one sitting, fix anything, and paste approved posts into the scheduler. Twenty minutes.", "Your inbox or the marketing repository"],
        ["4. Publish", "The scheduler posts on the calendar. Facebook and Instagram can also schedule natively for free.", "Buffer (all channels), Meta Business Suite"],
        ["5. Capture", "Every link carries a campaign tag. Free tools collect an email with consent text (your prelaunch lead model already records consent and campaign).", "Website forms, Brevo, CRM"],
        ["6. Nurture", "A five-email sequence sells the trial; the bot drafts replies to comments and questions for you to send.", "Brevo automation; Prompt P6 and P9"],
        ["7. Review", "Monthly, paste the numbers into Prompt P8 and get three decisions: what to do more of, what to stop, what to test.", "Buffer and Brevo exports, Google Analytics or Umami"],
    ], widths=[0.95 * inch, 3.75 * inch, CONTENT_W - 4.7 * inch])
    s += [H3("Which bot, honestly")]
    s += Tbl(["Option", "What it can do", "What it cannot do", "Cost"], [
        ["Claude Code Routine (recommended)", "Runs on a schedule inside a private marketing repository, reads your brand file and calendar, drafts the full weekly batch, commits it for review, and can call a scheduler's API or MCP server when you are ready to remove the manual paste.", "It will not post to a channel unless you give it a scheduler connection; that is a feature during the approval period.", "Included in a Claude subscription"],
        ["Grok Automations", "Scheduled prompts on any Grok tier; email-triggered jobs on SuperGrok. Excellent for a daily 'what did OSHA publish today' digest with live X context.", "Grok does not publish to X on your behalf; its X connector is read-only. Posting still needs Buffer or an API.", "Free; SuperGrok $30 a month for email triggers"],
        ["Scheduled ChatGPT tasks", "Similar weekly drafting and reminders.", "Same posting limitation.", "Included in a paid plan"],
        ["Direct X API", "Programmatic posting at $0.015 per post ($0.20 if the post has a link) on pay-per-use pricing.", "No free tier for new developers; each other network needs its own integration.", "About $5 to $15 a month at this volume"],
        ["Buffer API and MCP server", "Lets the bot queue posts into Buffer directly across all channels.", "Plan-dependent request limits.", "Included with Buffer plans in 2026"],
    ], widths=[1.35 * inch, 2.4 * inch, 1.85 * inch, CONTENT_W - 5.6 * inch])
    s += [Callout("Recommended flow for the first 90 days", "A Claude Code Routine drafts the week every Monday at 6 am and commits a single file to your private marketing repository. You review it over coffee, paste approved posts into Buffer, and send the newsletter from Brevo. A Grok Automation sends you a daily OSHA news digest so the Monday post is always current. After 90 days, connect Buffer's API so approved posts queue themselves.", "do")]

    s += [H2("5.6 Setup, step by step")]
    steps = [
        ("Fix the two security items first", ["Remove `.local-secret` and `db.sqlite3` from the public repository (commands in Section 2), rotate the secret everywhere it was used, and add a pre-commit check so it cannot recur. Marketing drives strangers to your GitHub and your site; both must be clean."], "The repository shows no secrets or databases and the server runs on a new secret.", "1 hour", "Charles"),
        ("Decide the product name and secure the handles", ["Pick the name (Section 3.8 and Section 6). Register the .com, and the same handle on LinkedIn, Facebook, Instagram, YouTube, X and TikTok even if you will not use them all yet."], "One name everywhere; the domain resolves to the marketing site.", "2 hours", "Charles"),
        ("Write the brand file", ["Create `brand.md` in a private marketing repository: audience, voice, the seven positioning sentences, the facts the bot may cite with sources (Prompt P0 contains a starter), the words it may never use, and the visual rules (ECI red and black, photo style, no stock hard-hat clichés)."], "Prompt P0 and brand.md say the same things.", "2 hours", "Charles with the bot"),
        ("Build the free tools that collect emails", ["Publish the OSHA Readiness Checklist for Electrical Contractors (PDF), the Bid-Readiness Score (a five-question form that emails a score), and the Toolbox Talk Tuesday signup. Each gets its own landing page with consent text, and each form writes to Brevo with a campaign tag."], "A test signup appears in Brevo with the right tag and receives the welcome email within a minute.", "1 to 2 days", "Charles or a developer"),
        ("Set up Brevo", ["Create the list, the signup forms, the welcome email, and the five-email nurture automation (Section 5.10). Authenticate your sending domain (SPF, DKIM, DMARC) so mail lands in inboxes."], "Test messages pass an authentication check and arrive in Gmail and Outlook inboxes, not spam.", "Half a day", "Charles"),
        ("Create Meta Business Suite and connect Facebook and Instagram", ["Create the Safety CoPilot Facebook page and Instagram business account; connect both in Business Suite so posts can be scheduled free. Keep the ECIteam page for ECI and cross-post selectively."], "A scheduled test post publishes to both.", "1 hour", "Charles"),
        ("Create the LinkedIn company page and refresh your personal profile", ["Headline: 'Founder, Safety CoPilot. Electrical contractor since 1984. Helping small trade contractors run inspection-ready safety programs.' Add the founder story in About. Turn on Creator mode."], "Company page live with logo, banner and the positioning sentence.", "1 hour", "Charles"),
        ("Claim Google Business Profile and YouTube", ["Claim the profile at the Covington address as a software company with a service area of the United States. Create the YouTube channel and upload the 60-second demo."], "Profile verified; first video live.", "2 hours plus verification wait", "Charles"),
        ("Connect everything to Buffer", ["Connect LinkedIn (page and profile), Facebook, Instagram, Google Business Profile, YouTube and X. Set the posting schedule to the rhythm in Section 5.4 in Eastern time."], "A test post from Buffer appears on every channel.", "1 hour", "Charles"),
        ("Set up tracking", ["Install Google Analytics 4 or the Umami analytics your candidate portal already uses. Adopt one link convention: `?utm_source=linkedin&utm_medium=social&utm_campaign=ttt-2026-w40`. Create a simple dashboard: sessions, signups, trials, paying customers."], "A click from a tagged post shows up in analytics with its source.", "2 hours", "Charles or a developer"),
        ("Create the marketing repository and the weekly Routine", ["Private GitHub repository with `brand.md`, `calendar.md`, `facts.md`, and a `weekly/` folder. Create the Claude Code Routine with Prompt P2 to run every Monday at 6 am Eastern, producing `weekly/2026-wNN.md`. Create the Grok Automation with Prompt P3 for the daily OSHA digest."], "Two consecutive Mondays produce a usable batch without edits to the prompt.", "2 hours", "Charles with the bot"),
        ("Dry run for two weeks before launch", ["Run the full loop with the waitlist audience: draft, approve, publish, measure. Fix what is clumsy. Record the 60-second demo video and three 30-second shorts."], "Two weeks of posts published on schedule; the video library exists.", "2 weeks elapsed", "Charles"),
        ("Recruit the first five partners", ["One insurance agency, the IEC Atlanta and Georgia chapter partner program, one safety consultant, one supply house, one payroll or bookkeeping firm that serves contractors. Use Prompt P10."], "Five conversations held; two agreements signed.", "3 weeks elapsed", "Charles"),
        ("Launch week", ["Announce on every channel the same day; personal LinkedIn post with the founder story; email to your GC, vendor and IEC contacts; Google Business Profile post; a short release to the Covington News and the Atlanta Business Chronicle's people-and-products section; founding-member offer with an end date."], "Launch-week trials counted; onboarding calls booked for each.", "1 week", "Charles"),
        ("Turn on the monthly review", ["First Monday of each month, run Prompt P8 with the exports and act on its three decisions. Kill any channel under 5% of leads after 90 days unless it costs nothing in time."], "A one-page monthly note exists for each month.", "1 hour a month", "Charles"),
    ]
    for i, (title, body, done, effort, who) in enumerate(steps, 1):
        s.append(Step(i, title, body, done=done, effort=effort, who=who))
    s += [Sp(8)]

    s += [H2("5.7 The first 90 days after launch")]
    s += Tbl(["Weeks", "Focus", "Bot output", "Your 20 minutes"], [
        ["-2 to 0", "Waitlist and dry run", "Teasers, founder story, checklist promotion, two weeks of the weekly rhythm", "Approve batches; record the demo video"],
        ["1", "Launch", "Announcement variants for every channel; email to the list; press note", "Personal LinkedIn post; call every trial within 24 hours"],
        ["2 to 4", "Educate", "The weekly rhythm; first LinkedIn article ('What your GC actually checks before mobilization')", "Approve; answer comments; book partner meetings"],
        ["5 to 8", "Prove", "First case study from a pilot; bilingual talk series; EMR explainer video script", "Collect the testimonial and logo; ask for Google reviews"],
        ["9 to 12", "Expand", "State compliance pages for Florida, Alabama, Tennessee and Texas; referral-program posts; retargeting copy if trial-to-paid is above 25%", "Turn on the referral program; decide on paid spend"],
    ], widths=[0.7 * inch, 1.05 * inch, 3.1 * inch, CONTENT_W - 4.85 * inch])

    s += [H2("5.8 Partners and referrals: the cheapest nationwide channel")]
    s += Tbl(["Partner type", "Why they care", "The offer", "How to find them"], [
        ["Insurance agents and brokers", "Lower EMR means better renewals and fewer claims for their book.", "20% recurring referral fee or co-branded checklist; a 'loss control' webinar for their clients.", "Your own agents first; then agencies that advertise contractor workers' comp in each state."],
        ["Trade associations (IEC, ABC, NECA, PHCC, ACCA chapters)", "Member benefits and safety programming.", "Member discount, a free chapter webinar, a sponsored Toolbox Talk Tuesday.", "IEC Atlanta and Georgia partner program first; IEC has chapters nationwide."],
        ["Safety consultants", "A system to put small clients on instead of spreadsheets.", "Reseller margin or referral fee; the Pro tier's quarterly review can be delivered by them.", "LinkedIn search by state; OSHA Outreach trainer directories."],
        ["Supply houses", "Foot traffic and customer loyalty.", "Counter-day demos; a QR card at the counter for the free checklist.", "Your own branches (Mayer, CED, Graybar, City Electric Supply) first."],
        ["Payroll, PEO and bookkeeping firms", "They already sell workers' comp and HR compliance to the same owners.", "Referral fee; bundle with onboarding.", "Local CPA firms and PEO agents who advertise to contractors."],
        ["General contractors' safety directors", "Fewer late submittals from small subs.", "A free GC view of their subs' packets in year two; today, a template pack they can hand to subs.", "ECI's own GCs; AGC Georgia Safety Committee."],
    ], widths=[1.35 * inch, 1.65 * inch, 2.05 * inch, CONTENT_W - 5.05 * inch])

    s += [H2("5.9 Search: the pages that will still bring customers in three years")]
    s += Bullets([
        "**Template and how-to pages** (publish first): site-specific safety plan for electrical contractors; toolbox talk sign-in sheet; competent person letter; OSHA 300A for construction with 20 to 249 employees; heat illness prevention plan template; lockout/tagout program outline; ladder inspection checklist; GC subcontractor safety submittal checklist.",
        "**State pages** (one per state, start with Georgia, Florida, Alabama, Tennessee, Texas, the Carolinas): OSHA jurisdiction, workers' comp threshold, heat rule status, state consultation program link, and a dated 'last reviewed' line. These rank for 'workers comp requirements [state] contractor' and 'OSHA consultation [state]'.",
        "**Comparison pages**: 'Safety CoPilot vs SafetyCulture for small contractors', 'vs SiteDocs', 'vs a spreadsheet'. Honest, with their published prices and the date.",
        "**Free tools**: bid-readiness score, EMR cost calculator, 300A applicability checker. Tools earn links and emails.",
        "**Technical basics**: one H1 per page, descriptive titles under 60 characters, meta descriptions, Open Graph images, a sitemap, schema.org SoftwareApplication and Organization markup, fast images, and a blog that lives on the same domain as the marketing site.",
    ])

    s += [H2("5.10 The free tool and the five emails that sell the trial")]
    s += Tbl(["Email", "Timing", "Subject line", "Content"], [
        ["1. Deliver", "Immediately", "Your OSHA readiness checklist (and the one thing most shops miss)", "The PDF, plus the single most common gap you see, plus a reply-to-me question: 'What did your GC ask you for last?'"],
        ["2. Story", "Day 2", "Why an electrical contractor built a safety department in software", "Founder story, ECI since 1984, the night the paperwork got out of hand. One link to the demo video."],
        ["3. Money", "Day 5", "What one serious citation costs versus a year of Safety CoPilot", "$16,550 versus $79 to $249 a month; EMR and bid thresholds; a customer quote if you have one."],
        ["4. Proof", "Day 8", "A foreman ran Tuesday's talk in Spanish in 4 minutes. Here's how.", "The 60-second video; the GC packet screenshot; invite to a 15-minute call."],
        ["5. Offer", "Day 12", "Founding-member pricing ends [date]", "The guarantee, the price, the end date, one button. Then move them to the weekly Toolbox Talk Tuesday list."],
    ], widths=[0.85 * inch, 0.9 * inch, 2.35 * inch, CONTENT_W - 4.1 * inch])

    s += [H2("5.11 Numbers to watch")]
    s += Tbl(["Cadence", "Metric", "Healthy sign"], [
        ["Weekly", "Posts published as scheduled; new email subscribers; site sessions from tagged links; trials started", "Over 90% of the planned posts went out; subscribers grow every week; at least one trial a week by month three"],
        ["Monthly", "Trials to paid; paying customers; revenue; cost per trial; churn; top three content pieces by clicks", "Trial-to-paid above 25%; churn under 3%; cost per trial under $50 when paid spend starts"],
        ["Quarterly", "Share of customers by source; partner-referred customers; state mix; review count and rating", "Search and partners together above 50% of new customers by quarter four; at least five Google reviews a quarter"],
    ], widths=[0.9 * inch, 3.1 * inch, CONTENT_W - 4.0 * inch])

    s += [H2("5.12 Guardrails for anything the bot writes")]
    s += Bullets([
        "Never say 'OSHA approved', 'OSHA certified' or 'guaranteed compliance'. Say 'aligned to 29 CFR 1926', 'helps you document', 'inspection-ready records'.",
        "Every regulatory number carries a source and a date; the bot must refuse to invent statistics.",
        "No customer names, logos, photos or job details without written permission; no photos of injuries or identifiable workers without consent.",
        "No commentary on politics, lawsuits, or specific companies' OSHA cases beyond what OSHA itself published.",
        "Spanish versions are reviewed by a fluent person before the first 20 go out; after that, spot-check monthly.",
        "Alt text on every image, captions on every video.",
        "Replies to real questions come from a human within one business day; the bot drafts, you send.",
        "Anything the bot cannot source goes to you as a question, not into a post.",
    ])
    return s
