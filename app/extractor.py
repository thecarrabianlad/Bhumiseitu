"""
extractor.py
------------
This is the FRONT DOOR of the whole P3 module. Every other file
(llm_client, validator, confidence, router, schemas, prompts) is a
helper that this file calls in order.

The one function you (or a teammate on Backend/P4) actually need to
know about is:

    extract_land_record(ocr_text, ocr_metadata=None)

Pipeline (this is literally what the function below does, in order):

    1. Send ocr_text to the LLM  -> candidate JSON (may be messy/wrong)
    2. Run deterministic validation on that JSON (validator.py)
    3. Run evidence/hallucination checking against the original OCR
       text (validator.py) -- any unsupported value gets nulled out
    4. Calculate a 0-100 confidence score from all of the above
       (confidence.py)
    5. Decide AUTO_SAVE vs CLERK_REVIEW from that score (router.py)
    6. Return one clean dictionary with extracted_data, confidence,
       route (and, for transparency/debugging, a "diagnostics" block)
"""

from typing import Optional

from app.llm_client import LLMClient, get_llm_client
from app.schemas import REQUIRED_FIELDS, empty_record
from app.validator import validate_schema_and_types, check_evidence
from app.confidence import calculate_confidence
from app.router import decide_route


def extract_land_record(
    ocr_text: str,
    ocr_metadata: Optional[dict] = None,
    llm_client: Optional[LLMClient] = None,
) -> dict:
    """Turn raw OCR text into a structured, validated land record with
    a confidence score and a routing decision.

    Args:
        ocr_text: raw text as produced by P4 (the OCR module). Can be
            English, Hindi, mixed, and may contain OCR noise/typos.
        ocr_metadata: optional dict P4 may supply about the OCR step
            itself, e.g. {"ocr_confidence": 0.87}. Safe to omit or
            pass None -- P3 does not require or depend on any specific
            shape from P4 beyond this being a plain dict if present.
        llm_client: optional. Lets tests (or advanced callers) inject
            a specific LLMClient implementation (e.g. MockLLMClient).
            If omitted, `get_llm_client()` decides automatically: it
            uses a real LLM if LLM_API_KEY is configured in the
            environment, otherwise it safely falls back to the mock
            client.

    Returns:
        {
            "extracted_data": { ...the 8 fixed fields... },
            "confidence": float (0-100),
            "route": "AUTO_SAVE" | "CLERK_REVIEW",
            "diagnostics": {
                "validation_errors": [...],
                "unsupported_fields": [...],
                "confidence_breakdown": {...},
            }
        }
    """
    if not isinstance(ocr_text, str) or ocr_text.strip() == "":
        # No usable input at all -- return an honest "we found
        # nothing" result rather than guessing or crashing.
        return _build_result(
            record=empty_record(),
            validation_result={"field_results": {f: True for f in REQUIRED_FIELDS}, "errors": ["ocr_text was empty"]},
            evidence_result={"supported": {f: None for f in REQUIRED_FIELDS}, "unsupported_fields": []},
            ocr_metadata=ocr_metadata,
        )

    client = llm_client or get_llm_client()

    # Step 1: LLM extraction (candidate JSON, not yet trusted).
    candidate = client.extract_raw(ocr_text)
    candidate = _coerce_to_fixed_schema(candidate)

    # Step 2: Deterministic validation.
    validation_result = validate_schema_and_types(candidate)

    # Step 3: Evidence / hallucination check. Any field that fails
    # the evidence check gets nulled out in the final record -- we
    # would rather say "we don't know" than report an unsupported
    # value as fact.
    evidence_result = check_evidence(candidate, ocr_text)
    final_record = dict(candidate)
    for field in evidence_result["unsupported_fields"]:
        final_record[field] = None
    # Also null out anything that failed structural validation but
    # wasn't already null.
    for field, passed in validation_result["field_results"].items():
        if not passed and final_record.get(field) is not None:
            final_record[field] = None

    return _build_result(final_record, validation_result, evidence_result, ocr_metadata)


def _build_result(record: dict, validation_result: dict, evidence_result: dict, ocr_metadata) -> dict:
    confidence_result = calculate_confidence(record, validation_result, evidence_result, ocr_metadata)
    route = decide_route(confidence_result["final_confidence"])

    return {
        "extracted_data": record,
        "confidence": confidence_result["final_confidence"],
        "route": route,
        "diagnostics": {
            "validation_errors": validation_result.get("errors", []),
            "unsupported_fields": evidence_result.get("unsupported_fields", []),
            "confidence_breakdown": confidence_result["breakdown"],
        },
    }


def _coerce_to_fixed_schema(candidate: dict) -> dict:
    """Defensive step: no matter what the LLM returned (missing keys,
    extra keys, wrong types), always produce a dict with exactly the
    8 required keys. Anything unexpected is dropped; anything missing
    becomes null. This guarantees every downstream file can always
    assume the fixed shape.
    """
    if not isinstance(candidate, dict):
        return empty_record()
    safe = empty_record()
    for field in REQUIRED_FIELDS:
        if field in candidate:
            safe[field] = candidate[field]
    return safe
