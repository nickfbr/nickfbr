# Recipe Box 🍳

A recipe app with a **Paste-to-Parse import** feature: paste raw recipe text or a
URL and the app parses it into a structured draft you review and edit before
saving. Built from the "Paste-to-Parse Recipe Import" feature spec.

```
recipe/
├── backend/    FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic v2 (the API + parser)
├── frontend/   Expo / expo-router React Native app (dark theme, gold accent)
└── docs/       db_design.md, ux_design.md
```

## How parsing works
- **Paste a URL** → the server tries `recipe-scrapers` (schema.org structured data)
  first, falling back to an Anthropic LLM call on the extracted page text.
- **Paste text** → a single Anthropic LLM call returns strict JSON.
- Either way you get the same draft shape. **Parsing never writes to the database** —
  you review the pre-filled Add Recipe form and tap Save, which is a separate call.
- URL fetches are SSRF-guarded (private/metadata IPs blocked, per-hop redirect
  re-checks, timeouts, size caps, HTML-only).

## Run it
**Backend** (see `backend/README.md`):
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set JWT_SECRET and ANTHROPIC_API_KEY
alembic upgrade head
uvicorn app.main:app --reload   # http://localhost:8000
```

**Frontend** (see `frontend/README.md`):
```bash
cd frontend
npm install
cp .env.example .env            # EXPO_PUBLIC_API_URL=http://localhost:8000
npx expo start
```

## Deploy (Docker / Render)
The backend API is containerized. Locally, `docker compose up --build` brings up
Postgres + the API (migrations run automatically). For Render, use the blueprint
`render.yaml` (Docker web service + managed Postgres) — see `backend/README.md`
for details. The Expo frontend is a mobile client and is built/distributed
separately (or served as a static web build).

## Tests
```bash
cd backend && pip install -r requirements-dev.txt && pytest   # 38 passing
cd frontend && npx tsc --noEmit                                # type-check
```

## Notes
- The canonical unit enum (`backend/app/units.py`) was extended with `lb` and
  `fl_oz` per the spec's §6 recommendation, since US recipes rely on them.
- Per-user rate limit on `/parse` is 20/hour (sliding window). Set `REDIS_URL`
  to enforce it globally across all workers/instances; without it the limiter is
  per-process. See `backend/README.md` → "Rate limiting".
- Out of scope (v1): importing recipe photos from URLs, bulk import.
