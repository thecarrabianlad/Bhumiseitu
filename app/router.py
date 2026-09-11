"""
router.py
---------
Decides what should happen to a record once we have its confidence
score. This is intentionally the simplest file in the whole project --
routing should be a trivial, obvious decision once confidence has been
computed properly.

Rule (fixed by project requirements):
    confidence >= 90  -> "AUTO_SAVE"
    confidence <  90  -> "CLERK_REVIEW"
"""

AUTO_SAVE_THRESHOLD = 90.0

ROUTE_AUTO_SAVE = "AUTO_SAVE"
ROUTE_CLERK_REVIEW = "CLERK_REVIEW"


def decide_route(confidence: float) -> str:
    """Return ROUTE_AUTO_SAVE if confidence meets the threshold,
    otherwise ROUTE_CLERK_REVIEW."""
    if confidence >= AUTO_SAVE_THRESHOLD:
        return ROUTE_AUTO_SAVE
    return ROUTE_CLERK_REVIEW
