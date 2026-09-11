"""
Tests for the P3 OCR pipeline.

Split into two groups:

1. Deterministic tests (always run, no network/model download needed):
   preprocessing stages, error handling, and the standardized output
   schema (verified by monkeypatching the OCR call itself).

2. Live OCR tests (opt-in): actually run PaddleOCR end-to-end. These
   require PaddleOCR's models to be downloaded on first use, which needs
   network access — set RUN_LIVE_OCR_TESTS=1 to enable them. They are
   skipped by default so the suite works offline / in restricted CI.

Run with:
    python3 -m unittest discover -s tests -v
"""
import os
import sys
import unittest

import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ocr import pipeline
from ocr.preprocessing import (
    convert_to_grayscale,
    denoise_image,
    deskew_image,
    enhance_contrast,
    load_image,
    preprocess_image,
    threshold_image,
    ImageLoadError,
)

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")
RUN_LIVE_OCR_TESTS = os.environ.get("RUN_LIVE_OCR_TESTS") == "1"


def _make_text_image(text="Hello World 123", size=(400, 120), angle=0, noise=False, faded=False):
    """Build a synthetic English test image (with optional skew/noise/fading)."""
    img = np.full((size[1], size[0], 3), 255, dtype=np.uint8)
    color = (150, 150, 150) if faded else (0, 0, 0)
    cv2.putText(img, text, (10, size[1] // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA)

    if noise:
        gauss_noise = np.random.normal(0, 20, img.shape).astype(np.int16)
        noisy = np.clip(img.astype(np.int16) + gauss_noise, 0, 255).astype(np.uint8)
        img = noisy

    if angle:
        h, w = img.shape[:2]
        matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        img = cv2.warpAffine(img, matrix, (w, h), borderValue=(255, 255, 255))

    return img


class PreprocessingTests(unittest.TestCase):
    def setUp(self):
        self.image = _make_text_image()

    def test_load_image_missing_file_raises(self):
        with self.assertRaises(ImageLoadError):
            load_image("/nonexistent/path/does_not_exist.png")

    def test_load_image_corrupt_file_raises(self):
        bad_path = os.path.join(SAMPLES_DIR, "_corrupt_test_file.png")
        with open(bad_path, "wb") as f:
            f.write(b"this is not a real image")
        try:
            with self.assertRaises(ImageLoadError):
                load_image(bad_path)
        finally:
            os.remove(bad_path)

    def test_convert_to_grayscale_shape_and_no_mutation(self):
        original = self.image.copy()
        gray = convert_to_grayscale(self.image)
        self.assertEqual(gray.ndim, 2)
        np.testing.assert_array_equal(self.image, original)  # input untouched

    def test_denoise_preserves_shape(self):
        gray = convert_to_grayscale(self.image)
        denoised = denoise_image(gray)
        self.assertEqual(denoised.shape, gray.shape)

    def test_enhance_contrast_preserves_shape(self):
        gray = convert_to_grayscale(self.image)
        contrasted = enhance_contrast(gray)
        self.assertEqual(contrasted.shape, gray.shape)

    def test_deskew_runs_on_rotated_image(self):
        rotated = _make_text_image(angle=8)
        gray = convert_to_grayscale(rotated)
        deskewed = deskew_image(gray)
        self.assertEqual(deskewed.shape, gray.shape)

    def test_deskew_noop_on_straight_image(self):
        gray = convert_to_grayscale(self.image)
        deskewed = deskew_image(gray)
        self.assertEqual(deskewed.shape, gray.shape)

    def test_threshold_image_is_binary(self):
        gray = convert_to_grayscale(self.image)
        thresholded = threshold_image(gray)
        unique_values = set(np.unique(thresholded).tolist())
        self.assertTrue(unique_values.issubset({0, 255}))

    def test_preprocess_image_full_pipeline_default(self):
        cleaned = preprocess_image(self.image)
        self.assertEqual(cleaned.ndim, 3)  # returned as BGR for OCR input
        self.assertEqual(cleaned.shape[:2], self.image.shape[:2])

    def test_preprocess_image_does_not_mutate_input(self):
        original = self.image.copy()
        preprocess_image(self.image, apply_binarization=True)
        np.testing.assert_array_equal(self.image, original)

    def test_preprocess_handles_noisy_faded_degraded_image(self):
        degraded = _make_text_image(noise=True, faded=True, angle=5)
        cleaned = preprocess_image(degraded)
        self.assertEqual(cleaned.shape[:2], degraded.shape[:2])


class ProcessDocumentErrorHandlingTests(unittest.TestCase):
    def test_missing_file_returns_standardized_error(self):
        result = pipeline.process_document("/no/such/file.png")
        self.assertFalse(result["success"])
        self.assertEqual(result["pages"], [])
        self.assertIsInstance(result["error"], str)

    def test_unsupported_extension_returns_standardized_error(self):
        bad_path = os.path.join(SAMPLES_DIR, "_unsupported.txt")
        with open(bad_path, "w") as f:
            f.write("not a document")
        try:
            result = pipeline.process_document(bad_path)
            self.assertFalse(result["success"])
            self.assertIn("Unsupported file type", result["error"])
        finally:
            os.remove(bad_path)

    def test_corrupt_image_returns_standardized_error_not_traceback(self):
        bad_path = os.path.join(SAMPLES_DIR, "_corrupt.png")
        with open(bad_path, "wb") as f:
            f.write(b"garbage bytes, not a real png")
        try:
            result = pipeline.process_document(bad_path)
            self.assertFalse(result["success"])
            self.assertNotIn("Traceback", result["error"])
        finally:
            os.remove(bad_path)


class StandardizedOutputSchemaTests(unittest.TestCase):
    """
    Verifies the output contract (structure, confidence, bboxes) without
    requiring PaddleOCR's models to be downloaded, by stubbing out the
    actual OCR call with a fixed fake result.
    """

    def setUp(self):
        self._original_run_ocr = pipeline._run_ocr_on_image
        pipeline._run_ocr_on_image = self._fake_run_ocr

        self.sample_path = os.path.join(SAMPLES_DIR, "_schema_test.png")
        cv2.imwrite(self.sample_path, _make_text_image())

    def tearDown(self):
        pipeline._run_ocr_on_image = self._original_run_ocr
        if os.path.exists(self.sample_path):
            os.remove(self.sample_path)

    @staticmethod
    def _fake_run_ocr(image, lang):
        return {
            "rec_texts": ["Hello World", "123"],
            "rec_scores": [0.97, 0.88],
            "rec_polys": [
                np.array([[10, 10], [100, 10], [100, 30], [10, 30]]),
                np.array([[10, 40], [50, 40], [50, 60], [10, 60]]),
            ],
        }

    def test_image_output_matches_standardized_schema(self):
        result = pipeline.process_document(self.sample_path, lang="en")

        self.assertTrue(result["success"])
        self.assertEqual(result["document_type"], "image")
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["pages"]), 1)

        page = result["pages"][0]
        self.assertEqual(page["page"], 1)
        self.assertEqual(page["text"], "Hello World\n123")
        self.assertAlmostEqual(page["average_confidence"], 0.925, places=3)
        self.assertEqual(page["language"], "en")
        self.assertEqual(len(page["lines"]), 2)

        line0 = page["lines"][0]
        self.assertEqual(line0["text"], "Hello World")
        self.assertEqual(line0["confidence"], 0.97)
        self.assertEqual(len(line0["bbox"]), 4)
        self.assertEqual(len(line0["bbox"][0]), 2)

    def test_ocr_exception_is_caught_and_returns_standardized_error(self):
        def _raise(*args, **kwargs):
            raise RuntimeError("simulated OCR engine failure")

        pipeline._run_ocr_on_image = _raise
        result = pipeline.process_document(self.sample_path, lang="en")
        self.assertFalse(result["success"])
        self.assertEqual(result["document_type"], "image")
        self.assertIn("OCR pipeline failed", result["error"])


@unittest.skipUnless(RUN_LIVE_OCR_TESTS, "Set RUN_LIVE_OCR_TESTS=1 to run real PaddleOCR (needs model download).")
class LivePaddleOCRTests(unittest.TestCase):
    """
    End-to-end tests against the real PaddleOCR engine. Skipped by default
    because PaddleOCR downloads model weights from the network on first
    use, which may not be available in restricted/offline environments.
    """

    def test_jpg_input(self):
        path = os.path.join(SAMPLES_DIR, "_live_test.jpg")
        cv2.imwrite(path, _make_text_image())
        try:
            result = pipeline.process_document(path, lang="en")
            self.assertTrue(result["success"])
            self.assertGreater(len(result["pages"][0]["lines"]), 0)
        finally:
            os.remove(path)

    def test_png_input(self):
        path = os.path.join(SAMPLES_DIR, "_live_test.png")
        cv2.imwrite(path, _make_text_image())
        try:
            result = pipeline.process_document(path, lang="en")
            self.assertTrue(result["success"])
        finally:
            os.remove(path)

    def test_degraded_document(self):
        path = os.path.join(SAMPLES_DIR, "_live_degraded.png")
        cv2.imwrite(path, _make_text_image(noise=True, faded=True, angle=6))
        try:
            result = pipeline.process_document(path, lang="en")
            self.assertTrue(result["success"])
        finally:
            os.remove(path)

    def test_hindi_english_sample_if_present(self):
        # Developers should drop a real Hindi/English sample document into
        # tests/samples/ (see samples/README.md). Skips gracefully if none
        # is present rather than failing the suite.
        candidates = [
            f for f in os.listdir(SAMPLES_DIR)
            if f.lower().startswith("hi_en") and f.lower().endswith((".jpg", ".jpeg", ".png", ".pdf"))
        ]
        if not candidates:
            self.skipTest("No Hindi/English sample found in tests/samples/ (see samples/README.md).")
        path = os.path.join(SAMPLES_DIR, candidates[0])
        result = pipeline.process_document(path, lang="hi")
        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()
