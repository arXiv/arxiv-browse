# Sync publshed PDFs from Cornell to a GS bucket

This is a script to sync the PDFs from a publish cycle to a GS Bucket.

# Synopsys

    cd sync_prod_to_gcp
    python --version
    # Python 3.8.0
    echo $GOOGLE_APPLICATION_CREDENTIALS
    # /users/e-prints/arxiv-production-1234.json or your own credentials
    # make will set up `sync.venv` the virtual env for sync to run.
    make
    #
    . sync.venv/bin/activate
    python sync_published_to_gcp.py /data/new/logs/publish_221101.log

# Development/Testing

## test_json_log

This is a quick test to make sure the JSON logging is working by running the dry run.

## test_sync

This is a test that uploads the test files and make sure the machinery is correct, for both the uploading and
the error reporting.
To force the sync to upload the file that exists in the bucket, it sets "RELOADS" so the load ignores that 
the item exists in the bucket.

### Ingredients

* GCP Bucket
* GCP service account
* A known storage object that is locked

## GCP

In arxiv-development, a bucket is created for the test. "arxiv-sync-test-01" is the name.

To access the bucket, a service account "sync_test_admen" is created. The account has the storage read/write 
permission.

    # Create the test admin role that has the storage I/O.
    gcloud beta iam roles create sync_test_admin --project=arxiv-development --file=test/gcp-sync-test-role.json

    # Create the test ademin account 
    gcloud iam service-accounts create sync-test-admin --project=arxiv-development --display-name="Sync Test Admin" --display-name="Sync Test Admin"

    # Give it the role of storage I/O
    gcloud projects add-iam-policy-binding arxiv-development --member="serviceAccount:sync-test-admin@arxiv-development.iam.gserviceaccount.com" --role="projects/arxiv-development/roles/sync_test_admin"

    # Allow the service account to access the storaeg bucket.
    gsutil iam ch serviceAccount:sync-test-admin@arxiv-development.iam.gserviceaccount.com:projects/arxiv-development/roles/sync_test_admin gs://arxiv-sync-test-01

    # DO NOT CREATE A NEW KEY UNLESS YOU NEET TO ROTATE THE KEY
    # gcloud iam service-accounts keys create sync-test.json --iam-account sync-test-admin@arxiv-development.iam.gserviceaccount.com
    # Created key is stored in 1password.
    # You can get the existing key in 1password with:

    op read "op:///hs3xn7ldhg3pgrql5j524rgpee/w2wtsf5v7kahbngr64m43mciou/qrdfsd5gbnatjpv7zof6vwca4q"

See `Makefile`

# Deployment

The script is designed to run as a cron job. 

## cronjob 

Old:

    15 21 * * 0-4 /opt_arxiv/e-prints/dissemination/sync_prod_to_gcp/sync_published.sh

New:

    15 21 * * 0-4 /users/e-prints/arxiv-browse/scrip/sync_prod_to_gcp/sync_published.sh

## Logging

There are two logging, one plain text, and the second is NDJSON that is designed for GCP. The JSON logging goes into
`/opt_arxiv/e-prints/logs/sync` and Stanza sends it out to GCP. See JSON logging.

### Stanza plug-in for sync

The plugin must be deployed on "arxiv-sync" host.

`arxiv-browse/scripts/sync_prod_to_gcp/stanza/plugins/arxiv_sync2gcp_log.yaml` -> `/opt/observiq/stanza/plugins/arxiv_sync2gcp_log.yaml`

On arxiv-sync, `/opt/observeiq/stanza/config.yaml` must include the following:

      - type: arxiv_sync2gcp_log
        log_path: "/opt_arxiv/e-prints/logs/sync/*"

### JSON logging

Note that, the JSON logger does log rotation. You do not need to set up the log cleaning.
OTOH, because of this, it is rather important for Stanza to be running.
Currently, the max file size is set to 4MiB, with 10 log files. It should be fine for a few days.




