#!/usr/bin/bash
# Runs subscribe_submissions.py for arxiv-development.
# You'd need a service account that can ues both the pub/sub and bucket I/O.
. sync.venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=~/sync-test.json
python subscribe_submissions.py --project=arxiv-development --debug --bucket=arxiv-sync-test-01 --json-log-dir /users/nt385/temp --topic=submission-publish 
deactivate
