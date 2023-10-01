import os
import subprocess
import unittest
import argparse
import pickle
import shutil
import json
from sync_published_to_gcp import main as sync_main

class SyncTestCase(unittest.TestCase):

    def setUp(self) -> None:
        # This isn't a goog idea, you know.
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('--test', help='test mode', action='store_true')
        self.parser.add_argument('--json-log-dir', help='Additional JSON logging', default='./json-log')
        self.parser.add_argument('-v', help='verbse', action='store_true')
        self.parser.add_argument('-d', help="Dry run no action", action='store_true')
        self.parser.add_argument('--prefix', help="FTP_PREFIX", default=None)
        self.parser.add_argument('--globals', help="Global variables")
        self.parser.add_argument('filename')
        if os.path.exists("test/test-output"):
            shutil.rmtree("test/test-output")
            pass
        os.makedirs("test/test-output", exist_ok=True)
        os.putenv("GOOGLE_APPLICATION_CREDENTIALS", "test/gcp-sync-test-role.json")
        self.overrides = repr({
            "GS_BUCKET": 'arxiv-sync-test-01',
            "GS_KEY_PREFIX": '/ps_cache',
            "CACHE_PREFIX": 'test/cache/',
            "PS_CACHE_PREFIX": 'test/cache/ps_cache/',
            "FTP_PREFIX": 'test/data/ftp/',
            "ORIG_PREFIX": 'test/data/orig/',
            "DATA_PREFIX": 'test/data/',
            "REUPLOADS": {'ftp/arxiv/papers/2308/2308.16189.abs': True}
        })
        rm_items = ["gsutil", "rm", "-a", "-f" ]
        droplets = ["gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/2308.16188.abs",
                    "gs://arxiv-sync-test-01/ftp/arxiv/papers/2308/2308.16188.tar.gz",
                    "gs://arxiv-sync-test-01/ps_cache/arxiv/pdf/2308/2308.16188v1.pdf"]
        subprocess.call(rm_items + droplets,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pass


    def tearDown(self) -> None:
        #shutil.rmtree("./test/test-output")
        pass

    def test_json_log(self):
        from sync_published_to_gcp import main as sync_main
        args = self.parser.parse_args(["-d", "-v", "--test",
                                       "--json-log-dir",  "./test/test-output",
                                       "--globals", self.overrides,
                                       "./test/data/publish_230901.log"])
        todos = sync_main(args)
        with open("./test/data/publish_230901.out.pickle", "wb") as outfd:
            pickle.dump(todos, outfd)
            pass
        with open("./test/data/publish_230901.expected.pickle", "rb") as expectfd:
            expected = pickle.load(expectfd)
            pass
        self.assertEqual(expected, todos)

        with open("./test/test-output/sync-to-gcp.log") as logfd:
            logs = logfd.readlines()
            pass
        actual = json.loads(logs[1])
        self.assertEqual("INFO", actual.get("level"))
        self.assertEqual("Dry run no changes made", actual.get("message"))
        self.assertEqual(1285, actual.get("todos"))

        success_log = json.loads(logs[2])
        self.assertEqual("1234", success_log.get("paper_id"))
        self.assertEqual("upload", success_log.get("action"))
        self.assertEqual("summary", success_log.get("category"))
        self.assertEqual("already_on_gs", success_log.get("outcome"))

        failure_log = json.loads(logs[3])
        self.assertEqual("WARNING", failure_log.get("level"))
        self.assertEqual("5678", failure_log.get("paper_id"))
        self.assertEqual("failed", failure_log.get("action"))
        self.assertEqual("summary", failure_log.get("category"))

        pass


    def test_sync(self):
        args = self.parser.parse_args(["-v",
                                       "--json-log-dir=./test/test-output",
                                       "--globals", self.overrides,
                                       "./test/data/publish_test.log"])
        todos = sync_main(args)
        with open("./test/test-output/sync-to-gcp.log") as logfd:
            logs = [json.loads(line) for line in logfd.readlines()]
            pass

        levels = {}
        for log in logs:
            if log.get("level") not in levels:
                levels[log.get("level")] = [log]
            else:
                levels[log.get("level")].append(log)
                pass
            pass

        self.assertEqual(2, len(levels["ERROR"]))
        for an_error in levels["ERROR"]:
            self.assertEqual("2308.16189", an_error.get("paper_id"))
            self.assertEqual("upload", an_error.get("action"))
            self.assertEqual("upload", an_error.get("category"))
            the_ex = an_error.get("exception")
            if an_error.get("item") == "test/data/ftp/arxiv/papers/2308/2308.16189.abs":
                self.assertEqual("Forbidden", the_ex.get("type"))
                pass
            elif an_error.get("item") == "test/data/ftp/arxiv/papers/2308/2308.16189.gz":
                self.assertEqual("FileNotFoundError", the_ex.get("type"))
                pass
            else:
                self.fail(f"Unexpected item " + repr(an_error.get("item")))
                pass
            pass
        self.assertEqual(2, len(levels["WARNING"]))

        pass



if __name__ == '__main__':
    unittest.main()
