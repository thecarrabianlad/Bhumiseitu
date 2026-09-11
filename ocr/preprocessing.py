"""
OpenCV-based preprocessing for degraded scanned documents (skew, noise,
poor contrast, faded text) ahead of OCR.

Every function here takes an image and returns a *new* image — none of
them mutate the array passed in, so the caller's original image is always
preserved.
"""
import cv2
import numpy as np


class ImageLoadError(Exception):
    """Raised when an image file is missing, unreadable, or corrupt."""


def load_image(path: str) -> np.ndarray:
    """Load an image from disk as a BGR array (OpenCV's default)."""
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise ImageLoadError(f"Could not read image (missing or corrupt): {path}")
    return image


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert a BGR (or already-grayscale) image to single-channel grayscale."""
    img = image.copy()
    if img.ndim == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def denoise_image(gray: np.ndarray, strength: int = 7) -> np.ndarray:
    """
    Reduce scan/sensor noise while trying to keep character edges intact.
    `strength` maps to OpenCV's non-local-means `h` parameter — higher
    removes more noise but can start to blur faint/faded strokes.
    """
    img = gray.copy()
    return cv2.fastNlMeansDenoising(
        img, None, h=strength, templateWindowSize=7, searchWindowSize=21
    )


def enhance_contrast(gray: np.ndarray, clip_limit: float = 2.0, tile_grid_size=(8, 8)) -> np.ndarray:
    """
    Boost local contrast with CLAHE (adaptive histogram equalization).
    This helps faded or unevenly-lit text become legible without
    over-amplifying background noise, unlike a global equalizer.
    """
    img = gray.copy()
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    return clahe.apply(img)


def _estimate_skew_angle(gray: np.ndarray) -> float:
    """
    Estimate the document's rotation angle (in degrees) from the spread of
    foreground (text) pixels, rather than assuming any fixed rotation.
    Returns 0.0 if there isn't enough foreground signal to estimate from,
    or if the estimated angle is implausibly large (likely noise).
    """
    img = gray.copy()
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh > 0))

    if coords.shape[0] < 20:
        return 0.0

    angle = cv2.minAreaRect(coords)[-1]
    # cv2.minAreaRect's angle convention varies with OpenCV version/box
    # orientation; normalize it into a small rotation-correction angle.
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) > 45:
        # Implausible for a document scan — treat as noise, not real skew.
        return 0.0
    return float(angle)


def deskew_image(gray: np.ndarray) -> np.ndarray:
    """Estimate and correct document skew. No-op if skew is negligible."""
    img = gray.copy()
    angle = _estimate_skew_angle(img)
    if abs(angle) < 0.1:
        return img

    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        img,
        matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated


def threshold_image(gray: np.ndarray) -> np.ndarray:
    """
    Adaptive (local) binarization — robust to uneven scan lighting on old
    documents. Adaptive thresholding is used instead of a single global
    cutoff (e.g. plain Otsu) specifically because a single global threshold
    tends to wipe out faded text in one part of the page while over-inking
    noise in another.
    """
    img = gray.copy()
    return cv2.adaptiveThreshold(
        img,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15,
    )


def preprocess_image(image: np.ndarray, apply_binarization: bool = False) -> np.ndarray:
    """
    Full preprocessing pipeline: grayscale -> denoise -> contrast enhance
    -> deskew -> (optional) binarize. Operates on a copy; the caller's
    original `image` is never modified.

    `apply_binarization` is opt-in and OFF by default: hard thresholding
    can destroy faded/thin characters on old scans, and PaddleOCR's
    detector/recognizer generally performs better on a clean grayscale
    image than on a pre-binarized one. Enable it for individual documents
    that are degraded enough to need it.

    Returns a 3-channel BGR image (PaddleOCR's expected input format).
    """
    working = image.copy()
    gray = convert_to_grayscale(working)
    denoised = denoise_image(gray)
    contrasted = enhance_contrast(denoised)
    deskewed = deskew_image(contrasted)
    final = threshold_image(deskewed) if apply_binarization else deskewed
    return cv2.cvtColor(final, cv2.COLOR_GRAY2BGR)
