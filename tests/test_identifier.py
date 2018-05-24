"""Tests for arXiv identifier class Identifier."""
from unittest import TestCase
from browse.domain.identifier import Identifier


class TestIdentifier(TestCase):
    """Tests for the ArXivIdentifier class."""

    def test_identifier_fields(self):
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

    def test_bad_identifiers(self):
        """Test known bad identifiers."""
        bad_ids = ('BAD_ID', 'hep-th/990100', 'hep-th/99010011', '0703.123',
                   '0703.123456', '', '/',
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
                   '0707.2096va', '0707.2096va/'
                   )

        for bad_id in bad_ids:
            with self.assertRaises(
                    Exception,
                    msg=f'{bad_id} is an invalid identifier') as context:
                Identifier(arxiv_id=bad_id)

            self.assertIn('invalid arXiv identifier', str(context.exception))

    def test_good_identifiers(self):
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
        }
        for provided_id, good_id in good_ids.items():
            gid = Identifier(arxiv_id=provided_id)
            self.assertIsInstance(gid, Identifier, 'valid instance')
            self.assertEqual(gid.id, good_id)
            self.assertEqual(gid.ids, provided_id)
