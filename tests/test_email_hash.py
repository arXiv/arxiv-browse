import unittest

from hypothesis import given
from hypothesis.strategies import text

from browse.services.util.email import generate_show_email_hash


class TestEmailHAsh(unittest.TestCase):

    @given(text(), text(), text())
    def test_fuzz_email_hash(self, s, v, x):
        h = generate_show_email_hash(s, v)
        self.assertEqual(h, generate_show_email_hash(s, v))

        if h is not None:
            if v != s:
                self.assertNotEqual(h, generate_show_email_hash(v, s))
            if x != v:
                self.assertNotEqual(h, generate_show_email_hash(s, x))
            if x != s:
                self.assertNotEqual(h, generate_show_email_hash(x, v))
