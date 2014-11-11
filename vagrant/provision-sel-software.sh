#!/usr/bin/env bash

#echo "Cloning github repos..."
#for githubrepo in "ua-snap/dvm-dos-tem" "tobeycarman/ddtv"
#do
#  user=`echo $githubrepo | cut -f1 -d/`
#  repo=`echo $githubrepo | cut -f2 -d/`
#
#  echo "Checking for $repo....."
#  if [ -d /home/vagrant/$repo ]
#  then
#    echo "Note: directory for $repo seems to exist - but may not be up-to-date.";
#  else
#    echo "Cloning repo $repo from github user $user..."
#    git clone git@github.com:$user/$repo.git /home/vagrant/$repo;
#  fi
#done


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






