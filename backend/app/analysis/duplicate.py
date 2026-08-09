from dataclasses import dataclass

import imagehash
from PIL import Image as PILImage
from sqlalchemy.orm import Session

from backend.app.models.image import Image


@dataclass
class DuplicateResult:
    exact_duplicate: bool
    duplicate_similarity: float | None
    matched_image_id: str | None
    reason: str


def calculate_phash(image_path: str) -> str:
    """Calculate a perceptual hash for an image."""
    with PILImage.open(image_path) as image:
        return str(imagehash.phash(image))


def analyze_duplicates(
    db: Session,
    image: Image,
) -> DuplicateResult:

    # ---------------------------------------------------------
    # 1. Exact duplicate detection using SHA-256
    # ---------------------------------------------------------
    exact_match = (
        db.query(Image)
        .filter(
            Image.sha256_hash == image.sha256_hash,
            Image.id != image.id,
        )
        .first()
    )

    if exact_match is not None:
        return DuplicateResult(
            exact_duplicate=True,
            duplicate_similarity=100.0,
            matched_image_id=exact_match.id,
            reason=(
                "Exact duplicate detected. "
                f"The image has the same SHA-256 hash as "
                f"image {exact_match.id}."
            ),
        )

    # ---------------------------------------------------------
    # 2. Calculate perceptual hash
    # ---------------------------------------------------------
    phash = calculate_phash(image.storage_path)

    # Save the pHash on the image record.
    image.phash = phash

    # ---------------------------------------------------------
    # 3. Find previously hashed images
    # ---------------------------------------------------------
    previous_images = (
        db.query(Image)
        .filter(
            Image.id != image.id,
            Image.phash.isnot(None),
        )
        .all()
    )

    if not previous_images:
        return DuplicateResult(
            exact_duplicate=False,
            duplicate_similarity=None,
            matched_image_id=None,
            reason=(
                "No previous image with a perceptual hash "
                "was available for comparison."
            ),
        )

    current_hash = imagehash.hex_to_hash(phash)

    best_similarity = 0.0
    best_match = None

    # ---------------------------------------------------------
    # 4. Compare pHash values
    # ---------------------------------------------------------
    for previous in previous_images:
        previous_hash = imagehash.hex_to_hash(
            previous.phash
        )

        distance = current_hash - previous_hash

        # pHash uses 64 bits.
        similarity = max(
            0.0,
            100.0 * (1.0 - distance / 64.0),
        )

        if similarity > best_similarity:
            best_similarity = similarity
            best_match = previous

    # ---------------------------------------------------------
    # 5. Classify visual similarity
    # ---------------------------------------------------------
    if best_match is not None and best_similarity >= 90.0:
        return DuplicateResult(
            exact_duplicate=False,
            duplicate_similarity=round(
                best_similarity,
                2,
            ),
            matched_image_id=best_match.id,
            reason=(
                "Visually similar image detected. "
                f"Perceptual similarity with image "
                f"{best_match.id} is "
                f"{best_similarity:.2f}%."
            ),
        )

    return DuplicateResult(
        exact_duplicate=False,
        duplicate_similarity=round(
            best_similarity,
            2,
        ),
        matched_image_id=(
            best_match.id if best_match else None
        ),
        reason=(
            "No significant visual duplicate detected. "
            f"Highest perceptual similarity was "
            f"{best_similarity:.2f}%."
        ),
    )