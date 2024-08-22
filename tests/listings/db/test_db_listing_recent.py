from datetime import date
from typing import List

from browse.services.listing import get_listing_service, ListingItem

#recent listing tests
def validate_recent_listing(listing: List[ListingItem]):
    '''makes sure no duplicat entries are returned and only new and cross listings'''
    all_ids=set()
    for item in listing:
        assert item.id not in all_ids
        all_ids.add(item.id)
        assert item.listingType=="new" or item.listingType=="cross"

def test_recent_basic(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_pastweek_articles("math.MP", 0, 15)
    validate_recent_listing(listing.listings)
    assert listing.count==2
    assert date(2011, 2, 3) in [entry[0] for entry in listing.pubdates] 
    assert date(2011, 2, 1) in [entry[0] for entry in listing.pubdates]
    assert any(item.id == "0906.3421" and item.listingType == "cross" for item in listing.listings)
    assert any(item.id == "0704.0248" and item.listingType == "cross" for item in listing.listings)

def test_no_abs_in_recent(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_pastweek_articles("math.PR", 0, 100)
    validate_recent_listing(listing.listings)
    assert all(item.id !="0712.3217" for item in listing.listings)

def test_no_rep_in_recent(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_pastweek_articles("math.RT", 0, 100)
    validate_recent_listing(listing.listings)
    assert all(item.id !="arXiv:math/0510544" for item in listing.listings)

def test_recent_find_alias(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_pastweek_articles("eess.SY", 0, 15)
    validate_recent_listing(listing.listings)
    assert any(item.id =="1008.3222" and item.listingType=="new" for item in listing.listings)
     
def test_recent_identify_new(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_pastweek_articles("math.CO", 0, 15)
    validate_recent_listing(listing.listings)
    assert any(item.id =="0906.3421" and item.listingType=="new" for item in listing.listings)
   
def test_recent_identify_new_cross(app_with_db):
    """new listings that arent primary in the category requessted"""
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_pastweek_articles("cond-mat.stat-mech", 0, 15)
    validate_recent_listing(listing.listings)
    assert any(item.id =="0906.3421" and item.listingType=="cross" for item in listing.listings)

def test_recent_identify_cross(app_with_db):
    """updates that are specifically cross updates"""
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_pastweek_articles("math.NT", 0, 15)
    validate_recent_listing(listing.listings)
    assert any(item.id =="0906.2112" and item.listingType=="cross" for item in listing.listings)
    
def test_recent_listing_counts(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_pastweek_articles("math", 0, 100)
    validate_recent_listing(listing.listings)
    expected_counts=[(date(2011,2,3),2), (date(2011,2,2),1), (date(2011,2,1),1), (date(2011,1,31),0), (date(2011,1,28),1)]
    assert listing.count==5 and len(listing.listings) == listing.count
    assert listing.pubdates == expected_counts

def test_recent_listing_order(app_with_db):
    #new then cross
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing=ls.list_pastweek_articles("math", 0, 100)
    validate_recent_listing(listing.listings)
    found=False
    for item in listing.listings:
        if item.id=="0906.3421":
            found=True
        if not found:
            assert item.listingType != "cross"

def test_archive_listing(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing1=ls.list_pastweek_articles("math", 0, 30)
        listing2=ls.list_pastweek_articles("eess", 0, 15)

    #finds different math categories
    validate_recent_listing(listing1.listings)
    assert any(item.id =="0906.4150" and item.listingType == "new" for item in listing1.listings)
    assert any(item.id =="0704.0248" and item.listingType == "cross" for item in listing1.listings)

    #finds alias category in alternate archive
    validate_recent_listing(listing2.listings)
    assert any(item.id =="1008.3222" and item.listingType == "new" for item in listing2.listings)

def test_recent_listing_page( client_with_db_listings):
    client = client_with_db_listings
    rv = client.get("/list/math.MP/recent")
    assert rv.status_code == 200
    text = rv.text
    assert "Thu, 3 Feb 2011 (showing 1 of 1 entries )" in text
    assert "arXiv:0906.3421" in text
    assert "(cross-list from math.CO)" in text
    assert "Tue, 1 Feb 2011 (showing 1 of 1 entries )" in text
    assert "Optics (physics.optics)" in text
    assert "; Mathematical Physics (math-ph)" in text

def test_recent_listing_page_alternate_names( client_with_db_listings):
    client = client_with_db_listings
    #subsumed archive case
    rv = client.get("/list/alg-geom/recent")
    assert rv.status_code == 200
    text = rv.text
    assert "Algebraic Geometry (math.AG)" in text
    assert "0906.2112" in text
    assert "Wed, 2 Feb 2011" in text
   
def test_recent_pagination(app_with_db):
    app = app_with_db
    with app.app_context():
        ls=get_listing_service()
        listing1=ls.list_pastweek_articles("math", 0, 1)
        listing2=ls.list_pastweek_articles("math", 1, 14)
    validate_recent_listing(listing1.listings)
    validate_recent_listing(listing2.listings)
    assert listing1.count==listing2.count
    assert len(listing1.listings)==1
    assert len(listing2.listings)>0
    first_id=listing1.listings[0].id
    assert all(item.id !=first_id for item in listing2.listings)
    
def test_recent_listing_page_pagination( client_with_db_listings):
    client = client_with_db_listings
    rv = client.get("/list/math/recent?show=1")
    assert rv.status_code == 200
    text = rv.text
    assert "Thu, 3 Feb 2011 (showing first 1 of 2 entries )" in text
    assert "Wed, 2 Feb 2011 (showing" not in text
    assert "0704.0046" not in text

    rv = client.get("/list/math/recent?skip=1")
    assert rv.status_code == 200
    text = rv.text
    assert "Thu, 3 Feb 2011 (continued, showing last 1 of 2 entries )" in text
    assert "0704.0046" in text
    assert "Tue, 1 Feb 2011 (showing 1 of 1 entries )" in text

def test_recent_page_links( client_with_db_listings):
    client = client_with_db_listings
    rv = client.get("/list/math/recent?show=2")
    assert rv.status_code == 200
    text = rv.text
    assert '<a href="/list/math/recent?skip=4&amp;show=2">\n          Fri, 28 Jan 2011\n        </a>' in text
    assert '<a href="/list/math/recent?skip=3&amp;show=2">\n          Tue, 1 Feb 2011\n        </a>' in text
    assert '<a href="/list/math/recent?skip=2&amp;show=2">\n          Wed, 2 Feb 2011\n        </a>' in text
    assert '<a href="/list/math/recent?skip=0&amp;show=2">\n          Thu, 3 Feb 2011\n        </a>' in text

