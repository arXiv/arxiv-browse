def test_should_be_db_listings(dbclient):
    from browse.services.listing import db_listing, get_listing_service
    assert dbclient and dbclient.application.config['DOCUMENT_LISTING_SERVICE'] == db_listing
    assert 'db_listing' in str(get_listing_service())

def test_basic_db_lists(dbclient):
    rv = dbclient.get('/list/hep-ph/2011-02')
    assert rv.status_code == 200

