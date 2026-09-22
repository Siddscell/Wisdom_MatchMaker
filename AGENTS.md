# AGENTS

`PROJECT_SPEC.md` is the source of truth for this project. Read it fully before changing code.

- Backend: Python 3.11+, FastAPI; routers → services → models; `services/scoring.py` stays pure.
- Frontend: plain JavaScript (`.jsx`/`.js`), Tailwind, no TypeScript. No Docker files.
- Where the spec is silent, choose the simplest option and add one line to `docs/DECISIONS.md`.
- Before calling work done: `ruff check . && ruff format --check . && pytest` in `backend/`
  (set `TEST_DATABASE_URL` for database tests) and `npm run lint && npm test && npm run build`
  in `frontend/`.
