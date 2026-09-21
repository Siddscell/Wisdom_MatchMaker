# Ownership transfer

How to hand the running system and its data to another owner. Pick (a), (b) or (c), then do (d).

## (a) Transfer the Supabase project

Keeps the same database, URL and data.

1. The new owner creates (or joins) a Supabase **organization**.
2. The current owner opens the project → **Project Settings → General → Transfer project** and
   picks the target organization. The current owner must be an Owner of the source organization
   and a member of the target one. Check the target organization's plan limits first.
3. After the transfer, remove the old owner from the target organization if they should lose access.
4. Rotate the secrets in (d). The connection string host stays the same, but the password should not.

## (b) Dump and restore into another Postgres

Use this for a different provider or a self-hosted server. It needs Postgres with `pgvector`.

```bash
# on the old database (use the direct connection string)
pg_dump "$OLD_URL" --no-owner --no-privileges --format=custom \
  --schema=public --file=matchmaking.dump

# on the new database
psql "$NEW_URL" -c "create extension if not exists vector;"
pg_restore --no-owner --no-privileges --dbname="$NEW_URL" matchmaking.dump
```

Then point `DATABASE_URL` at the new database and check `/health`. On plain Postgres the
Realtime publication does not exist. That's fine: the frontend falls back to polling.

## (c) Rebuild from the repository

Use this for a fresh, empty system (no data carried over).

1. Create a new Supabase project (or any Postgres with pgvector).
2. Run `supabase/migrations/0001_init.sql`, then `0002_indexes_rls.sql` (SQL editor or `psql`),
   or `alembic upgrade head` from `backend/`.
3. Fill `backend/.env` and `frontend/.env` from `.env.example` and start the app (see README).
4. Optional: load the demo data from the dashboard, or `POST /api/dev/seed`.

## (d) Secrets to rotate after any transfer

| Secret | Where | Why |
|---|---|---|
| Database password | Supabase → Project Settings → Database → Reset password; update `DATABASE_URL` | The old owner knows it; it bypasses RLS. |
| `service_role` key / secret keys | Supabase → Project Settings → API (roll keys) | Full access if ever used anywhere. The app does not need it. |
| anon / publishable key | same page; update `VITE_SUPABASE_ANON_KEY` and rebuild the frontend | Read access to notifications (see DECISIONS). |
| JWT secret | Supabase → Project Settings → API | Signs all Supabase tokens. |
| SMTP credentials | your mail provider; update `SMTP_*` | Sending as your domain. |
| GitHub access | repository settings: collaborators, deploy keys, Actions secrets | Code and CI. |

Also review: Supabase organization members, database roles created by hand, and any backups
or dumps copied to personal machines during the move.
