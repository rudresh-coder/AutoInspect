from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class QualityAnalysisResult:
    blur_score: float
    exposure_score: float
    contrast_score: float
    quality_score: float
    explanation: str


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(value, maximum))


def analyze_quality(image_path: str) -> QualityAnalysisResult:
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Unable to read image")

    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # ---------------------------------------------------------
    # 1. Blur / sharpness
    # ---------------------------------------------------------
    laplacian_variance = float(
        cv2.Laplacian(grayscale, cv2.CV_64F).var()
    )

    blur_score = _clamp(
        (laplacian_variance / 500.0) * 100.0
    )

    # ---------------------------------------------------------
    # 2. Exposure
    # ---------------------------------------------------------
    mean_brightness = float(np.mean(grayscale))

    exposure_distance = abs(mean_brightness - 128.0)

    exposure_score = _clamp(
        100.0 - (exposure_distance / 128.0) * 100.0
    )

    # ---------------------------------------------------------
    # 3. Contrast
    # ---------------------------------------------------------
    contrast_std = float(np.std(grayscale))

    contrast_score = _clamp(
        (contrast_std / 64.0) * 100.0
    )

    # ---------------------------------------------------------
    # 4. Overall quality
    # ---------------------------------------------------------
    quality_score = round(
        (
            blur_score * 0.4
            + exposure_score * 0.3
            + contrast_score * 0.3
        ),
        2,
    )

    # ---------------------------------------------------------
    # 5. Explainability
    # ---------------------------------------------------------
    reasons = []

    if blur_score < 40:
        reasons.append("image appears blurry")
    elif blur_score >= 75:
        reasons.append("image has good sharpness")
    else:
        reasons.append("image has moderate sharpness")

    if exposure_score < 40:
        reasons.append("exposure is poor")
    elif exposure_score >= 75:
        reasons.append("exposure is good")
    else:
        reasons.append("exposure is moderate")

    if contrast_score < 40:
        reasons.append("contrast is low")
    elif contrast_score >= 75:
        reasons.append("contrast is good")
    else:
        reasons.append("contrast is moderate")

    explanation = (
        f"Quality score is {quality_score}/100 because "
        + ", ".join(reasons)
        + "."
    )

    return QualityAnalysisResult(
        blur_score=round(blur_score, 2),
        exposure_score=round(exposure_score, 2),
        contrast_score=round(contrast_score, 2),
        quality_score=quality_score,
        explanation=explanation,
    )