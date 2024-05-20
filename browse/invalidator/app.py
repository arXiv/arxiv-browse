"""Flask app to listen to GS changes and purge cache at fastly.

 To be run as cloud run listening to changes on GS bucket.

See "Route Cloud Storage events to Cloud Run" at
 https://cloud.google.com/eventarc/docs/run/route-trigger-cloud-storage

To run:
    cd arxiv-browse  # run from root of project
    GOOGLE_APPLICATION_CREDENTIALS ~/.config/google-app-credentials.json \
    FASTLY_PURGE_TOKEN=$(gcloud secrets versions access 1 --secret="fastly_crowdsec_token") \
    flask --app browse.invalidator.app run --debug --reload &

    curl --data '{
    "kind": "storage#object",
    "id": "arxiv-production-data/txt/test/test.txt/1715976725972877",
    "selfLink": "https://www.googleapis.com/storage/v1/b/arxiv-production-data/o/txt%2Ftest%2Ftest.txt",
    "name": "txt/test/test.txt",
    "bucket": "arxiv-production-data",
    "generation": "1715976725972877",
    "metageneration": "1",
    "contentType": "text/plain",
    "timeCreated": "2024-05-17T20:12:06.024Z",
    "updated": "2024-05-17T20:12:06.024Z",
    "storageClass": "STANDARD",
    "timeStorageClassUpdated": "2024-05-17T20:12:06.024Z",
    "size": "56",
    "md5Hash": "xyz==",
    "contentLanguage": "en",
    "crc32c": "boLwHQ==",
    "etag": "xyz="
     }' \
    http://localhost:8080/

"""
import os

from typing import Dict, cast

import requests
from flask import Flask, Response, request, g, current_app

try:
    import google.cloud.logging
    client = google.cloud.logging.Client()
    client.setup_logging()
except EnvironmentError as ex:
    print(f"Could not import google-cloud-logging: {ex}")

import logging as log

from browse.invalidator import purge_urls, Invalidator


def invalidate_for_gs_change(bucket: str, key: str, invalidator: Invalidator) -> None:
    tup = purge_urls(key)
    if not tup:
        log.info(f"No purge: gs://{bucket}/{key} not related to an arxiv paper id")
        return
    paper_id, paths = tup
    if not paths:
        log.info(f"No purge: gs://{bucket}/{key} Related to {paper_id} but no paths")
        return
    for path in paths:
            try:
                invalidator.invalidate(path, paper_id)
            except Exception as exc:
                log.error(f"Purge failed: {path} failed {exc}")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["FASTLY_API_TOKEN"] = os.environ.get("FASTLY_API_TOKEN", "")

    app.config["FASTLY_URL"] = os.environ.get("FASTLY_URL", "https://api.fastly.com/purge")
    app.config["ALWAYS_SOFT_PURGE"] = os.environ.get('ALWAYS_SOFT_PURGE', "0") == "1"
    app.config["FASTLY_TEST_ON_STARTUP"] = os.environ.get("TEST_FASTLY_ON_STARTUP", "0") == "1"
    app.config["OPENTELEMETRY"] = os.environ.get("OPENTELEMETRY", "0") == "1"

    if app.config["FASTLY_TEST_ON_STARTUP"]:
        fastly = requests.get(f"{app.config['FASTLY_URL']}/current_customer",
                              headers={"Fastly-Key": app.config["FASTLY_PURGE_TOKEN"]})
        if fastly.status_code != 200:
            raise RuntimeError(f"Could not access fastly: {fastly.status_code} {fastly.text}")

    if app.config["OPENTELEMETRY"]:
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.propagate import set_global_textmap
        from opentelemetry.propagators.cloud_trace_propagator import (
            CloudTraceFormatPropagator,
        )
        set_global_textmap(CloudTraceFormatPropagator())
        FlaskInstrumentor().instrument_app(app)

    def get_invalidator() -> Invalidator:
        if not app.config["FASTLY_API_TOKEN"]:
            raise RuntimeError("FASTLY_API_TOKEN is not set")

        if "invalidator" not in g or not g.invalidator:
            g.invalidator = Invalidator(current_app.config['FASTLY_URL'],
                                        current_app.config['FASTLY_API_TOKEN'],
                                        current_app.config['ALWAYS_SOFT_PURGE'])
        return cast(Invalidator, g.invalidator)

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
        invalidate_for_gs_change(str(data.get("bucket")), str(data.get("name")), get_invalidator())
        return Response('', 200)

    return app
