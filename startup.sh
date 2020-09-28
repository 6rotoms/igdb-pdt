#!/usr/bin/env sh

python /script/populate_db.py --mock --persist >> /var/log/cron.log

cron
# keep alive
tail -f /dev/null
