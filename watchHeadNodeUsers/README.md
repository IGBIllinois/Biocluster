# watchHeadNodeUsers

* Fork of the original script from http://cva.stanford.edu/people/davidbbs/cluster/
* It runs on the headnode and/or login nodes of a cluster using cron
* Sends an email to a user if they were running an unauthorized process
* Useful so users do not run applications on headnode or login nodes.

## Installation

* Create directory /var/cache/watchHeadNodeUsers/.  It saves the state of the ps command in there
```
mkdir /var/cache/watchHeadNodeUsers
```
* Add it to cron to run every minute
```
* * * * * root /usr/local/sbin/watchHeadNodeUsers.py
```
* Copy log_rotate.conf.dist to /etc/logrotate.d/watchHeadNodeUsers to rotate log file
```
cp log_rotate.conf.dist /etc/logrotate.d/watchHeadNodeUsers
```
* Edit watchHeadNodeUsers.py variables for your environment
```
logFile = "/var/log/watchHeadNodeUsers.log"
stateFile = "/var/cache/watchHeadNodeUsers/watchHeadNodeUsers.state"
sendmailCommand = "/usr/sbin/sendmail"
emailServer = ""
alwaysCCOnAlerts = ""
emailFromAddress = ""
```

