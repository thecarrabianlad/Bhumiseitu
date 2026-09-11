"""
confidence.py
-------------
Calculates a single "confidence score" (0-100) for an extracted land
record, WITHOUT ever asking the LLM "how confident are you?". LLMs are
known to be poorly calibrated when asked to self-report confidence --
they might say "95% confident" about a completely made-up value. So
instead we compute our own score from measurable, independent signals.

THE FORMULA (documented so you can explain it to an SIH judge):

    final_confidence =
          0.15 * ocr_quality_score
        + 0.25 * completeness_score
        + 0.30 * validation_score
        + 0.30 * evidence_score
        - ambiguity_penalty

    (each term above, before weighting, is on a 0-100 scale; the
    final result is clamped to the 0-100 range)

WHY THESE WEIGHTS:
    - Evidence grounding (0.30) and validation (0.30) get the highest
      weight because they most directly answer "can we trust what was
      extracted?" -- which is the whole point of this module.
    - Completeness (0.25) matters (a mostly-empty record is less
      useful) but completeness alone doesn't mean the data is
      trustworthy, so it's weighted a bit lower than validation/
      evidence.
    - OCR quality (0.15) is the smallest weight because it's an input
      signal from an upstream module (P4) that we don't fully control
      and that may not even be available -- we still want it to move
      the needle, just not dominate.
    - The ambiguity penalty is subtracted directly (not weighted) so
      that severe problems (e.g. conflicting values) can meaningfully
      pull the score down regardless of the other terms.

These weights are a starting point for the hackathon; they are easy
to re-tune later (e.g. after getting feedback from real clerks) since
they are all defined as named constants below.
"""

from typing import Optional

from app.schemas import REQUIRED_FIELDS

# --- Weights (must sum to 1.0 across the four positive terms) ---
WEIGHT_OCR_QUALITY = 0.15
WEIGHT_COMPLETENESS = 0.25
WEIGHT_VALIDATION = 0.30
WEIGHT_EVIDENCE = 0.30

# Points subtracted per issue found (see _calculate_ambiguity_penalty).
PENALTY_PER_VALIDATION_ERROR = 8
PENALTY_PER_UNSUPPORTED_FIELD = 12
MAX_AMBIGUITY_PENALTY = 50  # never let the penalty alone wipe out more than this


def calculate_confidence(
    record: dict,
    validation_result: dict,
    evidence_result: dict,
    ocr_metadata: Optional[dict] = None,
) -> dict:
    """Compute the final 0-100 confidence score plus a breakdown of
    each component, so the breakdown can be shown to judges/clerks for
    transparency (this is important for an SIH demo -- "explainable
    confidence", not a black box).

    Args:
        record: the (validated) extracted record.
        validation_result: output of validator.validate_schema_and_types()
        evidence_result: output of validator.check_evidence()
        ocr_metadata: optional dict that P4 (OCR module) may supply,
            e.g. {"ocr_confidence": 0.87}. If P4 doesn't send this
            yet, we handle that gracefully (see _ocr_quality_score).

    Returns:
        {
            "final_confidence": float (0-100),
            "breakdown": {
                "ocr_quality_score": ...,
                "completeness_score": ...,
                "validation_score": ...,
                "evidence_score": ...,
                "ambiguity_penalty": ...,
            }
        }
    """
    ocr_quality_score = _ocr_quality_score(ocr_metadata)
    completeness_score = _completeness_score(record)
    validation_score = _validation_score(validation_result)
    evidence_score = _evidence_score(evidence_result)
    ambiguity_penalty = _ambiguity_penalty(validation_result, evidence_result)

    raw_score = (
        WEIGHT_OCR_QUALITY * ocr_quality_score
        + WEIGHT_COMPLETENESS * completeness_score
        + WEIGHT_VALIDATION * validation_score
        + WEIGHT_EVIDENCE * evidence_score
        - ambiguity_penalty
    )

    final_confidence = max(0.0, min(100.0, raw_score))

    return {
        "final_confidence": round(final_confidence, 1),
        "breakdown": {
            "ocr_quality_score": round(ocr_quality_score, 1),
            "completeness_score": round(completeness_score, 1),
            "validation_score": round(validation_score, 1),
            "evidence_score": round(evidence_score, 1),
            "ambiguity_penalty": round(ambiguity_penalty, 1),
        },
    }


def _ocr_quality_score(ocr_metadata: Optional[dict]) -> float:
    """If P4 supplies an OCR confidence (0-1 or 0-100), use it.
    Otherwise, assume a neutral middle score (60) -- we neither
    reward nor punish records when we simply don't know the OCR
    quality, since P4 is developed independently and may not send
    this yet.
    """
    if not ocr_metadata:
        return 60.0
    raw = ocr_metadata.get("ocr_confidence")
    if raw is None:
        return 60.0
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 60.0
    # Accept either a 0-1 fraction or an already-0-100 value.
    if 0 <= value <= 1:
        return value * 100
    return max(0.0, min(100.0, value))


def _completeness_score(record: dict) -> float:
    """What fraction of the 8 fields were actually extracted
    (non-null)? Expressed as a percentage."""
    filled = sum(1 for field in REQUIRED_FIELDS if record.get(field) is not None)
    return (filled / len(REQUIRED_FIELDS)) * 100


def _validation_score(validation_result: dict) -> float:
    """What fraction of fields passed deterministic validation?"""
    field_results = validation_result.get("field_results", {})
    if not field_results:
        return 0.0
    passed = sum(1 for ok in field_results.values() if ok)
    return (passed / len(field_results)) * 100


def _evidence_score(evidence_result: dict) -> float:
    """Of the fields that were actually filled in (non-null), what
    fraction are supported by the original OCR text? Fields that are
    null are excluded from this calculation (there's nothing to check
    evidence for)."""
    supported = evidence_result.get("supported", {})
    checked = [v for v in supported.values() if v is not None]
    if not checked:
        # No non-null fields at all -- there's no evidence to be
        # wrong about, so this isn't a evidence *problem*. We give a
        # neutral score rather than 0 or 100.
        return 50.0
    supported_count = sum(1 for v in checked if v is True)
    return (supported_count / len(checked)) * 100


def _ambiguity_penalty(validation_result: dict, evidence_result: dict) -> float:
    """Extra points subtracted for concrete problems: each
    validation error and each unsupported (unevidenced) field costs
    points, on top of already lowering validation_score/
    evidence_score above. This makes sure a record with, say, 3
    hallucinated fields drops decisively below the 90 threshold
    rather than being averaged away.
    """
    num_validation_errors = len(validation_result.get("errors", []))
    num_unsupported = len(evidence_result.get("unsupported_fields", []))

    penalty = (
        num_validation_errors * PENALTY_PER_VALIDATION_ERROR
        + num_unsupported * PENALTY_PER_UNSUPPORTED_FIELD
    )
    return min(penalty, MAX_AMBIGUITY_PENALTY)
