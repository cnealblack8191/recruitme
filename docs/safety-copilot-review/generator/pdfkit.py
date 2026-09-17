"""Small ReportLab helper layer for the Safety CoPilot report."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, PageBreak, KeepTogether, Image,
                                CondPageBreak, NextPageTemplate, Flowable)
from reportlab.platypus.tableofcontents import TableOfContents
from xml.sax.saxutils import escape
import re

# ---------- fonts ----------
FD = "/usr/share/fonts/truetype/liberation/"
pdfmetrics.registerFont(TTFont("Body", FD + "LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Body-Bold", FD + "LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Body-Italic", FD + "LiberationSans-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Body-BoldItalic", FD + "LiberationSans-BoldItalic.ttf"))
pdfmetrics.registerFont(TTFont("Mono", FD + "LiberationMono-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Mono-Bold", FD + "LiberationMono-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Display", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-BoldItalic")
registerFontFamily("Mono", normal="Mono", bold="Mono-Bold", italic="Mono", boldItalic="Mono-Bold")

# ---------- palette ----------
RED = colors.HexColor("#C8102E")
RED_DARK = colors.HexColor("#8F0B20")
INK = colors.HexColor("#141414")
SLATE = colors.HexColor("#4B5563")
MUTED = colors.HexColor("#6B7280")
LIGHT = colors.HexColor("#F4F4F5")
LIGHTER = colors.HexColor("#FAFAFA")
LINE = colors.HexColor("#D4D4D8")
AMBER = colors.HexColor("#B45309")
AMBER_BG = colors.HexColor("#FFF7E6")
GREEN = colors.HexColor("#15803D")
GREEN_BG = colors.HexColor("#ECFDF3")
BLUE = colors.HexColor("#1D4ED8")
BLUE_BG = colors.HexColor("#EFF6FF")
RED_BG = colors.HexColor("#FDECEE")

PAGE_W, PAGE_H = letter
LM = RM = 0.9 * inch
TM = 0.95 * inch
BM = 0.85 * inch
CONTENT_W = PAGE_W - LM - RM

# ---------- styles ----------
def _ps(name, **kw):
    base = dict(fontName="Body", fontSize=10, leading=14.2, textColor=INK, spaceAfter=6)
    base.update(kw)
    return ParagraphStyle(name, **base)

ST = {
    "body": _ps("body"),
    "small": _ps("small", fontSize=8.6, leading=11.6, textColor=SLATE),
    "tiny": _ps("tiny", fontSize=7.6, leading=9.8, textColor=MUTED),
    "lead": _ps("lead", fontSize=11.5, leading=16.5, textColor=SLATE, spaceAfter=10),
    "h1": _ps("h1", fontName="Body-Bold", fontSize=22, leading=26, textColor=INK, spaceBefore=6, spaceAfter=4),
    "h2": _ps("h2", fontName="Body-Bold", fontSize=14.5, leading=18, textColor=INK, spaceBefore=14, spaceAfter=5),
    "h3": _ps("h3", fontName="Body-Bold", fontSize=11.2, leading=14.5, textColor=RED_DARK, spaceBefore=9, spaceAfter=3, keepWithNext=1),
    "kicker": _ps("kicker", fontName="Body-Bold", fontSize=8.4, leading=11, textColor=RED, spaceAfter=2, keepWithNext=1),
    "bullet": _ps("bullet", leftIndent=14, bulletIndent=3, spaceAfter=3.5),
    "bullet2": _ps("bullet2", leftIndent=30, bulletIndent=18, spaceAfter=3, fontSize=9.4, leading=13.2),
    "num": _ps("num", leftIndent=18, bulletIndent=2, spaceAfter=4),
    "cell": _ps("cell", fontSize=8.7, leading=11.4, spaceAfter=0),
    "cellb": _ps("cellb", fontName="Body-Bold", fontSize=8.7, leading=11.4, spaceAfter=0),
    "cellh": _ps("cellh", fontName="Body-Bold", fontSize=8.7, leading=11.2, textColor=colors.white, spaceAfter=0),
    "mono": _ps("mono", fontName="Mono", fontSize=8.1, leading=10.8, textColor=INK, spaceAfter=0),
    "callout": _ps("callout", fontSize=9.4, leading=13.2, spaceAfter=0),
    "calloutlabel": _ps("calloutlabel", fontName="Body-Bold", fontSize=8.2, leading=10.5, spaceAfter=2),
    "toc1": _ps("toc1", fontName="Body-Bold", fontSize=10.5, leading=15, spaceAfter=1),
    "toc2": _ps("toc2", fontSize=9.4, leading=13, leftIndent=14, spaceAfter=0, textColor=SLATE),
    "quote": _ps("quote", fontName="Body-Italic", fontSize=10, leading=14.5, textColor=SLATE, leftIndent=12),
    "stepnum": _ps("stepnum", fontName="Body-Bold", fontSize=15, leading=17, textColor=RED, spaceAfter=0),
    "steptitle": _ps("steptitle", fontName="Body-Bold", fontSize=10.6, leading=13.5, spaceAfter=2),
    "stepmeta": _ps("stepmeta", fontName="Body-Bold", fontSize=7.8, leading=10, textColor=MUTED, spaceAfter=3),
    "cover_title": _ps("cover_title", fontName="Display", fontSize=30, leading=36, textColor=INK, spaceAfter=8),
    "cover_sub": _ps("cover_sub", fontSize=13.5, leading=19, textColor=SLATE, spaceAfter=6),
    "cover_meta": _ps("cover_meta", fontSize=10, leading=14, textColor=SLATE),
}

def md(text):
    """Very small inline markup: **bold**, *italic*, `code`. Escapes everything else."""
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r"<font face='Mono' size='8.3'>\1</font>", text)
    return text

def P(text, style="body", **kw):
    st = ST[style]
    if kw:
        st = ParagraphStyle(style + str(id(kw)), parent=st, **kw)
    return Paragraph(md(text), st)

def H1(text, num=None):
    label = f"{num}. {text}" if num else text
    return _Heading(label, ST["h1"], level=0, rule=True)

def H2(text):
    return _Heading(text, ST["h2"], level=1)

def H3(text):
    return Paragraph(md(text), ST["h3"])

def Kicker(text):
    return Paragraph(md(text).upper(), ST["kicker"])

def Lead(text):
    return Paragraph(md(text), ST["lead"])

def Bullets(items, style="bullet"):
    out = []
    for it in items:
        if isinstance(it, (list, tuple)):
            out.append(Paragraph(md(it[0]), ST[style], bulletText="•"))
            for sub in it[1]:
                out.append(Paragraph(md(sub), ST["bullet2"], bulletText="–"))
        else:
            out.append(Paragraph(md(it), ST[style], bulletText="•"))
    out.append(Spacer(1, 3))
    return out

def Numbered(items):
    out = []
    for i, it in enumerate(items, 1):
        out.append(Paragraph(md(it), ST["num"], bulletText=f"{i}."))
    out.append(Spacer(1, 3))
    return out

def Sp(h=6):
    return Spacer(1, h)

def Rule(color=LINE, width=0.6, space=6):
    t = Table([[""]], colWidths=[CONTENT_W], rowHeights=[space])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), width, color)]))
    return t

class _Heading(Flowable):
    """Heading that registers a TOC entry and a PDF outline bookmark."""
    def __init__(self, text, style, level=0, rule=False):
        Flowable.__init__(self)
        self.text, self.style, self.level, self.rule = text, style, level, rule
        self.para = Paragraph(md(text), style)
        self.keepWithNext = 1
    def wrap(self, aw, ah):
        w, h = self.para.wrap(aw, ah)
        self.h = h + (10 if self.rule else 0) + self.style.spaceBefore
        return w, self.h
    def split(self, aw, ah):
        return []
    def draw(self):
        c = self.canv
        key = "h%d-%s" % (self.level, abs(hash(self.text)))
        c.bookmarkPage(key)
        c.addOutlineEntry(self.text, key, level=self.level, closed=False)
        y = self.h - self.style.spaceBefore
        if self.rule:
            c.setStrokeColor(RED); c.setLineWidth(2.2)
            c.line(0, y - self.para.height - 6, 1.1 * inch, y - self.para.height - 6)
        self.para.drawOn(c, 0, y - self.para.height)
        # TOC notification
        from reportlab.platypus.doctemplate import _doNothing
        self._doctemplateAttr = None

def Callout(label, text, kind="tip"):
    """kind: tip (blue), warn (amber), do (green), risk (red)"""
    bar, bg, lab = {
        "tip": (BLUE, BLUE_BG, BLUE), "warn": (AMBER, AMBER_BG, AMBER),
        "do": (GREEN, GREEN_BG, GREEN), "risk": (RED, RED_BG, RED_DARK),
    }[kind]
    labst = ParagraphStyle("cl" + kind, parent=ST["calloutlabel"], textColor=lab)
    body = [Paragraph(md(label).upper(), labst)]
    if isinstance(text, (list, tuple)):
        for t in text:
            body.append(Paragraph(md(t), ST["callout"]))
            body.append(Spacer(1, 2))
    else:
        body.append(Paragraph(md(text), ST["callout"]))
    t = Table([["", body]], colWidths=[5, CONTENT_W - 5])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), bar), ("BACKGROUND", (1, 0), (1, -1), bg),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, -1), 10),
        ("RIGHTPADDING", (1, 0), (1, -1), 10), ("TOPPADDING", (1, 0), (1, -1), 7),
        ("BOTTOMPADDING", (1, 0), (1, -1), 7),
    ]))
    return KeepTogether([t, Spacer(1, 8)])

def PromptBlock(title, text):
    """Monospace, shaded block for copy-paste prompts. Splits across pages at blank lines."""
    blocks = [b for b in text.strip("\n").split("\n\n")]
    head = Paragraph(md(title), ParagraphStyle("pbh", parent=ST["calloutlabel"], textColor=SLATE))
    rows = [[head]]
    for b in blocks:
        lines = [escape(l) for l in b.split("\n")]
        html = "<br/>".join(l if l.strip() else "&nbsp;" for l in lines).replace("  ", "&nbsp;&nbsp;")
        rows.append([Paragraph(html, ST["mono"])])
    t = Table(rows, colWidths=[CONTENT_W], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("BACKGROUND", (0, 1), (-1, -1), LIGHTER),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE), ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, 0), 6), ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 4), ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    ]))
    return [t, Spacer(1, 9)]

def Tbl(header, rows, widths=None, zebra=True, align_right=None, fontsize=None):
    cw = widths or [CONTENT_W / len(header)] * len(header)
    cs = ST["cell"] if fontsize is None else ParagraphStyle("cfs", parent=ST["cell"], fontSize=fontsize, leading=fontsize * 1.3)
    data = [[Paragraph(md(h), ST["cellh"]) for h in header]]
    for r in rows:
        data.append([c if isinstance(c, Flowable) else Paragraph(md(str(c)), cs) for c in r])
    t = Table(data, colWidths=cw, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, RED), ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
    ]
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), LIGHTER))
    t.setStyle(TableStyle(style))
    return [t, Spacer(1, 9)]

def Step(n, title, body, done=None, effort=None, who=None):
    """Numbered step card."""
    meta = " · ".join([x for x in [f"Effort: {effort}" if effort else None, f"Owner: {who}" if who else None] if x])
    right = [Paragraph(md(title), ST["steptitle"])]
    if meta:
        right.append(Paragraph(md(meta).upper(), ST["stepmeta"]))
    if isinstance(body, str):
        body = [body]
    for b in body:
        if isinstance(b, Flowable):
            right.append(b)
        elif isinstance(b, (list, tuple)):
            right.extend(Bullets(b))
        else:
            right.append(Paragraph(md(b), ST["callout"]))
            right.append(Spacer(1, 3))
    if done:
        right.append(Paragraph("<font color='#15803D'><b>Done when:</b></font> " + md(done), ST["callout"]))
    left = Paragraph(str(n), ST["stepnum"])
    t = Table([[left, right]], colWidths=[0.42 * inch, CONTENT_W - 0.42 * inch])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (0, -1), 2), ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (1, 0), (1, -1), 4),
    ]))
    return t

def KV(rows, kw=1.7 * inch):
    data = [[Paragraph(md(k), ST["cellb"]), Paragraph(md(v), ST["cell"])] for k, v in rows]
    t = Table(data, colWidths=[kw, CONTENT_W - kw])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (0, -1), LIGHTER),
    ]))
    return [t, Spacer(1, 8)]

# ---------- document ----------
class ReportDoc(BaseDocTemplate):
    def __init__(self, path, title, subtitle, prepared_for, date_str, logo_path, running_title):
        BaseDocTemplate.__init__(self, path, pagesize=letter, leftMargin=LM, rightMargin=RM,
                                 topMargin=TM, bottomMargin=BM, title=title, author="Prepared for ECI",
                                 subject=subtitle)
        self.meta = dict(title=title, subtitle=subtitle, prepared_for=prepared_for, date_str=date_str,
                         logo=logo_path, running=running_title)
        frame = Frame(LM, BM, CONTENT_W, PAGE_H - TM - BM, id="main", leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="Cover", frames=[frame], onPage=self._cover_page),
            PageTemplate(id="Body", frames=[frame], onPage=self._body_page),
        ])
        self.toc = TableOfContents()
        self.toc.levelStyles = [ST["toc1"], ST["toc2"]]
        self.toc.dotsMinLevel = 0

    def afterFlowable(self, fl):
        if isinstance(fl, _Heading):
            self.notify("TOCEntry", (fl.level, fl.text, self.page))

    def _cover_page(self, canv, doc):
        m = self.meta
        canv.saveState()
        # top band
        canv.setFillColor(INK); canv.rect(0, PAGE_H - 0.55 * inch, PAGE_W, 0.55 * inch, stroke=0, fill=1)
        canv.setFillColor(RED); canv.rect(0, PAGE_H - 0.62 * inch, PAGE_W, 0.07 * inch, stroke=0, fill=1)
        canv.setFillColor(colors.white); canv.setFont("Body-Bold", 9.5)
        canv.drawString(LM, PAGE_H - 0.36 * inch, "ELECTRICAL CONTRACTOR INC.  ·  EST. 1984  ·  COVINGTON, GEORGIA")
        # logo
        try:
            canv.drawImage(m["logo"], LM, PAGE_H - 2.55 * inch, width=1.45 * inch, height=1.45 * inch, mask="auto")
        except Exception:
            pass
        # bottom band
        canv.setFillColor(INK); canv.rect(0, 0, PAGE_W, 1.35 * inch, stroke=0, fill=1)
        canv.setFillColor(colors.white); canv.setFont("Body-Bold", 10)
        canv.drawString(LM, 0.92 * inch, "Prepared for " + m["prepared_for"])
        canv.setFont("Body", 9.2); canv.setFillColor(colors.HexColor("#D4D4D8"))
        canv.drawString(LM, 0.68 * inch, m["date_str"])
        canv.drawString(LM, 0.46 * inch, "Working draft for internal use. Not legal, insurance, or OSHA compliance advice.")
        canv.restoreState()

    def _body_page(self, canv, doc):
        m = self.meta
        canv.saveState()
        canv.setFont("Body", 7.8); canv.setFillColor(MUTED)
        canv.drawString(LM, PAGE_H - 0.55 * inch, m["running"])
        canv.drawRightString(PAGE_W - RM, PAGE_H - 0.55 * inch, "ECI  ·  " + m["date_str"])
        canv.setStrokeColor(LINE); canv.setLineWidth(0.5)
        canv.line(LM, PAGE_H - 0.63 * inch, PAGE_W - RM, PAGE_H - 0.63 * inch)
        canv.line(LM, 0.6 * inch, PAGE_W - RM, 0.6 * inch)
        canv.setFont("Body", 7.8)
        canv.drawString(LM, 0.42 * inch, "Safety CoPilot  ·  safety1.ecinc.us")
        canv.setFillColor(INK); canv.setFont("Body-Bold", 8.2)
        canv.drawRightString(PAGE_W - RM, 0.42 * inch, "Page %d" % doc.page)
        canv.restoreState()

def cover_flowables(doc):
    m = doc.meta
    return [
        Spacer(1, 2.35 * inch),
        Paragraph(md(m["title"]), ST["cover_title"]),
        Rule(RED, 2.5, 4), Spacer(1, 6),
        Paragraph(md(m["subtitle"]), ST["cover_sub"]),
        Spacer(1, 18),
    ]

def render_pngs(pdf_path, out_prefix, pages=None, scale=1.4):
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(pdf_path)
    n = len(pdf)
    idx = pages if pages is not None else range(n)
    outs = []
    for i in idx:
        if i >= n:
            continue
        img = pdf[i].render(scale=scale).to_pil()
        p = f"{out_prefix}-{i+1:02d}.png"
        img.save(p)
        outs.append(p)
    return n, outs
