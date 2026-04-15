from alembic import op
from sqlalchemy import text


def citus_available() -> bool:
    conn = op.get_bind()
    result = conn.execute(text("SELECT COUNT(*) FROM pg_available_extensions WHERE name = 'citus'"))
    return bool(result.scalar())
