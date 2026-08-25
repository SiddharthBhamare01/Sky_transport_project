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

List a field's name in low_confidence_fields whenever the source text for that \
field is not crisply and unambiguously legible on the page - due to handwriting, \
blur, glare, low resolution, or partial visibility - even if you were able to \
produce a plausible-looking value for it. Legibility, not your confidence in the \
value you produced, is the test: if a human would need to double-check the source \
document to be sure, flag it. Set review_recommended to true whenever \
low_confidence_fields is non-empty, or for any other reason you are not confident \
in the extraction as a whole; briefly explain why in extraction_notes.

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
        if doc.page_count < 1:
            raise ValueError("PDF has no pages")
        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        return pix.tobytes("png")
    finally:
        doc.close()


def extract_from_bytes(file_bytes: bytes, mime_type: str) -> dict:
    if not config.has_api_key():
        raise ExtractionError("no_api_key", "No OPENAI_API_KEY is configured on the server.")

    if mime_type == "application/pdf":
        try:
            image_bytes = _pdf_first_page_to_png(file_bytes)
        except Exception as e:
            raise ExtractionError("invalid_pdf", "Could not read the uploaded PDF (it may be corrupt or empty).") from e
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

    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise ExtractionError("truncated", "The extraction response was cut off before completing. Try again.")

    text = choice.message.content
    if text is None:
        refusal = getattr(choice.message, "refusal", None)
        raise ExtractionError(
            "refused",
            refusal or "The extraction service declined to process this document.",
        )

    try:
        fields = json.loads(text)
    except (TypeError, ValueError) as e:
        raise ExtractionError("parse_error", "Could not parse the extraction result.") from e

    return fields
