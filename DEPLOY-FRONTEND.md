# Frontend deployment — summitteachable.com

**As of 2026-07-22 the marketing site is served from the Contabo VPS, not Netlify.**

| | |
|---|---|
| Live URL | https://summitteachable.com (`www.` 301s to apex) |
| Served from | `/opt/summitteachable/repo/frontend` on `156.67.28.100` |
| Served by | the shared `swifteagle-caddy` container, mounted read-only at `/srv/summitteachable` |
| Dashboard | https://dashboard.summitteachable.com — unchanged, still the `summitteachable-backend` container |

## ⚠️ This site is a hybrid — read before editing

The homepage is **not** a static file. `/` is a **200-proxy** to the live Django
course catalog (`/buy/`), so the URL stays `summitteachable.com` while the
content comes from the container. That's why `frontend/` has no `index.html`.

Consequences:

- **`summitteachable.com` must stay in `ALLOWED_HOSTS`** in
  `/opt/summitteachable/repo/backend/.env.prod`. Django receives
  `Host: summitteachable.com` on every homepage request; drop it and the
  homepage returns a bare **400**. (`CSRF_TRUSTED_ORIGINS` already lists it.)
  After editing that file: `docker compose up -d --force-recreate summitteachable`
  — `docker restart` does *not* re-read `env_file`.
- Changing the homepage means editing the **Django catalog template**, not
  `frontend/`. The old static landing page still lives at `/home`.
- Unlike Netlify (which proxied out over the public internet to
  `dashboard.summitteachable.com`), Caddy proxies **in-network** to
  `summitteachable:8000` — one less TLS hop, and it keeps working if DNS is mid-flight.

## Deploy a change

Static marketing pages (`about.html`, `markets.html`, `courses.html`, …):

```bash
git add -A && git commit -m "frontend: ..." && git push

ssh -i ~/.ssh/id_ed25519 root@156.67.28.100 \
  'git -C /opt/summitteachable/repo pull --ff-only && chown -R 1000:1000 /opt/summitteachable'
```

No build or restart needed. Backend/template changes still need
`cd /opt/swifteagle && docker compose up -d --build summitteachable`.

## Routing (ported from `netlify.toml`)

| Path | Behaviour |
|---|---|
| `/` | **200-proxy** → Django `/buy/` (course catalog) |
| `/static/*`, `/media/*` | **200-proxy** → Django, so the catalog's assets load |
| `/home` | static `home.html` (the old marketing landing) |
| `/about.html`, `/markets.html`, … | static file from `frontend/` |
| `/about` (no extension) | resolves via `try_files` |
| `/login` | 302 → `dashboard.summitteachable.com/auth/login/` |
| `/register` | 302 → `dashboard.summitteachable.com/auth/register/` |
| `/auth/*` | 302 → dashboard host, path preserved |
| `/buy/*` | 302 → dashboard host (so checkout sessions live on one origin) |
| `/dashboard/*` | 302 → dashboard host, path preserved |

Note the deliberate asymmetry: `/buy/` **listing** is proxied at the apex, but
`/buy/<slug>/` **redirects** to the dashboard host — the session and CSRF cookie
for checkout must be set on the dashboard origin. This is exactly what the
Netlify config did; don't "simplify" it.

Rules live in the `summitteachable.com` block of `/opt/swifteagle/Caddyfile`,
wrapped in `route { }` so the redirects reliably take precedence over the proxy
and file server.

## Rollback — ⚠️ Netlify is NOT currently a viable fallback

Checked at cutover (2026-07-22): all three Netlify origins return
**HTTP 503 `{"error":"usage_exceeded"}`** — the Netlify account has exceeded its
plan's usage limits, so the sites are hard-down there regardless of DNS. They
were already failing for real users *before* this migration.

Repointing DNS back to Netlify would therefore **restore an outage, not the
site**. To make that a real rollback path again you must first resolve the
Netlify account usage (wait for the monthly reset or upgrade the plan) and
confirm `https://<site>.netlify.app/` returns 200.

Practical rollback today = fix forward on the VPS (`git revert` + `git pull`),
which is fast because the frontend is served straight off disk.

If the Netlify account is healthy again, the DNS rollback is: apex A → `75.2.60.5`,
`www` CNAME → `summitteachable.netlify.app`.

Full runbook: `/opt/swifteagle/README.static-sites.md` on the VPS.
