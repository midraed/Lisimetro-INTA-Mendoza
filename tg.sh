#!/bin/bash
now=$(date)
to=$1
subject=$2
body=$3
tgpath=/home/guillermo/tg
LOGFILE="/home/guillermo/tg.log"
cd ${tgpath}
${tgpath}/telegram -k ${tgpath}/tg-server.pub -W <<EOF
msg $to $subject
safe_quit
EOF
echo "$now Recipient=$to Message=$subject" >> ${LOGFILE}
echo "Finished" >> ${LOGFILE}
