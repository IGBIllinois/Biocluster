#!/usr/bin/env python3

import argparse
from ping3 import ping
import re
from python_hosts import Hosts
import os
import errno
import subprocess
import time

descriptordir="/root/gpfs-descriptors/"
#descriptordir="/home/danield/Software/cluster/"
hostsfile="/etc/hosts"

parser = argparse.ArgumentParser(description="Add a Node to Warewulf")
parser.add_argument('--nodename',type=str,required=True,help="Name of node data network (data-compute-x-y)")
args=parser.parse_args()

def check_nodename(nodename, hostsfile):
    print("Looking for "+nodename)
    for entry in Hosts(hostsfile).entries:
        if entry.entry_type == 'ipv4':
            for name in entry.names:
                #print("check match on "+name)
                if name == nodename:
                    print("Found "+nodename)
                    return True
    return False

def check_ip_usage(address):
    print("Pinging "+address)
    response=ping(address)
    if response == None or response == False:
        return False
    else:
        return True

#check if node defined
if not check_nodename("data-"+args.nodename, hostsfile):
    print("Node data-"+args.nodename+" does not seem to be defined")
    quit()
else:
    print("Node data-"+args.nodename+" found")

#check if on network
if not check_ip_usage("data-"+args.nodename+".data.igb.illinois.edu"):
    print("Node "+args.nodename+" does not seem to be on line")
    quit()
else:
    print("Node "+args.nodename+" is on line")

#check if nodefile exists and write it
try:
    nodedescriptor=open(descriptordir+"data-"+args.nodename,"x")
except OSError as e:
    if e.errno == errno.EEXIST:
        print("The file "+descriptordir+"data-"+args.nodename+" already exists.  Make sure it is not needed before removing it.")
        quit()
    else:
        raise
nodedescriptor.write("data-"+args.nodename+":client-nonquorum:data-"+args.nodename)
nodedescriptor.close()

#check if already in cluster
print("Check if node already known by gpfs")
#print("mmlsnode |grep \" data-"+args.nodename+" \"")
process = subprocess.run("mmlsnode |grep \" data-"+args.nodename+" \"", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
error=process.stderr.decode('ascii')
output=process.stdout.decode('ascii')
if error != "":
    print(process.stderr)
    quit()
elif output != "":
    print("Problem adding node, seems like it might exist already")
    quit()
else:
    print("Node data-"+args.nodename+" looks to not be part of the cluster yet, proceeding")


#Add node to gpfs
print("Add node to GPFS")
#print("mmaddnode -N data-"+args.nodename+" --accept")
process = subprocess.run("mmaddnode -N data-"+args.nodename+" --accept", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
error=process.stderr.decode('ascii')
output=process.stdout.decode('ascii')
if not re.search("Command successfully completed", error):
    print("unknown error")
    print("ERROR: "+error)
    print("OUTPUT: "+output)
    quit()
elif re.search("Processing node data-"+args.nodename, output):
    print("Node successfully added")
else:
    print("Problem adding node")
    print("ERROR: "+error)
    print("OUTPUT: "+output)
    quit()
    
#change licensing
print("License Node in GPFS")
#print("mmchlicense client --accept -N data-"+args.nodename)
process = subprocess.run("mmchlicense client --accept -N data-"+args.nodename, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
error=process.stderr.decode('ascii')
output=process.stdout.decode('ascii')
if not re.search("Command successfully completed", error):
    print("ERROR: "+error)
    print("OUTPUT: "+output)
    quit()
elif re.search("The following nodes will be designated as possessing client licenses", output) and re.search("data-"+args.nodename, output):
    print("Node successfully added")
else:
    print("Problem changing license")
    print("ERROR: "+error)
    print("OUTPUT: "+output)
    quit()
    
#set autoload
print("Configure GPFS to autoload on node")
#print("mmchconfig autoload=yes -N data-"+args.nodename)
process = subprocess.run("mmchconfig autoload=yes -N data-"+args.nodename, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
error=process.stderr.decode('ascii')
output=process.stdout.decode('ascii')
if not re.search("Command successfully completed", error):
    print("ERROR: "+error)
    print("OUTPUT: "+output)
    quit()
elif output=="":
    print("Node autoloading gpfs")
else:
    print("Problem autoloading gpfs")
    print("ERROR: "+error)
    print("OUTPUT: "+output)
    quit()
    
#wait a few seconds
#time.sleep(3)

#update mmsdrfs
print("Update mmsdrfs in warewulf")
#print("wwsh file sync")
process = subprocess.run("wwsh file sync", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
error=process.stderr.decode('ascii')
output=process.stdout.decode('ascii')
if error != "":
    print("ERROR: "+error)
    print("OUTPUT: "+output)
    quit()
elif output=="":
    print("Files Updated")
else:
    print("Problem updating files")
    print("ERROR: "+error)
    print("OUTPUT: "+output)
    quit()
    
#provision mmsdrifs for node
print("Provision mmsdrfs to node")
#print("wwsh -y provision set "+args.nodename+" --fileadd mmsdrfs")
process = subprocess.run("wwsh -y provision set "+args.nodename+" --fileadd mmsdrfs", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
error=process.stderr.decode('ascii')
output=process.stdout.decode('ascii')
if error != "":
    print("ERROR: "+error)
    print("OUTPUT: "+output)
    quit()
elif output=="":
    print("mmsdrfs provisioned")
else:
    print("Problem provisioning mmsdrfs")
    print("ERROR: "+error)
    print("OUTPUT: "+output)
    quit()
    
#tell to reboot node
print("Now you need to reboot the compute node")
