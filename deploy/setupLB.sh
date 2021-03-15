#!/bin/bash
### Setting up the load balancer for browse
### Uses existing load balancer

set -evu

# Create a backend service
#
# This looks for a port named "http" on the instance group by default.
# BDC34 was having problem with other names but it should be investigated
# since having port 8000 named http is confusing.
gcloud compute backend-services create browse-backend \
       --project=$PROJ \
       --health-checks=browse-health-check \
       --global

# Add backend as a link to classifier instance group
gcloud compute backend-services add-backend browse-backend \
       --project=$PROJ \
       --instance-group=$BROWSE_MIG \
       --instance-group-zone=$ZONE \
       --balancing-mode=RATE \
       --max-rate=200 \
       --global



#################### Load Balancers ####################

gcloud compute ssl-certificates  create phoenix-arxiv-org-cert \
     --project=$PROJ \
     --certificate=phoenix_arxiv_org_cert.cer \
     --private-key=phoenix.arxiv.org.key \
     --global

# reserve an IP address
gcloud compute addresses create lb-ipv4-accounts \
       --project=$PROJ \
       --ip-version=IPV4 \
       --global


#################### Phoenix load balancer ####################
LB_ADDRESS=lb-ipv4-accounts

# This becomes the name of the load balancer in the GCP UI
gcloud compute url-maps create ${LOAD_BALANCER_BASE}-https \
       --project=$PROJ \
       --default-service browse-backend \
       --global

# Create a target HTTP(S) proxy to route requests to your URL map.
# The proxy is the portion of the load balancer that holds the SSL
# certificate.
gcloud compute target-https-proxies create target-https-proxy \
       --project=$PROJ \
       --ssl-certificates=phoenix-arxiv-org-cert \
       --url-map=${LOAD_BALANCER_BASE}-https \
       --global


# Create the frontend of the LB
# Create a global forwarding rule to route incoming requests to the proxy.
gcloud compute forwarding-rules create ${LOAD_BALANCER_BASE}-https-forwarding-rule \
       --project=$PROJ \
       --address=$LB_ADDRESS \
       --target-https-proxy=target-https-proxy \
       --ports=443 \
       --global

# If the load balancer doesn't work after about 60 sec.
# to to the GCP UI, go to load balancer, go to the load balancer that
# this script creates, click edit, click finalize and then save (or update)
# Even without changing anything this seems to kick the LB into working sometimes.

# HTTPS load balancers will also need an accompanying HTTP load balancer that
# configured to redirect all requests to the HTTPS load balancer.
# It does not need a backend to be defined; the .yaml configuration is used
# here so that the load balancer (url-map) can be created without a backend.

gcloud compute url-maps import ${LOAD_BALANCER_BASE}-http \
       --project=$PROJ \
       --source ./${LOAD_BALANCER_BASE}-http.yaml \
       --global

gcloud compute target-http-proxies create target-http-proxy \
       --project=$PROJ \
       --url-map=${LOAD_BALANCER_BASE}-http \
       --global

gcloud compute forwarding-rules create ${LOAD_BALANCER_BASE}-http-content-rule \
       --project=$PROJ \
       --address=$LB_ADDRESS \
       --target-http-proxy=target-http-proxy \
       --ports=80 \
       --global
