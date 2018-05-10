# arxiv-browse

### Flask development server

You can run the browse app directly. Using pipenv:

```bash
pipenv install
FLASK_APP=app.py FLASK_DEBUG=1 pipenv run flask run
```


This will monitor for any changes to the Python code and restart the server.
Unfortunately static files and templates are not monitored, so you'll have to
manually restart to see those changes take effect.

If all goes well, http://127.0.0.1:5000/abs/0906.5132 should render the basic
abs page.

### Rebuilding the test database

The default app configuration uses a test SQLite database in
``tests/data/browse.db``; it has been pre-populated with limited test data.

To rebuild the test database, run the following script:

```bash
FLASK_APP=app.py pipenv run python populate_test_database.py --drop_and_create
```
### Test suite

Before running the test suite, install the dev packages:

```bash
pipenv install --dev
```

Run the main test suite with the following command:

```bash
pipenv run nose2 --with-coverage
```

### Static checking
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

### Documentation style
Goal: zero errors/warnings.

```bash
pipenv run pydocstyle --convention=numpy --add-ignore=D401 browse
```

### Linting
Goal: 9/10 or better.

```bash
pipenv run pylint browse
