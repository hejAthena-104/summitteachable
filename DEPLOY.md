# Summit Teachable — Deploy Guide

## What runs where
- **Code:** GitHub `github.com/hejAthena-104/summitteachable` (monorepo).
  - `frontend/` → marketing pages + `netlify.toml` (the homepage proxy).
  - `backend/` → the Django dashboard + storefront.
- **Marketing + homepage** (`summitteachable.com`): **Netlify** — auto-deploys on every `git push`.
- **Dashboard / storefront** (`dashboard.summitteachable.com`): **Contabo VPS** `156.67.28.100`
  (Docker + Caddy). Needs a manual rebuild after backend changes.
- **Database:** Railway Postgres (DB only — leave it alone; do NOT deploy apps to Railway).

## The golden rule
1. Edit code locally.
2. `git add -A && git commit -m "what changed" && git push`
3. **Netlify** redeploys `frontend/` + `netlify.toml` automatically (~1 min). ← that's all you need for
   marketing / homepage-proxy / redirect changes.
4. If you changed anything under **`backend/`** (Django templates, views, models, static, fonts, images),
   also rebuild the VPS:

```bash
ssh root@156.67.28.100 \
  'cd /opt/summitteachable/repo && git pull && cd /opt/swifteagle && docker compose up -d --build summitteachable'
```

That single command pulls the latest code and rebuilds **only** the `summitteachable` container — the
other sites on the VPS (bloomvest, provena, webwave, plux, swifteagle) are untouched. On start it
**auto-runs migrations + seeds + collectstatic**, so you don't run those by hand.

## Common scenarios
| You changed… | Do this |
|---|---|
| Marketing page / `netlify.toml` only | `git push` — Netlify handles it |
| Django code/templates/static (`backend/`) | `git push` **+** the VPS rebuild command above |
| A Django **env var** (DB url, keys, hosts) | edit `/opt/summitteachable/repo/backend/.env.prod` on the VPS, then `cd /opt/swifteagle && docker compose up -d --force-recreate summitteachable` (a plain restart does NOT re-read env) |
| New **migrations** | nothing extra — they run automatically on container start |

## Handy commands (on the VPS)
```bash
ssh root@156.67.28.100
docker logs -f summitteachable-backend         # live logs
docker ps                                       # see all services + health
cd /opt/swifteagle && docker compose restart summitteachable   # quick restart (no env reload)
```

## Access you need
- **GitHub push:** the `git` remote is SSH (`git@github.com:hejAthena-104/summitteachable.git`).
- **VPS:** `ssh root@156.67.28.100` (SSH key).
- **Netlify:** the site is linked to the GitHub repo — pushes auto-deploy, nothing to run.
- **Admin:** NOT at `/admin/`. The path is the `ADMIN_URL` value in `.env.prod` on the VPS
  (`grep ADMIN_URL /opt/summitteachable/repo/backend/.env.prod`) — it is kept out of this repo on purpose.

## Rollback
- **Netlify:** dashboard → Deploys → pick a previous deploy → "Publish deploy".
- **VPS:** `cd /opt/summitteachable/repo && git checkout <good-commit> && cd /opt/swifteagle && docker compose up -d --build summitteachable`.
- Backups of the shared config exist on the VPS: `/opt/swifteagle/docker-compose.yml.bak.presummit`,
  `Caddyfile.bak.presummit`.

## First-time setup notes (already done, for reference)
- VPS service block lives in `/opt/swifteagle/docker-compose.yml` (`summitteachable`), Caddy block in
  `/opt/swifteagle/Caddyfile` (`dashboard.summitteachable.com → summitteachable:8000`).
- `.env.prod` (secrets) lives at `/opt/summitteachable/repo/backend/.env.prod` — it is **git-ignored**,
  so it stays on the VPS and is never pushed.

## Uploaded files (KYC documents, deposit proofs, avatars, payment QR codes)

They live on the host at **`/opt/summitteachable/media`**, bind-mounted to `/app/media` in the
container, so they survive a rebuild. Do not delete that directory — it is the only copy.

The container serves requests as the unprivileged `app` user (uid 999), but a bind mount keeps the
*host's* ownership, which does not have to match. When it did not, every upload died with
`PermissionError: [Errno 13] Permission denied: '/app/media/…'` and users got a 500 on KYC,
deposits and admin QR uploads. `docker-entrypoint.sh` now fixes this on every start: it begins as
root, creates the upload directories, `chown`s them to `app`, then drops privileges via `setpriv`.
So a restored or recopied media directory heals itself — just restart the container.

To check it by hand:
```bash
docker exec summitteachable-backend ls -ld /app/media          # expect owner `app`
docker exec -u app summitteachable-backend touch /app/media/.w && echo writable
docker logs summitteachable-backend | head -4                  # entrypoint prints the uid it drops to
```
The startup log warns loudly if the directory is still not writable.

## Abuse protection (added after the 2026-10-03 attack)

An automated tool made 232 admin password guesses, created ~40 accounts through the register and
checkout forms, and uploaded `.php` files as "proof of payment". Nothing was breached, but nothing
slowed it down either. What now stands in the way (`backend/config/security.py`):

- **Admin path** — set by `ADMIN_URL` in `.env.prod`; `/admin/` is a 404.
- **Throttling** — per-IP caps on POSTs to login (incl. admin), login/2FA code entry, the
  email-sending endpoints, register and checkout. Over the cap returns HTTP 429. Limits are
  `THROTTLE_RULES` in `config/security.py`; `AUTH_THROTTLE_ENABLED=False` in `.env.prod` switches it
  off in an emergency. Counters live in a file cache inside the container, so a rebuild resets them.
- **Uploads** — proof of payment, avatars and analysis charts must decode as a real JPG/PNG/WebP
  (max 8 MB) and are stored under a random name (`accounts/upload_utils.py: clean_image_upload`).
- **Turnstile** — the human check on register / login / checkout switches on only when BOTH
  `TURNSTILE_SITEKEY` and `TURNSTILE_SECRET` are in `.env.prod`. Without them the forms work as before.
- **Real visitor IPs** — gunicorn's access log and the Login History table now record the
  visitor's address (from Caddy's `X-Forwarded-For`), not Caddy's internal `172.18.x.x`.

To see who is being throttled: `docker logs summitteachable-backend 2>&1 | grep Throttled`.
