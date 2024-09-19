import pytest
from unittest.mock import patch
from datetime import datetime,  date
from flask import Flask
from werkzeug.exceptions import BadRequest
from bs4 import BeautifulSoup

from browse.controllers.catchup_page import _process_catchup_params, GROUPS, ARCHIVES, CATEGORIES, catchup_index_for_types, catchup_paging
from browse.services.database.catchup import get_catchup_data
from browse.services.database.listings import process_requested_subject
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

@pytest.fixture
def app_w_db(dbclient):
    app = Flask(__name__)
    with patch('browse.controllers.catchup_page.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2023, 8, 22)  
        mock_datetime.date = datetime.date 
        mock_datetime.strptime = datetime.strptime   
        yield app

#tests for proccessing parameters
def test_valid_params(app):
    with app.test_request_context('/catchup/math/2023-08-10?abs=True&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params('math','2023-08-10')
        assert subject == ARCHIVES["math"]
        assert start_day == date(year=2023, month=8, day=10)
        assert include_abs == True
        assert page == 2

def test_unexpected_params(app):
    with app.test_request_context('/catchup/grp_physics/2023-08-10?abs=True&page=2&extra_param=value'):
        with pytest.raises(BadRequest, match="Unexpected parameters"):
            _process_catchup_params('grp_physics','2023-08-10')

#subject tests

def test_invalid_subject(app):
    with app.test_request_context('/catchup/invalid_subject/2023-08-10?abs=True&page=2'):
        with pytest.raises(BadRequest, match="Invalid subject"):
            _process_catchup_params('invalid_subject','2023-08-10')

def test_subject_physics_grp(app):
    with app.test_request_context('/catchup/grp_physics/2023-08-10?abs=True&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params('grp_physics','2023-08-10')
        assert subject == GROUPS["grp_physics"]

def test_subject_physics_archive(app):
    with app.test_request_context('/catchup/physics/2023-08-10?abs=True&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params('physics','2023-08-10')
        assert subject == ARCHIVES["physics"]

def test_subject_category(app):
    with app.test_request_context('/catchup/math.RA/2023-08-10?abs=True&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params('math.RA','2023-08-10')
        assert subject == CATEGORIES["math.RA"]

def test_subject_category_archive(app):
    #archives that are also categories should default to archive to still work with archives like astro-ph which were once a stand alone category and have some papers without subcategories
    with app.test_request_context('/catchup/astro-ph/2023-08-10?abs=True&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params('astro-ph','2023-08-10')
        assert subject == ARCHIVES["astro-ph"]

#date tests
def test_invalid_date_format(app):
    #bad order
    with app.test_request_context('/catchup/grp_physics/08-10-2023?abs=True&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params('grp_physics','08-10-2023')
    #random texts
    with app.test_request_context('/catchup/grp_physics/whatsadate?abs=True&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params('grp_physics','whatsadate')
    #missing leading 0s
    with app.test_request_context('/catchup/grp_physics/2023-8-10?abs=True&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params('grp_physics','2023-8-10')
    #invalid month
    with app.test_request_context('/catchup/grp_physics/2023-25-05?abs=True&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params('grp_physics','2023-25-05')
    #2 digit year
    with app.test_request_context('/catchup/grp_physics/23-05-05?abs=True&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params('grp_physics','23-05-05')

def test_date_unallowed_day(app):
    #fixture set to think today is datetime(2023, 8, 22) 
    #future
    with app.test_request_context(f'/catchup/grp_physics/2023-09-10?abs=True&page=2'):
        with pytest.raises(BadRequest, match="Can't request date later than today"):
            _process_catchup_params('grp_physics','2023-09-10')

    # too far in the past
    with app.test_request_context(f'/catchup/grp_physics/2023-05-22?abs=True&page=2'):
        with pytest.raises(BadRequest, match="Catchup only allowed for past 90 days"):
            _process_catchup_params('grp_physics','2023-05-22')

#abstract tests
def test_invalid_abs_value(app):
    with app.test_request_context('/catchup/grp_physics/2023-08-10?abs=false&page=2'):
        with pytest.raises(BadRequest, match="Invalid abs value"):
            _process_catchup_params('grp_physics','2023-08-10')

def test_missing_abs_value(app):
    with app.test_request_context('/catchup/grp_physics/2023-08-10?page=2'):
        subject, start_day, include_abs, page = _process_catchup_params('grp_physics','2023-08-10')
        assert include_abs == False  # default

def test_abs_value(app):
    with app.test_request_context('/catchup/grp_physics/2023-08-10?page=2&abs=False'):
        subject, start_day, include_abs, page = _process_catchup_params('grp_physics','2023-08-10')
        assert include_abs == False 
    with app.test_request_context('/catchup/grp_physics/2023-08-10?page=2&abs=True'):
        subject, start_day, include_abs, page = _process_catchup_params('grp_physics','2023-08-10')
        assert include_abs == True

#page num tests
def test_invalid_page_value(app):
    with app.test_request_context('/catchup/grp_physics/2023-08-10?abs=True&page=invalid'):
        with pytest.raises(BadRequest, match="Invalid page value"):
            _process_catchup_params('grp_physics','2023-08-10')

def test_page_value_0(app):
    with app.test_request_context('/catchup/grp_physics/2023-08-10?abs=True&page=0'):
        with pytest.raises(BadRequest, match="Invalid page value"):
            _process_catchup_params('grp_physics','2023-08-10')

def test_page_value_negative(app):
    with app.test_request_context('/catchup/grp_physics/2023-08-10?abs=True&page=-3'):
        with pytest.raises(BadRequest, match="Invalid page value"):
            _process_catchup_params('grp_physics','2023-08-10')
def test_page_value(app):
    with app.test_request_context('/catchup/grp_physics/2023-08-10?page=4&abs=False'):
        subject, start_day, include_abs, page = _process_catchup_params('grp_physics','2023-08-10')
        assert page == 4
def test_page_value_default(app):
    with app.test_request_context('/catchup/grp_physics/2023-08-10?abs=False'):
        subject, start_day, include_abs, page = _process_catchup_params('grp_physics','2023-08-10')
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

#TESTS FOR THE CONTROLLER PAGE

def test_catchup_index_for_types(app_with_db):
    app = app_with_db
    subj= ARCHIVES['math']
    day=date(year=2024, month=3, day=9)
    base_url='/catchup/math/2024-03-09?abs=False&page='

    #nothing
    result=catchup_index_for_types(0,0,0, subj, day, False, 1 )
    expected=[]
    assert expected ==result['index_for_types']

    #normal all on one page
    result=catchup_index_for_types(5,3,1, subj, day, False, 1 )
    expected=[
        ('New submissions', '', 1),
        ('Cross-lists', '', 6),
        ('Replacements', '', 9),
    ]
    assert expected ==result['index_for_types']

    #all on different page
    with app.test_request_context('/'):
        result=catchup_index_for_types(5,3,1, subj, day, False, 2 )
    expected=[
        ('New submissions', base_url+"1", 1),
        ('Cross-lists', base_url+"1", 6),
        ('Replacements', base_url+"1", 9),
    ]
    assert expected ==result['index_for_types']
    
    #between many pages
    with app.test_request_context('/'):
        result=catchup_index_for_types(2003,2007,2001, subj, day, False, 2 )
    expected=[
        ('New submissions', base_url+"1", 1),
        ('Cross-lists', "", 4),
        ('Replacements', base_url+"3", 11),
    ]
    assert expected ==result['index_for_types']

    #missing a section
    with app.test_request_context('/'):
        result=catchup_index_for_types(2003,0,2001, subj, day, False, 1 )
    expected=[
        ('New submissions', '', 1),
        ('Replacements', base_url+"2", 4),
    ]
    assert expected ==result['index_for_types']

def test_catchup_paging(app_with_db):
    app = app_with_db
    subj=CATEGORIES['math.NA']
    day=date(year=2024, month=3, day=9)
    base_url='/catchup/math.NA/2024-03-09?abs=False&page='

    #1 page
    with app.test_request_context('/'):
        result=catchup_paging(subj, day, False, 1, 6)
    expected=[]
    assert result==expected

    #3 page page first
    with app.test_request_context('/'):
        result=catchup_paging(subj, day, False, 1, 4060)
    expected=[
        ('1', 'no-link'),
        ('2', base_url+'2'),
        ('3', base_url+'3')
    ]
    assert result==expected

    #6 page page last
    with app.test_request_context('/'):
        result=catchup_paging(subj, day, False, 6, 10003)
    expected=[
        ('1', base_url+'1'),
        ('2', base_url+'2'),
        ('3', base_url+'3'),
        ('4', base_url+'4'),
        ('5', base_url+'5'),
        ('6', 'no-link')
    ]
    assert result==expected

    #way too many pages at page 1
    with app.test_request_context('/'):
        result=catchup_paging(subj, day, False, 1, 40000)
    expected=[
        ('1', 'no-link'),
        ('...', 'no-link'),
        ('21', base_url+'21')
    ]
    assert result==expected

    #way too many pages at page 2
    with app.test_request_context('/'):
        result=catchup_paging(subj, day, False, 2, 40000)
    expected=[
        ('1', base_url+'1'),
        ('2', 'no-link'),
        ('...', 'no-link'),
        ('21', base_url+'21')
    ]
    assert result==expected

    #way too many pages at page 3
    with app.test_request_context('/'):
        result=catchup_paging(subj, day, False, 3, 40000)
    expected=[
        ('1', base_url+'1'),
        ('...', 'no-link'),
        ('3', 'no-link'),
        ('...', 'no-link'),
        ('21', base_url+'21')
    ]
    assert result==expected

    #way too many pages at page seccond to last
    with app.test_request_context('/'):
        result=catchup_paging(subj, day, False, 20, 40000)
    expected=[
        ('1', base_url+'1'),
        ('...', 'no-link'),
        ('20', 'no-link'),
        ('21', base_url+'21')
    ]
    assert result==expected

def test_catchup_cacheing(dbclient):
    #category
    resp = dbclient.get("/catchup/math.NA/2024-09-04") 
    assert resp.status_code ==200
    assert 'Surrogate-Control' in resp.headers
    assert resp.headers['Surrogate-Control'] =='max-age=604800'
    assert 'Surrogate-Key' in resp.headers
    header= resp.headers['Surrogate-Key'] 
    assert " catchup " in " "+header+" "
    assert " list-2024-09-math.NA " in " "+header+" "

    #archive
    resp = dbclient.get("/catchup/physics/2024-09-04") 
    assert resp.status_code ==200
    assert 'Surrogate-Control' in resp.headers
    assert resp.headers['Surrogate-Control'] =='max-age=604800'
    assert 'Surrogate-Key' in resp.headers
    header= resp.headers['Surrogate-Key'] 
    assert " catchup " in " "+header+" "
    assert " list-2024-09-physics " in " "+header+" "

    #physics group
    resp = dbclient.get("/catchup/grp_physics/2024-09-04") 
    assert resp.status_code ==200
    assert 'Surrogate-Control' in resp.headers
    assert resp.headers['Surrogate-Control'] =='max-age=604800'
    assert 'Surrogate-Key' in resp.headers
    header= resp.headers['Surrogate-Key'] 
    assert " catchup " in " "+header+" "
    assert " list-2024-09-grp_physics " in " "+header+" "

    #okay with parameters
    resp = dbclient.get("/catchup/grp_physics/2024-09-04?abs=True&page=3") 
    assert resp.status_code ==200
    assert 'Surrogate-Control' in resp.headers
    assert resp.headers['Surrogate-Control'] =='max-age=604800'
    assert 'Surrogate-Key' in resp.headers
    header= resp.headers['Surrogate-Key'] 
    assert " catchup " in " "+header+" "
    assert " list-2024-09-grp_physics " in " "+header+" "

def test_catchup_continue(dbclient):
    #continue link when it should be
    with patch('browse.controllers.catchup_page.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2011, 2, 15)  
        mock_datetime.date = datetime.date 
        mock_datetime.strptime = datetime.strptime  
        resp = dbclient.get("/catchup/math.NA/2011-02-01") 
      
    assert "Continue to the next day" in resp.text

    #continue link not present on last day
    with patch('browse.controllers.catchup_page.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2011, 2, 15)  
        mock_datetime.date = datetime.date 
        mock_datetime.strptime = datetime.strptime  
        resp = dbclient.get("/catchup/math.NA/2011-02-03") 
      
    assert "Continue to the next day" not in resp.text


    #correct continue link
    with patch('browse.controllers.catchup_page.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2011, 2, 15)  
        mock_datetime.date = datetime.date 
        mock_datetime.strptime = datetime.strptime  
        resp = dbclient.get("/catchup/math.NA/2011-02-01") 
      
    assert '<a href="/catchup/math.NA/2011-02-03?abs=False&amp;page=1">Continue to the next day</a>' in resp.text
    
    #correct no updates text
    assert 'No updates for Tue, 01 Feb 2011' in resp.text

    #correct page too far text
   
    with patch('browse.controllers.catchup_page.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2011, 2, 15)  
        mock_datetime.date = datetime.date 
        mock_datetime.strptime = datetime.strptime  
        resp = dbclient.get("/catchup/math.NA/2011-02-03?page=2") 
      
    assert 'No further updates for Thu, 03 Feb 2011' in resp.text

def test_catchup_items(dbclient):

    #basic, no abs
    with patch('browse.controllers.catchup_page.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2011, 2, 15)  
        mock_datetime.date = datetime.date 
        mock_datetime.strptime = datetime.strptime  
        resp = dbclient.get("/catchup/math/2011-02-03") 
      
    assert 'Replacement submissions (showing 2 of 2 entries)' in resp.text
    assert 'arXiv:0806.4129' in resp.text
    assert 'arXiv:math/0510544' in resp.text
    assert 'The structure of Lie algebras, Lie superalgebras and Leibniz algebras' not in resp.text

    #basic, with abs
    with patch('browse.controllers.catchup_page.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2011, 2, 15)  
        mock_datetime.date = datetime.date 
        mock_datetime.strptime = datetime.strptime  
        resp = dbclient.get("/catchup/math/2011-02-03?abs=True") 
      
    assert 'Replacement submissions (showing 2 of 2 entries)' in resp.text
    assert 'arXiv:0806.4129' in resp.text
    assert 'arXiv:math/0510544' in resp.text
    assert 'The structure of Lie algebras, Lie superalgebras and Leibniz algebras' in resp.text


def test_catchup_form(dbclient):
    resp = dbclient.get("/catchup") 

    #page headers
    assert resp.status_code ==200
    assert 'Surrogate-Control' in resp.headers
    assert resp.headers['Surrogate-Control'] =='max-age=604800'
    assert 'Surrogate-Key' in resp.headers
    header= resp.headers['Surrogate-Key'] 
    assert " catchup " in " "+header+" "
    assert " catchup-form " in " "+header+" "

    #form feilds
    soup = BeautifulSoup(resp.data, 'html.parser')
    form = soup.find('form', id='catchup-form')
    assert form is not None

    # hidden fields
    assert soup.find('input', {'type': 'hidden', 'id': 'subject', 'name': 'subject'}) is not None
    assert soup.find('input', {'type': 'hidden', 'id': 'date', 'name': 'date'}) is not None

    #subsection fields 
    assert form.find('select', {'id': 'day'}) is not None
    assert form.find('select', {'id': 'month'}) is not None
    assert form.find('select', {'id': 'year'}) is not None

    assert form.find('select', {'id': 'default-archives'}) is not None
    assert form.find('select', {'id': 'grp_math-archives'}) is not None
    assert form.find('select', {'id': 'default-categories'}) is not None
    assert form.find('select', {'id': 'hep-lat-categories'}) is not None
    assert form.find('select', {'id': 'group'}) is not None
  
    assert form.find('input', {'name': 'include_abs', 'type': 'checkbox'})  is not None


def test_catchup_form_redirect(dbclient):
    resp = dbclient.get("/catchup?subject=cs&date=2024-09-03" , follow_redirects=False) 
    assert resp.status_code ==301
    redirect_location = resp.headers.get("Location")
    assert redirect_location == "/catchup/cs/2024-09-03"

    assert 'Surrogate-Control' in resp.headers
    assert resp.headers['Surrogate-Control'] =='max-age=2600000'
    assert 'Surrogate-Key' in resp.headers
    header= resp.headers['Surrogate-Key'] 
    assert " catchup " in " "+header+" "
    assert " catchup-redirect " in " "+header+" "