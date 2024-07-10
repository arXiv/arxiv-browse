# Sync published submissons + PDFs from Cornell to a GS bucket

This is a script to sync the published submissions and PDFs from a publish cycle to a GS Bucket.

# History

## Pre 2024-07

Originally, when the daily.sh runs and generates the published log file, the cron job picks it up,
make the list of files to upload to GCP, ask the web node to generate PDF, and uploads them all.

Since the webnode's pdf generation is limited to certain number of processes, asking to generate
PDF as a batch job was somewhat unreliable. Because of this, the multiple cron jobs are needed
to complete the PDF generation and upload. 

When HTML submission put in the GCP queue, it became possible to not only manage the published 
articles more evenly spread out, it is now capable of retrying the PDF with sensible back off.

The two clients of the queue is created, one to generate PDF so that the cron jobs don't have to
generate PDFs for most of times, and the syncing of tarballs to GCP is spread out during the
daily.sh run to make the published list. 

Having 2 services + cron job were working okay but one omission was that, every week another 
rsync based cron job was running but it was suspected to remove files when the CIT's file server
mysteriously corrupts or not list a file. 

6 daily cron jobs, one weekly sync, 2 services - one to make PDF, other to sync blobs - was too
complex and esp. the weekly sync was not only dangerous but unexplainable due to the file server's
flakyness.

## Post 2024-07

submissions-to-gcp unifies all this and "trashes" the older version of published submissions 
if it exits on GCP bucket.

## Contributors

* BrianC (bdc34): The original log based sync-to-gcp
* ntai (nt385): The queue based sync-to-gcp, borrowing the functionality from the original
* mark (men73): kicked off the pub/sub based publishing  

# Synopsys of sync based on the published log

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

Although this became obsolete by the use of queue, it is still useful if you have to manually sync
the published submissions to GCP.

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

# Obsolete cron-based Deployment

The script is designed to run as a cron job.

## cronjob 

Old:

    15 21 * * 0-4 /opt_arxiv/e-prints/dissemination/sync_prod_to_gcp/sync_published.sh

New:

    15 21 * * 0-4 /users/e-prints/arxiv-browse/scrip/sync_prod_to_gcp/sync_published.sh

# Queue-based Deployment

The service runs on the sync node using systemd. See `resouce/systemd/submissons-to-gcp.service`

## submissons_to_gcp.py

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


# Submissions to GCP service

## General

A systemd service "submssions-to-gcp" subscribes to GCP pub/sub queue for published and 
copy the submission tarball and abstract file to GCP bucket.


## Service setup

There is a (template) unit file. The service process runs one process per web node.

    sudo systemctl enable submissions-to-gcp.service
    sudo systemctl start  submissions-to-gcp.service

This instantiate the service for sync-node.arxiv.org. 

## GCP Pub/sub

The topic is already set up as [`submission-published`](https://console.cloud.google.com/cloudpubsub/topic/detail/submission-published?project=arxiv-production)
This is used by HTML generation. 2nd subscriber is added for [this](https://console.cloud.google.com/cloudpubsub/subscription/detail/sync-submission-from-cit-to-gcp?project=arxiv-production).

