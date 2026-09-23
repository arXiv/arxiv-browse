"""retire_bucket_objects when the /orig destination already exists."""
import logging
import sys
import types
import unittest

try:
    import logging_json  # noqa: F401
except ImportError:  # only a log formatter; not needed to exercise the retire logic
    _stub = types.ModuleType('logging_json')
    _stub.JSONFormatter = logging.Formatter
    sys.modules['logging_json'] = _stub

from submissions_to_gcp import SyncVerdict, retire_bucket_objects


class FakeBlob:
    """Like google.cloud.storage.Blob: bucket.blob() has no metadata until reload()."""

    def __init__(self, store, name):
        self.store, self.name = store, name
        self.md5_hash = self.size = None

    def exists(self):
        return self.name in self.store

    def reload(self, projection=None):
        self.md5_hash, self.size = self.store[self.name]

    def delete(self):
        del self.store[self.name]


class FakeBucket:
    def __init__(self, store):
        self.store = store

    def blob(self, name):
        return FakeBlob(self.store, name)

    def copy_blob(self, *_args):
        raise AssertionError("must not copy when the destination exists")


class FakeClient:
    def __init__(self, bucket):
        self._bucket = bucket

    def bucket(self, _name):
        return self._bucket


class TestRetireExistingOrig(unittest.TestCase):
    FTP = 'ftp/arxiv/papers/2510/2510.02751.tar.gz'
    ORIG = 'orig/arxiv/papers/2510/2510.02751v1.tar.gz'

    def run_retire(self, store):
        verdict = SyncVerdict()
        retire_bucket_objects(FakeClient(FakeBucket(store)), [(self.FTP, self.ORIG, 'submission')], verdict, {})
        return verdict.verdicts[-1][1]

    def test_identical_destination_removes_ftp_copy(self):
        store = {self.FTP: ('v1md5==', 10), self.ORIG: ('v1md5==', 10)}
        self.assertEqual(self.run_retire(store), "Both Exists")
        self.assertEqual(store, {self.ORIG: ('v1md5==', 10)})

    def test_different_destination_is_left_alone(self):
        store = {self.FTP: ('v2md5==', 20), self.ORIG: ('v1md5==', 10)}
        self.assertEqual(self.run_retire(store), "Both exists but contents not the same!")
        self.assertEqual(store, {self.FTP: ('v2md5==', 20), self.ORIG: ('v1md5==', 10)})


if __name__ == '__main__':
    unittest.main()
