"""Tests for formats logic."""

from unittest import TestCase

from browse.services.documents.format_codes import formats_from_source_flag, formats_from_source_file_name


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
        self.assertListEqual(formats_from_source_flag('I'), ['src'])
        self.assertListEqual(formats_from_source_flag('IS'),
                             ['pdf', 'ps', 'other'])
        self.assertListEqual(formats_from_source_flag('', cache_flag=True),
                             ['nops', 'other'])
        self.assertListEqual(formats_from_source_flag('', cache_flag=False),
                             ['pdf', 'ps', 'other'])
        self.assertListEqual(
            formats_from_source_flag('', format_pref='fname=CM'),
            ['ps(CM)', 'other'])
        self.assertListEqual(formats_from_source_flag('P'),
                             ['pdf', 'ps', 'other'])
        self.assertListEqual(formats_from_source_flag('D', 'src'),
                             ['pdf', 'src', 'other'])
        self.assertListEqual(formats_from_source_flag('F'),
                             ['pdf', 'other'])
        self.assertListEqual(formats_from_source_flag('H'),
                             ['html', 'other'])
        self.assertListEqual(formats_from_source_flag('X'),
                             ['pdf', 'other'])

        self.assertListEqual(formats_from_source_flag('', 'pdf'),
                             ['pdf', 'other'])
        self.assertListEqual(formats_from_source_flag('', '400'),
                             ['ps(400)', 'other'])
        self.assertListEqual(formats_from_source_flag('', '600'),
                             ['ps(600)', 'other'])
        self.assertListEqual(formats_from_source_flag('', 'fname=cm'),
                             ['ps(cm)', 'other'])
        self.assertListEqual(formats_from_source_flag('', 'fname=CM'),
                             ['ps(CM)', 'other'])
        self.assertListEqual(formats_from_source_flag('', 'dvi'),
                             ['dvi', 'other'])
