import re
from dataclasses import dataclass

import easyocr


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


_reader = easyocr.Reader(
    ["en"],
    gpu=False,
)


def normalize_text(text: str) -> str:
    return re.sub(
        r"[^A-Z0-9]",
        "",
        text.upper(),
    )


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
    }

    return text in common_words


def _score_plate_candidate(
    normalized_text: str,
    ocr_confidence: float,
) -> PlateCandidate | None:

    length = len(normalized_text)

    if length < 6 or length > 12:
        return None

    if not any(char.isalpha() for char in normalized_text):
        return None

    if not any(char.isdigit() for char in normalized_text):
        return None

    if _is_obvious_non_plate(normalized_text):
        return None

    score = 0.0
    reasons = []

    # Indian registration plates are commonly
    # alphanumeric and generally fall within this range.
    if 8 <= length <= 10:
        score += 30
        reasons.append("valid registration-like length")
    else:
        score += 15

    digit_count = sum(char.isdigit() for char in normalized_text)
    letter_count = sum(char.isalpha() for char in normalized_text)

    if digit_count >= 2:
        score += 20
        reasons.append("contains multiple digits")

    if letter_count >= 2:
        score += 20
        reasons.append("contains multiple letters")

    confidence_score = ocr_confidence * 30
    score += confidence_score

    if ocr_confidence >= 0.7:
        reasons.append("high OCR confidence")
    elif ocr_confidence >= 0.5:
        reasons.append("moderate OCR confidence")
    else:
        reasons.append("low OCR confidence")

    return PlateCandidate(
        text=normalized_text,
        confidence=round(ocr_confidence, 4),
        score=round(score, 2),
        reason=", ".join(reasons),
    )


def extract_text(image_path: str) -> OCRResult:
    results = _reader.readtext(image_path)

    detections: list[OCRTextDetection] = []
    candidates: list[PlateCandidate] = []

    for _, text, confidence in results:
        text = text.strip()

        if not text:
            continue

        normalized = normalize_text(text)

        if not normalized:
            continue

        confidence = float(confidence)

        detections.append(
            OCRTextDetection(
                text=text,
                normalized_text=normalized,
                confidence=round(confidence, 4),
            )
        )

        candidate = _score_plate_candidate(
            normalized_text=normalized,
            ocr_confidence=confidence,
        )

        if candidate is not None:
            candidates.append(candidate)

    candidates.sort(
        key=lambda candidate: candidate.score,
        reverse=True,
    )

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

    best = candidates[0]

    # Require a minimum score before declaring
    # that a registration plate was detected.
    if best.score < 55:
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