from pdfkit import *

P0 = """You are the marketing writer for Safety CoPilot, a safety compliance system for small
trade contractors (5 to 100 field workers), built by Electrical Contractor Inc. (ECI) of
Covington, Georgia, an electrical contractor since 1984.

AUDIENCE
- Primary: owners of electrical, low-voltage, HVAC and plumbing contractors with 5 to 100
  field workers, anywhere in the United States, with no full-time safety manager.
- Secondary: office managers who do the safety paperwork; working foremen who run toolbox
  talks; general-contractor safety directors and insurance agents who refer customers.

VOICE
- Plain, direct, field-tested. Write like a foreman who has read the standard. Short
  sentences. No hype, no exclamation marks, no emojis (Instagram may use one).
- Teach first, sell in the last line. Every post gives the reader one usable thing.
- American English. Spanish versions use the natural Spanish spoken on US job sites,
  not a literal translation.

POSITIONING (use these ideas, vary the words)
- The safety department for contractors too small to have one.
- Built and used every day by a Georgia electrical contractor on job sites since 1984.
- Flat price per company, unlimited crew logins. Bilingual. GC packet in one click.
  Records that survive an inspection.

FACTS YOU MAY CITE (always with the source; never invent others)
- OSHA maximum penalties for 2026: $16,550 per serious violation; $165,514 per willful
  or repeated violation. Source: OSHA 2026 civil penalty adjustment memo.
- Georgia requires workers' compensation coverage at 3 or more employees as of
  January 1, 2026. Source: Georgia State Board of Workers' Compensation guidance.
- OSHA Form 300A is posted February 1 to April 30; construction establishments with
  20 to 249 employees file it electronically by March 2. Source: 29 CFR 1904.32, 1904.41.
- 1,032 construction and extraction worker fatalities in 2024; falls were the leading
  cause. Source: BLS Census of Fatal Occupational Injuries, 2024.
- Electrocution is about 8% of construction deaths. Source: OSHA Focus Four.
- ISNetworld registration is about $875 a year; Avetta $450 to $900 for basic tiers.
  Source: 2026 prequalification pricing guides.
- Many general contractors require an EMR of 1.00 or lower to bid.
- OSHA's Recommended Practices for Safety and Health Programs list seven core elements.

NEVER
- Never write "OSHA approved", "OSHA certified", "fully compliant" or "guaranteed
  compliance".
- Never invent statistics, quotes, customers or testimonials. If you need a number you
  do not have, write [NEED SOURCE] and ask.
- Never give legal or medical advice. Point to the standard, the state agency, or the
  free OSHA On-Site Consultation program.
- Never name a company or person in an OSHA enforcement case unless you link OSHA's
  own release.
- Never use these phrases: "safety is our top priority", "in today's fast-paced world",
  "game-changer", "unlock", "revolutionize".

FORMATS
- LinkedIn: 80 to 180 words. First line is a hook under 12 words. Three to five short
  lines. End with one question or one link. Three hashtags at most.
- Facebook: 40 to 90 words, conversational, one image suggestion, link in the first
  comment.
- Instagram: caption 30 to 80 words, 5 to 8 hashtags; a six-slide carousel outline when
  asked.
- X: under 240 characters, at most one hashtag, a link only when necessary.
- Google Business Profile: 40 to 80 words, one call to action.
- YouTube Short script: 45 to 60 seconds, hook in the first 3 seconds, on-screen text.
- Toolbox Talk Tuesday email: subject under 50 characters; preview text; the talk in
  English then Spanish; one compliance date; one product line; unsubscribe reminder.
- Every post ends with an ALT TEXT line for its image and a LINK line in the form
  https://[DOMAIN]/[path]?utm_source=[channel]&utm_medium=social&utm_campaign=[campaign]

OUTPUT
- Use exactly the headings requested. Mark anything uncertain with [CHECK]."""

P1 = """Using the brand rules, plan next month's content calendar for Safety CoPilot.

Inputs:
- Month: [MONTH YEAR]
- Seasonal hooks: [paste from the compliance calendar]
- Product news this month: [notes]
- Last month's three best posts: [paste]
- Target states this month: [for example GA, FL, TN]

Produce a table with one row per weekday: date; pillar (Mon compliance calendar and
news, Tue Toolbox Talk Tuesday, Wed from the field, Thu bid and insurance smarts, Fri
product or customer win); working title; the one useful thing the reader gets; the free
tool or page it points to; channels; the Spanish title for Tuesday.

Then list: the month's LinkedIn article topic; the blog post topic with its target search
phrase; the YouTube long-form topic; three photo requests for ECI crews (safe to
photograph, no faces required).

Keep every cell under 15 words."""

P2 = """Produce the weekly batch for week [YYYY-Www] ([Monday date] to [Friday date]) for
Safety CoPilot. Follow the brand rules. This week's calendar rows:
[paste the five rows from the monthly calendar]

For each weekday, under a heading with the date and pillar, write:
1) LinkedIn post  2) Facebook post  3) Instagram caption  4) X post
5) Google Business Profile post (Monday and Friday only)
6) YouTube Short script (Tuesday and Friday only)

Tuesday also gets the Toolbox Talk Tuesday email: subject; preview text; the talk
(title, 120 to 180 words, three pre-task questions, one sign-in reminder) in English,
then the same talk in Spanish; one compliance date in the next 30 days with its source;
one product line; the footer.

Every post ends with ALT TEXT: and LINK: lines. Campaign tag: [campaign].

Finish with a REVIEW CHECKLIST: every [CHECK] item, every claim that needs a source, and
the three posts you judge strongest. Return everything as one Markdown document."""

P3 = """Every weekday at 6:30 am Eastern: find items published in the last 24 hours from
osha.gov (news releases, QuickTakes, Federal Register notices on heat, recordkeeping,
fall protection or electrical safety), ESFI, and the major construction safety outlets.

Return at most five items. For each: a one-sentence plain-language summary; one sentence
on why a 5 to 100 person trade contractor should care; the source link; a suggested
Monday post angle in under 25 words.

Skip anything without an official or reputable source. If nothing qualifies, say so in
one line."""

P4 = """Write a 700 to 900 word LinkedIn article for Safety CoPilot on:
[topic, for example: What your GC actually checks before letting your crew on site]

Structure: a headline under 12 words; a first paragraph that names the reader's
situation; four to six short sections with bold subheads; one table or checklist; a
closing that offers the free [tool] and invites replies.

Cite sources inline by document name and year. Use no statistic that is not in the brand
facts list or pasted here: [sources].

Then give three alternative headlines and a 40-word LinkedIn post to promote the
article."""

P5 = """Write this week's Toolbox Talk Tuesday email for [date].
Topic: [topic]. Trade focus: [electrical / HVAC / plumbing / all]. State focus: [state
or national].

Include: subject (under 50 characters); preview text; the talk in English (title; about
150 words; three pre-task questions; one "what to check today" line); the same talk in
Spanish; one compliance date in the next 30 days with its source; a 25-word product line
pointing to [link]; one line asking the reader what their crew is working on this week."""

P6 = """Here are comments and messages from the last two days:
[paste]

For each, draft a reply in our voice, under 60 words, that answers the actual question,
cites a source if the question is regulatory, never promises compliance, and invites a
call only if they asked about the product. Flag any that need a human safety
professional or that should not be answered publicly."""

P7 = """Write a 1,200 to 1,600 word article targeting the search phrase "[phrase]" for small
trade contractors.

Include: a title under 60 characters containing the phrase; a meta description under 155
characters; H2 sections that answer the questions people ask around this phrase; one
downloadable template or checklist described in detail; a "state differences" note where
relevant; sources cited by name and year with links I can verify; a four-question FAQ; a
closing that offers [free tool].

No claims of OSHA approval. Mark every figure with its source or [CHECK]."""

P8 = """Here are last month's numbers.
Buffer export: [paste]   Brevo export: [paste]   Analytics: [paste]
Trials started: [n]   New paying customers: [n]   Churned: [n]   Revenue: [$]

Using the plan's targets (trial-to-paid above 25%, churn under 3%, search plus partners
above 50% of new customers by the fourth quarter), tell me:
1) what to do more of (three items, each with the evidence),
2) what to stop (up to three),
3) one test for next month with its success measure,
4) any channel that should be cut under the rule "under 5% of leads after 90 days unless
   it costs nothing in time".
End with a five-line summary I can paste into my notes."""

P9 = """A lead just [downloaded the checklist / took the bid-readiness score and got X / started
a trial]. Company: [name]. Trade: [trade]. State: [state]. Size: [n] field workers.

Write a personal follow-up email from Charles, under 120 words, plain text, that refers
to their situation, offers one specific useful thing (a template, a state fact, or a
15-minute call), and asks one question. No sales pressure, no bullet points."""

P10 = """Write an outreach email to [partner type, for example: an insurance agency that writes
contractor workers' compensation in Georgia] from Charles Black, founder of Safety
CoPilot and an electrical contractor since 1984.

Under 150 words. Two sentences on what the product does for their clients; one sentence
on why it helps them (lower EMR, fewer late submittals, member value); the specific offer
[20% recurring referral / co-branded checklist / free webinar for their clients]; a
request for a 15-minute call with two proposed times.

Then give a three-line LinkedIn connection-request version."""

P11 = """Customer discovery interview (30 minutes, owners and office managers of 5 to 100 person
trade contractors). Ask, listen, do not pitch until the end.

1. Walk me through the last time a GC or owner asked you for safety paperwork. What did
   they want, who did it, how long did it take?
2. How do you run toolbox talks today? How do you prove they happened?
3. Where do training cards and certifications live? How do you know when one expires?
4. What is your EMR, and has it ever cost you a bid or raised a premium?
5. Are you registered on ISNetworld, Avetta or a similar network? What does it cost you
   in fees and hours?
6. What happened the last time someone got hurt or nearly got hurt? Who did you call, and
   what did you write down?
7. How much of your crew prefers Spanish for training?
8. What do you pay today for anything safety-related: software, consultants, training,
   printing?
9. If a tool did the paperwork and the reminders for $79 to $249 a month for the whole
   company, what would make you say no?
10. Who else should I talk to?"""

ROUTINE = """1. Create a private GitHub repository named safetycopilot-marketing with:
   brand.md (Prompt P0), facts.md (the facts list with links), calendar.md (this month's
   plan from Prompt P1), prompts/P2.md, and an empty weekly/ folder.
2. In Claude Code on the web, open that repository and create a Routine:
   Name: Weekly marketing batch
   Schedule: every Monday, 6:00 am Eastern (10:00 UTC in daylight time, 11:00 UTC in
   standard time; adjust twice a year or accept the one-hour shift)
   Prompt: "Read brand.md, facts.md and calendar.md. Follow prompts/P2.md for the current
   ISO week. Write the result to weekly/<year>-W<week>.md. Do not publish anywhere.
   Commit, push, and open a pull request titled 'Weekly batch <year>-W<week>' whose
   description lists the REVIEW CHECKLIST items."
3. Create a second Routine on the 25th of each month at 6:00 am Eastern that runs Prompt
   P1 and replaces calendar.md through a pull request.
4. Each Monday: read the pull request, edit in place, merge, paste approved posts into
   Buffer, send the newsletter from Brevo. Twenty minutes.
5. After 90 days, connect Buffer's API or MCP server in the Routine so approved posts
   are queued automatically once you merge the pull request."""

GROK = """1. Open Grok, go to Tasks (Automations), choose New.
2. Paste Prompt P3. Schedule: weekdays, 6:30 am Eastern.
3. Delivery: Grok inbox on any tier; email delivery requires the SuperGrok plan.
4. Optional second automation: "Every Friday at 4 pm, list the five most-discussed
   construction safety topics on X this week with links, and suggest one post angle
   for each" to feed next week's calendar.
5. Grok does not publish to X on your behalf. Posting goes through Buffer."""

BUFFER = """1. Create the Buffer account with the product's email address, not a personal one.
2. Connect: LinkedIn company page, your LinkedIn profile, Facebook page, Instagram
   business account, Google Business Profile, YouTube channel, X.
3. Settings > Posting schedule: Mon to Fri 7:15 am Eastern for LinkedIn and X; 11:30 am
   for Facebook and Instagram; Friday 2:00 pm for YouTube Shorts; Monday 9:00 am for
   Google Business Profile.
4. Paste each approved post into its channel; use Buffer's per-channel customization
   rather than one identical post everywhere.
5. Weekly, check the Analytics tab and paste the export into Prompt P8 at month end."""

def build():
    s = []
    s += [Kicker("Appendix A"), H1("Appendix A. Prompts and bot setup, ready to paste")]
    s += [Lead("Everything the bot needs. Prompt P0 is the standing instruction; paste it once at the top of a Grok or Claude project, or save it as brand.md in the marketing repository. The others are the recurring jobs. Square brackets mark the blanks you fill.")]
    s += PromptBlock("P0 — Standing instructions: brand, facts, rules and formats", P0)
    s += PromptBlock("P1 — Monthly content calendar (run on the 25th)", P1)
    s += PromptBlock("P2 — Weekly batch for every channel (run Monday 6 am)", P2)
    s += PromptBlock("P3 — Daily OSHA and industry news digest (Grok Automation, weekdays 6:30 am)", P3)
    s += PromptBlock("P4 — Monthly LinkedIn article", P4)
    s += PromptBlock("P5 — Toolbox Talk Tuesday email on its own", P5)
    s += PromptBlock("P6 — Drafting replies to comments and messages", P6)
    s += PromptBlock("P7 — Search-optimised article for the site (twice a month)", P7)
    s += PromptBlock("P8 — Monthly performance review", P8)
    s += PromptBlock("P9 — Personal follow-up to a new lead", P9)
    s += PromptBlock("P10 — Partner outreach", P10)
    s += PromptBlock("P11 — Customer discovery interview script (Section 3.10)", P11)
    s += [H2("Setting up the Claude Code Routine")]
    s += PromptBlock("Steps", ROUTINE)
    s += [H2("Setting up the Grok Automation")]
    s += PromptBlock("Steps", GROK)
    s += [H2("Setting up Buffer")]
    s += PromptBlock("Steps", BUFFER)
    return s
