# Sync published submissons + PDFs from Cornell to a GS bucket

This is a script to sync the published submissions and PDFs from a publish cycle to a GS Bucket.

# History

## Pre 2024-08

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

## Post 2024-08

submissions-to-gcp unifies all this and "trashes" the older version of published submissions 
if it exits on GCP bucket.

See [submissions-to-gcp-service](#submissions-to-gcp-service)

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
The pytest tests uses the dev bucket heavily. 

To access the bucket, a service account "sync_test_admin" is created. The account has the storage read/write 
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

# Obsolete: cron-based Deployment

The script is designed to run as a cron job. With the use of pub/sub, the unit of work management
is done by the queue. Therefore, there is no reason to run the cron jobs for multiple retry just
to finish the job.

## cronjob (obsolete) 

Old:

    15 21 * * 0-4 /opt_arxiv/e-prints/dissemination/sync_prod_to_gcp/sync_published.sh

New:

    15 21 * * 0-4 /users/e-prints/arxiv-browse/scrip/sync_prod_to_gcp/sync_published.sh

# Queue-based Deployment - "submissions to gcp service"

The service runs on the sync node using systemd. See `resouce/systemd/submissons-to-gcp.service`

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

This is the unified "sync-to-gcp".

## General

A systemd service "submssions-to-gcp" subscribes to GCP pub/sub queue for published and 
copy the submission tarball and abstract file to GCP bucket.

This unifies the existing two services, one is to sync, the other is to ask webnode to generate
PDF and HTML.

## Service setup

There is a (template) unit file. The service process runs one process per web node.

    sudo systemctl enable submissions-to-gcp.service
    sudo systemctl start  submissions-to-gcp.service

This instantiate the service for sync-node.arxiv.org. 

## GCP Pub/sub

The topic is already set up as [`submission-published`](https://console.cloud.google.com/cloudpubsub/topic/detail/submission-published?project=arxiv-production)
This is used by HTML generation. 2nd subscriber is added for [this](https://console.cloud.google.com/cloudpubsub/subscription/detail/sync-submission-from-cit-to-gcp?project=arxiv-production).

### sync_published_to_gcp.py

There are 3 distinctive sections in the code, the planning, execution, and pub/sub interface.

* Pub/sub: submission_callback
* Planning: class SubmissionFilesState
* Execution: sync_to_gcp

As the process starts, the subscriber to the queue is registered as a pub/sub client.

Every message gets "submission_callback" as the daily announcemet submit the paper ID to the queue.

From it, first it creates the "sync plan" by creating an instance of SubmissionFilesState, and calls "get_expected_files()".
The returned value is a list of actions it needs to take.

#### Planning

Let's take an example from one of tests.

    def test_source_format_change(self):
        file_state = submission_message_to_file_state(
            {"type": "rep", "paper_id": "2403.99999", "version": 3, "src_ext": ".tar.gz"}, {},
            ask_webnode=False)
        expected = trim_test_dir(file_state.get_expected_files())
        self.assertEqual([
            {'type': 'abstract',
			 'cit': '/data/ftp/arxiv/papers/2403/2403.99999.abs',
             'status': 'current',
			 'gcp': 'ftp/arxiv/papers/2403/2403.99999.abs'},
            {'type': 'submission',
			 'cit': '/data/ftp/arxiv/papers/2403/2403.99999.tar.gz',
             'status': 'current',
			 'gcp': 'ftp/arxiv/papers/2403/2403.99999.tar.gz'},
            {'type': 'pdf-cache',
			 'cit': '/cache/ps_cache/arxiv/pdf/2403/2403.99999v3.pdf',
             'status': 'current',
			 'gcp': 'ps_cache/arxiv/pdf/2403/2403.99999v3.pdf'},
            {'type': 'abstract',
			 'cit': '/data/orig/arxiv/papers/2403/2403.99999v2.abs',
             'status': 'obsolete',
			 'version': 2,
             'obsoleted': 'ftp/arxiv/papers/2403/2403.99999.abs',
             'original': 'orig/arxiv/papers/2403/2403.99999v2.abs',
             'gcp': 'orig/arxiv/papers/2403/2403.99999v2.abs'},
            {'type': 'submission',
			 'cit': '/data/orig/arxiv/papers/2403/2403.99999v2.gz',
             'status': 'obsolete',
			 'version': 2,
			 'obsoleted': 'ftp/arxiv/papers/2403/2403.99999.gz',
             'original': 'orig/arxiv/papers/2403/2403.99999v2.gz',
             'gcp': 'orig/arxiv/papers/2403/2403.99999v2.gz'}
        ], expected)

Let's take a look at the first element.

* What kind of file to deal with:  'type': 'abstract'
* Where is the file on CIT?: 'cit': '/data/ftp/arxiv/papers/2403/2403.99999.abs'
* Why it needs to sync?: 'status': 'current'
* Where is the destination?: 'gcp': 'ftp/arxiv/papers/2403/2403.99999.abs'

The current one is a simple case. It needs to sync to GCP from CIT.

An interesting case is: `'status': 'obsolete'`. 

What this means is, the GCP's object became obsolete under /ftp, and needs
to be moved to /orig.

    'obsoleted': 'ftp/arxiv/papers/2403/2403.99999.gz',
    'original': 'orig/arxiv/papers/2403/2403.99999v2.gz'

Before attempting to copy the CIT's file to GCP, mimic the behavior of 
publishing process by moving "obsoleted" object to the "original" location.
By executing this, we can reduce the amount of copy as the older version 
of announced submission is moved to the /orig. 

During planning, it has to ask web nodes to generate the cached objects.
(PDF and HTML files)

PDF is straight forward as there is one file. For HTML files, once the
"ensure_html" call succeeds, the planner stores the HTML files (the
artifact of ensure_html) to the expected files.

Because of this for HTML, the number of files to copy is unknown until
ensure_html() returns the files in the ps_cache.

#### Execution

sync_to_gcp() function gets this list, and executes the plan in 2 phases.

First is the "obsolete" - look for the obsolete entries, and move the
bucket objects. So, this all happens within a GCP bucket.

Second is to copy the files from CIT to GCP.


## Running it

Any **bad** becomes nacking of the event. GCP pub/sub backs off so this 
becomes the retry attemp. When generating PDF, it is not unusual for
web node to fail to bulid PDF in time. 

If the events get stuck, someone needs to take a look at the failuer.
GCP logging gives some clue, and def. you can know the paper ID. 
Alart is set up on GCP so pay some attention to it.

