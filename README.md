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
