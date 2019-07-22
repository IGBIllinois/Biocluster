#!/usr/bin/env bash
IFS=$'\n'
 for i in $(find . -maxdepth 2 -mindepth 2 -type d|grep -v "^\./\."|grep -v "^.$");
 do
    #echo "$i"
    #find $i -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" "
    #echo "$i `find $i -type f| xargs --no-run-if-empty -I '{}' stat --format '%Y :%y %n' '{}'| sort -nr | cut -d: -f2-  |cut -d" " -f1,4- |head -n1`"
    echo -e "\"$i\"\t`find $i -type f -printf '"%p"\n'|xargs -I '{}' stat --format '%Y :%y %n' '{}' 2> /dev/null |sort -nr| cut -d: -f2-  |cut -d" " -f1,4- |head -n1`"
 done
unset IFS
