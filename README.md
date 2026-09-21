# Supplier Matchmaker

A web platform where **clients** post product requirements and **suppliers** post offerings.
An AI matching engine finds and ranks the pairs that fit, stores them, notifies both sides
(in-app and by email), and a dashboard shows requirements, offerings, matches, scores and status.

The AI runs **locally and for free**: a small open embedding model (`BAAI/bge-small-en-v1.5`)
on your own machine, no paid API.

> Screenshots: _add after first deployment_ (home, client portal, dashboard).

## How the matching works

Every time someone submits a form, the engine runs three stages in the background:

1. **Filter.** Only pairs that could really trade survive: same category, compatible units
   (kg and tonnes convert; boxes and pieces never mix), at least 25% of the quantity, a price
   no more than 50% over budget, a lead time no more than twice the deadline, and a buyer
   inside the supplier's delivery range (local 100 km, regional 500 km, national 5000 km).
2. **Understand meaning.** A language model turns each description into a list of numbers
   (an "embedding"). Similar meanings give similar numbers, so a buyer asking for
   **"MS pipe"** is shown a supplier of **"mild steel tube"**, ranked above "steel sheet",
   even though the two descriptions share no words.
3. **Score.** Meaning (40%), price against budget (20%), quantity (15%), delivery time (15%) and
   distance (10%) combine into a score from 0 to 100. Matches of **60+** are stored; **70+**
   notifies both sides once. **85+** is shown as *strong*, 70–84 as *good*, 60–69 as *fair*.

Numbers and units are deliberately handled by rules rather than the model: embeddings are
good at meaning and bad at arithmetic. Details: [docs/AI_MATCHING.md](docs/AI_MATCHING.md).

## Run it locally (no Docker)

You need **Python 3.11+**, **Node 18+** and a free **Supabase** account
(or any PostgreSQL with the `pgvector` extension).

### 1. Create the database

1. Create a project at [supabase.com](https://supabase.com) and note the database password.
2. Open **SQL Editor** and run, in order, the contents of
   `supabase/migrations/0001_init.sql` and then `supabase/migrations/0002_indexes_rls.sql`.
   (With `psql`: `psql "<connection string>" -f supabase/migrations/0001_init.sql`, then `0002`.)
3. Copy the connection string from **Project Settings → Database → Connection string**.
   Use **Direct connection** or **Session pooler** (not the transaction pooler).

### 2. Configure

Copy `.env.example` twice:

- to `backend/.env`: set `DATABASE_URL` to the connection string (with your password).
  Everything else has working defaults.
- to `frontend/.env`: only the `VITE_*` lines are read. For live notifications, set
  `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` (Project Settings → API). Without them the
  app polls every 15 seconds instead.

### 3. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m app.scripts.download_model # one-time, ~70 MB
uvicorn app.main:app --reload --port 8000
```

Check <http://localhost:8000/health>: it should report `"db": "ok"`. `model_loaded` becomes
`true` a few seconds after start.

> Instead of the SQL editor you can create the schema from here with `alembic upgrade head`.
> If you already ran the SQL files by hand, run `alembic stamp head` once instead.

### 4. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

### 5. Try it

Open <http://localhost:5173/dashboard> and click **Load sample data** (30 requirements,
46 offerings). Matching runs in the background, and the dashboard fills within a few seconds.

To see one side's view, type a sample email into **Acting as** at the top, for example
`buyer@northwind.example.com` (the "MS pipes" buyer), then open **Client**. There is no login:
the app is in demo mode and anyone can act as any email.
Emails the platform would send appear under **Dev: email outbox** in the footer.

## Tests and checks

```bash
cd backend
ruff check . && ruff format --check .
pytest                       # database tests are skipped without TEST_DATABASE_URL
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/matchmaking_test pytest
pytest -m slow               # semantic sanity check with the real model

cd frontend
npm run lint && npm test && npm run build
```

`TEST_DATABASE_URL` must point at an **empty, throwaway** Postgres database with pgvector whose
name contains `test`: the tests drop and recreate its schema. CI does all of this on every push.

## Project layout

```
backend/     FastAPI app: api/ (thin routers) -> services/ (matching, scoring, ...) -> models
frontend/    React + Vite + Tailwind (plain JavaScript)
supabase/    SQL migrations: the database can be rebuilt from these alone
docs/        ARCHITECTURE, AI_MATCHING, OWNERSHIP_TRANSFER, DECISIONS
```

All settings are environment variables (see `.env.example`); nothing is hard-coded to a
machine, so containerising later needs no code changes.
