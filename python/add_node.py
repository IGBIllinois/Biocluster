#!/usr/bin/env python3

import argparse
import ipaddress
from ping3 import ping
import re
from python_hosts import Hosts
import os
import errno
import subprocess
import time

#network definitions
clusternet='10.1.2.0/24'
datanet='172.16.28.0/24'
gateway='10.1.1.1'
netconfig='/root/node-network-configs/'
#netconfig='./'
hostsfile='/etc/hosts'
vnfs='standard-20220920'
bootstrap='4.18.0-348.23.1.el8_5.x86_64'

env = {}
env.update(os.environ)

if not os.access(netconfig, os.W_OK):
    print("Cannot write private network config to "+netconfig)
    quit()

def validate_ip_address(address):
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        print("IP address {} is not valid".format(address))
        quit()

def check_ip_space(address,network):
    if not ipaddress.ip_address(address) in ipaddress.ip_network(network):
        print("Error: IP address "+address+" is not in network "+network)
        print("This could be an error if network is not defined properly in this script")
        quit()
        
def check_ip_usage(address):
    response=ping(address)
    if response == None or response == False:
        print("IP "+address+" looks free")
    else:
        print("Error: IP address "+address+" is in use")
        print(response)
        quit()

def format_hw_address(address):
    if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", address.lower()) and not re.match("[0-9a-f]{4}.[0-9a-f]{4}.[0-9a-f]{4}$", address.lower()) and not re.match("[0-9a-f]{12}$",address.lower(
)):
        print("Hardware address "+address+" is not a valid hw address")
        quit()
    else:
        #remove the .-: characters
        address=address.replace('.','')
        address=address.replace(':','')
        address=address.replace('-','')
        return ':'.join(re.findall('..',address.lower())) 

def check_nodename(nodename, ip, hostsfile):
    for entry in Hosts(hostsfile).entries:
        if entry.entry_type == 'ipv4':
            if ip == entry.address:
                print("Error: Cluster IP address already defined in /etc/hosts")
                quit()
            for name in entry.names:
                if "data-"+name == nodename:
                    print("Error: Node name already defined in /etc/hosts")
                    quit()

parser = argparse.ArgumentParser(description="Add a Node to Warewulf")
parser.add_argument('--nodename',type=str,required=True,help="Name of node (compute-x-y)")
parser.add_argument('--ip',type=str,required=True,help="IP address of cluster interface (10.1.2.x)")
parser.add_argument('--dataip',type=str,required=True,help="IP address of data interface (172.16.28-32.x)")
parser.add_argument('--hwaddr',type=str,required=True,help="Hardware address of node network interface")
parser.add_argument('--datahwaddr',type=str,help="Hardware address of data network inteface, defaults to hwaddr")
parser.add_argument('--interface',type=str,default='eth0',help="Name of the network interface on the node (default eth0)")
parser.add_argument('--dataint',type=str,default='eth0.150',help="Name of the data network interace on node (default eth0.150)")
args=parser.parse_args()

#set data hw address to cluster hw address if data hw address does not exist
if args.datahwaddr == None:
  args.datahwaddr=args.hwaddr

#Check if ip addresses are valid
validate_ip_address(args.ip)
validate_ip_address(args.dataip)

#Check if ips are in networks
check_ip_space(args.ip,clusternet)
check_ip_space(args.dataip,datanet)

#Check if HWADDRs are valid and get in correct format
args.hwaddr=format_hw_address(args.hwaddr)
args.datahwaddr=format_hw_address(args.datahwaddr)

#check if ip address or hostname defined in /etc/hosts
check_nodename(args.nodename, args.ip, hostsfile)

#Check if ip addresses are on the network
check_ip_usage(args.ip)
check_ip_usage(args.dataip)

#if you made it this far, then it should be safe to run the commands
#write data network config file

try:
    dataipfile=open(netconfig+args.nodename+'-'+args.dataint,"x")
except OSError as e:
    if e.errno == errno.EEXIST:
        print("The file "+netconfig+args.nodename+'-'+args.dataint+" already exists.  Make sure it is not needed before removing it.")
        quit()
    else:
        raise
dataipfile.write("DEVICE="+args.dataint+"\nBOOTPROTO=static\nONBOOT=yes\nIPADDR="+args.dataip+"\nNETMASK=255.255.252.0\nHWADDR="+args.datahwaddr+"\nVLAN=yes")
dataipfile.close()
#update hosts to include data ip information
readhost=open(hostsfile,'r')
hostlines=readhost.readlines()
readhost.close
time.sleep(1)

#update /etc/hosts to include the data ip for the new node
writehost=open(hostsfile,'w')
for line in hostlines:
    if line == "### ALL ENTRIES BELOW THIS LINE WILL BE OVERWRITTEN BY WAREWULF ###\n":
        #print(args.dataip+"\t"+args.nodename+" "+args.nodename+".data.igb.illinois.edu")
        writehost.writelines(args.dataip+"\tdata-"+args.nodename+" data-"+args.nodename+".data.igb.illinois.edu\n")
    #print(line)
    writehost.writelines(line)
writehost.close()
time.sleep(1)

#add the node
print("/usr/bin/wwsh -y -v node new "+args.nodename+" --netdev="+args.interface+" --ipaddr="+args.ip+" --gateway="+gateway+" --hwaddr="+args.hwaddr)
process = subprocess.run("/usr/bin/wwsh -y node new "+args.nodename+" --netdev="+args.interface+" --ipaddr="+args.ip+" --gateway="+gateway+" --hwaddr="+args.hwaddr, shell=True, stdout=subprocess.PIPE, stderr=sub
process.PIPE)
print(process)
error=process.stderr.decode('ascii')
if error != "":
    print(process.stderr)
    quit()
      
#add changing files to node
print("wwsh file import "+netconfig+args.nodename+'-'+args.dataint+" --path=/etc/sysconfig/network-scripts/ifcfg-"+args.dataint)
process = subprocess.run("wwsh file import "+netconfig+args.nodename+'-'+args.dataint+" --path=/etc/sysconfig/network-scripts/ifcfg-"+args.dataint, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
error=process.stderr.decode('ascii')
if error != "":
    print(error)
    quit()
    
#provision the node
print("wwsh provision set "+args.nodename+"  --vnfs="+vnfs+" --bootstrap="+bootstrap+" --files=dynamic_hosts,passwd,group,shadow,munge.key,network,"+args.nodename+'-'+args.dataint)
process = subprocess.run("wwsh provision set "+args.nodename+"  --vnfs="+vnfs+" --bootstrap="+bootstrap+" --files=dynamic_hosts,passwd,group,shadow,munge.key,"+args.nodename+'-'+args.dataint, shell=True, stderr=
subprocess.PIPE, stdout=subprocess.PIPE)
error=process.stderr.decode('ascii')
if error != "":
    print(error)
    quit()
    
print("Now you need to reboot the node")
