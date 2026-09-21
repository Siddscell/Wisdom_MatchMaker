# AI Supplier–Client Matching Platform — Build Specification

This file is the single source of truth for building the project. Read it fully before writing code.
Where this spec is silent, choose the simplest option that satisfies the goals and record the decision
in `docs/DECISIONS.md` (one line: decision + reason). Do not add features listed under Non-goals.

---

## 1. Goal

A web platform where **clients** submit product requirements and **suppliers** submit offerings.
An **AI matching engine** finds and ranks suitable pairs, stores the results, notifies both sides,
and a **dashboard** shows requirements, offerings, matches and scores/status.

Evaluation criteria (design for these): implementation completeness, AI matching quality,
UI/UX, code quality and structure, documentation and scalability.

### Non-goals (do NOT build)
- Login/passwords, payments, chat between users, mobile apps.
- Per-match "why this match" explanation text or UI.
- A keyword-vs-AI accuracy comparison page.
- Any paid or per-call AI API. The whole system must run with **zero per-use AI cost**.
- Docker/containers (deferred). Do not add Dockerfiles or compose files yet.
- TypeScript. The frontend is plain JavaScript.

### Additions to the original brief (deliberate; keep them)
- `contact_email` on both forms (required, otherwise notifications have nowhere to go).
- `unit` on quantities (a quantity without a unit is ambiguous).
- `delivery_scope` on supplier form (structured form of "delivery capability").
- Match status flow: `new → notified → accepted | rejected`.

---

## 2. Tech stack

| Layer | Choice |
|---|---|
| Frontend | React 18 + Vite in **plain JavaScript (`.jsx`/`.js`, no TypeScript)**, Tailwind CSS, TanStack Query, react-hook-form + zod, React Router |
| Backend | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, psycopg 3, `pgvector` Python package |
| Database | **Supabase** (managed PostgreSQL + pgvector). Standard Postgres only, no Supabase-specific backend code |
| Embeddings | `fastembed` (ONNX, low memory) with model `BAAI/bge-small-en-v1.5` (384 dims). Runs locally, free |
| Notifications | In-app (table + Supabase Realtime with polling fallback) + email via pluggable backend |
| Background work | FastAPI `BackgroundTasks` for now; matching logic must be a plain function so it can move to Celery/RQ later |
| Tooling | `ruff` (lint+format), `pytest`, `eslint`+`prettier`, `vitest` (light), GitHub Actions CI. **No Docker for now** |

Portability rule: the backend must work against **any** Postgres with pgvector by changing `DATABASE_URL`.
Only the frontend's optional Realtime subscription is Supabase-specific.

---

## 3. Repository layout

```
.
├── AGENTS.md                  # copy or pointer to this spec
├── README.md                  # plain-language setup + "How the matching works"
├── .env.example
├── .github/workflows/ci.yml
├── docs/
│   ├── ARCHITECTURE.md        # includes a Mermaid diagram
│   ├── AI_MATCHING.md
│   ├── OWNERSHIP_TRANSFER.md  # moving the Supabase project/data to another owner
│   └── DECISIONS.md
├── supabase/migrations/
│   ├── 0001_init.sql
│   └── 0002_indexes_rls.sql
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py            # app factory, CORS, router registration
│   │   ├── config.py          # pydantic-settings, ALL tunables live here
│   │   ├── db.py              # engine/session
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── constants.py       # CATEGORIES, UNITS, DELIVERY_SCOPES
│   │   ├── api/               # thin routers: requirements, offerings, matches,
│   │   │                      #   notifications, dashboard, dev
│   │   ├── services/
│   │   │   ├── embedding.py   # load model once, embed(text) -> list[float]
│   │   │   ├── geo.py         # geocode + haversine, cached
│   │   │   ├── units.py       # unit families + conversion
│   │   │   ├── scoring.py     # PURE functions, no I/O
│   │   │   ├── matching.py    # orchestrates filter -> retrieve -> score -> store
│   │   │   ├── notifications.py
│   │   │   └── email.py       # backends: outbox (default), smtp
│   │   ├── scripts/download_model.py   # one-time embedding model download
│   │   └── seed/seed_data.py
│   └── tests/
└── frontend/
    ├── package.json, vite.config.js, tailwind.config.js, postcss.config.js, index.html
    └── src/{pages,components,api,lib,hooks}/   # .jsx for components/pages, .js for the rest
```

Layering rule: routers → services → models. Routers contain no business logic.
`scoring.py` has no database or network access so it is trivially unit-testable.

---

## 4. Data model (`supabase/migrations/0001_init.sql`)

Migrations are plain SQL files in the repo. The database must be fully rebuildable from them.

```sql
create extension if not exists vector;

create type match_status as enum ('new', 'notified', 'accepted', 'rejected');

create table requirements (
  id                   uuid primary key default gen_random_uuid(),
  client_name          text not null,
  contact_email        text not null,
  product_requirement  text not null,
  category             text not null,
  quantity             numeric not null check (quantity > 0),
  unit                 text not null,
  budget               numeric not null check (budget > 0),  -- TOTAL budget for the full quantity
  location             text not null,
  latitude             double precision,
  longitude            double precision,
  needed_within_days   int not null check (needed_within_days > 0), -- delivery timeline
  notes                text,
  embedding            vector(384),
  status               text not null default 'open',          -- open | closed
  created_at           timestamptz not null default now()
);

create table offerings (
  id                   uuid primary key default gen_random_uuid(),
  supplier_name        text not null,
  contact_email        text not null,
  product_offered      text not null,
  category             text not null,
  available_quantity   numeric not null check (available_quantity > 0),
  unit                 text not null,
  unit_price           numeric not null check (unit_price > 0),
  pricing_notes        text,                                   -- bulk discounts etc. (not used in scoring)
  location             text not null,
  latitude             double precision,
  longitude            double precision,
  lead_time_days       int not null check (lead_time_days >= 0),
  delivery_scope       text not null
                       check (delivery_scope in ('local','regional','national','international')),
  notes                text,
  embedding            vector(384),
  status               text not null default 'active',         -- active | inactive
  created_at           timestamptz not null default now()
);

create table matches (
  id              uuid primary key default gen_random_uuid(),
  requirement_id  uuid not null references requirements(id) on delete cascade,
  offering_id     uuid not null references offerings(id) on delete cascade,
  score           numeric(5,2) not null,        -- 0..100
  score_breakdown jsonb not null,               -- stored for debugging/future ML; NOT shown in UI
  status          match_status not null default 'new',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique (requirement_id, offering_id)          -- makes matching idempotent
);

create table notifications (
  id               uuid primary key default gen_random_uuid(),
  match_id         uuid not null references matches(id) on delete cascade,
  recipient_role   text not null check (recipient_role in ('client','supplier')),
  recipient_email  text not null,
  message          text not null,
  is_read          boolean not null default false,
  created_at       timestamptz not null default now()
);

create table email_outbox (
  id          uuid primary key default gen_random_uuid(),
  to_email    text not null,
  subject     text not null,
  body        text not null,
  created_at  timestamptz not null default now(),
  sent_at     timestamptz
);

create table geocode_cache (
  query       text primary key,
  latitude    double precision,
  longitude   double precision,
  created_at  timestamptz not null default now()
);
```

`0002_indexes_rls.sql`:
- HNSW indexes: `create index on requirements using hnsw (embedding vector_cosine_ops);` and the same for `offerings`.
- B-tree: `matches (requirement_id, score desc)`, `matches (offering_id, score desc)`, `notifications (recipient_email, is_read)`, `requirements (contact_email)`, `offerings (contact_email)`.
- Enable Row Level Security on **every** table. The backend connects with the database owner connection string, which bypasses RLS.
  Add exactly one policy: `anon` may `select` from `notifications` (needed for Realtime; demo-grade, document the caveat in `docs/DECISIONS.md`).

Supabase connection notes: use the direct connection (or session pooler) for the backend and migrations.
Do not use the transaction pooler with prepared statements.

---

## 5. Constants (`backend/app/constants.py`)

```python
CATEGORIES = [
  "Raw Materials & Metals", "Electronics & Electrical", "Packaging",
  "Textiles & Apparel", "Food & Agriculture", "Construction Materials",
  "Chemicals", "Machinery & Equipment", "Office & Consumables", "Other",
]
DELIVERY_SCOPES = {  # max delivery radius in km used when coordinates are known
  "local": 100, "regional": 500, "national": 5000, "international": None,  # None = unlimited
}
UNIT_FAMILIES = {   # unit -> (family, factor to base unit)
  "kg": ("mass", 1), "tonne": ("mass", 1000),
  "piece": ("count", 1), "box": ("count", 1), "unit": ("count", 1),
  "metre": ("length", 1), "litre": ("volume", 1),
}
```
The frontend must load categories, units and scopes from `GET /api/meta` (no duplicated lists).
If two units belong to different families the pair is not comparable and is excluded.
`box` and `piece` are both "count" but must only match when the unit strings are equal
(do not convert between them).

---

## 6. Matching engine (the core — implement exactly)

All tunables live in `config.py` and can be overridden by env vars.

### 6.1 Embedding
- Text per record: `"{product} | category: {category} | {notes or ''}"`.
- Model loaded **once** at startup (lazy singleton). Vectors are L2-normalised, so cosine similarity = dot product.
- Embed each record exactly once, at creation (and again only if its text fields change).
- Symmetric matching: same model and no query/passage prefixes on both sides.
- Model name and dimension are config values; changing the model requires a new migration for the vector size.

### 6.2 Pipeline (per new requirement; the supplier-side flow is the mirror image)

1. **Hard filters (SQL `WHERE`)** on `offerings`, status `active`:
   - `category = requirement.category` (config `STRICT_CATEGORY=true`; set false to allow cross-category via similarity).
   - Units comparable (section 5); available quantity (converted to the requirement's unit) `>= MIN_QTY_FRACTION * required` (default 0.25).
   - `lead_time_days <= MAX_LEAD_FACTOR * needed_within_days` (default 2.0).
   - `unit_price * quantity <= MAX_BUDGET_FACTOR * budget` (default 1.5).
   - If both sides have coordinates: distance `<=` the supplier's `delivery_scope` radius (skip when scope is `international`).
2. **Semantic retrieval**: among survivors, top `RETRIEVE_K` (default 30) by cosine distance using pgvector (`embedding <=> :vec`).
3. **Scoring** (`scoring.py`, pure functions, each sub-score in 0..1):
   - `semantic = clamp((cos - 0.55) / 0.35, 0, 1)` (calibration constants in config).
   - `price`: `total = unit_price * quantity`, `ratio = total / budget`.
     If `ratio <= 1`: `0.85 + 0.15 * (1 - ratio)`, else `max(0, 1 - (ratio - 1) / 0.5)`.
   - `quantity = min(1, available / required)`.
   - `delivery`: `lead <= needed` → `0.8 + 0.2 * (1 - lead / needed)`; otherwise `max(0, 1 - (lead - needed) / needed)`.
   - `location`: with coordinates, `1` within 50 km, linearly to `0` at 2000 km. Without coordinates: `1.0` same city string (case-insensitive), else `0.5`.
   - Final: `100 * (0.40*semantic + 0.20*price + 0.15*quantity + 0.15*delivery + 0.10*location)`, rounded to 2 decimals.
     Weights are config values and must sum to 1 (validate at startup).
4. **Store**: upsert rows into `matches` for the top `MAX_MATCHES_PER_ITEM` (default 10) with `score >= MATCH_MIN_SCORE` (default 60).
   Save every sub-score in `score_breakdown`. Re-running must not create duplicates or reset a match's status.
5. **Notify** once per new match with `score >= NOTIFY_MIN_SCORE` (default 70): create a notification for each side,
   queue an email for each side, then set status `new → notified`. Never notify twice for the same match.

### 6.3 Triggers
- New/updated requirement → match against all active offerings.
- New/updated offering → match against all open requirements.
- Run in a background task after the API response returns; the form response must not wait for matching.
- `POST /api/dev/rematch` recomputes everything (dev only).

### 6.4 Extension hook (document, do not build)
Accept/reject actions are the training signal. `docs/AI_MATCHING.md` must describe the future step:
replace fixed weights with a learned ranker (LightGBM/LambdaMART) and fine-tune the embedding model
on accepted pairs. Keep `score_breakdown` complete so this is possible later.

### 6.5 Scalability notes to include in docs
- Cost grows linearly with records (each embedded once), not with the number of pairs.
- Hard filters + HNSW keep each match run sublinear in table size.
- Matching is a plain function behind a background task; moving it to a worker queue needs no logic changes.

---

## 7. API (all under `/api`, JSON, Pydantic-validated)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness + DB check |
| GET | `/api/meta` | categories, units, delivery scopes, score thresholds |
| POST | `/api/requirements` | create requirement; schedules matching |
| GET | `/api/requirements` | list; filters `email`, `category`, `status` |
| GET | `/api/requirements/{id}` | detail incl. its matches |
| POST | `/api/offerings` | create offering; schedules matching |
| GET | `/api/offerings` | list; filters `email`, `category`, `status` |
| GET | `/api/offerings/{id}` | detail incl. its matches |
| GET | `/api/matches` | filters `requirement_id`, `offering_id`, `status`, `min_score`; sorted by score desc |
| PATCH | `/api/matches/{id}/status` | body `{status: accepted|rejected}`; only from `new|notified` |
| GET | `/api/notifications` | filters `email`, `unread` |
| POST | `/api/notifications/{id}/read` | mark read |
| GET | `/api/dashboard/summary` | counts, average score, matches by status |
| POST | `/api/dev/seed` | load sample data (disabled when `ENV=production`) |
| POST | `/api/dev/rematch` | recompute all matches (dev only) |
| GET | `/api/dev/outbox` | list captured emails (dev only) |

Rules:
- Validate: positive numbers, valid email, category/unit/scope in the allowed lists, sane string lengths (trim whitespace).
- Errors use one shape: `{"error": {"code": "...", "message": "...", "fields": {...}}}`.
- Responses use HTTP 201 on create, 422 on validation errors, 404 on missing ids, 409 on invalid status transitions.
- Contact emails are **hidden** in match listings until the match is `accepted` (privacy).

---

## 8. Notifications

- **In-app**: rows in `notifications`. Frontend subscribes to inserts through Supabase Realtime (anon key, read-only policy)
  and **falls back to polling every 15 seconds** if the subscription fails or env keys are absent.
  A bell icon in the header shows the unread count for the current "acting as" email.
- **Email**: `email.py` exposes `send(to, subject, body)` with two backends chosen by `EMAIL_BACKEND`:
  - `outbox` (default): writes to `email_outbox` only; viewable at `/dev/outbox` in the UI.
  - `smtp`: real sending through `SMTP_*` env vars.
- Templates (plain text):
  - Client: `A supplier match was found for "{product}": {supplier} (score {score}/100).`
  - Supplier: `A client requirement matches your offer "{product}": {client} (score {score}/100).`

---

## 9. Frontend

No login. Identity is the email the user types ("Acting as: name@company.com", stored in `localStorage`),
clearly labelled **"demo mode – no password"** in the footer.

### Pages
1. **Home `/`** — short product explanation and two large entry points: "I need a product" (client) / "I supply products" (supplier), plus a link to the dashboard.
2. **Client portal `/client`** — requirement form (all fields) and "My requirements" list with each item's top matches.
3. **Supplier portal `/supplier`** — offering form (all fields) and "My offerings" list with each item's matches.
4. **Dashboard `/dashboard`** — summary cards (total requirements, offerings, matches, average score, accepted count),
   then tabs: **Requirements**, **Offerings**, **Matches**, **Notifications**. Tables are sortable and filterable
   (category, status, min score). The Matches tab shows requirement, supplier, **score**, status, created date,
   and Accept/Reject actions for matches in `new|notified`.
5. **`/dev/outbox`** — captured emails (only when the backend reports dev mode).

### Form fields
- Client: Company/Client Name, Contact Email, Product Requirement, Category (select), Quantity + Unit, Budget (total),
  Location, Delivery Timeline (days), Additional Notes.
- Supplier: Supplier Name, Contact Email, Product Offered, Category (select), Available Quantity + Unit,
  Unit Price, Pricing Notes, Location, Lead Time (days), Delivery Scope (select), Additional Notes.
- Use react-hook-form + zod; inline field errors; disable the submit button while pending; on success show a
  confirmation stating that matching is running and where results will appear.

### UX requirements
- Score is shown as a number plus a horizontal bar; colour bands: ≥85 strong, 70–84 good, 60–69 fair (do not rely on colour alone — show the number).
- Status shown as a labelled badge.
- Every list/table has loading skeletons, empty states with a helpful next action, and error states with retry.
- Fully responsive (tables scroll horizontally or collapse into cards on mobile). Keyboard accessible, visible focus,
  labels on all inputs, contrast ≥ WCAG AA.
- Visual design: clean, restrained, generous whitespace, one accent colour, consistent spacing scale.
  Avoid generic template look; pick a distinctive type pairing and keep it consistent.
- Newly arrived notifications trigger a non-blocking toast.

Frontend talks to the backend only through a small API client module in `src/api/` (plain JS; describe request/response shapes with JSDoc comments).
The only direct Supabase usage is the Realtime subscription for notifications.

### Frontend conventions
- Vite + React with plain JavaScript only: functional components and hooks, `.jsx` for anything containing JSX.
- Tailwind CSS utility classes for all styling (configured via `tailwind.config.js` and `postcss.config.js`); no CSS-in-JS. Design tokens (colours, fonts, spacing) go in the Tailwind theme.
- Environment variables are read through `import.meta.env.VITE_*` in one place (`src/lib/env.js`).
- ESLint (react + react-hooks plugins) and Prettier configured; `npm run lint` and `npm run build` must pass.
- Shared validation rules live in zod schemas under `src/lib/schemas.js`, built from the values returned by `/api/meta`.

---

## 10. Configuration (`.env.example` must list all of these)

```
ENV=development                       # development | production
DATABASE_URL=postgresql+psycopg://USER:PASS@HOST:5432/postgres
CORS_ORIGINS=http://localhost:5173
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIM=384
STRICT_CATEGORY=true
MIN_QTY_FRACTION=0.25
MAX_LEAD_FACTOR=2.0
MAX_BUDGET_FACTOR=1.5
RETRIEVE_K=30
MAX_MATCHES_PER_ITEM=10
MATCH_MIN_SCORE=60
NOTIFY_MIN_SCORE=70
WEIGHT_SEMANTIC=0.40
WEIGHT_PRICE=0.20
WEIGHT_QUANTITY=0.15
WEIGHT_DELIVERY=0.15
WEIGHT_LOCATION=0.10
EMAIL_BACKEND=outbox                  # outbox | smtp
SMTP_HOST= SMTP_PORT= SMTP_USER= SMTP_PASSWORD= SMTP_FROM=
GEOCODER=nominatim                    # nominatim | none
# Frontend (Vite)
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```
Never commit real secrets. Fail fast at startup with a clear message when required settings are missing or weights do not sum to 1.

---

## 11. Sample data (`backend/app/seed/seed_data.py`)

Deterministic, idempotent seed of about 30 requirements and 40 offerings across at least 5 categories.
It must deliberately include cases that show the matching working:
- **Synonyms with no shared words**: e.g. "MS pipes 2 inch" vs "mild steel tubes, 50 mm".
- **Near misses**: right product but insufficient quantity; right product but far over budget; right product but too slow.
- **Distractors**: same category, different product (e.g. steel sheets vs steel pipes).
- Several suppliers competing for one requirement, and one supplier fitting several requirements.
Seeding twice must not create duplicates. Seeding triggers matching so the dashboard is populated immediately.

---

## 12. Testing

Backend (`pytest`):
- `scoring.py`: table-driven tests for every sub-score, boundaries included (ratio = 1, lead = needed, quantity = required).
- `units.py`: conversion and incompatibility.
- Matching flow against a test database: hard filters exclude what they should, results are sorted, re-running is idempotent,
  status is never reset, notifications are created exactly once.
- **Semantic sanity test** (marked `slow`): "mild steel tube" ranks above "cotton fabric" and above "steel sheet" for a "MS pipe" query.
- API tests for validation errors, status codes and the error shape.
Frontend: a light smoke test that each form validates and submits (mock API).
CI (GitHub Actions): ruff, pytest (fast tests), eslint, frontend build. CI must be green before the work is called done.

---

## 13. Local setup (no Docker)

Do not create Dockerfiles or compose files. Keep the code container-friendly anyway (all configuration through
environment variables, no hard-coded paths) so Docker can be added later without code changes.

The backend reads `backend/.env`; the frontend reads `frontend/.env` (only the `VITE_*` variables).

Backend (Python 3.11+):
```
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m app.scripts.download_model                   # one-time download of the embedding model
uvicorn app.main:app --reload --port 8000
```

Frontend (Node 18+):
```
cd frontend
npm install
npm run dev                                            # http://localhost:5173
```

`/health` must report `model_loaded: true/false` so a slow first start is easy to diagnose.
The README must let a non-expert run the project: create the Supabase project → run the migration files in order
(Supabase SQL editor or `psql`) → create `backend/.env` and `frontend/.env` from `.env.example`
→ start the backend → start the frontend → open the app → click "Load sample data".

---

## 14. Documentation deliverables

- `README.md` — what it is, screenshots placeholder, setup steps, and a plain-language **"How the matching works"** section
  (3 stages: filter, understand meaning, score; with the "MS pipe" = "mild steel tube" example).
- `docs/ARCHITECTURE.md` — components, data flow, Mermaid diagram, scalability notes (section 6.5).
- `docs/AI_MATCHING.md` — pipeline, formulas, why hybrid (embeddings fail on numbers/units, so structured scoring handles those),
  limitations (units, geocoding, English-only default model; swap to a multilingual model with the same 384 dims if needed),
  and the future learning step (section 6.4).
- `docs/OWNERSHIP_TRANSFER.md` — how to (a) transfer the Supabase project to another organisation or account,
  (b) alternatively `pg_dump`/restore into another Postgres with pgvector, (c) rebuild from `supabase/migrations`,
  (d) which secrets/keys must be rotated after a transfer.
- `docs/DECISIONS.md` — running log of choices made where this spec was silent.

---

## 15. Build order and acceptance criteria

Work in this order. Do not start a phase until the previous phase's checks pass. Commit after each phase.

| Phase | Deliver | Done when |
|---|---|---|
| 0 | Scaffold, config, migrations, `/health`, CI skeleton | Migrations apply cleanly on an empty Supabase DB; `/health` reports DB OK |
| 1 | Requirement/offering CRUD, validation, both forms, `/api/meta` | Both forms submit, validate, and persist; error shape is consistent |
| 2 | Embedding service, scoring, matching pipeline, tests | Fast tests pass; semantic sanity test passes; re-running matching is idempotent |
| 3 | Notifications (table, outbox, realtime + polling), bell + toast | A new matching pair produces exactly one notification per side and one email each |
| 4 | Dashboard, match actions, filters, status flow | All tabs work with filters; accept/reject updates status; invalid transitions return 409 |
| 5 | Seed data, empty/loading/error states, responsive + accessibility pass | Fresh install + "Load sample data" gives a populated, demo-ready app |
| 6 | Local run instructions, docs, CI green | A new machine can follow the README (no Docker) to a running app with no undocumented steps |

### Definition of done (final checklist)
- [ ] Every field from the brief exists in the correct form, in the database, and in the dashboard.
- [ ] Matching uses embeddings + structured scoring (no keyword-only path), stores results, and is idempotent.
- [ ] Both sides are notified once per relevant match (in-app + email outbox).
- [ ] Dashboard shows requirements, offerings, matches, score and status, with filters.
- [ ] Non-goals were not built. No paid AI dependency exists.
- [ ] Zero secrets in the repo; `.env.example` complete.
- [ ] Lint and tests pass in CI.
- [ ] Frontend is plain JavaScript with Tailwind; no TypeScript files and no Docker files exist.
- [ ] All five docs exist and match the implementation.
- [ ] `docs/DECISIONS.md` lists every deviation or assumption.
