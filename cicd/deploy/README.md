# Arxiv-Browse Terraform Deployment

This Terraform project deploys the arxiv-browse Cloud Run service to Google Cloud Platform.

## Overview

The project creates and manages:
- Cloud Run service for arxiv-browse
- IAM bindings for secret access
- GCS backend for Terraform state management

## Prerequisites

1. **Google Cloud SDK**: Install and configure `gcloud` CLI
2. **Terraform**: Install Terraform >= 1.0
3. **Authentication**: Ensure you have proper GCP authentication set up
4. **Project Setup**: The target project should be created using the `arxiv-env` script, which automatically grants the necessary cross-project IAM permissions
5. **Service Account**: The service account specified in variables must exist and have necessary permissions

## Files

- `main.tf` - Main Terraform configuration with GCS backend
- `variables.tf` - Variable definitions
- `outputs.tf` - Output definitions
- `variables.tfvars.orig` - Template for variable values
- `deploy.sh` - Deployment script
- `cloudrun.yaml` - Original Cloud Run configuration (for reference)

## Usage

### Workflow

1. **Create a new project** using the `arxiv-env` script (this automatically grants cross-project permissions):
   ```bash
   cd /path/to/arxiv-iac/arxiv-env
   ./arxiv-env -project_name your-project-name
   ```

2. **Deploy the arxiv-browse service** to the created project:
   ```bash
   cd /path/to/arxiv-browse/cicd/deploy
   ./deploy.sh -project_name your-project-name
   ```

### Quick Start

1. **Deploy to a project:**
   ```bash
   ./deploy.sh -project_name your-project-name
   ```

2. **Deploy to a specific region:**
   ```bash
   ./deploy.sh -project_name your-project-name -region us-east1
   ```

3. **Deploy with a specific Docker tag:**
   ```bash
   ./deploy.sh -project_name your-project-name -tag v1.2.3
   ```

4. **Deploy with all options:**
   ```bash
   ./deploy.sh -project_name your-project-name -region us-east1 -tag v1.2.3
   ```

### Manual Deployment

1. **Copy and customize variables:**
   ```bash
   cp variables.tfvars.orig variables.tfvars
   # Edit variables.tfvars with your values
   ```

2. **Initialize Terraform:**
   ```bash
   terraform init
   ```

3. **Plan deployment:**
   ```bash
   terraform plan -var-file="variables.tfvars"
   ```

4. **Apply changes:**
   ```bash
   terraform apply -var-file="variables.tfvars"
   ```

## State Management

The Terraform state is stored in a GCS bucket with the following structure:
- **Bucket**: `{project-name}` (sanitized)
- **Path**: `browse/state/default.tfstate`

The deployment script automatically:
1. Checks for existing state
2. Downloads and uses existing state if found
3. Migrates state to remote backend after deployment
4. Restores the original main.tf configuration

## Configuration

### Required Variables

- `project_name` - GCP project name (required)

### Optional Variables

- `region` - GCP region (default: us-central1)
- `tag` - Docker image tag to deploy (default: latest)

### Key Variables

- `container_image` - Docker image to deploy
- `service_account_email` - Service account for Cloud Run
- `vpc_connector` - VPC connector for private networking
- `max_instances` - Maximum number of Cloud Run instances
- `cpu_limit` / `memory_limit` - Resource limits

### Environment Variables

The Cloud Run service is configured with numerous environment variables for:
- Database connections
- Storage paths
- Service URLs
- Configuration flags

See `variables.tf` for the complete list.

## Outputs

After deployment, the following outputs are available:
- `service_url` - The Cloud Run service URL
- `service_name` - The service name
- `service_location` - The service location
- `service_id` - The service ID

## Troubleshooting

### State Issues
If you encounter state-related issues:
```bash
# Reinitialize with remote state
terraform init -migrate-state

# Check state
terraform state list
```

### Authentication Issues
Ensure proper authentication:
```bash
# Check current authentication
gcloud auth list

# Set up application default credentials
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_NAME
```

### Service Account Permissions
The service account needs:
- `roles/run.admin` - To manage Cloud Run services
- `roles/secretmanager.secretAccessor` - To access secrets
- `roles/iam.serviceAccountUser` - To use the service account

### Cross-Project Permission Issues
If you encounter permission errors related to:
- Docker image pulling from `gcr.io/arxiv-development/arxiv-browse`
- VPC connector access
- Secret access from `arxiv-development` project

**Solution**: Ensure the project was created using the `arxiv-env` script, which automatically grants these permissions. If the project was created manually, you need to grant the following permissions in the `arxiv-development` project:

```bash
# Get the Cloud Run service agent for your project
CLOUD_RUN_SERVICE_AGENT="service-$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')@serverless-robot-prod.iam.gserviceaccount.com"

# Grant the required permissions
gcloud projects add-iam-policy-binding arxiv-development \
    --member="serviceAccount:$CLOUD_RUN_SERVICE_AGENT" \
    --role="roles/storage.objectViewer" \
    --condition=None

gcloud projects add-iam-policy-binding arxiv-development \
    --member="serviceAccount:$CLOUD_RUN_SERVICE_AGENT" \
    --role="roles/artifactregistry.reader" \
    --condition=None

gcloud projects add-iam-policy-binding arxiv-development \
    --member="serviceAccount:$CLOUD_RUN_SERVICE_AGENT" \
    --role="roles/vpcaccess.user" \
    --condition=None
```

## Security Notes

- Database credentials are stored in Google Secret Manager
- The service uses VPC connector for private networking
- IAM bindings are automatically created for secret access
- State files are stored in GCS with appropriate access controls

## Development

To modify the configuration:
1. Update `variables.tf` for new variables
2. Update `main.tf` for resource changes
3. Update `variables.tfvars.orig` for default values
4. Test with `terraform plan` before applying
