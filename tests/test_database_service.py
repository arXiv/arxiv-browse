"""Tests for database service."""
import glob
from typing import List
from unittest import mock, TestCase
from unittest.mock import Mock, patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from arxiv.db.models import TrackbackPing
from browse.services.database import get_sequential_id
from browse.services import database
from arxiv.identifier import Identifier

from tests import grep_f_count, execute_sql_files, path_of_for_test


DATABASE_URL = 'sqlite:///:memory:'

import pytest


@pytest.mark.usefixtures("unittest_add_db")
class TestBrowseDatabaseService(TestCase):
    """:func:`.get_institution` gets an institution label for an IP address."""

    # @classmethod
    # def setUpClass(cls) -> None:
    #     """Initialize a database session with in-memory SQLite."""
    #     from browse.services import database

    #     cls.database_service = database
    #     mock_app = mock.MagicMock()
    #     mock_app.config = {'SQLALCHEMY_DATABASE_URI': DATABASE_URL,
    #                        'SQLALCHEMY_TRACK_MODIFICATIONS': False}

    #     mock_app.extensions = {}
    #     mock_app.root_path = ''

    #     database.db.init_app(mock_app)
    #     database.db.app = mock_app
    #     database.db.create_all()
    #     database.db.session.commit()

    #     inst_cornell = database.models.MemberInstitution(
    #         id=1,
    #         name='Cornell University',
    #         label='Cornell University'
    #     )
    #     database.db.session.add(inst_cornell)

    #     inst_cornell_ip = database.models.MemberInstitutionIP(
    #         id=1,
    #         sid=inst_cornell.id,
    #         start=2152988672,  # 128.84.0.0
    #         end=2153054207,    # 128.84.255.255
    #         exclude=0
    #     )
    #     database.db.session.add(inst_cornell_ip)

    #     inst_cornell_ip_exclude = \
    #         database.models.MemberInstitutionIP(
    #             id=2,
    #             sid=inst_cornell.id,
    #             start=2152991233,  # 128.84.10.1
    #             end=2152991242,    # 128.84.10.10
    #             exclude=1
    #         )
    #     database.db.session.add(inst_cornell_ip_exclude)

    #     inst_other = database.models.MemberInstitution(
    #         id=2,
    #         name='Other University',
    #         label='Other University'
    #     )
    #     database.db.session.add(inst_other)

    #     inst_other_ip = database.models.MemberInstitutionIP(
    #         id=3,
    #         sid=inst_other.id,
    #         start=2152991236,  # 128.84.10.4
    #         end=2152991242,    # 128.84.10.10
    #         exclude=0
    #     )
    #     database.db.session.add(inst_other_ip)
    #     database.db.session.commit()

    #     sql_dir = path_of_for_test('data/db/sql')
    #     sql_files: List[str] = glob.glob(f'{sql_dir}/*.sql')
    #     execute_sql_files(sql_files, database.db.engine)
    #     database.db.session.commit()

    #     """Disable logging to avoid messy output during testing"""
    #     import logging
    #     logging.disable(logging.WARNING)

    def test_get_institution_returns_an_id_and_label(self) -> None:
        """If IP address matches an institution, a label is returned."""
        inst = database.get_institution(
            '128.84.0.0')
        self.assertEqual(inst.get('id'), 3,
                         'Institution ID returned for IP at end of range')
        self.assertEqual(inst.get('label'), 'Cornell University',
                         'Institution label returned for IP at end of range')

        label = database.get_institution(
            '128.84.255.255').get('label')
        self.assertEqual(label, 'Cornell University',
                         'Institution label returned for IP at end of range')

        label = database.get_institution(
            '128.84.12.34').get('label')
        self.assertEqual(label, 'Cornell University',
                         'Institution label returned for IP within range')
        label = database.get_institution(
            '128.85.12.34')
        self.assertIsNone(
            label, 'No institution label returned for non-matching IP')
        label = database.get_institution(
            '128.84.10.1')
        self.assertIsNone(
            label, 'No institution label returned for excluded IP')

        label = database.get_institution(
            '128.84.10.5').get('label')
        self.assertEqual(
            label, 'Other University',
            'Institution label returned for IP excluded '
            'by one institution but included by another')

        with self.assertRaises(ValueError) as context:
            database.get_institution('notanip')

        self.assertIn(
            'does not appear to be an IPv4 or IPv6 address',
            str(context.exception))

    def test_all_trackback_pings(self) -> None:
        """Test if all trackback pings are counted."""
        # doc_sql_file = path_of_for_test(
        #     'data/db/sql/arXiv_trackback_pings.sql')

        # count_from_file = grep_f_count(
        #     doc_sql_file,
        #     '''INSERT INTO `arXiv_trackback_pings`'''
        # )
        count_from_db: int = database.count_all_trackback_pings()
        count_from_db_list: int = database.get_all_trackback_pings().__len__()

        self.assertEqual(
            count_from_db, 92,
            'Count of all trackback pings are correct'
        )

        self.assertEqual(
            count_from_db_list, 92,
            'All trackback pings are returned'
        )

    def test_trackback_pings(self) -> None:
        """Test if trackback pings for a specific paper are counted."""
        test_paper_id = '0808.4142'
        count_from_db: int = database.count_trackback_pings(test_paper_id)
        count_from_db_list: int = database.get_paper_trackback_pings(test_paper_id).__len__()
        self.assertEqual(
            count_from_db, 9,
            f'Correct count of pings returned for paper {test_paper_id}'
        )
        self.assertEqual(
            count_from_db_list, 9,
            f'Correct count of pings returned for paper {test_paper_id}'
        )

    def test_recent_trackback_pings(self) -> None:
        """Test if recent trackbacks can be retrieved."""
        tbs: List = database.\
            get_recent_trackback_pings(max_trackbacks=-1)
        self.assertEqual(len(tbs), 0, 'List should be empty')
        tbs: List = database.\
            get_recent_trackback_pings(max_trackbacks=25)
        self.assertGreater(len(tbs), 0, 'List should be nonempty')
        for tb in tbs:
            self.assertIsInstance(tb[0], TrackbackPing)
            self.assertIsInstance(tb[1], str)
            self.assertIsInstance(Identifier(
                arxiv_id=tb[1]), Identifier, 'Value looks like an Identifier')
            self.assertIsInstance(tb[2], str)


    def test_get_dblp_listing_path(self) -> None:
        """Test whether paper has a DBLP Bibliography URL."""
        test_paper_id = '0704.0361'
        self.assertEqual(
            database.get_dblp_listing_path(
                test_paper_id),
            'db/journals/corr/corr0704.html#abs-0704-0361',
            'get expected DBLP URL'
        )
        test_paper_id = '1807.00001'
        self.assertIsNone(
            database.get_dblp_listing_path(
                test_paper_id))

    def test_get_dblp_authors(self) -> None:
        """Test whether paper has DBLP authors."""
        test_paper_id = '0704.0361'
        self.assertListEqual(
            database.get_dblp_authors(
                test_paper_id),
            ['Ioannis Chatzigeorgiou', 'Miguel R. D. Rodrigues',
                'Ian J. Wassell', 'Rolando A. Carrasco']
        )
        test_paper_id = '1807.00002'
        self.assertListEqual(
            database.get_dblp_authors(
                test_paper_id), [])

    def test_get_document_count(self) -> None:
        """Test document count function."""
        self.assertGreater(
            database.get_document_count(),
            0,
            'There is at least one document in the DB.'
        )

    @mock.patch('arxiv.db.Session.execute')
    @mock.patch('arxiv.db.Session.scalar')
    def test_error_conditions(self, mock_scalar, mock_execute) -> None:
        mock_execute.side_effect = NoResultFound
        mock_scalar.side_effect = NoResultFound
        self.assertEqual(
            database.get_institution('10.0.0.1'), None)
        self.assertEqual([],
                         database.get_all_trackback_pings())
        self.assertListEqual(
            database.get_paper_trackback_pings('0704.0361'), [])
        self.assertEqual(
            database.count_trackback_pings('0704.0361'), 0)
        self.assertEqual(
            database.count_all_trackback_pings(), 0)
        self.assertEqual(
            database.get_dblp_listing_path('0704.0361'), None)
        self.assertEqual(
            database.get_dblp_authors('0704.0361'), [])
        mock_execute.side_effect = SQLAlchemyError
        mock_scalar.side_effect = SQLAlchemyError
        self.assertRaises(SQLAlchemyError,
                          database.get_institution, '10.0.0.1')
        self.assertRaises(
            SQLAlchemyError, database.get_all_trackback_pings)
        self.assertRaises(
            SQLAlchemyError, database.get_paper_trackback_pings, 'paperx')
        self.assertRaises(
            SQLAlchemyError, database.count_all_trackback_pings)
        self.assertRaises(
            SQLAlchemyError, database.get_dblp_listing_path, 'px')
        self.assertRaises(
            SQLAlchemyError, database.get_dblp_authors, 'authx')


    def test_sequential_id(self) -> None:
        self.assertEqual(get_sequential_id(''), None)
        self.assertEqual(get_sequential_id(Identifier('0906.3421'),is_next=True), '0906.4150')
        self.assertTrue(get_sequential_id(Identifier('0906.9150'),is_next=True).startswith('0907'))
        self.assertEqual(get_sequential_id(Identifier('0906.3421'),is_next=False), '0906.3336')
        self.assertTrue(get_sequential_id(Identifier('0907.2020'),is_next=False).startswith('0906'))
