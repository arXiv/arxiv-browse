"""
subscribe_submissions.py is an app that gets the published arxiv ID from the pub/sub queue on GCP,
check the files exist on CIT and uploads them to GCP bucket.

The "upload to GCP bucket" part is from existing sync_published_to_gcp.

As a matter of fact, this borrows the most of heavy lifting part from sync_published_to_gcp.py.
"""
import argparse
import sys
import typing
from time import gmtime
from pathlib import Path

import json
import os
import logging.handlers
import logging

from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud import pubsub_v1, storage

from identifier import Identifier
from sync_published_to_gcp import ORIG_PREFIX, FTP_PREFIX, upload, ArxivSyncJsonFormatter, \
    path_to_bucket_key

logging.basicConfig(level=logging.WARNING, format='(%(loglevel)s): (%(timestamp)s) %(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.WARNING)


LOG_FORMAT_KWARGS = {
    "fields": {
        "timestamp": "asctime",
        "level": "levelname",
    },
    "message_field_name": "message",
    # time.strftime has no %f code "datefmt": "%Y-%m-%dT%H:%M:%S.%fZ%z",
}

gs_client = storage.Client()

def submission_message_to_payloads(message: Message) -> typing.Tuple[str, typing.List[typing.Tuple[str, str]]]:
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
        logger.error(f"bad data {str(message.message_id)}")
        return ("",[])


    try:
        data = json.loads(json_str)
    except Exception as exc:
        logger.warning(f"bad({message.message_id}): {json_str[:1024]}")
        return ("",[])

    # /data/{ftp|orig}/{archive}/papers/{yymm}/{paper_id}{src_ext}
    paper_id = data.get('paper_id')
    version = data.get('version')
    src_ext = data.get('src_ext', ".tar.gz")

    xid = Identifier(f"{paper_id}v{version}" if version else paper_id)
    archive = ('arxiv' if not xid.is_old_id else xid.archive)
    logger.info("Processing %s", xid.ids)
    pairs = []

    if xid.has_version:
        src_path = f"{ORIG_PREFIX}{archive}/papers/{xid.yymm}/{xid.idv}{src_ext}"
        if os.path.exists(src_path):
            pairs.append((src_path, path_to_bucket_key(src_path)))
        abs_path = f"{ORIG_PREFIX}{archive}/papers/{xid.yymm}/{xid.idv}.abs"
        if os.path.exists(abs_path):
            pairs.append((abs_path, path_to_bucket_key(abs_path)))

    src_path = f"{FTP_PREFIX}{archive}/papers/{xid.yymm}/{xid.id}{src_ext}"
    if os.path.exists(src_path):
        pairs.append((src_path, path_to_bucket_key(src_path)))
    else:
        logger.error("Tex source does not exist: %s", src_path)
    abs_path = f"{FTP_PREFIX}{archive}/papers/{xid.yymm}/{xid.id}.abs"
    if os.path.exists(abs_path):
        pairs.append((abs_path, path_to_bucket_key(abs_path)))
    else:
        logger.error("abs does not exist: %s", abs_path)
    return (xid.ids, pairs)


def submission_callback(message: Message) -> None:
    """Pub/sub event handler to upload the submission tarball and .abs files to GCP."""
    global gs_client
    arxiv_id_str, payloads = submission_message_to_payloads(message)
    if not arxiv_id_str:
        logger.error(f"bad data {str(message.message_id)}")
        message.nack()
        return
    if not payloads:
        logger.warning(f"There is no associated files? xid: {arxiv_id_str}, mid: {str(message.message_id)}")
        message.nack()
        return
    xid = Identifier(arxiv_id_str)
    logger.info("Processing %s", arxiv_id_str)

    try:
        for local, remote in payloads:
            logger.debug("uploading: %s -> %s", local, remote)
            upload(gs_client, Path(local), remote)

        # Acknowledge the message so it is not re-sent
        logger.info("ack message: %s", xid.ids)
        message.ack()

    except Exception as exc:
        logger.error("Error processing message: {exc}", exc_info=True)
        message.nack()


def test_callback(message: Message) -> None:
    """Stand in callback to handle the pub/sub message. gets used for --test."""
    arxiv_id_str, payloads = submission_message_to_payloads(message)
    logger.debug(arxiv_id_str)
    for payload in payloads:
        logger.debug(f"{payload[0]} -> {payload[1]}")
    message.nack()
    sys.exit(0)


def submission_pull_messages(project_id: str, subscription_id: str, test: bool = False) -> None:
    """
    Create a subscriber client and pull messages from a Pub/Sub subscription.

    Args:
        project_id (str): Google Cloud project ID
        subscription_id (str): ID of the Pub/Sub subscription
        test (bool): Test - get one message, print it, nack, and exit
    """
    
    global gs_client
    gs_client = storage.Client()

    subscriber_client = pubsub_v1.SubscriberClient()
    subscription_path = subscriber_client.subscription_path(project_id, subscription_id)
    callback = test_callback if test else submission_callback
    streaming_pull_future = subscriber_client.subscribe(subscription_path, callback=callback)
    with subscriber_client:
        try:
            streaming_pull_future.result()
        except Exception as e:
            logger.error("Subscribe failed: %s", str(e), exc_info=True)
            streaming_pull_future.cancel()


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
