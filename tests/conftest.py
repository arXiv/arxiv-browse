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
    import sys
    print(f"sys.path is {sys.path}")
    os.environ['TRACE']='0'
    os.environ['STORAGE_PREFIX'] = './tests/data'
    from arxiv_dissemination import app
    return app

@pytest.fixture
def client(app_local_fs):
    return app_local_fs.test_client()
