#!/usr/bin/bash

JSON_LOG_DIR=/opt_arxiv/e-prints/logs/sync
mkdir -p $JSON_LOG_DIR

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"
if [ ! -d sync.venv ] ; then
  make
fi

. sync.venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=~/arxiv-production-cred.json
python webnode_pdf_requset.py --json-log-dir $JSON_LOG_DIR
deactivate
