"""create citus tables

Revision ID: c170093a26a3
Revises: acc01156a51a
Create Date: 2026-03-21 11:53:53.454039+00:00

"""

from collections.abc import Sequence

from alembic import op

from migrations.helpers import citus_available

# revision identifiers, used by Alembic.
revision: str = "c170093a26a3"
down_revision: str | Sequence[str] | None = "acc01156a51a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    if not citus_available():
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS citus")

    # --- Reference tables (replicated to every shard node) ---
    op.execute("SELECT create_reference_table('foods')")
    op.execute("SELECT create_reference_table('drinks')")
    op.execute("SELECT create_reference_table('users')")
    op.execute("SELECT create_reference_table('user_oauth')")
    op.execute("SELECT create_reference_table('user_profiles')")

    # --- Distributed tables (sharded by user_id, all co-located) ---
    op.execute("SELECT create_distributed_table('meals', 'user_id')")
    op.execute("SELECT create_distributed_table('meal_foods', 'user_id', colocate_with => 'meals')")
    op.execute("SELECT create_distributed_table('meal_drinks', 'user_id', colocate_with => 'meals')")
    op.execute("SELECT create_distributed_table('meal_summaries', 'user_id', colocate_with => 'meals')")
    op.execute("SELECT create_distributed_table('periodic_summaries', 'user_id', colocate_with => 'meals')")


def downgrade() -> None:
    """Downgrade schema."""
    if not citus_available():
        return

    op.execute("SELECT undistribute_table('periodic_summaries')")
    op.execute("SELECT undistribute_table('meal_summaries')")
    op.execute("SELECT undistribute_table('meal_drinks')")
    op.execute("SELECT undistribute_table('meal_foods')")
    op.execute("SELECT undistribute_table('meals')")
    op.execute("SELECT undistribute_table('user_profiles')")
    op.execute("SELECT undistribute_table('user_oauth')")
    op.execute("SELECT undistribute_table('users')")
    op.execute("SELECT undistribute_table('drinks')")
    op.execute("SELECT undistribute_table('foods')")
