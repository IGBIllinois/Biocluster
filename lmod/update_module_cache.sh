#!/bin/bash
source /etc/profile
module use /opt/ohpc/admin/lmod/6.0.24/modulefiles/Core
module load lmod
update_lmod_system_cache_files $LMOD_DEFAULT_MODULEPATH
