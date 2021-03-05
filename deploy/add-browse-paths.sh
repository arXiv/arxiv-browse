set -v 
#################### browse paths ####################
# https://cloud.google.com/load-balancing/docs/url-map
#
# setupLB.sh should be run before this command
######################################################

. config.sh

BACKEND=browse-backend
MAPPINGS=$(BROWSE_SERVER_NAME=$SERVER_NAME  python -c 'import browse.pathmap' $BACKEND)
gcloud compute url-maps add-path-matcher $LOAD_BALANCER \
       --path-matcher-name=browse-paths \
       --default-service=$BACKEND \
       --delete-orphaned-path-matcher \
       --existing-host=$SERVER_NAME \
       --path-rules=$MAPPINGS

