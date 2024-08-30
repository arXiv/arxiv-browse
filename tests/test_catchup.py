import pytest
from unittest.mock import patch
from datetime import datetime,  date
from flask import Flask
from werkzeug.exceptions import BadRequest

from browse.controllers.catchup_page import _process_catchup_params, GROUPS, ARCHIVES, CATEGORIES
from browse.services.database.catchup import get_catchup_data
from browse.services.database.listings import process_requested_subject
from browse.services.listing import  get_listing_service
from tests.listings.db.test_db_listing_new import validate_new_listing


#PARAMETER TEST SECTION
@pytest.fixture
def app():
    app = Flask(__name__)
    with patch('browse.controllers.catchup_page.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2023, 8, 22)  
        mock_datetime.date = datetime.date 
        mock_datetime.strptime = datetime.strptime   
        yield app

#tests for proccessing parameters
def test_valid_params(app):
    with app.test_request_context('/catchup?subject=math&date=2023-08-10&abs=True&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert subject == ARCHIVES["math"]
        assert start_day == date(year=2023, month=8, day=10)
        assert include_abs == True
        assert page == 2

def test_unexpected_params(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=True&page=2&extra_param=value'):
        with pytest.raises(BadRequest, match="Unexpected parameters"):
            _process_catchup_params()

#subject tests
def test_missing_subject(app):
    with app.test_request_context('/catchup?date=2023-08-10&abs=True&page=2'):
        with pytest.raises(BadRequest, match="Subject required"):
            _process_catchup_params()

def test_invalid_subject(app):
    with app.test_request_context('/catchup?subject=invalid_subject&date=2023-08-10&abs=True&page=2'):
        with pytest.raises(BadRequest, match="Invalid subject"):
            _process_catchup_params()

def test_subject_physics_grp(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=True&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert subject == GROUPS["grp_physics"]

def test_subject_physics_archive(app):
    with app.test_request_context('/catchup?subject=physics&date=2023-08-10&abs=True&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert subject == ARCHIVES["physics"]

def test_subject_category(app):
    with app.test_request_context('/catchup?subject=math.RA&date=2023-08-10&abs=True&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert subject == CATEGORIES["math.RA"]

def test_subject_category_archive(app):
    #archives that are also categories should default to archive to still work with archives like astro-ph which were once a stand alone category and have some papers without subcategories
    with app.test_request_context('/catchup?subject=astro-ph&date=2023-08-10&abs=True&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert subject == ARCHIVES["astro-ph"]

#date tests
def test_missing_date(app):
    with app.test_request_context('/catchup?subject=grp_physics&abs=True&page=2'):
        with pytest.raises(BadRequest, match="Start date required"):
            _process_catchup_params()

def test_invalid_date_format(app):
    #bad order
    with app.test_request_context('/catchup?subject=grp_physics&date=08-10-2023&abs=True&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params()
    #random texts
    with app.test_request_context('/catchup?subject=grp_physics&date=whatsadate&abs=True&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params()
    #missing leading 0s
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-8-10&abs=True&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params()
    #invalid month
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-25-05&abs=True&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params()
    #2 digit year
    with app.test_request_context('/catchup?subject=grp_physics&date=23-05-05&abs=True&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params()

def test_date_unallowed_day(app):
    #fixture set to think today is datetime(2023, 8, 22) 
    #future
    with app.test_request_context(f'/catchup?subject=grp_physics&date=2023-09-10&abs=True&page=2'):
        with pytest.raises(BadRequest, match="Can't request date later than today"):
            _process_catchup_params()

    # too far in the past
    with app.test_request_context(f'/catchup?subject=grp_physics&date=2023-05-22&abs=True&page=2'):
        with pytest.raises(BadRequest, match="Catchup only allowed for past 90 days"):
            _process_catchup_params()

#abstract tests
def test_invalid_abs_value(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=false&page=2'):
        with pytest.raises(BadRequest, match="Invalid abs value"):
            _process_catchup_params()

def test_missing_abs_value(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert include_abs == False  # default

def test_abs_value(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&page=2&abs=False'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert include_abs == False 
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&page=2&abs=True'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert include_abs == True

#page num tests
def test_invalid_page_value(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=True&page=invalid'):
        with pytest.raises(BadRequest, match="Invalid page value"):
            _process_catchup_params()

def test_page_value_0(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=True&page=0'):
        with pytest.raises(BadRequest, match="Invalid page value"):
            _process_catchup_params()

def test_page_value_negative(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=True&page=-3'):
        with pytest.raises(BadRequest, match="Invalid page value"):
            _process_catchup_params()
def test_page_value(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&page=4&abs=False'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert page == 4
def test_page_value_default(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=False'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert page == 1


# DATABASE QUERY SECTION
def test_group_subject_processing():
    result_archs, result_cats=process_requested_subject(GROUPS['grp_physics'])
    expected_archs={
        "astro-ph", 'cond-mat', 'gr-qc', 'hep-ex', 'hep-lat', 'hep-ph', 'hep-th',
        'math-ph', 'nlin', 'nucl-ex', 'nucl-th', 'physics', 'quant-ph',
        'acc-phys','ao-sci', 'atom-ph', 'bayes-an', 'chem-ph', 'plasm-ph', #subsumed into physics
        'adap-org', 'comp-gas', 'chao-dyn', 'solv-int', 'patt-sol', #subsumed into nlin
        'mtrl-th', 'supr-con' #subsumed into cond-mat
                    }
    expected_cats={('math', 'MP')}
    assert result_archs==expected_archs
    assert result_cats==expected_cats

def test_archive_subject_processing():
    #physics archive works seperate from group
    result_archs, result_cats=process_requested_subject(ARCHIVES['physics'])
    expected_archs={ 'physics', 'acc-phys','ao-sci', 'atom-ph', 'bayes-an', 'chem-ph', 'plasm-ph'}
    expected_cats=set()
    assert result_archs==expected_archs
    assert result_cats==expected_cats

    #cs archive has aliases
    result_archs, result_cats=process_requested_subject(ARCHIVES['cs'])
    expected_archs={'cs', 'cmp-lg'}
    expected_cats={('eess','SY'), ('math', 'NA'), ('math', 'IT')}
    assert result_archs==expected_archs
    assert result_cats==expected_cats

def test_category_subject_processing():
    #normal
    result_archs, result_cats=process_requested_subject(CATEGORIES['cs.CC'])
    expected_archs=set()
    expected_cats={('cs','CC')}
    assert result_archs==expected_archs
    assert result_cats==expected_cats

    #alias
    result_archs, result_cats=process_requested_subject(CATEGORIES['q-fin.EC'])
    expected_archs=set()
    expected_cats={('q-fin','EC'), ('econ','GN')}
    assert result_archs==expected_archs
    assert result_cats==expected_cats

    #subsumed
    result_archs, result_cats=process_requested_subject(CATEGORIES['math.DG'])
    expected_archs={'dg-ga'}
    expected_cats={('math','DG')}
    assert result_archs==expected_archs
    assert result_cats==expected_cats

def test_get_catchup_data_basic(app_with_db):
    test_date=date(year=2011, month=2, day=3)
    app = app_with_db
    with app.app_context():
        listing=get_catchup_data(ARCHIVES['math'], test_date, True, 0)
    validate_new_listing(listing.listings)
    assert listing.new_count==0 and listing.cross_count==0 and listing.rep_count==2
    assert listing.announced == date(2011,2,3)
    assert any(
        item.id == "math/0510544" and item.listingType == "rep" and item.primary == "math.RT"
        for item in listing.listings
    )

def test_get_catchup_data_include_alias(app_with_db):
    test_date=date(year=2011, month=2, day=3)
    app = app_with_db
    with app.app_context():
        listing=get_catchup_data(ARCHIVES['math'], test_date, False, 0)
    validate_new_listing(listing.listings)
    assert listing.new_count==0 and listing.cross_count==0 and listing.rep_count==2
    assert listing.announced == date(2011,2,3)
    assert any(
        item.id == "0806.4129" and item.listingType == "rep" and item.primary == "math-ph"
        for item in listing.listings
    )
    assert all(item.id!='0712.3217' for item in listing.listings) #dont include jref entry

def test_get_catchup_no_data(app_with_db):
    test_date=date(year=2011, month=2, day=4)
    app = app_with_db
    with app.app_context():
        listing=get_catchup_data(ARCHIVES['math'], test_date, False, 0)
    validate_new_listing(listing.listings)
    assert listing.new_count==0 and listing.cross_count==0 and listing.rep_count==0
    assert listing.announced == date(2011,2,4)
    assert len(listing.listings)==0

def test_get_catchup_data_grp_physics(app_with_db):
    test_date=date(year=2011, month=2, day=3)
    app = app_with_db
    with app.app_context():
        listing=get_catchup_data(GROUPS['grp_physics'], test_date, False, 0)
    validate_new_listing(listing.listings)
    assert listing.new_count==0 and listing.cross_count==0 and listing.rep_count==4
    assert listing.announced == date(2011,2,3)
    assert any(
        item.id == "hep-th/0703166" and item.listingType == "rep" and item.primary == "hep-th"
        for item in listing.listings
    )

def test_get_catchup_data_wdr(app_with_db):
    test_date=date(year=2011, month=2, day=3)
    app = app_with_db
    with app.app_context():
        listing=get_catchup_data(CATEGORIES['cond-mat.str-el'], test_date, True, 0)
    validate_new_listing(listing.listings)
    assert listing.new_count==0 and listing.cross_count==0 and listing.rep_count==1
    assert listing.announced == date(2011,2,3)
    assert any(
        item.id == "cond-mat/0703772" and item.listingType == "rep" and item.primary == "cond-mat.str-el"
        for item in listing.listings
    )