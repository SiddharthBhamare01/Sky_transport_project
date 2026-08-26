"""
Renders a PNG preview of page 1 of each test PDF in this folder, for the
README and the QA guide doc. Run: python test-samples/_make_previews.py
"""

from pathlib import Path

import pymupdf

HERE = Path(__file__).parent

for pdf_path in sorted(HERE.glob("test_bol_*.pdf")):
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
    out_path = pdf_path.with_suffix(".png")
    pix.save(out_path)
    print("wrote", out_path.name)
