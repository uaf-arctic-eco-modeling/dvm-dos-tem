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
# Add github's key to knownhosts
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


#
# Setup the input library mirror
#

# This step is hard to automate securely, so here is the general idea:
#
#     # Make sure the output location exists
#     mkdir -p /data/mirrors/atlas/dvmdostem-input-catalog/
#    
#     # Change into the dvmdostem repo, and run the updating script.
#     # If you don't have ssh keys or ssh key agent forwarding setup
#     # Then this will prompt you for your atlas username and password.
#     cd $HOME/dvm-dos-tem
#     DST="/home/vagrant/data/mirrors/atlas/dvmdostem-input-catalog" ./scripts/update-mirror.sh


#
# Setup various preference files (dotfiles)
#

# Ubuntu bashrc file - Not sure how to manage this  automatically, so for now, 
# here are the changes I (tbc) have made manually, to the bashrc file (8/10/18):
#  - increase HISTSIZE, HISTFILESIZE
#  - uncomment line with "force_color_prompt=yes"
#  - add this at the bottom: 
#    export SITE_SPECIFIC_INCLUDES=-I/usr/include/jsoncpp
#  - enable git branch in prompt according to here:
#    https://askubuntu.com/questions/730754/how-do-i-show-the-git-branch-with-colours-in-bash-prompt
#    Place this in the .bashrc:
#        parse_git_branch() {
#          git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/(\1)/'
#        }
#        if [ "$color_prompt" = yes ]; then
#          PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[01;31m\] $(parse_git_branch)\[\033[00m\]\$ '
#        else
#          PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w$(parse_git_branch)\$ '
#        fi
#        # THE SIX LINES BELOW are the default prompt and the unset (which were in the original .bashrc)
#        #if [ "$color_prompt" = yes ]; then
#        #    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
#        #else
#        #    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
#        #fi
#        #unset color_prompt force_color_prompt

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


echo "DONE setting up a dvm-dos-tem environment. You should be ready to go!"
