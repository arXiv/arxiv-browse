import argparse
import sys
import typing
from time import gmtime

from google.cloud import pubsub_v1, storage
import json
import os
import logging.handlers
import logging

from google.cloud.pubsub_v1.subscriber.message import Message

from identifier import Identifier
from .sync_published_to_gcp import ORIG_PREFIX, FTP_PREFIX, upload, ArxivSyncJsonFormatter, \
    path_to_bucket_key

logging.basicConfig(level=logging.WARNING, format='%(message)s (%(threadName)s)')
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

    paper_id = data.get('paper_id')
    version = data.get('version')
    xid = Identifier(f"{paper_id}v{version}" if version else paper_id)
    archive = ('arxiv' if not xid.is_old_id else xid.archive)
    logger.info("Processing %s", xid.ids)

    # Process the message
    if xid.has_version:
        tex_path = f"{ORIG_PREFIX}/{archive}/papers/{xid.yymm}/{xid.filename}.tar.gz"
    else:
        tex_path = f"{FTP_PREFIX}/{archive}/papers/{xid.yymm}/{xid.filename}.tar.gz"
    tex_key = path_to_bucket_key(tex_path)

    abs_path = f"{FTP_PREFIX}/{archive}/papers/{xid.yymm}/{xid.filename}.abs"
    abs_key = path_to_bucket_key(abs_path)
    return (xid.ids, [(abs_path, abs_key), (tex_path, tex_key)])


def submission_callback(message: Message) -> None:
    global gs_client
    arxiv_id_str, payloads = submission_message_to_payloads(message)
    if not arxiv_id_str:
        logger.error(f"bad data {str(message.message_id)}")
        message.nack()
        return
    xid = Identifier(arxiv_id_str)
    logger.info("Processing %s", arxiv_id_str)

    try:
        for local, remote in payloads:
            logger.debug("uploading: %s -> %s", local, remote)
            upload(gs_client, local, remote)

        # Acknowledge the message so it is not re-sent
        logger.info("ack message: %s", xid.ids)
        message.ack()

    except Exception as exc:
        logger.error("Error processing message: {exc}", exc_info=True)
        message.nack()


def test_callback(message: Message) -> None:
    arxiv_id_str, payloads = submission_message_to_payloads(message)
    print(arxiv_id_str)
    for payload in payloads:
        print("%s -> %s", payload[0], payload[1])
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
            streaming_pull_future.cancel()


if __name__ == "__main__":
    ad = argparse.ArgumentParser(epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ad.add_argument('--project', help='', dest="project", default="arxiv-production")
    ad.add_argument('--topic', help='', dest="topic", default="submission-published")
    ad.add_argument('--subscription', help='test mode', dest="subscription",
                    default="sync-submission-from-cit-to-gcp")
    ad.add_argument('--json-log-dir', help='Additional JSON logging',
                    default='/var/log/e-prints')
    ad.add_argument('--debug', help='Set logging to debug', action='store_true')
    ad.add_argument('--test', help='Test reading the queue', action='store_true')
    ad.add_argument('--globals', help="Global variables")
    args = ad.parse_args()

    project_id = args.project
    subscription_id = "your-subscription-id"

    if args.json_log_dir and os.path.exists(args.json_log_dir):
        json_logHandler = logging.handlers.RotatingFileHandler(os.path.join(args.json_log_dir, "submissions.log"),
                                                               maxBytes=4 * 1024 * 1024,
                                                               backupCount=10)
        json_formatter = ArxivSyncJsonFormatter(**LOG_FORMAT_KWARGS)
        json_formatter.converter = gmtime
        json_logHandler.setFormatter(json_formatter)
        json_logHandler.setLevel(logging.DEBUG if args.v or args.debug else logging.INFO)
        logger.addHandler(json_logHandler)
        pass

    # Ensure the environment is authenticated
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        print("Environment variable 'GOOGLE_APPLICATION_CREDENTIALS' is not set.")
        sys.exit(1)

    submission_pull_messages(project_id, subscription_id, test=args.test)
