#!/bin/sh
# Container entrypoint for the summitteachable backend.
# Takes ownership of the media volume as root, drops to the unprivileged `app`
# user, applies migrations against the configured DATABASE_URL (Railway Postgres
# in production), then execs gunicorn as PID 1.
set -e

MEDIA_DIR="${MEDIA_DIR:-/app/media}"

# MEDIA_ROOT is a host bind mount (/opt/summitteachable/media on the VPS), so its
# ownership comes from the host and REPLACES the Dockerfile's build-time chown.
# When it did not match the runtime uid, every upload died with
#   PermissionError: [Errno 13] Permission denied: '/app/media/kyc/documents/…'
# and users got a bare 500 on KYC, deposit proofs and admin QR uploads. Fix the
# ownership as root on every start — it re-heals after a volume restore — then
# drop straight back down to `app` for the rest of this script.
if [ "$(id -u)" = "0" ]; then
    echo "[entrypoint] preparing media volume at ${MEDIA_DIR}…"
    mkdir -p \
      "${MEDIA_DIR}/kyc/documents" \
      "${MEDIA_DIR}/kyc/selfies" \
      "${MEDIA_DIR}/deposits" \
      "${MEDIA_DIR}/course_purchases" \
      "${MEDIA_DIR}/payment_qr_codes" \
      "${MEDIA_DIR}/payment_methods" \
      "${MEDIA_DIR}/avatars" \
      "${MEDIA_DIR}/analysis"
    chown -R app:app "${MEDIA_DIR}"
    echo "[entrypoint] dropping privileges to app…"
    exec setpriv --reuid=app --regid=app --init-groups "$0" "$@"
fi

# Everything below runs as the unprivileged `app` user.
echo "[entrypoint] running as $(id -un) (uid $(id -u))"

# Fail fast and loudly if the media volume still is not writable — a silent
# read-only mount would otherwise only show up as 500s once a user uploads.
if ! touch "${MEDIA_DIR}/.writable" 2>/dev/null; then
    echo "[entrypoint] WARNING: ${MEDIA_DIR} is NOT writable by $(id -un) — uploads will fail." >&2
else
    rm -f "${MEDIA_DIR}/.writable"
fi

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
