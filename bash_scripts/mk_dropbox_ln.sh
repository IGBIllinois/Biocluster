#!/bin/bash

USER=`whoami`;
if [ $UID -ge 1000 ]; then
	if [[ $USER =~ ^[a-m] ]]; then
		home_path="/home/a-m/$USER"
        	drop_path="/home/a-m/dropboxes/$USER"

	elif [[ $USER =~ ^[n-z] ]]; then
		home_path="/home/n-z/$USER"
        	drop_path="/home/n-z/dropboxes/$USER"
	fi

	if [ ! -d $home_path/dropbox ]; then
		ln -s $drop_path $home_path/dropbox
		echo "Created dropbox symbolic link"
	fi




fi


