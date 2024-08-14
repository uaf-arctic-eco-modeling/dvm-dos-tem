#!/bin/bash

#
# bootstrap-sel-custom.sh
#
# Clones SEL repos, sets up dotfiles, (bashrc, vimrc, etc), any other
# user level settings.
#

echo "Running bootstrap-sel-custom.sh script..."
echo "Should not require sudo priviledges to run!"

#
# Note: Not sure if it is better to use tilde or "$HOME" ??
#

#
# add github's key to knownhosts
#
if [[ ! -f ~/.ssh/known_hosts ]]; then
  mkdir -p ~/.ssh
  touch ~/.ssh/known_hosts
fi

echo "Appending github's key to ~/.ssh/known_hosts..."
ssh-keyscan github.com >> "$HOME"/.ssh/known_hosts
chmod 600 "$HOME"/.ssh/known_hosts

#
# Clone our software repos...
#
if [ ! -d "$HOME"/dvm-dos-tem ]
then
  git clone https://github.com/ua-snap/dvm-dos-tem.git "$HOME"/dvm-dos-tem  
fi
cd dvm-dos-tem
git remote rename origin upstream
git checkout devel
git pull --ff-only upstream devel:devel
git checkout master
git pull --ff-only upstream master:master
cd ..

if [ ! -d "$HOME"/ddtv ]
then
  git clone git@github.com:tobeycarman/ddtv.git "$HOME"/ddtv
fi
cd ddtv
git remote rename origin upstream
git checkout master
git pull --ff-only upstream master:master
cd ..

#
# setup various preference files (dotfiles)
#

# BASH preferences...
echo "Setting up bashrc preferences file...."
cat <<EOF > "$HOME"/.bashrc
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

# VIM preferences...
cat <<EOF >> "$HOME"/.vimrc
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

# GIT prefs..?
#  - email, editor, color etc??

# Matplotlib prefs...?
#   - might be able to source a file from a gist online?
#   e.g. https://gist.github.com/huyng/816622



echo "DONE setting up a dvm-dos-tem environment. You should be ready to go!"
