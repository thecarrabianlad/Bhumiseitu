# P3 Integration Contract (for teammates)

Send this to whoever is building P4 (OCR) and Backend.

## What P4 sends to P3

```python
from app.extractor import extract_land_record

result = extract_land_record(
    ocr_text,             # REQUIRED: plain string of OCR output
    ocr_metadata=None,    # OPTIONAL: e.g. {"ocr_confidence": 0.87}
)
```

- `ocr_text` is the only thing P4 must provide. It can be English, Hindi, mixed, and can
  contain OCR noise — P3 is built to handle that.
- `ocr_metadata` is optional. If P4's OCR engine can report a confidence score for the scan
  itself, pass it as `{"ocr_confidence": <0-1 or 0-100>}`. If P4 can't provide this (yet),
  just omit it — P3 still works correctly without it.
- **P3 does not depend on how P4 is implemented internally** — only on receiving a plain
  string.

## What P3 returns to the Backend

```json
{
  "extracted_data": {
    "owner_name": "...", "khasra_number": "...", "area": 0.0, "area_unit": "...",
    "village": "...", "tehsil": "...", "district": "...", "land_use": "..."
  },
  "confidence": 0.0,
  "route": "AUTO_SAVE",
  "diagnostics": { "validation_errors": [], "unsupported_fields": [], "confidence_breakdown": {} }
}
```

- `extracted_data` always has exactly these 8 keys. Missing information is `null`, never
  guessed.
- `confidence` is a number from 0 to 100.
- `route` is always exactly `"AUTO_SAVE"` or `"CLERK_REVIEW"`.
- `diagnostics` is optional extra detail (useful for a clerk-review UI or logging) — the
  backend is not required to use it.

## What the Backend should do

- `route == "AUTO_SAVE"` → save `extracted_data` directly.
- `route == "CLERK_REVIEW"` → send the record to a human review queue instead of saving it
  automatically. `diagnostics` can help explain to the clerk why review is needed.

## Notes

- P3 has no database, no API server, and no UI of its own — it's a pure function
  (`extract_land_record`). Backend can call it directly as a Python import, or wrap it in a
  thin HTTP endpoint if the backend runs as a separate service.
- P3 has zero dependency on the current implementation of P4, the backend, the frontend, or
  the database — only on this input/output contract above.
