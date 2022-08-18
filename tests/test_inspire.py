import os
import unittest
from datetime import date

from bs4 import BeautifulSoup
from hamcrest import *
from tests.test_abs_parser import ABS_FILES

from app import app
from browse.domain.license import ASSUMED_LICENSE_URI
from browse.services.document.metadata import AbsMetaSession
from browse.services.util.external_refs_cits import (
    INSPIRE_REF_CIT_CATEGORIES,
    get_orig_publish_date,
    include_inspire_link,
)


class InspireTest(unittest.TestCase):

    def setUp(self):
        app.testing = True
        app.config['APPLICATION_ROOT'] = ''
        self.app = app.test_client()

    def test_abs_with_inspire(self):
        f1 = ABS_FILES + '/ftp/arxiv/papers/1108/1108.5926.abs'
        m = AbsMetaSession.parse_abs_file(filename=f1)

        assert_that( m , is_not( None))
        assert_that( get_orig_publish_date(m.arxiv_identifier), equal_to(date(2011,8,1)))
        assert_that( m.primary_category , is_not( equal_to(None)))

        assert_that(include_inspire_link( m ), is_not(equal_to(False)),
                     '1108.5926v1 should get Insire link')

        rv = self.app.get('/abs/1108.5926v1')
        assert_that(rv.status_code, 200)
        assert_that( rv.data.decode('utf-8'), contains_string('INSPIRE HEP'),
                     '1108.5926 should get INSPIRE link')

    def test_abs_without_inspire(self):
        f1 = ABS_FILES + '/ftp/math/papers/0202/0202001.abs'
        m = AbsMetaSession.parse_abs_file(filename=f1)

        assert_that( m , is_not( None))
        assert_that(include_inspire_link( m ), equal_to(False),
                     'math/0202001 should NOT get Insire link')

        rv = self.app.get('/abs/math/0202001')
        assert_that(rv.status_code, 200)
        assert_that( rv.data.decode('utf-8'), is_not(contains_string('INSPIRE HEP')),
                     'math/0202001 should NOT get INSPIRE link')
