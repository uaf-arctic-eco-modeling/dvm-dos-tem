#!/bin/bash 

# This script will build the docker images for the dvmdostem project.
# Note: Some steps may take a while, please be patient.

# Note: You may try --no-cache with the docker build commands if they
# fail with various errors reccomending --fix-missing errors.

# Here is a handy formulation for finding and deleting old docker images, 
# adjust the grep commands as necessary: 
#
#     $ docker image ls | grep dvmdostem \
#       | grep v0.5.6-87-g | awk '{print $1,$2}' | sed -e 's/ /:/g' 
#
# This can then be wrapped in a for loop that calls docker image rm to cleanup.


function usage () {
  echo "usage: "
  echo "  $ ./docker-build-wrapper.sh [ help | all | cpp-dev | dev | build | run | autocal | map ]"
  echo ""
  echo "  Wrapper program around docker build that will assist in consistently"
  echo "  building and tagging images for the dvmdostem project."
  echo ""  
  echo "  Some of the images take a long time to build and require many GB of"
  echo "  storage space so you can select specific images to build here."
  echo "  Note that the images are built on top of eachother, so you may have" 
  echo "  to explicitly build some of the underlying images before some of the" 
  echo "  upper level images."
  echo ""  
  echo "  For details on each image, read the comments in this script file."
  echo ""
  echo "  --help, help            Print this message."
  echo "  --all, all              Build all the images."
  echo "  --cpp-dev, cpp-dev      Build the cpp-dev image."
  echo "  --dev, dev              Build the dev image."
  echo "  --build, build          Build the build image."
  echo "  --run, run              Build the run image."
  echo "  --autocal, autocal      Build the autocal image."
  echo "  --map, map              Build the mapping support image."
  
  echo "  "

  if [[ "$#" -gt 0 ]]
  then
    echo "Error: $1"
  fi
  echo ""
}

# Sets various environment variables that are passed into the actual docker
# build command.
function setup() {

  # Use --tags so that lightweight tags are found. Useful for local tagging
  # as well as making sure that images built during the release process are 
  # appropriately tagged.
  GIT_VERSION=$(git describe --tags)

  # This helps with sharing host folders to container. It is important that the
  # user in the container has the same uid/gid as the host user so that both
  # users can have read and write permissions on the files. In many circumstances
  # this build wrapper script will be run with sudo, so we have to find the id 
  # of the login user, not the sudo user, to pass into the guest.
  export HOSTUID=$(id -u $(logname))
  export HOSTGID=$(id -g $(logname))

}

function build_all() {
  build_cpp_dev
  build_dev
  build_build
  build_run
  build_autocal
  build_map
}

function build_cpp_dev() {
  # IMAGE FOR GENERAL C++ DEVELOPMENT
  # Makes a general development image with various dev tools installed:
  # e.g. compiler, make, gdb, etc
  echo "Building cpp-dev image for $GIT_VERSION using hostuid=$HOSTUID and hostgid=$HOSTGID"
  docker build --build-arg GIT_VERSION=$GIT_VERSION \
               --build-arg UID=$HOSTUID --build-arg GID=$HOSTGID \
               --target cpp-dev --tag cpp-dev:$GIT_VERSION .
}

function build_dev() {
  # IMAGE FOR GENERAL DVMDOSTEM DEVELOPMENT 
  # Makes the specific dvmdostem development image with dvmdostem specific
  # dependencies installed, e.g: boost, netcdf, jsoncpp, etc. Intention is that
  # your host machine's repo will be mounted as a volume at /work, and you can
  # use this container as a compile time and run time environment.
  echo "Building dev image for $GIT_VERSION using hostuid=$HOSTUID and hostgid=$HOSTGID"
  docker build --build-arg GIT_VERSION=$GIT_VERSION \
               --build-arg UID=$HOSTUID --build-arg GID=$HOSTGID \
               --target dvmdostem-dev --tag dvmdostem-dev:$GIT_VERSION .
}

function build_autocal() {
  # IMAGE FOR DVMDOSTEM AUTO-CALIBRATION WITH MADS
  # This adds the Julia Language and the Mads Package to enable auto-calibration.
  # Otherwise the usage is basically the same as the dev container with the same
  # volume mounts.
  echo "Building autocal image for $GIT_VERSION using hostuid=$HOSTUID and hostgid=$HOSTGID"
  docker build --build-arg GIT_VERSION=$GIT_VERSION \
               --build-arg UID=$HOSTUID --build-arg GID=$HOSTGID \
               --target dvmdostem-autocal --tag dvmdostem-autocal:$GIT_VERSION .
}

function build_build() {
  # IMAGE FOR BUILDING (COMPILING) DVMDOSTEM
  # This is for a stand-alone container that can be used to compile the
  # dvmdostem binary without needing to mount volumes when the container
  # is started. The required files are copied directly to the image.
  # The intention is to use this purely as a compile time environment 
  # used to create the dvmdostem binary so that it can be copied into
  # the lean run image.
  echo "Building build (compile) image for $GIT_VERSION using hostuid=$HOSTUID and hostgid=$HOSTGID"
  docker build --build-arg GIT_VERSION=$GIT_VERSION \
               --build-arg UID=$HOSTUID --build-arg GID=$HOSTGID \
               --target dvmdostem-build --tag dvmdostem-build:$GIT_VERSION .
}

function build_run() {
  # IMAGE FOR SIMPLY RUNNING DMVDOSTEM AND ASSOCIATED SCRIPTS
  # A lean images with only the bare minimum stuff to run dvmdostem
  # Does NOT have development tools, compilers, editors, etc
  echo "Building run image for $GIT_VERSION using hostuid=$HOSTUID and hostgid=$HOSTGID"
  docker build --build-arg GIT_VERSION=$GIT_VERSION \
               --build-arg UID=$HOSTUID --build-arg GID=$HOSTGID \
               --target dvmdostem-run --tag dvmdostem-run:$GIT_VERSION .
}

function build_map() {
  # IMAGE FOR WORKING WITH MAPPING TOOLS, SPECIFICALLY GDAL
  # The bastard step child needed to run various gdal tools
  # THis one is different becuase it requires an entirely separate Dockerfile
  # because the base image is different.
  echo "Building mapping image for $GIT_VERSION using hostuid=$HOSTUID and hostgid=$HOSTGID"
  docker build --build-arg GIT_VERSION=$GIT_VERSION \
               --build-arg UID=$HOSTUID --build-arg GID=$HOSTGID \
               --tag dvmdostem-mapping-support:$GIT_VERSION \
               -f Dockerfile-mapping-support .
}

# First pass over arguments, exit if user asks for help
for i in $@;
do
  case $i in
    -h | --help | help )
        usage "None! :-) "
        exit
        ;;
    *)
      echo "" > /dev/null
      ;;
  esac
done

# Second pass, do all the other stuff
while [ "$1" != "" ]; do
  case $1 in
    all | -a | --all )            shift
                                  setup 
                                  build_all
                                  ;;

    cpp-dev | --cpp-dev )         shift
                                  setup
                                  build_cpp_dev
                                  ;;

    dev | --dev )                 shift
                                  setup
                                  build_dev
                                  ;;

    build | --build )             shift
                                  setup
                                  build_build
                                  ;;

    run | --run )                 shift
                                  setup
                                  build_run
                                  ;;

    autocal | --autocal )         shift
                                  setup
                                  build_autocal
                                  ;;

    map | --map )                 shift
                                  setup
                                  build_map
                                  ;;

    * )                           usage "Problem with command line arguments!"
                                  exit 1
  esac
  shift
done



