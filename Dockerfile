# --- Stage 1: Builder ---
FROM python:3.11-slim-bookworm AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies for build
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- ADDED: Forcibly remove the conflicting sub-dependency ---
RUN pip uninstall -y pytest-anyio


# --- Stage 2: Final ---
FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /code

# Create non-root user
RUN useradd --create-home appuser
RUN chown -R appuser:appuser /code

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/local/include /usr/local/include
COPY --from=builder /usr/local/share /usr/local/share

# Copy application code (Assuming your app code is in a folder named 'app')
COPY ./src /code/src
COPY ./app /code/app
COPY ./alembic.ini /code/alembic.ini
COPY ./alembic /code/alembic


# Switch to non-root user
USER appuser

# Expose port for the app (Railway will set PORT env var)
EXPOSE 8000

# Final run command for production - FORCE MIGRATION
CMD ["sh", "-c", "set -e && cd /code && echo '=== FORCING MIGRATIONS ===' && echo 'Current directory:' && pwd && echo 'Files in directory:' && ls -la && echo 'Alembic files:' && ls -la alembic* && echo 'Running migrations...' && alembic upgrade head && echo '=== MIGRATIONS COMPLETED ===' && echo 'Starting Gunicorn server...' && gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8000} --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100"]