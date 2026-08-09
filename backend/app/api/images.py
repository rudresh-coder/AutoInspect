from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.image import ImageUploadResponse
from backend.app.services.image_service import create_image_record


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

    return ImageUploadResponse(
        processing_id=image_record.id,
        status=image_record.status,
        filename=image_record.original_filename,
        created_at=image_record.created_at,
    )