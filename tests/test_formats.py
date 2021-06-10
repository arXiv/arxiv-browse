"""Tests for formats logic."""

from unittest import TestCase
from browse.services.documents.fs_implementation.formats import formats_from_source_file_name,\
    formats_from_source_type


class TestFormats(TestCase):
    """Tests for formats logic."""

    def test_formats_from_source_file_name(self):
        """Test formats returned from file name."""
        self.assertListEqual(formats_from_source_file_name('foo.pdf'),
                             ['pdfonly'])
        self.assertListEqual(formats_from_source_file_name('/bar.ps.gz'),
                             ['pdf', 'ps'])
        self.assertListEqual(formats_from_source_file_name('abc.html.gz'),
                             ['html'])
        self.assertListEqual(formats_from_source_file_name('baz.html'),
                             [])
        self.assertListEqual(formats_from_source_file_name(''),
                             [])

    def test_formats_from_source_type(self):
        """Tests formats based on metadata source type and other parameters."""
        self.assertListEqual(formats_from_source_type('I'), ['src'])
        self.assertListEqual(formats_from_source_type('IS'),
                             ['pdf', 'ps', 'other'])
        self.assertListEqual(formats_from_source_type('', cache_flag=True),
                             ['nops', 'other'])
        self.assertListEqual(formats_from_source_type('', cache_flag=False),
                             ['pdf', 'ps', 'other'])
        self.assertListEqual(
            formats_from_source_type('', format_pref='fname=CM'),
            ['ps(CM)', 'other'])
        self.assertListEqual(formats_from_source_type('P'),
                             ['pdf', 'ps', 'other'])
        self.assertListEqual(formats_from_source_type('D', 'src'),
                             ['src', 'pdf', 'other'])
        self.assertListEqual(formats_from_source_type('F'),
                             ['pdf', 'other'])
        self.assertListEqual(formats_from_source_type('H'),
                             ['html', 'other'])
        self.assertListEqual(formats_from_source_type('X'),
                             ['pdf', 'other'])

        self.assertListEqual(formats_from_source_type('', 'pdf'),
                             ['pdf', 'other'])
        self.assertListEqual(formats_from_source_type('', '400'),
                             ['ps(400)', 'other'])
        self.assertListEqual(formats_from_source_type('', '600'),
                             ['ps(600)', 'other'])
        self.assertListEqual(formats_from_source_type('', 'fname=cm'),
                             ['ps(cm)', 'other'])
        self.assertListEqual(formats_from_source_type('', 'fname=CM'),
                             ['ps(CM)', 'other'])
        self.assertListEqual(formats_from_source_type('', 'dvi'),
                             ['dvi', 'other'])
