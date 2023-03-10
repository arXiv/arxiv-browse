import subprocess
from datetime import datetime

logs_dir = '/opt_arxiv/e-prints/sync_to_arxiv_production/logs'

remote = 'remote:' #name configured with rclone
bucket = 'arxiv-production-data'

excludes = "--exclude 'lost+found/**' --exclude '.snapshot/**' --exclude '.htaccess'  "
"--exclude '.nfs*'  --exclude '.cit_nfs_mount_test'  --exclude 'arxiv-sync.txt'"

args = "--modify-window 1100ms"

template = f'/usr/bin/rclone sync {excludes} {args} {{0}} remote:{{1}}'

rclone_exit_codes ={
    0: "Success",
    1: "Syntax or usage error",
    2: "Error not otherwise categorised",
    3: "Directory not found",
    4: "File not found",
    5: "Temporary error (one that more retries might fix) (Retry errors)",
    6: "Less serious errors (like 461 errors from dropbox) (NoRetry errors)",
    7: "Fatal error (one that more retries won't fix, like account suspended) (Fatal errors)",
    8: "Transfer exceeded - limit set by --max-transfer reached",
    9: "Operation successful, but no files transferred",
}

#        from          to              logname
jobs = [['/data/ftp', f'{bucket}/ftp/', 'ftp'],
        ['/data/orig', f'{bucket}/orig', 'orig'],
        ['/cache/ps_cache', f'{bucket}/ps_cache', 'ps-cache'],
        ]

timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")

def dosync(frm, to, logname, timestamp):
    command = template.format(frm, to)
    logfilename = 'logs/{logname}-{timestamp}.log'
    with open(logfilename, 'w') as outfh:
        process = subprocess.run(command.split(), stdout=outfh, stderr=subprocess.STDOUT)
        if process.returncode in [0, 9]:
            log('INFO', rclone_exit_codes[process.returncode])
        elif process.returncode in rclone_exit_codes:
            log('ERROR', rclone_exit_codes[process.returncode])
            send_logs(frm, to, logfilename)
        else:
            log('ERROR', f"non-zero unknown exit code by rclone of {process.returncode}")
            send_logs(frm, to, logfilename)


def log(severity, msg):
    print(severity + " " + msg)

def send_logs(frm, to, logfilename):
    pass
