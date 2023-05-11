import unittest

from app import app


class Check_2103_11058_Test(unittest.TestCase):

    def setUp(self):
        app.testing = True
        app.config['APPLICATION_ROOT'] = ''
        self.app = app.test_client()

    def test_2103_11058(self):
        id = '2103.11058'
        rv = self.app.get('/abs/' + id)
        self.assertEqual(rv.status_code, 200)
