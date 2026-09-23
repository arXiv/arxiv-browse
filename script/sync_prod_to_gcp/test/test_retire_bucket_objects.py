"""retire_bucket_objects must not archive a /ftp object that is no longer the retired version."""
import logging
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

try:
    import logging_json  # noqa: F401
except ImportError:  # only a log formatter; not needed to exercise the retire logic
    _stub = types.ModuleType('logging_json')
    _stub.JSONFormatter = logging.Formatter
    sys.modules['logging_json'] = _stub

import submissions_to_gcp
from submissions_to_gcp import SyncVerdict, md5_base64, retire_bucket_objects


class FakeBlob:
    def __init__(self, store, name):
        self.store, self.name = store, name

    def exists(self):
        return self.name in self.store

    def reload(self, projection=None):
        pass

    @property
    def md5_hash(self):
        return self.store.get(self.name)

    @property
    def size(self):
        return 0

    def delete(self):
        del self.store[self.name]


class FakeBucket:
    def __init__(self, store):
        self.store = store
        self.copies = []

    def blob(self, name):
        return FakeBlob(self.store, name)

    def copy_blob(self, from_blob, _bucket, to_obj):
        self.copies.append((from_blob.name, to_obj))
        self.store[to_obj] = self.store[from_blob.name]
        return FakeBlob(self.store, to_obj)


class FakeClient:
    def __init__(self, bucket):
        self._bucket = bucket

    def bucket(self, _name):
        return self._bucket


class TestRetireBucketObjects(unittest.TestCase):
    FTP = 'ftp/arxiv/papers/2510/2510.02751.tar.gz'
    ORIG = 'orig/arxiv/papers/2510/2510.02751v1.tar.gz'

    def setUp(self):
        fd, self.cit_v1 = tempfile.mkstemp(suffix='.tar.gz')
        with os.fdopen(fd, 'wb') as fh:
            fh.write(b'version 1 bundle')
        self.addCleanup(os.remove, self.cit_v1)
        self.v1_md5 = md5_base64(self.cit_v1)

    def run_retire(self, ftp_md5):
        store = {self.FTP: ftp_md5}
        bucket = FakeBucket(store)
        uploads = []

        def fake_upload(_client, localpath, key, upload_logger=None):
            uploads.append((str(localpath), key))
            store[key] = md5_base64(str(localpath))

        with patch.object(submissions_to_gcp, 'upload', fake_upload):
            retire_bucket_objects(FakeClient(bucket), [(self.FTP, self.ORIG, 'submission', self.cit_v1)],
                                  SyncVerdict(), {})
        return store, bucket.copies, uploads

    def test_ftp_still_retired_version_is_moved(self):
        store, copies, uploads = self.run_retire(self.v1_md5)
        self.assertEqual(copies, [(self.FTP, self.ORIG)])
        self.assertEqual(uploads, [])
        self.assertEqual(store, {self.ORIG: self.v1_md5})

    def test_ftp_already_new_version_uploads_retired_from_cit(self):
        # 2510.02751 on 2026-09-23: an admin restore synced the fixed v2 to /ftp before
        # the delayed publish sync retired v1, which then copied v2 into orig/...v1.
        store, copies, uploads = self.run_retire('md5-of-the-new-v2==')
        self.assertEqual(copies, [])
        self.assertEqual(uploads, [(self.cit_v1, self.ORIG)])
        self.assertEqual(store, {self.ORIG: self.v1_md5})


if __name__ == '__main__':
    unittest.main()
