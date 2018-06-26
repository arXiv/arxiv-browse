# from unittest import TestCase
import unittest

from hypothesis import given
from hypothesis.strategies import text

from browse.domain.clickthrough import create_hash, is_hash_valid


class TestClickthrough(unittest.TestCase):

    @given(text(), text())
    def test_clickthrough(self, s, v):
        h = create_hash(s, v)
        self.assertTrue(is_hash_valid(s, v, h))
