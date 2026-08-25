# Canned extraction results for the 3 fixtures in samples/.
#
# These are genuine frozen outputs from a real call to app/extractor.py
# (OpenAI gpt-4o-mini) against each fixture - not hand-authored. Sample mode
# only skips the network call at request time; the extraction logic itself
# is identical to what runs on a real upload.
#
# Note the bol_northstar_photo result: the model misread "Freightway Rd" as
# "Freighthay Rd" on the deliberately noisy/skewed photo fixture, and did
# NOT set review_recommended to flag it - a genuine, observed failure mode
# worth citing directly in the PIIRL "Result" section (see README.md).

SAMPLES = {
    "bol_acme_freight": {
        "filename": "bol_acme_freight.pdf",
        "display_name": "Clean BOL (PDF) — Acme Freight",
        "fields": {
            "document_type": "BOL",
            "shipper_name": "Acme Freight LLC",
            "shipper_address": "1200 Industrial Pkwy, Modesto, CA 95351",
            "consignee_name": "Bluepeak Retail Co.",
            "consignee_address": "88 Commerce Dr, Reno, NV 89501",
            "carrier_name": "Acme Freight LLC",
            "load_number": "LD-48213",
            "pro_number": "PRO-990214",
            "pickup_date": "2026-08-20",
            "delivery_date": None,
            "weight": 4200,
            "weight_unit": "lb",
            "piece_count": 12,
            "commodity_description": "Palletized dry goods",
            "freight_charge_terms": "prepaid",
            "signature_present": False,
            "review_recommended": False,
            "extraction_notes": None,
        },
    },
    "bol_northstar_photo": {
        "filename": "bol_northstar_logistics_photo.jpg",
        "display_name": "Phone-photo BOL (JPG) — Northstar Logistics",
        "fields": {
            "document_type": "BOL",
            "shipper_name": "Northstar Logistics",
            "shipper_address": "455 Freighthay Rd\nStockton, CA 95206",
            "consignee_name": "Cascade Wholesale Foods",
            "consignee_address": "22 Market St\nSacramento, CA 95814",
            "carrier_name": "Northstar Logistics",
            "load_number": "LD-77120",
            "pro_number": "PRO-114455",
            "pickup_date": "2026-08-21",
            "delivery_date": None,
            "weight": 6100,
            "weight_unit": "lb",
            "piece_count": 8,
            "commodity_description": "Refrigerated produce",
            "freight_charge_terms": "prepaid",
            "signature_present": False,
            "review_recommended": False,
            "extraction_notes": None,
        },
    },
    "pod_acme_delivery": {
        "filename": "pod_acme_freight_delivery.png",
        "display_name": "Proof of Delivery (PNG) — Acme Freight",
        "fields": {
            "document_type": "POD",
            "shipper_name": "Acme Freight LLC",
            "shipper_address": None,
            "consignee_name": "Harbor & Vine Cafe Supply",
            "consignee_address": None,
            "carrier_name": None,
            "load_number": "LD-48213",
            "pro_number": None,
            "pickup_date": None,
            "delivery_date": "2026-08-22",
            "weight": 4180,
            "weight_unit": "lb",
            "piece_count": None,
            "commodity_description": None,
            "freight_charge_terms": None,
            "signature_present": True,
            "review_recommended": False,
            "extraction_notes": None,
        },
    },
}
