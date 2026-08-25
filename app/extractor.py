import base64
import json

import openai
import pymupdf

from . import config
from .schema import BOL_SCHEMA

SYSTEM_PROMPT = """You are extracting shipment data from a US trucking Bill of \
Lading (BOL) or Proof of Delivery (POD) document for a dispatch team, so the data \
can be entered into a tracking spreadsheet without manual retyping.

Extract only what is visibly printed or handwritten on the document. Never infer \
or guess a value that is not legible or not present - set it to null instead. \
Never invent a value to fill a field.

Set review_recommended to true whenever handwriting is ambiguous, a field is only \
partially visible, the image quality makes a value uncertain, or you are otherwise \
not confident in what you read. When review_recommended is true, briefly explain \
why in extraction_notes.

Dates should be normalized to YYYY-MM-DD when the source format allows it \
unambiguously; otherwise leave the value as printed or set it to null."""


class ExtractionError(Exception):
    def __init__(self, kind: str, message: str):
        self.kind = kind
        self.message = message
        super().__init__(message)


def _pdf_first_page_to_png(file_bytes: bytes) -> bytes:
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    try:
        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        return pix.tobytes("png")
    finally:
        doc.close()


def extract_from_bytes(file_bytes: bytes, mime_type: str) -> dict:
    if not config.has_api_key():
        raise ExtractionError("no_api_key", "No OPENAI_API_KEY is configured on the server.")

    if mime_type == "application/pdf":
        image_bytes = _pdf_first_page_to_png(file_bytes)
        image_mime = "image/png"
    else:
        image_bytes = file_bytes
        image_mime = mime_type

    b64_data = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{image_mime};base64,{b64_data}"

    client = openai.OpenAI(api_key=config.OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model=config.EXTRACTION_MODEL,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract the shipment data from this document."},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "bol_extraction",
                    "schema": BOL_SCHEMA,
                    "strict": True,
                },
            },
        )
    except openai.RateLimitError as e:
        raise ExtractionError("rate_limited", "The extraction service is rate-limited right now. Please try again shortly.") from e
    except openai.APIConnectionError as e:
        raise ExtractionError("connection_error", "Could not reach the extraction service.") from e
    except openai.APIStatusError as e:
        raise ExtractionError("api_error", f"Extraction service returned an error ({e.status_code}).") from e

    text = response.choices[0].message.content
    try:
        fields = json.loads(text)
    except json.JSONDecodeError as e:
        raise ExtractionError("parse_error", "Could not parse the extraction result.") from e

    return fields
