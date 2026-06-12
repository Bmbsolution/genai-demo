# Gatherly backend — container image for Cloud Run.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the package (and its deps) first so the layer caches across code changes.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Run as a non-root user (defence in depth); own /app so a local SQLite run works.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run injects PORT (defaults to 8080); bind to it.
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn gatherly.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
