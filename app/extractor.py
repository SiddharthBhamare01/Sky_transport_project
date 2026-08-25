import base64
import json

import anthropic

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


def extract_from_bytes(file_bytes: bytes, mime_type: str) -> dict:
    if not config.has_api_key():
        raise ExtractionError("no_api_key", "No ANTHROPIC_API_KEY is configured on the server.")

    block_type = "document" if mime_type == "application/pdf" else "image"
    b64_data = base64.b64encode(file_bytes).decode("ascii")

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=config.EXTRACTION_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": block_type,
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": b64_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Extract the shipment data from this document.",
                        },
                    ],
                }
            ],
            output_config={"format": {"type": "json_schema", "schema": BOL_SCHEMA}},
        )
    except anthropic.RateLimitError as e:
        raise ExtractionError("rate_limited", "The extraction service is rate-limited right now. Please try again shortly.") from e
    except anthropic.APIConnectionError as e:
        raise ExtractionError("connection_error", "Could not reach the extraction service.") from e
    except anthropic.APIStatusError as e:
        raise ExtractionError("api_error", f"Extraction service returned an error ({e.status_code}).") from e

    text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
    try:
        fields = json.loads(text)
    except json.JSONDecodeError as e:
        raise ExtractionError("parse_error", "Could not parse the extraction result.") from e

    return fields
