# ✳ Wisdom

**The right supplier. The right buyer. Found for you.**

Wisdom is an AI matchmaking platform for Indian B2B trade. **Clients** post what they need,
**suppliers** post what they sell, and Wisdom finds, ranks and introduces the pairs that can
really do business: on meaning, price, quantity, delivery time and distance. Both sides are
notified in-app and by email, and a dashboard shows every listing, match, score and status.

## Why it exists

Small and mid-sized businesses still source through phone calls, WhatsApp groups and
directories. Keyword search fails them because trade speaks in synonyms: a buyer asks for
**"MS pipe"**, the best supplier lists **"mild steel tube"**, and they never meet. Even when
they do, most leads die on price, stock, lead time or distance, found out only after days of
calls.

| | Who | What they get |
|---|---|---|
| **Client** | Fabricators, contractors, retailers, restaurants, schools | Ranked, qualified suppliers without cold-calling; budget stays private |
| **Supplier** | Manufacturers, traders, stockists, distributors | Buyers that already fit their stock, price and delivery reach; price stays private |

**How it is used**

1. Sign up with email and password as a client or a supplier.
2. Post a listing in under a minute: product, quantity and unit, budget or unit price, city,
   timeline and an optional photo. Category is suggested, the last city and unit are
   remembered, and live helpers show ₹ per unit and the delivery date.
3. Matching runs in the background; results appear within seconds.
4. A match scoring 70+ notifies both sides in-app and by email.
5. Accept or reject. Contact details are shared only when both sides accept, and every decision
   teaches the ranker.

**Why Wisdom:** it understands meaning (and photos), drops pairs that cannot trade before anyone
picks up the phone, learns from decisions, keeps prices private, and runs its AI locally at zero
per-match cost. Built for India: ₹ with Indian digit grouping, Indian cities, kg/quintal/tonne.

## Architecture

```
React SPA ──HTTP/JSON──▶ FastAPI ──SQLAlchemy──▶ Supabase Postgres + pgvector
   │                        │
   │                        ├─ background task: embed → filter → retrieve → score → store → notify
   │                        ├─ local AI models (text + image embeddings)
   │                        └─ Gmail SMTP (every email also kept in an outbox)
   └──── Supabase Auth (email + password, role in user metadata) and Storage (photos)
```

- **Routers → services → models.** Routers stay thin; `services/scoring.py` is pure functions.
- Posting a form never waits for the AI: matching runs after the response is sent.
- Each listing is embedded and geocoded once; re-running matching is idempotent and never
  overwrites a match's accepted/rejected status.

## Technology stack

| Area | Technology |
|---|---|
| Frontend | React 18, Vite, plain JavaScript, Tailwind CSS, TanStack Query, react-hook-form + zod, React Router |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2, Pydantic settings, Alembic |
| Database | PostgreSQL on Supabase with pgvector |
| AI (local, free) | `BAAI/bge-small-en-v1.5` for text, CLIP ViT-B/32 for photos (fastembed) |
| Auth & files | Supabase Auth, Supabase Storage |
| Geo | OpenStreetMap Nominatim with a database cache; haversine distance in SQL |
| Quality | ruff, pytest, ESLint, Prettier, Vitest, GitHub Actions CI |

## AI matching approach

A hybrid engine: **models for meaning, rules for numbers.** Embeddings are good at "is this the
same product?" and bad at arithmetic, so each does what it is good at.

1. **Hard filters (SQL).** Only pairs that could really trade survive: comparable units (kg and
   tonnes convert; boxes and pieces never mix), at least 10% of the quantity, price at most 2×
   the budget, lead time at most 3× the deadline, and the buyer inside the supplier's delivery
   range (local 100 km, regional 500 km, national 5000 km).
2. **Meaning (pgvector).** Each description becomes a 384-dimension embedding; the 50 nearest
   survivors by cosine similarity are scored. With photos, CLIP compares photo↔photo or
   photo↔text; when the text is unsure, the photo decides.
3. **Score (0–100).**

   | Signal | Weight | Measure |
   |---|---|---|
   | Meaning | 40% | calibrated cosine similarity (text and photos) |
   | Price | 20% | full marks within budget, falls to 0 at 2× budget |
   | Quantity | 15% | share of the required quantity in stock |
   | Delivery | 15% | full marks on time, falls to 0 at 3× the deadline |
   | Distance | 10% | full within 50 km, 0 at 2000 km |

   **85+** strong, **70–84** good, **55–69** fair. Matches of 55+ are stored, 70+ notify both
   sides once. Unrelated products are never stored, however cheap or close.
4. **Learning.** Every accept/reject refits a logistic-regression ranker on the stored
   sub-scores; its weights blend in with the defaults above as decisions accumulate.

Every threshold and weight is an environment variable (see `.env.example`).

## Setup

You need **Python 3.11+**, **Node 18+** and a free **Supabase** project.

**1. Supabase**

- Create a project; click **Connect** and copy the **Session pooler** connection string.
- **Authentication → Sign In / Providers → Email:** switch **Confirm email** off, so users log in
  straight away with email and password.
- Optional, for email: create a Gmail **App Password** (<https://myaccount.google.com/apppasswords>)
  and enter it under **Authentication → Emails → SMTP Settings** (`smtp.gmail.com`, port 465).

**2. Configure.** Copy `.env.example` to `backend/.env` and set `DATABASE_URL`, `SUPABASE_URL`
and `SUPABASE_ANON_KEY` (Project Settings → API, the publishable key); for email also set
`EMAIL_BACKEND=smtp` and the `SMTP_*` values. Copy the `VITE_*` lines to `frontend/.env` with the
same URL and key.

**3. Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head                 # creates the schema and the photo bucket
python -m app.scripts.download_model # one-time download of the models (~0.7 GB)
uvicorn app.main:app --reload --port 8000
```

<http://localhost:8000/health> should report `"db": "ok"`.

**4. Frontend**

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

**5. Try it.** Open <http://localhost:5173/dashboard> and click **Load sample data** (30
requirements, 49 offerings across India). Then register as a client and post
*"MS pipes, 2 inch diameter", 2000 kg, budget ₹1,50,000, Pune, 21 days*: mild-steel tube
suppliers appear, ranked, within seconds. Search listings from the navigation bar.

## Tests

```bash
cd backend && ruff check . && ruff format --check . && pytest
cd frontend && npm run lint && npm test && npm run build
```

Database tests run when `TEST_DATABASE_URL` points at an empty, throwaway Postgres database
with pgvector whose name contains `test`. CI runs everything on every push.

## Project layout

```
backend/     FastAPI app: api/ (routers) -> services/ (matching, scoring, ml, ...) -> models
frontend/    React + Vite + Tailwind (plain JavaScript)
supabase/    SQL migrations: the database can be rebuilt from these alone
```
