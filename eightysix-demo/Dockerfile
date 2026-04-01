# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] python-multipart openpyxl chardet boto3

WORKDIR /app
COPY . .
COPY --from=frontend-builder /frontend/dist /app/frontend/dist

RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH=/app

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
