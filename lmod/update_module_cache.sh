#!/bin/bash
source /etc/profile
/opt/ohpc/admin/lmod/lmod/libexec/update_lmod_system_cache_files -t /home/apps/cache/system.txt -d /home/apps/cache/spidercache $MODULEPATH
