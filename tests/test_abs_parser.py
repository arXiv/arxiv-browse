"""Tests for arXiv abstract (.abs) parser."""
import os
from unittest import TestCase
from datetime import datetime
from dateutil.tz import tzutc
from browse.domain.metadata import DocMetadata, Submitter, SourceType, \
    VersionEntry
from browse.services.document.metadata import AbsMetaSession

ABS_FILES = 'tests/data/abs_files'


class TestAbsParser(TestCase):
    """Test  parsing metadata from .abs files."""

    def test_bulk_parsing(self):
        """Parse all nonempty .abs files in test set."""
        num_files_tested = 0
        for dir_name, subdir_list, file_list in os.walk(ABS_FILES):
            for fname in file_list:
                fname_path = os.path.join(dir_name, fname)
                # skip any empty files
                if os.stat(fname_path).st_size == 0:
                    continue
                if not fname_path.endswith('.abs'):
                    continue
                num_files_tested += 1
                m = AbsMetaSession.parse_abs_file(filename=fname_path)
                self.assertIsInstance(m, DocMetadata)
                self.assertNotEqual(m.license, None)
                self.assertNotEqual(m.license.effectiveLicenseUri, None,
                                    'sould have an effectiveLicenseUri')
                # self.assertTrue(m.initialized, 'instance initialized')

        # our test set should be sufficiently large
        self.assertGreater(num_files_tested, 1_000, 'comprehensive dataset')

    def test_individual_files(self):
        """Test individual .abs files."""
        f1 = ABS_FILES + '/orig/arxiv/papers/0906/0906.5132v3.abs'
        m = AbsMetaSession.parse_abs_file(filename=f1)

        self.assertIsInstance(m, DocMetadata)
        self.assertEqual(m.arxiv_id, '0906.5132', 'arxiv_id')
        self.assertEqual(
            m.submitter,
            Submitter(
                name='Vladimir P. Mineev',
                email='***REMOVED***'
            )
        )
        self.assertListEqual(
            m.version_history,
            [
                VersionEntry(
                    version=1,
                    raw='Date: Sun, 28 Jun 2009 11:24:35 GMT   (17kb)',
                    submitted_date=datetime(2009, 6, 28, 11, 24, 35,
                                            tzinfo=tzutc()),
                    size_kilobytes=17,
                    source_type=SourceType(code='')
                ),
                VersionEntry(
                    version=2,
                    raw='Date (revised v2): Tue, 21 Jul '
                        '2009 09:45:44 GMT   (17kb)',
                    submitted_date=datetime(2009, 7, 21, 9, 45, 44,
                                            tzinfo=tzutc()),
                    size_kilobytes=17,
                    source_type=SourceType(code='')
                ),
                VersionEntry(
                    version=3,
                    raw='Date (revised v3): Wed, 29 Jul '
                        '2009 11:13:43 GMT   (17kb)',
                    submitted_date=datetime(2009, 7, 29, 11, 13, 43,
                                            tzinfo=tzutc()),
                    size_kilobytes=17,
                    source_type=SourceType(code='')
                )
            ]
        )
        self.assertEqual(m.version, 3)
        self.assertEqual(m.title, 'Recent developments in unconventional '
                                  'superconductivity theory')
        self.assertEqual(m.authors, 'V.P.Mineev')
        self.assertEqual(m.categories, 'cond-mat.supr-con cond-mat.mtrl-sci')
        self.assertEqual(m.comments, '15 pages')
        self.assertNotEqual(m.license, None)
        self.assertEqual(
            m.license.effectiveLicenseUri,
            'http://arxiv.org/licenses/nonexclusive-distrib/1.0/'
        )
        self.assertMultiLineEqual(
            m.abstract,
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
        for value in [m.acm_class, m.doi, m.journal_ref, m.report_num,
                      m.proxy]:
            self.assertIsNone(value)
