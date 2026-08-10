import hashlib
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image as PILImage
from PIL import UnidentifiedImageError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.image import Image
from backend.app.services.storage import (
    delete_file,
    r2_is_configured,
    upload_file,
)


def validate_content_type(upload: UploadFile) -> None:
    if upload.content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "code": "UNSUPPORTED_IMAGE_TYPE",
                "message": "Only JPEG, PNG, and WebP images are supported.",
            },
        )


def save_upload_file(
    upload: UploadFile,
    processing_id: str,
) -> tuple[str, int]:
    extension = Path(upload.filename or "").suffix.lower()

    if not extension:
        extension = ".img"

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension,
    )

    destination = Path(temp_file.name)

    total_size = 0

    try:
        with temp_file:
            while True:
                chunk = upload.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if (
                    total_size
                    > settings.max_file_size_mb * 1024 * 1024
                ):
                    raise HTTPException(
                        status_code=(
                            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                        ),
                        detail={
                            "code": "IMAGE_TOO_LARGE",
                            "message": (
                                f"Image exceeds the maximum allowed "
                                f"size of "
                                f"{settings.max_file_size_mb} MB."
                            ),
                        },
                    )

                temp_file.write(chunk)

        return str(destination), total_size

    except HTTPException:
        destination.unlink(missing_ok=True)
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

    local_path, file_size = save_upload_file(
        upload,
        processing_id,
    )

    extension = Path(
        upload.filename or ""
    ).suffix.lower()

    if not extension:
        extension = ".img"

    object_key = (
        f"images/{processing_id}{extension}"
    )

    uploaded_to_r2 = False

    try:
        width, height, _ = inspect_image(local_path)
        sha256_hash = calculate_sha256(local_path)

        if r2_is_configured():
            upload_file(
                local_path=local_path,
                object_key=object_key,
                content_type=upload.content_type,
            )

            uploaded_to_r2 = True

            storage_path = object_key

        else:
            storage_path = local_path

        image = Image(
            id=processing_id,
            original_filename=os.path.basename(
                upload.filename or "unknown"
            ),
            storage_path=storage_path,
            mime_type=(
                upload.content_type
                or "application/octet-stream"
            ),
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
        if uploaded_to_r2:
            delete_file(object_key)

        raise

    except Exception as exc:
        db.rollback()

        if uploaded_to_r2:
            delete_file(object_key)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "IMAGE_PROCESSING_FAILED",
                "message": (
                    "Unable to process uploaded "
                    "image metadata."
                ),
            },
        ) from exc

    finally:
        if r2_is_configured():
            os.unlink(local_path)