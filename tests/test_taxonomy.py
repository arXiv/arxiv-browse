"""Tests for arXiv taxonomy module."""
from unittest import TestCase
from datetime import datetime
from browse.services.document.taxonomy import GROUPS, ARCHIVES, \
    ARCHIVES_ACTIVE, CATEGORIES, ARCHIVES_SUBSUMED, \
    LEGACY_ARCHIVE_AS_PRIMARY, LEGACY_ARCHIVE_AS_SECONDARY


class TestTaxonomy(TestCase):
    """Tests for the arXiv category taxonomy definitions."""

    def test_groups(self):
        """Tests for the highest level of the category taxonomy (groups)."""
        for key, value in GROUPS.items():
            self.assertRegexpMatches(key, r'^grp_[a-z\-_]+$')
            self.assertIn('name', value, 'name defined for {}'.format(key))
            self.assertIsInstance(value['name'], str, 'name is a str')
            self.assertIn(
                'start_year', value, 'start_year defined for {}'.format(key))
            self.assertIsInstance(
                value['start_year'], int, 'start_year is an integer')
            self.assertGreater(value['start_year'],
                               1990, 'start_year > 1990')
            if 'default_archive' in value:
                self.assertIn(
                    value['default_archive'],
                    ARCHIVES,
                    'default_archive {} is a valid archive'.format(
                        value['default_archive'])
                )

    def test_archives(self):
        """Tests for the middle level of the category taxonomy (archives)."""
        for key, value in ARCHIVES.items():
            self.assertIn('name', value, 'name defined for {}'.format(key))
            self.assertIsInstance(value['name'], str, 'name is a str')
            self.assertIn('in_group', value,
                          'in_group defined for {}'.format(key))
            self.assertIn(value['in_group'], GROUPS,
                          '{} is a valid group'.format(value['in_group']))
            self.assertIn('start_date', value,
                          'start_date defined for {}'.format(key))
            start_dt = datetime.strptime(value['start_date'], '%Y-%m')
            self.assertIsInstance(start_dt, datetime)
            self.assertGreaterEqual(start_dt, datetime(1991, 8, 1))
            if 'end_date' in value:
                end_dt = datetime.strptime(value['end_date'], '%Y-%m')
                self.assertGreater(
                    end_dt, start_dt, 'end_date greater than start_date')

    def test_active_archives(self):
        """Tests for active (non-defunct) archives."""
        for key, value in ARCHIVES_ACTIVE.items():
            self.assertNotIn('end_date', value)

    def test_archives_subsumed(self):
        """Tests for defunct archives that have been subsumed by categories."""
        for key, value in ARCHIVES_SUBSUMED.items():
            self.assertIn(key, ARCHIVES, '{} is a valid archive'.format(key))
            self.assertIn(
                'end_date',
                ARCHIVES[key],
                '{} is a defunct archive'.format(key)
            )
            self.assertIn(
                value,
                CATEGORIES,
                '{} is a valid category'.format(value)
            )
            self.assertNotIn(
                'end_date',
                ARCHIVES[CATEGORIES[value]['in_archive']],
                '{} is not in a defunct archive'.format(value)
            )

    def test_legacy_archives_as_categories(self):
        """Test for archives that were used as primary/secondary categories."""
        for key, value in LEGACY_ARCHIVE_AS_PRIMARY.items():
            self.assertIn(key, ARCHIVES, '{} is a valid archive'.format(key))
            dt = datetime.strptime(value, '%Y-%m')
            self.assertIsInstance(dt, datetime)
        for key, value in LEGACY_ARCHIVE_AS_SECONDARY.items():
            self.assertIn(key, ARCHIVES, '{} is a valid archive'.format(key))
            dt = datetime.strptime(value, '%Y-%m')
            self.assertIsInstance(dt, datetime)

    def test_categories(self):
        """Test for the lowest level of the category taxonomy (categories)."""
        for key, value in CATEGORIES.items():
            self.assertIn('name', value, 'name defined for {}'.format(key))
            self.assertIsInstance(value['name'], str, 'name is a str')
            self.assertIn('in_archive', value,
                          'in_archive defined for {}'.format(key))
            self.assertIn(value['in_archive'], ARCHIVES,
                          '{} is a valid archive'.format(value['in_archive']))
