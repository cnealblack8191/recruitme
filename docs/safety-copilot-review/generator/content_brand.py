from pdfkit import *

def build():
    s = []
    s += [Kicker("Section 6"), H1("Name, brand and domain", 6)]
    s += [Lead("'Safety CoPilot' describes the product well and it is the name in your code, so this section is not an argument to throw it away lightly. It is an argument to check it properly, because 'Copilot' belongs to Microsoft in the public's mind and in search results, and a national launch is the last cheap moment to change.")]
    s += [H2("6.1 The problem with the current name")]
    s += Bullets([
        "Search: 'safety copilot' returns Microsoft Copilot content and Copilot-branded safety integrations. Your pages would compete with Microsoft for your own brand name.",
        "Trademark: Microsoft holds Copilot marks across software categories. A software product called 'Safety CoPilot' invites a letter, and even a polite one costs money and time at the worst moment.",
        "Repository and hostnames already vary: SafetyCoPilot (folder), safeftypro (repository), safety1.ecinc.us (site). Pick one name and use it everywhere.",
        "'SafetyPro' is not an escape: a consulting firm (SafetyPro Resources), an enterprise platform (safetypro24.com) and a machine-safety app already use it.",
    ])
    s += [H2("6.2 Candidate names to check")]
    s += Tbl(["Candidate", "Why it could work", "Watch for"], [
        ["SiteReady", "Says the outcome (ready for the GC, ready for the inspector). Short, spellable on the phone.", "Common word pair; check software marks carefully."],
        ["CrewSafe HQ", "Crew-first, phone-first. 'HQ' signals the system of record.", "'CrewSafe' variants exist in adjacent markets; the 'HQ' suffix may be needed."],
        ["ToolboxIQ", "Anchors on the toolbox talk, the habit everyone knows.", "Sounds like a training-only product; check the IQ-suffix crowd."],
        ["PacketReady", "Names the one-click GC packet, the feature nobody else sells.", "Narrow; the product is more than the packet."],
        ["Redline Safety", "Electrical heritage (redline drawings), ECI red, memorable.", "'Redline' is used by many companies; safety category check required."],
        ["Journeyman Safety", "Trade credibility, implies experience not theory.", "Long; check for training schools with the name."],
        ["SafeCrew by ECI", "Plain, honest, carries the founder credibility in the name.", "'Safe Crew' is generic; the 'by ECI' suffix does the differentiating."],
        ["Foreman's Desk", "The foreman is the user who makes records complete; 'desk' says system.", "Check hospitality and furniture marks; slightly dated feel."],
    ], widths=[1.3 * inch, 3.0 * inch, CONTENT_W - 4.3 * inch])
    s += [H2("6.3 How to check a name in one afternoon")]
    s += Numbered([
        "Search the USPTO trademark database for the exact name and close variants in classes 9 and 42 (software and software services). A live registration or pending application in those classes is a stop sign.",
        "Search Google for the name plus 'safety', 'construction' and 'app'. Two pages of results with no competing product is the target.",
        "Check the .com and the matching handles on LinkedIn, Facebook, Instagram, YouTube, X and TikTok. A hyphenated or suffixed domain is acceptable only if the .com is parked, not if it is a competitor.",
        "Check the Apple and Google app stores for the name.",
        "Say it on the phone to five contractors and ask them to spell it back. If two get it wrong, drop it.",
        "Shortlist three, register the .com for each (about $15 a year), and choose within a week. Keep 'by Electrical Contractor Inc.' or 'by ECI' as a suffix on the logo and in the footer whatever you choose.",
    ])
    s += [H2("6.4 Tagline options")]
    s += Bullets([
        "The safety department for contractors too small to have one.",
        "Run safety like a crew, not a binder.",
        "Inspection-ready. Bid-ready. Every week.",
        "Built on job sites since 1984.",
    ])
    s += [H2("6.5 Visual identity notes")]
    s += Bullets([
        "Keep ECI's black and red for the 'by ECI' mark; give the product its own primary colour with enough contrast for body text (a deep navy or slate works with red accents). Red is for buttons and warnings, never paragraphs.",
        "Photography: real ECI crews, real panels and lifts, daylight, no stock hard-hat handshakes. Get written consent from anyone identifiable; blur faces otherwise.",
        "Typography: one readable sans-serif for the app and the site; the candidate portal's Source Sans 3 is a good choice and already licensed for web use.",
        "One logo file set: full lockup, icon only, and a one-colour version for embroidery on ECI shirts, which is the cheapest advertising you will ever buy.",
    ])
    return s
