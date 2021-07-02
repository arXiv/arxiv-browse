"""Tests for bibtex citations."""
from unittest import TestCase
from browse.services.documents.fs_implementation.parse_abs import parse_abs_file
from browse.formatting.cite import arxiv_bibtex
from tests import path_of_for_test

ABS_FILES = path_of_for_test('data/abs_files')


abs_to_test = \
    [ABS_FILES + '/ftp/arxiv/papers/0705/0705.0001.abs',
     ABS_FILES + '/ftp/arxiv/papers/1108/1108.5926.abs',
     ABS_FILES + '/ftp/arxiv/papers/1902/1902.11195.abs',
     ABS_FILES + '/ftp/arxiv/papers/1902/1902.05884.abs',
     ABS_FILES + '/ftp/arxiv/papers/1307/1307.0001.abs',
     ABS_FILES + '/ftp/arxiv/papers/1307/1307.0584.abs',
     ABS_FILES + '/ftp/arxiv/papers/1307/1307.0101.abs',
     ABS_FILES + '/ftp/arxiv/papers/1307/1307.0010.abs',
     ABS_FILES + '/ftp/arxiv/papers/1310/1310.8286.abs',
     ABS_FILES + '/ftp/arxiv/papers/0806/0806.0920.abs',
     ABS_FILES + '/ftp/arxiv/papers/1501/1501.05201.abs',
     ABS_FILES + '/ftp/arxiv/papers/1501/1501.99999.abs',
     ABS_FILES + '/ftp/arxiv/papers/1501/1501.00002.abs',
     ABS_FILES + '/ftp/arxiv/papers/1501/1501.00001.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0667.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0997.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0169.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0476.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0510.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0050.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0244.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0236.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0394.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0349.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0428.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0844.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0751.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0652.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0393.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0903.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0327.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0232.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0764.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0105.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0906.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0392.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0233.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0060.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0713.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0091.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0850.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0679.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0712.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0026.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0792.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0745.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0292.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0910.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0664.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0115.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0749.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0611.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0690.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0612.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0279.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0405.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0180.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0741.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0603.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0998.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0760.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0647.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0787.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0121.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0332.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0281.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0817.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0314.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0639.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0170.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0703.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0632.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0155.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0819.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0829.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0434.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0458.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0478.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0582.abs',
     ABS_FILES + '/ftp/arxiv/papers/0704/0704.0083.abs']


class TestCite(TestCase):
    """Test cite."""

    def test_cite(self):
        """Test cite."""
        
        for fname_path in abs_to_test:                
            cite=arxiv_bibtex(parse_abs_file(filename=fname_path))
            self.assertIsNotNone(cite)
