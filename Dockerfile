# Dockerfile for dvmdostem project.
#
# Uses a multi-stage build. If you want to only create one of the
# intermediate stages, then run something like:
#
#    $ docker build --target cpp-dev --tag cpp-dev:0.0.1 .
#
#    Note trailing '.' specifying build context as current directory!
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

# Various command line netcdf tools
RUN apt-get install -y nco netcdf-bin

# Make a developer user so as not to always be root
RUN useradd -ms /bin/bash develop
RUN echo "develop   ALL=(ALL:ALL) ALL" >> /etc/sudoers
USER develop

# Pyenv dependencies for building full Python with all extensions.
USER root
RUN apt-get update
RUN apt-get install -y --fix-missing build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev python-openssl git


# Bare bones python approach might be to use system provided python, which in 
# ubuntu focal (20.4) means python3 and pip3, or installing python-is-python3
#RUN apt-get install python3-pip
#RUN apt-get install python-is-python3
#RUN pip install matplotlib numpy pandas bokeh netCDF4 commentjson ipython

# For a more robust version managed python system, use Pyenv.
# Pyenv may be overkill - was trying it in order to help with gdal install
# but never got it to work. Decided to use a separate image with gdal support
# but pyenv might be useful for other packages in the future and is a nice
# unified way to package and version manage our tooling that has been working
# well across macOS, Ubunut, CentOS, etc. 
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
RUN pip install jupyter
RUN pip install lhsmdu
COPY --chown=develop:develop special_configurations/jupyter_notebook_config.py /home/develop/.jupyter/jupyter_notebook_config.py

#RUN pip install gdal ## Doesn't work...
#RUN pip install GDAL ## Doesn't work...
# docker build --target dvmdostem-build --tag dvmdostem-build:0.0.1 .

# The final image that we will run as a container.
FROM dvmdostem-build:0.0.1 as dvmdostem-run
WORKDIR /work
ENV SITE_SPECIFIC_INCLUDES="-I/usr/include/jsoncpp"
ENV SITE_SPECIFIC_LIBS="-I/usr/lib"
ENV PATH="/work:$PATH"
ENV PATH="/work/scripts:$PATH"
# docker build --target dvmdostem-run --tag dvmdostem-run:0.0.1 .

# A production ready container...
# At some point we could trim down and selectively copy out only the 
# required shared libraries needed for running dvmdostem...
#FROM dvmdostem-run as dvmdostem-lean



#########
# NOTES #
#########

# Examples of stand alone use. Alternatively it seems you can use 
# docker-compose for a lot of this and avoid having to explcitly specify 
# volumes, etc:
# docker run --rm -it --volume $(pwd):/work dvmdostem-run:0.0.1 bash
# docker run --rm -it --volume $(pwd):/work dvmdostem-run:0.0.1 make
# docker run --rm -it --volume $(pwd):/work dvmdostem-run:0.0.1 /work/dvmdostem --help
#INCATALOG="/Users/tobeycarman/Documents/SEL/dvmdostem-input-catalog"
#docker run -it --rm -p 5006:5006 --volume $(pwd):/work --volume $INCATALOG:/data/dvmdostem-input-catalog dvmdostem-run:0.0.1


# Dockerfile words:
# RUN - is used to install stuff and setup environment
# CMD - only a single CMD per image, default command when starting container, easily overrridden by docker run
# ENTRYPOINT - the CMD is *always* appended to ENTRYPOINT

#Lots of good ideas here:
# https://github.com/cpp-projects-showcase/docker-images/blob/master/ubuntu2004/Dockerfile

