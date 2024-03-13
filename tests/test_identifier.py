"""Tests for arXiv identifier class Identifier."""
from unittest import TestCase

from arxiv.identifier import Identifier


class TestIdentifier(TestCase):
    """Tests for the ArXivIdentifier class."""

    def test_identifier_fields(self) -> None:
        """Test individual fields in Identifier object."""
        tid1 = Identifier(arxiv_id='0803.1924')
        self.assertIsInstance(tid1, Identifier, 'valid instance')
        self.assertIsNotNone(tid1.id, 'id is not None')
        self.assertIs(tid1.is_old_id, False, 'id is new type')
        self.assertEqual(tid1.archive, 'arxiv', 'archive is arxiv for new ID')
        self.assertEqual(tid1.yymm, '0803', 'yymm matches')
        self.assertEqual(tid1.year, 2008, 'year matches')
        self.assertEqual(tid1.month, 3, 'month matches')
        self.assertEqual(tid1.num, 1924, 'numerical id matches')
        self.assertEqual(tid1.id, '0803.1924', 'id matches')
        self.assertEqual(tid1.ids, '0803.1924', 'id specified matches')
        self.assertEqual(tid1.filename, '0803.1924', 'filename matches')
        self.assertEqual(tid1.squashed, '0803.1924', 'squashed id matches')
        self.assertEqual(tid1.squashedv, '0803.1924', 'squashed idv matches')
        # tid1_next = tid1.next_id()
        # self.assertIsInstance(tid1_next, Identifier)
        # self.assertEqual(tid1_next.id, '0803.1925', 'next id matches')

        tid2 = Identifier(arxiv_id='hep-th/0701051v4')
        self.assertIsInstance(tid2, Identifier, 'valid instance')
        self.assertIsNotNone(tid2.id, 'id is not None')
        self.assertIs(tid2.is_old_id, True, 'id is old type')
        self.assertEqual(tid2.archive, 'hep-th',
                         'archive is hep-th for old ID')
        self.assertEqual(tid2.yymm, '0701', 'yymm matches')
        self.assertEqual(tid2.year, 2007, 'year matches')
        self.assertEqual(tid2.month, 1, 'month matches')
        self.assertEqual(tid2.num, 51, 'numerical id matches')
        self.assertEqual(tid2.id, 'hep-th/0701051', 'id matches')
        self.assertEqual(tid2.ids, 'hep-th/0701051v4', 'id specified matches')
        self.assertEqual(tid2.filename, '0701051', 'filename matches')
        self.assertEqual(tid2.squashed, 'hep-th0701051', 'squashed id matches')
        self.assertEqual(tid2.squashedv, 'hep-th0701051v4',
                         'squashed idv matches')
        # tid2_next = tid2.next_id()
        # self.assertIsInstance(tid2_next, Identifier)
        # self.assertEqual(tid2_next.id, 'hep-th/0701052', 'next id matches')

        tid3 = Identifier(arxiv_id='1201.0001')
        self.assertIsInstance(tid3, Identifier, 'valid instance')
        self.assertIsNotNone(tid3.id, 'id is not None')
        self.assertIs(tid3.is_old_id, False, 'id is new type')
        self.assertEqual(tid3.yymm, '1201', 'yymm matches')
        self.assertEqual(tid3.year, 2012, 'year matches')
        self.assertEqual(tid3.month, 1, 'month matches')
        self.assertEqual(tid3.num, 1, 'numerical id matches')
        self.assertEqual(tid3.id, '1201.0001', 'id matches')
        self.assertEqual(tid3.ids, '1201.0001', 'id specified matches')
        self.assertEqual(tid3.filename, '1201.0001', 'filename matches')
        self.assertEqual(tid3.squashed, '1201.0001', 'squashed id matches')
        self.assertEqual(tid3.squashedv, '1201.0001',
                         'squashed idv matches')
        # tid3_next = tid3.next_id()
        # self.assertIsInstance(tid3_next, Identifier)
        # self.assertEqual(tid3_next.id, '1201.0002')

    def test_bad_identifiers(self) -> None:
        """Test known bad identifiers."""
        bad_ids = ('BAD_ID', 'hep-th/990100', 'hep-th/99010011', '0703.123',
                   '0703.123456', '', '/', '0713.0001', '0800.0001'
                   # ids ending 000 or .0000+ are not valid
                   'quant-ph/9409000', '0704.0000',
                   # other bad ids with different lengths of numbers
                   'quant-ph/940900', 'quant-ph/94090000', 'quant-ph/94091',
                   'quant-ph/940912',
                   # P10k - add 123456 test
                   'quant-ph/94091234', '0707.000', '0707.00000', '0707.1',
                   '0707.12', '0707.123', '0707.123456',
                   # double numbers (google makes these up?)
                   '0705.35950705.3595v1/', 'arxiv:0705.35950705.3595v1/',
                   # non-numeric version
                   '0707.2096va', '0707.2096va/',
                   # pre-new-id
                   '0612.1234', '0612.1234'
                   '0703.1234', '0703.1234',
                   )

        for bad_id in bad_ids:
            with self.assertRaises(
                    Exception,
                    msg=f'{bad_id} is an invalid identifier') as context:
                Identifier(arxiv_id=bad_id)

            self.assertIn('invalid arXiv identifier', str(context.exception))

    def test_good_identifiers(self) -> None:
        """Test known good identifiers."""
        good_ids = {
            'hep-th/9901001': 'hep-th/9901001',
            '/hep-th/0702050':  'hep-th/0702050',
            '/hep-th/0702050v1':  'hep-th/0702050',
            '/0708.1234':  '0708.1234',
            '/0708.1234v1':  '0708.1234',
            'hep-th//9901001': 'hep-th/9901001',
            'hep-th///9901001': 'hep-th/9901001',
            'arxiv:hep-th/9901001': 'hep-th/9901001',
            'hep-th/9901001/extra': 'hep-th/9901001',
            'hep-th/9901001/ExTrA': 'hep-th/9901001',
            'HEP-TH/9901001/extra': 'hep-th/9901001',
            'HEP-TH/9901001/ExTrA': 'hep-th/9901001',
            '0704.0001': '0704.0001'
        }
        for provided_id, good_id in good_ids.items():
            gid = Identifier(arxiv_id=provided_id)
            self.assertIsInstance(gid, Identifier, 'valid instance')
            self.assertEqual(gid.id, good_id)
            self.assertEqual(gid.ids, provided_id)

    # def test_next_previous_id(self):
    #     """Test next/previous consecutive identifier."""
    #
    #     tid1 = Identifier(arxiv_id='0704.0001')
    #     self.assertIsInstance(tid1, Identifier, 'valid instance')
    #     tid1_next = tid1.next_id()
    #     self.assertIsInstance(tid1_next, Identifier, 'valid instance')
    #     self.assertEqual(tid1_next.id, '0704.0002')
    #     tid1_prev = tid1.previous_id()
    #     self.assertIsNone(tid1_prev, 'previous is none')
    #     tid1_next_prev = tid1_next.previous_id()
    #     self.assertIsInstance(tid1_next_prev, Identifier, 'valid instance')
    #     self.assertEqual(tid1, tid1_next_prev)
    #
    #     tid2 = Identifier(arxiv_id='0705.0001')
    #     self.assertIsInstance(tid2, Identifier, 'valid instance')
    #     tid2_next = tid2.next_id()
    #     self.assertIsInstance(tid2_next, Identifier, 'valid instance')
    #     self.assertEqual(tid2_next.id, '0705.0002')
    #     tid2_prev = tid2.previous_id()
    #     self.assertIsInstance(tid2_prev, Identifier, 'valid instance')
    #     self.assertEqual(tid2_prev.id, '0704.9999')
    #     tid2_prev_next = tid2_prev.next_id()
    #     self.assertIsInstance(tid2_prev_next, Identifier, 'valid instance')
    #     self.assertEqual(tid2, tid2_prev_next)
    #
    #     tid3 = Identifier(arxiv_id='1412.9999')
    #     self.assertIsInstance(tid3, Identifier, 'valid instance')
    #     tid3_next = tid3.next_id()
    #     self.assertIsInstance(tid3_next, Identifier, 'valid instance')
    #     self.assertEqual(tid3_next.id, '1501.00001')
    #     tid3_prev = tid3.previous_id()
    #     self.assertIsInstance(tid3_prev, Identifier, 'valid instance')
    #     self.assertEqual(tid3_prev.id, '1412.9998')
    #     tid3_next_prev = tid3_next.previous_id()
    #     self.assertIsInstance(tid3_next_prev, Identifier, 'valid instance')
    #     self.assertEqual(tid3_next_prev, tid3)
    #
    #     tid4 = Identifier(arxiv_id='alg-geom/9912999')
    #     self.assertIsInstance(tid4, Identifier, 'valid instance')
    #     tid4_next = tid4.next_id()
    #     self.assertIsInstance(tid4_next, Identifier, 'valid instance')
    #     self.assertEqual(tid4_next.id, 'alg-geom/0001001')
    #     tid4_next_prev = tid4_next.previous_id()
    #     self.assertIsInstance(tid4_next_prev, Identifier, 'valid instance')
    #     self.assertEqual(tid4_next_prev, tid4)
