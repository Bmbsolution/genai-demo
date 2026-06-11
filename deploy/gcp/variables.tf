variable "project_id" {
  type        = string
  description = "GCP project id (e.g. gatherly-499115)."
}

variable "region" {
  type        = string
  description = "Region for Cloud Run, Cloud SQL, and Artifact Registry."
  default     = "northamerica-northeast1"
}

variable "service_name" {
  type        = string
  description = "Cloud Run service name."
  default     = "gatherly-api"
}

variable "image" {
  type        = string
  description = <<-EOT
    Container image to deploy. Defaults to a public placeholder so the FIRST
    `terraform apply` succeeds before you have pushed an image. After pushing,
    re-apply with -var image=<region>-docker.pkg.dev/<project>/gatherly/gatherly-api:<tag>.
  EOT
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "google_client_id" {
  type        = string
  description = "Google OAuth web client id (public, not a secret)."
}

variable "cors_allow_origin_regex" {
  type        = string
  description = "Regex of allowed browser origins for the API (frontend domains)."
  default     = "https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?|https://([a-z0-9-]+\\.)*netlify\\.app"
}

variable "db_tier" {
  type        = string
  description = "Cloud SQL machine tier. db-f1-micro is the cheapest."
  default     = "db-f1-micro"
}

variable "db_name" {
  type    = string
  default = "gatherly"
}

variable "db_user" {
  type    = string
  default = "gatherly_app"
}

variable "min_instances" {
  type        = number
  description = "Cloud Run min instances. 0 = scale to zero (cheapest)."
  default     = 0
}

variable "max_instances" {
  type    = number
  default = 2
}
