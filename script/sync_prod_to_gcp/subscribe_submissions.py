"""
subscribe_submissions.py is an app that gets the published arxiv ID from the pub/sub queue on GCP,
check the files exist on CIT and uploads them to GCP bucket.

The "upload to GCP bucket" part is from existing sync_published_to_gcp.

As a matter of fact, this borrows the most of heavy lifting part from sync_published_to_gcp.py.

The published submission queue provides the submission source file extension which is used to
upload the legacy system submissions to the GCP bucket.
"""
import argparse
import signal
import sys
import typing
from time import gmtime, sleep
from pathlib import Path

import json
import os
import logging.handlers
import logging
import threading

from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1 import SubscriberClient
from google.cloud.storage import Client as StorageClient

from identifier import Identifier
from sync_published_to_gcp import ORIG_PREFIX, FTP_PREFIX, upload, ArxivSyncJsonFormatter, \
    path_to_bucket_key

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


def submission_message_to_payloads(message: Message, log_extra: dict) -> typing.Tuple[str, typing.List[typing.Tuple[str, str]]]:
    """
    Parse the submission_published message, map it to CIT files and returns the list of
    files to upload to GCP bucket.
    The schema is
    https://console.cloud.google.com/cloudpubsub/schema/detail/submission-publication?project=arxiv-production
    however, this only cares paper_id and version.

    Since upload() looks at the size of bucket object / CIT file to decide copy or not
    copy, this will attempt to upload the versioned and latest at the same time but the uploading
    may or may not happen.
    """
    try:
        json_str = message.data.decode('utf-8')
    except UnicodeDecodeError:
        logger.error(f"bad data {str(message.message_id)}", extra=log_extra)
        return ("", [])

    try:
        data = json.loads(json_str)
    except Exception as _exc:
        logger.warning(f"bad({message.message_id}): {json_str[:1024]}", extra=log_extra)
        return ("", [])

    publish_type = data.get('type') # cross | jref | new | rep | wdr
    paper_id = data.get('paper_id')
    version = data.get('version')
    log_extra["arxiv_id"] = paper_id

    # The source may not have a consistent .tar.gz name.
    # Some other possibilities:
    #
    # {paperidv}.pdf pdf only submission
    # {paperidv}.gz single file submisison
    # {paperidv}.html.gz html source submission
    #
    # NOTE: This cannot handle this special case.
    # I think there is one case in the system where there is a submission with two source files
    # that the admins manually crafted. It would have: {paperidv}.pdf and {paperidv}.tar.gz
    # This was to get a pdf only submission with ancillary files.

    # Now, the submission file extension is provided in the message
    src_ext = data.get('src_ext')
    # Not sure I have to do this but better safe than sorry
    src_ext = src_ext.strip() if src_ext else None
    if src_ext:
        submission_exts = [src_ext.strip(), ".abs"]
    else:
        src_ext = None
        # cast a wider net for older queue element
        submission_exts = [".pdf", ".gz", ".html.gz", ".tar.gz", ".abs"]

    xid_latest = Identifier(f"{paper_id}")
    logger.info("Processing %s.v%s:%s", xid_latest.ids, str(version), str(src_ext), extra=log_extra)
    archive = ('arxiv' if not xid_latest.is_old_id else xid_latest.archive)
    pairs = []

    latest_dir = f"{FTP_PREFIX}{archive}/papers/{xid_latest.yymm}"
    for dotext in submission_exts:
        src_path = f"{latest_dir}/{xid_latest.id}{dotext}"
        if os.path.exists(src_path):
            pairs.append((src_path, path_to_bucket_key(src_path)))
        else:
            if src_ext is not None:
                logger.error("Source does not exist: %s", src_path, extra=log_extra)

    # if it is new/cross/jref just /data/ftp/arxiv/papers/{YYMM}/{paperidv}.* needs to be synced.
    # If it is a replacement or wdr additionally /data/orig/arxiv/papers/{YYMM}/{paperid}{version-1}.* needs to be synced.
    if publish_type in ["rep", "wdr"]:
        prev_version = 1
        try:
            prev_version = max(1, int(version) - 1)
        except:
            pass
        versioned_parent = f"{ORIG_PREFIX}{archive}/papers/{xid_latest.yymm}"
        for dotext in submission_exts:
            src_path = f"{versioned_parent}/{xid_latest.id}v{prev_version}{dotext}"
            if os.path.exists(src_path):
                pairs.append((src_path, path_to_bucket_key(src_path)))

    return (xid_latest.ids, pairs)


class ThreadLocalData:
    def __init__(self):
        self._local = threading.local()

    @property
    def storage(self):
        if not hasattr(self._local, 'storage'):
            # Initialize the Storage instance for the current thread
            self._local.storage = StorageClient()
        return self._local.storage

mydata = ThreadLocalData()

def submission_callback(message: Message) -> None:
    """Pub/sub event handler to upload the submission tarball and .abs files to GCP."""
    # Create a thread-local object
    gs_client = mydata.storage
    log_extra = {"message_id": str(message.message_id), "app": "pubsub"}
    arxiv_id_str, payloads = submission_message_to_payloads(message, log_extra)
    if not arxiv_id_str:
        logger.error(f"bad data {str(message.message_id)}", extra=log_extra)
        message.nack()
        return
    if not payloads:
        logger.warning(f"There is no associated files? xid: {arxiv_id_str}, mid: {str(message.message_id)}", extra=log_extra)
        message.nack()
        return
    xid = Identifier(arxiv_id_str)
    log_extra["arxiv_id"] = arxiv_id_str
    logger.info("Processing %s", arxiv_id_str, extra=log_extra)

    try:
        for local, remote in payloads:
            logger.debug("uploading: %s -> %s", local, remote, extra=log_extra)
            upload(gs_client, Path(local), remote)

        # Acknowledge the message so it is not re-sent
        logger.info("ack message: %s", xid.ids, extra=log_extra)
        message.ack()

    except Exception as exc:
        logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)
        message.nack()


def test_callback(message: Message) -> None:
    """Stand in callback to handle the pub/sub message. gets used for --test."""
    log_extra = {"message_id": str(message.message_id), "app": "pubsub-test"}
    arxiv_id_str, payloads = submission_message_to_payloads(message, log_extra)
    logger.debug(arxiv_id_str)
    for payload in payloads:
        logger.debug(f"{payload[0]} -> {payload[1]}")
    message.nack()
    sys.exit(0)


running = True

def signal_handler(_signal: int, _frame: typing.Any):
    """Graceful shutdown request"""
    global running
    running = False

# Attach the signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def submission_pull_messages(project_id: str, subscription_id: str, test: bool = False) -> None:
    """
    Create a subscriber client and pull messages from a Pub/Sub subscription.

    Args:
        project_id (str): Google Cloud project ID
        subscription_id (str): ID of the Pub/Sub subscription
        test (bool): Test - get one message, print it, nack, and exit
    """
    subscriber_client = SubscriberClient()
    subscription_path = subscriber_client.subscription_path(project_id, subscription_id)
    callback = test_callback if test else submission_callback
    streaming_pull_future = subscriber_client.subscribe(subscription_path, callback=callback)
    log_extra = {"app": "pubsub"}
    logger.info("Starting %s %s", project_id, subscription_id, extra=log_extra)
    with subscriber_client:
        try:
            while running:
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
    ad = argparse.ArgumentParser(epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ad.add_argument('--project',
                    help='GCP project name. Default is arxiv-production',
                    dest="project", default="arxiv-production")
    ad.add_argument('--topic',
                    help='GCP pub/sub name. The default matches with arxiv-production',
                    dest="topic", default="submission-published")
    ad.add_argument('--subscription',
                    help='Subscription name. Default is the one in production', dest="subscription",
                    default="sync-submission-from-cit-to-gcp")
    ad.add_argument('--json-log-dir',
                    help='JSON logging directory. The default is correct on the sync-node',
                    default='/var/log/e-prints')
    ad.add_argument('--debug', help='Set logging to debug. Does not invoke testing',
                    action='store_true')
    ad.add_argument('--test', help='Test reading the queue but not do anything',
                    action='store_true')
    ad.add_argument('--bucket',
                    help='The bucket name. The default is mentioned in sync_published_to_gcp so for the production, you do not need to provide this - IOW it automatically uses the same buchet as sync-to-gcp',
                    dest="bucket", default="")
    args = ad.parse_args()

    project_id = args.project
    subscription_id = args.subscription

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.json_log_dir and os.path.exists(args.json_log_dir):
        json_logHandler = logging.handlers.RotatingFileHandler(os.path.join(args.json_log_dir, "submissions.log"),
                                                               maxBytes=4 * 1024 * 1024,
                                                               backupCount=10)
        json_formatter = ArxivSyncJsonFormatter(**LOG_FORMAT_KWARGS)
        json_formatter.converter = gmtime
        json_logHandler.setFormatter(json_formatter)
        json_logHandler.setLevel(logging.DEBUG if args.debug else logging.INFO)
        logger.addHandler(json_logHandler)
        pass

    # Ensure the environment is authenticated
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        logger.error("Environment variable 'GOOGLE_APPLICATION_CREDENTIALS' is not set.")
        sys.exit(1)
    if args.bucket:
        import sync_published_to_gcp
        sync_published_to_gcp.GS_BUCKET = args.bucket

    from sync_published_to_gcp import GS_BUCKET
    logger.info("GCP bucket %s", GS_BUCKET)
    submission_pull_messages(project_id, subscription_id, test=args.test)
