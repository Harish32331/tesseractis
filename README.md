# The Tesseractis

AI-assisted identification of mixed plastic waste from a photograph, with
honest confidence reporting and recycling guidance. Built as a hackathon/
assignment submission.

## Stack
- **Backend:** FastAPI, PostgreSQL, Redis, SQLAlchemy + Alembic, Argon2id auth
- **Frontend:** Next.js, TypeScript, Tailwind
- **AI:** Provider-abstracted; ships with `MockVisionProvider` (clearly
  labeled "DEMO / MOCK AI RESULT" in the UI — no real accuracy claims are made)

## Run locally (no Docker required)

**Backend**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # edit DATABASE_URL/REDIS_URL if needed
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev
```

Requires a local PostgreSQL (`tesseractis` db) and Redis instance — see
`.env.example` for the expected connection strings.

## Run locally with Docker
```bash
cp .env.example .env   # edit SESSION_SECRET at minimum
docker compose up --build
```
Frontend on :3000, backend on :8000, Postgres on :5432, Redis on :6379.

## Tests
```bash
cd backend
export AI_PROVIDER=mock REDIS_URL=redis://localhost:6379/0
pytest app/tests/ -v
```
19/19 tests pass as of this submission, including cross-user IDOR
protection, malicious/spoofed upload rejection, and RBAC enforcement.

## Deployment (see DEPLOYMENT.md for exact steps)
Recommended: Render (backend + managed Postgres + Redis) + Vercel (frontend).
Both Dockerfiles are provided; Render/Railway can also build directly from
`backend/Dockerfile` and `frontend/Dockerfile` without Compose.

## Environment variables
See `.env.example` — every variable is documented there. Never commit
a real `.env` file (already gitignored).

## Known limitations (stated honestly)
- `AI_PROVIDER=mock` only. `RealVisionProvider` is not implemented — the
  interface exists (`app/ai/base.py`, `app/ai/factory.py`) but no external
  vision API has been chosen or wired in. The UI labels every mock result.
- No trained/fine-tuned plastic classifier exists; no accuracy numbers are
  claimed anywhere in the app.
- Recycling guidance is a configurable rule engine seeded with placeholder
  text, not verified local municipal rules.
