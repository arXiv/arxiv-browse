import os
import unittest
import sync_published_to_gcp
sync_published_to_gcp.GS_BUCKET = "arxiv-sync-test-01"
# Adjest to local testing
test_dir = os.path.dirname(os.path.abspath(__file__))
sync_published_to_gcp.CACHE_PREFIX = os.path.join(test_dir, 'cache', '')
sync_published_to_gcp.PS_CACHE_PREFIX = os.path.join(test_dir, 'cache', 'ps_cache', '')
sync_published_to_gcp.FTP_PREFIX = os.path.join(test_dir, 'data', 'ftp', '')
sync_published_to_gcp.ORIG_PREFIX = os.path.join(test_dir, 'data', 'orig', '')
sync_published_to_gcp.DATA_PREFIX = os.path.join(test_dir, 'data', '')
TEST_PORT = 12721
sync_published_to_gcp.CONCURRENCY_PER_WEBNODE = [(f'localhost:{TEST_PORT}', 1)]

from submissions_to_gcp import submission_message_to_file_state, sync_to_gcp, logger, MissingGeneratedFile, \
    SubmissionFilesState
import subprocess
import shutil

import http.server
import threading
import re
from identifier import Identifier as ArxivId


class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """the handler gets the pdf request, and copy the dummy PDF to the destination.
    if it's html request, unpack the html and put it under /ps_cache

    When asking PDF, if the version is 99, the 404 returned.
    """
    def do_GET(self):
        pdf_req = re.match(r'^/pdf/(\d{4}\.\d{5}v\d+)(.pdf|)$', self.path)
        if pdf_req:
            paper_id = ArxivId(pdf_req.group(1))
            if paper_id.has_version:
                if paper_id.version == 99:
                    self.send_response(404)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html> <body> <h1>Hello, world!</h1> </body> </html>")
                    return

            x_path = os.path.join(test_dir, "data", "x.pdf")
            pdf_path = os.path.join(sync_published_to_gcp.PS_CACHE_PREFIX, "arxiv", "pdf", paper_id.yymm, f"{paper_id.idv}.pdf")
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
                if paper_id.has_version:
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


def start_http_server(server_class=http.server.HTTPServer, handler_class=SimpleHTTPRequestHandler, port=TEST_PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

def run_server_in_thread(port):
    thread = threading.Thread(target=start_http_server, args=(http.server.HTTPServer, SimpleHTTPRequestHandler, port))
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
                    "gs://arxiv-sync-test-01/trash/ftp/arxiv/papers/2308/2308.16188.pdf",
                    "gs://arxiv-sync-test-01/trash/ftp/arxiv/papers/2308/2308.16188.pdf",
                    "gs://arxiv-sync-test-01/trash/ftp/arxiv/papers/1907/1907.07431.gz",
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

        pass


    def tearDown(self) -> None:
        paper_id = "2308.16190"
        pdf_path = os.path.join(sync_published_to_gcp.PS_CACHE_PREFIX, "arxiv", "pdf", "2308",
                                f"{paper_id}.pdf")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        pass


    def test_submission_message_to_payloads(self):

        def make_payloads(test_data: dict):
            file_state = submission_message_to_file_state(test_data, {}, ask_webnode=False)
            # The local contains the test_dir, so remove it and normalize for test
            return [(entry[0][len(test_dir):], entry[1]) for entry in file_state.to_payloads()]

        payloads = make_payloads({"paper_id": "physics/0106051", "version": "5", "src_ext": ".gz"})

        self.assertEqual([('/data/ftp/physics/papers/0106/0106051.abs', 'ftp/physics/papers/0106/0106051.abs'),
                          ('/data/ftp/physics/papers/0106/0106051.gz', 'ftp/physics/papers/0106/0106051.gz'),
                          # To unify the PDF generation to sync, it now includes the PDF in syncing files
                          ('/cache/ps_cache/physics/pdf/0106/0106051v5.pdf', 'ps_cache/physics/pdf/0106/0106051v5.pdf')
                          ], payloads)


        payloads = make_payloads({"type": "rep", "paper_id": "physics/0106051", "version": 5, "src_ext": ".gz"})

        self.assertEqual([('/data/ftp/physics/papers/0106/0106051.abs', 'ftp/physics/papers/0106/0106051.abs'),
                          ('/data/ftp/physics/papers/0106/0106051.gz', 'ftp/physics/papers/0106/0106051.gz'),

                          # To unify the PDF generation to sync, it now includes the PDF in syncing files
                          ('/cache/ps_cache/physics/pdf/0106/0106051v5.pdf', 'ps_cache/physics/pdf/0106/0106051v5.pdf'),

                          ('/data/orig/physics/papers/0106/0106051v4.abs', 'orig/physics/papers/0106/0106051v4.abs'),
                          ('/data/orig/physics/papers/0106/0106051v4.gz', 'orig/physics/papers/0106/0106051v4.gz')], payloads)

        payloads = make_payloads({"type": "rep", "paper_id": "2403.07874", "version": 3, "src_ext": ".tar.gz"})
        self.assertEqual([('/data/ftp/arxiv/papers/2403/2403.07874.abs', 'ftp/arxiv/papers/2403/2403.07874.abs'),
                          ('/data/ftp/arxiv/papers/2403/2403.07874.tar.gz', 'ftp/arxiv/papers/2403/2403.07874.tar.gz'),
                          ('/cache/ps_cache/arxiv/pdf/2403/2403.07874v3.pdf', 'ps_cache/arxiv/pdf/2403/2403.07874v3.pdf'), # ditto
                          ('/data/orig/arxiv/papers/2403/2403.07874v2.abs', 'orig/arxiv/papers/2403/2403.07874v2.abs'),
                          ('/data/orig/arxiv/papers/2403/2403.07874v2.tar.gz', 'orig/arxiv/papers/2403/2403.07874v2.tar.gz')], payloads)

    def test_sync_op(self):
        # The set up copies a PDF to  ftp/arxiv/papers/2308/2308.16188.pdf
        # When sync happens, the .tar.gz, .abs in ftp and pdf in ps_cache are synced and the
        # pdf in the ftp is renamed to trash/ftp/arxiv/papers/2308/2308.16188.pdf
        paper_id = "2308.16188"
        data = {
            "type": "new",
            "paper_id": paper_id,
            "version": "2",
            "src_ext": ".tar.gz"
        }
        log_extra = {"paper_id": paper_id}

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

        try:
            sync_to_gcp(state, log_extra)
            # Acknowledge the message so it is not re-sent
            logger.info("ack message: %s", state.xid.ids, extra=log_extra)

        except Exception as _exc:
            logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)
            self.fail("Any exception is a bad test. Fix the test")
            pass

        # The existing file is moved to trash
        self.assertEqual("1115014", get_file_size(f"gs://arxiv-sync-test-01/trash/ftp/arxiv/papers/2308/{paper_id}.pdf"))

        # New submissions
        self.assertEqual( "2642", get_file_size(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.abs"))
        self.assertEqual( "141", get_file_size(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.tar.gz"))


    def test_ask_pdf(self):
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

        try:
            sync_to_gcp(state, log_extra)
            # Acknowledge the message so it is not re-sent
            logger.info("ack message: %s", state.xid.ids, extra=log_extra)

        except Exception as _exc:
            logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)
            self.fail("Any exception is a bad test. Fix the test")
            pass

        # Fake PDF is created.
        self.assertEqual("1115014", get_file_size(f"gs://arxiv-sync-test-01/ps_cache/arxiv/pdf/2308/{paper_id}v1.pdf"))

        # New submissions
        self.assertEqual("2643", get_file_size(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.abs"))
        self.assertEqual("141", get_file_size(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.tar.gz"))


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
            return

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

        try:
            sync_to_gcp(state, log_extra)
            # Acknowledge the message so it is not re-sent
            logger.info("ack message: %s", state.xid.ids, extra=log_extra)

        except Exception as _exc:
            logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)
            self.fail("Any exception is a bad test. Fix the test")
            pass

        # Fake HTML file is created.
        self.assertEqual("84", get_file_size(f"gs://arxiv-sync-test-01/ps_cache/arxiv/html/2308/{paper_id}v1/{paper_id}v1.html"))

        # New submissions
        self.assertEqual("1055", get_file_size(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.abs"))


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
        subprocess.call(["gsutil", "cp", "test/data/orig/arxiv/papers/1907/1907.07431v2.abs",
                         "gs://arxiv-sync-test-01/ftp/arxiv/papers/1907/1907.07431.abs"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        obsolete = "gs://arxiv-sync-test-01/ftp/arxiv/papers/1907/1907.07431.gz"
        trashed = "gs://arxiv-sync-test-01/trash/ftp/arxiv/papers/1907/1907.07431.gz"

        subprocess.call(["gsutil", "cp", "test/data/ftp/arxiv/papers/1907/1907.07431.gz",
                        obsolete],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # double cheke it is there.
        # This created the obsolete file is in /ftp
        self.assertEqual("36", get_file_size(obsolete))
        # Trashed file does not exist yet
        self.assertFalse(bucket_object_exists(trashed))

        test_data = {"paper_id": "1907.07431", "version": "3", "src_ext": ".tar.gz"}

        # This should ask webnode to make the PDF file
        file_state = submission_message_to_file_state(test_data, {}, ask_webnode=True)
        # Trim off the source's leading test dir so the test expected is more readable
        payloads = [(entry[0][len(test_dir):], entry[1]) for entry in file_state.to_payloads()]
        self.assertEqual(
            [('/data/ftp/arxiv/papers/1907/1907.07431.abs', 'ftp/arxiv/papers/1907/1907.07431.abs'),
                  ('/data/ftp/arxiv/papers/1907/1907.07431.tar.gz','ftp/arxiv/papers/1907/1907.07431.tar.gz'),
                  ('/cache/ps_cache/arxiv/pdf/1907/1907.07431v3.pdf', 'ps_cache/arxiv/pdf/1907/1907.07431v3.pdf')],
            payloads)
        log_extra = {}
        try:
            sync_to_gcp(file_state, log_extra)

        except Exception as _exc:
            logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)
            self.fail("Any exception is a bad test. Fix the test")
            pass

        # Now the trashed object is there
        self.assertEqual("36", get_file_size(trashed))
        # because the obsolete file is moved to the trash.
        self.assertFalse(bucket_object_exists(obsolete))
