"""Tests for arXiv abstract (.abs) parser."""
import os
from datetime import datetime
from unittest import TestCase

from dateutil.tz import tzutc
from browse.domain.metadata import DocMetadata, Submitter
from browse.domain.version import VersionEntry, SourceFlag

from browse.services.documents.fs_implementation.parse_abs import parse_abs_file
from tests import path_of_for_test

ABS_FILES = path_of_for_test('data/abs_files')


class TestAbsParser(TestCase):
    """Test  parsing metadata from .abs files."""

    def test_bulk_parsing(self):
        """Parse all nonempty .abs files in test set."""
        num_files_tested = 0
        from_regex = r'(?m)From:\s+[^<]+<[^@]+@[^>]+>'
        self.assertRegex('From: J Doe <jdoe@example.org>', from_regex)
        for dir_name, subdir_list, file_list in os.walk(ABS_FILES):
            for fname in file_list:
                fname_path = os.path.join(dir_name, fname)
                # skip any empty files
                if os.stat(fname_path).st_size == 0:
                    continue
                if not fname_path.endswith('.abs'):
                    continue
                num_files_tested += 1
                dm = parse_abs_file(filename=fname_path)
                self.assertIsInstance(dm, DocMetadata)
                self.assertNotEqual(dm.license, None)
                self.assertNotEqual(dm.license.effective_uri, None,
                                    'should have an effectiveLicenseUri')
                self.assertRegex(dm.raw_safe,
                                 r'(?m)From:\s+',
                                 'has a From: line')
                self.assertNotRegex(dm.raw_safe,
                                    from_regex,
                                    'has a From: line but no email')
        # our test set should be sufficiently large
        self.assertGreater(num_files_tested, 1_000, 'comprehensive dataset')

    def test_individual_files(self):
        """Test individual .abs files."""
        f1 = ABS_FILES + '/orig/arxiv/papers/0906/0906.5132v3.abs'
        ams = parse_abs_file(filename=f1)

        self.assertIsInstance(ams, DocMetadata)
        self.assertEqual(ams.arxiv_id, '0906.5132', 'arxiv_id')
        self.assertEqual(
            ams.submitter,
            Submitter(
                name='Vladimir P. Mineev',
                email='WTUwTuyJ.Owwldw@sOD.n4'
            )
        )
        self.assertListEqual(
            ams.version_history,
            [
                VersionEntry(
                    version=1,
                    raw='Date: Sun, 28 Jun 2009 11:24:35 GMT   (17kb)',
                    submitted_date=datetime(2009, 6, 28, 11, 24, 35,
                                            tzinfo=tzutc()),
                    size_kilobytes=17,
                    source_flag=SourceFlag(code='')
                ),
                VersionEntry(
                    version=2,
                    raw='Date (revised v2): Tue, 21 Jul '
                        '2009 09:45:44 GMT   (17kb)',
                    submitted_date=datetime(2009, 7, 21, 9, 45, 44,
                                            tzinfo=tzutc()),
                    size_kilobytes=17,
                    source_flag=SourceFlag(code='')
                ),
                VersionEntry(
                    version=3,
                    raw='Date (revised v3): Wed, 29 Jul '
                        '2009 11:13:43 GMT   (17kb)',
                    submitted_date=datetime(2009, 7, 29, 11, 13, 43,
                                            tzinfo=tzutc()),
                    size_kilobytes=17,
                    source_flag=SourceFlag(code='')
                )
            ]
        )
        self.assertEqual(ams.version, 3)
        self.assertEqual(ams.title, 'Recent developments in unconventional '
                                    'superconductivity theory')
        self.assertEqual(str(ams.authors), 'V.P.Mineev')
        self.assertEqual(ams.categories, 'cond-mat.supr-con cond-mat.mtrl-sci')
        self.assertEqual(ams.comments, '15 pages')
        self.assertNotEqual(ams.license, None)
        self.assertEqual(
            ams.license.effective_uri,
            'http://arxiv.org/licenses/nonexclusive-distrib/1.0/'
        )
        self.assertMultiLineEqual(
            ams.abstract,
            '''  The review of recent developments in the unconventional superconductivity
theory is given. In the fist part I consider the physical origin of the Kerr
rotation polarization of light reflected from the surface of superconducting
$Sr_2RuO_4$. Then the comparison of magneto-optical responses in
superconductors with orbital and spin spontaneous magnetization is presented.
The latter result is applied to the estimation of the magneto-optical
properties of neutral superfluids with spontaneous magnetization. The second
part is devoted to the natural optical activity or gyrotropy properties of
noncentrosymmetric metals in their normal and superconducting states. The
temperature behavior of the gyrotropy coefficient is compared with the
temperature behavior of paramagnetic susceptibility determining the noticeable
increase of the paramagnetic limiting field in noncentrosymmetric
superconductors. In the last chapter I describe the order parameter and the
symmetry of superconducting state in the itinerant ferromagnet with
orthorhombic symmetry. Finally the Josephson coupling between two adjacent
ferromagnet superconducting domains is discussed.
'''
        )
        for value in [ams.acm_class, ams.doi, ams.journal_ref, ams.report_num,
                      ams.proxy]:
            self.assertIsNone(value)

    def test_subsumed_category(self):
        """Test individual .abs files."""
        f1 = ABS_FILES + '/ftp/adap-org/papers/9303/9303001.abs'
        m = parse_abs_file(filename=f1)
        self.assertIsInstance(m, DocMetadata)
        self.assertEqual('adap-org/9303001', m.arxiv_id, 'arxiv_id')

        self.assertTrue(m.primary_category)
        self.assertTrue(m.primary_category.canonical,
                        'subsumed category adap-org should have a canonical')

    def test_psi_in_abs(self):
        """Test text in abs ARXIVNG-1612"""
        f1 = ABS_FILES + '/ftp/arxiv/papers/1901/1901.05426.abs'
        m = parse_abs_file(filename=f1)
        self.assertIsInstance(m, DocMetadata)
        self.assertNotIn('$φ$', m.abstract,
                         'TeX psi in abstract should not get converted to UTF8')
