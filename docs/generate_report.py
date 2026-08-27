"""
Builds a detailed project report PDF for handover.
Run: python docs/generate_report.py
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, HRFlowable, ListFlowable, ListItem, KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.pdfgen import canvas as canvas_mod

HERE = Path(__file__).parent
OUT_PATH = HERE / "Project_Report.pdf"

INK = colors.HexColor("#171b26")
DIM = colors.HexColor("#555b66")
ACCENT = colors.HexColor("#4f5fe8")
ACCENT_DARK = colors.HexColor("#3c4bd6")
ACCENT_SOFT = colors.HexColor("#eef0fe")
BORDER = colors.HexColor("#d8dce1")
WARN_BG = colors.HexColor("#fff6e5")
WARN_BORDER = colors.HexColor("#e8b93b")
GOOD = colors.HexColor("#1a7f4b")

styles = getSampleStyleSheet()
title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], fontSize=26, leading=32, textColor=INK)
subtitle_style = ParagraphStyle("ReportSubtitle", parent=styles["Normal"], fontSize=13, textColor=DIM, alignment=TA_CENTER, spaceAfter=6)
meta_style = ParagraphStyle("Meta", parent=styles["Normal"], fontSize=10.5, textColor=DIM, alignment=TA_CENTER)
h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceBefore=6, spaceAfter=10, textColor=INK)
h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12.5, spaceBefore=14, spaceAfter=6, textColor=ACCENT_DARK)
body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14.5, spaceAfter=8, textColor=INK)
bullet_style = ParagraphStyle("Bullet", parent=body, spaceAfter=4)
caption = ParagraphStyle("Caption", parent=styles["Normal"], fontSize=8.5, textColor=DIM, alignment=TA_CENTER, spaceBefore=4, spaceAfter=14)
quote = ParagraphStyle("Quote", parent=body, textColor=DIM, leftIndent=12, borderColor=BORDER, borderWidth=0, spaceAfter=10)


def architecture_diagram():
    d = Drawing(480, 160)

    def box(x, y, w, h, label, sub=None, fill=ACCENT_SOFT, text_color=ACCENT_DARK):
        d.add(Rect(x, y, w, h, rx=6, ry=6, fillColor=fill, strokeColor=ACCENT_DARK, strokeWidth=1))
        d.add(String(x + w / 2, y + h / 2 + (4 if sub else -2), label, fontName="Helvetica-Bold",
                      fontSize=9.5, fillColor=text_color, textAnchor="middle"))
        if sub:
            d.add(String(x + w / 2, y + h / 2 - 10, sub, fontName="Helvetica",
                          fontSize=7.5, fillColor=DIM, textAnchor="middle"))

    def arrow(x1, y1, x2, y2, label=None, label_dx=0):
        d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#8891a5"), strokeWidth=1.2))
        dx, dy = x2 - x1, y2 - y1
        length = max((dx ** 2 + dy ** 2) ** 0.5, 0.001)
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        head = 5
        tip = (x2, y2)
        left = (x2 - head * ux + head * 0.5 * px, y2 - head * uy + head * 0.5 * py)
        right = (x2 - head * ux - head * 0.5 * px, y2 - head * uy - head * 0.5 * py)
        d.add(Polygon([tip[0], tip[1], left[0], left[1], right[0], right[1]],
                       fillColor=colors.HexColor("#8891a5"), strokeColor=None))
        if label:
            d.add(String((x1 + x2) / 2 + label_dx, (y1 + y2) / 2 + 4, label,
                          fontName="Helvetica", fontSize=7, fillColor=DIM, textAnchor="middle"))

    box(10, 80, 110, 50, "Browser", "static/*.js — no build step")
    box(190, 110, 130, 40, "Supabase", "Auth + Postgres (shipment_rows)", fill=colors.HexColor("#e3f8ec"), text_color=GOOD)
    box(190, 40, 130, 40, "FastAPI on Render", "/api/extract, /api/notify/*")
    box(370, 80, 100, 40, "OpenAI", "vision model")
    box(370, 10, 100, 40, "Gmail SMTP", "OAuth2 (XOAUTH2)")

    arrow(120, 115, 190, 130, "auth, read/write rows", label_dx=-10)
    arrow(120, 95, 190, 60, "upload file / notify", label_dx=10)
    arrow(320, 60, 370, 95, "vision call")
    arrow(320, 45, 370, 30, "send email")

    return d


def screenshot_flow(img_path, width_in, caption_text):
    from PIL import Image as PILImage
    w_px, h_px = PILImage.open(img_path).size
    w = width_in * inch
    h = w * (h_px / w_px)
    return [Image(str(img_path), width=w, height=h), Paragraph(caption_text, caption)]


def header_footer(c: canvas_mod.Canvas, doc):
    c.saveState()
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(0.75 * inch, letter[1] - 0.55 * inch, letter[0] - 0.75 * inch, letter[1] - 0.55 * inch)
    c.setFont("Helvetica", 8)
    c.setFillColor(DIM)
    c.drawString(0.75 * inch, letter[1] - 0.48 * inch, "Sky Transport — Shipment Document Data Extractor")
    c.drawRightString(letter[0] - 0.75 * inch, letter[1] - 0.48 * inch, "AUTOMATE Track — Technical Assessment Report")
    c.line(0.75 * inch, 0.6 * inch, letter[0] - 0.75 * inch, 0.6 * inch)
    c.drawString(0.75 * inch, 0.45 * inch, "Sky Transport Solutions")
    c.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, f"Page {doc.page}")
    c.restoreState()


def cover_accent():
    d = Drawing(480, 6)
    d.add(Rect(140, 0, 200, 4, fillColor=ACCENT, strokeColor=None))
    d.hAlign = "CENTER"
    return d


def cover_page(story):
    story.append(Spacer(1, 1.6 * inch))
    story.append(cover_accent())
    story.append(Spacer(1, 18))
    story.append(Paragraph("Sky Transport", title_style))
    story.append(Paragraph("Shipment Document Data Extractor", ParagraphStyle(
        "T2", parent=title_style, fontSize=17, textColor=ACCENT_DARK, spaceBefore=0, spaceAfter=18)))
    story.append(Paragraph(
        "A web application that reads a Bill of Lading or Proof of Delivery — a PDF or a phone "
        "photo — and extracts the shipment fields a dispatcher would otherwise retype by hand.",
        subtitle_style,
    ))
    story.append(Spacer(1, 26))

    info_table = Table([
        ["Project track", "AUTOMATE — Sky Transport Solutions technical assessment"],
        ["Author", "Siddharth Bhamare"],
        ["Report date", "August 2026"],
        ["Live application", "https://sky-transport-project.vercel.app"],
        ["Backend API", "https://sky-transport-project.onrender.com"],
        ["Source repository", "github.com/SiddharthBhamare01/Sky_transport_project"],
        ["License", "MIT"],
    ], colWidths=[1.7 * inch, 4.3 * inch])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), ACCENT_DARK),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("BACKGROUND", (0, 0), (0, -1), ACCENT_SOFT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(KeepTogether([Spacer(1, 6), info_table]))
    story.append(PageBreak())


def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(t, bullet_style), leftIndent=6) for t in items],
        bulletType="bullet", start="•", leftIndent=14,
    )


story = []
cover_page(story)

# --- Executive summary ---
story.append(Paragraph("Executive Summary", h1))
story.append(Paragraph(
    "This project automates a small but recurring manual task at a trucking/logistics operator: "
    "retyping shipper, consignee, load number, dates, weight, and commodity fields off of paper or "
    "photographed Bill of Lading (BOL) and Proof of Delivery (POD) documents into a tracking "
    "spreadsheet. Rather than building a brittle OCR/template pipeline, the solution uses a "
    "multimodal LLM call constrained to a strict JSON schema, keeping a human in the loop for every "
    "field before it is saved. The application is fully deployed and live: a FastAPI backend on "
    "Render, a static frontend on Vercel, and Supabase providing authentication and a shared, "
    "multi-user Postgres-backed queue.",
    body,
))
story.append(Paragraph(
    "The result is a working, deployed, mobile-capable tool — not a prototype — including real "
    "accounts, password reset, email notifications, camera-capture support for field use, and a "
    "CI pipeline, alongside an honest account of where the extraction's confidence-flagging still "
    "falls short (see Testing &amp; Results).",
    body,
))

# --- Problem statement ---
story.append(Paragraph("Problem Statement", h1))
story.append(Paragraph(
    "At a small trucking/logistics operator, dispatchers regularly retype the same handful of "
    "fields off of BOL and POD paperwork — PDFs from carriers, or phone photos taken at the dock — "
    "into a tracking spreadsheet. It is the same few minutes of manual copying per document, "
    "several times a day, and it is exactly the kind of repetitive task that is easy to get wrong "
    "under time pressure: a transposed digit on a load number is a real problem when someone goes "
    "looking for that shipment later.",
    body,
))

# --- Solution overview ---
story.append(Paragraph("Solution Overview", h1))
story.append(Paragraph(
    "Rather than a rigid template-matching OCR pipeline — brittle across different carriers' "
    "document layouts, and slow to harden in the time available — the solution uses a multimodal "
    "LLM call constrained to a fixed JSON schema. This gets layout-agnostic extraction \"for free\" "
    "via prompting, while the strict schema keeps the output predictable enough to build a UI "
    "around. The design leans on keeping a human in the loop: the model is instructed to say "
    "\"I don't know\" rather than guess, and every field stays editable before anything is saved.",
    body,
))
story.append(Paragraph("Key features", h2))
story.append(bullets([
    "LLM-based extraction with a strict JSON schema — no brittle OCR/regex templates.",
    "Three ways to get a document in: drag-and-drop, file browser, or a dedicated camera-capture button for mobile field use.",
    "HEIC/HEIF support — the default photo format on iPhones, transcoded server-side before extraction.",
    "Per-field low-confidence flagging, not just one document-level flag.",
    "Accounts and a shared queue — Google or email/password sign-in via Supabase Auth, with password reset.",
    "Transactional email notifications (welcome, password-changed, shipment-added) sent via Gmail over OAuth2, always to the token's own verified address — never a free-text recipient.",
    "Sample/demo mode — three fixture documents let anyone demo the full workflow with zero API calls.",
    "CSV export, client-side, ready to paste into a spreadsheet.",
    "Mobile-first refinements: ~44px touch targets, offline/slow-network-aware error messages, and loading feedback for the backend's free-tier cold start.",
]))
story.append(PageBreak())

# --- Architecture ---
story.append(Paragraph("Architecture &amp; Tech Stack", h1))
story.append(Paragraph(
    "The frontend talks to Supabase directly for data (authentication, reading/writing shipment "
    "rows) using a public, Row-Level-Security-protected key. The FastAPI backend stays stateless "
    "and is responsible for exactly two things: calling OpenAI, and sending the three notification "
    "emails — which need secrets that must never reach the browser.",
    body,
))
story.append(KeepTogether([architecture_diagram(), Paragraph("Request flow between the browser, Supabase, the FastAPI backend, and external services.", caption)]))

tech_rows = [
    ["Layer", "Choice"],
    ["Backend", "Python, FastAPI, Uvicorn"],
    ["Extraction", "OpenAI vision model (gpt-4o-mini by default), structured JSON-schema output"],
    ["Document handling", "PyMuPDF (PDF → image), Pillow + pillow-heif (HEIC → PNG)"],
    ["Frontend", "Vanilla HTML/CSS/JS — no build step, no framework"],
    ["Auth &amp; database", "Supabase (Postgres + Auth: Google OAuth and email/password)"],
    ["Email", "Gmail SMTP via OAuth2 (XOAUTH2), verified with a Supabase JWT server-side"],
    ["Hosting", "Render (backend API), Vercel (static frontend)"],
    ["CI", "GitHub Actions — backend import/compile check, frontend JS syntax check"],
]
tech_table = Table([[Paragraph(c, body) for c in row] for row in tech_rows], colWidths=[1.5 * inch, 4.5 * inch])
tech_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT_DARK),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("BACKGROUND", (0, 1), (0, -1), ACCENT_SOFT),
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(Spacer(1, 10))
story.append(tech_table)
story.append(PageBreak())

# --- Screenshots ---
story.append(Paragraph("Application Walkthrough", h1))
story.append(Paragraph(
    "Screenshots below are from the live, deployed application (stubbed session for illustration).",
    body,
))
story.append(Paragraph("Sign in", h2))
story.append(Paragraph("Email/password or Google, via Supabase Auth. Login is required to use the extractor, which is what allows every row in the shared queue to carry a genuine, verified owner.", body))
for flowable in screenshot_flow(HERE / "screenshot-login.png", 3.6, "Figure 1 — Sign-in screen"):
    story.append(flowable)

story.append(Paragraph("Extraction results and per-field confidence flagging", h2))
story.append(Paragraph(
    "The screenshot below demonstrates the core feature in action: <b>delivery_date</b> and "
    "<b>signature_present</b> are individually highlighted because the source document doesn't "
    "clearly show them, with a plain-language explanation banner above the form. The shared queue "
    "table below carries the same flag through on a saved row, so a dispatcher scanning the table "
    "later can still see which rows need a second look.",
    body,
))
for flowable in screenshot_flow(HERE / "screenshot-extraction.png", 5.6, "Figure 2 — Extraction results with low-confidence flags and the shared queue"):
    story.append(flowable)
story.append(PageBreak())

mobile_section = [
    Paragraph("Mobile field use", h2),
    Paragraph(
        "On a phone, a dedicated camera-capture button (using the HTML capture attribute) opens the "
        "rear camera directly, and HEIC photos — the default format on iPhone — are supported end to "
        "end. Interactive elements are sized to the ~44px minimum recommended touch target.",
        body,
    ),
] + screenshot_flow(HERE / "screenshot-mobile.png", 2.0, "Figure 3 — Mobile view with camera capture")
story.append(KeepTogether(mobile_section))
story.append(PageBreak())

# --- Testing & Results ---
story.append(Paragraph("Testing &amp; Results", h1))
story.append(Paragraph(
    "All three sample documents were run through the real pipeline (gpt-4o-mini, live API key, not "
    "mocked) twice — once with the original single-flag design, once after adding "
    "low_confidence_fields.",
    body,
))
story.append(Paragraph("Run 1 — single review_recommended flag", h2))
story.append(Paragraph(
    "The clean printed PDF extracted perfectly. The POD also extracted cleanly, correctly leaving "
    "fields not present on a POD as null. The noisy/skewed \"phone photo\" fixture is where it "
    "broke: the model misread \"Freightway Rd\" as \"Freighthay Rd\" and did <b>not</b> set "
    "review_recommended to flag it — a dispatcher trusting that flag would have missed a bad row.",
    body,
))
story.append(Paragraph("Run 2 — after adding low_confidence_fields", h2))
story.append(Paragraph(
    "The clean PDF still extracted perfectly with nothing flagged. The fix did not fully work, "
    "though: on a re-run of the noisy photo, the model produced yet another misread of the same "
    "street name (\"Freighthway Rd\", a third variant across runs, confirming the model is "
    "non-deterministic here) and again did <b>not</b> flag shipper_address as low-confidence. "
    "Separately, on the POD it <i>over</i>-flagged: six fields correctly left null (because they "
    "are not on a POD at all) were also listed as low-confidence, conflating \"structurally "
    "absent\" with \"illegible.\"",
    body,
))
story.append(Paragraph(
    "This is an honest, partial result rather than a fixed one — the feature changed the failure "
    "mode without eliminating it. A second verification pass on flagged fields, or separating "
    "\"not applicable\" from \"illegible\" directly in the schema, is the recommended next "
    "iteration rather than trusting the current flag as-is.",
    body,
))
story.append(Paragraph("Additional verification performed this session", h2))
story.append(bullets([
    "A HEIC test photo was generated and run through the real extraction pipeline end to end (direct call and full HTTP path), correctly matching ground-truth field values.",
    "Camera-capture wiring was verified with a stubbed-session Playwright test plus a real local extraction round trip, since no physical phone camera was available to test with directly.",
    "Mobile layout, touch-target sizing, offline handling, and the Render cold-start loading indicator were each verified with targeted automated browser tests, not just visual inspection.",
    "Three additional fictional test PDFs and a QA guide document (test-samples/) were produced for exercising the live upload path independently of the built-in demo fixtures.",
]))

# --- Known limitations ---
story.append(Paragraph("Known Limitations &amp; Future Work", h1))
story.append(bullets([
    "Single/small documents only — no multi-page batch handling.",
    "Per-field confidence flagging is a partial fix, not a full one (see Testing &amp; Results above) — a second verification pass or schema-level separation of \"not applicable\" vs. \"illegible\" is the recommended next step.",
    "PDF preview uses an iframe; browsers without a built-in PDF viewer fall back to an \"Open PDF in new tab\" link.",
    "No mobile \"card view\" for the shared table yet — on a narrow phone screen it is a horizontally-scrollable wide table rather than a stacked layout.",
    "No offline draft persistence — a backgrounded mobile tab discarded by the OS mid-review will lose in-progress, not-yet-saved field edits.",
    "Session-expiry mid-review surfaces as a generic save error rather than an automatic re-login prompt that preserves the in-progress review.",
    "With more time: batch upload, duplicate/date-sanity validation against existing rows, and a direct export/integration into whatever system the dispatch team already uses instead of a CSV hop.",
]))

# --- Deployment ---
story.append(Paragraph("Deployment", h1))
story.append(Paragraph(
    "The application is deployed with continuous delivery already wired up: Render and Vercel both "
    "auto-deploy from the main branch on every push, and a GitHub Actions workflow runs a "
    "build/syntax gate on every push and pull request, independent of the deploy itself.",
    body,
))
deploy_rows = [
    ["Component", "Platform", "Notes"],
    ["Frontend", "Vercel", "Static site, Root Directory set to static/, no build step"],
    ["Backend API", "Render", "Free tier — cold-starts (~50s) after inactivity"],
    ["Database &amp; Auth", "Supabase", "Postgres + Auth (Google, email/password), Row Level Security enforced"],
    ["Email delivery", "Gmail (OAuth2)", "Backend-only secrets, never exposed to the browser"],
    ["CI", "GitHub Actions", "Runs on every push/PR, independent of the native Render/Vercel deploy"],
]
deploy_table = Table([[Paragraph(c, body) for c in row] for row in deploy_rows], colWidths=[1.3 * inch, 1.1 * inch, 3.6 * inch])
deploy_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT_DARK),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("BACKGROUND", (0, 1), (0, -1), ACCENT_SOFT),
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(deploy_table)
story.append(PageBreak())

# --- Conclusion ---
story.append(Paragraph("Conclusion &amp; Key Takeaways", h1))
story.append(bullets([
    "A schema-constrained multimodal LLM call is a practical substitute for a template-matching OCR pipeline on documents whose layout varies by sender — it generalized across three visually distinct fixtures (a clean PDF, a skewed/noisy phone photo, and a structurally different POD) without any per-layout code.",
    "Self-reported confidence is not reliable on its own: a single document-level \"review recommended\" flag missed a genuine misread in testing. Reframing it as a legibility check on individual fields (low_confidence_fields) changed, but did not eliminate, that failure mode — evidence that a second verification pass or a stricter schema distinction is needed before this flag should be fully trusted.",
    "Keeping a human in the loop — every field editable before saving, null over guessing — is a deliberate design choice that limits the damage of the extraction model's remaining unreliability, rather than a workaround for it.",
    "Adding accounts was driven by a concrete constraint, not scope creep for its own sake: a safe \"who gets notified\" answer required a real, verified identity, which a stateless, database-free design could not provide.",
]))
story.append(Paragraph("Illustrative business-impact estimate", h2))
story.append(Paragraph(
    "Using representative assumptions rather than measured data: if manually transcribing one "
    "document takes a dispatcher roughly 3 minutes, and a small dispatch team processes on the "
    "order of 20 such documents per day, automating extraction and review down to under a minute "
    "per document would save on the order of <b>~40&ndash;50 minutes per day</b>, or roughly "
    "<b>3&ndash;4 hours per week</b>, for that team — before accounting for the reduction in "
    "transcription errors that a human-reviewed, schema-validated pipeline provides over manual "
    "retyping.",
    body,
))

story.append(HRFlowable(width="100%", color=BORDER, thickness=1, spaceBefore=16, spaceAfter=10))
story.append(Paragraph(
    "Full technical documentation, setup instructions, and the complete honest testing narrative "
    "are maintained in the project's README.md in the source repository linked on the cover page.",
    caption,
))

doc = SimpleDocTemplate(
    str(OUT_PATH), pagesize=letter,
    leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.85 * inch, bottomMargin=0.85 * inch,
    title="Sky Transport — Project Report", author="Siddharth Bhamare",
)
doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=header_footer)
print("wrote", OUT_PATH.name)
