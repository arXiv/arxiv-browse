cd /opt_arxiv/e-prints/dissemination/sync_prod_to_gcp/

# if running between 8pm and midnight
DATE=`date +%y%m%d --date='12:00 tomorrow'`
PUBLISHLOG=/data/new/logs/publish_$DATE.log
if [ ! -e $PUBLISHLOG ]
then
    echo "No publish log at $PUBLISHLOG, no sync attempted." > err.txt
    /bin/gsutil -q -h "Content-Type:text/plain" cp err.txt gs://legacy_support/sync_published/$DATE.err ;
    rm err.txt
    exit 1
fi

. venv/bin/activate
python sync_published_to_gcp.py /data/new/logs/publish_$DATE.log > sync_published_$DATE.report 2> sync_published_$DATE.err
deactivate

if [ -s sync_published_$DATE.report ]
then    
    if /bin/gsutil -q -h "Content-Type:text/plain" cp \
	sync_published_$DATE.report gs://legacy_support/sync_published/$DATE.report ;
    then
	rm sync_published_$DATE.report
    else
	echo "Could not save report to GS! leaving on disk"
    fi
else
    echo "Report was zero size" >> sync_published_$DATE.err
fi

if [ -s sync_published_$DATE.err ]
then
    head -n 100 sync_published_$DATE.err

    if /bin/gsutil -q -h "Content-Type:text/plain" cp \
	sync_published_$DATE.err gs://legacy_support/sync_published/$DATE.err ;
    then 
	printf "\n\nError log saved at gs://legacy_support/sync_published/$DATE.err\n"
	rm sync_published_$DATE.err
    else
	echo "Could not save error report! leaving on disk"
    fi

    exit 1
fi

