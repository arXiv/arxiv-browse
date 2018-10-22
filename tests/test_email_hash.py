import unittest

from hypothesis import given
from hypothesis.strategies import text

from browse.services.util.email import generate_show_email_hash


class TestEmailHash(unittest.TestCase):
    @given(text(), text(), text())
    def test_fuzz_email_hash(self, s, v, x):
        h = generate_show_email_hash(s, v)
        self.assertEqual(h, generate_show_email_hash(s, v))

        if h is None: return

        if v != s:
            if f'{v}/{s}' == f'{s}/{v}': return
            
            self.assertNotEqual(h,
                                generate_show_email_hash(v, s),
                                'the hash for (v,s) should not equal hash '
                                f'for (s,v) but it did for v:{v} s:{s}')
        if x != v:
            self.assertNotEqual(h, generate_show_email_hash(s, x),
                                'For some value x, hash(s,v) must not equal hash(s,x)'
                                f' but it did for x:{x} v:{v} and s:{s}')
        if x != s:
            self.assertNotEqual(h, generate_show_email_hash(x, v),
                                'For some value x, hash(s,v) must not equal hash(x,v)'
                                f' but it did for x:{x} v:{v} and s:{s}')
