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

DB_FILE= "./pytest.db"
SQLALCHEMY_DATABASE_URI=f"sqlite:///{DB_FILE}"
DELETE_DB_FILE_ON_EXIT = True

from browse.factory import create_web_app


@pytest.fixture(scope='session')
def app_loaded_db():
    """A test DB populated with fresh data."""
    app = _app_with_db(SQLALCHEMY_DATABASE_URI)
    with app.app_context():
        from browse.services.listing import db_listing
        import browse.services.documents as documents
        from flask import g
        g.doc_service = documents.db_docs(app.settings, g)
        g.listing_service = db_listing(app.settings, g)

    return app


@pytest.fixture(scope='function')
def dbclient(app_loaded_db):
    """A browse app client with a test DB populated with fresh data.

    This is function so each test funciton gets an new app_context."""
    with app_loaded_db.app_context():
        yield app_loaded_db.test_client() # yield so the tests already have the app_context


@pytest.fixture()
def unittest_add_db(request, app_loaded_db):
    """Adds dbclient to the calling UnitTest object"""
    with app_loaded_db.app_context():
        request.cls.dbclient = dbclient
        yield

    
@pytest.fixture(scope='function')
def client_with_fake_listings():
    """A browser client with fake listings and FS abs documents"""
    app = create_web_app()
    from browse.services.listing import fake_listings
    app.config.DOCUMENT_LISTING_SERVICE = fake_listings
    app.testing = True
    app.config['APPLICATION_ROOT'] = ''
    with app.app_context():
        import browse.services.listing as listing
        import browse.services.documents as documents
        from flask import g
        g.doc_service = documents.fs_docs(app.settings, g)
        g.listing_service = listing.fake(app.settings, g)
        yield app.test_client() #yield so the tests already have the app_context


#NOT A FIXTURE
def _app_with_db(db_uri):
    from browse.services.listing import db_listing
    import browse.services.documents as documents

    app = create_web_app()
    app.config.update({'SQLALCHEMY_DATABASE_URI': SQLALCHEMY_DATABASE_URI})
    app.config.update({'DOCUMENT_LISTING_SERVICE': db_listing})
    app.config.update({'DOCUMENT_ABSTRACT_SERVICE': documents.db_docs})

    app.settings.DOCUMENT_ABSTRACT_SERVICE = documents.db_docs
    app.settings.DOCUMENT_LISTING_SERVICE = db_listing
    app.testing = True
    app.config['APPLICATION_ROOT'] = ''
    return app
