"""add_locale_and_translations

Revision ID: d4e5f6a7b8c9
Revises: b3f1a2c4d5e6
Create Date: 2026-03-24 00:00:00.000000+00:00

"""

from collections.abc import Sequence

import pgvector.sqlalchemy.vector
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "15a262805bb1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIMENSION = 768


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "user_profiles",
        sa.Column("locale", sa.String(10), nullable=False, server_default="en-US"),
    )
    op.alter_column("user_profiles", "locale", server_default=None)

    op.create_table(
        "food_translations",
        sa.Column("food_id", sa.String(26), sa.ForeignKey("foods.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("locale", sa.String(10), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSION), nullable=True),
    )

    op.create_table(
        "drink_translations",
        sa.Column("drink_id", sa.String(26), sa.ForeignKey("drinks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("locale", sa.String(10), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSION), nullable=True),
    )

    op.execute(
        "INSERT INTO food_translations (food_id, locale, name, embedding) "
        "SELECT id, 'en-US', name, embedding FROM foods"
    )
    op.execute(
        "INSERT INTO drink_translations (drink_id, locale, name, embedding) "
        "SELECT id, 'en-US', name, embedding FROM drinks"
    )

    op.create_index(
        "ix_food_translations_embedding",
        "food_translations",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.create_index(
        "ix_drink_translations_embedding",
        "drink_translations",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.execute("SELECT create_distributed_table('food_translations', 'food_id')")
    op.execute("SELECT create_distributed_table('drink_translations', 'drink_id')")

    op.drop_index("ix_foods_embedding", table_name="foods", postgresql_using="hnsw")
    op.drop_column("foods", "embedding")
    op.drop_column("foods", "name")

    op.drop_index("ix_drinks_embedding", table_name="drinks", postgresql_using="hnsw")
    op.drop_column("drinks", "embedding")
    op.drop_column("drinks", "name")


def downgrade() -> None:
    """Downgrade schema."""
    vector_col = pgvector.sqlalchemy.vector.VECTOR(dim=EMBEDDING_DIMENSION)

    op.add_column("foods", sa.Column("name", sa.Text(), nullable=False, server_default=""))
    op.add_column("foods", sa.Column("embedding", vector_col, nullable=True))
    op.add_column("drinks", sa.Column("name", sa.Text(), nullable=False, server_default=""))
    op.add_column("drinks", sa.Column("embedding", vector_col, nullable=True))

    op.execute(
        "UPDATE foods f SET name = ft.name, embedding = ft.embedding "
        "FROM food_translations ft WHERE f.id = ft.food_id AND ft.locale = 'en-US'"
    )
    op.execute(
        "UPDATE drinks d SET name = dt.name, embedding = dt.embedding "
        "FROM drink_translations dt WHERE d.id = dt.drink_id AND dt.locale = 'en-US'"
    )

    op.alter_column("foods", "name", server_default=None)
    op.alter_column("drinks", "name", server_default=None)

    op.execute("SELECT undistribute_table('drink_translations')")
    op.execute("SELECT undistribute_table('food_translations')")
    op.drop_index("ix_drink_translations_embedding", table_name="drink_translations", postgresql_using="hnsw")
    op.drop_index("ix_food_translations_embedding", table_name="food_translations", postgresql_using="hnsw")
    op.drop_table("drink_translations")
    op.drop_table("food_translations")

    op.create_index(
        "ix_drinks_embedding",
        "drinks",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_foods_embedding",
        "foods",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.drop_column("user_profiles", "locale")
