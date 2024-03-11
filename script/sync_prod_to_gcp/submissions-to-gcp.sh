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
python subscribe_submissions.py $S2G_DEBUG_FLAGS --json-log-dir $JSON_LOG_DIR
deactivate
