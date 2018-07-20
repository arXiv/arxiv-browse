"""Tests for database service."""
import glob
from typing import List
from unittest import mock, TestCase
from unittest.mock import Mock, patch
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.orm.exc import NoResultFound

from tests import grep_f_count, execute_sql_files, test_path_of

DATABASE_URL = 'sqlite:///:memory:'


class TestBrowseDatabaseService(TestCase):
    """:func:`.get_institution` gets an institution label for an IP address."""

    @classmethod
    def setUpClass(cls) -> None:
        """Initialize a database session with in-memory SQLite."""
        from browse.services import database

        cls.database_service = database
        mock_app = mock.MagicMock()
        mock_app.config = {'SQLALCHEMY_DATABASE_URI': DATABASE_URL,
                           'SQLALCHEMY_TRACK_MODIFICATIONS': False}

        mock_app.extensions = {}
        mock_app.root_path = ''

        database.db.init_app(mock_app)
        database.db.app = mock_app
        database.db.create_all()
        database.db.session.commit()

        inst_cornell = database.models.MemberInstitution(
            id=1,
            name='Cornell University',
            label='Cornell University'
        )
        database.db.session.add(inst_cornell)

        inst_cornell_ip = database.models.MemberInstitutionIP(
            id=1,
            sid=inst_cornell.id,
            start=2152988672,  # 128.84.0.0
            end=2153054207,    # 128.84.255.255
            exclude=0
        )
        database.db.session.add(inst_cornell_ip)

        inst_cornell_ip_exclude = \
            database.models.MemberInstitutionIP(
                id=2,
                sid=inst_cornell.id,
                start=2152991233,  # 128.84.10.1
                end=2152991242,    # 128.84.10.10
                exclude=1
            )
        database.db.session.add(inst_cornell_ip_exclude)

        inst_other = database.models.MemberInstitution(
            id=2,
            name='Other University',
            label='Other University'
        )
        database.db.session.add(inst_other)

        inst_other_ip = database.models.MemberInstitutionIP(
            id=3,
            sid=inst_other.id,
            start=2152991236,  # 128.84.10.4
            end=2152991242,    # 128.84.10.10
            exclude=0
        )
        database.db.session.add(inst_other_ip)
        database.db.session.commit()

        sql_dir = test_path_of('data/db/sql')
        sql_files: List[str] = glob.glob(f'{sql_dir}/*.sql')
        execute_sql_files(sql_files, database.db.engine)
        database.db.session.commit()

    def test_get_institution_returns_a_label(self) -> None:
        """If IP address matches an institution, a label is returned."""
        label = TestBrowseDatabaseService.database_service.get_institution(
            '128.84.0.0')
        self.assertEqual(label, 'Cornell University',
                         'Institution label returned for IP at end of range')
        label = TestBrowseDatabaseService.database_service.get_institution(
            '128.84.255.255')
        self.assertEqual(label, 'Cornell University',
                         'Institution label returned for IP at end of range')

        label = TestBrowseDatabaseService.database_service.get_institution(
            '128.84.12.34')
        self.assertEqual(label, 'Cornell University',
                         'Institution label returned for IP within range')
        label = TestBrowseDatabaseService.database_service.get_institution(
            '128.85.12.34')
        self.assertIsNone(
            label, 'No institution label returned for non-matching IP')
        label = TestBrowseDatabaseService.database_service.get_institution(
            '128.84.10.1')
        self.assertIsNone(
            label, 'No institution label returned for excluded IP')

        label = TestBrowseDatabaseService.database_service.get_institution(
            '128.84.10.5')
        self.assertEqual(
            label, 'Other University',
            'Institution label returned for IP excluded '
            'by one institution but included by another')

        with self.assertRaises(ValueError) as context:
            TestBrowseDatabaseService.database_service\
                .get_institution('notanip')

        self.assertIn(
            'does not appear to be an IPv4 or IPv6 address',
            str(context.exception))

    def test_all_trackback_pings(self) -> None:
        """Test if all trackback pings are counted."""
        doc_sql_file = test_path_of('data/db/sql/arXiv_trackback_pings.sql')

        count_from_file = grep_f_count(
            doc_sql_file,
            '''INSERT INTO `arXiv_trackback_pings`'''
        )
        count_from_db: int = TestBrowseDatabaseService.database_service\
            .count_all_trackback_pings()
        count_from_db_list: int = TestBrowseDatabaseService.database_service\
            .get_all_trackback_pings().__len__()

        if count_from_file is not None:
            self.assertEqual(
                count_from_db, count_from_file,
                'Count of all trackback pings are correct'
            )
        else:
            self.assertIsNotNone(
                count_from_file,
                'count of trackback pings is defined'
            )

        self.assertEqual(
            count_from_db_list, count_from_file,
            'All trackback pings are returned'
        )

    def test_trackback_pings(self) -> None:
        """Test if trackback pings for specific paper are counted."""
        test_paper_id = '0808.4142'
        count_from_db: int = TestBrowseDatabaseService.database_service\
            .count_trackback_pings(test_paper_id)
        count_from_db_list: int = TestBrowseDatabaseService.database_service\
            .get_trackback_pings(test_paper_id).__len__()
        self.assertEqual(
            count_from_db, 8,
            f'Correct count of pings returned for paper {test_paper_id}'
        )
        self.assertEqual(
            count_from_db_list, 9,
            f'Correct count of pings returned for paper {test_paper_id}'
        )

    def test_sciencewise_ping(self) -> None:
        """Test whether paper with version suffix has a ScienceWISE ping."""
        test_paper_id_v = '1605.09669v2'
        self.assertTrue(
            TestBrowseDatabaseService.database_service.
            has_sciencewise_ping(test_paper_id_v))
        test_paper_id_v = '1605.09669'
        self.assertFalse(
            TestBrowseDatabaseService.database_service.
            has_sciencewise_ping(test_paper_id_v))
        test_paper_id_v = None
        self.assertFalse(
            TestBrowseDatabaseService.database_service.
            has_sciencewise_ping(test_paper_id_v))

    def test_get_dblp_listing_path(self) -> None:
        """Test whether paper has a DBLP Bibliography URL."""
        test_paper_id = '0704.0361'
        self.assertEqual(
            TestBrowseDatabaseService.database_service.get_dblp_listing_path(
                test_paper_id),
            'db/journals/corr/corr0704.html#abs-0704-0361',
            f'get expected DBLP URL'
        )
        test_paper_id = '1807.00001'
        self.assertIsNone(
            TestBrowseDatabaseService.database_service.get_dblp_listing_path(
                test_paper_id))

    def test_get_dblp_authors(self) -> None:
        """Test whether paper has DBLP authors."""
        test_paper_id = '0704.0361'
        self.assertListEqual(
            TestBrowseDatabaseService.database_service.get_dblp_authors(
                test_paper_id),
            ['Ioannis Chatzigeorgiou', 'Miguel R. D. Rodrigues',
                'Ian J. Wassell', 'Rolando A. Carrasco']
        )
        test_paper_id = '1807.00002'
        self.assertListEqual(
            TestBrowseDatabaseService.database_service.get_dblp_authors(
                test_paper_id), [])

    @mock.patch('browse.services.database.models.db.session.query')
    def test_error_conditions(self, mock_query)->None:
        mock_query.side_effect = NoResultFound
        self.assertEqual(
            TestBrowseDatabaseService.database_service.get_institution('10.0.0.1'), None)
        self.assertEqual([],
            TestBrowseDatabaseService.database_service.get_all_trackback_pings())
        self.assertListEqual(
            TestBrowseDatabaseService.database_service.get_trackback_pings('0704.0361'), [])
        self.assertEqual(
            TestBrowseDatabaseService.database_service.count_trackback_pings('0704.0361'), 0)
        self.assertEqual(
            TestBrowseDatabaseService.database_service.count_all_trackback_pings(), 0)
        self.assertEqual(
            TestBrowseDatabaseService.database_service.has_sciencewise_ping('0704.0361'), False)
        self.assertEqual(
            TestBrowseDatabaseService.database_service.get_dblp_listing_path('0704.0361'), None)
        self.assertEqual(
            TestBrowseDatabaseService.database_service.get_dblp_authors('0704.0361'), [])
        mock_query.side_effect = SQLAlchemyError
        self.assertRaises(SQLAlchemyError,
                          TestBrowseDatabaseService.database_service.get_institution, '10.0.0.1')
        self.assertRaises(SQLAlchemyError, TestBrowseDatabaseService.database_service.get_all_trackback_pings)
        self.assertRaises(SQLAlchemyError, TestBrowseDatabaseService.database_service.get_trackback_pings, 'paperx')
        self.assertRaises(SQLAlchemyError, TestBrowseDatabaseService.database_service.count_all_trackback_pings)
        self.assertRaises(SQLAlchemyError, TestBrowseDatabaseService.database_service.has_sciencewise_ping, 'px')
        self.assertRaises(SQLAlchemyError, TestBrowseDatabaseService.database_service.get_dblp_listing_path, 'px')
        self.assertRaises(SQLAlchemyError, TestBrowseDatabaseService.database_service.get_dblp_authors,'authx')

    @classmethod
    def tearDownClass(cls) -> None:
        """Close the database session and drop all tables."""
        cls.database_service.db.session.remove()
        cls.database_service.db.drop_all()
