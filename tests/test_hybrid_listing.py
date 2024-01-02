from datetime import datetime

from browse.services.database.listings import (
    _combine_yearly_article_counts,
    _process_yearly_article_counts,
    get_yearly_article_counts,
    _check_alternate_name,
    _all_possible_categories,
    _entries_into_listing_items,
    get_articles_for_month
)
from browse.services.listing import YearCount, MonthCount, get_listing_service
from browse.services.database.models import Metadata

from unittest.mock import MagicMock, patch
from flask import g, current_app

SAMPLE_METADATA1=Metadata(
    metadata_id = 1,
    document_id = 1,
    paper_id = "1234.5678",
    created = datetime(2008,11,1,15,7,3),
    updated = datetime(2008,11,1,19,30,20),
    submitter_id = 7,
    submitter_name = "Marco",
    submitter_email = "fake@email.com",
    source_size = 700,
    source_format = "tex",
    source_flags = 1,
    title = "It's a title",
    authors = "Not Marco",
    abs_categories = "cs.CG cs.LO",
    comments = "comments here",
    proxy = None,
    report_num = None,
    msc_class = None,
    acm_class = None,
    journal_ref = "Very Impressive Journal",
    doi = None,
    abstract = "Sample text",
    license = "license",
    version = 1,
    modtime = 50,
    is_current = 1,
    is_withdrawn = 0
)

SAMPLE_METADATA2=Metadata(
    metadata_id = 2,
    document_id = 2,
    paper_id = "1234.5679",
    created = datetime(2008,11,1,15,7,3),
    updated = datetime(2008,11,1,19,30,20),
    submitter_id = 7,
    submitter_name = "Marco",
    submitter_email = "fake@email.com",
    source_size = 700,
    source_format = "tex",
    source_flags = 1,
    title = "It's a title",
    authors = "Not Marco",
    abs_categories = "cs.LO cs.CG",
    comments = "comments here",
    proxy = None,
    report_num = None,
    msc_class = None,
    acm_class = None,
    journal_ref = "Very Impressive Journal",
    doi = None,
    abstract = "Sample text",
    license = "license",
    version = 1,
    modtime = 50,
    is_current = 1,
    is_withdrawn = 0
)


#listing pages below
def test_alt_name():
    #aliases both directions
    assert "math.MP"==_check_alternate_name("math-ph")
    assert "math-ph"==_check_alternate_name("math.MP")

    #subsumed only fetches older names
    assert "cs.CL"!=_check_alternate_name("cmp-lg")
    assert "cmp-lg"==_check_alternate_name("cs.CL")

def test_possible_categories():
    
    assert ["math.KT"]==_all_possible_categories("math.KT") #single category

    #single category with different name
    assert "cs.SY" in _all_possible_categories("eess.SY")
    assert "eess.SY" in _all_possible_categories("eess.SY")

    #new archive
    assert "q-alg" in _all_possible_categories("math") 
    assert "stat.TH" in _all_possible_categories("math")
    assert "math.GM" in _all_possible_categories("math")
    #legacy archive
    assert "comp-gas" in _all_possible_categories("comp-gas")
    assert "nlin.CG" not in _all_possible_categories("comp-gas")
    #archive is category and archive
    assert "astro-ph" in _all_possible_categories("astro-ph")
    assert "astro-ph.EP" in _all_possible_categories("astro-ph")

def test_transform_into_listing():
    items=[(SAMPLE_METADATA1,1),(SAMPLE_METADATA2,0)]
    new, cross=_entries_into_listing_items(items)

    assert len(new)==1 and len(cross)==1
    assert new[0].id=="1234.5678" and cross[0].id=="1234.5679"
    assert new[0].primary=="cs.CG" and cross[0].primary=="cs.LO"
    assert new[0].article.arxiv_id_v=="1234.5678v1" and cross[0].article.arxiv_id_v=="1234.5679v1"

def test_listings_for_month(app_with_hybrid_listings):
    app = app_with_hybrid_listings
    with app.app_context():
        ls=get_listing_service()
        #finds primary listings for a category
        items=ls.list_articles_by_month("math.CO", 2009, 6, 0,25)
        assert items.pubdates[0][0].year==2009 and items.pubdates[0][0].month==6
        assert any(item.id=="0906.3421" and item.listingType=="new" for item in items.listings)

        #finds cross listings for a category
        items=ls.list_articles_by_month("math.CT", 2009, 6, 0,25)
        assert any(item.id=="0906.4150" and item.listingType=="cross" for item in items.listings)

        #finds listsings within an archive
        items=ls.list_articles_by_month("math", 2009, 6, 0,25)
        assert items.count>=4
        assert any(item.id=="0906.4150" and item.listingType=="new" for item in items.listings)

        #alias still primary
        items=ls.list_articles_by_month("math.MP", 2008, 6, 0,25) 
        assert any(item.id=="0806.4129" and item.listingType=="new" for item in items.listings)
        items=ls.list_articles_by_month("eess.SY", 2010, 8, 0,25) 
        assert any(item.id=="1008.3222" and item.listingType=="new" for item in items.listings)

        #alias in other archive listing
        items=ls.list_articles_by_month("cs", 2007, 12, 0,25) 
        assert any(item.id=="0712.3217" and item.listingType=="new" for item in items.listings)

        #pagination
        items1=ls.list_articles_by_month("math", 2009, 6, 0,2)
        items2=ls.list_articles_by_month("math", 2009, 6, 2,25)
        assert items1.count>2
        assert items1.count== items2.count
        assert items1.listings[0] not in items2.listings
        assert items1.listings[1] not in items2.listings
        assert len(items1.listings)==2
        assert len(items2.listings)>=2

        #subsumed archives are found
        items=ls.list_articles_by_month('nlin.CD', 1995, 10, 0,25)
        assert any(item.id=="chao-dyn/9510015" and item.listingType=="new" for item in items.listings)

        #new categories are not found in subsumed archvies
        items=ls.list_articles_by_month("chao-dyn", 2008, 12, 0,25)
        assert not any(item.id=="0812.4551" for item in items.listings)

        #old style id
        items=ls.list_articles_by_month("cond-mat.mes-hall", 2005, 1, 0,25)
        assert items.pubdates[0][0].year==2005 and items.pubdates[0][0].month==1
        assert any(item.id=="cond-mat/0501593" and item.listingType=="new" for item in items.listings)

        #2007 finds both styles
        items=ls.list_articles_by_month("math.PR", 2007, 12, 0,25)
        assert any(item.id=="0712.3217" and item.listingType=="cross" for item in items.listings)
        items=ls.list_articles_by_month("hep-th", 2007, 3, 0,25)
        assert any(item.id=="hep-th/0703166" and item.listingType=="new" for item in items.listings)
    
        #two digit year
        items=ls.list_articles_by_month('nlin.CD', 95, 10, 0,25)
        assert items.pubdates[0][0].year==1995 and items.pubdates[0][0].month==10
        assert any(item.id=="chao-dyn/9510015" and item.listingType=="new" for item in items.listings)
        items=ls.list_articles_by_month("math.CO", 9, 6, 0,25)
        assert items.pubdates[0][0].year==2009 and items.pubdates[0][0].month==6
        assert any(item.id=="0906.3421" and item.listingType=="new" for item in items.listings)

def test_listings_for_year(app_with_hybrid_listings):
    app = app_with_hybrid_listings
    with app.app_context():
        ls=get_listing_service()

        #items from different months
        items=ls.list_articles_by_month("gr-qc", 2009, None, 0,25)
        assert items.pubdates[0][0].year==2009
        assert items.count>=2
        assert any(item.id=="0907.2020" and item.listingType=="new" for item in items.listings)
        assert any(item.id=="0906.5504" and item.listingType=="new" for item in items.listings)

        #old ids
        items=ls.list_articles_by_month("gr-qc", 2009, None, 0,25)
        assert items.pubdates[0][0].year==2009
        assert items.count>=2
        assert any(item.id=="0907.2020" and item.listingType=="new" for item in items.listings)
        assert any(item.id=="0906.5504" and item.listingType=="new" for item in items.listings)

        #two digit year
        items=ls.list_articles_by_month('ao-sci', 95, None, 0,25)
        assert items.pubdates[0][0].year==1995 
        assert any(item.id=="chao-dyn/9510015" and item.listingType=="cross" for item in items.listings)
        items=ls.list_articles_by_month("math.CO", 9, None, 0,25)
        assert items.pubdates[0][0].year==2009
        assert any(item.id=="0906.3421" and item.listingType=="new" for item in items.listings)

def test_month_listing_page( client_with_hybrid_listings):
    client = client_with_hybrid_listings

    rv = client.get("/list/chao-dyn/199510")
    assert rv.status_code == 200
    text = rv.text
    #page formatting
    assert 'Chaotic Dynamics' in text
    assert 'Authors and titles for October 1995' in text
    #listing item dispalyed properly
    assert 'Estimating the Attractor Dimension of the Equatorial Weather System'in text #TODO change this back to 4 digit year when all of listings is running on browse
    #print(text)
    assert '<a href ="/abs/chao-dyn/9510015" title="Abstract" id="chao-dyn/9510015">\n        arXiv:chao-dyn/9510015\n      </a>' in text
    assert '<a href="https://arxiv.org/search/chao-dyn?searchtype=author&amp;query=Tiong,+M+L+B">Melvin Leok Boon Tiong</a>' in text

    #two digit year
    rv = client.get("/list/chao-dyn/9510")
    assert rv.status_code == 200
    text = rv.text
    assert '<a href ="/abs/chao-dyn/9510015" title="Abstract" id="chao-dyn/9510015">\n        arXiv:chao-dyn/9510015\n      </a>' in text
    assert 'Authors and titles for October 1995' in text

    #TODO make sure subsumed archives go to the new page

def test_year_listing_page( client_with_hybrid_listings):
    client = client_with_hybrid_listings

    #two digit year
    rv = client.get("/list/chao-dyn/95")
    assert rv.status_code == 200
    text = rv.text
    #page formatting
    assert 'Chaotic Dynamics' in text
    assert 'Authors and titles for 1995' in text
    #listing item dispalyed properly
    assert 'Estimating the Attractor Dimension of the Equatorial Weather System'in text #TODO change this back to 4 digit year when all of listings is running on browse
    #print(text)
    assert '<a href ="/abs/chao-dyn/9510015" title="Abstract" id="chao-dyn/9510015">\n        arXiv:chao-dyn/9510015\n      </a>' in text
    assert '<a href="https://arxiv.org/search/chao-dyn?searchtype=author&amp;query=Tiong,+M+L+B">Melvin Leok Boon Tiong</a>' in text
    
    #TODO fix conflist with YYMM
    # rv = client.get("/list/chao-dyn/1995")
    # assert rv.status_code == 200
    # text = rv.text
    # assert '<a href ="/abs/chao-dyn/9510015" title="Abstract" id="chao-dyn/9510015">\n        arXiv:chao-dyn/9510015\n      </a>' in text
    # assert 'Authors and titles for October 1995' in text

#year page below

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


@patch("browse.services.database.listings._get_yearly_article_counts_old_id")
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
        "<a href=/list/cond-mat/0911?skip=0>|</a>      <b>2</b> + 0 (Nov 2009)"
        in text
    ) #TODO change this back to 4 digit year when all of listings is running on browse
    assert '<a href="/year/cond-mat/92">1992</a>' in text

    rv = client.get("/year/cs/23")
    assert rv.status_code == 200
    text = rv.text
    assert '<a href="/year/cs/92">1992</a>' not in text  # cs didnt exist in 1992


def test_monthly_counts_hybrid(app_with_hybrid_listings):

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
