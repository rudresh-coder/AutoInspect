import hashlib
import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image as PILImage
from PIL import UnidentifiedImageError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.image import Image


def validate_content_type(upload: UploadFile) -> None:
    if upload.content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "code": "UNSUPPORTED_IMAGE_TYPE",
                "message": "Only JPEG, PNG, and WebP images are supported.",
            },
        )


def save_upload_file(upload: UploadFile, processing_id: str) -> tuple[str, int]:
    upload_directory = Path(settings.upload_dir)
    upload_directory.mkdir(parents=True, exist_ok=True)

    extension = Path(upload.filename or "").suffix.lower()

    if not extension:
        extension = ".img"

    filename = f"{processing_id}{extension}"
    destination = upload_directory / filename

    total_size = 0

    try:
        with destination.open("wb") as output_file:
            while True:
                chunk = upload.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > settings.max_file_size_mb * 1024 * 1024:
                    destination.unlink(missing_ok=True)

                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail={
                            "code": "IMAGE_TOO_LARGE",
                            "message": (
                                f"Image exceeds the maximum allowed size "
                                f"of {settings.max_file_size_mb} MB."
                            ),
                        },
                    )

                output_file.write(chunk)

    except HTTPException:
        raise

    except Exception as exc:
        destination.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "IMAGE_STORAGE_FAILED",
                "message": "Unable to store uploaded image.",
            },
        ) from exc

    return str(destination), total_size


def inspect_image(
    file_path: str,
) -> tuple[int, int, str]:
    try:
        with PILImage.open(file_path) as image:
            image.verify()

        with PILImage.open(file_path) as image:
            width, height = image.size
            image_format = image.format or "UNKNOWN"

        return width, height, image_format

    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_IMAGE",
                "message": "The uploaded file is not a valid readable image.",
            },
        ) from exc


def calculate_sha256(file_path: str) -> str:
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


def create_image_record(
    db: Session,
    upload: UploadFile,
) -> Image:

    validate_content_type(upload)

    processing_id = str(uuid4())

    storage_path, file_size = save_upload_file(
        upload,
        processing_id,
    )

    try:
        width, height, _ = inspect_image(storage_path)
        sha256_hash = calculate_sha256(storage_path)

        image = Image(
            id=processing_id,
            original_filename=os.path.basename(
                upload.filename or "unknown"
            ),
            storage_path=storage_path,
            mime_type=upload.content_type or "application/octet-stream",
            file_size=file_size,
            width=width,
            height=height,
            sha256_hash=sha256_hash,
            status="pending",
        )

        db.add(image)
        db.commit()
        db.refresh(image)

        return image

    except HTTPException:
        os.unlink(storage_path)
        raise

    except Exception as exc:
        db.rollback()
        os.unlink(storage_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "IMAGE_PROCESSING_FAILED",
                "message": "Unable to process uploaded image metadata.",
            },
        ) from exc