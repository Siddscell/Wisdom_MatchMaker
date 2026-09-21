# Decisions

Choices made where the spec was silent, and every deliberate deviation. One line each: decision, then reason.

## Matching

- **Embedding text is `"{product} | {notes}"`, without the category** (spec: `… | category: X | …`). Reason: category is already a hard filter. A shared suffix on both sides raised similarity between unrelated same-category products by 0.06–0.10 and compressed the useful range (measured: with it, "copper wire" outranked "mild steel tubes" for "MS pipes").
- **`SEMANTIC_FLOOR=0.65`, `SEMANTIC_RANGE=0.28`** (spec example: 0.55 / 0.35). Reason: tuned on labelled seed pairs. Wrong notifications fell from 13 to 1 with 36/37 true matches kept (table in AI_MATCHING.md). The spec puts these constants in config.
- **Price and budget filter use the requirement's quantity converted to the offering's unit** (`unit_price × required_qty`), not the offering's available quantity. Reason: the buyer pays for what they need, and `unit_price` is per offering unit.
- **All hard filters, including the haversine delivery radius, run in SQL** before the top-K vector search. Reason: filtering after retrieval could let excluded rows take the K slots.
- **Records without an embedding are skipped as candidates** until their own background job embeds them. Reason: the model can fail to load, and a zero or fake vector would produce nonsense scores.
- **No zero-vector fallback when the model cannot load** (replaces the earlier fallback). Matching raises and logs, `/health` shows `model_loaded: false`, and `POST /api/dev/rematch` retries. Reason: silent garbage matches are worse than a visible failure.
- **Matches that fall out of an item's top 10 on a re-run are kept, not deleted.** Reason: never lose a match someone may already have been notified about or acted on.
- **Notify-once is enforced by a conditional `UPDATE … WHERE status='new'`.** Reason: it stays correct under concurrent matching runs without locks.
- **Seed data carries coordinates.** Reason: a deterministic demo that works offline and shows distance filtering. User-entered records are geocoded.
- **Geocoding misses ("no such place") are cached; network errors are not.** Reason: don't hammer Nominatim for unknown places, but retry after transient failures.
- **No update endpoints for requirements/offerings.** Reason: not in the API table. "Re-embed on change" therefore has nothing to trigger yet, and matching still runs on create and on rematch.

## API and data

- **Emails are trimmed and lower-cased** on input and in `email` filters. Reason: "acting as" lookups must not depend on capitalisation.
- **Reserved TLDs (`.test`, `.local`, …) are rejected** by email validation. Seed data uses `*.example.com`. Reason: default `email-validator` behaviour, and fine for real addresses.
- **Unknown request fields are rejected (422).** Reason: catches client typos early.
- **Response keys are snake_case everywhere** (the previous `/api/meta` used camelCase). Reason: one convention across the API.
- **`/api/meta` also returns `dev_mode`.** Reason: the frontend shows the outbox link and seed button only in development.
- **`/health` returns 503 when the database check fails.** Reason: load balancers and uptime checks read the status code.
- **Unhandled errors are converted to the standard error shape by a middleware inside CORS.** Reason: otherwise the browser sees a 500 without CORS headers as an opaque network error.
- **`score_breakdown` is not returned by the API.** Reason: the spec says it is not shown in the UI. It stays in the database for debugging and training.
- **List endpoints have a `limit`** (matches 500, notifications 100, outbox 200). Reason: bounded responses.

## Database and infrastructure

- **Alembic is kept, but only as a runner for the plain SQL files** in `supabase/migrations/` (they remain the source of truth). Reason: gives people without `psql` a one-command setup and tracks what was applied. RLS is also enabled on `alembic_version`, because Supabase exposes `public` tables to the anon key.
- **Migration 0002 creates a `nologin` `anon` role if missing and adds `notifications` to `supabase_realtime` only if that publication exists.** Reason: the same files work on Supabase and on plain Postgres (tests, CI), and Realtime does not fire without the publication.
- **Demo-grade caveat: the `anon` select policy on `notifications` lets anyone holding the anon key read *all* notifications** (recipient emails and messages). Reason: Realtime needs a read policy and there is no login. With real auth, restrict it to `recipient_email = auth.email()`.
- **The DB engine disables psycopg prepared statements** (`prepare_threshold=None`). Reason: safe behind any Supabase pooler mode.
- **`postgresql://` URLs are rewritten to `postgresql+psycopg://`.** Reason: Supabase's copy-paste URL then just works.
- **CI runs database tests against a `pgvector/pgvector:pg16` GitHub service container.** Reason: the matching tests need real pgvector. This adds no Docker files to the repo (the spec's non-goal).
- **Database tests refuse to run unless the database name contains "test".** Reason: they drop the `public` schema.
- **`SMTP` backend also records every email in `email_outbox`** (with `sent_at` on success). Reason: an audit trail, and a failed send is never lost.

## Frontend

- **No `@hookform/resolvers`: an 8-line zod resolver lives in `src/lib/schemas.js`.** Reason: avoids a dependency for a few lines.
- **ESLint `react/prop-types` is off.** Reason: plain JavaScript without PropTypes. Props are documented with JSDoc.
- **The frontend accepts `VITE_SUPABASE_ANON_KEY` or `VITE_SUPABASE_PUBLISHABLE_KEY`.** Reason: Supabase renamed the anon key to "publishable".
- **Notification polling continues while the tab is hidden** (`refetchIntervalInBackground`). Reason: the bell count is current when the user returns. Other lists pause in the background.
- **Match lists and the summary refresh every 10 seconds.** Reason: matching finishes after the form response, and fair matches (< 70) produce no notification to trigger a refresh.
- **Accept/Reject is available in the portals as well as the dashboard.** Reason: it's where a user reviews their own matches. No new endpoint was needed.
- **Currency is not modelled.** Budgets and prices are plain numbers assumed to be in one currency.
- **Fonts load from Google Fonts** (Fraunces + IBM Plex Sans) with system fallbacks. Reason: a distinctive pairing with no bundled font files.
