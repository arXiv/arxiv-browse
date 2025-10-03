variable "project_name" {
  description = "The GCP project name"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "container_image" {
  description = "The container image to deploy"
  type        = string
  default     = "gcr.io/arxiv-development/arxiv-browse:latest"
}

variable "max_instances" {
  description = "Maximum number of instances for autoscaling"
  type        = number
  default     = 2
}

variable "cpu_limit" {
  description = "CPU limit for the container"
  type        = string
  default     = "1000m"
}

variable "memory_limit" {
  description = "Memory limit for the container"
  type        = string
  default     = "2Gi"
}

variable "service_account_email" {
  description = "Service account email for the Cloud Run service (empty for default Compute Engine service account)"
  type        = string
  default     = ""  # Empty means use default Compute Engine service account
}

variable "vpc_connector" {
  description = "VPC connector for the Cloud Run service"
  type        = string
  default     = "projects/arxiv-development/locations/us-central1/connectors/clourrunconnector"
}

# Environment variables
variable "base_server" {
  description = "Base server URL"
  type        = string
  default     = "browse.dev.arxiv.org"
}

variable "document_abstract_service" {
  description = "Document abstract service"
  type        = string
  default     = "browse.services.documents.db_docs"
}

variable "document_listing_service" {
  description = "Document listing service"
  type        = string
  default     = "browse.services.listing.db_listing"
}

variable "document_listing_path" {
  description = "Document listing path"
  type        = string
  default     = "gs://arxiv-production-data/ftp"
}

variable "dissemination_storage_prefix" {
  description = "Dissemination storage prefix"
  type        = string
  default     = "gs://arxiv-production-data"
}

variable "document_latest_versions_path" {
  description = "Document latest versions path"
  type        = string
  default     = "gs://arxiv-production-data/ftp"
}

variable "document_original_versions_path" {
  description = "Document original versions path"
  type        = string
  default     = "gs://arxiv-production-data/orig"
}

variable "document_cache_path" {
  description = "Document cache path"
  type        = string
  default     = "gs://arxiv-production-data/ps_cache"
}

variable "latexml_base_url" {
  description = "LaTeXML base URL"
  type        = string
  default     = "https://browse.dev.arxiv.org"
}

variable "help_server" {
  description = "Help server URL"
  type        = string
  default     = "info.dev.arxiv.org"
}

variable "classic_html_bucket" {
  description = "Classic HTML bucket name"
  type        = string
  default     = "arxiv-dev-html-papers"
}

variable "latexml_enabled" {
  description = "Whether LaTeXML is enabled"
  type        = string
  default     = "1"
}

variable "genpdf_api_url" {
  description = "GenPDF API URL"
  type        = string
  default     = "0"
}

variable "genpdf_api_timeout" {
  description = "GenPDF API timeout"
  type        = string
  default     = "590"
}

variable "genpdf_api_storage_prefix" {
  description = "GenPDF API storage prefix"
  type        = string
  default     = "gs://arxiv-sync-test-01"
}

variable "genpdf_service_url" {
  description = "GenPDF service URL"
  type        = string
  default     = "0"
}

variable "classic_db_transaction_isolation_level" {
  description = "Classic DB transaction isolation level"
  type        = string
  default     = "READ UNCOMMITTED"
}

variable "latexml_db_transaction_isolation_level" {
  description = "LaTeXML DB transaction isolation level"
  type        = string
  default     = "READ UNCOMMITTED"
}

variable "source_storage_prefix" {
  description = "Source storage prefix"
  type        = string
  default     = "gs://arxiv-production-data"
}

variable "classic_db_uri_secret_name" {
  description = "Classic DB URI secret name"
  type        = string
  default     = "browse-sqlalchemy-db-uri"
}

variable "latexml_db_uri_secret_name" {
  description = "LaTeXML DB URI secret name"
  type        = string
  default     = "latexml_db_uri_psycog2"
}

variable "copy_secrets_from_arxiv_development" {
  description = "Whether to copy secret values from arxiv-development project"
  type        = bool
  default     = false
}

variable "impersonate_service_account" {
  description = "Service account to impersonate (for development)"
  type        = string
  default     = ""
}

variable "commit_sha" {
  description = "Git commit SHA for deployment tracking"
  type        = string
  default     = ""
}
