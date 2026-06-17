# Recipe Box — Backend (FastAPI)

FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic v2. Implements recipe CRUD, JWT
auth, and the **Paste-to-Parse recipe import** feature (`POST /api/recipes/parse`).

## Quick start

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # or requirements-dev.txt for tests
cp .env.example .env                      # set JWT_SECRET and ANTHROPIC_API_KEY
alembic upgrade head                      # create schema (defaults to local SQLite)
uvicorn app.main:app --reload             # http://localhost:8000  (/docs for OpenAPI)
```

Production: Postgres + Gunicorn with Uvicorn workers, e.g.
`gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 --timeout 60`
(generous timeout so the LLM/URL-fetch calls in `/parse` can complete).

## Configuration (`.env`)
See `.env.example`. Notable: `DATABASE_URL`, `JWT_SECRET`, `ANTHROPIC_API_KEY`,
`ANTHROPIC_MODEL` (defaults to current Sonnet, configurable), and the parse limits
(`PARSE_RATE_LIMIT_PER_HOUR`, `MAX_TEXT_LENGTH`, fetch timeout/size/redirect caps).

## API

| Method | Path                  | Auth | Description                          |
|--------|-----------------------|------|--------------------------------------|
| POST   | `/api/auth/register`  | —    | Create account → `{accessToken}`     |
| POST   | `/api/auth/login`     | —    | Log in → `{accessToken}`             |
| GET    | `/api/recipes`        | ✓    | List the user's recipes              |
| GET    | `/api/recipes/{id}`   | ✓    | Get one recipe                       |
| POST   | `/api/recipes`        | ✓    | Create a recipe                      |
| POST   | `/api/recipes/parse`  | ✓    | Parse text/URL → draft (no DB write) |

All JSON is camelCase. Errors use one envelope app-wide:
`{ "error": { "code", "message", "fields"? } }`.

### `/api/recipes/parse`
Body has **exactly one** of `text` or `url`. Returns a `{ draft, meta }` for the
client to review and edit in the Add Recipe form before saving via
`POST /api/recipes`. **Parsing never writes to the DB.**

- **URL** → tries `recipe-scrapers` (schema.org) first (`structured_data`); if no
  parser/usable result, extracts page text and falls back to the LLM
  (`llm_fallback`).
- **Text** → one Anthropic call (`llm`), temperature 0, JSON-only.
- Output is validated through Pydantic, steps re-sequenced 1..N, numeric ranges
  clamped, units coerced to the canonical enum (unmapped ones flagged).

**Error codes:** `INVALID_INPUT` (422), `URL_NOT_ALLOWED` (400),
`UNPARSEABLE` (422), `FETCH_FAILED` (502), `PARSER_UNAVAILABLE` (502),
`RATE_LIMITED` (429).

**Security:** server-side URL fetches are SSRF-guarded — scheme allowlist, DNS
resolution + private/link-local/loopback/metadata-IP blocking, per-hop redirect
re-validation, 5s timeout, 2 MB cap, HTML-only, no cookies/auth forwarded
(`app/parsing/ssrf.py`, `fetcher.py`).

## Rate limiting (`/api/recipes/parse`)

The parse endpoint is rate-limited **per user** to bound LLM cost and abuse
(`app/rate_limit.py`). It is a **sliding window**: at most
`PARSE_RATE_LIMIT_PER_HOUR` (default **20**) requests per user in any rolling
3600-second window — not a fixed hourly bucket, so a burst can't reset at the top
of the hour.

What happens when you exceed it:
- The request is rejected with **HTTP 429** and the standard envelope
  `{"error":{"code":"RATE_LIMITED","message":"Too many import requests. Try again in about Ns."}}`,
  where `N` is computed from when the oldest request in your window expires.
- Nothing is parsed or saved.

Two backends, selected automatically by config:
- **`REDIS_URL` set → global limiter.** A single atomic Redis Lua script
  (sorted-set sliding window, keyed `parse_rl:user:<id>`) enforces the limit
  across **every worker and instance**. This is what you want in production with
  `WEB_CONCURRENCY > 1` or more than one instance — otherwise each process keeps
  its own count and the effective limit multiplies by the worker count.
- **`REDIS_URL` unset → in-memory limiter.** Process-local sliding window. Fine
  for single-process local dev and tests.

**Failure mode:** if Redis is unreachable, the limiter **fails open** (allows the
request) and logs a warning — feature availability is preferred over hard-blocking
when the limiter backend is down. The Anthropic provider's own limits remain a
backstop. Keys auto-expire (`PEXPIRE`) so there is no unbounded growth.

## Deployment (Docker / Render)

The API is containerized (`Dockerfile`): Gunicorn + Uvicorn workers, non-root,
`$PORT`-aware, 120s timeout (so the LLM/URL-fetch calls in `/parse` can finish).

**Local container stack** (Postgres + API, mirrors prod) — from `recipe/`:
```bash
docker compose up --build      # API on http://localhost:8000
```
The `migrate` service runs `alembic upgrade head` before the API starts. Set
`ANTHROPIC_API_KEY` in your shell for the parse endpoint to reach the LLM.

**Render** — deploy via the blueprint `recipe/render.yaml` (Docker web service +
free Postgres). It generates `JWT_SECRET`, wires `DATABASE_URL` from the managed
DB, and runs migrations as the `preDeployCommand`. Set `ANTHROPIC_API_KEY` as a
secret in the dashboard. If deploying from the monorepo root rather than a
dedicated `nickfbr/recipe` repo, move `render.yaml` to the repo root and prefix
its paths with `recipe/`.

Plain Docker:
```bash
docker build -t recipe-box-api ./backend
docker run -p 8000:8000 -e JWT_SECRET=... -e DATABASE_URL=... -e ANTHROPIC_API_KEY=... recipe-box-api
# run migrations once against the target DB: alembic upgrade head
```

## Layout
```
app/
  main.py            app + CORS + error handlers
  config.py          settings (pydantic-settings)
  database.py        engine/session/Base
  models.py          SQLAlchemy models
  schemas.py         Pydantic v2 (camelCase aliases)
  auth.py            JWT + password hashing
  errors.py          AppError + standardized envelope
  rate_limit.py      per-user sliding-window limiter
  units.py           canonical unit enum + synonyms
  routers/           auth, recipes
  parsing/
    service.py         orchestration (path selection, confidence, clamping)
    fetcher.py         safe URL fetch
    ssrf.py            SSRF guard
    scraper_adapter.py recipe-scrapers adapter
    ingredient_parser.py  free-text line parser
    llm_parser.py      Anthropic call + JSON extraction
    html_text.py       HTML→text for the LLM fallback
alembic/             migrations
tests/               pytest suite
```

## Tests
```bash
pip install -r requirements-dev.txt
pytest            # 38 tests: parser edge cases, SSRF, parse endpoint, parse→save
```
External effects (httpx, recipe-scrapers, Anthropic) are mocked.
