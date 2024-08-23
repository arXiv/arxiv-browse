import pytest
from unittest.mock import patch
from datetime import datetime, timedelta, date
from flask import Flask, request
from werkzeug.exceptions import BadRequest

from browse.controllers.catchup_page import _process_catchup_params, GROUPS, ARCHIVES, CATEGORIES

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
    with app.test_request_context('/catchup?subject=math&date=2023-08-10&abs=true&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert subject == ARCHIVES["math"]
        assert start_day == date(year=2023, month=8, day=10)
        assert include_abs == True
        assert page == 2

def test_unexpected_params(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=true&page=2&extra_param=value'):
        with pytest.raises(BadRequest, match="Unexpected parameters"):
            _process_catchup_params()

#subject tests
def test_missing_subject(app):
    with app.test_request_context('/catchup?date=2023-08-10&abs=true&page=2'):
        with pytest.raises(BadRequest, match="Subject required"):
            _process_catchup_params()

def test_invalid_subject(app):
    with app.test_request_context('/catchup?subject=invalid_subject&date=2023-08-10&abs=true&page=2'):
        with pytest.raises(BadRequest, match="Invalid subject"):
            _process_catchup_params()

def test_subject_physics_grp(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=true&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert subject == GROUPS["grp_physics"]

def test_subject_physics_archive(app):
    with app.test_request_context('/catchup?subject=physics&date=2023-08-10&abs=true&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert subject == ARCHIVES["physics"]

def test_subject_category(app):
    with app.test_request_context('/catchup?subject=math.RA&date=2023-08-10&abs=true&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert subject == CATEGORIES["math.RA"]

def test_subject_category_archive(app):
    #archives that are also categories should default to archive to still work with archives like astro-ph which were once a stand alone category and have some papers without subcategories
    with app.test_request_context('/catchup?subject=astro-ph&date=2023-08-10&abs=true&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert subject == ARCHIVES["astro-ph"]

#date tests
def test_missing_date(app):
    with app.test_request_context('/catchup?subject=grp_physics&abs=true&page=2'):
        with pytest.raises(BadRequest, match="Start date required"):
            _process_catchup_params()

def test_invalid_date_format(app):
    #bad order
    with app.test_request_context('/catchup?subject=grp_physics&date=08-10-2023&abs=true&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params()
    #random texts
    with app.test_request_context('/catchup?subject=grp_physics&date=whatsadate&abs=true&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params()
    #missing leading 0s
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-8-10&abs=true&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params()
    #invalid month
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-25-05&abs=true&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params()
    #2 digit year
    with app.test_request_context('/catchup?subject=grp_physics&date=23-05-05&abs=true&page=2'):
        with pytest.raises(BadRequest, match="Invalid date format"):
            _process_catchup_params()

def test_date_unallowed_day(app):
    #fixture set to think today is datetime(2023, 8, 22) 
    #future
    with app.test_request_context(f'/catchup?subject=grp_physics&date=2023-09-10&abs=true&page=2'):
        with pytest.raises(BadRequest, match="Can't request date later than today"):
            _process_catchup_params()

    # too far in the past
    with app.test_request_context(f'/catchup?subject=grp_physics&date=2023-05-22&abs=true&page=2'):
        with pytest.raises(BadRequest, match="Catchup only allowed for past 90 days"):
            _process_catchup_params()

#abstract tests
def test_invalid_abs_value(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=Fralse&page=2'):
        with pytest.raises(BadRequest, match="Invalid abs value"):
            _process_catchup_params()

def test_missing_abs_value(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&page=2'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert include_abs == False  # default

def test_abs_value(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&page=2&abs=false'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert include_abs == False 
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&page=2&abs=true'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert include_abs == True

#page tests
def test_invalid_page_value(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=true&page=invalid'):
        with pytest.raises(BadRequest, match="Invalid page value"):
            _process_catchup_params()

def test_page_value_0(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=true&page=0'):
        with pytest.raises(BadRequest, match="Invalid page value"):
            _process_catchup_params()

def test_page_value_negative(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=true&page=-3'):
        with pytest.raises(BadRequest, match="Invalid page value"):
            _process_catchup_params()
def test_page_value(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&page=4&abs=false'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert page == 4
def test_page_value_default(app):
    with app.test_request_context('/catchup?subject=grp_physics&date=2023-08-10&abs=false'):
        subject, start_day, include_abs, page = _process_catchup_params()
        assert page == 1