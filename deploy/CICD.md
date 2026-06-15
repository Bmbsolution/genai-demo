# CI/CD

**Split ownership:** GitHub Actions runs CI for both apps + deploys the
**backend to Railway**; **Netlify** builds and serves the **frontend**.

- **`.github/workflows/ci.yml`** — on every PR to `main`: backend `ruff` + `mypy`
  + `pytest`, frontend `lint` + `tsc` + `vitest` + `build`. Path-filtered (a job
  runs only when its app changed).
- **`.github/workflows/deploy.yml`** — on every merge to `main` touching
  `gatherly-be/**`: `railway up` deploys the FastAPI service to **Railway**
  (Dockerfile build). Railway hosts the API + managed Postgres.
- **Frontend** — deployed to **Netlify**. Its build inlines `NEXT_PUBLIC_API_URL`
  (the Railway API URL) at build time, so a backend URL change needs a frontend
  rebuild.

> **History:** the backend used to run on GCP Cloud Run, provisioned by Terraform
> (`deploy/gcp/`, now destroyed). We moved to Railway because the `manegreinc.com`
> org policy (Domain Restricted Sharing) blocked public `allUsers` access to Cloud
> Run and no one could lift it. The `deploy/gcp/` Terraform is kept for reference
> only — it is not used.

## Backend — Railway

Live API: **https://gatherly-be-production.up.railway.app** · Railway project
`gatherly` (service `gatherly-be` + `Postgres`), environment `production`.

### One-time: the deploy token

CD authenticates to Railway with a project-scoped token:

1. Railway → project **gatherly** → **Settings → Tokens** → create a token scoped
   to the **production** environment.
2. Add it as the GitHub repo secret **`RAILWAY_TOKEN`**:
   ```bash
   gh secret set RAILWAY_TOKEN --repo Bmbsolution/genai-demo --body "<token>"
   ```

That's it — the next merge touching `gatherly-be/**` runs `railway up --service
gatherly-be --ci`, which builds the Dockerfile on Railway and waits for the
deploy to go live (failing the job if the build fails). `workflow_dispatch` also
triggers a manual roll.

### Backend env vars (set on the Railway service, not in CI)

| Var | Value |
|---|---|
| `GATHERLY_ENVIRONMENT` | `production` |
| `GATHERLY_DATABASE_URL` | `postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.RAILWAY_PRIVATE_DOMAIN}}:5432/${{Postgres.PGDATABASE}}` |
| `GATHERLY_JWT_SECRET` | (random, HS256) |
| `GATHERLY_GOOGLE_CLIENT_ID` | the OAuth web client id |
| `GATHERLY_CORS_ALLOW_ORIGIN_REGEX` | `https://gatherly-events-app[.]netlify[.]app` (use `[.]`, not `\.` — the shell mangles backslashes) |

Manual deploy from a workstation: `cd gatherly-be && railway up` (CLI already
linked to the project).

## Frontend — Netlify

The site **gatherly-events-app** (team `fsawadogo`) serves `gatherly-fe`. Deploy
options:

- **CLI (current):** `cd gatherly-fe && netlify deploy --build --prod --site <id>`
  with `NEXT_PUBLIC_API_URL` exported (works from a workstation; the CLI push
  hangs on GitHub runners, so it's not in Actions).
- **Netlify Git integration (optional, recommended):** link `Bmbsolution/genai-demo`
  in the Netlify UI (base dir `gatherly-fe`, build `pnpm build`, branch `main`) so
  pushes auto-build on Netlify's infra. `gatherly-fe/netlify.toml` already skips
  builds on backend-only commits.

**Env vars** (Netlify site → Environment variables):

| Var | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://gatherly-be-production.up.railway.app` |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | the OAuth web client id |

## Notes

- **Deploy ref guard:** every deploy job is gated on `github.ref == 'refs/heads/main'`,
  so `workflow_dispatch` can only deploy from `main` — not an arbitrary branch.
- **Action pinning:** third-party actions are pinned to commit SHAs; keep them
  current with Dependabot (`.github/dependabot.yml`). The Railway CLI is installed
  via `npm i -g @railway/cli` in the job.
- **Google sign-in** needs the Netlify origin added to the OAuth client's
  Authorized JavaScript origins in Google Cloud Console (independent of CI).
- The old `NETLIFY_*` and `GCP_*` repo secrets/variables are no longer used and
  can be deleted.
