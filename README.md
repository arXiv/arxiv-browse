# arxiv-browse

## Running Browse with the Flask development server

You can run the browse app directly.

```bash
make venv
````

or 

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

### Running Browse with .env file

First, you'd need to create the '.env' file somewhere. Using tests/.env is suggested.

    export GOOGLE_APPLICATION_CREDENTIALS=<Your SA credential>
    export BROWSE_SQLALCHEMY_DATABASE_URI="mysql://browse:<BROWSE_PASSWORD>@127.0.0.1:1234/arXiv"
    export DOCUMENT_ABSTRACT_SERVICE=browse.services.documents.db_docs
    export DOCUMENT_LATEST_VERSIONS_PATH=gs://arxiv-production-data/ftp
    export DOCUMENT_ORIGNAL_VERSIONS_PATH=gs://arxiv-production-data/orig
    export DOCUMENT_CACHE_PATH=gs://arxiv-production-data/ps_cache
    export DOCUMENT_LISTING_PATH=gs://arxiv-production-data/ftp
    export DISSEMINATION_STORAGE_PREFIX=gs://arxiv-production-data
    export LATEXML_ENABLED=True
    export LATEXML_BASE_URL=https://browse.arxiv.org/latexml
    export FLASKS3_ACTIVE=1

You need a SA cred to access the db, and the cloud-sql-proxy running.

You can find the browse password here:
https://console.cloud.google.com/security/secret-manager/secret/browse-sqlalchemy-db-uri/versions?project=arxiv-production

If you have a PyCharm,
script: main.py
Enable env files
   Add tests/.env

![docs/development/pycharm-run-setting.png](docs/development/pycharm-run-setting.png)

### SA Credentials

Your SA needs followings:

* Cloud SQL Client
* Secret Manager Secret Accessor
* Storage Object Viewer

Save the private key somewhere on your local machine. Optionally save it in 1password.

### Running cloud-sql-proxy

Once you have the google SA private key, you can run the cloud-sql-proxy.

```bash
main proxy
``` 

NOTE: cloud_sql_proxy and cloud-sql-proxy (new) have different options.
In this, only describes the new as you probably don't have the old one.

	cloud-sql-proxy --address 0.0.0.0 --port 1234 arxiv-production:us-east4:arxiv-production-rep4

If the proxy is working, you can use mysql client to connect to the db.

```bash
mysql -u browse -p --host 127.0.0.1 --port 1234 arXiv
Enter password: 
...
Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> show tables;
+------------------------------------------+
| Tables_in_arXiv                          |
+------------------------------------------+
| Subscription_UniversalInstitution        |
````

### Test suite

Run the main test suite with the following command:

```bash
pytest tests
```

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

### Tests and linting for PRs
There is a github action that runs on PRs that merge to develop. PRs for which
these tests fail will be blocked. It is the equivalent of running:

```
# if there are Python syntax errors or undefined names
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

pytest tests
```

