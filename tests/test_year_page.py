
from browse.services.database.listings import (
    _process_yearly_article_counts,
    get_yearly_article_counts)
from browse.services.listing import YearCount, MonthCount, get_listing_service

from unittest.mock import MagicMock, patch


def test_process_yearly_article_counts():
    row1 = MagicMock()
    row1.month = "01"
    row1.count_new = 5
    row1.count_cross = 3

    row2 = MagicMock()
    row2.month = "02"
    row2.count_new = 8
    row2.count_cross = 2

    row3 = MagicMock()
    row3.month = "11"
    row3.count_new = 84
    row3.count_cross = 0

    query_result = [row1, row2, row3]

    months = [
        MonthCount(2021, 1, 5, 3),
        MonthCount(2021, 2, 8, 2),
        MonthCount(2021, 3, 0, 0),
        MonthCount(2021, 4, 0, 0),
        MonthCount(2021, 5, 0, 0),
        MonthCount(2021, 6, 0, 0),
        MonthCount(2021, 7, 0, 0),
        MonthCount(2021, 8, 0, 0),
        MonthCount(2021, 9, 0, 0),
        MonthCount(2021, 10, 0, 0),
        MonthCount(2021, 11, 84, 0),
        MonthCount(2021, 12, 0, 0),
    ]
    year = YearCount(2021, 97, 5, months)

    result = _process_yearly_article_counts(query_result, year=2021)

    assert result == year


def test_get_yearly_article_counts(app_with_db):
    app = app_with_db
    with app.app_context():
        # pre id-swap
        # TODO cant test old data on sqlite

        # post id-swap

        months = [
            MonthCount(2009, 1, 0, 0),
            MonthCount(2009, 2, 0, 0),
            MonthCount(2009, 3, 0, 0),
            MonthCount(2009, 4, 0, 0),
            MonthCount(2009, 5, 0, 0),
            MonthCount(2009, 6, 1, 1),
            MonthCount(2009, 7, 0, 0),
            MonthCount(2009, 8, 0, 0),
            MonthCount(2009, 9, 0, 0),
            MonthCount(2009, 10, 0, 0),
            MonthCount(2009, 11, 0, 0),
            MonthCount(2009, 12, 0, 0),
        ]
        year1 = YearCount(2009, 1, 1, months)

        assert year1 == get_yearly_article_counts(
            "cond-mat", 2009
        )  # this is dependedant in the data in the test databse not changing

        # 2007 mid id-swap
        # TODO cant test early 2007 data on sqlite

@patch("browse.services.listing.db_listings.get_yearly_article_counts")
def test_year_page_db(mock, client_with_db_listings):
    client = client_with_db_listings

    mock.return_value = YearCount(1998)  # TODO dont mock function if able to run on sql
    rv = client.get("/year/cond-mat/1998")
    assert rv.status_code == 200

    mock.return_value = YearCount(2007)  # TODO dont mock function if able to run on sql
    rv = client.get("/year/cond-mat/2007")
    assert rv.status_code == 200


def test_year_page_data_db(client_with_db_listings):
    client = client_with_db_listings

    # has data in test database
    rv = client.get("/year/math/2009")
    assert rv.status_code == 200
    text = rv.text
    assert '<a href="/year/math/2011">2011</a>' in text
    assert "<p>2009 totals: <b>4 articles</b> + <i>0 cross-lists</i></p>" in text
    assert (
        "<a href=/list/math/2009-06?skip=0>|</a>      <b>4</b> + 0 (Jun 2009)"
        in text
    ) #TODO change this back to 4 digit year when all of listings is running on browse
    assert '<a href="/year/math/1992">1992</a>' in text

    rv = client.get("/year/cs/2023")
    assert rv.status_code == 200
    text = rv.text
    assert '<a href="/year/cs/1992">1992</a>' not in text  # cs didnt exist in 1992


def test_monthly_counts_db(app_with_db):

    app = app_with_db
    with app.app_context():
        ls = get_listing_service()
        result = ls.monthly_counts("cond-mat", 2009)

        months = [
            MonthCount(2009, 1, 0, 0),
            MonthCount(2009, 2, 0, 0),
            MonthCount(2009, 3, 0, 0),
            MonthCount(2009, 4, 0, 0),
            MonthCount(2009, 5, 0, 0),
            MonthCount(2009, 6, 1, 1),
            MonthCount(2009, 7, 0, 0),
            MonthCount(2009, 8, 0, 0),
            MonthCount(2009, 9, 0, 0),
            MonthCount(2009, 10, 0, 0),
            MonthCount(2009, 11, 0, 0),
            MonthCount(2009, 12, 0, 0),
        ]
        year = YearCount(2009, 1, 1, months)
        assert result == year

def test_finds_archives_with_no_categories(app_with_db):
    app = app_with_db
    with app.app_context():

        months = [
            MonthCount(2009, 1, 0, 0),
            MonthCount(2009, 2, 0, 0),
            MonthCount(2009, 3, 0, 0),
            MonthCount(2009, 4, 0, 0),
            MonthCount(2009, 5, 0, 0),
            MonthCount(2009, 6, 1, 0),
            MonthCount(2009, 7, 1, 0),
            MonthCount(2009, 8, 0, 0),
            MonthCount(2009, 9, 0, 0),
            MonthCount(2009, 10, 0, 0),
            MonthCount(2009, 11, 0, 0),
            MonthCount(2009, 12, 0, 0),
        ]
        year1 = YearCount(2009, 2, 0, months)

        assert year1 == get_yearly_article_counts(
            "gr-qc", 2009
        )  
