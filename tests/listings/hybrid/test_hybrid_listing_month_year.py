from datetime import datetime

from browse.services.database.listings import _entries_into_monthly_listing_items
from browse.services.listing import get_listing_service
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

#month listing tests

def test_transform_into_listing():
    items=[(SAMPLE_METADATA1,1),(SAMPLE_METADATA2,0)]
    new, cross=_entries_into_monthly_listing_items(items)

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

    rv = client.get("/list/chao-dyn/1995-10")
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

def test_year_listing_page( client_with_hybrid_listings):
    client = client_with_hybrid_listings

    #two digit year
    rv = client.get("/list/chao-dyn/1995")
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
