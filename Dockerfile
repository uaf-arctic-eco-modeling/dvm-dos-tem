# Dockerfile for dvmdostem project.
#
# This Dockerfile specifies several images that are useful for the 
# dvmdostem project. The primary reason for multiple images is to allow for  
# a development environment and a stripped down run time environemnt.
# A container started from one of the development images will have all 
# the development tools available, while a container started from a run
# focused image should be smaller and leaner but won't necessarily have 
# development tooling.
#
# For more info see the docker_build_wrapper.sh script.
#
# Uses a multi-stage build. If you want to only create one of the
# intermediate stages, then run something like:
#
#    $ docker build --target cpp-dev --tag cpp-dev:$(git describe) .
#
#    NOTE trailing '.' specifying build context as current directory!
#
# If you simply docker build the entire file, or one of the 
# later stages you will end up with several un-named, un-tagged 
# images from the preceeding stages (i.e. <none>:<none> in the output 
# docker image ls). For this reason, it might
# be nicer to build and tag each stage successively,
#

ARG GIT_VERSION=latest

# IMAGE FOR GENERAL C++ DEVELOPMENT.
# General development tools, compilers, text editors, etc
FROM ubuntu:focal as cpp-dev
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y --fix-missing && apt-get install -y \
    build-essential \
    doxygen \
    gdb \
    gdbserver \
    git \
    vim \
  && rm -rf /var/lib/apt/lists/*


# IMAGE FOR GENERAL DVMDOSTEM DEVELOPMENT.
# More specific build stuff for compiling dvmdostem and running 
# python scripts
FROM cpp-dev:$GIT_VERSION as dvmdostem-dev
# dvmdostem dependencies
RUN apt-get update -y --fix-missing && apt-get install -y \
    libboost-all-dev \
    libjsoncpp-dev \
    liblapacke \
    liblapacke-dev \
    libnetcdf-dev \
    libreadline-dev \
  && rm -rf /var/lib/apt/lists/*

# Various command line netcdf tools
RUN apt-get update -y --fix-missing && apt-get install -y \
    nco \
    netcdf-bin \
  && rm -rf /var/lib/apt/lists/*

# Make a developer user so as not to always be root
RUN useradd -ms /bin/bash develop
RUN echo "develop   ALL=(ALL:ALL) ALL" >> /etc/sudoers
USER develop

# Pyenv dependencies for building full Python with all extensions.
USER root
RUN apt-get update --fix-missing -y && apt-get install -y \ 
    build-essential \
    curl \
    git \
    libffi-dev \
    libssl-dev \
    libbz2-dev \
    liblzma-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libreadline-dev \
    libsqlite3-dev \
    llvm \
    python-openssl \
    tk-dev \
    wget \
    xz-utils \
    zlib1g-dev \
  && rm -rf /var/lib/apt/lists/*

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
# well across macOS, Ubuntu, CentOS, etc. 
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
COPY requirements_general_dev.txt .
RUN pip install -r requirements_general_dev.txt

COPY --chown=develop:develop special_configurations/jupyter_notebook_config.py /home/develop/.jupyter/jupyter_notebook_config.py

ENV SITE_SPECIFIC_INCLUDES="-I/usr/include/jsoncpp"
ENV SITE_SPECIFIC_LIBS="-I/usr/lib"
ENV PATH="/work:$PATH"
ENV PATH="/work/scripts:$PATH"
WORKDIR /work
# or use command
#ENTRYPOINT [ "tail", "-f", "/dev/null" ]


# IMAGE FOR BUILDING (COMPILING) DVMDOSTEM.
# This is for a stand-alone container that can be used to compile the
# dvmdostem binary without needing to mount volumes when the container
# is started. The required files are copied directly to the image.
# In the dev image, the source code is not present in the image and must be
# made available to the image (usually by mounting a volume) at the time the 
# container is started from the image.
FROM dvmdostem-dev:${GIT_VERSION} as dvmdostem-build
COPY src/ /work/src
COPY Makefile /work/Makefile
COPY include/ /work/include

COPY scripts/ /work/scripts
COPY calibration/ /work/calibration
COPY parameters/ /work/parameters
COPY config/ /work/config
USER root

# During development, it can be faster to test by copying in the binary
#COPY dvmdostem /work/dvmdostem
RUN make

USER develop
# Use this to keep container going when doing docker compose up
# CMD ["tail -f /dev/null"]


# IMAGE FOR RUNNING (NOT DEVELOPING) DVMDOSTEM.
# This is designed to be a production image, lightweight in size, and with 
# minimal tools. Only the dvmdostem and required shared libraries are installed
# on top of a bare ubuntu installation. No tools (git, make, etc) are included.
# No source code. Just the compiled dvmdostem application.
#
# Use the dvmdostem-build image to create a container that can compile
# dvmdostem, which is then copied into this image
# 
# A container run from this images will need to have data supplied (i.e. one or 
# more mounted volumes) in order to run dvmdostem.
#
FROM ubuntu:focal as dvmdostem-run

WORKDIR /work

COPY --from=dvmdostem-build /work/dvmdostem ./

COPY --from=dvmdostem-build /work/scripts ./scripts
COPY --from=dvmdostem-build /work/calibration ./calibration
COPY --from=dvmdostem-build /work/parameters ./parameters
COPY --from=dvmdostem-build /work/config ./config

# This seems to gets the whole python install, although I expect at some
# point when an extension is needed, will have to find that shared lib and 
# copy it in... 
#  ~ 800 MB
COPY --from=dvmdostem-build /home/develop/.pyenv /home/develop/.pyenv

# Discovered by using ldd on compiled binary in testing environment
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libboost_filesystem.so.1.71.0  /lib/x86_64-linux-gnu/libboost_filesystem.so.1.71.0
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libboost_program_options.so.1.71.0 /lib/x86_64-linux-gnu/libboost_program_options.so.1.71.0
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libboost_thread.so.1.71.0 /lib/x86_64-linux-gnu/libboost_thread.so.1.71.0
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libboost_log.so.1.71.0 /lib/x86_64-linux-gnu/libboost_log.so.1.71.0
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libjsoncpp.so.1 /lib/x86_64-linux-gnu/libjsoncpp.so.1
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/liblapacke.so.3 /lib/x86_64-linux-gnu/liblapacke.so.3
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libtmglib.so.3 /lib/x86_64-linux-gnu/libtmglib.so.3
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libhdf5_serial_hl.so.100 /lib/x86_64-linux-gnu/libhdf5_serial_hl.so.100
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libhdf5_serial.so.103 /lib/x86_64-linux-gnu/libhdf5_serial.so.103
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libcurl-gnutls.so.4 /lib/x86_64-linux-gnu/libcurl-gnutls.so.4
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libgfortran.so.5 /lib/x86_64-linux-gnu/libgfortran.so.5
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libnetcdf.so.15 /lib/x86_64-linux-gnu/libnetcdf.so.15
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libreadline.so.8 /lib/x86_64-linux-gnu/libreadline.so.8
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libblas.so.3 /lib/x86_64-linux-gnu/libblas.so.3
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/liblapack.so.3 /lib/x86_64-linux-gnu/liblapack.so.3
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libblas.so.3 /lib/x86_64-linux-gnu/libblas.so.3
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/liblapack.so.3 /lib/x86_64-linux-gnu/liblapack.so.3
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libsz.so.2 /lib/x86_64-linux-gnu/libsz.so.2
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libnghttp2.so.14 /lib/x86_64-linux-gnu/libnghttp2.so.14
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/librtmp.so.1 /lib/x86_64-linux-gnu/librtmp.so.1
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libssh.so.4 /lib/x86_64-linux-gnu/libssh.so.4
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libpsl.so.5 /lib/x86_64-linux-gnu/libpsl.so.5
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libgssapi_krb5.so.2 /lib/x86_64-linux-gnu/libgssapi_krb5.so.2
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libldap_r-2.4.so.2 libldap_r-2./lib/x86_64-linux-gnu/4.so.2
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/liblber-2.4.so.2 liblber-2./lib/x86_64-linux-gnu/4.so.2
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libbrotlidec.so.1 /lib/x86_64-linux-gnu/libbrotlidec.so.1
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libquadmath.so.0 /lib/x86_64-linux-gnu/libquadmath.so.0
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libldap_r-2.4.so.2 /lib/x86_64-linux-gnu/libldap_r-2.4.so.2
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/liblber-2.4.so.2 /lib/x86_64-linux-gnu/liblber-2.4.so.2
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libaec.so.0 /lib/x86_64-linux-gnu/libaec.so.0
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libcrypto.so.1.1 /lib/x86_64-linux-gnu/libcrypto.so.1.1
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libkrb5.so.3 /lib/x86_64-linux-gnu/libkrb5.so.3
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libk5crypto.so.3 /lib/x86_64-linux-gnu/libk5crypto.so.3
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libkrb5support.so.0 /lib/x86_64-linux-gnu/libkrb5support.so.0
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libbrotlicommon.so.1 /lib/x86_64-linux-gnu/libbrotlicommon.so.1
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libsasl2.so.2 /lib/x86_64-linux-gnu/libsasl2.so.2
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libgssapi.so.3 /lib/x86_64-linux-gnu/libgssapi.so.3
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libkeyutils.so.1 /lib/x86_64-linux-gnu/libkeyutils.so.1
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libheimntlm.so.0 /lib/x86_64-linux-gnu/libheimntlm.so.0
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libkrb5.so.26 /lib/x86_64-linux-gnu/libkrb5.so.26
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libasn1.so.8 /lib/x86_64-linux-gnu/libasn1.so.8
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libhcrypto.so.4 /lib/x86_64-linux-gnu/libhcrypto.so.4
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libroken.so.18 /lib/x86_64-linux-gnu/libroken.so.18
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libwind.so.0 /lib/x86_64-linux-gnu/libwind.so.0
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libwind.so.0 /lib/x86_64-linux-gnu/libwind.so.0
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libheimbase.so.1 /lib/x86_64-linux-gnu/libheimbase.so.1
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libhx509.so.5 /lib/x86_64-linux-gnu/libhx509.so.5
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libsqlite3.so.0 /lib/x86_64-linux-gnu/libsqlite3.so.0
COPY --from=dvmdostem-dev /lib/x86_64-linux-gnu/libheimbase.so.1 /lib/x86_64-linux-gnu/libheimbase.so.1

# Make a developer user so as not to always be root
RUN useradd -ms /bin/bash develop
RUN echo "develop   ALL=(ALL:ALL) ALL" >> /etc/sudoers
USER develop
ENV HOME=/home/develop
ENV PYENV_ROOT=$HOME/.pyenv
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# Set a few environemnt variables for ease of use...
ENV PATH="/work:$PATH"
ENV PATH="/work/scripts:$PATH"



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

