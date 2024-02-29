from datetime import datetime
from browse.services.database.listings import (
    _check_alternate_name,
    _all_possible_categories,
    _metadata_to_listing_item
)
from browse.services.listing import get_listing_service, NotModifiedResponse
from browse.services.database.models import Metadata

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