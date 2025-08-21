#!/bin/bash

if [ -z $PAM_USER ]; then
	echo "PAM_USER environment variable unset. This script is to be used with pam_exec.so module";
	exit
fi
if [ $UID -lt 1000 ]; then
	exit
fi
if [[ $PAM_USER =~ ^[a-m] ]]; then
        drop_path="/home/a-m/dropboxes/$PAM_USER"

elif [[ $PAM_USER =~ ^[n-z] ]]; then
        drop_path="/home/n-z/dropboxes/$PAM_USER"
fi

if [ ! -d $PAM_USER ]; then
	mkdir -m 2773 $drop_path
	chown $PAM_USER.$PAM_USER $drop_path
	echo "$drop_path created"
else 
	echo "$drop_path already exists"
fi

