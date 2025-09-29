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
import importlib
import pkgutil
import random
import shutil
import sys
import tempfile

import pytest
from pathlib import Path

from arxiv.auth.legacy import util
from sqlalchemy import create_engine

from browse.factory import create_web_app
from arxiv.config import Settings

from tests import path_of_for_test

import browse.services.documents as documents
import browse.services.listing as listing


ARXIV_BASE_SETTINGS = Settings()

TESTING_CONFIG = {
    'DOCUMENT_LISTING_SERVICE': listing.db_listing,
    'DOCUMENT_ABSTRACT_SERVICE': documents.db_docs,
    "APPLICATION_ROOT": "",
    "TESTING": True,
    "LATEXML_ENABLED": 1
    }

def test_config():
    return TESTING_CONFIG.copy()


@pytest.fixture(scope='session')
def test_dir():
    db_path = tempfile.mkdtemp()
    yield db_path
    shutil.rmtree(db_path)


@pytest.fixture(scope='session')
def classic_db_engine(test_dir):
    uri = f'sqlite:///{test_dir}/test_classic.db'
    engine = create_engine(uri)
    util.create_all(engine)
    yield engine


@pytest.fixture(scope='session')
def latexml_db_engine(test_dir):
    uri = f'sqlite:///{test_dir}/test_latexml.db'
    engine = create_engine(uri)
    util.create_all(engine)
    yield engine


@pytest.fixture(scope='session')
def loaded_db(test_dir):
    """Loads the testing db"""

    app = create_web_app(**test_config())
    with app.app_context():
        from arxiv import db
        uri = f'sqlite:///{test_dir}/test_latexml.db'
        db._latexml_engine = create_engine(uri)
        util.create_all(db._latexml_engine)
        uri = f'sqlite:///{test_dir}/test_classic.db'
        db._classic_engine = create_engine(uri)
        util.create_all(db._classic_engine)

        from arxiv.db import models
        models.configure_db_engine(db._classic_engine, db._latexml_engine)
        from . import populate_test_database
        populate_test_database(True, db, db._classic_engine, db._latexml_engine) # type: ignore
        db._classic_engine = None
        db._latexml_engine = None
        return Path(test_dir) / "test_classic.db", Path(test_dir) / "test_latexml.db"

@pytest.fixture(scope='function')
def loaded_db_copy(test_dir, loaded_db):
    classic_db, latex_db = loaded_db
    prefix = random.randint(1,100)
    fn_classic_db_file = Path(test_dir)/ f"{prefix}_function_scoped_classic.db"
    shutil.copyfile(classic_db, fn_classic_db_file)
    fn_latex_db_file = Path(test_dir)/ f"{prefix}_function_scoped_latex.db"
    shutil.copyfile(latex_db, fn_latex_db_file)
    yield(f"sqlite:///{fn_classic_db_file}", f"sqlite:///{fn_latex_db_file}")
    fn_latex_db_file.unlink()
    fn_classic_db_file.unlink()


def get_all_modules_in_package(package_name):
    """
    Lists all modules (including subpackages) within a specified package.
    """
    try:
        package = __import__(package_name, fromlist=["dummy"])
        package_path = package.__path__
    except ImportError:
        print(f"Error: Package '{package_name}' not found.")
        return []

    modules = []
    for importer, modname, ispkg in pkgutil.walk_packages(path=package_path, prefix=package.__name__ + '.'):
        modules.append(modname)
    return modules


def _modules(package_name):
    package = __import__(package_name, fromlist=["dummy"])
    package_path = package.__path__
    modules = []
    for importer, modname, ispkg in pkgutil.walk_packages(path=package_path, prefix=package.__name__ + '.'):
        modules.append(modname)

    return modules



@pytest.fixture
def reset_packages():
    from browse.services import global_object_store
    global_object_store._stores = {}

    from browse.services import dissemination
    dissemination._article_store = None
    # for module in _modules("arxiv") + _modules("browse"):
    #     try:
    #         mm = __import__(module, fromlist=["dummy"])
    #         importlib.reload(mm)
    #     except Exception as e:
    #         print(f"Failed to reload {module}: {e}")



@pytest.fixture
def app_with_db(loaded_db_copy, reset_packages):
    """App setup with DB backends and listing service."""
    conf = test_config()
    conf.update({"CLASSIC_DB_URI": loaded_db_copy[0]})
    conf.update({"LATEXML_DB_URI": loaded_db_copy[1]})
    conf.update({'DOCUMENT_LISTING_SERVICE': listing.db_listing})
    conf.update({'DOCUMENT_ABSTRACT_SERVICE': documents.db_docs})
    app = create_web_app(**conf)
    with app.app_context():
        from flask import g
        g.doc_service = documents.db_docs(app.config, g)
        g.listing_service = listing.db_listing(app.config, g)

    return app

@pytest.fixture
def app_with_fake(loaded_db_copy, reset_packages):
    """A browser client with fake listings and FS abs documents"""

    # This depends on loaded_db becasue the services.database needs the DB
    # to be loaded eventhough listings and abs are done via fake and FS.

    import browse.services.documents as documents
    import browse.services.listing as listing
    conf = test_config()
    conf.update({"CLASSIC_DB_URI": loaded_db_copy[0]})
    conf.update({"LATEXML_DB_URI": loaded_db_copy[1]})
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

@pytest.fixture
def app_with_test_fs(loaded_db_copy, reset_packages):
    """A browser client with FS abs documents and listings"""

    # This depends on loaded_db becasue the services.database needs the DB
    # to be loaded eventhough listings and abs are done via FS.

    import browse.services.listing as listing
    conf = test_config()
    conf.update({"CLASSIC_DB_URI": loaded_db_copy[0]})
    conf.update({"LATEXML_DB_URI": loaded_db_copy[1]})
    conf["DISSEMINATION_STORAGE_PREFIX"] = './tests/data/abs_files/'
    conf["DOCUMENT_ABSTRACT_SERVICE"] = documents.fs_docs
    conf["DOCUMENT_LISTING_SERVICE"] = listing.fs_listing
    conf["DOCUMENT_LISTING_PATH"] = "tests/data/abs_files/ftp"
    conf["ABS_PATH_ROOT"] = "tests/data/abs_files/"
    app = create_web_app(**conf)
    with app.app_context():
        from flask import g
        g.doc_service = documents.fs_docs(app.config, g)
        g.listing_service = listing.fs_listing(app.config, g)
        yield app

@pytest.fixture(scope='function')
def dbclient(app_with_db):
    """A browse app client with a test DB populated with fresh data.

    This is function so each test function gets a new app_context."""
    with app_with_db.app_context():
        yield app_with_db.test_client()  # yield so the tests already have the app_context


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
