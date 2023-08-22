#!/bin/bash

#############
#Installation
#1. Install mailx and postfix. 'dnf -y install mailx postfix'
#2. Run newaliases. 'newaliases'
#3. Start Postfix. 'systemctl enable postfix', 'systemctl start postfix'
#4. Add script to /etc/cron.d/badnodes to run at 8AM'
#5. 00 08 * * * root /usr/local/biocluster/bash_scripts/badnodes.sh
############


MAILTO=help@igb.illinois.edu
HOSTNAME=`hostname`
FROM="`hostname -s`@`hostname`"
CURRENT_TIME=`date "+%s"`
BAD_NODES=`sinfo -h --format "%n %T" -R`
HEADER="Below is a list of nodes that are currently DOWN, DRNG, DRAINING, FAIL, or FAILING state"
MESSAGE="${HEADER}\n\n ${BAD_NODES}\n"

if [[ -n ${BAD_NODES} ]]; then
	echo -e "${MESSAGE}" | mailx -s "${HOSTNAME} - Bad Nodes" -r ${FROM} ${MAILTO}
fi
