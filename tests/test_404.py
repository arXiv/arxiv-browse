import pytest
import unittest


@pytest.mark.usefixtures("unittest_add_fake")
class Test_404(unittest.TestCase):

    def test_it_should_be_404(self):
        rv = self.client.get('/abs?archive=foo&papernum=1234567')
        self.assertEqual(rv.status_code, 404)

        rv = self.client.get('/abs?0704.0600')
        self.assertEqual(rv.status_code, 404,
                         'singleton case for new IDs not supported')
