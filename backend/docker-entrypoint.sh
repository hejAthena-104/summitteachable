#!/bin/sh
# Container entrypoint for the summitteachable backend.
# Applies migrations against the configured DATABASE_URL (Railway Postgres
# in production), then execs gunicorn as PID 1.
set -e

echo "[entrypoint] applying database migrations…"
python manage.py migrate --no-input

echo "[entrypoint] seeding baseline + content data…"
python manage.py seed_basics || true
python manage.py seed_courses || true
python manage.py seed_analysis || true
python manage.py seed_traders || true

echo "[entrypoint] starting gunicorn on 0.0.0.0:${PORT:-8000}"
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
