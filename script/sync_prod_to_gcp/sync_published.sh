#!/bin/bash

PIDFILE="/var/run/sync_to_gcp_cron_job.pid"

if [ -f "$PIDFILE" ]; then
    # Check if the process with the stored PID is still running
    PID=$(cat "$PIDFILE")
    if ps -p $PID > /dev/null; then
        # Wait loop to wait until the lock is released
        while ps -p $PID > /dev/null; do
            sleep 1
        done
    else
        rm "$PIDFILE"
    fi
fi
echo $$ > "$PIDFILE"

# Remove the lock file at exit.
at_exit() {
    if [ -f "$PIDFILE" ]; then
        FILE_PID=$(cat "$PIDFILE")
        if [ "$FILE_PID" -eq "$$" ]; then
            rm -f "$PIDFILE"
        fi
    fi
}
trap at_exit EXIT


TEXT_LOG_DIR=/opt_arxiv/e-prints/dissemination/sync_prod_to_gcp
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"
if [ ! -d sync.venv ] ; then
  make
fi

# Is this a test/
if [ "$1" = "YES_THIS_IS_A_TEST" ]
then
    shift
    TESTING_ARGS="-v -d --test"
fi

# if running between 8pm and midnight
DATE=`date +%y%m%d --date='12:00 tomorrow'`
if [ ! -z $1 ]
then
    DATE=$1
fi

PUBLISHLOG=/data/new/logs/publish_${DATE}.log
if [ ! -e $PUBLISHLOG ]
then
    echo "No publish log at $PUBLISHLOG, no sync attempted."
    echo "No publish log at $PUBLISHLOG, no sync attempted." > $TEXT_LOG_DIR/err.txt
    /bin/gsutil -q -h "Content-Type:text/plain" cp $TEXT_LOG_DIR/err.txt gs://legacy_support/sync_published/$DATE.err ;
    rm err.txt
    exit 1
fi

JSON_LOG_DIR=/opt_arxiv/e-prints/logs/sync
mkdir -p $JSON_LOG_DIR

. sync.venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=~/arxiv-production-cred.json
python sync_published_to_gcp.py $TESTING_ARGS --json-log-dir $JSON_LOG_DIR  /data/new/logs/publish_$DATE.log >> $TEXT_LOG_DIR/sync_published_$DATE.report 2>> $TEXT_LOG_DIR/sync_published_$DATE.err
deactivate

if [ ! -z "$TESTING_ARGS" ]; then 
    exit 0
fi

if [ -s $TEXT_LOG_DIR/sync_published_$DATE.report ]
then    
    if /bin/gsutil -q -h "Content-Type:text/plain" cp \
	$TEXT_LOG_DIR/sync_published_$DATE.report gs://legacy_support/sync_published/$DATE.report ;
    then
	rm -f $TEXT_LOG_DIR/sync_published_$DATE.report
    else
	echo "Could not save report to GS! leaving on disk"
    fi
else
    echo "sync_published_to_gcp upload report was zero size" >> $TEXT_LOG_DIR/sync_published_$DATE.err
fi

if [ -s $TEXT_LOG_DIR/sync_published_$DATE.err ]
then
    head -n 100 $TEXT_LOG_DIR/sync_published_$DATE.err

    if /bin/gsutil -q -h "Content-Type:text/plain" cp \
	$TEXT_LOG_DIR/sync_published_$DATE.err gs://legacy_support/sync_published/$DATE.err ;
    then 
	printf "\n\nError log saved at gs://legacy_support/sync_published/$DATE.err\n"
	rm $TEXT_LOG_DIR/sync_published_$DATE.err
    else
	echo "Could not save error report! leaving on disk"
    fi

    exit 1
fi
