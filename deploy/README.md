# To initally deploy to GCP:

0. copy env_values.txt.example to env_values.txt and set all TODOs in there to the correct values.
00. gcloud config set project arxiv-phoenix
1. source config.sh
2. ./setupCompute.sh
3. ./setupLB.sh
4. cd .. ; ./deploy/add-browse-paths.sh
5. ./deploy/build-and-push.sh
6. ./deploy/update-instance-group.sh $(cat TAG.txt)

# To update instence groups on GCP:

0. gcloud config set project arxiv-phoenix
1. source ./deploy/config.sh
2. ./deploy/build-and-push.sh
3. ./deploy/update-instance-group.sh $(cat TAG.txt)
