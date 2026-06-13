# CI/CD

Two GitHub Actions workflows:

- **`.github/workflows/ci.yml`** — on every PR to `main`: backend `ruff` + `mypy`
  + `pytest`, frontend `lint` + `tsc` + `vitest` + `build`. Path-filtered (a job
  runs only when its app changed).
- **`.github/workflows/deploy.yml`** — on every merge to `main`: backend →
  Cloud Run, frontend → Netlify. Path-filtered. Infra is provisioned once by
  Terraform (`deploy/gcp`); this pipeline only rolls new images/builds.

## Already configured (in the repo)

| Kind | Name | Value |
|---|---|---|
| variable | `GCP_PROJECT` | `gatherly-499115` |
| variable | `GCP_REGION` | `northamerica-northeast1` |
| variable | `GCP_DEPLOY_SA` | `gatherly-deployer@gatherly-499115.iam.gserviceaccount.com` |
| variable | `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | (set) |
| secret | `NETLIFY_AUTH_TOKEN` | (set) |
| secret | `NETLIFY_SITE_ID` | `534fda63-…` |

→ **Frontend CD is ready.** Merging a change under `gatherly-fe/**` auto-deploys to Netlify.

## You must add (one-time) for backend CD

### 1. `NEXT_PUBLIC_API_URL` (variable) — after the backend is live
```bash
gh variable set NEXT_PUBLIC_API_URL --repo Bmbsolution/genai-demo --body "<cloud-run-url>"
```
(Or paste me the URL and I'll set it.) Frontend reads this at build time.

### 2. GCP Workload Identity Federation — keyless auth for the deploy job
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
- The deployer SA needs `iam.serviceAccountUser` so it can deploy a service that
  runs as the `gatherly-run` runtime SA (granted project-wide above).
- To rotate the Netlify token, replace the `NETLIFY_AUTH_TOKEN` secret (currently
  the personal CLI token — a dedicated CI token is tidier).
- Prefer per-environment deploys? Split `main` → staging and tags → prod; the
  path-filter pattern stays the same.
