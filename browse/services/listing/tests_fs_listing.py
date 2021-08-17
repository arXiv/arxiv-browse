from unittest import TestCase
from datetime import datetime, date
import os
import re
from werkzeug.exceptions import BadRequest

from tests import path_of_for_test
LISTING_FILES = path_of_for_test('data/listing_files')

from .fs_listings import FsListingFilesService

class TestFsListingImplementation(TestCase):
    """Tests for the file system listing implementation.

        list_new_articles(self,archiveOrCategory: str, skip: int,
           show: int, if_modified_since: Optional[str] = None) -> NewResponse:
    """
    # Done
    def test_new_listing(self):
        archiveOrCategory = "cs.GT"
        skip = 0
        show = 500
        if_modified_since = None

        fsls = FsListingFilesService({'listing_files': LISTING_FILES})

        # 1 archive listing
        archiveOrCategory = "cs"
        resp = fsls.list_new_articles(archiveOrCategory, skip, show, if_modified_since)

        assert len(resp['listings']) == 442
        assert resp['new_count'] == 310
        assert resp['cross_count'] == 132
        assert resp['rep_count'] == 0
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        assert resp['listings'][0]['id'] == '2108.01075'
        assert resp['listings'][0]['listingType'] == 'new'
        assert resp['listings'][0]['primary'] == 'cs.CV'

        # 2 category listing
        archiveOrCategory = "cs.GT"
        self.assertEqual(archiveOrCategory, 'cs.GT')

        resp = fsls.list_new_articles(archiveOrCategory, skip, show, if_modified_since)

        assert len(resp['listings']) == 20
        assert resp['new_count'] == 12
        assert resp['cross_count'] == 8
        assert resp['rep_count'] == 0
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        # 3 category listing
        archiveOrCategory = "hep-th"
        resp = fsls.list_new_articles(archiveOrCategory, skip, show, if_modified_since)

        assert len(resp['listings']) == 29
        assert resp['new_count'] == 16
        assert resp['cross_count'] == 13
        assert resp['rep_count'] == 0
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        # Expect error - invalid archive
        with self.assertRaises(BadRequest):
            archiveOrCategory = "hep-does-not-exist"
            resp = fsls.list_new_articles(archiveOrCategory, skip, show, if_modified_since)

        # Expect error - No test data
        with self.assertRaises(BadRequest):
            archiveOrCategory = "math"
            resp = fsls.list_new_articles(archiveOrCategory, skip, show, if_modified_since)

    # Done
    def test_pastweek_listing(self):
        archiveOrCategory = "cs.GT"
        skip = 0
        show = 25
        if_modified_since = None

        fsls = FsListingFilesService({'listing_files': LISTING_FILES})

        archiveOrCategory = "cs"
        resp = fsls.list_pastweek_articles(archiveOrCategory, skip, show, if_modified_since)

        assert len(resp['listings']) == 25
        assert resp['count'] == 1400
        assert len(resp['pubdates']) == 5
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        archiveOrCategory = "cs.GT"
        self.assertEqual(archiveOrCategory, 'cs.GT')

        resp = fsls.list_pastweek_articles(archiveOrCategory, skip, show, if_modified_since)

        assert len(resp['listings']) == 18
        assert resp['count'] == 18
        assert len(resp['pubdates']) == 5
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        archiveOrCategory = "hep-th"
        resp = fsls.list_pastweek_articles(archiveOrCategory, skip, show, if_modified_since)

    # Done
    def test_month_listing(self):
        """Test monthly listing."""
        archiveOrCategory = "cs.GT"
        skip = 0
        show = 25
        if_modified_since = None

        fsls = FsListingFilesService({'listing_files': LISTING_FILES})

        archiveOrCategory = "cs"
        resp = fsls.list_articles_by_month(archiveOrCategory, 21, 6, skip, show, if_modified_since)

        assert len(resp['listings']) == 25
        assert resp['count'] == 7553
        assert len(resp['pubdates']) == 1
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        archiveOrCategory = "cs.GT"
        resp = fsls.list_articles_by_month(archiveOrCategory, 21, 6, skip, show, if_modified_since)

        assert len(resp['listings']) == 25
        assert resp['count'] == 137
        assert len(resp['pubdates']) == 1
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        archiveOrCategory = "hep-th"
        resp = fsls.list_articles_by_month(archiveOrCategory, 21, 6, skip, show, if_modified_since)

        assert len(resp['listings']) == 25
        assert resp['count'] == 575
        assert len(resp['pubdates']) == 1
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

    def test_year_listing(self):
        archiveOrCategory = "cs.GT"
        skip = 0
        show = 25
        if_modified_since = "Thu, 31 Dec 2020 08:49:37 GMT"

        fsls = FsListingFilesService({'listing_files': LISTING_FILES})

        # Test partial year
        archiveOrCategory = "cs"
        resp = fsls.list_articles_by_year(archiveOrCategory, 21, skip, show, if_modified_since)

        assert len(resp['listings']) == 25
        assert resp['count'] == 45846
        assert len(resp['pubdates']) == 8
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        archiveOrCategory = "cs.GT"
        self.assertEqual(archiveOrCategory, 'cs.GT')

        resp = fsls.list_articles_by_year(archiveOrCategory, 21, skip, show, if_modified_since)

        assert len(resp['listings']) == 25
        assert resp['count'] == 684
        assert len(resp['pubdates']) == 8
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        archiveOrCategory = "hep-th"
        resp = fsls.list_articles_by_year(archiveOrCategory, 21, skip, show, if_modified_since)

        assert len(resp['listings']) == 25
        assert resp['count'] == 3749
        assert len(resp['pubdates']) == 8
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        #Test full year
        archiveOrCategory = "cs"
        resp = fsls.list_articles_by_year(archiveOrCategory, 20, skip, show, if_modified_since)

        assert len(resp['listings']) == 25
        assert resp['count'] == 71440
        assert len(resp['pubdates']) == 12
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        archiveOrCategory = "cs.GT"
        self.assertEqual(archiveOrCategory, 'cs.GT')

        resp = fsls.list_articles_by_year(archiveOrCategory, 20, skip, show, if_modified_since)

        assert len(resp['listings']) == 25
        assert resp['count'] == 1052
        assert len(resp['pubdates']) == 12
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

    def test_monthly_counts(self):
        archiveOrCategory = "cs.GT"
        skip = 0
        show = 25
        if_modified_since = "Thu, 31 Dec 2020 08:49:37 GMT"

        fsls = FsListingFilesService({'listing_files': LISTING_FILES})

        archiveOrCategory = "cs"
        resp = fsls.monthly_counts(archiveOrCategory, 20)

        print(f'**Monthly counts cs: {resp}')
        print(f'Monthly:')
        for monthly_count in resp:
            print(f"*{monthly_count}*: {resp[monthly_count]}")
        print(f"New: {resp['new_count']} + {resp['cross_count']} = {resp['new_count'] + resp['cross_count']}")

        assert len(resp['month_counts']) == 12
        assert resp['new_count'] == 59309
        assert resp['cross_count'] == 12132
        assert resp['new_count'] + resp['cross_count'] == 71441
        assert len(resp['listings']) == 71441
        month_count_listing = resp['listings']

        # Debugging - monthly count is off by 1
        #show = 80000
        archiveOrCategory = "cs"
        resp = fsls.list_articles_by_year(archiveOrCategory, 20, skip, show, if_modified_since)
        ## assert len(resp['listings']) == 71441
        ###by_year_listing = resp['listings']
        ###assert month_count_listing == by_year_listing
        # End Debugging

        archiveOrCategory = "cs"
        resp = fsls.monthly_counts(archiveOrCategory, 21)

        print(f'**Monthly counts cs: {resp}**')
        print(f'Monthly:')
        for monthly_count in resp:
            print(f"*{monthly_count}*: {resp[monthly_count]}")
        print(f"New: {resp['new_count']} + {resp['cross_count']} = {resp['new_count'] + resp['cross_count']}")

        assert len(resp['month_counts']) == 8
        assert resp['new_count'] == 39373
        assert resp['cross_count'] == 6474
        assert resp['new_count'] + resp['cross_count'] == 45847

    # Done
    def test_is_rule(self):
        """Test supporting _is_rule routine that signals item type."""
        random_line = "Date: Mon,  2 Aug 21 00:32:07 GMT"
        standard = '------------------------------------------------------------------------------'
        crosses = '%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-'
        replaces = '%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%'
        end = '%%%---%%%---%%%---%%%---%%%---%%%---%%%---%%%---%%%---%%%---%%%---%%%---%%%---'

        fsls = FsListingFilesService({'listing_files': LISTING_FILES})

        (is_rule, type) = fsls._is_rule(random_line, 'new')
        assert is_rule == 0
        assert type == ''

        (is_rule, type) = fsls._is_rule(standard, 'new')
        assert is_rule == 1
        assert type == ''

        (is_rule, type) = fsls._is_rule(crosses, 'new')
        assert is_rule == 1
        assert type == 'cross'

        (is_rule, type) = fsls._is_rule(replaces, 'new')
        assert is_rule == 1
        assert type == 'rep'

        (is_rule, type) = fsls._is_rule(end, 'new')
        assert is_rule == 1
        assert type == 'end'

    # Done
    def test_skip_and_show(self):
        """Simple tests of the basic parser"""

        archiveOrCategory = "cs.GT"
        skip = 0
        show = 500
        if_modified_since = None

        fsls = FsListingFilesService({'listing_files': LISTING_FILES})

        # 1 archive listing
        archiveOrCategory = "cs"
        resp = fsls.list_new_articles(archiveOrCategory, skip, show, if_modified_since)

        assert len(resp['listings']) == 442
        assert resp['new_count'] == 310
        assert resp['cross_count'] == 132
        assert resp['rep_count'] == 0
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        assert resp['listings'][0]['id'] == '2108.01075'
        assert resp['listings'][0]['listingType'] == 'new'
        assert resp['listings'][0]['primary'] == 'cs.CV'

        # Try getting 442 updates in two slices
        skip = 0
        show = 250
        resp1 = fsls.list_new_articles(archiveOrCategory, skip, show, if_modified_since)
        assert len(resp1['listings']) == 250

        skip = 250
        show = 250
        resp2 = fsls.list_new_articles(archiveOrCategory, skip, show, if_modified_since)
        assert len(resp2['listings']) == 192

        # Check a few points
        assert resp['listings'][0] == resp1['listings'][0]
        assert resp['listings'][441] == resp2['listings'][191]

        # Compare the entire listing of updates
        combined = resp1['listings'] + resp2['listings']
        assert resp['listings'] == combined

    # Done
    def test_generate_listing_path(self):
        """Test path generation """
        fsls = FsListingFilesService({'listing_files': LISTING_FILES})

        listingType = 'new'
        archiveOrCategory = 'cs'
        year = 11
        month = 3

        # new archive
        path = fsls._generate_listing_path(listingType, archiveOrCategory,
                                    year, month)
        # Get rid of root portion of path
        rel_path = re.sub(LISTING_FILES, '', path)
        assert rel_path == '/cs/listings/new'

        # new category
        archiveOrCategory = 'cs.MA'
        path = fsls._generate_listing_path(listingType, archiveOrCategory,
                                           year, month)
        # Get rid of root portion of path
        rel_path = re.sub(LISTING_FILES, '', path)
        assert rel_path == '/cs/listings/new.MA'

        # pathweek
        listingType = 'pastweek'
        archiveOrCategory = 'cs'

        path = fsls._generate_listing_path(listingType, archiveOrCategory,
                                           year, month)
        # Get rid of root portion of path
        rel_path = re.sub(LISTING_FILES, '', path)
        assert rel_path == '/cs/listings/pastweek'

        # pastweek category
        archiveOrCategory = 'cs.MA'
        path = fsls._generate_listing_path(listingType, archiveOrCategory,
                                           year, month)
        # Get rid of root portion of path
        rel_path = re.sub(LISTING_FILES, '', path)
        assert rel_path == '/cs/listings/pastweek.MA'

        # month archive
        listingType = 'month'
        archiveOrCategory = 'cs'
        path = fsls._generate_listing_path(listingType, archiveOrCategory,
                                           year, month)
        # Get rid of root portion of path
        rel_path = re.sub(LISTING_FILES, '', path)
        assert rel_path == '/cs/listings/1103'

        # month category
        archiveOrCategory = 'cs.MA'
        path = fsls._generate_listing_path(listingType, archiveOrCategory,
                                           year, month)
        # Get rid of root portion of path
        rel_path = re.sub(LISTING_FILES, '', path)
        assert rel_path == '/cs/listings/1103'

        # cond-mat.quant-gas (special characters)
        with self.assertRaises(BadRequest):
            archiveOrCategory = 'cond-mat.quant-gas'
            listingType = 'new'
            path = fsls._generate_listing_path(listingType, archiveOrCategory,
                                               year, month)
        # Get rid of root portion of path
        rel_path = re.sub(LISTING_FILES, '', path)
        assert rel_path == '/cs/listings/1103'

        # Test some bad parameters
        with self.assertRaises(BadRequest):
            archiveOrCategory = 'JUNK'
            path = fsls._generate_listing_path(listingType, archiveOrCategory,
                                               year, month)

        with self.assertRaises(BadRequest):
            archiveOrCategory = 'math'
            path = fsls._generate_listing_path(listingType, archiveOrCategory,
                                               year, month)

    # Done
    def test_if_modified_since(self):
        """Test if_modified since behavior.

        Current test data is from August 4th, 2021.
        """
        archiveOrCategory = "cs.GT"
        skip = 0
        show = 25

        # Date older than data (expect is modified)
        if_modified_since_before = "Sun, 1 Aug 2021 08:49:37 GMT"
        # Date newer than data (expect not modified)
        if_modified_since_after = "Sat, 10 Aug 2021 08:49:37 GMT"

        fsls = FsListingFilesService({'listing_files': LISTING_FILES})

        # new
        archiveOrCategory = "cs"
        resp = fsls.list_new_articles(archiveOrCategory, skip, show, if_modified_since_before)

        # expect data
        assert len(resp['listings']) == 442
        assert resp['new_count'] == 310
        assert resp['cross_count'] == 132
        assert resp['rep_count'] == 0
        assert resp['expires'] != None
        assert datetime.strptime(resp['expires'], '%a, %d %b %Y %H:%M:%S GMT')

        archiveOrCategory = "cs.GT"

        # expect not modified response
        resp = fsls.list_new_articles(archiveOrCategory, skip, show, if_modified_since_after)

        assert resp['not_modified'] == True
        assert resp['expires'] != None

        # pastweek

        # expect data
        archiveOrCategory = "hep-th"
        resp = fsls.list_pastweek_articles(archiveOrCategory, skip, show, if_modified_since_before)

        # expect not modified response
        resp = fsls.list_pastweek_articles(archiveOrCategory, skip, show, if_modified_since_after)
        assert resp['not_modified'] == True
        assert resp['expires'] != None

        # month

        archiveOrCategory = "cs"
        resp = fsls.list_articles_by_month(archiveOrCategory, 21, 6, skip, show, if_modified_since_before)

        archiveOrCategory = "cs"
        resp = fsls.list_articles_by_month(archiveOrCategory, 21, 6, skip, show, if_modified_since_after)
        assert resp['not_modified'] == True
        assert resp['expires'] != None

        # year (also tests partial year)
        archiveOrCategory = "hep-th"
        resp = fsls.list_articles_by_year(archiveOrCategory, 21, skip, show, if_modified_since_before)

        archiveOrCategory = "hep-th"
        resp = fsls.list_articles_by_year(archiveOrCategory, 21, skip, show, if_modified_since_after)
        assert resp['not_modified'] == True
        assert resp['expires'] != None


