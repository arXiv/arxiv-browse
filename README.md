# arxiv-browse

### Running Browse with the Flask development server

You can run the browse app directly.

```bash
python -m venv ./venv
source ./venv/bin/activate
pip install poetry
poetry install
FLASK_APP=app.py FLASK_DEBUG=1 flask run
```

If all goes well, http://127.0.0.1:5000/abs/0906.5132 should render the basic
abs page.

This will monitor for any changes to the Python code and restart the server.
Unfortunately static files and templates are not monitored, so you'll have to
manually restart to see those changes take effect.

By default, the application will use the directory trees in
`tests/data/abs_files` and `tests/data/cache` and when looking for the
document metadata and cache files, respectively. These paths can be
overridden via environment variables (see `browse/config.py`).

### Test suite

Install the mypy types before running the test suite, 

```bash
mypy --install-types
```

Then you need to build the database:
```bash
source ./venv/bin/activate
FLASK_APP=app.py python populate_test_database.py --drop_and_create
```

Run the main test suite with the following command:

```bash
pytest
```

### Building the test database

A database is needed for many features of browse. Run this and it will create  a test SQLite database in
``tests/data/browse.db``. The default app configuration uses this file.

To rebuild the test database, run the following script:

```bash
source ./venv/bin/activate
FLASK_APP=app.py python populate_test_database.py --drop_and_create
```

### Running Browse in Docker
You can also run the browse app in Docker. The following commands will build
and run browse using defaults for the configuration parameters and will use
the test data from `tests/data`.

```bash
docker build . -t arxiv/browse:some_tag
docker run -it 8000:8000 arxiv/browse:some_tag
```
If all goes well, http://localhost:8000/ will render the home page.

### Configuration Parameters

Configuration parameters (and defaults) are defined in
`browse/config.py`.  Any of these can be overridden with environment
variables when testing the application.

Below are some examples of some application-specific parameters:

Database URI:
* `SQLALCHEMY_DATABASE_URI`

Paths to .abs and source files:
* `DOCUMENT_LATEST_VERSIONS_PATH`
* `DOCUMENT_ORIGNAL_VERSIONS_PATH`

Path to cache directory:
* `DOCUMENT_CACHE_PATH`

arXiv Labs options:
* `LABS_BIBEXPLORER_ENABLED`

### Serving static files on S3

We use [Flask-S3](https://flask-s3.readthedocs.io/en/latest/) to serve static
files via S3. Following the instructions for Flask-S3 should just work.

### Static checking
Goal: zero errors/warnings.

Use `# type: ignore` to disable mypy messages that do not reveal
actual programming errors and are impractical to fix. If ignoring
without verifying, insert a `# TODO: recheck`. If there is an active
`mypy` GitHub issue (i.e. it's a bug/limitation in mypy) relevant to
missed check, link that for later follow-up.

```bash
mypy -p browse
```

Note that we filter out messages about test modules, and messages about a known
limitation of mypy related to ``dataclasses`` support.

### Documentation style
Goal: zero errors/warnings.

```bash
pydocstyle --convention=numpy --add-ignore=D401 browse
```

### Linting
Goal: 9/10 or better.

```bash
pylint browse
```
