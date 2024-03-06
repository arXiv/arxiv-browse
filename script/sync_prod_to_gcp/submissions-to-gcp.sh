#!/bin/bash

TEXT_LOG_DIR=/opt_arxiv/e-prints/dissemination/sync_prod_to_gcp
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"
if [ ! -d sync.venv ] ; then
  make
fi

. sync.venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=~/arxiv-production-cred.json
python subscribe_submissions.py $TESTING_ARGS $SYNC_EXTRA -v --json-log-dir $JSON_LOG_DIR  >> $TEXT_LOG_DIR/sync_published_$DATE.report 2>> $TEXT_LOG_DIR/sync_published_$DATE.err
deactivate
