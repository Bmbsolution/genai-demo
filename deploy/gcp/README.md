# Deploy Gatherly to GCP (Cloud Run + Cloud SQL)

Cheapest-viable production setup, all as Terraform:

| Piece | Service | Cost posture |
|---|---|---|
| API | Cloud Run (scale-to-zero) | pay per request; ~$0 idle |
| Database | Cloud SQL Postgres 15, `db-f1-micro`, 10 GB HDD, no backups | a few $/month (always-on) |
| Secrets | Secret Manager (JWT secret, DB URL) | negligible |
| Images | Artifact Registry | negligible |

> The only meaningful idle cost is Cloud SQL. To pause spend, `terraform destroy`
> (or stop the SQL instance) when you're not demoing.

## Prerequisites (one-time)

```bash
gcloud auth login
gcloud auth application-default login      # Terraform uses these credentials
gcloud config set project gatherly-499115
# Make sure billing is enabled on the project (Console → Billing).
```

You need: `terraform >= 1.5`, `gcloud`, and `docker`.

## Deploy (first time)

```bash
cd deploy/gcp
cp terraform.tfvars.example terraform.tfvars     # then edit the values
terraform init
terraform apply                                  # ~10 min (Cloud SQL is slow to create)
```

The first apply deploys a **placeholder** image so everything stands up. Now
build and push the real backend image, then roll it out:

```bash
./build-and-push.sh gatherly-499115 northamerica-northeast1
terraform apply -var="image=northamerica-northeast1-docker.pkg.dev/gatherly-499115/gatherly/gatherly-api:latest"
```

Grab the URL:

```bash
terraform output service_url      # e.g. https://gatherly-api-xxxx.a.run.app
curl "$(terraform output -raw service_url)/health"
```

The app creates its tables on first boot (SQLAlchemy `create_all`). Seed a host
if you want demo data (one-off, from your machine, pointed at the same DB via the
Cloud SQL Auth Proxy) — or just sign up through the UI.

## Point the frontend at it

The Next.js app reads `NEXT_PUBLIC_API_URL`. For the deployed frontend
(e.g. Netlify) set:

```
NEXT_PUBLIC_API_URL=https://gatherly-api-xxxx.a.run.app
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<your Google web client id>
```

Then tighten the API's CORS to that origin:

```bash
terraform apply -var='cors_allow_origin_regex=https://gatherly\.netlify\.app'
```

Also add your deployed frontend origin to the Google OAuth client's
**Authorized JavaScript origins** (Google Cloud Console → Credentials).

## Tear down

```bash
terraform destroy
```

## Notes / production hardening (not in this cheapest-viable cut)

- **Migrations:** the app uses `create_all` on startup. For real change
  management, add Alembic and run migrations as a release step instead.
- **Backups:** `backup_configuration.enabled = false` for cost. Turn on for prod.
- **State:** Terraform state holds generated secrets. Use a remote backend
  (GCS bucket with versioning + encryption) for anything beyond a solo demo.
- **DB availability:** `ZONAL` (single zone). Use `REGIONAL` for HA.
