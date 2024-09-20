from datetime import date
from typing import List

from browse.services.listing import  get_listing_service, ListingItem

def validate_new_listing(listing: List[ListingItem]):
    all_ids=set()
    for item in listing:
        assert item.id not in all_ids
        all_ids.add(item.id)
        assert item.listingType!="no_match"

def test_basic_listing(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_new_articles("math.RT", 0, 15)
    validate_new_listing(listing.listings)
    assert listing.new_count==0 and listing.cross_count==0 and listing.rep_count==1
    assert listing.announced == date(2011,2,3)
    assert any(
        item.id == "math/0510544" and item.listingType == "rep" and item.primary == "math.RT"
        for item in listing.listings
    )

def test_no_abs(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_new_articles("math.PR", 0, 100)
    validate_new_listing(listing.listings)
    assert all(item.id !="0712.3217" for item in listing.listings)

def test_no_replacements_above_5(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_new_articles("math.DG", 0, 100)
    validate_new_listing(listing.listings)
    assert all(item.id !="0906.3336" for item in listing.listings)
    
def test_find_alias(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_new_articles("eess.SY", 0, 15)
    validate_new_listing(listing.listings)
    assert any(item.id =="1008.3222" and item.listingType=="new" for item in listing.listings)
    
def test_identify_new(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_new_articles("math.CO", 0, 15)
    validate_new_listing(listing.listings)
    assert any(item.id =="0906.3421" and item.listingType=="new" for item in listing.listings)

def test_identify_new_cross(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_new_articles("cond-mat.stat-mech", 0, 15)
    validate_new_listing(listing.listings)
    assert any(item.id =="0906.3421" and item.listingType=="cross" for item in listing.listings)

def test_identify_cross(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_new_articles("math.NT", 0, 15)
    validate_new_listing(listing.listings)
    assert any(item.id =="0906.2112" and item.listingType=="cross" for item in listing.listings)

def test_identify_replace(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing1=ls.list_new_articles("math-ph", 0, 15)
        listing2=ls.list_new_articles("cond-mat.mtrl-sci", 0, 15)
    validate_new_listing(listing1.listings)
    validate_new_listing(listing2.listings)
    #primary replacement
    assert any(item.id =="0806.4129" and item.listingType=="rep" for item in listing1.listings)
    # cross listing replacement aka rep-cross
    assert any(item.id =="cond-mat/0703772" and item.listingType=="rep" for item in listing2.listings)
    
def test_listing_counts(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_new_articles("math", 0, 100)
    validate_new_listing(listing.listings)
    assert listing.new_count==1
    assert listing.cross_count==1
    assert listing.rep_count==4
    assert len(listing.listings) == listing.new_count + listing.cross_count + listing.rep_count

def test_listing_order(app_with_db):
    #new then cross then replace then replace cross
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_new_articles("math", 0, 100)
    validate_new_listing(listing.listings)
    order={"new":1, "cross":2, "rep":3}
    current_min=1
    last_id="0" #its string ordering and some old ids start with letters
    now_repcross=False
    for item in listing.listings:
        score=order[item.listingType] 
        assert score >= current_min
        if score > current_min:
            current_min=score
            last_id=item.id
        else:
            if not now_repcross and item.listingType=="rep" and item.id<last_id:
                #replace is allowed to have one disconnect between rep and repcross
                now_repcross=True
            else:
                assert item.id>last_id
            last_id=item.id
    
def test_pagination(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing1=ls.list_new_articles("math", 0, 1)
        listing2=ls.list_new_articles("math", 1, 14)
    validate_new_listing(listing1.listings)
    validate_new_listing(listing2.listings)
    assert listing1.new_count==listing2.new_count
    assert listing1.cross_count==listing2.cross_count
    assert listing1.rep_count==listing2.rep_count
    assert len(listing1.listings)==1
    assert len(listing2.listings)>0
    first_id=listing1.listings[0].id
    assert all(item.id !=first_id for item in listing2.listings)
    
def test_archive_listing(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing1=ls.list_new_articles("math", 0, 30)
        listing2=ls.list_new_articles("eess", 0, 15)

    #finds different math categories
    validate_new_listing(listing1.listings)
    assert any(item.id =="0806.4129" and item.listingType == "rep" for item in listing1.listings)
    assert any(item.id =="math/0510544" and item.listingType == "rep" for item in listing1.listings)
    
    #finds alias category in alternate archive
    validate_new_listing(listing2.listings)
    assert any(item.id =="1008.3222" and item.listingType == "new" for item in listing2.listings)

def test_intra_archive_crosses(app_with_db):
    #crosslists from one category into another shouldnt appear as crosses on the archive page
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_new_articles("math", 0, 30)
    validate_new_listing(listing.listings)
    assert all(item.id !="0906.2112" or item.listingType != "cross" for item in listing.listings)

def test_new_listing_page( client_with_db_listings):
    client = client_with_db_listings
    rv = client.get("/list/math.RT/new")
    assert rv.status_code == 200
    text = rv.text
    assert "Replacement submissions" in text
    assert "arXiv:math/0510544" in text
    assert "Leibniz superalgebras graded by finite root systems" in text
    assert "showing 1 of 1 entries" in text

def test_new_listing_page_alternate_names( client_with_db_listings):
    client = client_with_db_listings
    #subsumed archive case
    rv = client.get("/list/mtrl-th/new")
    assert rv.status_code == 200
    text = rv.text
    assert "Replacement submissions" in text
    assert "arXiv:cond-mat/0703772" in text
