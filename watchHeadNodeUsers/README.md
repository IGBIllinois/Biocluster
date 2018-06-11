# watchHeadNodeUsers

* This came from [http://cva.stanford.edu/people/davidbbs/cluster/]
* It runs on the headnode and/or login nodes of a cluster using cron
* Sends an email to a user if they were running an unauthorized process
* Useful so users do not run applications on headnode or login nodes.

## Installation

* Create directory /var/cache/watchHeadNodeUsers/.  It saves the state of the ps command in there
```
mkdir /var/cache/watchHeadNodeUsers
```
* Copy config.inc.py.dist to config.inc.py
```
cp config.inc.py.dist config.inc.py
```
* Edit config.inc.py to have your sendmail command, email server, cc email, from address, and the mail message you want to have
* Add it to cron to run every minute
```
* * * * * root /usr/local/sbin/watchHeadNodeUsers.py
```
