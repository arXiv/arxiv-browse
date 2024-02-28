from browse.services.database.listings import (
    _check_alternate_name,
    _all_possible_categories
)
from browse.services.listing import get_listing_service, NotModifiedResponse

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

def test_not_modified(app_with_hybrid_listings):
    app = app_with_hybrid_listings
    with app.app_context():
        ls=get_listing_service()
        listing1=ls.list_pastweek_articles("math", 0, 100, "Wed, 10 Mar 2010 12:34:56 GMT")
        listing2=ls.list_pastweek_articles("math", 0, 100, "Thu, 29 Mar 2012 00:03:56 GMT")
    assert isinstance(listing1, NotModifiedResponse) 
    assert not isinstance(listing2, NotModifiedResponse)
