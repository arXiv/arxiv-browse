import json
import os
import time
from typing import Dict, Tuple, List, Optional
from google.api_core import retry

from arxiv.identifier import OLD_STYLE, STANDARD, Identifier

import requests
from flask import Flask, Response, request
from google.cloud import secretmanager

PROJECT = os.environ.get('PROJECT')
USE_SOFT_PURGE = os.environ.get('USE_SOFT_PURGE', "0") == "1"
FASTLY_URL = os.environ.get("FASTLY_URL", "https://api.fastly.com")
ORIGIN_HOSTNAME = os.environ.get("ORIGIN_HOSTNAME", "arxiv.org")

FASTLY_API_KEY_SECRET_NAME = os.environ.get("FASTLY_API_KEY_SECRET_NAME", "fastly-api-key")
"Actual secret is in GCP Secret Manager, see `_fastly_secrets()`."

RELOAD_SECRET_SEC = int(os.environ.get("RELOAD_SECRET_SEC", 60 * 15))

_API_KEY = ""
_API_KEY_TIME: float = time.time()

app = Flask(__name__)

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


def _fastly_secrets() -> str:
    # get from secret manager
    global _API_KEY, _API_KEY_TIME
    if not _API_KEY or time.time() - _API_KEY_TIME > RELOAD_SECRET_SEC:
        sm = secretmanager.SecretManagerServiceClient()
        sec = sm.access_secret_version(request={"name": FASTLY_API_KEY_SECRET_NAME})
        _API_KEY = sec.payload.data.decode("UTF-8")
        _API_KEY_TIME = time.time()

    return _API_KEY


def _paperid(name: str) -> Optional[Identifier]:
    if match := STANDARD.search(name):
        return Identifier(match.group("arxiv_id"))
    if match := OLD_STYLE.search(name):
        return Identifier(match.group("arxiv_id"))
    else:
        return None


def _purge_urls(bucket: str, name: str, paperid: Identifier) -> List[str]:
    # Since it is not clear if this is the current file or an older one
    # invalidate both the versioned URL and the un-versioned current URL
    if '/pdf/' in name:
        return [f"arxiv.org/pdf/{paperid.idv}", f"arxiv.org/pdf/{paperid.id}"]
    if '/ftp/' in name or '/orig/' in name:
        if name.endswith(".abs"):
            return [f"arxiv.org/abs/{paperid.idv}", f"arxiv.org/abs/{paperid.id}"]
        else:
            return [f"arxiv.org/e-print/{paperid.idv}", f"arxiv.org/e-print/{paperid.id}",
                    f"arxiv.org/src/{paperid.idv}", f"arxiv.org/src/{paperid.id}"]
    if '/html/' in name:
        # Note this does not invalidate any paths inside the html.tgz
        return [f"arxiv.org/html/{paperid.idv}", f"arxiv.org/html/{paperid.id}",
                # Note needs both with and without trailing slash
                f"arxiv.org/html/{paperid.idv}/", f"arxiv.org/html/{paperid.id}/"]
    if '/ps/' in name:
        return [f"arxiv.org/ps/{paperid.idv}", f"arxiv.org/ps/{paperid.id}"]
    if '/docx/' in name:
        return [f"arxiv.org/docx/{paperid.idv}", f"arxiv.org/docx/{paperid.id}"]

    _log("INFO", f"No purge found gs://{bucket}/{name}", paperid)
    return []


def _invalidate_at_fastly(bucket: str, name: str) -> None:
    paperid = _paperid(name)
    if paperid is None:
        _log("INFO", "No purge: gs://{bucket}/{name} not related to a paperid")
        return
    for url in _purge_urls(bucket, name, paperid):
        _invalidate(url, paperid)


@retry.Retry()
def _invalidate(arxiv_url: str, paperid: Identifier) -> None:
    apikey = _fastly_secrets()
    headers = {"Fastly-Key": apikey}
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
