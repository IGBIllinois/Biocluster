#!/bin/bash

# Expected arguments are: $1="-s", $2=mail subject, $3=mail address
# That would correspond to a normal call of /usr/bin/mail

# extract the job ID from the standard mail subject produced by SLURM

log_file="/var/log/job.log"

job_id=$(echo $2 | cut -f 2 -d "=" | cut -f 1 -d " ")

#strip _* at end of job array job_id
substring="_\*"
if [[ $job_id =~ $substring ]];
then
        job_id="${job_id:0:-2}"
fi


# gather important information through sacct from SLURM

sleep 10
job_info=$(/usr/bin/sacct --jobs=$job_id --allocations --parsable2 --format JobName,NodeList,Partition,User,Account,ExitCode,Timelimit,NCPUS,NNodes,ReqMem,Submit,Start,End,Elapsed,State,Comment) || exit 


# prepare a table for the email body with job information
# in principle this is a transposed version of the sacct output

content=$(echo "$job_info" | awk -F "|" '
{ 
    for (i=1; i<=NF; i++)  {
        a[NR,i] = $i
    }
}
NF>p { p = NF }
END {    
    for(j=1; j<=p; j++) {
        str=a[1,j]
        for(i=2; i<=NR; i++){
            str=str":\t"a[i,j];
        }
        print str
    }
}')

# where are we running?

hostname=$(hostname)

# prepare the complete email text in a temporary file

echo -e "Biocluster SLURM daemon on $hostname.\nSince you requested to be informed by mail, here are some details of the corresponding job:\n\n" >> /tmp/$job_id.body
echo -e "$content" >> /tmp/$job_id.body
#echo -e "\n\nSincerly,\nYour friendly SLURM daemon\n" >> /tmp/$job_id.body
# get additional variables
# better to pull from here since the subject line changes due to there
# job name

node=$(sacct --jobs=$job_id --format=NodeList --noheader)
state=$(sacct --jobs=$job_id --format=state --noheader)
name=$(sacct --jobs=$job_id --format=JobName --noheader)

# remove white spaces from variable names

node=${node//[[:blank:]]/}
state=${state//[[:blank:]]/}
name=${name//[[:blank:]]/}

# send the email

#/usr/bin/mail -s "Job ${name} on $node [Job $job_id] changed status to $state" $3 < /tmp/$job_id.body
/usr/bin/mail -s "$2" $3 < /tmp/$job_id.body

# delete the temporary email text
rm /tmp/$job_id.body


