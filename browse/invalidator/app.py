"""Flask app to purge cache at fastly.

 To be run as cloud run listening to changes on gs bucket.

See "Route Cloud Storage events to Cloud Run" at
 https://cloud.google.com/eventarc/docs/run/route-trigger-cloud-storage


To run:
    cd arxiv-browse  # run from root of project
    GOOGLE_APPLICATION_CREDENTIALS ~/.config/google-app-credentials.json \
    FASTLY_PURGE_TOKEN=$(gcloud secrets versions access 1 --secret="fastly_crowdsec_token") \
    flask --app browse.invalidator.app run --debug --reload
"""
import json
import os

from typing import Dict, Optional
from google.api_core import retry

from arxiv.identifier import Identifier

import requests
from flask import Flask, Response, request

# import logging as log
# import google.cloud.logging as logging
# logging_client = logging.Client()
# logging_client.setup_logging()
import google.auth

from invalidator import _paperid, _purge_urls

# credentials, project_id = google.auth.default()
# if hasattr(credentials, "service_account_email"):
#     print(f"Running as {credentials.service_account_email}")
# else:
#     print("WARNING: no service account credential. User account credential?")


PROJECT = os.environ.get('arxiv-production')
USE_SOFT_PURGE = os.environ.get('USE_SOFT_PURGE', "0") == "1"
FASTLY_URL = os.environ.get("FASTLY_URL", "https://api.fastly.com")
ORIGIN_HOSTNAME = os.environ.get("ORIGIN_HOSTNAME", "arxiv.org")

FASTLY_PURGE_TOKEN = os.environ.get("FASTLY_PURGE_TOKEN")
"API token to purge at Fastly."



def _log(severity: str, msg: str, paperid: Optional[Identifier] = None) -> None:
    # https://cloud.google.com/run/docs/samples/cloudrun-manual-logging
    log_fields = {"severity": severity, "message": msg}
    if paperid is not None:
        log_fields["arxivPaperId"] = paperid.idv

    request_is_defined = "request" in globals() or "request" in locals()
    if request_is_defined and request:
        # For special fields see https://cloud.google.com/logging/docs/agent/logging/configuration#special-fields
        trace_header = request.headers.get("X-Cloud-Trace-Context")
        if trace_header and PROJECT:
            trace = trace_header.split("/")
            log_fields["logging.googleapis.com/trace"] = f"projects/{PROJECT}/traces/{trace[0]}"

    print(json.dumps(log_fields))

app = Flask(__name__)


def _invalidate_at_fastly(bucket: str, name: str) -> None:
    paperid = _paperid(name)
    if paperid is None:
        _log("INFO", "No purge: gs://{bucket}/{name} not related to a paperid")
        return
    for url in _purge_urls(bucket, name, paperid):
        _invalidate(url, paperid)


@retry.Retry()
def _invalidate(arxiv_url: str, paperid: Identifier) -> None:
    headers = {"Fastly-Key": FASTLY_PURGE_TOKEN}
    if USE_SOFT_PURGE:
        headers["fastly-soft-purge"] = "1"
    resp = requests.get(f"{FASTLY_URL}/{arxiv_url}", headers=headers)
    if resp.status_code != 200:
        _log("ERROR", f"Could not purge {arxiv_url}: {resp.status_code} {resp.text}", paperid)
    else:
        _log("INFO", f"Purged {arxiv_url}", paperid)


@app.route("/", methods=["POST"])
def invalidate_on_bucket_change() -> Response:
    """
    Takes in the eventarc trigger payload invalidates any related papers.

    Format of incoming data:
    https://github.com/googleapis/google-cloudevents/blob/main/proto/google/events/cloud/storage/v1/data.proto

    Returns
    -------
    Response
        Returns a 200 response with no payload
    """
    data: Dict[str, str] = request.get_json()
    name = str(data.get("name"))
    bucket = str(data.get("bucket"))
    _invalidate_at_fastly(bucket, name)
    return Response('', 200)


fastly = requests.get(f"{FASTLY_URL}/current_customer", headers={"Fastly-Key": FASTLY_PURGE_TOKEN})
if fastly.status_code != 200:
    raise RuntimeError(f"Could not access fastly: {fastly.status_code} {fastly.text}")

