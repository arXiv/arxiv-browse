import unittest

from app import app

class ListPageTest(unittest.TestCase):
    def setUp(self):
        app.testing = True
        app.config['APPLICATION_ROOT'] = ''
        self.app = app
        self.client = app.test_client()

    def test_not_modified(self):
        with self.app.app_context():
            rv = self.client.get('/abs/0704.0600')
            self.assertEqual(rv.status_code, 200)

            last_mod = rv.headers['Last-Modified']
            etag = rv.headers['ETag']
            rv = self.client.get('/abs/0704.0600',
                                 headers={'If-Modified-Since': last_mod})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'if-modified-since': last_mod})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'IF-MODIFIED-SINCE': last_mod})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'If-ModiFIED-SiNCE': last_mod})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'If-None-Match': etag})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'if-none-match': etag})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'IF-NONE-MATCH': etag})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'iF-NoNE-MaTCH': etag})
            self.assertEqual(rv.status_code, 304)
            
