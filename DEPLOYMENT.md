# Deployment Steps

I cannot create accounts, push to your GitHub, or deploy to any hosting
platform from this sandboxed environment — it has no credentials for
GitHub, Vercel, Render, or Railway, and no network access to those
platforms' dashboards/APIs. Everything below is fully built, tested, and
ready; these are the exact steps for *you* to go live.

## 1. Push to GitHub
```bash
# from the tesseractis/ folder (already a git repo with one commit)
git remote add origin https://github.com/<your-username>/tesseractis.git
git branch -M main
git push -u origin main
```

## 2. Deploy the backend — Render (recommended, simplest)
1. On Render: **New → Web Service** → connect your `tesseractis` repo.
2. Root directory: `backend`. Render will detect `backend/Dockerfile` automatically.
3. **New → PostgreSQL** (free/starter tier) → copy its internal connection string.
4. **New → Redis** (Render Key Value / Redis) → copy its internal connection string.
5. On the web service, set environment variables:
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | the Postgres connection string from step 3, with `postgresql+psycopg2://` prefix |
   | `REDIS_URL` | the Redis connection string from step 4 |
   | `SESSION_SECRET` | a random value, e.g. output of `openssl rand -hex 32` |
   | `SESSION_COOKIE_SECURE` | `true` |
   | `ENVIRONMENT` | `production` |
   | `AI_PROVIDER` | `mock` |
   | `CORS_ALLOWED_ORIGINS_RAW` | your Vercel URL from step 3 below, e.g. `https://tesseractis.vercel.app` |
6. Build command: (none needed — Dockerfile handles it). Start command: (none needed — Dockerfile's `CMD` runs `alembic upgrade head` then starts uvicorn).
7. Deploy. Copy the resulting URL, e.g. `https://tesseractis-api.onrender.com`.

## 3. Deploy the frontend — Vercel
1. On Vercel: **Add New → Project** → import the same `tesseractis` repo.
2. Root directory: `frontend`.
3. Environment variable: `NEXT_PUBLIC_API_BASE_URL` = the Render backend URL from step 2.7.
4. Deploy. Copy the resulting URL, e.g. `https://tesseractis.vercel.app`.
5. **Go back to Render** and set `CORS_ALLOWED_ORIGINS_RAW` to this exact Vercel URL (step 2.5 above), then redeploy the backend so CORS actually allows it.

## 4. Verify
- `https://<render-url>/health` → `{"status":"ok"}`
- `https://<render-url>/ready` → `{"status":"ready", "checks": {"database": true, "redis": true}}`
- Open the Vercel URL → register → upload a photo → see a result.

## Notes
- Cookies: `SESSION_COOKIE_SECURE=true` + both apps served over HTTPS (Render/Vercel do this by default) is required for the session cookie to work — if login appears to "not stick," this is the first thing to check.
- The mock AI provider needs no API key. If you later add a real vision API, set `AI_PROVIDER=real` and `AI_API_KEY=...` only after implementing `RealVisionProvider` in `backend/app/ai/` (currently raises a clear error rather than silently faking a result).
