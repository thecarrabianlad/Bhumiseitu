"""
Confidence-scoring service interface.

This step takes the per-field confidences produced by extraction and
decides (a) an overall record confidence and (b) whether the record
needs human review. This may end up owned by P4, P5, or shared -- swap
the implementation below as your team decides.

HOW TO PLUG IN:
1. Create a new module in this package implementing `ConfidenceService`.
2. Update `get_confidence_service()` at the bottom of this file.
"""
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Dict, List, Tuple

from app.schemas.record import ExtractedField

# Fields with confidence below this threshold trigger "needs_review".
DEFAULT_REVIEW_THRESHOLD = 0.75


class ConfidenceService(ABC):
    """Abstract base class every concrete confidence-scoring implementation must extend."""

    @abstractmethod
    def evaluate(
        self, fields: Dict[str, ExtractedField]
    ) -> Tuple[float, List[str], bool]:
        """
        Args:
            fields: field_name -> ExtractedField as produced by extraction.

        Returns:
            (overall_confidence, low_confidence_field_names, needs_review)
        """
        raise NotImplementedError


class SimpleAverageConfidenceService(ConfidenceService):
    """
    Baseline implementation: overall confidence = average of per-field
    confidences; needs_review = True if any field is below threshold or
    if there are no fields at all.
    """

    def __init__(self, threshold: float = DEFAULT_REVIEW_THRESHOLD):
        self.threshold = threshold

    def evaluate(
        self, fields: Dict[str, ExtractedField]
    ) -> Tuple[float, List[str], bool]:
        if not fields:
            return 0.0, [], True

        confidences = [f.confidence for f in fields.values()]
        overall = sum(confidences) / len(confidences)

        low_confidence_fields = [
            name for name, field in fields.items() if field.confidence < self.threshold
        ]
        needs_review = len(low_confidence_fields) > 0

        return round(overall, 4), low_confidence_fields, needs_review


@lru_cache
def get_confidence_service() -> ConfidenceService:
    """Dependency-injection point -- swap for a smarter implementation later."""
    return SimpleAverageConfidenceService()
