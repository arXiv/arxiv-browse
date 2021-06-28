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
def dbclient():
    """A browse app client with a test DB populated with fresh data."""
    from browse.services.listing import db_listing
    import browse.services.documents as documents

    app = create_web_app()
    with app.app_context() as ctx:
        app.config.update({'DOCUMENT_LISTING_SERVICE': db_listing})
        app.config.update({'DOCUMENT_ABSTRACT_SERVICE': documents.db_docs})
        app.config.update({'BROWSE_SQLALCHEMY_DATABASE_URI': SQLALCHEMY_DATABASE_URI})

        app.settings.DOCUMENT_ABSTRACT_SERVICE = documents.db_docs
        app.settings.DOCUMENT_LISTING_SERVICE = db_listing
        app.testing = True
        app.config['APPLICATION_ROOT'] = ''

        from flask import g
        g.doc_service = documents.db_docs(app.settings, g)
        g.listing_service = db_listing(app.settings, g)

        #from browse.services.database import models
        #from . import populate_test_database
        #populate_test_database(True, models)

        yield app.test_client()


@pytest.fixture(scope='session')
def client_with_fake_listings():
    app = create_web_app()
    from browse.services.listing import fake_listings
    app.config.DOCUMENT_LISTING_SERVICE = fake_listings    
    app.testing = True
    app.config['APPLICATION_ROOT'] = ''
    return app.test_client()


