"""
webnode_pdf_request.py is an app that gets the published arxiv ID from the pub/sub queue on GCP,
and compile the submissions TeX with webnode to generate PDF.

The request (pub/sub entry) is subsumed when the pdf exists, so this is a pretty safe operation.

"""
import argparse
import signal
import threading
import typing
from time import gmtime, sleep

import json
import os
import logging.handlers
import logging

import requests
from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1 import SubscriberClient

from identifier import Identifier
from sync_published_to_gcp import (
    ArxivSyncJsonFormatter, PS_CACHE_PREFIX, CONCURRENCY_PER_WEBNODE,
    ensure_pdf)

logging.basicConfig(level=logging.INFO, format='(%(loglevel)s): (%(timestamp)s) %(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


LOG_FORMAT_KWARGS = {
    "fields": {
        "timestamp": "asctime",
        "level": "levelname",
    },
    "message_field_name": "message",
    # time.strftime has no %f code "datefmt": "%Y-%m-%dT%H:%M:%S.%fZ%z",
}

MESSAGE_COUNT = 0  # Set this to negative to shutdown


def signal_handler(_signal: int, _frame: typing.Any):
    """Graceful shutdown request"""
    global MESSAGE_COUNT
    MESSAGE_COUNT = -99999 # Just a very negative int


# Attach the signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class ThreadedSession:
    def __init__(self):
        self._local = threading.local()

    @property
    def session(self):
        if not hasattr(self._local, 'storage'):
            # Initialize the Storage instance for the current thread
            self._local.session = requests.Session()
        return self._local.session

thread_data = ThreadedSession()

def subscribe_published(project_id: str, subscription_id: str, request_timeout: int) -> None:
    """
    Create a subscriber client and pull messages for published submission.

    Args:
        project_id (str): Google Cloud project ID
        subscription_id (str): ID of the Pub/Sub subscription
        request_timeout: request timeout
    """
    global MESSAGE_COUNT

    def ping_callback(message: Message) -> None:
        """Pub/sub event handler to upload the submission tarball and .abs files to GCP."""
        global MESSAGE_COUNT
        my_tag = MESSAGE_COUNT
        log_extra = {"service": "ping_webnode", "count": MESSAGE_COUNT}
        if my_tag < 0:
            logger.info("shutting down", extra=log_extra)
            message.nack()
            return
        MESSAGE_COUNT = (MESSAGE_COUNT + 1) % len(CONCURRENCY_PER_WEBNODE)

        try:
            json_str = message.data.decode('utf-8')
        except UnicodeDecodeError:
            logger.error(f"bad data {str(message.message_id)}", extra=log_extra)
            message.nack()
            return

        try:
            data = json.loads(json_str)
        except Exception as _exc:
            logger.warning(f"bad({message.message_id}): {json_str[:1024]}", extra=log_extra)
            return

        #publish_type = data.get('type') # cross | jref | new | rep | wdr
        paper_id = data.get('paper_id')
        version = data.get('version')

        if not paper_id:
            logger.error(f"bad data {str(message.message_id)}", extra=log_extra)
            message.nack()
            return
        arxiv_id_str = f'{paper_id}v{version}' if version else paper_id
        arxiv_id = Identifier(arxiv_id_str)
        log_extra["arxiv_id"] = arxiv_id_str

        host, n_para = CONCURRENCY_PER_WEBNODE[min(len(CONCURRENCY_PER_WEBNODE)-1, max(0, my_tag))]
        try:
            pdf_file, url, _1, duration_ms = ensure_pdf(thread_data.session, host, arxiv_id)
            logger.info("nack message - pdf file does not exist: %s",
                        arxiv_id.ids, extra=log_extra)
            if pdf_file.exists():
                logger.info("ack message - pdf file exists: %s", arxiv_id.ids, extra=log_extra)
                message.ack()
                return
        except Exception as _exc:
            logger.debug("ensure_pdf: %s", arxiv_id.ids, extra=log_extra,
                         exc_info=True, stack_info=False)
            pass
        logger.info("nack message - pdf file does not exist: %s", arxiv_id.ids, extra=log_extra)
        message.nack()
        return


    subscriber_client = SubscriberClient()
    subscription_path = subscriber_client.subscription_path(project_id, subscription_id)
    streaming_pull_future = subscriber_client.subscribe(subscription_path, callback=ping_callback)
    log_extra = {"app": "pubsub"}
    logger.info("Starting %s %s", project_id, subscription_id, extra=log_extra)
    with subscriber_client:
        try:
            while MESSAGE_COUNT >= 0:
                sleep(0.2)
            streaming_pull_future.cancel()  # Trigger the shutdown
            streaming_pull_future.result(timeout=30)  # Block until the shutdown is complete
        except TimeoutError:
            logger.info("Timeout")
            streaming_pull_future.cancel()
        except Exception as e:
            logger.error("Subscribe failed: %s", str(e), exc_info=True, extra=log_extra)
            streaming_pull_future.cancel()
    logger.info("Exiting", extra=log_extra)


if __name__ == "__main__":
    # projects/arxiv-production/subscriptions/webnode-pdf-compilation
    ad = argparse.ArgumentParser(epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ad.add_argument('--project',
                    help='GCP project name. Default is arxiv-production',
                    dest="project", default="arxiv-production")
    ad.add_argument('--topic',
                    help='GCP pub/sub name. The default matches with arxiv-production',
                    dest="topic", default="submission-published")
    ad.add_argument('--subscription',
                    help='Subscription name. Default is the one in production', dest="subscription",
                    default="webnode-pdf-compilation")
    ad.add_argument('--json-log-dir',
                    help='JSON logging directory. The default is correct on the sync-node',
                    default='/var/log/e-prints')
    ad.add_argument('--timeout', help='Web node request timeout',
                    default=10, type=int)
    ad.add_argument('--debug', help='Set logging to debug. Does not invoke testing',
                    action='store_true')
    ad.add_argument('--test', help='Test reading the queue but not do anything',
                    action='store_true')
    args = ad.parse_args()

    project_id = args.project
    subscription_id = args.subscription

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.json_log_dir and os.path.exists(args.json_log_dir):
        json_logHandler = logging.handlers.RotatingFileHandler(os.path.join(args.json_log_dir, "webnode-pdf.log"),
                                                               maxBytes=4 * 1024 * 1024,
                                                               backupCount=10)
        json_formatter = ArxivSyncJsonFormatter(**LOG_FORMAT_KWARGS)
        json_formatter.converter = gmtime
        json_logHandler.setFormatter(json_formatter)
        json_logHandler.setLevel(logging.DEBUG if args.debug else logging.INFO)
        logger.addHandler(json_logHandler)

    subscribe_published(project_id, subscription_id, args.timeout)
