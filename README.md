# arxiv-browse

## Running Browse with the Flask development server

You can run the browse app directly. Using pipenv:

```bash
python --version
3.6.15
python -m venv venv
venv/bin/activate
pip install pipenv==2022.4.8
pipenv install
pipenv run python main.py
```

This will monitor for any changes to the Python code and restart the server.
Unfortunately static files and templates are not monitored, so you'll have to
manually restart to see those changes take effect.

If all goes well, http://127.0.0.1:5000/abs/0906.5132 should render the basic
abs page.

By default, the application will use the directory trees in
`tests/data/abs_files` and `tests/data/cache` and when looking for the
document metadata and cache files, respectively. These paths can be
overridden via environment variables (see `browse/config.py`).

## Pipfile Edits for Development
```
arxiv-base = { editable = true, path = "../arxiv-base" }
arxiv-base = {editable = true, git = "https://github.com/arXiv/arxiv-base.git", ref = "ARXIVNG-3824-bootstrap"}
```

## Rebuilding the test database

The default app configuration uses a test SQLite database in
``tests/data/browse.db``; it has been pre-populated with a small set of test
data.

To rebuild the test database, run the following script:

```bash
FLASK_APP=app.py pipenv run python populate_test_database.py --drop_and_create
```

## Running Browse in Docker
You can also run the browse app in Docker. The following commands will build
and run browse using defaults for the configuration parameters and will use
the test data from `tests/data`.

Install [Docker](https://docs.docker.com/get-docker/) if you haven't already, then run the following:

```bash
script/start
```

This command will build the docker image and run it.

If all goes well, http://localhost:8000/ will render the home page.

## Configuration Parameters

Configuration parameters (and defaults) are defined in `browse/config.py`.
Any of these can be overridden on the command line when testing the application.

Below are some examples of some application-specific parameters:

Database URI:
* `SQLALCHEMY_DATABASE_URI``

Paths to .abs and source files:
* `DOCUMENT_LATEST_VERSIONS_PATH`
* `DOCUMENT_ORIGNAL_VERSIONS_PATH`

Path to cache directory:
* `DOCUMENT_CACHE_PATH`

arXiv Labs options:
* `LABS_BIBEXPLORER_ENABLED`

## Serving static files on S3

We use [Flask-S3](https://flask-s3.readthedocs.io/en/latest/) to serve static
files via S3.

After looking up the AWS keys and region and bucket:
```bash
cd arxiv-browse
git pull
AWS_ACCESS_KEY_ID=x AWS_SECRET_ACCESS_KEY=x \
 AWS_REGION=us-east-1 FLASKS3_BUCKET_NAME=arxiv-web-static1 \
 pipenv run python upload_static_assets.py
```

In AWS -> CloudFront, select the static.arxiv.org distribution, -> Invalidations -> Create invalidation,
and enter a list of url file paths, eg: /static/browse/0.3.4/css/arXiv.css.

It may be help to use a web browser's inspect->network to find the active release version.


## Test suite

Before running the test suite, install the dev packages:

```bash
pipenv install --dev
```

Run the main test suite with the following command:

```bash
pipenv run nose2 --with-coverage
```

## Static checking
Goal: zero errors/warnings.

Use `# type: ignore` to disable mypy messages that do not reveal actual
programming errors, and that are impractical to fix. If ignoring without
verifying, insert a `# TODO: recheck`.

If there is an active `mypy` GitHub issue (i.e. it's a bug/limitation in mypy)
relevant to missed check, link that for later follow-up.

```bash
pipenv run mypy -p browse | grep -v "test.*" | grep -v "defined here"
```

Note that we filter out messages about test modules, and messages about a known
limitation of mypy related to ``dataclasses`` support.

## Documentation style
Goal: zero errors/warnings.

```bash
pipenv run pydocstyle --convention=numpy --add-ignore=D401 browse
```

## Linting
Goal: 9/10 or better.

```bash
pipenv run pylint browse
```
