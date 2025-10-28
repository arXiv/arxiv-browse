from datetime import datetime
from browse.services.database.listings import (
    _all_possible_categories,
    _metadata_to_listing_item,
    _without_deleted
)
from browse.services.listing import ListingItem, get_listing_service, NotModifiedResponse
from arxiv.db.models import Metadata

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


def test_list_dl_links(client_with_db_listings):
    client = client_with_db_listings
    rv = client.get("/list/math/recent")
    assert rv.status_code == 200
    assert '<a href="/pdf/0906.3421" title="Download PDF" id="pdf-0906.3421" aria-labelledby="pdf-0906.3421">pdf</a>' in rv.text
    assert '<a href="/format/0906.3421" title="Other formats" id="oth-0906.3421" aria-labelledby="oth-0906.3421">other</a>' in rv.text
    assert '<a href="/ps/0906.3421" title="Download PostScript" id="ps-0906.3421" aria-labelledby="ps-0906.3421">ps</a>' not in rv.text

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
    assert "nlin.CG" in _all_possible_categories("comp-gas")
    #archive is category and archive
    assert "astro-ph" in _all_possible_categories("astro-ph")
    assert "astro-ph.EP" in _all_possible_categories("astro-ph")

def test_not_modified(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing1=ls.list_pastweek_articles("math", 0, 100, "Wed, 10 Mar 2010 12:34:56 GMT")
        listing2=ls.list_pastweek_articles("math", 0, 100, "Thu, 29 Mar 2012 00:03:56 GMT")
    assert isinstance(listing1, NotModifiedResponse) 
    assert not isinstance(listing2, NotModifiedResponse)

def test_metadata_to_listing_item():
    meta=SAMPLE_METADATA1
    result=_metadata_to_listing_item(meta, "new")
    assert result.article.modified is not None
    
    #test that Null modification dates are handleable
    meta.updated=None
    result=_metadata_to_listing_item(meta, "new")
    assert result.article.modified is not None
    meta.updated=datetime(2000,1,1)
    meta.modtime=None
    result=_metadata_to_listing_item(meta, "new")
    assert result.article.modified is not None
    meta.updated=None
    meta.modtime=None
    result=_metadata_to_listing_item(meta, "new")
    assert result.article.modified is not None

def test_listings_without_deleted():
    """ARXIVCE-4060"""
    orig_items = [ListingItem('2307.10650', "new", "cheese"),
                  ListingItem('2307.10651', "new", "cheese"),
                  ListingItem('2307.10652', "new", "cheese")]
    filtered_items = _without_deleted(orig_items)
    assert "2307.10651" not in [item.id for item in filtered_items]
    assert "2307.10650" in [item.id for item in filtered_items]
    assert "2307.10652" in [item.id for item in filtered_items]

    orig_items2 = [ListingItem('1005.0836', "new", "cheese"),
                   ListingItem('1005.0837', "new", "cheese"),
                   ListingItem('1005.0838', "new", "cheese")]
    filtered_items2 = _without_deleted(orig_items2)
    assert "1005.0836" not in [item.id for item in filtered_items2]
    assert "1005.0837" in [item.id for item in filtered_items2]
    assert "1005.0838" in [item.id for item in filtered_items2]
