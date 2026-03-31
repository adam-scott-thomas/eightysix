# Stage 1: Build — install compiled deps with gcc
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /tmp/
RUN pip install --no-cache-dir --prefix=/install \
    fastapi uvicorn[standard] "sqlalchemy[asyncio]" asyncpg \
    alembic pydantic pydantic-settings python-dotenv \
    "passlib[bcrypt]" "python-jose[cryptography]" email-validator \
    slowapi

# Stage 2: Runtime — slim image, no gcc
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /install /usr/local

WORKDIR /app
COPY . .

RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
