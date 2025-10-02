#!/bin/bash

# Deploy arxiv-browse Cloud Run service using Terraform
# Usage: ./deploy.sh -project_name <project> [-region <region>] [-tag <tag>]

set -e

# Default values
REGION="us-central1"
PROJECT_NAME=""
IMAGE_TAG="latest"
IMAGE_REGISTRY="gcr.io/arxiv-development/arxiv-browse"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -project_name)
      PROJECT_NAME="$2"
      shift 2
      ;;
    -region)
      REGION="$2"
      shift 2
      ;;
    -tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 -project_name <project> [-region <region>] [-tag <tag>]"
      echo "  -project_name: GCP project name (required)"
      echo "  -region: GCP region (default: us-central1)"
      echo "  -tag: Docker image tag to deploy (default: latest)"
      exit 0
      ;;
    *)
      echo "Unknown option $1"
      echo "Usage: $0 -project_name <project> [-region <region>] [-tag <tag>]"
      exit 1
      ;;
  esac
done

# Validate required arguments
if [[ -z "$PROJECT_NAME" ]]; then
  echo "Error: -project_name is required"
  echo "Usage: $0 -project_name <project> [-region <region>] [-tag <tag>]"
  exit 1
fi

# Construct full container image name
CONTAINER_IMAGE="${IMAGE_REGISTRY}:${IMAGE_TAG}"

echo "Deploying arxiv-browse to project: $PROJECT_NAME, region: $REGION, image: $CONTAINER_IMAGE"
echo ""
echo "NOTE: This deployment will copy secret values from arxiv-development project."
echo "If you get permission errors, you may need to grant the following permissions:"
echo "  - roles/secretmanager.secretAccessor on arxiv-development project"
echo "  - roles/storage.objectViewer on arxiv-development project (for image access)"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clean up existing Terraform state files and configuration
echo "Cleaning up existing Terraform state files and configuration..."
rm -f *.tfstat*
rm -rf .terraform*
rm -f .terraform.lock.hcl
rm -f variables.tfvars
rm -f main.tf.original
rm -f main.tf.bak
rm -f variables.tfvars.bak

# exit 1

# Create backup of original main.tf for restoration
echo "Creating backup of original main.tf..."
cp main.tf main.tf.original
echo "Backup created."

# Comment out backend configuration for initial deployment
echo "Commenting out backend configuration for initial deployment..."
sed -i.bak '/^  backend "gcs" {/,/^  }/ s/^/  # /' main.tf
rm -f main.tf.bak
echo "Backend configuration reset to commented state."

# Copy variables.tfvars.orig to variables.tfvars if it doesn't exist
if [[ ! -f "variables.tfvars" ]]; then
  echo "Creating variables.tfvars from template..."
  cp variables.tfvars.orig variables.tfvars
fi

# Update project_name, region, and container_image in variables.tfvars
echo "Updating variables.tfvars with project_name=$PROJECT_NAME, region=$REGION, and container_image=$CONTAINER_IMAGE"
sed -i.bak "s/project_name = \".*\"/project_name = \"$PROJECT_NAME\"/" variables.tfvars
sed -i.bak "s/region = \".*\"/region = \"$REGION\"/" variables.tfvars
# Use a different delimiter for sed to avoid issues with special characters
sed -i.bak "s|container_image = \".*\"|container_image = \"$CONTAINER_IMAGE\"|" variables.tfvars

# Clean up backup file
rm -f variables.tfvars.bak

# Determine bucket name (same as project name, sanitized)
STATE_BUCKET_NAME=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | sed -e 's/[^a-z0-9-]/ /g' -e 's/  */-/g' -e 's/^-*//' -e 's/-*$//')
# Check for existing state in env/state (from arxiv-env script)
EXISTING_STATE_PATH="env/state/default.tfstate"
# New state will be stored in browse/state
NEW_STATE_PATH="browse/state/default.tfstate"

echo "Using bucket name: $STATE_BUCKET_NAME"
echo "Checking for existing state at: gs://$STATE_BUCKET_NAME/$EXISTING_STATE_PATH"
echo "New state will be stored at: gs://$STATE_BUCKET_NAME/$NEW_STATE_PATH"

# Check for existing browse state file
echo "Checking for existing browse state file..."
if gsutil ls gs://$STATE_BUCKET_NAME/$NEW_STATE_PATH >/dev/null 2>&1; then
  echo "Found existing browse state file in bucket $STATE_BUCKET_NAME"
  echo "This deployment will update the existing Cloud Run service."
else
  echo "No existing browse state file found, proceeding with new Cloud Run deployment"
fi

# Configure remote backend
echo "Configuring remote state backend..."
echo "Backend configuration:"
echo "  bucket = \"$STATE_BUCKET_NAME\""
echo "  prefix = \"browse/state\""

# Restore the original main.tf with backend configuration
cp main.tf.original main.tf
# Update the backend configuration with the correct bucket and prefix
sed -i.bak "s/bucket = \"project-id\"/bucket = \"$STATE_BUCKET_NAME\"/" main.tf
sed -i.bak 's/prefix = "browse\/state"/prefix = "browse\/state"/' main.tf
rm -f main.tf.bak

# Set the gcloud project to the correct project ID
echo "Setting gcloud project to: $PROJECT_NAME"
gcloud config set project "$PROJECT_NAME"

# Initialize Terraform with remote backend
echo "Running terraform init with remote backend..."
terraform init

# Grant cross-project permissions for image access
echo "Setting up cross-project permissions for image access..."
echo "Granting Cloud Run service agent access to arxiv-development GCR registry..."

# Get the Cloud Run service agent for the target project
CLOUD_RUN_SERVICE_AGENT="service-$(gcloud projects describe $PROJECT_NAME --format='value(projectNumber)')@serverless-robot-prod.iam.gserviceaccount.com"

echo "Cloud Run service agent: $CLOUD_RUN_SERVICE_AGENT"

# Grant the necessary permissions for cross-project image access
echo "Granting permissions for cross-project image access..."

# Grant storage.objectViewer role (for GCR access)
echo "Granting storage.objectViewer role to Cloud Run service agent in arxiv-development project..."
gcloud projects add-iam-policy-binding arxiv-development \
    --member="serviceAccount:$CLOUD_RUN_SERVICE_AGENT" \
    --role="roles/storage.objectViewer" \
    --condition=None \
    --quiet

if [ $? -eq 0 ]; then
  echo "✅ Successfully granted storage.objectViewer role"
else
  echo "⚠️  Warning: Failed to grant storage.objectViewer role automatically."
  echo "   This may be because you don't have IAM admin permissions in arxiv-development project."
  echo "   Please run this command manually in the arxiv-development project:"
  echo "   gcloud projects add-iam-policy-binding arxiv-development \\"
  echo "     --member=\"serviceAccount:$CLOUD_RUN_SERVICE_AGENT\" \\"
  echo "     --role=\"roles/storage.objectViewer\" \\"
  echo "     --condition=None"
  echo ""
  echo "   Or ask someone with IAM admin access to run it for you."
  echo "   Then re-run this deployment script."
  exit 1
fi

# Also try to grant Artifact Registry Reader role (for the specific permission needed)
echo "Granting artifactregistry.reader role to Cloud Run service agent in arxiv-development project..."
gcloud projects add-iam-policy-binding arxiv-development \
    --member="serviceAccount:$CLOUD_RUN_SERVICE_AGENT" \
    --role="roles/artifactregistry.reader" \
    --condition=None \
    --quiet

if [ $? -eq 0 ]; then
  echo "✅ Successfully granted artifactregistry.reader role"
else
  echo "⚠️  Warning: Failed to grant artifactregistry.reader role automatically."
  echo "   This may be because you don't have IAM admin permissions in arxiv-development project."
  echo "   Please run this command manually in the arxiv-development project:"
  echo "   gcloud projects add-iam-policy-binding arxiv-development \\"
  echo "     --member=\"serviceAccount:$CLOUD_RUN_SERVICE_AGENT\" \\"
  echo "     --role=\"roles/artifactregistry.reader\" \\"
  echo "     --condition=None"
  echo ""
  echo "   Or ask someone with IAM admin access to run it for you."
  echo "   Then re-run this deployment script."
  exit 1
fi

# Grant VPC Access Connector usage permission
echo "Granting VPC Access Connector usage permission to Cloud Run service agent in arxiv-development project..."
gcloud projects add-iam-policy-binding arxiv-development \
    --member="serviceAccount:$CLOUD_RUN_SERVICE_AGENT" \
    --role="roles/vpcaccess.user" \
    --condition=None \
    --quiet

if [ $? -eq 0 ]; then
  echo "✅ Successfully granted vpcaccess.user role"
else
  echo "⚠️  Warning: Failed to grant vpcaccess.user role automatically."
  echo "   This may be because you don't have IAM admin permissions in arxiv-development project."
  echo "   Please run this command manually in the arxiv-development project:"
  echo "   gcloud projects add-iam-policy-binding arxiv-development \\"
  echo "     --member=\"serviceAccount:$CLOUD_RUN_SERVICE_AGENT\" \\"
  echo "     --role=\"roles/vpcaccess.user\" \\"
  echo "     --condition=None"
  echo ""
  echo "   Or ask someone with IAM admin access to run it for you."
  echo "   Then re-run this deployment script."
  exit 1
fi

# Plan the deployment
echo "Planning Terraform deployment..."
terraform plan -var-file="variables.tfvars"
if [ $? -ne 0 ]; then
  echo "Terraform plan failed. Please check your configuration and authentication. Exiting."
  exit 1
fi

# Ask for confirmation
read -p "Do you want to apply these changes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "Running terraform apply (creating/updating Cloud Run service)..."
  terraform apply -var-file="variables.tfvars"
  if [ $? -ne 0 ]; then
    echo "Terraform apply failed. Please check your configuration and authentication. Exiting."
    exit 1
  fi
  
  echo "--- Deployment Complete! ---"
  echo "Your project ID is: $PROJECT_NAME"
  echo "Your region is: $REGION"
  echo "Your state bucket is: $STATE_BUCKET_NAME"
  echo "State location: gs://$STATE_BUCKET_NAME/browse/state"
  
  # Show Terraform outputs
  echo "--- Showing Terraform Outputs ---"
  echo "Running terraform output to display all created resources..."
  terraform output
  if [ $? -ne 0 ]; then
    echo "Warning: Failed to retrieve terraform outputs, but deployment was successful."
    echo "You can manually run 'terraform output' to see the outputs."
  fi
  
  # Clean up temporary files created during deployment
  echo ""
  echo "--- Cleaning up temporary files ---"
  rm -f main.tf.original
  rm -f variables.tfvars
  echo "✅ Cleanup complete. Ready for check-in."
else
  echo "Deployment cancelled."
  # Still clean up temporary files even if deployment was cancelled
  echo "Cleaning up temporary files..."
  rm -f main.tf.original
  rm -f variables.tfvars
  echo "✅ Cleanup complete."
  exit 0
fi
