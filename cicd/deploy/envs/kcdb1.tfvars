# Terraform variables for arxiv-browse Cloud Run deployment
# Copy this file to variables.tfvars and modify as needed

# Required variables (will be set by deployment script)
project_name = "arxiv-kcdb1"
region       = "us-central1"

# Container configuration
container_image = "gcr.io/arxiv-development/arxiv-browse:latest"
max_instances   = 2
cpu_limit       = "1000m"
memory_limit    = "2Gi"

# Service account and networking
service_account_email = "" # Empty for default Compute Engine service account
vpc_connector         = "projects/arxiv-kcdb1/locations/us-central1/connectors/cloudrunconnector"

# Application configuration
base_server                            = "browse.kcdb1.arxiv.org"
document_abstract_service              = "browse.services.documents.db_docs"
document_listing_service               = "browse.services.listing.db_listing"
document_listing_path                  = "gs://arxiv-production-data/ftp"
dissemination_storage_prefix           = "gs://arxiv-production-data"
document_latest_versions_path          = "gs://arxiv-production-data/ftp"
document_original_versions_path        = "gs://arxiv-production-data/orig"
document_cache_path                    = "gs://arxiv-production-data/ps_cache"
latexml_base_url                       = "https://browse.kcdb1.arxiv.org"
help_server                            = "info.kcdb1.arxiv.org"
classic_html_bucket                    = "arxiv-kcdb1-html-papers"
latexml_enabled                        = "1"
genpdf_api_url                         = "0"
genpdf_api_timeout                     = "590"
genpdf_api_storage_prefix              = "gs://arxiv-sync-test-01"
genpdf_service_url                     = "0"
classic_db_transaction_isolation_level = "READ UNCOMMITTED"
latexml_db_transaction_isolation_level = "READ UNCOMMITTED"
source_storage_prefix                  = "gs://arxiv-production-data"
min_instances                          = 1

cloudsql_instance = "arxiv-kcdb1:us-central1:main-arxiv-db"

# Secret names
classic_db_uri_secret_name = "main_arxiv_db_readonly_uri"
latexml_db_uri_secret_name = "latexml_db_uri_psycog2"