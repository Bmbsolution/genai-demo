# Gatherly on GCP — cheapest viable: Cloud Run (scale-to-zero) + Cloud SQL
# Postgres (db-f1-micro) + Secret Manager + Artifact Registry.

locals {
  apis = [
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.apis)
  service            = each.value
  disable_on_destroy = false
}

# --- Container registry -------------------------------------------------------

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "gatherly"
  format        = "DOCKER"
  description   = "Gatherly backend images"
  depends_on    = [google_project_service.apis]
}

# --- Generated secrets --------------------------------------------------------

resource "random_password" "db" {
  length  = 32
  special = false # keep it URL-safe (it goes into the DSN)
}

resource "random_password" "jwt" {
  length  = 48
  special = false
}

# --- Cloud SQL (Postgres) -----------------------------------------------------

resource "google_sql_database_instance" "pg" {
  name                = "gatherly-pg"
  database_version    = "POSTGRES_15"
  region              = var.region
  deletion_protection = false

  settings {
    tier              = var.db_tier
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_HDD" # cheapest

    ip_configuration {
      ipv4_enabled = true # Cloud Run connects via the managed socket, not this IP
    }

    backup_configuration {
      enabled = false # cheapest; enable for anything real (see README)
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_sql_database" "db" {
  name     = var.db_name
  instance = google_sql_database_instance.pg.name
}

resource "google_sql_user" "user" {
  name     = var.db_user
  instance = google_sql_database_instance.pg.name
  password = random_password.db.result
}

# --- Secret Manager -----------------------------------------------------------

resource "google_secret_manager_secret" "jwt" {
  secret_id  = "gatherly-jwt-secret"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "jwt" {
  secret      = google_secret_manager_secret.jwt.id
  secret_data = random_password.jwt.result
}

resource "google_secret_manager_secret" "database_url" {
  secret_id  = "gatherly-database-url"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret = google_secret_manager_secret.database_url.id
  # asyncpg over the Cloud SQL unix socket mounted at /cloudsql/<connection_name>.
  secret_data = "postgresql+asyncpg://${var.db_user}:${random_password.db.result}@/${var.db_name}?host=/cloudsql/${google_sql_database_instance.pg.connection_name}"
}

# --- Runtime identity + IAM ---------------------------------------------------

resource "google_service_account" "run" {
  account_id   = "gatherly-run"
  display_name = "Gatherly Cloud Run runtime"
}

resource "google_secret_manager_secret_iam_member" "jwt_access" {
  secret_id = google_secret_manager_secret.jwt.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run.email}"
}

resource "google_secret_manager_secret_iam_member" "database_url_access" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run.email}"
}

resource "google_project_iam_member" "sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.run.email}"
}

# --- Cloud Run service --------------------------------------------------------

resource "google_cloud_run_v2_service" "api" {
  name                = var.service_name
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  # After the first apply, CI (`gcloud run deploy --image`) owns the running
  # image + client metadata. Ignore them so re-applying infra doesn't roll back
  # the deployed version.
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }

  template {
    service_account = google_service_account.run.email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.image

      ports {
        container_port = 8080
      }

      env {
        name  = "GATHERLY_ENVIRONMENT"
        value = "production"
      }
      env {
        name  = "GATHERLY_GOOGLE_CLIENT_ID"
        value = var.google_client_id
      }
      env {
        name  = "GATHERLY_CORS_ALLOW_ORIGIN_REGEX"
        value = var.cors_allow_origin_regex
      }
      env {
        name = "GATHERLY_DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GATHERLY_JWT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jwt.secret_id
            version = "latest"
          }
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.pg.connection_name]
      }
    }
  }

  depends_on = [
    google_secret_manager_secret_version.database_url,
    google_secret_manager_secret_version.jwt,
    google_secret_manager_secret_iam_member.database_url_access,
    google_secret_manager_secret_iam_member.jwt_access,
    google_project_iam_member.sql_client,
  ]
}

# Public API (the SPA calls it from the browser).
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
