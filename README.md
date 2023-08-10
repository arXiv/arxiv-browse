# arxiv-browse

### Running Browse with the Flask development server

You can run the browse app directly.

```bash
python --version
# 3.10.x
python -m venv ./venv
source ./venv/bin/activate
pip install poetry
poetry install
python main.py
```
Then go to http://127.0.0.1:8080/abs/0906.5132

This will monitor for any changes to the Python code and restart the server.
Unfortunately static files and templates are not monitored, so you'll have to
manually restart to see those changes take effect.

By default, the application will use the directory trees in
`tests/data/abs_files` and `tests/data/cache` and when looking for the document
metadata and PDF files. These paths can be overridden via environment variables
(see `browse/config.py`).

### Test suite

Run the main test suite with the following command:

```bash
pytest
```

### Running Browse in Docker
You can also run the browse app in Docker. The following commands will build
and run browse using defaults for the configuration parameters and will use
the test data from `tests/data`.

Install [Docker](https://docs.docker.com/get-docker/) if you haven't already, then run the following:

```bash
script/start
```

This command will build the docker image and run it.

If all goes well, http://localhost:8000/ will render the home page.

### Configuration Parameters

See `browse/config.py` for configuration parameters and defaults). Any of these
can be overridden with environment variables.

### Serving static files on S3

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
