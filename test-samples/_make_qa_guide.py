"""
Builds a polished, email-shareable QA guide PDF covering the three test
fixtures in this folder. Run: python test-samples/_make_qa_guide.py
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, HRFlowable,
)

HERE = Path(__file__).parent
OUT_PATH = HERE / "QA_Test_Fixtures_Guide.pdf"

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleBig", parent=styles["Title"], fontSize=22, spaceAfter=6)
subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=12, textColor=colors.HexColor("#555b66"), spaceAfter=24)
h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceBefore=18, spaceAfter=8, textColor=colors.HexColor("#2b2f38"))
body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10.5, leading=15, spaceAfter=10)
caption = ParagraphStyle("Caption", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#667085"), spaceAfter=14)
cell_label = ParagraphStyle("CellLabel", parent=styles["Normal"], fontSize=9.5, fontName="Helvetica-Bold", textColor=colors.HexColor("#3c4bd6"))
cell_value = ParagraphStyle("CellValue", parent=styles["Normal"], fontSize=9.5, leading=12)

FIXTURES = [
    {
        "file": "test_bol_1_summit_hardware.pdf",
        "image": "test_bol_1_summit_hardware.png",
        "title": "1. Summit Hardware Supply → Redwood Building Co.",
        "rows": [
            ("Document type", "BOL"),
            ("Shipper", "Summit Hardware Supply, 310 Foundry Ave, Boise, ID 83702"),
            ("Consignee", "Redwood Building Co., 77 Timberline Rd, Eugene, OR 97401"),
            ("Carrier", "Summit Hardware Supply"),
            ("Load #", "LD-30871"),
            ("PRO #", "PRO-220198"),
            ("Pickup date", "2026-08-24"),
            ("Weight", "5400 lb"),
            ("Pieces", "18"),
            ("Commodity", "Steel fasteners, boxed"),
            ("Freight terms", "Prepaid"),
            ("Signature present", "No (unsigned line)"),
        ],
    },
    {
        "file": "test_bol_2_pacific_textiles.pdf",
        "image": "test_bol_2_pacific_textiles.png",
        "title": "2. Pacific Textiles Inc. → Sunrise Garment Outlet",
        "rows": [
            ("Document type", "BOL"),
            ("Shipper", "Pacific Textiles Inc., 902 Millwork Ln, Fresno, CA 93701"),
            ("Consignee", "Sunrise Garment Outlet, 14 Harbor Blvd, Long Beach, CA 90802"),
            ("Carrier", "Pacific Textiles Inc."),
            ("Load #", "LD-55602"),
            ("PRO #", "PRO-336102"),
            ("Pickup date", "2026-08-25"),
            ("Weight", "2750 lb"),
            ("Pieces", "40"),
            ("Commodity", "Cotton fabric rolls"),
            ("Freight terms", "Prepaid"),
            ("Signature present", "No (unsigned line)"),
        ],
    },
    {
        "file": "test_bol_3_greenline_produce.pdf",
        "image": "test_bol_3_greenline_produce.png",
        "title": "3. Greenline Produce Co. → Metro Fresh Markets",
        "rows": [
            ("Document type", "BOL"),
            ("Shipper", "Greenline Produce Co., 48 Orchard Rd, Salinas, CA 93901"),
            ("Consignee", "Metro Fresh Markets, 610 Riverside Ave, San Jose, CA 95112"),
            ("Carrier", "Greenline Produce Co."),
            ("Load #", "LD-61944"),
            ("PRO #", "PRO-447213"),
            ("Pickup date", "2026-08-26"),
            ("Weight", "8900 lb"),
            ("Pieces", "60"),
            ("Commodity", "Refrigerated leafy greens"),
            ("Freight terms", "Prepaid"),
            ("Signature present", "No (unsigned line)"),
        ],
    },
]

TABLE_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef0fe")),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8dce1")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
])

story = []

story.append(Paragraph("Sky Transport — QA Test Fixtures Guide", title_style))
story.append(Paragraph(
    "Manual test documents for the Shipment Document Data Extractor, for exercising the live "
    "upload &amp; extraction path end to end.",
    subtitle_style,
))
story.append(HRFlowable(width="100%", color=colors.HexColor("#d8dce1"), thickness=1, spaceAfter=16))

story.append(Paragraph("Purpose", h2))
story.append(Paragraph(
    "The app ships with built-in “try a sample” buttons that replay pre-recorded extraction "
    "results without calling OpenAI, so a reviewer can see the workflow even without an API key "
    "configured. The three fictional Bills of Lading in this guide are for the opposite purpose: "
    "uploading a real file through the dropzone and exercising the actual live extraction call "
    "(<b>POST /api/extract</b> → OpenAI’s vision model → parsed JSON fields), end to end.",
    body,
))
story.append(Paragraph(
    "For each fixture below, the “Expected fields” table is the ground truth the document was "
    "generated from — compare it against what the app actually extracts to confirm the live "
    "pipeline is producing correct results.",
    body,
))

story.append(Paragraph("How to test", h2))
for i, step in enumerate([
    "Open the deployed app and log in (email/password or Google).",
    "Drop one of the three PDFs into the upload dropzone (or click “browse”) and click Extract.",
    "Compare the extracted fields shown in the form against the Expected fields table for that document.",
    "Click “Add to table” to also exercise the Supabase insert and the “shipment added” notification email.",
], 1):
    story.append(Paragraph(f"{i}. {step}", body))

story.append(PageBreak())

for fx in FIXTURES:
    story.append(Paragraph(fx["title"], h2))
    story.append(Paragraph(f"Source file: <font face='Courier'>{fx['file']}</font>", caption))
    img_path = HERE / fx["image"]
    img = Image(str(img_path), width=2.9 * inch, height=2.9 * inch * (1584 / 1224))
    wrapped_rows = [[Paragraph(k, cell_label), Paragraph(v, cell_value)] for k, v in fx["rows"]]
    table = Table(wrapped_rows, colWidths=[1.15 * inch, 3.15 * inch])
    table.setStyle(TABLE_STYLE)
    row = Table([[img, table]], colWidths=[3.1 * inch, 4.4 * inch])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(row)
    story.append(Spacer(1, 20))

story.append(HRFlowable(width="100%", color=colors.HexColor("#d8dce1"), thickness=1, spaceBefore=10, spaceAfter=10))
story.append(Paragraph(
    "All company names and addresses in this document are fictional and do not represent any real business.",
    caption,
))

doc = SimpleDocTemplate(
    str(OUT_PATH), pagesize=letter,
    leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.75 * inch, bottomMargin=0.75 * inch,
)
doc.build(story)
print("wrote", OUT_PATH.name)
