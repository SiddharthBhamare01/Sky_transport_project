"""
Generates 3 fictional sample shipment documents used as demo fixtures:
  1. bol_acme_freight.pdf                 - clean printed Bill of Lading (PDF)
  2. bol_northstar_logistics_photo.jpg    - same style, skewed/noisy to simulate a phone photo
  3. pod_acme_freight_delivery.png        - Proof of Delivery with a drawn signature

All company names/addresses are fictional and do not represent any real business.
Run: python samples/generate_samples.py
"""

import math
import random
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT_DIR = Path(__file__).parent


def draw_bol_pdf(path: Path, shipper, consignee, carrier, load_number,
                  pro_number, pickup_date, weight, pieces, commodity):
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    y = height - 0.75 * inch

    c.setFont("Helvetica-Bold", 16)
    c.drawString(0.75 * inch, y, "BILL OF LADING")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 0.75 * inch, y, f"Load #: {load_number}")
    y -= 14
    c.drawRightString(width - 0.75 * inch, y, f"PRO #: {pro_number}")
    y -= 30

    def box(title, lines, top):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(0.75 * inch, top, title)
        c.rect(0.75 * inch, top - 14 - 14 * len(lines), 3.3 * inch, 14 * len(lines) + 10)
        c.setFont("Helvetica", 9)
        yy = top - 14
        for line in lines:
            c.drawString(0.85 * inch, yy, line)
            yy -= 14
        return top - 14 - 14 * len(lines) - 20

    y = box("SHIP FROM", shipper, y)
    y = box("SHIP TO", consignee, y)

    c.setFont("Helvetica", 9)
    c.drawString(0.75 * inch, y, f"Carrier: {carrier}")
    y -= 16
    c.drawString(0.75 * inch, y, f"Pickup Date: {pickup_date}")
    y -= 24

    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.75 * inch, y, "FREIGHT DESCRIPTION")
    y -= 16
    table_top = y
    col_x = [0.75 * inch, 2.2 * inch, 4.0 * inch, 5.4 * inch, 6.6 * inch]
    headers = ["Pieces", "Commodity", "Weight", "Class", "Terms"]
    c.setFont("Helvetica-Bold", 9)
    for x, h in zip(col_x, headers):
        c.drawString(x, y, h)
    y -= 4
    c.line(0.75 * inch, y, width - 0.75 * inch, y)
    y -= 16
    c.setFont("Helvetica", 9)
    row = [str(pieces), commodity, f"{weight} lb", "70", "Prepaid"]
    for x, v in zip(col_x, row):
        c.drawString(x, y, v)
    y -= 10
    c.rect(0.75 * inch, y, width - 1.5 * inch, table_top - y + 20)

    y -= 60
    c.setFont("Helvetica", 9)
    c.drawString(0.75 * inch, y, "Shipper Signature: ____________________________")
    c.drawString(4.2 * inch, y, "Date: __________")

    c.showPage()
    c.save()


def photo_effect(img: Image.Image, angle=3.5, noise=18) -> Image.Image:
    img = img.rotate(angle, expand=True, fillcolor=(235, 232, 225))
    px = img.load()
    w, h = img.size
    for _ in range(int(w * h * 0.02)):
        x = random.randrange(w)
        yv = random.randrange(h)
        n = random.randint(-noise, noise)
        r, g, b = px[x, yv][:3]
        px[x, yv] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    return img


def draw_bol_image(path: Path, shipper, consignee, carrier, load_number,
                    pro_number, pickup_date, weight, pieces, commodity, as_photo=False):
    W, H = 1000, 1300
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    try:
        font_bold = ImageFont.truetype("arialbd.ttf", 30)
        font = ImageFont.truetype("arial.ttf", 20)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font_bold = font = font_small = ImageFont.load_default()

    y = 40
    d.text((40, y), "BILL OF LADING", font=font_bold, fill="black")
    d.text((W - 300, y), f"Load #: {load_number}", font=font_small, fill="black")
    d.text((W - 300, y + 26), f"PRO #: {pro_number}", font=font_small, fill="black")
    y += 70

    def box(title, lines, top):
        d.text((40, top), title, font=font, fill="black")
        d.rectangle([40, top + 28, 620, top + 28 + 24 * len(lines) + 14], outline="black", width=2)
        yy = top + 40
        for line in lines:
            d.text((55, yy), line, font=font_small, fill="black")
            yy += 24
        return top + 28 + 24 * len(lines) + 14 + 30

    y = box("SHIP FROM", shipper, y)
    y = box("SHIP TO", consignee, y)

    d.text((40, y), f"Carrier: {carrier}", font=font_small, fill="black")
    y += 28
    d.text((40, y), f"Pickup Date: {pickup_date}", font=font_small, fill="black")
    y += 40

    d.text((40, y), "FREIGHT DESCRIPTION", font=font, fill="black")
    y += 30
    d.rectangle([40, y, W - 40, y + 60], outline="black", width=2)
    d.text((55, y + 18), f"{pieces} pcs   {commodity}   {weight} lb   Class 70   Prepaid",
            font=font_small, fill="black")
    y += 100

    d.text((40, y), "Shipper Signature: ____________________________", font=font_small, fill="black")
    d.text((550, y), "Date: __________", font=font_small, fill="black")

    if as_photo:
        img = photo_effect(img)
        img.save(path, "JPEG", quality=72)
    else:
        img.save(path, "PNG")


def draw_pod_png(path: Path, shipper, consignee, load_number, delivery_date, weight):
    W, H = 1000, 700
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    try:
        font_bold = ImageFont.truetype("arialbd.ttf", 30)
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font_bold = font = ImageFont.load_default()

    d.text((40, 30), "PROOF OF DELIVERY", font=font_bold, fill="black")
    d.text((40, 90), f"Load #: {load_number}", font=font, fill="black")
    d.text((40, 125), f"Shipper: {shipper[0]}", font=font, fill="black")
    d.text((40, 160), f"Consignee: {consignee[0]}", font=font, fill="black")
    d.text((40, 195), f"Delivered: {delivery_date}", font=font, fill="black")
    d.text((40, 230), f"Weight received: {weight} lb", font=font, fill="black")

    d.text((40, 300), "Received in good condition by:", font=font, fill="black")
    d.line([(40, 400), (500, 400)], fill="black", width=2)

    # scribble signature
    random.seed(7)
    px, py = 60, 380
    points = [(px, py)]
    for _ in range(40):
        px += random.randint(5, 15)
        py += random.randint(-25, 25)
        points.append((px, py))
    d.line(points, fill="black", width=3, joint="curve")
    d.text((40, 410), "Signature", font=font, fill="black")

    img.save(path, "PNG")


if __name__ == "__main__":
    random.seed(42)

    draw_bol_pdf(
        OUT_DIR / "bol_acme_freight.pdf",
        shipper=["Acme Freight LLC", "1200 Industrial Pkwy", "Modesto, CA 95351"],
        consignee=["Bluepeak Retail Co.", "88 Commerce Dr", "Reno, NV 89501"],
        carrier="Acme Freight LLC",
        load_number="LD-48213",
        pro_number="PRO-990214",
        pickup_date="2026-08-20",
        weight=4200,
        pieces=12,
        commodity="Palletized dry goods",
    )

    draw_bol_image(
        OUT_DIR / "bol_northstar_logistics_photo.jpg",
        shipper=["Northstar Logistics", "455 Freightway Rd", "Stockton, CA 95206"],
        consignee=["Cascade Wholesale Foods", "22 Market St", "Sacramento, CA 95814"],
        carrier="Northstar Logistics",
        load_number="LD-77120",
        pro_number="PRO-114455",
        pickup_date="2026-08-21",
        weight=6100,
        pieces=8,
        commodity="Refrigerated produce",
        as_photo=True,
    )

    draw_pod_png(
        OUT_DIR / "pod_acme_freight_delivery.png",
        shipper=["Acme Freight LLC"],
        consignee=["Harbor & Vine Cafe Supply"],
        load_number="LD-48213",
        delivery_date="2026-08-22",
        weight=4180,
    )

    print("Generated 3 sample documents in", OUT_DIR)
