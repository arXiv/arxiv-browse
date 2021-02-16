#!/bin/bash

source config.sh

if [ ! $1 ]
then
    echo "Must pass image URL as first parm"
    exit 1
fi


gcloud container images describe $1

if [ %! ]
then
    echo "No image found for $1"
    gcloud container images list
    exit 1
fi

set -ef
TEMPLATE="browse-template-$(date +%Y%m%d-%H%M%S)"

#### UPDATE PROCESS ####

# create a new template with a new name
gcloud compute instance-templates create-with-container $TEMPLATE \
       --machine-type e2-medium \
       --tags=allow-browse-health-check \
       --container-env-file=env_values.txt \
       --container-image $IMAGE_URL

# change the template of the instance group
gcloud compute instance-groups managed set-instance-template $BROWSE_MIG \
       --template=$TEMPLATE \
       --zone=$ZONE

# start a rolling update of the instance group
gcloud compute instance-groups managed rolling-action start-update $BROWSE_MIG \
       --version template=$TEMPLATE \
       --max-surge 4 \
       --zone=$ZONE
