"""Special pytest fixture configuration file.

This file automatically provides all fixtures defined in it to all
pytest tests in this directory and sub directories.

See https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files

pytest fixtures are used to initialize object for test functions. The
fixtures run for a function are based on the name of the argument to
the test function.

Scope = 'session' means that the fixture will be run onec and reused
for the whole test run session. The default scope is 'function' which
means that the fixture will be re-run for each test function.

"""
import pytest

from browse.factory import create_web_app

@pytest.fixture(scope='session')
def loaded_db():
    """Loads the testing db"""
    app = create_web_app() 
    with app.app_context():
        from browse.services.database import models
        from . import populate_test_database
        populate_test_database(True, models)
   
    

@pytest.fixture(scope='session')
def app_with_db(loaded_db):
    """App setup with DB backends."""
    from browse.services.listing import db_listing
    import browse.services.documents as documents

    app = create_web_app()
    app.config.update({'DOCUMENT_LISTING_SERVICE': db_listing})
    app.config.update({'DOCUMENT_ABSTRACT_SERVICE': documents.db_docs})
    app.settings.DOCUMENT_ABSTRACT_SERVICE = documents.db_docs
    app.settings.DOCUMENT_LISTING_SERVICE = db_listing
    
    app.testing = True
    app.config['APPLICATION_ROOT'] = ''

    with app.app_context():
        from browse.services.listing import db_listing
        import browse.services.documents as documents
        from flask import g
        g.doc_service = documents.db_docs(app.settings, g)
        g.listing_service = db_listing(app.settings, g)

    return app

    
@pytest.fixture(scope='function')
def app_with_fake(loaded_db):
    """A browser client with fake listings and FS abs documents"""

    # This depends on loaded_db becasue the services.database needs the DB
    # to be loaded eventhough listings and abs are done via fake and FS.
    app = create_web_app()
    import browse.services.listing as listing
    import browse.services.documents as documents

    app.config.update({'DOCUMENT_LISTING_SERVICE': listing.fake})
    app.config.update({'DOCUMENT_ABSTRACT_SERVICE': documents.fs_docs})

    app.settings.DOCUMENT_ABSTRACT_SERVICE = documents.fs_docs
    app.settings.DOCUMENT_LISTING_SERVICE = listing.fake

    app.testing = True
    app.config['APPLICATION_ROOT'] = ''
    
    with app.app_context():
        from flask import g
        g.doc_service = documents.fs_docs(app.settings, g)
        g.listing_service = listing.fake(app.settings, g)

    return app

@pytest.fixture(scope='function')
def dbclient(app_with_db):
    """A browse app client with a test DB populated with fresh data.

    This is function so each test funciton gets an new app_context."""
    with app_with_db.app_context():
        yield app_with_db.test_client() # yield so the tests already have the app_context


@pytest.fixture(scope='function')
def client_with_fake_listings(app_with_fake):
    with app_with_fake.app_context():
        yield app_with_fake.test_client() # yield so the tests already have the app_context

@pytest.fixture()
def unittest_add_db(request, dbclient):
    """Adds dbclient to the calling UnitTest object

    To use this add @pytest.mark.usefixtures("unittest_add_db") to the UnitTest TestCase class."""
    request.cls.dbclient = dbclient


@pytest.fixture()
def unittest_add_fake(request, client_with_fake_listings):
    """Adds client with fake listing data and FS abs data to the calling UnitTest object

    To use this add @pytest.mark.usefixtures("unittest_add_fake") to the UnitTest TestCase class."""
    request.cls.client = client_with_fake_listings
    


#NOT A FIXTURE
def _app_with_db():
    from browse.services.listing import db_listing
    import browse.services.documents as documents

    app = create_web_app()
    app.config.update({'DOCUMENT_LISTING_SERVICE': db_listing})
    app.config.update({'DOCUMENT_ABSTRACT_SERVICE': documents.db_docs})

    app.settings.DOCUMENT_ABSTRACT_SERVICE = documents.db_docs
    app.settings.DOCUMENT_LISTING_SERVICE = db_listing
    app.testing = True
    app.config['APPLICATION_ROOT'] = ''
    return app
