"""test cookies"""
import unittest

from app import app


#from bs4 import BeautifulSoup



class CookiesPageTest(unittest.TestCase):

    def setUp(self):
        app.testing = True
        app.config['APPLICATION_ROOT'] = ''
        self.app = app.test_client()


    def test_cookies_with_no_params(self):
        """Test the cookies page."""
        rv = self.app.get('/cookies')
        self.assertEqual(rv.status_code, 200)
        html = rv.data.decode('utf-8')
        self.assertIn('Select preferred download format', html)
        self.assertIn('show additional debugging information', html, 'should have SHOW debugging link')

    def test_cookies_with_debug(self):
        """Test the cookies page."""
        rv = self.app.get('/cookies?debug=1')
        self.assertEqual(rv.status_code, 200)
        html = rv.data.decode('utf-8')
        self.assertIn('Select preferred download format', html)
        self.assertIn('hide debugging information', html, 'should have HIDE debugging link')

    def test_post_to_cookies(self):
        rv = self.app.post('/cookies/set?debug=1', data={'ps':'pdf'})
        self.assertEqual(rv.status_code, 302)
        cookies =  map(lambda kv: kv[1], filter(lambda kv : kv[0]=='Set-Cookie', rv.headers.items()))
        self.assertIn('xxx-ps-defaults=pdf; Path=/', cookies)
