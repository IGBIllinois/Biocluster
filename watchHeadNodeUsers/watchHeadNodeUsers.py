#!/usr/bin/env python

#
# A script to watch for excesive CPU usage by users on the head node.
# This script functions by running top every so often to look for any
# processes that are using too much CPU/memory. If it finds any it then
# checks to see if they belong to a group for "real" users. If that is
# found to be true then the temperature for that user/process is increased.
# Once the temperature gets high enough a warnining email is sent, the
# temperature is decreased, and the time of the warning is recorded.
# On every cycle all temperatures are decreased and user/processes that are 
# below a certain temperature are removed from the watch list.
#
# If a user process gets up in temperature again a warning is only sent
# if the last warning was sent sufficiently earlier. (I.e., we only want 
# to send 1 warning every 12 hours and not one every 5 minutes.)
#
# Created by David Black-Schaffer.
#

import sys, re, os, time, datetime, pickle


DEBUG = False

# File to log to
logFile = "/var/log/watchHeadNodeUsers.log"
# File to store our state from run to run
stateFile = "/var/cache/watchHeadNodeUsers/watchHeadNodeUsers.state"

# If we're debugging use local files
if (DEBUG):
	logFile = "./watchHeadNodeUsers.log"
	stateFile = "./watchHeadNodeUsers.state"

# Commands
topCommand = "/bin/ps -A o pid,user:18,s,%cpu,%mem,time,comm"
localAccountsCommand = "awk -F':' '{ print $1}' /etc/passwd | grep"
sendmailCommand = "/usr/sbin/sendmail"
emailServer = "igb.illinois.edu"

# Someone to always CC on email alerts
alwaysCCOnAlerts = "cnrg-warn@igb.illinois.edu"
# The from address for the emails
emailFromAddress = "Biocluster <do-not-reply@igb.illinois.edu>"
# Mail message body
mailMessage = "Hello,\n\tThis is a friendly reminder that you have been running a process on the Biocluster login node. You should not run anything that uses up a lot of CPU or memory on the login node. Instead please use 'srun --pty /bin/bash' to login to a compute node. More information can be found at https://help.igb.illinois.edu/Biocluster\n"

# Processes to ignore
processesToIgnore = ["smbd", "Xvnc", "sshd", "ssh", "rsync","wget", "mmfsd", "scp", "grep","sftp-server","vim","sftp","cp","gftp-gtk","system-specific","find","emacs","globus-gridftp-","sort","cut","du","ftp","lftp","uzip","ascp","aws","gtdownload","less","curl","rclone","gdc-client","iget","prefetch","conda","fastq-dump"]
# Users to ignore
usersToIgnore = ["blastweb","datamover"]
# Thresholds for CPU and memory usage that lead to an increase in the user's
#  record temperature.
cpuLimit = 15.0
memLimit = 5.0


# A dictionary between user-process and the hotness of each process.
userRecords = {}
# A dictionary between user-processes and the details of their usage
userProcess = {}
# Last warned dates. 
userLastWarned = {}
# Time between warnings in hours
hoursBetweenWarnings = 2

# How much the record is decreased on each iteration (every sleepTime)
recordCoolDown = 1
# How much the record is increased each time it uses too much CPU/memory
recordPenalty = recordCoolDown + 10
# Threshold for sending a warning.
# If this is run every 5 minutes, then with recordPenalty = 11 and recordCoolDown = 1,
#  a user will get a warning after 2 runs (10 minutes) with a warning threshold
# of 20.
recordWarningThreshold = 20 




# Open the logfile
try:
    log = open(logFile, "a")
except IOError:
    print "Could not open log file for writing. Using 'temp.log' instead. " + logFile
    log = open("temp.log", "a")


# Open the previous data
try:
	pickleFile = open(stateFile, "r")
	[userRecords, userProcess, userLastWarned] = pickle.load(pickleFile)
	pickleFile.close()
except IOError or PickleError:
	print "Could not open previous state. Creating a new one..."


        
# Slowly cool down the userRecords' temperatures so they will be removed
#  once they are not active.
for record in userRecords.keys():
	userRecords[record] = userRecords[record] - recordCoolDown;
	# If it's too cold remove the record.
	if (userRecords[record] <= 0):
		if (DEBUG):
			print "Removing record for user " + record
		del userRecords[record]
		del userProcess[record]

# Remove all the last warned times that are out of date.
for record in userLastWarned.keys():
	if (userLastWarned.has_key(record)):
		difference = datetime.datetime.now() - userLastWarned[record]
		timediff = difference.seconds/3600.0 + difference.days*24.0
		if (timediff > (hoursBetweenWarnings+1)):
			if (DEBUG):
				print "Removing last warned date: "+ str(userLastWarned[record]) +" for user " + record
			del userLastWarned[record]

# Get the top output
child = os.popen(topCommand, "r")

# Read in the headers
headers = child.readline()

# Look at each process running
for line in child.readlines():
	match = re.search("\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", line)
	if (match):
		PID = match.group(1)
		user = match.group(2)
		cpu = match.group(4)
		mem = match.group(5)
		cpuTime = match.group(6)
		process = match.group(7)
	
		cpuPercent = float(cpu)
		memPercent = float(mem)
	
		# If it is using too much CPU or memory check if it is a real user process.
		if (((cpuPercent >= cpuLimit) | (memPercent >= memLimit)) & (process not in processesToIgnore)):
			if (DEBUG):
				print "\t1. User: " + user + " is over limits: " + str(cpuPercent) + "/" + str(memPercent)
			# Check if this is a real user by seeing if they are not in
			# the passwd file which should include only local users
			child2 = os.popen(localAccountsCommand + " " + user, "r")
			result = child2.readline()
			child2.close()
			if(DEBUG):
				print "\t1. user found in passwd " + result
			realUser = True
			if (result):
				realUser = False
				if (DEBUG):
					print "\t2. User local match: " + user
			if(user in usersToIgnore):
				realUser = False
                              	if (DEBUG):
                                      	print "\t2. User to ignore: " + user
			# If it is a real user processes, then increase the temperature for
			#  this processes by indexing it in the dictionary by username-process.
			#  This insures that even if the PID changes we'll still find them.
			if (realUser):
				now = datetime.datetime
				record = user+"-"+process
				if (DEBUG):
					print "\t3. Increasing: " + str(now.now()) + PID + " " + user + " " + cpu + " " + mem + " " + cpuTime + " " +process
				# Increment the userRecord
				if (userRecords.has_key(record)):
					userRecords[record] = userRecords[record] + recordPenalty
				else:
					userRecords[record] = recordPenalty
				userProcess[record] = "\nuser: " + user + "\nprocess: " + process + "\nPID: " + PID + "\ncpu%: " + cpu + "\nmem%: " + mem + "\ncpu time: " + cpuTime
		
				log.write(str(now.now()) +": " + record + " (" + PID + " cpu:" + cpu + " mem:" + mem + " cpuTime: " +cpuTime+") = " + str(userRecords[record]) +"\n")
				log.flush()
			
# We're done with the top output
child.close()






# Look for any records that need to get warnings
for record in userRecords.keys():
	if (DEBUG):
		print record + " = " + str(userRecords[record])

	if (userRecords[record] >= recordWarningThreshold):
	# Reset the record temp. It will be removed next time.
		userRecords[record] = 0
	
		# Check that we haven't sent a warning in the last day
		okToSendWarning = True
		if (userLastWarned.has_key(record)):
			difference = datetime.datetime.now() - userLastWarned[record]
			timediff = difference.days*24.0 + difference.seconds/3600.00
			if (timediff < hoursBetweenWarnings):
				okToSendWarning = False
				if (DEBUG):
					print "Not okay to send warning: difference: " + str(timediff) + " from: " + str(userLastWarned[record]) + " < " + str(hoursBetweenWarnings)
				else:
					log.write(str(now.now()) +": Not sending warning for: " + record +"\n")
			else:
				if (DEBUG):
					print "Okay to send warning: difference: " + str(timediff) + " from: " + str(userLastWarned[record]) + " > " + str(hoursBetweenWarnings)
		
		if (okToSendWarning):
			# Record the time of the warning
			userLastWarned[record] = datetime.datetime.now()
	
			# Find the user name and send a polite email.
			# match = re.search("([A-Za-z0-9_-]+)-(.*)", record)
			match = re.search("user: (.*?)\\nprocess: (.*?)\\n", userProcess[record], re.M)
			userEmail = match.group(1) + "@" + emailServer
			userCommand = match.group(2)

			# userEmail = "cnrg-warn@igb.illinois.edu"	
			if (DEBUG):
				print record + " gets warning for " + userCommand
	
			now = datetime.datetime
			nowStr = str(now.now())
			log.write(nowStr + ": warning to " + record +" for " + userProcess[record] + "\n")
	
			# Build and send the email.
			p = os.popen(sendmailCommand +" -t", "w")
			p.write("To: " + userEmail + "\n")
			p.write("CC: "+ alwaysCCOnAlerts + "\n")
			p.write("Reply-To: help@igb.illinois.edu\n")
			p.write("Subject: Biocluster Login Node Usage Reminder (" + record +")\n")
			p.write("From: " + emailFromAddress + "\n")
			p.write("\n")
			p.write(mailMessage + "\n")
			p.write("\n")
			p.write("If you have any questions about this please contact us at help@igb.illinois.edu.\n")
			p.write("\n")
			p.write("Computer and Network Resource Group\n")
			p.write("\n")
			p.write("Process details: " + userProcess[record] +"\n")
			p.write("Limits: %cpu: " + str(cpuLimit) + " %mem: " + str(memLimit) +"\n")
			p.write("Warning sent: " +nowStr + "\n")
			p.write("\n")
			result = p.close()
			log.write(str(now.now()) +": sending warning to " + userEmail + " for " + record+"\n")
			log.flush()

# Save the state
try:
	pickleFile = open(stateFile, "w")
	pickle.dump([userRecords, userProcess, userLastWarned], pickleFile)
	pickleFile.close()
except IOError or PickleError:
	print "ERROR: could not write data to state file " + stateFile

	
log.close()
 
