#!/bin/bash 

# Using this script will be easiest if you have setup ssh
# keys that allow access to the remote (source) system.
# Also assumed that you have something like the following 
# settings in your ~/.ssh/config
#
#    Host atlas
#    HostName atlas.snap.uaf.edu
#    User tcarman2
#    IdentityFile ~/.ssh/tbc-modex-key

# We are maintaining the primary input catalog on the atlas
# server at UAF, in part because the scripts and source data
# for generating new dvmdostem inputs are functioning on atlas.
SRC="atlas:/big_scratch/tem/dvmdostem-input-catalog/"

# USER SHOULD SET THE DESTINATION PATH!
# This can be hard coded into this script or set from and enviornment
# variable. If you hard-code the value in this script, you may have
# to stash or discard your changes before updating from git. For this
# reason, it may be easier to set the DST environment variable before
# running this update script.
# EXAMPLE:
#    $ DST="/home/vagrant/data/mirrors/atlas/dvmdostem-input-catalog" ./update-mirror.sh

if [[ -z $DST ]]
then
  echo "ERROR!"
  echo "You must set the DST (destination) path before running this script!"
  echo "Example:"
  echo "  $ DST=/some/path/dvmdostem-input-catalog ./update-mirror.sh"
  echo ""
  exit -1
fi 

echo "Updating data from atlas..."
rsync -avz --delete --exclude='.DS_Store' --exclude="*/output/*" "$SRC" "$DST"
