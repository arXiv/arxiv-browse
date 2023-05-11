#!/bin/bash
# makes the managed instance group for browse
#set -evuo pipefail
set -vu

# # Need to open the firewall to perform health check on instances
gcloud compute firewall-rules create allow-browse-health-check \
        --project=$PROJ \
        --allow tcp:$PORT \
        --source-ranges 130.211.0.0/22,35.191.0.0/16,209.85.204.0/22 \
        --network default

TEMPLATE="browse-template-$(date +%Y%m%d-%H%M%S)"

# make template
gcloud compute instance-templates create-with-container $TEMPLATE \
       --project=$PROJ \
       --machine-type e2-medium \
       --tags=allow-browse-health-check \
       --container-env-file=env_values.txt \
       --container-image $IMAGE_URL

# Make health check for instance group
# Host is mandatory since Flask will mysteriously 404 if it deosn't match SERVER_NAME
gcloud compute health-checks create http browse-health-check \
       --project=$PROJ \
       --check-interval=10s \
       --host=phoenix.arxiv.org \
       --port=$PORT

# make instance group
gcloud compute instance-groups managed create $BROWSE_MIG \
       --project=$PROJ \
       --base-instance-name browse \
       --initial-delay=120s \
       --size 1 \
       --template $TEMPLATE \
       --health-check browse-health-check \
       --zone=$ZONE

# Set named port for the load balancer to pick up.
#
# By default, the load balancer is looking for a port named "http". We
# had problems using other names.
gcloud compute instance-groups managed set-named-ports $BROWSE_MIG \
       --project=$PROJ \
       --named-ports http:$PORT \
       --zone=$ZONE

# Not sure about the above command with --named-port http:$PORT
# There is a chance it should be something like --namec-port browse-http:$PORT
