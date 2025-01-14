# arxiv-browse

## Running Browse with the Flask development server

```bash
python --version
# 3.11.x
python -m venv ./venv
source ./venv/bin/activate
pip install poetry==1.3.2
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
pytest tests
```

## Running with access to the production database

The above method will only give you access to minimal data in the built-in test
dataset. For full (read-only) access to the production database, the following
steps are necessary:

Prerequisites:
you are logged into gcloud and have default application credentials. This
can be achieved by calling `gcloud auth login --update-adc --force` and
logging into your @arxiv.org account.

Next, **all** the following steps have to be done.

Also, in the following we assume that you two port variable set in the environment:
```
MAIN_DB_PORT=3301
LATEXML_DB_PORT=3302
```
(the numbers are not important, but must be different)

### Create a .env file

Create the '.env' file somewhere. Using tests/.env is suggested.

```
DOCUMENT_ABSTRACT_SERVICE=browse.services.documents.db_docs
ABS_PATH_ROOT=gs://arxiv-production-data
DOCUMENT_CACHE_PATH=gs://arxiv-production-data/ps_cache
DOCUMENT_LISTING_PATH=gs://arxiv-production-data/ftp
DISSEMINATION_STORAGE_PREFIX=gs://arxiv-production-data
LATEXML_ENABLED=True
LATEXML_BUCKET="gs://latexml_document_conversions"
LATEXML_BASE_URL=//127.0.0.1:8080
FLASKS3_ACTIVE=1
CLASSIC_DB_URI=" SEE BELOW "
LATEXML_DB_URI=" SEE BELOW "
```

The value of `CLASSIC_DB_URI` one can obtain by
```
MAIN_SECRET=$(gcloud secrets versions access latest --project=arxiv-production  --secret=readonly-arxiv-db-uri)
echo $MAIN_SECRET | sed -e "s#/arXiv.*#127.0.0.1:${MAIN_DB_PORT}/arXiv#"
```

The value of `LATEXML_DB_URI` one can obtain by
```
LATEXML_SECRET=$(gcloud secrets versions access latest --project=arxiv-production  --secret=latexml_db_uri_psycopg2)
echo $LATEXML_SECRET | sed -e "s#/latexmldb.*#127.0.0.1:${LATEXML_DB_PORT}/latexmldb#"
```

If you have a PyCharm,
script: main.py
Enable env files
   Add tests/.env

![docs/development/pycharm-run-setting.png](docs/development/pycharm-run-setting.png)


### Running cloud-sql-proxy

You can obtain the database name `MAIN_DB_NAME` from the same `$SECRET` as in the previous step:
```
MAIN_DB_NAME=$(echo $MAIN_SECRET | sed -e "s#^.*unix_socket=/cloudsql/##")
```

Similar, for the `LATEXML_DB_NAME` one needs to do
```
LATEXML_DB_NAME=$(echo $LATEXML_SECRET | sed -e "s#^.*host=/cloudsql/##")
```


NOTE: `cloud_sql_proxy` and `cloud-sql-proxy` (new) have different options.

```
cloud-sql-proxy --address 0.0.0.0 --port ${MAIN_DB_PORT} ${MAIN_DB_NAME}
cloud-sql-proxy --address 0.0.0.0 --port ${LATEXML_DB_PORT} ${LATEXML_DB_NAME}
```

For the old version
```
cloud_sql_proxy --instances=${MAIN_DB_NAME}=tcp:${MAIN_DB_PORT}
cloud_sql_proxy --instances=${LATEXML_DB_NAME}=tcp:${LATEXML_DB_PORT}
```


If the proxy is working, you can use mysql client to connect to the db.

```bash
mysql -u browse -p --host 127.0.0.1 --port ${MAIN_DB_PORT} arXiv
Enter password: 
...
Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> show tables;
+------------------------------------------+
| Tables_in_arXiv                          |
+------------------------------------------+
| Subscription_UniversalInstitution        |
````

### Running Browse in Docker
You can also run the browse app in Docker. The following commands will build and
run browse using defaults for the configuration parameters and will use the test
data from `tests/data`. Install [Docker](https://docs.docker.com/get-docker/) if
you haven't already, then run the following:

```bash
script/start
```

This command will build the docker image and run it. If all goes well,
http://localhost:8000/ will render the home page.

### Configuration Parameters

See `browse/config.py` for configuration parameters and defaults). Any of these
can be overridden with environment variables.

### Tests and linting for PRs
There is a github action that runs on PRs that merge to develop. PRs for which
these tests fail will be blocked. It is the equivalent of running:

```
# if there are Python syntax errors or undefined names
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

pytest tests
```

### Setting up pytest in PyCharm

![docs/development/pycharm-run-setting.png](docs/development/pycharm-pytest.png)


### Makefile

There is a make file form running the app and other tasks.

```bash
make venv
````
