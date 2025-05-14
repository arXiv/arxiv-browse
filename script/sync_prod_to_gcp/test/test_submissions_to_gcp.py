import datetime
import json
import logging
import os
import time
import unittest
from datetime import timezone

import sync_published_to_gcp

sync_published_to_gcp.GS_BUCKET = "arxiv-sync-test-01"
# Adjust to local testing
test_dir = os.path.dirname(os.path.abspath(__file__))
sync_published_to_gcp.CACHE_PREFIX = os.path.join(test_dir, 'cache', '')
sync_published_to_gcp.PS_CACHE_PREFIX = os.path.join(test_dir, 'cache', 'ps_cache', '')
sync_published_to_gcp.FTP_PREFIX = os.path.join(test_dir, 'data', 'ftp', '')
sync_published_to_gcp.ORIG_PREFIX = os.path.join(test_dir, 'data', 'orig', '')
sync_published_to_gcp.DATA_PREFIX = os.path.join(test_dir, 'data', '')
TEST_PORT = 12721
sync_published_to_gcp.CONCURRENCY_PER_WEBNODE = [(f'localhost:{TEST_PORT}', 1)]

from submissions_to_gcp import submission_message_to_file_state, sync_to_gcp, logger, \
    MissingGeneratedFile, \
    BrokenSubmission, TIMEOUTS, SyncVerdict, submission_callback, TIMEOUTS
import subprocess
import shutil

import http.server
import threading
import re
from identifier import Identifier as ArxivId

from unittest.mock import MagicMock


TIMEOUTS["PDF_TIMEOUT"] = 3
TIMEOUTS["HTML_TIMEOUT"] = 3


def trim_test_dir(fileset):
    for idx in range(len(fileset)):
        fileset[idx]['cit'] = fileset[idx]['cit'][len(test_dir):]
    return fileset


class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """the handler gets the pdf request, and copy the dummy PDF to the destination.
    if it's html request, unpack the html and put it under /ps_cache

    When asking PDF, if the version is 99, the 404 returned.
    When asking PDF, if the version is 98, the 404 returned after 120 seconds wait - to test the
    timeout.
    """

    def do_GET(self):
        for pattern in [r'^/pdf/(\d{4}\.\d{5}v\d+)(.pdf|)$', r'^/pdf/([a-z\-]+/\d{7}v\d+)(.pdf|)$']:
            pdf_req = re.match(pattern, self.path)
            if pdf_req:
                break

        if pdf_req:
            paper_id = ArxivId(pdf_req.group(1))
            if paper_id.has_version:
                if paper_id.version == 99:
                    self.send_response(404)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html> <body> <h1>Hello, world!</h1> </body> </html>")
                    return
                if paper_id.version == 98:
                    #
                    time.sleep(200)
                    self.send_response(404)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html> <body> <h1>Hello, world!</h1> </body> </html>")
                    return

            x_path = os.path.join(test_dir, "data", "x.pdf")
            archive = paper_id.archive if paper_id.is_old_id else "arxiv"
            pdf_path = os.path.join(sync_published_to_gcp.PS_CACHE_PREFIX, archive, "pdf",
                                    paper_id.yymm, f"{paper_id.filename}v{paper_id.version}.pdf")
            if not os.path.exists(pdf_path):
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                shutil.copy(x_path, pdf_path)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html> <body> <h1>Hello, world!</h1> </body> </html>")
            return

        # 'http://localhost:12721/html/2308.99990v1'
        html_req = re.match(r'^/html/(\d{4}\.\d{5}v\d+)$', self.path)
        if html_req:
            paper_id = ArxivId(html_req.group(1))

            # PosixPath('/home/ntai/arxiv/arxiv-browse/script/sync_prod_to_gcp/test/cache/ps_cache/arxiv/html/2308/2308.99990v1')
            for suffix in [".html.gz", ".tar.gz"]:
                # 2409.03427 is under /ftp
                if paper_id.has_version and paper_id.id != "2409.03427":
                    source_path = os.path.join(test_dir, "data", "orig", "arxiv", "papers",
                                               paper_id.yymm,
                                               f"{paper_id.idv}{suffix}")
                else:
                    source_path = os.path.join(test_dir, "data", "ftp", "arxiv", "papers",
                                               paper_id.yymm,
                                               f"{paper_id.id}{suffix}")
                if os.path.exists(source_path):
                    break
            else:
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                return
            # /home/ntai/arxiv/arxiv-browse/script/sync_prod_to_gcp/test/cache/ps_cache/arxiv/html/2308/2308.99990v1'
            html_path = os.path.join(sync_published_to_gcp.PS_CACHE_PREFIX, "arxiv", "html",
                                     paper_id.yymm, paper_id.idv)
            os.makedirs(html_path, exist_ok=True)
            if suffix == ".tar.gz":
                subprocess.call(['tar', 'xzf', source_path], cwd=html_path)
            else:
                dest = os.path.join(html_path, os.path.basename(source_path))
                shutil.copy(source_path, dest)
                subprocess.call(['gunzip', dest])

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html> <body> <h1>Hello, world!</h1> </body> </html>")
            return

        self.send_response(404)
        self.end_headers()


def start_http_server(server_class=http.server.HTTPServer, handler_class=SimpleHTTPRequestHandler,
                      port=TEST_PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


def run_server_in_thread(port):
    thread = threading.Thread(target=start_http_server,
                              args=(http.server.HTTPServer, SimpleHTTPRequestHandler, port))
    thread.daemon = True
    thread.start()
    return thread


def get_file_size(obj: str):
    out = subprocess.check_output(["gsutil", "ls", "-l", obj]).decode("utf-8")
    return out.splitlines()[0].strip().split()[0]


def bucket_object_exists(obj: str) -> bool:
    try:
        # Run the gsutil command to check if the object exists
        subprocess.check_output(["gsutil", "ls", obj], stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError as e:
        # If the object does not exist, gsutil will return a non-zero exit code
        if b"CommandException" in e.output:
            return False
        raise  # Re-raise the exception if it's not the expected error


arxivce_1756_obsolete = "gs://arxiv-sync-test-01/ftp/arxiv/papers/1907/1907.07431.gz"


class TestSubmissionsToGCP(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """starts the dummy http server"""
        cls.port = TEST_PORT
        cls.server_thread = run_server_in_thread(cls.port)

    @classmethod
    def tearDownClass(cls):
        cls.server_thread.join(0)

    def setUp(self) -> None:
        logger.setLevel(logging.DEBUG)
        # This isn't a goog idea, you know.
        if os.path.exists("test/test-output"):
            shutil.rmtree("test/test-output")
            pass
        os.makedirs("test/test-output", exist_ok=True)
        os.putenv("GOOGLE_APPLICATION_CREDENTIALS", "test/gcp-sync-test-role.json")
        rm_items = ["gsutil", "rm", "-a", "-f"]
        droplets = ["gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/2308.16188.abs",
                    "gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/2308.16188.tar.gz",
                    "gs://arxiv-sync-test-01/ps_cache/arxiv/pdf/2308/2308.16188v1.pdf",
                    "gs://arxiv-sync-test-01/ps_cache/arxiv/pdf/2308/2308.16188v2.pdf",
                    "gs://arxiv-sync-test-01/ps_cache/arxiv/pdf/2308/2308.16190v1.pdf",
                    "gs://arxiv-sync-test-01/ps_cache/arxiv/html/2308/2308.99990v1/2308.99990v1.html",
                    "gs://arxiv-sync-test-01/ftp/arxiv/papers/1907/1907.07431.tar.gz",
                    "gs://arxiv-sync-test-01/orig/arxiv/papers/1907/1907.07431v2.abs",
                    "gs://arxiv-sync-test-01/orig/arxiv/papers/1907/1907.07431v2.gz",
                    "gs://arxiv-sync-test-01/ps_cache/arxiv/pdf/2409/2409.10667v1.pdf",
                    "gs://arxiv-sync-test-01/ps_cache/physics/pdf/0106/0106051v1.pdf",
                    ]
        subprocess.call(rm_items + droplets,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        subprocess.call(["gsutil", "cp", "test/data/ftp/arxiv/papers/2308/2308.16188.pdf",
                         "gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/2308.16188.pdf"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # make sure that the dummy pdf doesn't exist
        paper_id = "2308.16190"
        pdf_path = os.path.join(sync_published_to_gcp.PS_CACHE_PREFIX, "arxiv", "pdf", "2308",
                                f"{paper_id}.pdf")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        paper_id = "2308.99990v1"
        html_path = os.path.join(sync_published_to_gcp.PS_CACHE_PREFIX, "arxiv", "html", "2308",
                                 paper_id)
        if os.path.exists(html_path):
            shutil.rmtree(html_path)

        archive = "physics"
        xid = "0106051v3"
        pdf_path = os.path.join(sync_published_to_gcp.PS_CACHE_PREFIX, archive, "pdf", xid[0:4], xid + ".pdf")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        html_path_2409_03427v1 = os.path.join(
            sync_published_to_gcp.PS_CACHE_PREFIX, "arxiv", "html", "2409", "2409.03427v1")
        if os.path.exists(html_path_2409_03427v1):
            shutil.rmtree(html_path_2409_03427v1)

        # test_arxivce_1756
        # Thess are the v2 abs, and .gz as being replaced, and copied under /ftp
        subprocess.call(["gsutil", "cp", "test/data/orig/arxiv/papers/1907/1907.07431v2.abs",
                         "gs://arxiv-sync-test-01/ftp/arxiv/papers/1907/1907.07431.abs"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["gsutil", "cp", "test/data/ftp/arxiv/papers/1907/1907.07431.gz",
                        arxivce_1756_obsolete],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pass

    def tearDown(self) -> None:
        paper_id = "2308.16190"
        pdf_path = os.path.join(sync_published_to_gcp.PS_CACHE_PREFIX, "arxiv", "pdf", "2308",
                                f"{paper_id}.pdf")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        pass

    def test_sync_op(self):
        # The set up copies a PDF to  ftp/arxiv/papers/2308/2308.16188.pdf
        # When sync happens, the .tar.gz, .abs in ftp and pdf in ps_cache are synced and the
        # pdf in the ftp is removed.
        paper_id = "2308.16188"
        data = {
            "type": "rep",
            "paper_id": paper_id,
            "version": "2",
            "src_ext": ".tar.gz"
        }
        log_extra = {"paper_id": paper_id}

        self.assertTrue(
            bucket_object_exists(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.pdf"))

        try:
            state = submission_message_to_file_state(data, log_extra, ask_webnode=False)
            desired_state = state.get_expected_files()
            if not desired_state:
                self.fail("Desired state must not be none")

        except MissingGeneratedFile as exc:
            logger.info(str(exc), extra=log_extra)
            self.fail("PDF should exist in the test")

        except Exception as _exc:
            logger.warning(
                f"Unknown error xid: {paper_id}", extra=log_extra, exc_info=True, stack_info=False)
            self.fail("Any exception is a bad test. Fix the test")

        verdict = SyncVerdict()

        try:
            sync_to_gcp(state, verdict, log_extra)
            # Acknowledge the message so it is not re-sent
            logger.info("ack message: %s", state.xid.ids, extra=log_extra)

        except Exception as _exc:
            logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)
            self.fail("Any exception is a bad test. Fix the test")

        # The PDF still there. In the real life, this is the new published PDF in /ftp
        self.assertTrue(
            bucket_object_exists(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.pdf"))

        # New submissions
        self.assertEqual("2642", get_file_size(
            f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.abs"))
        self.assertEqual("141", get_file_size(
            f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.tar.gz"))
        self.assertTrue(verdict.good())


    def test_html_submission_2409_03427(self):
        file_state = submission_message_to_file_state(
            {"type": "new", "paper_id": "2409.03427", "version": 1, "src_ext": ".html.gz"}, {},
            ask_webnode=True)
        expected = trim_test_dir(file_state.get_expected_files())
        self.assertEqual([
            {'cit': '/data/ftp/arxiv/papers/2409/2409.03427.abs',
             'gcp': 'ftp/arxiv/papers/2409/2409.03427.abs',
             'status': 'current',
             'type': 'abstract'},
            {'cit': '/data/ftp/arxiv/papers/2409/2409.03427.html.gz',
             'gcp': 'ftp/arxiv/papers/2409/2409.03427.html.gz',
             'status': 'current',
             'type': 'submission'},
            {'cit': '/cache/ps_cache/arxiv/html/2409/2409.03427v1',
             'gcp': 'ps_cache/arxiv/html/2409/2409.03427v1',
             'status': 'current',
             'type': 'html-cache'},
            {'cit': '/cache/ps_cache/arxiv/html/2409/2409.03427v1/2409.03427.html',
             'gcp': 'ps_cache/arxiv/html/2409/2409.03427v1/2409.03427.html',
             'status': 'current',
             'type': 'html-files'}
        ], expected)

    def test_ask_pdf(self):
        """Get the PDF for modern arXiv ID, create PDF and send to GCP"""
        paper_id = "2308.16190"
        data = {
            "type": "new",
            "paper_id": paper_id,
            "version": "1",
            "src_ext": ".tar.gz"
        }
        log_extra = {"paper_id": paper_id}

        try:
            state = submission_message_to_file_state(data, log_extra, ask_webnode=True)
            desired_state = state.get_expected_files()
            if not desired_state:
                self.fail("Desired state must not be none")

        except MissingGeneratedFile as exc:
            logger.info(str(exc), extra=log_extra)
            self.fail("PDF should exist in the test")

        except Exception as _exc:
            logger.warning(
                f"Unknown error xid: {paper_id}", extra=log_extra, exc_info=True, stack_info=False)
            self.fail("Any exception is a bad test. Fix the test")

        verdict = SyncVerdict()
        try:
            sync_to_gcp(state, verdict, log_extra)
            # Acknowledge the message so it is not re-sent
            logger.info("ack message: %s", state.xid.ids, extra=log_extra)

        except Exception as _exc:
            logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)
            self.fail("Any exception is a bad test. Fix the test")

        # Fake PDF is created.
        self.assertEqual("1115014", get_file_size(
            f"gs://arxiv-sync-test-01/ps_cache/arxiv/pdf/2308/{paper_id}v1.pdf"))

        # New submissions
        self.assertEqual("2643", get_file_size(
            f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.abs"))
        self.assertEqual("141", get_file_size(
            f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.tar.gz"))
        self.assertTrue(verdict.good())


    def test_not_ask_pdf(self):
        """Get the PDF for modern arXiv ID, create PDF and send to GCP"""
        paper_id = "2308.16190"
        data = {
            "type": "new",
            "paper_id": paper_id,
            "version": "1",
            "src_ext": ".tar.gz"
        }
        log_extra = {"paper_id": paper_id}
        abs_obj = f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.abs"
        if bucket_object_exists(abs_obj):
            subprocess.run(["gsutil", "rm", "-a", "-f", abs_obj])

        for idx in range(3):
            try:
                state = submission_message_to_file_state(data, log_extra, cache_upload=False)
                desired_state = state.get_expected_files()
                if not desired_state:
                    self.fail("Desired state must not be none")

            except MissingGeneratedFile as exc:
                logger.info(str(exc), extra=log_extra)
                self.fail("This exception should not happen")

            except Exception as _exc:
                logger.warning(
                    f"Unknown error xid: {paper_id}", extra=log_extra, exc_info=True, stack_info=False)
                self.fail("Any exception is a bad test. Fix the test")

            verdict = SyncVerdict()
            try:
                sync_to_gcp(state, verdict, log_extra)
                # Acknowledge the message so it is not re-sent
                logger.info("Sync success: %s", state.xid.ids, extra=log_extra)

            except Exception as _exc:
                logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)
                self.fail("Any exception is a bad test. Fix the test")

            if not bucket_object_exists(abs_obj):
                self.fail("obj %s did not copy?" % abs_obj)

            self.assertTrue(verdict.good(), "Verdict not okay ")


    def test_ask_pdf_for_old_arxiv_id(self):
        """Get the PDF for old arXiv ID, create PDF and send to GCP"""
        xid = "0106051"
        yymm = xid[0:4]
        archive = "physics"
        paper_id = f"{archive}/{xid}"
        version = "3"
        data = {
            "type": "new",
            "paper_id": paper_id,
            "version": version,
            "src_ext": ".tar.gz"
        }
        log_extra = {"paper_id": paper_id}

        try:
            state = submission_message_to_file_state(data, log_extra, ask_webnode=True)
            desired_state = state.get_expected_files()
            if not desired_state:
                self.fail("Desired state must not be none")

        except MissingGeneratedFile as exc:
            logger.info(str(exc), extra=log_extra)
            self.fail("PDF should exist in the test")

        except Exception as _exc:
            logger.warning(
                f"Unknown error xid: {paper_id}", extra=log_extra, exc_info=True, stack_info=False)
            self.fail("Any exception is a bad test. Fix the test")


        verdict = SyncVerdict()

        try:
            sync_to_gcp(state, verdict, log_extra)
            # Acknowledge the message so it is not re-sent
            logger.info("ack message: %s", state.xid.ids, extra=log_extra)

        except Exception as _exc:
            logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)
            self.fail("Any exception is a bad test. Fix the test")
            pass

        # Fake PDF is created.
        self.assertEqual("1115014", get_file_size(
            f"gs://arxiv-sync-test-01/ps_cache/{archive}/pdf/{yymm}/{xid}v{version}.pdf"))

        # New submissions
        self.assertEqual("515", get_file_size(
            f"gs://arxiv-sync-test-01/ftp/{archive}/papers/{yymm}/{xid}.abs"))
        self.assertEqual("141", get_file_size(
            f"gs://arxiv-sync-test-01/ftp/{archive}/papers/{yymm}/{xid}.tar.gz"))

        self.assertTrue(verdict.good(), "Verdict not okay ")

    def test_ask_pdf_timeout(self):
        """
        The source does not exist and therefore the pdf cannot be made.
        The test should end with HTTP returnin 404, times out.
        """
        paper_id = "2308.99999"
        data = {
            "type": "new",
            "paper_id": paper_id,
            "version": "98",  # version 98 gets 404 reply after 120 seconds
            "src_ext": ".tar.gz"
        }

        pdf_path = os.path.join(sync_published_to_gcp.PS_CACHE_PREFIX, "arxiv", "pdf", "2308",
                                f"{paper_id}v{data['version']}.pdf")
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)

        log_extra = {"paper_id": paper_id}

        try:
            state = submission_message_to_file_state(data, log_extra, ask_webnode=True)
            desired_state = state.get_expected_files()
            if not desired_state:
                self.fail("Desired state must not be none")

        except sync_published_to_gcp.WebnodeException as webn_exc:
            # The exception is replaced with missing generated file
            self.fail(
                "PDF should not be created and end with the exception, but this is not the expected exception.")
            pass

        except MissingGeneratedFile as _exc:
            print("PDF should not be created and end with the exception - this test passed")
            return

        except BrokenSubmission as _exc:
            self.fail("Morally correct but a test bug nonetheless")
            return

        except Exception as _exc:
            self.fail("all other exceptions are bad")
            return

        self.fail("PDF should not be created and end with the exception")

    def test_ask_pdf_then_fail(self):
        """
        The source does not exist and therefore the pdf cannot be made.
        The test should end with HTTP returnin 404, times out.
        """
        paper_id = "2308.99999"
        data = {
            "type": "new",
            "paper_id": paper_id,
            "version": "99",  # version 99 gets 404 reply
            "src_ext": ".tar.gz"
        }
        log_extra = {"paper_id": paper_id}

        try:
            state = submission_message_to_file_state(data, log_extra, ask_webnode=True)
            desired_state = state.get_expected_files()
            if not desired_state:
                self.fail("Desired state must not be none")

        except MissingGeneratedFile as _exc:
            print("PDF should not be created and end with the exception - this test passed")
            return

        except Exception as _exc:
            self.fail("all other exceptions are bad")

        self.fail("PDF should not be created and end with the exception")

    def test_ask_html(self):
        """
        Ask webnode to make HTML file
        """
        paper_id = "2308.99990"
        data = {
            "type": "new",
            "paper_id": paper_id,
            "version": "1",
            "src_ext": ".html.gz"
        }
        log_extra = {"paper_id": paper_id}

        try:
            state = submission_message_to_file_state(data, log_extra, ask_webnode=True)
        except MissingGeneratedFile as exc:
            logger.info(str(exc), extra=log_extra)
            self.fail("PDF should exist in the test")

        except Exception as _exc:
            logger.warning(
                f"Unknown error xid: {paper_id}", extra=log_extra, exc_info=True, stack_info=False)
            self.fail("Any exception is a bad test. Fix the test")

        desired_state = state.get_expected_files()
        if not desired_state:
            logger.warning(
                f"There is no associated files? xid: {state.xid.ids}",
                extra=log_extra)

        verdict = SyncVerdict()
        try:
            sync_to_gcp(state, verdict, log_extra)
            # Acknowledge the message so it is not re-sent
            logger.info("ack message: %s", state.xid.ids, extra=log_extra)

        except Exception as _exc:
            logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)
            self.fail("Any exception is a bad test. Fix the test")
            pass

        # Fake HTML file is created.
        self.assertEqual("84", get_file_size(
            f"gs://arxiv-sync-test-01/ps_cache/arxiv/html/2308/{paper_id}v1/{paper_id}v1.html"))

        # New submissions
        self.assertEqual("1055", get_file_size(
            f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.abs"))
        self.assertTrue(verdict.good(), "Verdict not okay ")


    def test_arxivce_1756(self):
        """
The ftp area has the current version and it must not have files from non-current versions.

This becomes a problem when finding the source for a paper. If there are multiple source files it
is ambiguous which is the right one. Currently there is no record of which source file is associated
 with which version. There is also no source file resolution order.

dc34 @soup: Downloads$ gsutil ls -l gs://arxiv-production-data/orig/arxiv/papers/1907/1907.07431*
       772  2022-02-01T11:40:52Z  gs://arxiv-production-data/orig/arxiv/papers/1907/1907.07431v1.abs
     25559  2021-08-10T22:31:38Z  gs://arxiv-production-data/orig/arxiv/papers/1907/1907.07431v1.gz
       875  2024-05-16T00:48:10Z  gs://arxiv-production-data/orig/arxiv/papers/1907/1907.07431v2.abs
     24560  2024-05-16T00:48:10Z  gs://arxiv-production-data/orig/arxiv/papers/1907/1907.07431v2.gz
TOTAL: 4 objects, 51766 bytes (50.55 KiB)
bdc34 @soup: Downloads$ gsutil ls -l gs://arxiv-production-data/ftp/arxiv/papers/1907/1907.07431*
       961  2024-05-16T00:48:08Z  gs://arxiv-production-data/ftp/arxiv/papers/1907/1907.07431.abs
     24560  2021-08-11T03:56:30Z  gs://arxiv-production-data/ftp/arxiv/papers/1907/1907.07431.gz
   5205590  2024-05-16T00:48:09Z  gs://arxiv-production-data/ftp/arxiv/papers/1907/1907.07431.tar.gz
TOTAL: 3 objects, 5231111 bytes (4.99 MiB)

------------------------------------------------------------------------------
\\
arXiv:1907.07431
From: Reynald Lercier <foo@example.com>
Date: Wed, 17 Jul 2019 10:35:13 GMT   (25kb)
Date (revised v2): Tue, 17 Dec 2019 14:06:04 GMT   (24kb)
Date (revised v3): Wed, 15 May 2024 17:42:55 GMT   (5084kb,A)

Title: Siegel modular forms of degree three and invariants of ternary quartics
Authors: Reynald Lercier and Christophe Ritzenthaler
Categories: math.NT math.AG
MSC-class: 14K20, 14K25, 14J15, 11F46, 14L24
DOI: 10.1090/proc/14940
License: http://arxiv.org/licenses/nonexclusive-distrib/1.0/
\\
  We...
\\

so the correct file state of /ftp is
    * gs://arxiv-production-data/ftp/arxiv/papers/1907/1907.07431.abs
    * gs://arxiv-production-data/ftp/arxiv/papers/1907/1907.07431.tar.gz
"""
        # set up
        # double check it is there.
        # This created the obsolete file is in /ftp
        self.assertEqual("36", get_file_size(arxivce_1756_obsolete))

        test_data = {"type": "rep", "paper_id": "1907.07431", "version": "3", "src_ext": ".tar.gz"}

        # This should ask webnode (well, local http server for this test) to make the PDF file
        file_state = submission_message_to_file_state(test_data, {}, ask_webnode=True)

        expected = trim_test_dir(file_state.get_expected_files())
        # I know this is tested in other one but, you know, ask_webnode is different.
        self.assertEqual(
            [{'cit': '/data/ftp/arxiv/papers/1907/1907.07431.abs',
              'gcp': 'ftp/arxiv/papers/1907/1907.07431.abs',
              'status': 'current',
              'type': 'abstract'},
             {'cit': '/data/ftp/arxiv/papers/1907/1907.07431.tar.gz',
              'gcp': 'ftp/arxiv/papers/1907/1907.07431.tar.gz',
              'status': 'current',
              'type': 'submission'},
             {'cit': '/cache/ps_cache/arxiv/pdf/1907/1907.07431v3.pdf',
              'gcp': 'ps_cache/arxiv/pdf/1907/1907.07431v3.pdf',
              'status': 'current',
              'type': 'pdf-cache'},
             {'cit': '/data/orig/arxiv/papers/1907/1907.07431v2.abs',
              'gcp': 'orig/arxiv/papers/1907/1907.07431v2.abs',
              'obsoleted': 'ftp/arxiv/papers/1907/1907.07431.abs',
              'original': 'orig/arxiv/papers/1907/1907.07431v2.abs',
              'status': 'obsolete',
              'type': 'abstract',
              'version': 2},
             {'cit': '/data/orig/arxiv/papers/1907/1907.07431v2.gz',
              'gcp': 'orig/arxiv/papers/1907/1907.07431v2.gz',
              'obsoleted': 'ftp/arxiv/papers/1907/1907.07431.gz',
              'original': 'orig/arxiv/papers/1907/1907.07431v2.gz',
              'status': 'obsolete',
              'type': 'submission',
              'version': 2}],
            expected)

        log_extra = {}
        verdict = SyncVerdict()

        try:
            sync_to_gcp(file_state, verdict, log_extra)

        except Exception as _exc:
            logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)
            self.fail("Any exception is a bad test. Fix the test")

        for entry in expected:
            gcp = "gs://arxiv-sync-test-01/" + entry['gcp']
            should_be_true = bucket_object_exists(gcp)
            if not should_be_true:
                logger.error(f"{gcp} <-- should exist but not there")
            self.assertEqual(gcp, gcp if should_be_true else "")

        # because the obsolete file is deleted
        self.assertFalse(bucket_object_exists("gs://arxiv-sync-test-01/ftp/arxiv/papers/1907/1907.07431.gz"))

        self.assertTrue(verdict.good(), "Verdict not okay ")


    def test_new_pdf(self):
        paper_id = "2409.10667"
        test_data = {"type": "new", "paper_id": paper_id, "version": "1", "src_ext": ".pdf"}
        file_state = submission_message_to_file_state(test_data, {}, ask_webnode=True)
        expected = trim_test_dir(file_state.get_expected_files())
        self.assertEqual([
            {'cit': f'/data/ftp/arxiv/papers/2409/{paper_id}.abs',
             'gcp': f'ftp/arxiv/papers/2409/{paper_id}.abs',
             'status': 'current',
             'type': 'abstract'},
            {'cit': f'/data/ftp/arxiv/papers/2409/{paper_id}.pdf',
             'gcp': f'ftp/arxiv/papers/2409/{paper_id}.pdf',
             'status': 'current',
             'type': 'submission'}
        ], expected)
        # This should not be created
        self.assertFalse(bucket_object_exists(
            f"gs://arxiv-sync-test-01/ps_cache/arxiv/pdf/2409/{paper_id}v1/{paper_id}v1.pdf"))


class TestPayloadToMeta(unittest.TestCase):

    def test_new(self):
        test_data = {"type": "new", "paper_id": "2308.99991", "version": "1", "src_ext": ".tar.gz"}
        file_state = submission_message_to_file_state(test_data, {}, ask_webnode=False)
        expected = trim_test_dir(file_state.get_expected_files())
        self.assertEqual([
            {'cit': '/data/ftp/arxiv/papers/2308/2308.99991.abs',
             'gcp': 'ftp/arxiv/papers/2308/2308.99991.abs',
             'status': 'current',
             'type': 'abstract'},
            {'cit': '/data/ftp/arxiv/papers/2308/2308.99991.tar.gz',
             'gcp': 'ftp/arxiv/papers/2308/2308.99991.tar.gz',
             'status': 'current',
             'type': 'submission'},
            {'cit': '/cache/ps_cache/arxiv/pdf/2308/2308.99991v1.pdf',
             'gcp': 'ps_cache/arxiv/pdf/2308/2308.99991v1.pdf',
             'status': 'current',
             'type': 'pdf-cache'}
        ], expected)

    def test_wdr(self):
        # withdrawal -
        # the v2 abs is populated, but v1 .abs, .tar.gz are retired
        # v2 .tar.gz is not made
        test_data = {"type": "wdr", "paper_id": "2308.99992", "version": "2", "src_ext": ".tar.gz"}
        file_state = submission_message_to_file_state(test_data, {}, ask_webnode=False)
        expected = trim_test_dir(file_state.get_expected_files())
        self.assertEqual([
            {'cit': '/data/ftp/arxiv/papers/2308/2308.99992.abs',
             'gcp': 'ftp/arxiv/papers/2308/2308.99992.abs',
             'status': 'current',
             'type': 'abstract'},
            {'cit': '/data/orig/arxiv/papers/2308/2308.99992v1.abs',
             'gcp': 'orig/arxiv/papers/2308/2308.99992v1.abs',
             'obsoleted': 'ftp/arxiv/papers/2308/2308.99992.abs',
             'original': 'orig/arxiv/papers/2308/2308.99992v1.abs',
             'status': 'obsolete',
             'type': 'abstract',
             'version': 1},
            {'cit': '/data/orig/arxiv/papers/2308/2308.99992v1.tar.gz',
             'gcp': 'orig/arxiv/papers/2308/2308.99992v1.tar.gz',
             'obsoleted': 'ftp/arxiv/papers/2308/2308.99992.tar.gz',
             'original': 'orig/arxiv/papers/2308/2308.99992v1.tar.gz',
             'status': 'obsolete',
             'type': 'submission',
             'version': 1}
        ], expected)

    def test_jref_1(self):
        test_data = {"type": "jref", "paper_id": "2308.99994", "version": "2", "src_ext": ".pdf"}
        file_state = submission_message_to_file_state(test_data, {}, ask_webnode=False)
        expected = trim_test_dir(file_state.get_expected_files())
        self.assertEqual([
            {'cit': '/data/ftp/arxiv/papers/2308/2308.99994.abs',
             'gcp': 'ftp/arxiv/papers/2308/2308.99994.abs',
             'status': 'current',
             'type': 'abstract'},
            {'cit': '/data/ftp/arxiv/papers/2308/2308.99994.pdf',
             'gcp': 'ftp/arxiv/papers/2308/2308.99994.pdf',
             'status': 'current',
             'type': 'submission'}
            ], expected)

    def test_cross(self):
        test_data = {"type": "cross", "paper_id": "2308.99995", "version": "2", "src_ext": ".tar.gz"}
        file_state = submission_message_to_file_state(test_data, {}, ask_webnode=False)
        expected = trim_test_dir(file_state.get_expected_files())
        self.assertEqual([
            {'cit': '/data/ftp/arxiv/papers/2308/2308.99995.abs',
             'gcp': 'ftp/arxiv/papers/2308/2308.99995.abs',
             'status': 'current',
             'type': 'abstract'},
            {'cit': '/data/ftp/arxiv/papers/2308/2308.99995.tar.gz',
             'gcp': 'ftp/arxiv/papers/2308/2308.99995.tar.gz',
             'status': 'current',
             'type': 'submission'},
            {'cit': '/cache/ps_cache/arxiv/html/2308/2308.99995v2',
             'gcp': 'ps_cache/arxiv/html/2308/2308.99995v2',
             'status': 'current',
             'type': 'html-cache'}
        ], expected)

    def test_jref_2(self):
        test_data = {"type": "jref", "paper_id": "2308.99996", "version": "2", "src_ext": ".tar.gz"}
        file_state = submission_message_to_file_state(test_data, {}, ask_webnode=False)
        expected = trim_test_dir(file_state.get_expected_files())
        self.assertEqual([
            {'cit': '/data/ftp/arxiv/papers/2308/2308.99996.abs',
             'gcp': 'ftp/arxiv/papers/2308/2308.99996.abs',
             'status': 'current',
             'type': 'abstract'},
            {'cit': '/data/ftp/arxiv/papers/2308/2308.99996.tar.gz',
             'gcp': 'ftp/arxiv/papers/2308/2308.99996.tar.gz',
             'status': 'current',
             'type': 'submission'},
            {'cit': '/cache/ps_cache/arxiv/pdf/2308/2308.99996v2.pdf',
             'gcp': 'ps_cache/arxiv/pdf/2308/2308.99996v2.pdf',
             'status': 'current',
             'type': 'pdf-cache'}
        ], expected)

    def test_submission_message_to_payloads(self):
        test_data = {"type": "rep", "paper_id": "physics/0106051", "version": "3", "src_ext": ".gz"}
        file_state = submission_message_to_file_state(test_data, {}, ask_webnode=False)
        payloads = trim_test_dir(file_state.get_expected_files())
        self.assertEqual(
            [
                {'cit': '/data/ftp/physics/papers/0106/0106051.abs',
                 'gcp': 'ftp/physics/papers/0106/0106051.abs',
                 'status': 'current',
                 'type': 'abstract'},
                {'cit': '/data/ftp/physics/papers/0106/0106051.gz',
                 'gcp': 'ftp/physics/papers/0106/0106051.gz',
                 'status': 'current',
                 'type': 'submission'},
                {'cit': '/cache/ps_cache/physics/pdf/0106/0106051v3.pdf',
                 'gcp': 'ps_cache/physics/pdf/0106/0106051v3.pdf',
                 'status': 'current',
                 'type': 'pdf-cache'},
                {'cit': '/data/orig/physics/papers/0106/0106051v2.abs',
                 'gcp': 'orig/physics/papers/0106/0106051v2.abs',
                 'obsoleted': 'ftp/physics/papers/0106/0106051.abs',
                 'original': 'orig/physics/papers/0106/0106051v2.abs',
                 'status': 'obsolete',
                 'type': 'abstract',
                 'version': 2},
                {'cit': '/data/orig/physics/papers/0106/0106051v2.gz',
                 'gcp': 'orig/physics/papers/0106/0106051v2.gz',
                 'obsoleted': 'ftp/physics/papers/0106/0106051.gz',
                 'original': 'orig/physics/papers/0106/0106051v2.gz',
                 'status': 'obsolete',
                 'type': 'submission',
                 'version': 2}
            ], payloads)

        test_data = {"type": "rep", "paper_id": "physics/0106051", "version": 3, "src_ext": ".gz"}
        file_state = submission_message_to_file_state(test_data, {}, ask_webnode=False)
        payloads = trim_test_dir(file_state.get_expected_files())

        self.assertEqual(
            [
                {'cit': '/data/ftp/physics/papers/0106/0106051.abs',
                 'gcp': 'ftp/physics/papers/0106/0106051.abs',
                 'status': 'current',
                 'type': 'abstract'},
                {'cit': '/data/ftp/physics/papers/0106/0106051.gz',
                 'gcp': 'ftp/physics/papers/0106/0106051.gz',
                 'status': 'current',
                 'type': 'submission'},
                {'cit': '/cache/ps_cache/physics/pdf/0106/0106051v3.pdf',
                 'gcp': 'ps_cache/physics/pdf/0106/0106051v3.pdf',
                 'status': 'current',
                 'type': 'pdf-cache'},
                {'cit': '/data/orig/physics/papers/0106/0106051v2.abs',
                 'gcp': 'orig/physics/papers/0106/0106051v2.abs',
                 'obsoleted': 'ftp/physics/papers/0106/0106051.abs',
                 'original': 'orig/physics/papers/0106/0106051v2.abs',
                 'status': 'obsolete',
                 'type': 'abstract',
                 'version': 2},
                {'cit': '/data/orig/physics/papers/0106/0106051v2.gz',
                 'gcp': 'orig/physics/papers/0106/0106051v2.gz',
                 'obsoleted': 'ftp/physics/papers/0106/0106051.gz',
                 'original': 'orig/physics/papers/0106/0106051v2.gz',
                 'status': 'obsolete',
                 'type': 'submission',
                 'version': 2}
            ],
            payloads)

    def test_arxivce_1756(self):
        test_data = {"type": "rep", "paper_id": "1907.07431", "version": "3", "src_ext": ".tar.gz"}

        file_state = submission_message_to_file_state(test_data, {}, ask_webnode=False)
        expected = trim_test_dir(file_state.get_expected_files())
        self.assertEqual(
            [{'cit': '/data/ftp/arxiv/papers/1907/1907.07431.abs',
              'gcp': 'ftp/arxiv/papers/1907/1907.07431.abs',
              'status': 'current',
              'type': 'abstract'},
             {'cit': '/data/ftp/arxiv/papers/1907/1907.07431.tar.gz',
              'gcp': 'ftp/arxiv/papers/1907/1907.07431.tar.gz',
              'status': 'current',
              'type': 'submission'},
             {'cit': '/cache/ps_cache/arxiv/pdf/1907/1907.07431v3.pdf',
              'gcp': 'ps_cache/arxiv/pdf/1907/1907.07431v3.pdf',
              'status': 'current',
              'type': 'pdf-cache'},
             {'cit': '/data/orig/arxiv/papers/1907/1907.07431v2.abs',
              'gcp': 'orig/arxiv/papers/1907/1907.07431v2.abs',
              'obsoleted': 'ftp/arxiv/papers/1907/1907.07431.abs',
              'original': 'orig/arxiv/papers/1907/1907.07431v2.abs',
              'status': 'obsolete',
              'type': 'abstract',
              'version': 2},
             {'cit': '/data/orig/arxiv/papers/1907/1907.07431v2.gz',
              'gcp': 'orig/arxiv/papers/1907/1907.07431v2.gz',
              'obsoleted': 'ftp/arxiv/papers/1907/1907.07431.gz',
              'original': 'orig/arxiv/papers/1907/1907.07431v2.gz',
              'status': 'obsolete',
              'type': 'submission',
              'version': 2}],
            expected)

    def test_source_format_change(self):
        file_state = submission_message_to_file_state(
            {"type": "rep", "paper_id": "2403.99999", "version": 3, "src_ext": ".tar.gz"}, {},
            ask_webnode=False)
        expected = trim_test_dir(file_state.get_expected_files())
        self.assertEqual([
            {'type': 'abstract', 'cit': '/data/ftp/arxiv/papers/2403/2403.99999.abs',
             'status': 'current', 'gcp': 'ftp/arxiv/papers/2403/2403.99999.abs'},
            {'type': 'submission', 'cit': '/data/ftp/arxiv/papers/2403/2403.99999.tar.gz',
             'status': 'current', 'gcp': 'ftp/arxiv/papers/2403/2403.99999.tar.gz'},
            {'type': 'pdf-cache', 'cit': '/cache/ps_cache/arxiv/pdf/2403/2403.99999v3.pdf',
             'status': 'current', 'gcp': 'ps_cache/arxiv/pdf/2403/2403.99999v3.pdf'},
            {'type': 'abstract', 'cit': '/data/orig/arxiv/papers/2403/2403.99999v2.abs',
             'status': 'obsolete', 'version': 2,
             'obsoleted': 'ftp/arxiv/papers/2403/2403.99999.abs',
             'original': 'orig/arxiv/papers/2403/2403.99999v2.abs',
             'gcp': 'orig/arxiv/papers/2403/2403.99999v2.abs'},
            {'type': 'submission', 'cit': '/data/orig/arxiv/papers/2403/2403.99999v2.gz',
             'status': 'obsolete', 'version': 2, 'obsoleted': 'ftp/arxiv/papers/2403/2403.99999.gz',
             'original': 'orig/arxiv/papers/2403/2403.99999v2.gz',
             'gcp': 'orig/arxiv/papers/2403/2403.99999v2.gz'}
        ], expected)

    def test_arxivce_2763(self):
        test_data = {"type": "jref", "paper_id": "1008.9000", "version": "1", "src_ext": ""}

        file_state = submission_message_to_file_state(test_data, {}, ask_webnode=False)
        expected = trim_test_dir(file_state.get_expected_files())
        self.assertEqual([
            {'cit': '/data/ftp/arxiv/papers/1008/1008.9000.abs',
             'gcp': 'ftp/arxiv/papers/1008/1008.9000.abs',
             'status': 'current',
             'type': 'abstract'},
            {'cit': '/data/ftp/arxiv/papers/1008/1008.9000.ps.gz',
             'gcp': 'ftp/arxiv/papers/1008/1008.9000.ps.gz',
             'status': 'current',
             'type': 'submission'},
            {'cit': '/cache/ps_cache/arxiv/pdf/1008/1008.9000v1.pdf',
             'gcp': 'ps_cache/arxiv/pdf/1008/1008.9000v1.pdf',
             'status': 'current',
             'type': 'pdf-cache'},
        ],
        expected)


    def test_pdf_timeout(self):
        """
        The source does not exist and therefore the pdf cannot be made.
        The test should end with HTTP returnin 404, times out.
        """
        paper_id = "2308.99999"
        data = {
            "type": "new",
            "paper_id": paper_id,
            "version": "98",  # version 98 gets 404 reply after 120 seconds
            "src_ext": ".tar.gz"
        }

        pdf_path = os.path.join(sync_published_to_gcp.PS_CACHE_PREFIX, "arxiv", "pdf", "2308",
                                f"{paper_id}v{data['version']}.pdf")
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)

        abs_obj = f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.abs"
        if bucket_object_exists(abs_obj):
            subprocess.run(["gsutil", "rm", "-a", "-f", abs_obj])

        mock_message = MagicMock()
        mock_message.data = json.dumps(data).encode('utf-8')
        mock_message.attributes = {}
        mock_message.message_id = "12345"
        mock_message.publish_time = datetime.datetime.now(timezone.utc)

        TIMEOUTS["PDF_TIMEOUT"] = 1
        TIMEOUTS["HTML_TIMEOUT"] = 1

        try:
            submission_callback(mock_message)

        except Exception as _exc:
            logging.exception(_exc)
            pass

        # the abs is copied. (did not exist before, and exists now in the bucket)
        self.assertTrue(bucket_object_exists(abs_obj))

        # message.nack() called once
        mock_message.nack.assert_called_once()
