"""
webnode_pdf_request.py is an app that gets the published arxiv ID from the pub/sub queue on GCP,
and compile the submissions TeX with webnode to generate PDF.

This is done using the function ensure_pdf() from sync_published_to_gcp.

The request (pub/sub entry) is subsumed when the pdf exists, so this is a pretty safe operation.
"""
import argparse
import shlex
import signal
import subprocess
import threading
import typing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import gmtime, sleep

import json
import os
import logging.handlers
import logging
import gzip
import tarfile

import requests
from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1 import SubscriberClient

from identifier import Identifier
from sync_published_to_gcp import (
    ArxivSyncJsonFormatter, CONCURRENCY_PER_WEBNODE, ensure_pdf, FTP_PREFIX)

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
        if not hasattr(self._local, 'session'):
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
        """Pub/sub event handler to upload the submission tarball and .abs files to GCP.
        Note that, this is running in a thread driven by the gcp pub/sub client.
        """
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
        arxiv_id_str = f'{paper_id}v{version}' if version else paper_id
        src_ext: typing.Union[str, None] = data.get('src_ext')
        if src_ext and len(src_ext) > 0 and src_ext[0] != ".":
            src_ext = "." + src_ext
        log_extra["arxiv_id"] = arxiv_id_str
        log_extra["src_ext"] = str(src_ext)

        # If the message is totally bogus, nothing I can do. Error it out
        if not paper_id:
            logger.error(f"bad data {str(message.message_id)}", extra=log_extra)
            message.nack()
            return

        # PDF / HTML submissions - move on
        if src_ext in [".pdf", ".html.gz"]:
            logger.info("ack message - not a TeX submission: %s ext %s",
                        arxiv_id_str, str(src_ext), extra=log_extra)
            message.ack()
            return

        arxiv_id = Identifier(arxiv_id_str)
        archive = ('arxiv' if not arxiv_id.is_old_id else arxiv_id.archive)
        pdf_source = Path(f"{FTP_PREFIX}/{archive}/papers/{arxiv_id.yymm}/{arxiv_id.filename}.pdf")
        # PDF submissions - move on
        if pdf_source.exists():
            logger.info("ack message - PDF submission: %s ext %s",
                        arxiv_id_str, str(src_ext), extra=log_extra)
            message.ack()
            return

        # Ignored submission
        gz_source = Path(f"{FTP_PREFIX}/{archive}/papers/{arxiv_id.yymm}/{arxiv_id.filename}.gz")
        if gz_source.exists():
            # Open the gzip file in read mode with text encoding set to ASCII
            try:
                with gzip.open(gz_source, 'rt', encoding='ascii') as f:
                    content = f.read()
                    if content.startswith("%auto-ignore"):
                        logger.info("ack message - auto-ignore: %s ext %s",
                              arxiv_id_str, str(src_ext), extra=log_extra)
                        message.ack()
                        return
            except Exception as _exc:
                logger.warning("bad .gz: %s ext %s",
                            arxiv_id_str, str(src_ext), extra=log_extra,
                               exc_info=True, stack_info=False)

        # Removed submission
        tgz_source = Path(f"{FTP_PREFIX}/{archive}/papers/{arxiv_id.yymm}/{arxiv_id.filename}.tar.gz")
        if tgz_source.exists():
            try:
                with tarfile.open(tgz_source, 'r:gz') as submission:
                    toplevels = submission.getnames()
                    if "removed.txt" in toplevels:
                        logger.info("ack message - removed submission: %s ext %s",
                              arxiv_id_str, str(src_ext), extra=log_extra)
                        message.ack()
                        return
            except Exception as _exc:
                logger.warning("bad tgz: %s", arxiv_id.ids, extra=log_extra,
                               exc_info=True, stack_info=False)

        host, n_para = CONCURRENCY_PER_WEBNODE[min(len(CONCURRENCY_PER_WEBNODE)-1, max(0, my_tag))]
        log_extra['web_node'] = host
        try:
            pdf_file, url, _1, duration_ms = ensure_pdf(thread_data.session, host, arxiv_id, timeout=30)
            if pdf_file.exists():
                logger.info("ack message - pdf file exists: %s", arxiv_id.ids, extra=log_extra)
                message.ack()
                return
        except Exception as _exc:
            logger.warning("ensure_pdf: %s", arxiv_id.ids, extra=log_extra,
                           exc_info=True, stack_info=False)
            pass

        t_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        t_pub = message.publish_time.replace(tzinfo=timezone.utc)
        message_age: timedelta = t_now - t_pub
        compilation_timeout = int(os.environ.get("TEX_COMPILATION_TIMEOUT_MINUTES", "30"))
        if message_age > timedelta(minutes=compilation_timeout):
            try:
                slacking = subprocess.call(['/users/e-prints/bin/tex-compilation-problem-notification',
                                            arxiv_id.ids], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if slacking.returncode != 0:
                    logger.error("Failed to send notification: %s", arxiv_id.ids, extra=log_extra)
            except:
                logger.error('Slacking for %s did not work', arxiv_id.ids)
                pass
 
            log_extra['age'] = str(message_age)
            help_needed = os.environ.get("TEX_COMPILATION_RECIPIENT", "help@arxiv.org")
            subject = f"TeX compilation for {paper_id}v{version} failed"
            mail_body = f"Hello EUST,\nTex compilation for {paper_id}v{version} has failed. Please resolve the issue.\n\nThis message is generated by a bot on arxiv-sync.serverfarm.cornell.edu.\n"
            if os.environ.get("DRAIN_WEBNODE_REQUEST_QUEUE") == "TRUE":
                # equivalent of /dev/null
                cmd = ["echo", subject]
            else:
                # I cannot comeup with anything useful
                cmd = ["/usr/bin/mail", "-r", "e-prints@arxiv.org", "-s", subject, help_needed]
            mail = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                mail.communicate(mail_body, timeout=60)
                if mail.returncode == 0:
                    logger.warning(f"Alart mail sent: {subject}", extra=log_extra)
                    message.ack()
                    return
                else:
                    logger.error("Failed to send mail: %s", shlex.join(cmd), extra=log_extra)
            except Exception as exc:
                logger.error(f"Failed: %s", shlex.join(cmd), extra=log_extra, exc_info=True)
                pass
            pass

        logger.warning("nack message: %s", arxiv_id.ids, extra=log_extra)
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
    ad.add_argument('--debug', help='Set logging to debug.',
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
