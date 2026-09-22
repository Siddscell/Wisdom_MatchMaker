"""Apply supabase/migrations/0003 (model_state, per-user notification policy).

Revision ID: 0002_auth_ml
Revises: 0001_initial_schema
"""

from pathlib import Path

from alembic import op

revision = "0002_auth_ml"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

MIGRATIONS = Path(__file__).resolve().parents[3] / "supabase" / "migrations"


def upgrade() -> None:
    op.execute((MIGRATIONS / "0003_auth_ml.sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute('drop table if exists model_state; drop policy if exists "own_notifications" on notifications')
