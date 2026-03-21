"""add meal fks

Revision ID: 467b6206bb7d
Revises: 0003
Create Date: 2026-03-21 12:11:41.241605+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "467b6206bb7d"
down_revision: str | Sequence[str] | None = "c170093a26a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_foreign_key(
        "fk_meal_foods_meal",
        "meal_foods",
        "meals",
        ["user_id", "meal_id"],
        ["user_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_meal_drinks_meal",
        "meal_drinks",
        "meals",
        ["user_id", "meal_id"],
        ["user_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_meal_summaries_meal",
        "meal_summaries",
        "meals",
        ["user_id", "meal_id"],
        ["user_id", "id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_meal_summaries_meal", "meal_summaries", type_="foreignkey")
    op.drop_constraint("fk_meal_drinks_meal", "meal_drinks", type_="foreignkey")
    op.drop_constraint("fk_meal_foods_meal", "meal_foods", type_="foreignkey")
