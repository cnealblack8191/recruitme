import sys, os
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
from pdfkit import *
import content_summary, content_site, content_business, content_growth, content_marketing, content_brand, content_prompts, content_talks, content_sources

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(S, "SafetyCoPilot-Site-Review-Strategy-Marketing-Plan.pdf")
doc = ReportDoc(OUT,
    "Safety CoPilot: Site Review, Business Strategy and a Bot-Run Marketing Plan",
    "A step-by-step improvement guide for safety1.ecinc.us, an honest assessment of the business idea and its path to $10,000 a month nationwide, and an inexpensive marketing engine a bot can run.",
    "Charles Black, Electrical Contractor Inc. (ECI)", "September 17, 2026",
    os.path.join(S, "eci-logo.png"), "Safety CoPilot — Site Review, Strategy & Marketing Plan")

story = cover_flowables(doc)
story += [Paragraph(md("**Inside:** executive summary · site fixes and rebuild steps · business assessment · growth model to $10k a month · bot-run marketing engine · naming · 30/60/90 plan · paste-ready prompts · 26 toolbox talks · sources"), ST["cover_meta"])]
story += [NextPageTemplate("Body"), PageBreak(), H1("Contents"), doc.toc, PageBreak()]
story += content_summary.build_summary(); story += [PageBreak()]
story += content_site.build(); story += [PageBreak()]
story += content_business.build(); story += [PageBreak()]
story += content_growth.build(); story += [PageBreak()]
story += content_marketing.build(); story += [PageBreak()]
story += content_brand.build(); story += [PageBreak()]
story += content_summary.build_plan(); story += [PageBreak()]
story += content_prompts.build(); story += [PageBreak()]
story += content_talks.build(); story += [PageBreak()]
story += content_sources.build()
doc.multiBuild(story)
n, outs = render_pngs(OUT, os.path.join(S, "page"), scale=1.25)
print("PDF pages:", n)
print("size KB:", os.path.getsize(OUT) // 1024)
