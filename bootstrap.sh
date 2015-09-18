#!/bin/bash

# bootstrap.sh - for pulling up a dvmdostem development environment

#
#  Primary packages needed to compile and run dvm-dos-tem
#  * may need sudo??
#

#  NOTE: You've gotta install openmpi *after* NetCDF! This keeps NetCDF from
#  getting setup with some pesky #defines that cause errors when trying to
#  compile files that include <mpi.h>.
#  More info: http://www.unidata.ucar.edu/mailing_lists/archives/netcdfgroup/2009/msg00347.html
yum install -y git gcc-c++ jsoncpp-devel readline-devel netcdf-devel netcdf-cxx-devel boost-devel
yum install -y openmpi-devel

# Need this to fix the "H5Pset_dxpl_mpio" error that otherwise comes when
# running IPython and importing netCDF4
yum install -y hdf5-openmpi-devel

# this seems to help x11 forwarding
yum install -y xauth

# packages used for plotting
yum install -y python-matplotlib python-matplotlib-wx netcdf4-python python-ipython

# For processing/preparing the "new style" inputs
yum install -y gdal gdal-devel

# For compiling with Scons
yum install -y scons

#
# Bonus - basic functionality should exist w/o these packages and settings
#

yum install -y gitk git-gui

# For graphical debugging
# Note: If gdb is not installed, then QT Creator will complain about "Unable
#       to create a debugger engine of the type 'no engine'"
#       Also it may be necessary to install xterm. For some reason Colin and
#       Tobey's VMs (from this Vagrantfile) had xterm and gdb and Ruth's did
#       not...Strange?
yum install -y gdb xterm qt-creator

# For viewing IPython notebooks, and viewing Netcdf I/O files.
yum install -y ncview nco firefox


# The man page conflicts between vim and vim-minimal. Removing vim-minimal
# takes sudo with it, crippling later attempts at inline provisioning. So we
# make sure to reinstall sudo.
su -c "yum remove -y vim-minimal && yum install -y vim && yum install -y sudo"




# v---------NOTE NEED TO FIGURE OUT HOW TO CHANGE TO NORMAL USER FOR THIS

# add github's key to knownhosts
if [[ ! -f ~/.ssh/known_hosts ]]; then
  mkdir -p ~/.ssh
  touch ~/.ssh/known_hosts
fi

echo "Appending github's key to ~/.ssh/known_hosts..."
ssh-keyscan github.com >> $(HOME)/.ssh/known_hosts
chmod 600 ~/.ssh/known_hosts

# grab our own packages
if [ ! -d /home/vagrant/dvm-dos-tem ]
then
  git clone git@github.com:ua-snap/dvm-dos-tem.git /home/vagrant/dvm-dos-tem
fi
cd dvm-dos-tem
git remote rename origin upstream
git checkout devel
git pull --ff-only upstream devel:devel
cd ..

if [ ! -d /home/vagrant/ddtv ]
then
  git clone git@github.com:tobeycarman/ddtv.git /home/vagrant/ddtv
fi
cd ddtv
git remote rename origin upstream
git checkout master
git pull --ff-only upstream master:master
cd ..

# v---------NOTE NEED TO FIGURE OUT HOW TO CHANGE TO NORMAL USER FOR THIS

# setup the bashrc file
cat << EOF > $(HOME)/.bashrc
# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions

# Add git branch to bash prompt...
source /usr/share/git-core/contrib/completion/git-prompt.sh
export PS1='[\u@\h \W$(declare -F __git_ps1 &>/dev/null && __git_ps1 " (%s)")]\$ '

# set up some environment variables
export SITE_SPECIFIC_INCLUDES=-I/usr/include/jsoncpp
export PATH=$PATH:/usr/lib64/openmpi/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib64/openmpi/lib

EOF

# v---------NOTE NEED TO FIGURE OUT HOW TO CHANGE TO NORMAL USER FOR THIS

# setup some vim settings.
cat << EOF >> $(HOME)/.vimrc
syntax on              " this is needed to see syntax
set ls=2               " allways show status line
set hlsearch           " highlight searches
set incsearch          " do incremental searching
set ruler              " show the cursor position all the time
set visualbell t_vb=   " turn off error beep/flash
set ignorecase         " ignore case while searching
set number             " put numbers on side
set expandtab          " insert tabs instead of spaces
set tabstop=2          " use 2 spaces
set shiftwidth=2       " how many columns to move with reindent operators (>>, <<)

EOF


# Can we setup some general git congigurations??
# user, email, editor, color, etc??


