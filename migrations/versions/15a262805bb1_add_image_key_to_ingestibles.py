"""add_image_key_to_ingestibles

Revision ID: 15a262805bb1
Revises: a5334e55f04f
Create Date: 2026-03-22 11:02:08.975837+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "15a262805bb1"
down_revision: str | Sequence[str] | None = "a5334e55f04f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "foods",
        sa.Column("image_key", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True),
    )
    op.add_column(
        "drinks",
        sa.Column("image_key", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("drinks", "image_key")
    op.drop_column("foods", "image_key")
