# Gatherly — deployment runbook

**Frontend → Netlify** · **Backend → GCP (Cloud Run + Cloud SQL)**

## Status

| Piece | Where | State |
|---|---|---|
| Frontend | Netlify — https://gatherly-events-app.netlify.app | **Live** (SSR; `/`, `/login`, `/rsvp/[token]` → 200) |
| Backend | GCP Cloud Run + Cloud SQL (`deploy/gcp`) | **Apply-ready** — image verified to build + boot; run `terraform apply` on your machine |

> `gcloud`/`terraform` can't run in the dev sandbox, so the backend `apply` runs
> on your machine. The image is de-risked: `docker build` succeeds and the
> container boots and serves `/health` → `200`.

## 1 · Backend → GCP

Prereqs: `gcloud`, `terraform >= 1.5`, `docker`; a GCP project with billing on.

```bash
gcloud auth login
gcloud auth application-default login          # Terraform uses these creds
gcloud config set project gatherly-499115

cd deploy/gcp
# terraform.tfvars is already filled (project, region, Google client id,
# and CORS locked to the Netlify origin). Review it, then:
terraform init
terraform apply                                # ~10 min (Cloud SQL is slow)

# Build & push the real backend image, then roll it out:
./build-and-push.sh gatherly-499115 northamerica-northeast1
terraform apply -var="image=northamerica-northeast1-docker.pkg.dev/gatherly-499115/gatherly/gatherly-api:latest"

API_URL=$(terraform output -raw service_url)
curl "$API_URL/health"                         # → {"data":{"status":"ok",...}}
```

The app creates its tables on first boot (`create_all`). Sign up through the UI,
or seed a demo host via the Cloud SQL Auth Proxy.

## 2 · Point the live frontend at the backend

The frontend deploys from GitHub via Netlify's Git integration (see
`deploy/CICD.md`). Set the API URL as a Netlify env var, then trigger a rebuild
(`NEXT_PUBLIC_*` is inlined at build time):

```bash
netlify env:set NEXT_PUBLIC_API_URL "$API_URL"   # the Cloud Run URL from step 1
```
Then trigger a rebuild so it gets inlined: push any commit to `main`, or hit
**Deploys → Trigger deploy** in the Netlify UI.

`NEXT_PUBLIC_GOOGLE_CLIENT_ID` is already set on the Netlify site.

## 3 · OAuth origin (one click)

Google Cloud Console → Credentials → your OAuth **web** client → **Authorized
JavaScript origins** → add `https://gatherly-events-app.netlify.app`.

CORS is already locked to that origin via `terraform.tfvars`; if you change the
Netlify domain, update it there and `terraform apply` again.

## Verified before handing off

- Backend image: `docker build` ✓ · container boots + `/health` 200 ✓
- Frontend: live on Netlify, SSR routes return 200 ✓
- Terraform: env + secrets (DB URL, JWT) wired into Cloud Run, Cloud SQL socket mounted ✓

## Tear down

```bash
cd deploy/gcp && terraform destroy
```

Cloud SQL is the only meaningful idle cost; destroy (or stop the instance) when
you're not demoing.
