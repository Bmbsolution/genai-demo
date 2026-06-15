# Gatherly — deployment runbook

**Frontend → Netlify** · **Backend → Railway (FastAPI + managed Postgres)**

## Status

| Piece | Where | State |
|---|---|---|
| Frontend | Netlify — https://gatherly-events-app.netlify.app | **Live** (SSR; `/`, `/login`, `/rsvp/[token]` → 200) |
| Backend | Railway — https://gatherly-be-production.up.railway.app | **Live** (`/health` → 200; email/password sign-in works end-to-end) |

> The backend previously ran on **GCP Cloud Run + Cloud SQL** (`deploy/gcp/`). It
> was moved to Railway and the GCP infra was destroyed (`terraform destroy`),
> because the `manegreinc.com` org policy blocked public access to Cloud Run. The
> `deploy/gcp/` Terraform is kept for reference only.

## 1 · Backend → Railway

Prereqs: the Railway CLI (`npm i -g @railway/cli`), authenticated (`railway login`).

```bash
cd gatherly-be
railway up --service gatherly-be        # Dockerfile build on Railway, then deploy
```

Railway project `gatherly` (env `production`) holds the `gatherly-be` service and
a managed `Postgres`. App env vars are set on the service (see `deploy/CICD.md`),
including:

```
GATHERLY_DATABASE_URL=postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.RAILWAY_PRIVATE_DOMAIN}}:5432/${{Postgres.PGDATABASE}}
GATHERLY_CORS_ALLOW_ORIGIN_REGEX=https://gatherly-events-app[.]netlify[.]app
```

The app creates its tables on first boot (`create_all`) — no migration step.
Verify: `curl https://gatherly-be-production.up.railway.app/health` → `{"data":{"status":"ok",…}}`.

CD: merging a change under `gatherly-be/**` to `main` auto-deploys via
`.github/workflows/deploy.yml` (needs the `RAILWAY_TOKEN` repo secret — see
`deploy/CICD.md`).

## 2 · Point the frontend at the backend

`NEXT_PUBLIC_API_URL` is inlined at build time, so a change needs a frontend rebuild:

```bash
netlify env:set NEXT_PUBLIC_API_URL "https://gatherly-be-production.up.railway.app"
cd gatherly-fe
NEXT_PUBLIC_API_URL=https://gatherly-be-production.up.railway.app \
  netlify deploy --build --prod --site <site-id>
```

`NEXT_PUBLIC_GOOGLE_CLIENT_ID` is already set on the Netlify site.

## 3 · OAuth origin (one click — needed for Google sign-in only)

Google Cloud Console → Credentials → your OAuth **web** client → **Authorized
JavaScript origins** → add `https://gatherly-events-app.netlify.app`.

Email/password sign-in works without this; only Google Sign-In needs it. CORS is
controlled by `GATHERLY_CORS_ALLOW_ORIGIN_REGEX` on the Railway service — update
it there if the frontend domain changes.

## Verified

- Backend: `/health` → 200 publicly; CORS allows the Netlify origin; register
  returns JWTs (end-to-end auth works).
- Frontend: live on Netlify, SSR routes 200, bundle points at the Railway API.

## Tear down

```bash
railway down --service gatherly-be      # remove the service (keeps the project)
# or delete the whole project in the Railway dashboard
```
