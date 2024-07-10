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

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """the handler gets the pdf request, and copy the dummy PDF to the destination"""
    def do_GET(self):
        pdf_req = re.match(r'^/pdf/(\d{4}\.\d{5}v\d+)(.pdf|)$', self.path)
        if pdf_req:
            paper_id = pdf_req.group(1)
            x_path = os.path.join(test_dir, "data", "x.pdf")
            pdf_path = os.path.join(sync_published_to_gcp.PS_CACHE_PREFIX, "arxiv", "pdf", "2308", f"{paper_id}.pdf")
            if not os.path.exists(pdf_path):
                shutil.copy(x_path, pdf_path)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html> <body> <h1>Hello, world!</h1> </body> </html>")
            return

        # 'http://localhost:12721/html/2308.99990v1'
        html_req = re.match(r'^/html/(\d{4}\.\d{5}v\d+)$', self.path)
        if html_req:
            paper_id = html_req.group(1)

            # PosixPath('/home/ntai/arxiv/arxiv-browse/script/sync_prod_to_gcp/test/cache/ps_cache/arxiv/html/2308/2308.99990v1')
            for suffix in [".html.gz", ".tar.gz"]:
                local_path = os.path.join(test_dir, "data", "ftp", "papers", "2308", f"{paper_id}{suffix}")
                if os.path.exists(local_path):
                    break
            else:
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                return

            html_path = os.path.join(sync_published_to_gcp.PS_CACHE_PREFIX, "arxiv", "html", "2308", os.path.basename(local_path))
            if not os.path.exists(html_path):
                os.makedirs(os.path.dirname(html_path), exist_ok=True)
                shutil.copy(local_path, html_path)
                pass
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


class TestSubscribeSumissions(unittest.TestCase):

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
                    "gs://arxiv-sync-test-01/trash/ftp/arxiv/papers/2308/2308.16188.pdf"
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
                logger.warning(
                    f"There is no associated files? xid: {state.xid.ids}",
                    extra=log_extra)

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
        self.assertEqual(get_file_size(f"gs://arxiv-sync-test-01/trash/ftp/arxiv/papers/2308/{paper_id}.pdf"), "1115014")

        # New submissions
        self.assertEqual(get_file_size(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.abs"), "9")
        self.assertEqual(get_file_size(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.tar.gz"), "141")


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
                logger.warning(
                    f"There is no associated files? xid: {state.xid.ids}",
                    extra=log_extra)

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
        self.assertEqual(get_file_size(f"gs://arxiv-sync-test-01/ps_cache/arxiv/pdf/2308/{paper_id}v1.pdf"), "1115014")

        # New submissions
        self.assertEqual(get_file_size(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.abs"), "9")
        self.assertEqual(get_file_size(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.tar.gz"), "141")


    def test_ask_html(self):
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
            desired_state = state.get_expected_files()
            if not desired_state:
                logger.warning(
                    f"There is no associated files? xid: {state.xid.ids}",
                    extra=log_extra)

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
        self.assertEqual(get_file_size(f"gs://arxiv-sync-test-01/ps_cache/arxiv/pdf/2308/{paper_id}v1.pdf"), "1115014")

        # New submissions
        self.assertEqual(get_file_size(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.abs"), "9")
        self.assertEqual(get_file_size(f"gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/{paper_id}.tar.gz"), "141")
