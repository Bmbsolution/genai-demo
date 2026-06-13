# CI/CD

**Split ownership:** GitHub Actions runs CI for both apps + deploys the
**backend**; **Netlify** builds and deploys the **frontend** from GitHub directly.

- **`.github/workflows/ci.yml`** — on every PR to `main`: backend `ruff` + `mypy`
  + `pytest`, frontend `lint` + `tsc` + `vitest` + `build`. Path-filtered (a job
  runs only when its app changed).
- **`.github/workflows/deploy.yml`** — on every merge to `main` touching
  `gatherly-be/**`: build the image → Cloud Run. Infra is provisioned once by
  Terraform (`deploy/gcp`); this pipeline only rolls new images.
- **Netlify Git integration** — on every push to `main`, Netlify builds
  `gatherly-fe` on its own buildbot and publishes (SSR via the Next.js runtime).
  No GitHub Actions job is involved.

> **Why not deploy the frontend from Actions?** `netlify deploy --build` run on a
> GitHub-hosted runner reliably hangs in the upload phase after a clean build
> (16+ min, no output). Netlify's own buildbot doesn't, so the frontend is
> deployed by Netlify's Git integration instead. The `NETLIFY_*` secrets below
> are no longer used by Actions and can be deleted.

## Frontend — Netlify Git integration (one-time)

In the Netlify UI for the **gatherly-events-app** site (team `fsawadogo`):

1. **Site configuration → Build & deploy → Continuous deployment → Link
   repository** → GitHub → `Bmbsolution/genai-demo`. Authorize the Netlify
   GitHub App for the repo if prompted.
2. Build settings (Netlify also reads `gatherly-fe/netlify.toml`):
   - **Base directory:** `gatherly-fe`
   - **Build command:** `pnpm build`
   - **Publish directory:** `gatherly-fe/.next` (auto-detected by the Next.js runtime)
   - **Production branch:** `main`
3. **Environment variables** (Site configuration → Environment variables):
   - `NEXT_PUBLIC_GOOGLE_CLIENT_ID` — already set ✅
   - `NEXT_PUBLIC_API_URL` — add once the backend is live (the Cloud Run URL)
4. Trigger a deploy (push to `main`, or **Deploys → Trigger deploy**) to confirm.

That's it — every later merge to `main` auto-builds and publishes the frontend.

## Already configured (in the repo) — backend CD

| Kind | Name | Value |
|---|---|---|
| variable | `GCP_PROJECT` | `gatherly-499115` |
| variable | `GCP_REGION` | `northamerica-northeast1` |
| variable | `GCP_DEPLOY_SA` | `gatherly-deployer@gatherly-499115.iam.gserviceaccount.com` |
| variable | `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | (set — also mirror it in Netlify env) |
| secret | `NETLIFY_AUTH_TOKEN` | (unused now — safe to delete) |
| secret | `NETLIFY_SITE_ID` | (unused now — safe to delete) |

## You must add (one-time) for backend CD

### GCP Workload Identity Federation — keyless auth for the deploy job
Run once (needs `gcloud`, project owner). Creates a deployer SA and lets **only
this repo** impersonate it — no long-lived JSON key.

```bash
PROJECT=gatherly-499115
REPO=Bmbsolution/genai-demo
NUM=$(gcloud projects describe $PROJECT --format='value(projectNumber)')
SA=gatherly-deployer@$PROJECT.iam.gserviceaccount.com

gcloud iam service-accounts create gatherly-deployer --project=$PROJECT \
  --display-name="GitHub Actions deployer"

for ROLE in roles/run.admin roles/artifactregistry.writer roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding $PROJECT \
    --member="serviceAccount:$SA" --role="$ROLE" >/dev/null
done

gcloud iam workload-identity-pools create github --project=$PROJECT \
  --location=global --display-name="GitHub"

gcloud iam workload-identity-pools providers create-oidc github \
  --project=$PROJECT --location=global --workload-identity-pool=github \
  --display-name="GitHub OIDC" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='$REPO' && assertion.ref=='refs/heads/main'" \
  --issuer-uri="https://token.actions.githubusercontent.com"

gcloud iam service-accounts add-iam-policy-binding $SA --project=$PROJECT \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$NUM/locations/global/workloadIdentityPools/github/attribute.repository/$REPO"

# Set the provider resource name as the repo secret:
gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --repo $REPO \
  --body "projects/$NUM/locations/global/workloadIdentityPools/github/providers/github"
```

That's it — the next merge touching `gatherly-be/**` builds the image, pushes to
Artifact Registry, and `gcloud run deploy`s it. Terraform ignores the running
image (`lifecycle.ignore_changes`), so re-applying infra won't roll it back.

## Notes

- **Action pinning:** every third-party action is pinned to a commit SHA (with a
  `# vN` comment) — mutable tags can be re-pointed to malicious code, which is
  acute for the backend job (`id-token: write` + GCP SA). Keep them current with
  Dependabot digest updates (`.github/dependabot.yml`, package-ecosystem
  `github-actions`).
- **WIF scope:** the trust policy's `attribute-condition` pins both the repo and
  `refs/heads/main`, so only this repo's `main`-branch runs can mint a token —
  a malicious PR can't impersonate the deployer SA.
- **Deploy ref guard:** every deploy job is gated on `github.ref == 'refs/heads/main'`,
  so `workflow_dispatch` (or anything else) can only deploy from `main` — not from
  an arbitrary branch where prod secrets would otherwise be exposed.
- **Optional gate:** to require a human approval before each prod deploy, put the
  deploy jobs in a GitHub **Environment** (`production`) with required reviewers
  and move the secrets there. Not enabled here because it would block the
  "deploy automatically on every merge" behaviour you asked for — opt in if you
  want a manual approval step instead.
- The deployer SA needs `iam.serviceAccountUser` so it can deploy a service that
  runs as the `gatherly-run` runtime SA (granted project-wide above).
- To rotate the Netlify token, replace the `NETLIFY_AUTH_TOKEN` secret (currently
  the personal CLI token — a dedicated CI token is tidier).
- Prefer per-environment deploys? Split `main` → staging and tags → prod; the
  path-filter pattern stays the same.
