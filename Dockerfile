# Dockerfile for dvmdostem project.
#
# Uses a multi-stage build. If you want to only create one of the
# intermediate stages, then run something like:
#
#    $ docker build --target cpp-dev --tag cpp-dev:0.0.1 .
#
# If you simply docker build the entire file, or one of the 
# later stages you will end up with several un-named, un-tagged 
# images from the preceeding stages (i.e. <none>:<none> in the output 
# docker image ls). For this reason, it might
# be nicer to build and tag each stage successively,
#

# General dev tools compilers, etc
FROM ubuntu:focal as cpp-dev
ENV DEBIAN_FRONTEND=noninteractive
# Might combine these two using &&, somwewhere I read that is better
RUN apt-get update
# general tools and dependencies for development
RUN apt-get install -y build-essential git gdb gdbserver doxygen
# docker build --target cpp-dev --tag cpp-dev:0.0.1 .


# More specific build stuff for compiling dvmdostem and
# running python scripts
FROM cpp-dev:0.0.1 as dvmdostem-build
# dvmdostem dependencies
RUN apt-get install -y libjsoncpp-dev libnetcdf-dev libboost-all-dev libreadline-dev liblapacke liblapacke-dev
# docker build --target dvmdostem-build --tag dvmdostem-build:0.0.1 .

# Make a developer user so as not to always be root
RUN useradd -ms /bin/bash develop
RUN echo "develop   ALL=(ALL:ALL) ALL" >> /etc/sudoers
USER develop

# Pyenv dependencies
USER root
RUN apt-get update
RUN apt-get install -y --fix-missing build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev python-openssl git


# I think this works, if you don't want to use ipython
#RUN pip install matplotlib numpy pandas bokeh netCDF4 commentjson ipython

# Pyenv may be overkill - was trying it in order to help with gdal install
# but never got it to work. Decided to use a separate image with gdal support
USER develop
ENV HOME=/home/develop
RUN git clone https://github.com/pyenv/pyenv.git $HOME/.pyenv
ENV PYENV_ROOT=$HOME/.pyenv
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
RUN git clone https://github.com/pyenv/pyenv-virtualenv.git $(pyenv root)/plugins/pyenv-virtualenv
RUN pyenv install 3.8.6
RUN pyenv global 3.8.6
RUN pyenv rehash
RUN python --version
RUN pip install -U pip pipenv
RUN pip install matplotlib numpy pandas bokeh netCDF4 commentjson
RUN pip install ipython
#RUN pip install gdal ## Doesn't work...
#RUN pip install GDAL
# docker build --target dvmdostem-build --tag dvmdostem-build:0.0.1 .


# The final image that we will run as a container. At some point 
# we could trim this down and selectively copy out only the 
# required shared libraries needed for running.
FROM dvmdostem-build:0.0.1 as dvmdostem-run
WORKDIR /work
ENV SITE_SPECIFIC_INCLUDES="-I/usr/include/jsoncpp"
ENV SITE_SPECIFIC_LIBS="-I/usr/lib"
ENV PATH="/work:$PATH"
# docker build --target dvmdostem-run --tag dvmdostem-run:0.0.1 .


#Lots of good ideas here:
#https://github.com/cpp-projects-showcase/docker-images/blob/master/ubuntu2004/Dockerfile

# docker run --rm -it --volume $(pwd):/work dvmdostem-run:0.0.1 bash
# docker run --rm -it --volume $(pwd):/work dvmdostem-run:0.0.1 make
# docker run --rm -it --volume $(pwd):/work dvmdostem-run:0.0.1 /work/dvmdostem --help
#INCATALOG="/Users/tobeycarman/Documents/SEL/dvmdostem-input-catalog"
#docker run -it --rm -p 5006:5006 --volume $(pwd):/work --volume $INCATALOG:/data/dvmdostem-input-catalog dvmdostem-run:0.0.1

# A helper image that runs

# A production ready container...
#FROM dvmdostem-run as dvmdostem-lean
#



# RUN - is used to install stuff and setup environment
# CMD - only a single CMD per image, default command when starting container, easily overrridden by docker run
# ENTRYPOINT - the CMD is *always* appended to ENTRYPOINT


#RUN git clone https://github.com/ua-snap/dvm-dos-tem.git

#ENV SITE_SPECIFIC_INCLUDES="-I/usr/include/jsoncpp"
#ENV SITE_SPECIFIC_LIBS="-I/usr/lib"
#WORKDIR /src/dvm-dos-tem

#RUN git checkout master && make clean && make
#CMD ["./dvmdostem --help"]

# WORKDIR /src
# COPY src/ ./src
# COPY include ./include
# COPY Makefile ./

# #WORKDIR /src
# COPY .git/ /src/.git
# COPY demo-data ./demo-data
# #WORKDIR /workshop
# RUN ["git", "--work-tree", "/src", "checkout", "master"]
# RUN ["ls"]


# ENV GIT_WORK_TREE=/workshop
# ENV SITE_SPECIFIC_INCLUDES="-I/usr/include/jsoncpp"
# ENV SITE_SPECIFIC_LIBS="-L/usr/local/"
# RUN make clean && make

# CMD ["./dvmdostem --help"]




#FROM ubuntu:focal
#RUN apt-get update && apt-get install -y libjsoncpp-dev libnetcdf-dev libboost-all-dev libreadline-dev liblapacke-dev
# ENV SITE_SPECIFIC_LIBS="-L/tmp"
# WORKDIR /opt/dvm-dos-tem
# RUN echo "am I here???"
# RUN echo ""
# COPY --from=build /src/dvmdostem .
# 
# #RUN ["ls", "../../src"]
# 
# 
# #RUN ["cp", "/src/dvmdostem", "/opt/dvm-dos-tem"]
# #RUN ["cp", "/src/demo-data", "/opt/dvm-dos-tem"]
# 
# CMD ["./dvmdostem"] 
