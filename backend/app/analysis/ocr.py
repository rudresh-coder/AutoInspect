import re
from dataclasses import dataclass

import cv2
import easyocr
import numpy as np


@dataclass
class OCRTextDetection:
    text: str
    normalized_text: str
    confidence: float


@dataclass
class PlateCandidate:
    text: str
    confidence: float
    score: float
    reason: str


@dataclass
class OCRResult:
    detected_text: list[OCRTextDetection]
    plate_detected: bool
    plate_text: str | None
    plate_confidence: float | None
    plate_reason: str


_reader = None


def get_reader():
    global _reader

    if _reader is None:
        _reader = easyocr.Reader(
            ["en"],
            gpu=False,
        )

    return _reader


# ---------------------------------------------------------
# Text normalization
# ---------------------------------------------------------

def normalize_text(text: str) -> str:
    return re.sub(
        r"[^A-Z0-9]",
        "",
        text.upper(),
    )


# ---------------------------------------------------------
# Obvious non-plate text
# ---------------------------------------------------------

def _is_obvious_non_plate(text: str) -> bool:
    common_words = {
        "GLOBAL",
        "ALUMNI",
        "RECRUITERS",
        "EXPLORE",
        "CAREERS",
        "CREATIVITY",
        "ANIMATION",
        "DIGITAL",
        "CONTENT",
        "LEARN",
        "FROM",
        "NEW",
        "PUNE",
        "RENA",
        "HOSPITAL",
        "AGARWALS",
        "EYE",
        "CENTRE",
        "CENTER",
        "SCHOOL",
        "COLLEGE",
        "HOTEL",
        "RESTAURANT",
        "MOTORS",
        "SERVICE",
    }

    return text in common_words


# ---------------------------------------------------------
# Indian registration-pattern helpers
# ---------------------------------------------------------

def _looks_like_indian_registration(text: str) -> bool:
    """
    Heuristic check for common Indian vehicle registration formats.

    Examples:
        KA01AB1234
        MH12DE1432
        TN38A1234
        DL3CAB1234

    This is intentionally heuristic rather than a strict validator.
    """

    patterns = [
        # Typical: KA01AB1234
        r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{3,4}$",

        # Some older/shorter formats
        r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{1,4}$",

        # BH-series: 22BH1234AA
        r"^[0-9]{2}BH[0-9]{4}[A-Z]{2}$",
    ]

    return any(re.fullmatch(pattern, text) for pattern in patterns)


def _has_registration_structure(text: str) -> bool:
    """
    Looks for the general structure expected in a registration number:
        letters + digits + letters/digits

    This is intentionally less strict than _looks_like_indian_registration().
    """

    has_letters = any(char.isalpha() for char in text)
    has_digits = any(char.isdigit() for char in text)

    if not has_letters or not has_digits:
        return False

    # Registration plates normally contain a meaningful mixture
    # rather than a single long word.
    digit_count = sum(char.isdigit() for char in text)
    letter_count = sum(char.isalpha() for char in text)

    return digit_count >= 2 and letter_count >= 2


# ---------------------------------------------------------
# Candidate scoring
# ---------------------------------------------------------

def _score_plate_candidate(
    normalized_text: str,
    ocr_confidence: float,
    box_width: float | None = None,
    box_height: float | None = None,
) -> PlateCandidate | None:

    length = len(normalized_text)

    # Avoid extremely short or extremely long OCR fragments.
    if length < 6 or length > 12:
        return None

    if _is_obvious_non_plate(normalized_text):
        return None

    if not _has_registration_structure(normalized_text):
        return None

    score = 0.0
    reasons = []

    # -----------------------------------------------------
    # Length
    # -----------------------------------------------------

    if 8 <= length <= 10:
        score += 20
        reasons.append("registration-like length")
    elif 7 <= length <= 11:
        score += 10

    # -----------------------------------------------------
    # Character composition
    # -----------------------------------------------------

    digit_count = sum(char.isdigit() for char in normalized_text)
    letter_count = sum(char.isalpha() for char in normalized_text)

    if digit_count >= 2:
        score += 15
        reasons.append("contains multiple digits")

    if letter_count >= 2:
        score += 15
        reasons.append("contains multiple letters")

    # -----------------------------------------------------
    # Indian registration structure
    # -----------------------------------------------------

    if _looks_like_indian_registration(normalized_text):
        score += 30
        reasons.append("matches common Indian registration format")

    # -----------------------------------------------------
    # OCR confidence
    # -----------------------------------------------------

    confidence_score = ocr_confidence * 20
    score += confidence_score

    if ocr_confidence >= 0.75:
        reasons.append("high OCR confidence")
    elif ocr_confidence >= 0.55:
        reasons.append("moderate OCR confidence")
    else:
        reasons.append("low OCR confidence")

    # -----------------------------------------------------
    # Bounding-box geometry
    # -----------------------------------------------------

    if box_width and box_height and box_height > 0:

        aspect_ratio = box_width / box_height

        # A registration number is commonly presented as
        # a horizontally oriented text region.
        if 2.0 <= aspect_ratio <= 8.0:
            score += 10
            reasons.append("plate-like text geometry")

    return PlateCandidate(
        text=normalized_text,
        confidence=round(ocr_confidence, 4),
        score=round(score, 2),
        reason=", ".join(reasons),
    )


# ---------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------

def _create_ocr_variants(image_path: str) -> list[np.ndarray]:
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Unable to read image")

    # Keep OCR processing memory bounded.
    max_dimension = 1600

    height, width = image.shape[:2]

    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)

        image = cv2.resize(
            image,
            (
                int(width * scale),
                int(height * scale),
            ),
            interpolation=cv2.INTER_AREA,
        )

    variants = [image]

    # Create only one additional enhanced variant.
    height, width = image.shape[:2]

    scale = 1.5

    upscaled = cv2.resize(
        image,
        (
            int(width * scale),
            int(height * scale),
        ),
        interpolation=cv2.INTER_CUBIC,
    )

    gray = cv2.cvtColor(
        upscaled,
        cv2.COLOR_BGR2GRAY,
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    enhanced_gray = clahe.apply(gray)

    enhanced = cv2.cvtColor(
        enhanced_gray,
        cv2.COLOR_GRAY2BGR,
    )

    variants.append(enhanced)

    return variants


# ---------------------------------------------------------
# OCR extraction
# ---------------------------------------------------------

def extract_text(image_path: str) -> OCRResult:

    reader = get_reader()

    variants = _create_ocr_variants(image_path)

    detections: list[OCRTextDetection] = []
    candidates: list[PlateCandidate] = []

    # Prevent the same text from being added repeatedly
    # when it appears in multiple preprocessing variants.
    seen_text: set[str] = set()

    for variant_index, image in enumerate(variants):

        results = reader.readtext(
            image,
            allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            detail=1,
        )

        for box, text, confidence in results:

            text = text.strip()

            if not text:
                continue

            normalized = normalize_text(text)

            if not normalized:
                continue

            confidence = float(confidence)

            # -------------------------------------------------
            # Bounding box dimensions
            # -------------------------------------------------

            points = np.array(box)

            x_coordinates = points[:, 0]
            y_coordinates = points[:, 1]

            box_width = float(
                x_coordinates.max() - x_coordinates.min()
            )

            box_height = float(
                y_coordinates.max() - y_coordinates.min()
            )

            # -------------------------------------------------
            # Store OCR detection
            # -------------------------------------------------

            detection_key = normalized

            if detection_key not in seen_text:

                detections.append(
                    OCRTextDetection(
                        text=text,
                        normalized_text=normalized,
                        confidence=round(confidence, 4),
                    )
                )

                seen_text.add(detection_key)

            # -------------------------------------------------
            # Candidate scoring
            # -------------------------------------------------

            candidate = _score_plate_candidate(
                normalized_text=normalized,
                ocr_confidence=confidence,
                box_width=box_width,
                box_height=box_height,
            )

            if candidate is not None:
                candidates.append(candidate)

    # ---------------------------------------------------------
    # No candidates
    # ---------------------------------------------------------

    if not candidates:

        return OCRResult(
            detected_text=detections,
            plate_detected=False,
            plate_text=None,
            plate_confidence=None,
            plate_reason=(
                "OCR detected text, but no sufficiently strong "
                "vehicle registration candidate was found."
            ),
        )

    # ---------------------------------------------------------
    # Select strongest candidate
    # ---------------------------------------------------------

    candidates.sort(
        key=lambda candidate: candidate.score,
        reverse=True,
    )

    best = candidates[0]

    # ---------------------------------------------------------
    # Detection threshold
    # ---------------------------------------------------------

    if best.score < 50:

        return OCRResult(
            detected_text=detections,
            plate_detected=False,
            plate_text=None,
            plate_confidence=best.confidence,
            plate_reason=(
                f"Best OCR candidate '{best.text}' did not reach "
                f"the plate-confidence threshold."
            ),
        )

    # ---------------------------------------------------------
    # Successful detection
    # ---------------------------------------------------------

    return OCRResult(
        detected_text=detections,
        plate_detected=True,
        plate_text=best.text,
        plate_confidence=best.confidence,
        plate_reason=(
            f"Candidate '{best.text}' was selected because it has "
            f"{best.reason}."
        ),
    )