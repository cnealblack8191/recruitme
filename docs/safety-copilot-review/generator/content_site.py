from pdfkit import *

PUSH = """# In PowerShell, inside C:\\Users\\CharlesNBlack\\Documents\\ChatGPT\\SafetyCoPilot
git init
git add .
git commit -m "Full SafetyCoPilot source"
git remote add origin https://github.com/cnealblack8191/safeftypro.git
#   (if git says origin already exists: git remote set-url origin <that URL>)
git push -u origin main --force
#   --force is safe here because GitHub holds only the partial web upload.
#   Then: GitHub > Settings > General > Danger Zone > Change visibility > Private"""

CLEANUP = """# Run inside the SafetyCoPilot folder on your PC, after the full source is pushed.
# 1) Stop tracking the two files (they stay on your disk, leave GitHub).
git rm --cached .local-secret db.sqlite3
git commit -m "Remove local secret and development database from the repository"
git push

# 2) Remove them from history so the old commit no longer serves them.
#    Easiest: on GitHub, Settings > Danger Zone > delete the repository, create it again
#    (private this time), and push a fresh history:
git checkout --orphan clean
git add .
git commit -m "SafetyCoPilot source"
git branch -D main
git branch -m main
git push -u origin main --force

# 3) Rotate: generate a new local secret and a new server secret.
python -c "import secrets; print(secrets.token_urlsafe(64))"
#    Put the new value in .local-secret locally and in the server's environment
#    (DJANGO_SECRET_KEY), restart the web and worker services, and expect every user to
#    sign in again. Change the three account passwords that were in db.sqlite3.

# 4) Stop it happening again: install a secret scanner as a pre-commit hook.
pip install pre-commit detect-secrets
detect-secrets scan > .secrets.baseline
#    then add detect-secrets to .pre-commit-config.yaml and run: pre-commit install"""

def build():
    s = []
    s += [Kicker("Section 2"), H1("The site: what to fix, in order", 2)]
    s += [Lead("This section is the step-by-step improvement guide for safety1.ecinc.us. It starts with two urgent repository fixes, then rebuilds the marketing site around the positioning in Section 3, then hardens the Django application for strangers, then closes with a launch checklist. Steps are numbered in the order to do them.")]

    s += [H2("2.1 What was reviewed and how")]
    s += Bullets([
        "The public repository cnealblack8191/safeftypro at commit ef4e164 (16 top-level files uploaded through the GitHub web page: README, environment example, Dockerfile, requirements, launch scripts, and the development database).",
        "The database schema and seed content (45 tables, 9 requirement rules, 54 toolbox talk records, 3 program worksheets, 60 queued notifications, 2 demo companies, 3 user accounts). No personal data was read or copied.",
        "Your candidate portal (hire.ecinc.us) and QC field app repositories for ECI's brand, hosting conventions (Apache TLS proxy, PM2 or systemd, Let's Encrypt, Bluehost DNS, AWS) and reusable patterns (offline photo queue, immutable audit trail).",
        "**Not reviewed:** the live pages. The environment this review ran in blocks safety1.ecinc.us and ecinc.us, and the application folders (templates, views, static files) were not in the repository at the time of writing. Findings that depend on them are marked [verify on the live site].",
    ])

    s += [H2("2.2 Two fixes to make today")]
    s += [Step(1, "Remove the secret and the database from the public repository, then rotate", [
        "The upload placed `.local-secret` (an 86-character random token) and `db.sqlite3` (3 user accounts with password hashes, 3 active sessions, company and notification data) on a public GitHub page. Both are listed in `.gitignore`; the web uploader ignores that file. Treat the secret as compromised even if it was only ever used for local preview, because Django signs sessions and password-reset links with it.",
        PromptBlock("Cleanup commands", CLEANUP)[0],
    ], done="GitHub shows neither file in any commit; the server runs on a new secret; the three passwords are changed.", effort="1 hour", who="Charles")]
    s += [Step(2, "Push the complete source and make the repository private", [
        "Only the top level of the project reached GitHub. Push from the command line so `config/`, `safety/`, `templates/`, `static/`, `deploy/` and `docs/` arrive. Make the repository private: the code, the deployment scripts and the AWS instance identifier in `Setup-Administrator.ps1` are not things a competitor or an attacker needs to read.",
        PromptBlock("Push commands", PUSH)[0],
        "Add the GitHub Actions workflow from your QC repository as a template so `python manage.py test` and `python manage.py check --deploy` run on every push.",
    ], done="The repository is private, contains the full tree, and a green check appears on the latest commit.", effort="1 hour", who="Charles")]

    s += [H2("2.3 The job of the marketing site")]
    s += [P("Today the public face is an early-access landing page served by the application in `PUBLIC_PRELAUNCH` mode, with an interest form that records consent text and campaign tags (the `prelaunchlead` and `prelaunchvisit` tables). That is a sound foundation for a waitlist. It is not enough to sell a $79 to $249 a month product to a stranger in Texas. The site has to do five things in this order: say who it is for, prove it works, show the price, remove the risk, and collect the email or the trial.")]
    s += [Callout("The five-second test", "A contractor lands on the home page from a LinkedIn post at 9 pm. Within five seconds they should be able to say: 'This is a safety program tool for small trade contractors like me, made by an electrical contractor, it costs about $150 a month for my whole company, and I can try it or get a free checklist.' Every step in 2.4 and 2.5 serves that sentence.", "tip")]

    s += [H2("2.4 Site structure to build")]
    s += Tbl(["Page", "Purpose", "Must contain"], [
        ["Home", "Pass the five-second test and route visitors", "Hero (2.5), three proof bars, how it works in four steps, the GC packet, the seven-element culture table (Section 4.6), pricing teaser, guarantee, founder line, FAQ, two calls to action repeated"],
        ["How it works", "Show the weekly loop", "Screens or a 60-second video: Monday reminders, Tuesday talk with sign-in, inspection with photo, corrective action closed, monthly leadership summary, packet export"],
        ["For owners / For office managers / For foremen", "Speak to each persona", "One page each, with the three things that person stops doing by hand"],
        ["Electrical / HVAC / Plumbing / Low voltage", "Trade depth and search traffic", "Trade-specific hazards, the talks and programs included, a sample talk to read, a sample packet to download"],
        ["Pricing", "Remove the price question", "Three flat tiers, unlimited crew logins, annual discount, founding-member banner with end date, the 40-worker comparison chart, the guarantee, FAQ on seats, sites, cancellation, data export"],
        ["Free tools", "Collect emails", "OSHA Readiness Checklist (PDF), Bid-Readiness Score, Toolbox Talk Tuesday signup, site-specific safety plan starter, 300A applicability checker"],
        ["State pages", "Nationwide search traffic", "One page per state as described in Section 5.9, dated"],
        ["About / The ECI story", "Trust", "1984, Covington, K-12 schools, IEC, the apprenticeship program, the founder's reason for building this, the named qualified reviewer, photos of real crews"],
        ["Security and data", "Answer the insurer and the office manager", "Encryption, backups, MFA for operators, immutable records, retention, who can see what, how to export and leave"],
        ["Legal", "Required for nationwide sales", "Terms of service, privacy policy, acceptable use, the disclaimer that the product supports but does not certify compliance"],
        ["Book a call / Start trial", "Conversion", "A 15-minute onboarding call booking, or the trial signup that already exists at /signup/, with a phone number visible"],
        ["Blog", "Search and proof of expertise", "Two articles a month from Prompt P7, on the same domain"],
    ], widths=[1.35 * inch, 1.55 * inch, CONTENT_W - 2.9 * inch])

    s += [H2("2.5 Home page copy, ready to paste")]
    s += Tbl(["Block", "Copy"], [
        ["Eyebrow", "For electrical, HVAC, plumbing and low-voltage contractors with 5 to 100 field workers"],
        ["Headline", "The safety department for contractors too small to have one"],
        ["Subhead", "Weekly toolbox talks with sign-in, written programs, training records, incident handling and the packet your GC asks for, run from a phone. Built and used every day by a Georgia electrical contractor on job sites since 1984."],
        ["Primary button", "Start your 14-day trial"],
        ["Secondary button", "Get the free OSHA readiness checklist"],
        ["Proof bar 1", "Flat price for the whole company. Unlimited crew logins. English and Spanish."],
        ["Proof bar 2", "Records that survive an inspection: every talk, signature and correction is timestamped and cannot be edited after the fact."],
        ["Proof bar 3", "One click produces the safety submittal packet general contractors and prequalification networks ask for."],
        ["How it works", "1. Tell us your trade, crew size and state. 2. Get your written program, your calendar of talks, inspections and reviews, and your reminders. 3. Foremen run Tuesday's talk from a phone; crews sign in. 4. When the GC, the insurer or an inspector asks, download the packet."],
        ["The money line", "A single serious OSHA citation can cost $16,550. Registering with ISNetworld costs about $875 a year before you have produced a single document. Safety CoPilot starts at $79 a month for your whole company."],
        ["Guarantee", "Inspection-ready records in 30 days, or we work with you free until you have them."],
        ["Founder line", "'I have run electrical crews since 1984. We built this because the safety binder never survived contact with a real job site.' Charles Black, Electrical Contractor Inc., Covington, Georgia."],
        ["Closing call to action", "Start the trial, or take the two-minute bid-readiness score and see where you stand."],
    ], widths=[1.35 * inch, CONTENT_W - 1.35 * inch])
    s += [P("Keep every regulatory number with a small source line and a 'checked on' date. Replace the money line's figures when the OSHA penalty table changes each January.", "small")]

    s += [H2("2.6 Step-by-step site improvements")]
    steps = [
        ("Separate the marketing site from the application by hostname", ["Serve the marketing pages at the product domain (for example www.[name].com) and the application at app.[name].com. Keep safety1.ecinc.us as a redirect. This lets you use different analytics, caching and security headers on each, and it stops search engines indexing login pages.", "Your QC deployment already runs Apache as a TLS proxy with Certbot renewal hooks; reuse that pattern with two virtual hosts."], "Both hostnames serve over HTTPS with valid certificates; HTTP redirects; the old address redirects to the new one.", "Half a day", "Developer"),
        ("Rewrite the home page to the copy in 2.5 and add the twelve pages in 2.4", ["Start with Home, Pricing, Free tools, About and Legal. Trade and state pages follow in the first month. Every page has one job and one primary button."], "Five people outside ECI pass the five-second test on the home page.", "1 to 2 weeks", "Charles and a developer"),
        ("Build the three free tools as real forms that write to the lead list", ["The prelaunch lead model already stores email, company, interest, source, campaign and consent. Extend it or connect the forms to Brevo. Send the checklist automatically and start the five-email sequence (Section 5.10)."], "A test submission arrives in Brevo tagged with its campaign and receives the PDF within one minute.", "2 to 3 days", "Developer"),
        ("Publish pricing with the comparison chart and the guarantee", ["Use the chart in Section 3.6 and the tier table. State clearly: no per-seat fees, cancel any time, export your data any time."], "The pricing page answers seats, sites, cancellation and data export without a call.", "1 day", "Charles"),
        ("Add search basics to every page", ["Unique title under 60 characters and meta description under 155; one H1; Open Graph image; canonical URL; `sitemap.xml` via Django's sitemap framework and `robots.txt` that allows the marketing site and disallows the app; JSON-LD for Organization, SoftwareApplication and, on the pricing page, Offer."], "Google Search Console shows the sitemap accepted and no coverage errors.", "1 day", "Developer"),
        ("Install analytics and one link convention", ["Use the Umami analytics your candidate portal already references, or Google Analytics 4. Adopt the UTM convention from Section 5.6 step 10. Track four events: checklist download, score completed, trial started, call booked."], "Each of the four events fires in a test and appears in the dashboard.", "Half a day", "Developer"),
        ("Harden the Django deployment for strangers", ["Run `python manage.py check --deploy` and clear every warning: `DEBUG=0`, exact `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` (start at 300, raise after a week), secure and HttpOnly cookies, `X_FRAME_OPTIONS=DENY`, a Content-Security-Policy header, and `SESSION_COOKIE_AGE` suited to shared field phones. Keep `private-media/` off the web root as the README says.", "Rate-limit signup, login and password reset (the `loginattempt` table shows throttling exists for login; extend it). Add a honeypot field to public forms."], "`check --deploy` reports no issues; a header scanner such as securityheaders.com grades A or better [verify on the live site].", "1 day", "Developer"),
        ("Fix email before launch", ["Replace the Gmail app-password SMTP setup with Amazon SES (you already run on AWS), Postmark or Resend. Publish SPF, DKIM and DMARC for the sending domain. Send incident alerts from a dedicated subdomain (for example alerts.[name].com) so marketing mail never affects their reputation. Add SMS for the URGENT class."], "Test mail passes SPF, DKIM and DMARC checks and arrives in Gmail and Outlook inboxes; an urgent test alert arrives by SMS.", "2 to 3 days", "Developer"),
        ("Make the site fast and readable on a phone", ["Compress and resize images (WebP, under 200 KB each), lazy-load below the fold, self-host or preload fonts, and keep the home page under 1.5 MB. Check with Lighthouse on a mid-range Android phone."], "Lighthouse performance above 85 and accessibility above 95 on mobile [verify on the live site].", "1 day", "Developer"),
        ("Pass a basic accessibility review", ["Contrast at least 4.5:1 for body text (ECI red on white passes for large text only; use it for accents, not paragraphs), visible focus states, labels on every form field, alt text on every image, captions on the video, keyboard-only navigation of the signup flow."], "No critical or serious issues in an axe scan; a keyboard-only signup succeeds.", "Half a day", "Developer"),
        ("Publish the legal and security pages", ["Terms of service with the support-not-certify disclaimer, privacy policy covering worker records and retention, and the security page. Have a lawyer read the terms once; templates from a reputable generator are a fine starting point."], "All three pages are linked in the footer of every page.", "2 days plus legal review", "Charles"),
        ("Add trust signals that are true today", ["'Since 1984', IEC membership, 'used daily on ECI job sites', photos of real crews with consent, the qualified reviewer's name and credential, a real phone number and Covington address, links to the ECI company site. Add customer logos and quotes only as they become real."], "Every trust claim on the site can be backed by a document or a person.", "1 day", "Charles"),
        ("Instrument the trial so you can see where people stop", ["Track signup started, company created, first employee added, first talk scheduled, first talk completed, first packet downloaded. Email yourself when a trial stalls for three days."], "A funnel report shows each step's completion rate for the last 30 days.", "1 to 2 days", "Developer"),
        ("Put an uptime monitor and a status line in place", ["The README notes there is no external uptime monitor. Use a free monitor for the marketing site, the app login page and the worker heartbeat (`serviceheartbeat` exists). Alert to your phone."], "A deliberate stop of the worker produces an alert within five minutes.", "1 hour", "Developer"),
    ]
    for i, (title, body, done, effort, who) in enumerate(steps, 3):
        s.append(Step(i, title, body, done=done, effort=effort, who=who))
    s += [Sp(6)]

    s += [H2("2.7 Inside the application: the ten changes that matter most to buyers")]
    s += [P("These are product changes visible in the schema and README that affect whether a stranger buys and stays. Section 4.5 covers the deeper platform gaps (payments, email provider, offline, state plans).")]
    s += Numbered([
        "**Publish the content.** 0 of 54 talks and 0 of 3 programs are published. A trial that opens to empty libraries ends. Ship at least 26 reviewed talks (English and Spanish) and three finished programs before launch.",
        "**A first-week onboarding checklist** inside the app: add crew, pick trade, confirm state, schedule the first talk, run it, download the packet. Show progress on the dashboard.",
        "**The GC packet export**: one action that bundles the current program versions, training matrix, last 12 weeks of talk reports with signatures, open and closed corrective actions, 300A where applicable, and slots for the COI and EMR letter. Your ZIP export is the start; make it a branded PDF too.",
        "**A bid-readiness score** computed from what exists: program reviewed within 12 months, talk completion rate, open corrective actions, expired credentials, 300A posted. Show it to the owner every Monday.",
        "**Spanish everywhere the crew touches**: talk text, sign-in screen, reminder messages, quiz questions.",
        "**Photo-first inspection** from a phone using the QC field app's uploader and offline queue.",
        "**Cert expiry reminders to the employee**, not only the office (the `credential` table has `expires_on`; the `employee` table has an email).",
        "**A share link for GC safety directors** to view a company's current packet without an account, expiring in 30 days, logged in the audit table.",
        "**Data export and account deletion** on demand, documented on the security page. Buyers' insurers ask; some state privacy laws require it.",
        "**Show the audit trail** to the customer: the immutable snapshot and digest already exist in `report`; a visible 'this record has not changed since [date]' line turns an internal safeguard into a selling point.",
    ])

    s += [H2("2.8 Launch-readiness checklist")]
    s += Tbl(["Area", "Ready when"], [
        ["Repository", "Private, full source, no secrets, tests and deploy check green on every push"],
        ["Hosting", "Marketing and app hostnames on HTTPS with automatic renewal; backups restored once in a drill; uptime monitor alerting"],
        ["Application", "check --deploy clean; MFA enrolled for operators; payments live; transactional email authenticated; SMS for urgent alerts"],
        ["Content", "26 talks and 3 programs published and signed off by the named qualified person; Spanish reviewed"],
        ["Site", "Twelve pages live; five-second test passed; free tools delivering; analytics events firing; legal pages linked"],
        ["Proof", "ECI running its own program for 30 days; five pilots signed; one video; one written testimonial"],
        ["Marketing", "Brand file, calendar, Routine and Buffer connected; two-week dry run complete; partner conversations started"],
    ], widths=[1.3 * inch, CONTENT_W - 1.3 * inch])
    return s
