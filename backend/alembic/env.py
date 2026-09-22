"""Alembic runs the plain SQL files in supabase/migrations (the source of truth) and tracks
which ones were applied. Usage from backend/: alembic upgrade head"""

from alembic import context
from sqlalchemy import create_engine, pool

from app.config import get_settings

connectable = create_engine(get_settings().DATABASE_URL, poolclass=pool.NullPool)
with connectable.connect() as connection:
    context.configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()
    # Supabase exposes public tables to the anon key; keep Alembic's bookkeeping private too.
    connection.exec_driver_sql("alter table alembic_version enable row level security")
    connection.commit()
