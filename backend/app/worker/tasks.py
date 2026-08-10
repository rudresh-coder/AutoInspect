import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.analysis.pipeline import run_analysis
from backend.app.core.database import SessionLocal
from backend.app.models.image import Image
from backend.app.services.storage import download_file, r2_is_configured


def process_image(processing_id: str) -> None:
    db: Session = SessionLocal()

    temp_path: str | None = None
    original_storage_path: str | None = None
    image: Image | None = None

    try:
        image = db.get(Image, processing_id)

        if image is None:
            raise ValueError(
                f"Image {processing_id} was not found"
            )

        image.status = "processing"
        image.processing_started_at = datetime.now(timezone.utc)
        image.error_message = None

        db.commit()

        original_storage_path = image.storage_path

        # When using R2, download the image to a temporary
        # local file because the analysis pipeline expects
        # a filesystem path.
        if r2_is_configured():
            suffix = Path(
                original_storage_path
            ).suffix or ".img"

            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
            )

            temp_path = temp_file.name
            temp_file.close()

            download_file(
                object_key=original_storage_path,
                local_path=temp_path,
            )

            image.storage_path = temp_path

        # Run the actual analysis pipeline.
        run_analysis(
            db=db,
            image=image,
        )

        image.status = "completed"
        image.processing_completed_at = datetime.now(timezone.utc)

        db.commit()

    except Exception as exc:
        db.rollback()

        image = db.get(Image, processing_id)

        if image is not None:
            image.status = "failed"
            image.error_message = str(exc)

            db.commit()

        raise

    finally:
        # Restore the persistent storage path in the SQLAlchemy
        # object so it is never accidentally persisted as a
        # temporary local path.
        if (
            original_storage_path is not None
            and image is not None
        ):
            image.storage_path = original_storage_path

        # Remove the temporary downloaded image.
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

        db.close()