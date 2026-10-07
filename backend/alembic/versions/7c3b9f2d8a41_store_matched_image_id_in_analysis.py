"""store matched image id in image analyses

Revision ID: 7c3b9f2d8a41
Revises: d1c2aba16051
Create Date: 2026-10-07 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c3b9f2d8a41"
down_revision: Union[str, Sequence[str], None] = "d1c2aba16051"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "image_analyses",
        sa.Column(
            "matched_image_id",
            sa.String(length=36),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_image_analyses_matched_image_id"),
        "image_analyses",
        ["matched_image_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_image_analyses_matched_image_id_images",
        "image_analyses",
        "images",
        ["matched_image_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_image_analyses_matched_image_id_images",
        "image_analyses",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_image_analyses_matched_image_id"),
        table_name="image_analyses",
    )
    op.drop_column("image_analyses", "matched_image_id")