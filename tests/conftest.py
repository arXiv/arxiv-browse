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
from pathlib import Path
from browse.factory import create_web_app
from arxiv.config import Settings

from tests import path_of_for_test

import browse.services.documents as documents
import browse.services.listing as listing

DEFAULT_DB = "sqlite:///tests/data/browse.db"
TESTING_LATEXML_DB = 'sqlite:///tests/data/latexmldb.db'


ARXIV_BASE_SETTINGS = Settings(
    
)

TESTING_CONFIG = {
    "CLASSIC_DB_URI": DEFAULT_DB,
    "LATEXML_DB_URI": TESTING_LATEXML_DB,
    'DOCUMENT_LISTING_SERVICE': listing.db_listing,
    'DOCUMENT_ABSTRACT_SERVICE': documents.db_docs,
    "APPLICATION_ROOT": "",
    "TESTING": True,
    "LATEXML_ENABLED": 1
    }

def test_config():
    return TESTING_CONFIG.copy()

@pytest.fixture(scope='session')
def loaded_db():
    """Loads the testing db"""
    app = create_web_app(**test_config())
    with app.app_context():
        from arxiv import db
        from . import populate_test_database
        populate_test_database(True, db)


@pytest.fixture(scope='session')
def app_with_db(loaded_db):
    """App setup with DB backends and listing service."""

    conf = test_config()
    app = create_web_app(**conf)

    with app.app_context():
        from flask import g
        g.doc_service = documents.db_docs(app.config, g)
        g.listing_service = listing.db_listing(app.config, g)

    return app

@pytest.fixture(scope='function')
def app_with_fake(loaded_db):
    """A browser client with fake listings and FS abs documents"""

    # This depends on loaded_db becasue the services.database needs the DB
    # to be loaded eventhough listings and abs are done via fake and FS.

    import browse.services.documents as documents
    import browse.services.listing as listing

    conf = test_config()
    conf.update({'DOCUMENT_LISTING_SERVICE': listing.fake})
    conf.update({'DOCUMENT_ABSTRACT_SERVICE': documents.fs_docs})

    app = create_web_app(**conf)
    with app.app_context():
        from flask import g
        g.doc_service = documents.fs_docs(app.config, g)
        g.listing_service = listing.fs_listing(app.config, g)
        yield app


@pytest.fixture
def storage_prefix():
    return './tests/data/abs_files/'


@pytest.fixture(scope='function')
def app_with_test_fs(loaded_db):
    """A browser client with FS abs documents and listings"""

    # This depends on loaded_db becasue the services.database needs the DB
    # to be loaded eventhough listings and abs are done via FS.

    import browse.services.listing as listing

    conf = test_config()
    conf["DISSEMINATION_STORAGE_PREFIX"] = './tests/data/abs_files/'
    conf["DOCUMENT_ABSTRACT_SERVICE"] = documents.fs_docs
    conf["DOCUMENT_LISTING_SERVICE"] = listing.fs_listing
    conf["DOCUMENT_LISTING_PATH"] = "tests/data/abs_files/ftp"
    conf["DOCUMENT_LATEST_VERSIONS_PATH"] = "tests/data/abs_files/ftp"
    conf["DOCUMENT_ORIGNAL_VERSIONS_PATH"] = "tests/data/abs_files/orig"

    app = create_web_app(**conf)

    with app.app_context():
        from flask import g
        g.doc_service = documents.fs_docs(app.config, g)
        g.listing_service = listing.fs_listing(app.config, g)
        yield app

@pytest.fixture(scope='function')
def dbclient(app_with_db):
    print ("DB CLIENT FIXTURE IS GOOD")

    """A browse app client with a test DB populated with fresh data.

    This is function so each test funciton gets an new app_context."""
    with app_with_db.app_context():
        yield app_with_db.test_client() # yield so the tests already have the app_context


@pytest.fixture(scope='function')
def client_with_fake_listings(app_with_fake):
    with app_with_fake.app_context():
        yield app_with_fake.test_client() # yield so the tests already have the app_context

@pytest.fixture(scope='function')
def client_with_db_listings(app_with_db):
    with app_with_db.app_context():
        yield app_with_db.test_client() # yield so the tests already have the app_context

@pytest.fixture(scope='function')
def client_with_test_fs(app_with_test_fs):
    with app_with_test_fs.app_context():
        yield app_with_test_fs.test_client() # yield so the tests already have the app_context


@pytest.fixture()
def unittest_add_fake_app(request, app_with_fake):
    """Adds fake_app to the calling UnitTest object

    To use this add @pytest.mark.usefixtures("unittest_add_fake_app") to the UnitTest TestCase class."""
    request.cls.app = app_with_fake


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


@pytest.fixture()
def abs_path() -> Path:
    """`Path` to the test abs files."""
    return Path(path_of_for_test('data/abs_files'))


#NOT A FIXTURE
def _app_with_db():
    import browse.services.documents as documents


    conf = test_conf()
    conf["DOCUMENT_ABSTRACT_SERVICE"] = documents.db_docs
    conf["DOCUMENT_LISTING_SERVICE"] = db_listing

    app = create_web_app(**conf)

    return app



# #################### Integration test marker ####################
"""
Setup to mark integration tests.

https://docs.pytest.org/en/latest/example/simple.html
Mark integration tests like this:

@pytest.mark.integration
def test_something():
  ...
"""

def pytest_addoption(parser):
    parser.addoption(
        "--runintegration", action="store_true", default=False,
        help="run arxiv dissemination integration tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark tests as integration tests")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runintegration"):
        # --runintegration given in cli: do not skip integration tests
        return
    skip_integration = pytest.mark.skip(reason="need --runintegration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
