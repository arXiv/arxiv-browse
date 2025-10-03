terraform {
  required_version = "~> 1.13"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.2"
    }
  }
  
  # Backend configuration will be added dynamically by the script
  backend "gcs" {
    bucket = var.bucket
    prefix = "browse/state"
  }
}

provider "google" {
  project = var.project_name
  region  = var.region
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "arxiv_browse" {
  name     = "arxiv-browse"
  location = var.region
  
  deletion_protection = false

  template {
    labels = {
      "managed-by" = "terraform"
    }

    scaling {
      max_instance_count = var.max_instances
    }

    containers {
      name  = "arxiv-browse"
      image = var.commit_sha != "" ? "${split(":", var.container_image)[0]}:${var.commit_sha}" : var.container_image

      ports {
        name           = "http1"
        container_port = 8080
      }

      env {
        name  = "BASE_SERVER"
        value = var.base_server
      }

      env {
        name  = "DOCUMENT_ABSTRACT_SERVICE"
        value = var.document_abstract_service
      }

      env {
        name  = "DOCUMENT_LISTING_SERVICE"
        value = var.document_listing_service
      }

      env {
        name  = "DOCUMENT_LISTING_PATH"
        value = var.document_listing_path
      }

      env {
        name  = "DISSEMINATION_STORAGE_PREFIX"
        value = var.dissemination_storage_prefix
      }

      env {
        name  = "DOCUMENT_LATEST_VERSIONS_PATH"
        value = var.document_latest_versions_path
      }

      env {
        name  = "DOCUMENT_ORIGNAL_VERSIONS_PATH"
        value = var.document_original_versions_path
      }

      env {
        name  = "DOCUMENT_CACHE_PATH"
        value = var.document_cache_path
      }

      env {
        name  = "LATEXML_BASE_URL"
        value = var.latexml_base_url
      }

      env {
        name  = "HELP_SERVER"
        value = var.help_server
      }

      env {
        name  = "CLASSIC_HTML_BUCKET"
        value = var.classic_html_bucket
      }

      env {
        name  = "LATEXML_ENABLED"
        value = var.latexml_enabled
      }

      env {
        name  = "GENPDF_API_URL"
        value = var.genpdf_api_url
      }

      env {
        name  = "GENPDF_API_TIMEOUT"
        value = var.genpdf_api_timeout
      }

      env {
        name  = "GENPDF_API_STORAGE_PREFIX"
        value = var.genpdf_api_storage_prefix
      }

      env {
        name  = "GENPDF_SERVICE_URL"
        value = var.genpdf_service_url
      }

      env {
        name  = "CLASSIC_DB_TRANSACTION_ISOLATION_LEVEL"
        value = var.classic_db_transaction_isolation_level
      }

      env {
        name  = "LATEXML_DB_TRANSACTION_ISOLATION_LEVEL"
        value = var.latexml_db_transaction_isolation_level
      }

      env {
        name  = "SOURCE_STORAGE_PREFIX"
        value = var.source_storage_prefix
      }

      dynamic "env" {
        for_each = var.copy_secrets_from_arxiv_development ? [1] : []
        content {
          name  = "CLASSIC_DB_URI"
          value_source {
            secret_key_ref {
              secret  = "projects/${var.project_name}/secrets/${var.classic_db_uri_secret_name}"
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = var.copy_secrets_from_arxiv_development ? [1] : []
        content {
          name  = "LATEXML_DB_URI"
          value_source {
            secret_key_ref {
              secret  = "projects/${var.project_name}/secrets/${var.latexml_db_uri_secret_name}"
              version = "latest"
            }
          }
        }
      }

      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
      }

      liveness_probe {
        http_get {
          path = "/"
          port = 8080
        }
        initial_delay_seconds = 30
        timeout_seconds      = 2
        period_seconds       = 60
        failure_threshold    = 3
      }

      startup_probe {
        tcp_socket {
          port = 8080
        }
        timeout_seconds   = 240
        period_seconds    = 240
        failure_threshold = 1
      }
    }

    service_account = var.service_account_email != "" ? var.service_account_email : "${data.google_project.current.number}-compute@developer.gserviceaccount.com"

    # VPC connector disabled for now - can be enabled later if needed
    # dynamic "vpc_access" {
    #   for_each = var.vpc_connector != "" ? [1] : []
    #   content {
    #     connector = var.vpc_connector
    #     egress    = "PRIVATE_RANGES_ONLY"
    #   }
    # }

    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# Note: The Cloud Run service agent from the target project needs to be granted
# access to the arxiv-development project's GCR registry. This should be done
# manually in the arxiv-development project by granting the following service account
# the roles/storage.objectViewer role:
# service-953276348471@serverless-robot-prod.iam.gserviceaccount.com

# Note: The service account ${var.service_account_email} should already have
# the necessary permissions to pull images from gcr.io/arxiv-development/arxiv-browse
# These permissions are typically granted at the project level in arxiv-development

# Grant current user/service account access to read secrets from arxiv-development
data "google_client_openid_userinfo" "me" {}

# Get current project info for default service account
data "google_project" "current" {
  project_id = var.project_name
}

# Determine if the current user is a service account or regular user
locals {
  is_service_account = can(regex(".*@.*\\.iam\\.gserviceaccount\\.com$", data.google_client_openid_userinfo.me.email))
  member_prefix = local.is_service_account ? "serviceAccount" : "user"
}

resource "google_project_iam_member" "secret_reader" {
  project = "arxiv-development"
  role    = "roles/secretmanager.secretAccessor"
  member  = "${local.member_prefix}:${data.google_client_openid_userinfo.me.email}"
}

resource "google_project_iam_member" "secret_version_reader" {
  project = "arxiv-development"
  role    = "roles/secretmanager.viewer"
  member  = "${local.member_prefix}:${data.google_client_openid_userinfo.me.email}"
}

resource "google_project_iam_member" "storage_reader" {
  project = "arxiv-development"
  role    = "roles/storage.objectViewer"
  member  = "${local.member_prefix}:${data.google_client_openid_userinfo.me.email}"
}

# Create secrets in the target project (only when copying secrets)
# Terraform will handle the case where secrets already exist
resource "google_secret_manager_secret" "classic_db_uri" {
  count     = var.copy_secrets_from_arxiv_development ? 1 : 0
  secret_id = var.classic_db_uri_secret_name
  project   = var.project_name

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
  
  lifecycle {
    ignore_changes = [labels, replication]
  }
}

resource "google_secret_manager_secret" "latexml_db_uri" {
  count     = var.copy_secrets_from_arxiv_development ? 1 : 0
  secret_id = var.latexml_db_uri_secret_name
  project   = var.project_name

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
  
  lifecycle {
    ignore_changes = [labels, replication]
  }
}

# Copy secret values from arxiv-development project (if accessible)
data "google_secret_manager_secret_version" "classic_db_uri_source" {
  count   = var.copy_secrets_from_arxiv_development ? 1 : 0
  project = "arxiv-development"
  secret  = var.classic_db_uri_secret_name
  
  depends_on = [
    google_project_iam_member.secret_reader
  ]
}

data "google_secret_manager_secret_version" "latexml_db_uri_source" {
  count   = var.copy_secrets_from_arxiv_development ? 1 : 0
  project = "arxiv-development"
  secret  = var.latexml_db_uri_secret_name
  
  depends_on = [
    google_project_iam_member.secret_reader
  ]
}


resource "google_secret_manager_secret_version" "classic_db_uri_version" {
  count       = var.copy_secrets_from_arxiv_development ? 1 : 0
  secret      = google_secret_manager_secret.classic_db_uri[0].id
  secret_data = data.google_secret_manager_secret_version.classic_db_uri_source[0].secret_data
}

resource "google_secret_manager_secret_version" "latexml_db_uri_version" {
  count       = var.copy_secrets_from_arxiv_development ? 1 : 0
  secret      = google_secret_manager_secret.latexml_db_uri[0].id
  secret_data = data.google_secret_manager_secret_version.latexml_db_uri_source[0].secret_data
}

# IAM binding for the service account to access secrets
# Grant access to the default Compute Engine service account when no specific service account is provided
resource "google_secret_manager_secret_iam_binding" "classic_db_uri" {
  count     = var.copy_secrets_from_arxiv_development ? 1 : 0
  project   = var.project_name
  secret_id = var.classic_db_uri_secret_name
  role      = "roles/secretmanager.secretAccessor"
  members = var.service_account_email != "" ? [
    "serviceAccount:${var.service_account_email}",
  ] : [
    "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com",
  ]
  
  depends_on = [google_secret_manager_secret.classic_db_uri]
}

resource "google_secret_manager_secret_iam_binding" "latexml_db_uri" {
  count     = var.copy_secrets_from_arxiv_development ? 1 : 0
  project   = var.project_name
  secret_id = var.latexml_db_uri_secret_name
  role      = "roles/secretmanager.secretAccessor"
  members = var.service_account_email != "" ? [
    "serviceAccount:${var.service_account_email}",
  ] : [
    "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com",
  ]
  
  depends_on = [google_secret_manager_secret.latexml_db_uri]
}

# Enable Secret Manager API
resource "google_project_service" "secretmanager" {
  project = var.project_name
  service = "secretmanager.googleapis.com"
  
  disable_dependent_services = false
  disable_on_destroy        = false
}
