To deploy to GCP:

0. copy env_values.txt.example to env_values.txt and set all TODOs in there to the correct values.
1. source config.sh
2. ./setupCompute.sh
3. ./setupLB.sh
4. cd .. ; deploy/add-browse-paths.sh
