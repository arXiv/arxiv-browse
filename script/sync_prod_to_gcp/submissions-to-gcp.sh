#!/usr/bin/bash

JSON_LOG_DIR=/opt_arxiv/e-prints/logs/sync
mkdir -p $JSON_LOG_DIR

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"
if [ ! -d sync.venv ] ; then
  make
fi

# useful debugging
# S2G_DEBUG_FLAGS=--debug --test

. sync.venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=~/arxiv-production-cred.json
export TEX_COMPILATION_FAILURE_FIRST_NOTIFICATION_TIME=180
export TEX_COMPILATION_TIMEOUT_MINUTES=1020
python submissions_to_gcp.py $S2G_DEBUG_FLAGS --json-log-dir $JSON_LOG_DIR
deactivate
