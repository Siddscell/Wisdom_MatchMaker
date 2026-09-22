"""Apply supabase/migrations/0004 (listing images and CLIP embeddings).

Revision ID: 0003_images
Revises: 0002_auth_ml
"""

from pathlib import Path

from alembic import op

revision = "0003_images"
down_revision = "0002_auth_ml"
branch_labels = None
depends_on = None

MIGRATIONS = Path(__file__).resolve().parents[3] / "supabase" / "migrations"


def upgrade() -> None:
    op.execute((MIGRATIONS / "0004_images.sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    for table in ("requirements", "offerings"):
        op.execute(
            f"alter table {table} drop column image_url, drop column image_embedding, "
            "drop column clip_text_embedding"
        )
