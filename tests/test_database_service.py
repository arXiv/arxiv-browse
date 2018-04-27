"""Tests for database service."""
from unittest import mock, TestCase


DATABASE_URL = 'sqlite:///:memory:'


class TestGetInstitution(TestCase):
    """:func:`.get_institution` gets an institution label for an IP address."""

    def setUp(self):
        """Initialize a database session with in-memory SQLite."""

        from browse.services import database
        self.database_service = database
        mock_app = mock.MagicMock()
        mock_app.config = {'SQLALCHEMY_DATABASE_URI': DATABASE_URL,
                           'SQLALCHEMY_TRACK_MODIFICATIONS': False}

        mock_app.extensions = {}
        mock_app.root_path = ''

        self.database_service.db.init_app(mock_app)
        self.database_service.db.app = mock_app
        self.database_service.db.create_all()
        inst_cornell = self.database_service.models.MemberInstitution(
            id=1,
            name='Cornell University',
            label='Cornell University'
        )
        self.database_service.db.session.add(inst_cornell)

        inst_cornell_ip = self.database_service.models.MemberInstitutionIP(
            id=1,
            sid=inst_cornell.id,
            start=2152988672,  # 128.84.0.0
            end=2153054207,    # 128.84.255.255
            exclude=0
        )
        self.database_service.db.session.add(inst_cornell_ip)

        inst_cornell_ip_exclude = self.database_service.models. \
            MemberInstitutionIP(
                id=2,
                sid=inst_cornell.id,
                start=2152991233,  # 128.84.10.1
                end=2152991242,    # 128.84.10.10
                exclude=1
            )
        self.database_service.db.session.add(inst_cornell_ip_exclude)

        inst_other = self.database_service.models.MemberInstitution(
            id=2,
            name='Other University',
            label='Other University'
        )
        self.database_service.db.session.add(inst_other)

        inst_other_ip = self.database_service.models.MemberInstitutionIP(
            id=3,
            sid=inst_other.id,
            start=2152991236,  # 128.84.10.4
            end=2152991242,    # 128.84.10.10
            exclude=0
        )
        self.database_service.db.session.add(inst_other_ip)

    def test_get_institution_returns_a_label(self):
        """If IP address matches an institution, a label is returned."""
        label = self.database_service.models.get_institution('128.84.0.0')
        self.assertEqual(label, 'Cornell University',
                         'Institution label returned for IP at end of range')
        label = self.database_service.models.get_institution('128.84.255.255')
        self.assertEqual(label, 'Cornell University',
                         'Institution label returned for IP at end of range')

        label = self.database_service.models.get_institution('128.84.12.34')
        self.assertEqual(label, 'Cornell University',
                         'Institution label returned for IP within range')
        label = self.database_service.models.get_institution('128.85.12.34')
        self.assertIsNone(
            label, 'No institution label returned for non-matching IP')
        label = self.database_service.models.get_institution('128.84.10.1')
        self.assertIsNone(
            label, 'No institution label returned for excluded IP')

        label = self.database_service.models.get_institution('128.84.10.5')
        self.assertEqual(
            label, 'Other University',
            'Institution label returned for IP excluded '
            'by one institution but included by another')

        with self.assertRaises(ValueError) as context:
            self.database_service.models.get_institution('notanip')

        self.assertIn(
            'does not appear to be an IPv4 or IPv6 address',
            str(context.exception))

    def tearDown(self):
        """Close the database session and drop all tables."""
        self.database_service.db.session.remove()
        self.database_service.db.drop_all()
