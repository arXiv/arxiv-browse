import unittest
import logging 

from app import app
 
class It_Should_be_404_Test(unittest.TestCase):
    
    def setUp(self):
        """Disable logging to avoid messy output during testing"""
        import logging
        wlog = logging.getLogger('werkzeug')
        wlog.disabled = True

        app.testing = True
        app.config['APPLICATION_ROOT'] = ''
        self.app = app.test_client()

    def test_its_should_be_404(self):
        rv = self.app.get('/abs?archive=foo&papernum=1234567')
        self.assertEqual(rv.status_code, 404)

        rv = self.app.get('/abs?0704.0600')
        self.assertEqual(rv.status_code, 404,
                         'singleton case for new IDs not supported')

