#!/bin/bash

PROGPATH=/usr/local/bin
MAX=2

time /usr/bin/python3 $PROGPATH/make_snapshots.py --fileset=a-m --max=$MAX
time /usr/bin/python3 $PROGPATH/make_snapshots.py --fileset=n-z --max=$MAX
time /usr/bin/python3 $PROGPATH/make_snapshots.py --fileset=labs --max=$MAX
time /usr/bin/python3 $PROGPATH/make_snapshots.py --fileset=groups --max=$MAX
