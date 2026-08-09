from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.analysis.pipeline import run_analysis
from backend.app.core.database import SessionLocal
from backend.app.models.image import Image


def process_image(processing_id: str) -> None:
    db: Session = SessionLocal()

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
        db.close()