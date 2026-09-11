# Backend — Intelligent Land Record Digitization MVP

FastAPI backend that connects the frontend to the OCR, AI extraction, and
Supabase database components. This service owns the API layer, request
validation, orchestration, and DB access — it does **not** implement OCR
or LLM extraction itself (see "Where teammates plug in" below).

## Structure

```
backend/
  app/
    main.py                     # FastAPI app, router wiring, error handlers
    core/
      config.py                 # env-driven settings (Settings/get_settings)
    db/
      supabase_client.py        # Supabase client factory
      storage.py                # file upload helper (Supabase Storage)
    schemas/
      common.py                 # APIResponse / APIError envelope, pagination
      document.py                # Document upload/process schemas
      record.py                  # LandRecord schemas (list + detail)
      review.py                  # approve/reject request/response schemas
    services/
      ocr/interface.py           # <-- P4 plugs in real OCR here
      extraction/interface.py    # <-- P5 plugs in real field extraction here
      confidence/interface.py    # confidence scoring / review threshold logic
      records_service.py         # all Supabase queries (documents + records)
      mappers.py                 # DB row -> response schema conversion
      pipeline.py                # orchestrates OCR -> extraction -> confidence -> DB
    routes/
      documents.py               # POST /documents/upload, POST /documents/{id}/process
      records.py                 # GET /records, GET /records/{id}
      review.py                  # GET /records/review, POST approve/reject
      health.py                  # GET /health
  requirements.txt
  .env.example
```

## Running locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real Supabase values
uvicorn app.main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs

Without real Supabase credentials, `/health` and `/docs` work, but any
route touching the database will raise a clear `RuntimeError` from
`get_supabase()` rather than failing silently.

## API summary

All routes are mounted under `/api/v1` and return the same envelope:

```json
{ "success": true, "data": {...}, "message": "...", "meta": {...} }
{ "success": false, "data": null, "message": "...", "error_code": "..." }
```

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/documents/upload` | Upload a scanned document (multipart file) |
| POST | `/api/v1/documents/{document_id}/process` | Run OCR + extraction + confidence, create a land record |
| GET | `/api/v1/records` | List land records (pagination, `status`/`district` filters) |
| GET | `/api/v1/records/{record_id}` | Full detail for one land record |
| GET | `/api/v1/records/review` | List records with status `needs_review` |
| POST | `/api/v1/records/{record_id}/approve` | Approve a record (optional field corrections) |
| POST | `/api/v1/records/{record_id}/reject` | Reject a record |

## Where teammates plug in

**P4 (OCR):**
Implement `OCRService.extract_text()` in a new file under
`app/services/ocr/` (e.g. `tesseract_ocr.py`), then point
`get_ocr_service()` at it. Contract: takes raw file bytes + content type,
returns `OCRResult(raw_text=...)`.

**P5 (AI extraction):**
Implement `ExtractionService.extract_fields()` in a new file under
`app/services/extraction/`, then point `get_extraction_service()` at it.
Contract: takes raw OCR text, returns `Dict[str, ExtractedField]` where
each field has a `value` and a `confidence` (0–1). Try to match field
names in `LandRecordFields` (`app/schemas/record.py`) — anything else
still comes through fine via `extra_fields`.

**DB owner (Supabase):**
`app/db/supabase_client.py` and `app/services/records_service.py` assume
two tables, `documents` and `land_records` (shapes documented at the top
of `records_service.py`). Adjust column names/queries there if the actual
schema differs, and set `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` /
`SUPABASE_STORAGE_BUCKET` in `.env`.

Nothing outside these files needs to change when a real implementation
is swapped in — `pipeline.py` and the routes only depend on the abstract
interfaces.

## Notes / next steps

- `pipeline._fetch_file_bytes()` is a stub — wire it to
  `supabase.storage.from_(bucket).download(path)` once storage is finalized.
- Confidence review threshold defaults to `0.75` in
  `app/services/confidence/interface.py` — tune once real confidence
  scores are available.
- Add auth (e.g. Supabase JWT verification) before this goes past MVP —
  currently endpoints are unauthenticated.
