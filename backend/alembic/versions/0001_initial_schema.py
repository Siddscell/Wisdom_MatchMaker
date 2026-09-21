"""Apply supabase/migrations/0001 and 0002.

Revision ID: 0001_initial_schema
Revises:
"""

from pathlib import Path

from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

MIGRATIONS = Path(__file__).resolve().parents[3] / "supabase" / "migrations"


def upgrade() -> None:
    for name in ("0001_init.sql", "0002_indexes_rls.sql"):
        op.execute((MIGRATIONS / name).read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute(
        "drop table if exists notifications, email_outbox, geocode_cache, matches, "
        "offerings, requirements cascade; drop type if exists match_status"
    )
