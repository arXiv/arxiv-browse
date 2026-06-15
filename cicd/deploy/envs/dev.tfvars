# Terraform variables for arxiv-browse Cloud Run deployment
# Copy this file to variables.tfvars and modify as needed

# Required variables (will be set by deployment script)
project_name = "arxiv-development"
region       = "us-central1"

# Container configuration
container_image = "gcr.io/arxiv-development/arxiv-browse:latest"
# gcr.io/arxiv-development/arxiv-browse:c3fed0a1af197f1627e264f162bdb0a8a31c9e79
max_instances = 2
cpu_limit     = "1000m"
memory_limit  = "2Gi"

# Service account and networking
service_account_email = "" # Empty for default Compute Engine service account
vpc_connector         = "projects/arxiv-development/locations/us-central1/connectors/clourrunconnector"

# Application configuration
base_server                            = "browse.dev.arxiv.org"
document_abstract_service              = "browse.services.documents.db_docs"
document_listing_service               = "browse.services.listing.db_listing"
document_listing_path                  = "gs://arxiv-production-data/ftp"
dissemination_storage_prefix           = "gs://arxiv-production-data"
document_latest_versions_path          = "gs://arxiv-production-data/ftp"
document_original_versions_path        = "gs://arxiv-production-data/orig"
document_cache_path                    = "gs://arxiv-production-data/ps_cache"
latexml_base_url                       = "https://browse.dev.arxiv.org"
help_server                            = "info.dev.arxiv.org"
classic_html_bucket                    = "arxiv-dev-html-papers"
latexml_enabled                        = "1"
genpdf_api_url                         = ""
genpdf_api_timeout                     = "590"
genpdf_api_storage_prefix              = "gs://arxiv-sync-test-01"
genpdf_service_url                     = ""
classic_db_transaction_isolation_level = "READ UNCOMMITTED"
latexml_db_transaction_isolation_level = "READ UNCOMMITTED"
source_storage_prefix                  = "gs://arxiv-production-data"
min_instances                          = 1
session_affinity                       = true
cloudsql_instance                      = "arxiv-development:us-east4:arxiv-db-dev"
browse_minimal_banner_enabled          = "1"
browse_user_banner_enabled             = "1"
browse_special_message_enabled         = "1"
latexml_bucket                         = "gs://latexml_arxiv_id_converted"
auth_server                            = "dev.arxiv.org"

# Secret names
classic_db_uri_secret_name = "browse-sqlalchemy-db-uri"
latexml_db_uri_secret_name = "latexml_db_uri_psycog2"

allow_unauthenticated = true