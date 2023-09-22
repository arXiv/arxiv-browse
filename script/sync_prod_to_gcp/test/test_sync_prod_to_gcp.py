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
        os.makedirs("./test/test-output")
        pass


    def tearDown(self) -> None:
        shutil.rmtree("./test/test-output")
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
            second = logfd.readlines()[1]
            actual = json.loads(second)
            pass
        self.assertEqual("INFO", actual.get("level"))
        self.assertEqual("Dry run no changes made", actual.get("message"))
        self.assertEqual(1285, actual.get("todos"))
        pass



if __name__ == '__main__':
    unittest.main()
