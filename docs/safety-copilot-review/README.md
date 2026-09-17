# Safety CoPilot review, strategy and marketing plan

`SafetyCoPilot-Site-Review-Strategy-Marketing-Plan.pdf` is the report prepared for Charles Black on September 17, 2026: step-by-step site improvements for safety1.ecinc.us, an assessment of the business idea and its path to $10,000 a month nationwide, a bot-run marketing plan, paste-ready prompts, a starter list of 26 toolbox talks, and sources.

`research-notes.md` holds the research findings and citations the report draws on.

## Rebuilding the PDF

```sh
pip install reportlab pypdf pypdfium2 pillow
cd generator
python3 build_report.py            # writes the PDF next to the script and page-*.png previews
```

The generator expects the Liberation and DejaVu TrueType fonts at their usual Linux paths (`/usr/share/fonts/truetype/`). Edit the `content_*.py` modules to change the text; `pdfkit.py` holds the styles and layout helpers.
