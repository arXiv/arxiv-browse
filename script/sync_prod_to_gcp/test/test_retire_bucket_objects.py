"""retire_bucket_objects must leave CIT's copy of the retired version in /orig."""
import os
import tempfile
import unittest
from unittest.mock import patch

import submissions_to_gcp
from submissions_to_gcp import SyncVerdict, md5_base64, retire_bucket_objects


class FakeBlob:
    """Like google.cloud.storage.Blob: bucket.blob() has no md5_hash, bucket.get_blob() does."""

    def __init__(self, store, name, md5_hash=None):
        self.store, self.name, self.md5_hash = store, name, md5_hash

    def delete(self):
        del self.store[self.name]


class FakeBucket:
    def __init__(self, store):
        self.store = store
        self.copies = []

    def blob(self, name):
        return FakeBlob(self.store, name)

    def get_blob(self, name):
        return FakeBlob(self.store, name, self.store[name]) if name in self.store else None

    def copy_blob(self, from_blob, _bucket, to_obj):
        self.copies.append((from_blob.name, to_obj))
        self.store[to_obj] = self.store[from_blob.name]
        return FakeBlob(self.store, to_obj, self.store[to_obj])


class FakeClient:
    def __init__(self, bucket):
        self._bucket = bucket

    def bucket(self, _name):
        return self._bucket


class TestRetireBucketObjects(unittest.TestCase):
    FTP = 'ftp/arxiv/papers/2510/2510.02751.tar.gz'
    ORIG = 'orig/arxiv/papers/2510/2510.02751v1.tar.gz'
    V2 = 'md5-of-the-new-v2=='

    def setUp(self):
        fd, self.cit_v1 = tempfile.mkstemp(suffix='.tar.gz')
        with os.fdopen(fd, 'wb') as fh:
            fh.write(b'version 1 bundle')
        self.addCleanup(os.remove, self.cit_v1)
        self.V1 = md5_base64(self.cit_v1)

    def run_retire(self, store, cit_path=None, upload_error=None):
        bucket = FakeBucket(store)
        uploads = []

        def fake_upload(_client, localpath, key, upload_logger=None):
            if upload_error:
                raise upload_error
            uploads.append((str(localpath), key))
            store[key] = md5_base64(str(localpath))

        verdict = SyncVerdict()
        with patch.object(submissions_to_gcp, 'upload', fake_upload):
            retire_bucket_objects(FakeClient(bucket), [(self.FTP, self.ORIG, 'submission', cit_path or self.cit_v1)],
                                  verdict, {})
        return bucket.copies, uploads, verdict

    def test_ftp_still_retired_version_is_moved(self):
        store = {self.FTP: self.V1}
        copies, uploads, verdict = self.run_retire(store)
        self.assertEqual((copies, uploads), ([(self.FTP, self.ORIG)], []))
        self.assertEqual(store, {self.ORIG: self.V1})
        self.assertTrue(verdict.good())

    def test_ftp_already_new_version_uploads_retired_from_cit(self):
        # 2510.02751 on 2026-09-23: an admin restore synced the fixed v2 to /ftp before
        # the delayed publish sync retired v1, which then copied v2 into orig/...v1.
        store = {self.FTP: self.V2}
        copies, uploads, verdict = self.run_retire(store)
        self.assertEqual((copies, uploads), ([], [(self.cit_v1, self.ORIG)]))
        self.assertEqual(store, {self.FTP: self.V2, self.ORIG: self.V1})
        self.assertTrue(verdict.good())

    def test_redelivery_removes_leftover_ftp_copy(self):
        store = {self.FTP: self.V1, self.ORIG: self.V1}
        copies, uploads, verdict = self.run_retire(store)
        self.assertEqual((copies, uploads), ([], []))
        self.assertEqual(store, {self.ORIG: self.V1})
        self.assertEqual(verdict.verdicts[-1][1], "Destination Exists")

    def test_wrong_orig_is_repaired_and_current_ftp_kept(self):
        # The state the blind copy left behind: /orig/...v1 and /ftp both hold v2.
        store = {self.FTP: self.V2, self.ORIG: self.V2}
        copies, uploads, verdict = self.run_retire(store)
        self.assertEqual((copies, uploads), ([], [(self.cit_v1, self.ORIG)]))
        self.assertEqual(store, {self.FTP: self.V2, self.ORIG: self.V1})
        self.assertTrue(verdict.good())

    def test_without_cit_copy_falls_back_to_moving_ftp(self):
        store = {self.FTP: self.V2}
        copies, uploads, verdict = self.run_retire(store, cit_path='/nonexistent/2510.02751v1.tar.gz')
        self.assertEqual((copies, uploads), ([(self.FTP, self.ORIG)], []))
        self.assertEqual(store, {self.ORIG: self.V2})
        self.assertTrue(verdict.good())

    def test_failed_upload_is_a_bad_verdict(self):
        store = {self.FTP: self.V2}
        _copies, _uploads, verdict = self.run_retire(store, upload_error=OSError("upload failed"))
        self.assertFalse(verdict.good())
        self.assertEqual(store, {self.FTP: self.V2})


if __name__ == '__main__':
    unittest.main()
