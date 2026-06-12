output "service_url" {
  description = "Public HTTPS URL of the Gatherly API on Cloud Run."
  value       = google_cloud_run_v2_service.api.uri
}

output "artifact_registry" {
  description = "Docker repo to push images to."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"
}

output "sql_connection_name" {
  description = "Cloud SQL instance connection name."
  value       = google_sql_database_instance.pg.connection_name
}
