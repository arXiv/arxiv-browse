import os
import unittest
import argparse
from sync_published_to_gcp import main as sync_main
import pickle
import shutil
import json

class SyncTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('--test', help='test mode', action='store_true')
        self.parser.add_argument('--json-log-dir', help='Additional JSON logging', default='./json-log')
        self.parser.add_argument('-v', help='verbse', action='store_true')
        self.parser.add_argument('-d', help="Dry run no action", action='store_true')
        self.parser.add_argument('filename')
        if os.path.exists("./test/test-output"):
            shutil.rmtree("./test/test-output")
            pass
        os.makedirs("./test/test-output", exist_ok=True)
        pass


    def tearDown(self) -> None:
        #shutil.rmtree("./test/test-output")
        pass

    def test_json_log(self):
        args = self.parser.parse_args(["-d", "-v", "--test",
                                       "--json-log-dir",  "./test/test-output",
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



if __name__ == '__main__':
    unittest.main()
