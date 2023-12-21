from browse.services.database import (
    _combine_yearly_article_counts,
    _process_yearly_article_counts,
    get_yearly_article_counts,
)
from browse.services.listing import YearCount, MonthCount, hybrid_listing

from unittest.mock import MagicMock, patch
from flask import g, current_app


def test_combine_yearly_article_counts():
    months1 = [
        MonthCount(2005, 1, 1, 1),
        MonthCount(2005, 2, 2, 2),
        MonthCount(2005, 3, 5, 16),
        MonthCount(2005, 4, 7, 0),
        MonthCount(2005, 5, 11, 21),
        MonthCount(2005, 6, 19, 1),
        MonthCount(2005, 7, 0, 1),
        MonthCount(2005, 8, 0, 6),
        MonthCount(2005, 9, 1, 1),
        MonthCount(2005, 10, 45, 2),
        MonthCount(2005, 11, 1, 1),
        MonthCount(2005, 12, 3, 5),
    ]
    months2 = [
        MonthCount(2005, 1, 0, 5),
        MonthCount(2005, 2, 0, 0),
        MonthCount(2005, 3, 1, 7),
        MonthCount(2005, 4, 3, 8),
        MonthCount(2005, 5, 71, 2),
        MonthCount(2005, 6, 9, 51),
        MonthCount(2005, 7, 0, 4),
        MonthCount(2005, 8, 50, 6),
        MonthCount(2005, 9, 1, 1),
        MonthCount(2005, 10, 4, 22),
        MonthCount(2005, 11, 1, 1),
        MonthCount(2005, 12, 3, 5),
    ]
    months_total = [
        MonthCount(2005, 1, 1, 6),
        MonthCount(2005, 2, 2, 2),
        MonthCount(2005, 3, 6, 23),
        MonthCount(2005, 4, 10, 8),
        MonthCount(2005, 5, 82, 23),
        MonthCount(2005, 6, 28, 52),
        MonthCount(2005, 7, 0, 5),
        MonthCount(2005, 8, 50, 12),
        MonthCount(2005, 9, 2, 2),
        MonthCount(2005, 10, 49, 24),
        MonthCount(2005, 11, 2, 2),
        MonthCount(2005, 12, 6, 10),
    ]
    year1 = YearCount(2005, 95, 57, months1)
    year2 = YearCount(2005, 143, 112, months2)
    year_total = YearCount(2005, 238, 169, months_total)

    assert year_total == _combine_yearly_article_counts(year1, year2)
    assert year_total.new_count == sum(month.new for month in year_total.by_month)
    assert year_total.cross_count == sum(month.cross for month in year_total.by_month)


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


def test_get_yearly_article_counts(app_with_hybrid_listings):
    app = app_with_hybrid_listings
    with app.app_context():
        # pre id-swap
        # TODO cant test old data on sqlite

        # post id-swap

        months = [
            MonthCount(2009, 1, 0, 0),
            MonthCount(2009, 2, 0, 0),
            MonthCount(2009, 3, 1, 0),
            MonthCount(2009, 4, 1, 0),
            MonthCount(2009, 5, 0, 0),
            MonthCount(2009, 6, 1, 1),
            MonthCount(2009, 7, 0, 0),
            MonthCount(2009, 8, 0, 0),
            MonthCount(2009, 9, 1, 1),
            MonthCount(2009, 10, 1, 0),
            MonthCount(2009, 11, 2, 0),
            MonthCount(2009, 12, 1, 0),
        ]
        year1 = YearCount(2009, 8, 2, months)

        assert year1 == get_yearly_article_counts(
            "cond-mat", 2009
        )  # this is dependedant in the data in the test databse not changing

        # 2007 mid id-swap
        # TODO cant test early 2007 data on sqlite


@patch("browse.services.database._get_yearly_article_counts_old_id")
def test_year_page_hybrid(mock, client_with_hybrid_listings):
    client = client_with_hybrid_listings

    mock.return_value = YearCount(1998)  # TODO dont mock function if able to run on sql
    rv = client.get("/year/cond-mat/98")
    assert rv.status_code == 200

    mock.return_value = YearCount(2007)  # TODO dont mock function if able to run on sql
    rv = client.get("/year/cond-mat/07")
    assert rv.status_code == 200

    # has data in test database
    rv = client.get("/year/cond-mat/09")
    assert rv.status_code == 200
    text = rv.text
    assert '<a href="/year/cond-mat/11">2011</a>' in text
    assert "<p>2009 totals: <b>8 articles</b> + <i>2 cross-lists</i></p>" in text
    assert (
        "<a href=/list/cond-mat/200911?skip=0>|</a>      <b>2</b> + 0 (Nov 2009)"
        in text
    )
    assert '<a href="/year/cond-mat/92">1992</a>' in text

    rv = client.get("/year/cs/23")
    assert rv.status_code == 200
    text = rv.text
    assert '<a href="/year/cs/92">1992</a>' not in text  # cs didnt exist in 1992


def test_monthly_counts_hybrid(app_with_hybrid_listings):
    from browse.services.listing import get_listing_service

    app = app_with_hybrid_listings
    with app.app_context():
        ls = get_listing_service()
        result = ls.monthly_counts("cond-mat", 2009)

        months = [
            MonthCount(2009, 1, 0, 0),
            MonthCount(2009, 2, 0, 0),
            MonthCount(2009, 3, 1, 0),
            MonthCount(2009, 4, 1, 0),
            MonthCount(2009, 5, 0, 0),
            MonthCount(2009, 6, 1, 1),
            MonthCount(2009, 7, 0, 0),
            MonthCount(2009, 8, 0, 0),
            MonthCount(2009, 9, 1, 1),
            MonthCount(2009, 10, 1, 0),
            MonthCount(2009, 11, 2, 0),
            MonthCount(2009, 12, 1, 0),
        ]
        year = YearCount(2009, 8, 2, months)
        assert result == year

def test_finds_archives_with_no_categories(app_with_hybrid_listings):
    app = app_with_hybrid_listings
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
