#!/usr/bin/bash

JSON_LOG_DIR=/opt_arxiv/e-prints/logs/sync
mkdir -p $JSON_LOG_DIR

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"
if [ ! -d sync.venv ] ; then
  make
fi

. sync.venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=~/sync-test.json
python subscribe_submissions.py --project=arxiv-development --debug --bucket=arxiv-sync-test-01 --json-log-dir /users/nt385/temp --topic=submission-publish 
deactivate
