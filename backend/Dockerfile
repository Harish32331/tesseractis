# The Tesseractis — backend container
FROM python:3.12-slim

WORKDIR /app

# System deps needed by psycopg2 and Pillow at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Runs as a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Applies migrations, then starts the API. Migrations run on every boot,
# which is safe/idempotent with Alembic and keeps deploys simple.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
