# Config vars for deploying to gcp

export PROJ=arxiv-phoenix
export PORT=8000
export BROWSE_MIG=browse
export ZONE=us-east1-d
export LOAD_BALANCER=phoenix-lb
export SERVER_NAME="phoenix.arxiv.org"

# This should not be set to latest so the instance template is
# deterministic but there is probably a better way to do this.
export IMAGE_URL=gcr.io/arxiv-phoenix/browse:0.0.1

