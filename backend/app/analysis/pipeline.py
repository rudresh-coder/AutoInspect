from sqlalchemy.orm import Session

from backend.app.analysis.ocr import extract_text
from backend.app.analysis.quality import analyze_quality
from backend.app.models.analysis import ImageAnalysis
from backend.app.models.image import Image
from backend.app.analysis.duplicate import analyze_duplicates


def run_analysis(db: Session, image: Image) -> ImageAnalysis:
    quality_result = analyze_quality(image.storage_path)
    ocr_result = extract_text(image.storage_path)

    duplicate_result = analyze_duplicates(db=db, image=image)

    explanation = (
        f"{quality_result.explanation} "
        f"Plate analysis: {ocr_result.plate_reason} "
        f"Duplicate analysis: {duplicate_result.reason}"
    )

    analysis = db.query(ImageAnalysis).filter(
        ImageAnalysis.image_id == image.id
    ).one_or_none()

    if analysis is None:
        analysis = ImageAnalysis(image_id=image.id)
        db.add(analysis)

    analysis.overall_score = quality_result.quality_score
    analysis.quality_score = quality_result.quality_score
    analysis.blur_score = quality_result.blur_score
    analysis.exposure_score = quality_result.exposure_score
    analysis.contrast_score = quality_result.contrast_score
    analysis.plate_detected = ocr_result.plate_detected
    analysis.plate_text = ocr_result.plate_text
    analysis.plate_confidence = ocr_result.plate_confidence
    analysis.explanation = explanation
    analysis.duplicate_detected = duplicate_result.exact_duplicate
    analysis.duplicate_similarity = duplicate_result.duplicate_similarity
    analysis.matched_image_id = duplicate_result.matched_image_id

    db.flush()
    return analysis