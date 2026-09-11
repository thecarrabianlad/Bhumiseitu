# Test samples

This folder is for **local, developer-provided** sample documents used to
manually exercise the OCR pipeline. It is intentionally empty in git.

Do **not** commit:
- real/copyrighted land records or scans belonging to a person or authority
- any personally identifiable document
- large binary files

## What to add locally

Drop your own test files here (they're covered by `.gitignore`, except this
README), for example:

- `sample_en.jpg` / `sample_en.png` — a clean English document
- `sample_degraded.jpg` — a scanned, skewed, or faded document
- `hi_en_sample.jpg` (or `.png` / `.pdf`) — a Hindi + English prototype
  document. The filename prefix `hi_en` is picked up automatically by
  `tests/test_ocr.py`'s `LivePaddleOCRTests.test_hindi_english_sample_if_present`.

## Running the live OCR tests against your samples

The default test run (`python3 -m unittest discover -s tests`) skips tests
that call the real PaddleOCR engine, since PaddleOCR downloads model
weights from the network on first use. To run those too, once you have
network access and/or local samples in place:

```bash
RUN_LIVE_OCR_TESTS=1 python3 -m unittest discover -s tests -v
```
