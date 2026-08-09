from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ImageAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    overall_score: float | None
    quality_score: float | None
    blur_score: float | None
    exposure_score: float | None
    contrast_score: float | None

    plate_detected: bool
    plate_text: str | None
    plate_confidence: float | None

    exact_duplicate: bool
    duplicate_similarity: float | None

    explanation: str | None

    created_at: datetime
    updated_at: datetime


class ImageStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    processing_id: str
    filename: str
    status: str

    file_size: int
    width: int
    height: int

    created_at: datetime
    updated_at: datetime

    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    error_message: str | None

    analysis: ImageAnalysisResponse | None = None