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



#################### Load Balancer ####################

gcloud compute ssl-certificates  create phoenix-arxiv-org-cert \
     --project=arxiv-phoenix \
     --certificate=phoenix_arxiv_org_cert.cer \
     --private-key=phoenix.arxiv.org.key \
     --global

# reserve an IP address
gcloud compute addresses create lb-ipv4-accounts \
       --project=$PROJ \
       --ip-version=IPV4 \
       --global
       

#################### Phoenix load balancer ####################

# This becomes the name of the load balancer in the GCP UI
gcloud compute url-maps create phoenix-lb \
       --project=$PROJ \
       --default-service browse-backend \
       --global

# Create a target HTTP(S) proxy to route requests to your URL map.
# The proxy is the portion of the load balancer that holds the SSL
# certificate.
gcloud compute target-https-proxies create target-https-proxy \
       --project=$PROJ \
       --ssl-certificates=phoenix-arxiv-org-cert \
       --url-map=phoenix-lb \
       --global


# Create the frontend of the LB
# Create a global forwarding rule to route incoming requests to the proxy.
gcloud compute forwarding-rules create phoenix-lb-forwarding-rule \
       --project=$PROJ \
       --address=lb-ipv4-accounts \
       --target-https-proxy=target-https-proxy \
       --ports=443 \
       --global

# If the load balancer doesn't work after about 60 sec.
# to to the GCP UI, go to load balancer, go to the load balancer that
# this script creates, click edit, click finalize and then save (or update)
# Even without changing anything this seems to kick the LB into working sometimes.


