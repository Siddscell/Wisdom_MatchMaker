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

## API and data

- **Emails are trimmed and lower-cased** everywhere they are compared. Reason: ownership and notification lookups must not depend on capitalisation.
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
- **Notifications are readable only by their recipient** (migration 0003: `authenticated` users, `recipient_email = auth.jwt() ->> 'email'`), replacing the earlier demo policy that let the anon key read all of them.
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
- **Currency is not modelled.** Budgets and prices are plain numbers assumed to be in one currency.
- **Fonts load from Google Fonts** (Fraunces + IBM Plex Sans) with system fallbacks. Reason: a distinctive pairing with no bundled font files.

## Accounts, dashboards and learning (added after the original spec)

- **Login is now in scope** (the spec listed it as a non-goal): Supabase Auth, email + password. Reason: requested, so suppliers and clients can register and get their own dashboard.
- **The backend verifies tokens by calling Supabase's `/auth/v1/user`**, not by checking JWTs locally. Reason: works with both legacy and new signing keys and needs no JWT library. Cost: one round trip per logged-in request (marked `ponytail:` for JWKS verification later).
- **Role (client/supplier) and company are stored in the Supabase user metadata at sign-up.** Clients can only post requirements, suppliers only offerings.
- **A listing belongs to the account whose verified email created it** (`contact_email`, set from the token and no longer a form field). There's no separate owner column. Reason: the email already identifies the owner, and seed listings stay claimable by registering their email. Caveat: changing the account email loses ownership.
- **Public dashboard: listings and match scores without contact emails, budgets or prices; no notifications tab.** Matches show contact emails only to the two parties, and only once accepted.
- **Only a party to a match may accept or reject it** (403 otherwise).
- **Edits re-embed only when the product or notes text changed, and re-geocode only when the location changed**, then re-match. Closing a listing stops new matching, and reopening re-matches.
- **The learned ranker is a numpy logistic regression, not LightGBM.** Reason: with tens of labels, gradient-boosted trees overfit and a new dependency isn't justified; the weights blend with the prior until data accumulates (see AI_MATCHING.md).
- **No cross-encoder reranker.** Reason: measured, and none beat the existing embeddings on our data (table in AI_MATCHING.md).
- **Category suggestion comes from the nearest existing listing (1-NN), not zero-shot.** Reason: 76/76 vs 47/76 on the seed data. It's only a suggestion that fills an empty field, and users can change it.
- **Kept as code, not learned:** unit conversion and the hard filters. Reason: they're facts or explicit business limits (all configurable), and a model would only learn them approximately.
- **The frontend smoke test no longer covers the logged-out redirect.** Reason: jsdom's `AbortSignal` is incompatible with React Router navigation in tests; the redirect is one `<Navigate>`.

## India

- **The platform targets India:** sample data uses Indian companies, cities and rupee prices; money shows as ₹ with Indian digit grouping (`en-IN`, e.g. ₹1,50,000); form hints use Indian cities. Reason: requested.
- **Geocoding prefers India but is not restricted to it** (Nominatim `viewbox` over India, `bounded=0`). Reason: `countrycodes=in` put "Dubai" in Kerala, which broke the international delivery scope; the bias still keeps "Nagpur" and "Thane" in India. Known gap: a bare "Shanghai" still resolves to a village in Punjab, so write "Shanghai, China".
- **Pairs with a semantic sub-score below `MIN_SEMANTIC` (0.1) are never stored.** Reason: price, quantity, delivery and location alone add up to 60, so a cheap, nearby "Pens" offering matched a "Pipe" requirement. 0.1 keeps "MS pipes" ↔ "mild steel tubes" (0.14).
- **`quintal` (100 kg) added as a unit.** Reason: standard in Indian agricultural trade; converts within the mass family.
- **Delivery radii unchanged** (local 100 km, regional 500 km, national 5000 km). Reason: 5000 km covers India end to end.
- **Currency is still not a field:** all amounts are treated as INR.

## Wisdom brand, photos and visual matching

- **Product name Wisdom; green gradients, black and white; one typeface (Instrument Sans).** The hero art is hand-made SVG (hills and two discs, supply and demand), not stock or generated imagery. Reason: requested; loads instantly and has no licensing.
- **The landing page shows live platform numbers instead of partner logos.** Reason: there are no partners yet, and fake logos would mislead.
- **One photo per listing**, uploaded by the browser straight to the public Supabase Storage bucket `listing-images`, into a folder named after the user's id (a storage policy enforces this). The listing stores only the URL. Reason: simplest path; several photos per listing can come later with a small table.
- **The backend only accepts image URLs from that bucket.** Reason: it downloads the image to embed it, so any other URL would let users make the server fetch arbitrary addresses (SSRF).
- **CLIP ViT-B/32 through fastembed** for photos; calibrated separately for photo↔photo and photo↔text on sample photos (AI_MATCHING.md). Reason: runs locally at no cost, and the library was already a dependency.
- **When the text is confident (text semantic ≥ `TEXT_CONFIDENT`, 0.5) a photo can only raise the meaning sub-score; when the text is unsure, the photo evidence replaces it.** Reason: CLIP was right 15/20 times, not enough to veto confident text. But short names give unsure text ("Mirrors" ↔ "glass robot" cos 0.72, close to the true pair "MS pipes" ↔ "mild steel tubes" at 0.69), and on live data the photos separated every pair (true: photo↔photo ≥ 0.93, photo↔text ≥ 0.27; false: ≤ 0.57, ≤ 0.20).
- **A photo that can't be downloaded or read is skipped** (logged); matching continues on text. Reason: never block a listing on its photo.
- **Match emails are sent through Gmail SMTP** when `SMTP_PASSWORD` (a Google App Password) is set; the outbox always keeps a copy. The password is only ever typed into `backend/.env` and Supabase by the owner.
