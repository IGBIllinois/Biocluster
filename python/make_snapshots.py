#!/usr/bin/env python3 

import argparse
import datetime
import os
import re

fsroot="/IGBDATA"
filesystem='igbdata'

parser = argparse.ArgumentParser(description="Snapshot Manager")
parser.add_argument('--fileset',type=str,required=True,help="GPFS fileset to make snapshot on")
parser.add_argument('--max',type=int,default=0,help="Maximum number of snapshots under managment to allow in filesystem")
args=parser.parse_args()

date=datetime.datetime.now()
date=date.strftime("%Y%m%d")

subfolders = [ f.path for f in os.scandir(fsroot+'/'+args.fileset+'/.snapshots/') if f.is_dir() ]
subfolders = [os.path.basename(subfolder) for subfolder in subfolders]
subfolders = [ subfolder for subfolder in subfolders if re.match("\d{8}",subfolder) ]

if args.max >0:
    print(subfolders)
    if date in subfolders:
        print("Today's snapshot already exists, exiting")
        quit()
    else:
        while len(subfolders)>=args.max:
            subfolders.sort()
            print(subfolders[0])
            print("/usr/lpp/mmfs/bin/mmdelsnapshot "+filesystem+" "+args.fileset+":"+subfolders[0])
            response=os.system("/usr/lpp/mmfs/bin/mmdelsnapshot "+filesystem+" "+args.fileset+":"+subfolders[0])
            print(response)
            subfolders = [ f.path for f in os.scandir(fsroot+'/'+args.fileset+'/.snapshots/') if f.is_dir() ]
            subfolders = [os.path.basename(subfolder) for subfolder in subfolders]
            subfolders = [ subfolder for subfolder in subfolders if re.match("\d{8}",subfolder) ]
else:
    print("Not removing any old snapshots")

if not os.path.exists(fsroot+'/'+args.fileset+'/.snapshots/'+date):
    print("/usr/lpp/mmfs/bin/mmcrsnapshot "+filesystem+" "+args.fileset+":"+date)
    response=os.system("/usr/lpp/mmfs/bin/mmcrsnapshot "+filesystem+" "+args.fileset+":"+date)
    print(response)
else:
    print("Error: snapshot "+date+" appears to already exist in "+fsroot+'/'+args.fileset+'/.snapshots/')
    quit()
