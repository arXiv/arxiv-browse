import unittest

from tests.test_fs_abs_parser import ABS_FILES
from browse.services.documents.fs_implementation.fs_abs import FsDocMetadataService

from arxiv.taxonomy.category import Category
from arxiv.files.object_store import LocalObjectStore


class CategoriesTest(unittest.TestCase):

    def setUp(self):
        self.absService = FsDocMetadataService(LocalObjectStore(ABS_FILES))

    def test_categories_for_0906_3421v1_cats(self):
        (id, primary, secondaries) = ('0906.3421v1', 'Combinatorics (math.CO)',
                                      ['Statistical Mechanics (cond-mat.stat-mech)', 'Mathematical Physics (math-ph)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0906_3421_cats(self):
        (id, primary, secondaries) = ('0906.3421', 'Combinatorics (math.CO)',
                                      ['Statistical Mechanics (cond-mat.stat-mech)', 'Mathematical Physics (math-ph)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0129_cats(self):
        (id, primary, secondaries) = ('0704.0129', 'Dynamical Systems (math.DS)',
                                      ['Mathematical Physics (math-ph)', 'Analysis of PDEs (math.AP)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0914_cats(self):
        (id, primary, secondaries) = ('0704.0914', 'Analysis of PDEs (math.AP)',
                                      ['Mathematical Physics (math-ph)', 'Optics (physics.optics)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0582_cats(self):
        (id, primary, secondaries) = ('0704.0582',
                                      'Probability (math.PR)', ['Mathematical Physics (math-ph)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0495_cats(self):
        (id, primary, secondaries) = ('0704.0495', 'Quantum Physics (quant-ph)',
                                      ['Mathematical Physics (math-ph)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0681_cats(self):
        (id, primary, secondaries) = ('0704.0681', 'Soft Condensed Matter (cond-mat.soft)',
                                      ['Statistical Mechanics (cond-mat.stat-mech)', 'Instrumentation and Detectors (physics.ins-det)', 'Optics (physics.optics)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0761_cats(self):
        (id, primary, secondaries) = ('0704.0761', 'Statistical Mechanics (cond-mat.stat-mech)',
                                      ['Soft Condensed Matter (cond-mat.soft)', 'Chemical Physics (physics.chem-ph)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0528_cats(self):
        (id, primary, secondaries) = ('0704.0528', 'Networking and Internet Architecture (cs.NI)',
                                      ['Information Theory (cs.IT)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0869_cats(self):
        (id, primary, secondaries) = ('0704.0869', 'Statistical Mechanics (cond-mat.stat-mech)',
                                      ['Mathematical Physics (math-ph)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0796_cats(self):
        (id, primary, secondaries) = ('0704.0796', 'Quantum Physics (quant-ph)',
                                      ['Astrophysics (astro-ph)', 'Statistical Mechanics (cond-mat.stat-mech)', 'High Energy Physics - Phenomenology (hep-ph)', 'Mathematical Physics (math-ph)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0046_cats(self):
        (id, primary, secondaries) = ('0704.0046',
                                      'Quantum Physics (quant-ph)', ['Information Theory (cs.IT)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0976_cats(self):
        (id, primary, secondaries) = ('0704.0976', 'Statistical Mechanics (cond-mat.stat-mech)',
                                      ['Disordered Systems and Neural Networks (cond-mat.dis-nn)',
                                       'Chaotic Dynamics (nlin.CD)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0041_cats(self):
        (id, primary, secondaries) = ('0704.0041', 'Quantum Algebra (math.QA)',
                                      ['Mathematical Physics (math-ph)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0918_cats(self):
        (id, primary, secondaries) = ('0704.0918',
                                      'Algebraic Geometry (math.AG)', ['Statistics Theory (math.ST)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0123_cats(self):
        (id, primary, secondaries) = ('0704.0123', 'Chaotic Dynamics (nlin.CD)',
                                      ['Other Condensed Matter (cond-mat.other)', 'Optics (physics.optics)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0520_cats(self):
        (id, primary, secondaries) = ('0704.0520', 'Quantum Physics (quant-ph)',
                                      ['Other Condensed Matter (cond-mat.other)',
                                       'Atomic Physics (physics.atom-ph)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0084_cats(self):
        (id, primary, secondaries) = ('0704.0084', 'Soft Condensed Matter (cond-mat.soft)',
                                      ['Pattern Formation and Solitons (nlin.PS)',
                                       'Fluid Dynamics (physics.flu-dyn)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0588_cats(self):
        (id, primary, secondaries) = ('0704.0588',
                                      'Probability (math.PR)', ['Statistics Theory (math.ST)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

    def test_categories_for_0704_0687_cats(self):
        (id, primary, secondaries) = ('0704.0687', 'Analysis of PDEs (math.AP)',
                                      ['Mathematical Physics (math-ph)'])
        doc = self.absService.get_abs(id)
        self.assertIsNotNone(doc)
        assert doc.primary_category.display() == primary
        assert doc.display_secondaries() == secondaries

