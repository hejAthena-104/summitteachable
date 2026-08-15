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
- **Admin:** https://dashboard.summitteachable.com/admin/  (`admin` / change the seeded password).

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
