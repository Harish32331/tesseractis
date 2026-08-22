from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

register_error_handlers(app)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.get("/health", tags=["system"])
def health() -> dict:
    """Liveness probe — minimal, non-sensitive response only."""
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
def ready() -> dict:
    """Readiness probe — actually checks DB and Redis, not just a static reply."""
    from sqlalchemy import text

    from app.core.db import engine
    from app.security.rate_limit import get_redis

    checks = {"database": False, "redis": False}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    try:
        get_redis().ping()
        checks["redis"] = True
    except Exception:
        pass

    all_ok = all(checks.values())
    return {"status": "ready" if all_ok else "degraded", "environment": settings.ENVIRONMENT, "checks": checks}


from app.api.v1 import admin, auth, scans  # noqa: E402

app.include_router(auth.router)
app.include_router(scans.router)
app.include_router(admin.router)
