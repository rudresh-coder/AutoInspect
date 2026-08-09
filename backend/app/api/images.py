from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from rq import Retry
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.image import Image
from backend.app.schemas.analysis import (
    ImageAnalysisResponse,
    ImageStatusResponse,
)
from backend.app.schemas.image import ImageUploadResponse
from backend.app.services.image_service import create_image_record
from backend.app.worker.queue import image_processing_queue
from backend.app.worker.tasks import process_image


router = APIRouter(
    prefix="/api/v1/images",
    tags=["Images"],
)


@router.post(
    "",
    response_model=ImageUploadResponse,
    status_code=202,
)
def upload_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    image_record = create_image_record(
        db=db,
        upload=image,
    )

    image_processing_queue.enqueue(
        process_image,
        image_record.id,
        retry=Retry(max=2, interval=[5, 15]),
    )

    return ImageUploadResponse(
        processing_id=image_record.id,
        status=image_record.status,
        filename=image_record.original_filename,
        created_at=image_record.created_at,
    )


@router.get(
    "/{processing_id}",
    response_model=ImageStatusResponse,
)
def get_image_status(
    processing_id: str,
    db: Session = Depends(get_db),
):
    image = (
        db.query(Image)
        .filter(Image.id == processing_id)
        .one_or_none()
    )

    if image is None:
        raise HTTPException(
            status_code=404,
            detail="Image processing ID not found",
        )

    analysis = image.analysis

    return ImageStatusResponse(
        processing_id=image.id,
        filename=image.original_filename,
        status=image.status,
        file_size=image.file_size,
        width=image.width,
        height=image.height,
        created_at=image.created_at,
        updated_at=image.updated_at,
        processing_started_at=image.processing_started_at,
        processing_completed_at=image.processing_completed_at,
        error_message=image.error_message,
        analysis=(
            ImageAnalysisResponse.model_validate(analysis)
            if analysis is not None
            else None
        ),
    )