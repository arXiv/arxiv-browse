"""Special pytest fixture configuration file.


This file automatically provides all fixtures defined in it to all
pytest tests in this directory and sub directories.

See https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files

pytest fixtures are used to initialize objects for test functions. The
fixtures run for a function are based on the name of the argument to
the test function.
"""
import os
import pytest
from pathlib import Path
import sys

# This is to allow running pytest in the root directory of the project
cwd = Path('.').absolute()
if not any([path==cwd for path in sys.path]):
    sys.path.append(str(cwd))

@pytest.fixture
def app_local_fs():
    """Pytest fixture to get a dissemination app pointed at `tests/data`"""
    if not os.environ.get('STORAGE_PREFIX', None):
        os.environ['STORAGE_PREFIX'] = './tests/data/'
    os.environ['TRACE']='0'
    from arxiv_dissemination import app
    return app.factory()

@pytest.fixture
def client(app_local_fs):
    return app_local_fs.test_client()


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

