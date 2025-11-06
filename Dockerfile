# Dockerfile for dvmdostem project.
#
# This file contains specifications for images that are useful for the dvmdostem
# project. The images described in this file are:
#
#  * cpp-dev                 general purpose C, C++ compilers, libraries, etc
#  * dvmdostem-dev           libraries, tools for developing dvmdostem
#  * dvmdostem-build         a standalone compile environment for dvmdostem
#  * dvmdostem-run           a standalone run-time environemnt for dvmdostem
#  * dvmdostem-autocal       built on top of the dev image, includes julia and
#                            MADS
#
# There is an additional image for the project, dvmdostem-mapping-support, which
# has its own Dockerfile.
#
# The intention is that most (all?) development and testing work will be done in
# containers based on the -dev image. The -build and -run images are intended
# for deployment of dvmdostem on a cloud system or within another system, such
# as PEcAn.
#
# This Dockerfile uses a multi-stage build. If you want to only create one of
# the intermediate stages, then run something like:
#
#    $ docker build --target cpp-dev --tag cpp-dev:$(git describe) .
#
#    NOTE: trailing '.' specifying build context as current directory!
#
# If you simply docker build the entire file, or one of the later stages you
# will end up with several un-named, un-tagged images from the preceeding stages
# (i.e. <none>:<none> in the output from docker image ls). For this reason, it
# might be nicer to build and tag each stage successively.
#
# See docker-build-wrapper.sh for more info and ideas about building and and
# tagging images.
#

# This is used for tagging images. In most cases, this value will be overridden
# by passing a --build-arg when running docker build to create your images. See
# docker-build-wrapper.sh for examples of this pattern in use.
# These must be defined here with default values and then in each stage
# of the build you must again declare the ARG lines...
ARG GIT_VERSION=latest
ARG UNAME=develop
ARG UID=1000
ARG GID=1000

# === IMAGE FOR GENERAL C++ DEVELOPMENT =======================================
# General development tools, compilers, text editors, etc
FROM ubuntu:jammy AS cpp-dev
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y --fix-missing && apt-get install -y \
    build-essential \
    doxygen \
    graphviz \
    gdb \
    gdbserver \
    git \
    vim \
  && rm -rf /var/lib/apt/lists/*


# === IMAGE FOR GENERAL DVMDOSTEM DEVELOPMENT =================================
# More specific build stuff for compiling dvmdostem and running the project's
# associated python scripts. 
FROM cpp-dev:$GIT_VERSION AS dvmdostem-dev
ARG UNAME
ARG UID
ARG GID

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

# Make a developer user so as not to always be root.
# In order for the resulting container to be able to mount host directories 
# as volumes and have read/write access, we must be sure that the new user 
# here has the same UID and GID as the user on the machine hosting the
# container. Here we have default values for the UNAME, UID and GID, but
# if you need to you can override them by passing --build-arg to the docker
# build command.
RUN groupadd -g $GID -o $UNAME
RUN useradd -m -u$UID -g$GID -s /bin/bash $UNAME
RUN echo "$UNAME   ALL=(ALL:ALL) ALL" >> /etc/sudoers
USER $UNAME

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
    python3-openssl \
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
USER $UNAME
ENV HOME=/home/$UNAME
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

COPY --chown=$UNAME:$UNAME special_configurations/jupyter_notebook_config.py /home/$UNAME/.jupyter/jupyter_notebook_config.py

ENV SITE_SPECIFIC_INCLUDES="-I/usr/include/jsoncpp"
ENV SITE_SPECIFIC_LIBS="-I/usr/lib"
ENV PATH="/work:$PATH"
ENV PATH="/work/scripts:$PATH"
ENV PATH="/work/scripts/util:$PATH"
WORKDIR /work
# or use command
#ENTRYPOINT [ "tail", "-f", "/dev/null" ]

# ==== IMAGE FOR RUNNING JULIA/MADS AUTO CALIBRATION STUFF ====================
# Basically the dev image with Julia and MADS installed. Julia and MADS add
# significantly to the build time and size, so they are split out to a separate
# image here.
FROM dvmdostem-dev:${GIT_VERSION} AS dvmdostem-autocal
ARG UNAME
ARG UID
ARG GID

# Install julia as root...
USER root
RUN mkdir -p /usr/local/bin \
    && mkdir -p /opt \
    && wget https://julialang-s3.julialang.org/bin/linux/x64/1.7/julia-1.7.3-linux-x86_64.tar.gz \
    && tar -xzf julia-1.7.3-linux-x86_64.tar.gz \
    && cp -r julia-1.7.3 /opt/ \
    && ln -s /opt/julia-1.7.3/bin/julia /usr/local/bin/julia

# Then install julia packages on a per-user basis...
USER $UNAME
RUN echo 'using Pkg; Pkg.add(name="Mads", version="1.3.10")' | julia
RUN echo 'using Pkg; Pkg.add("PyCall")' | julia
RUN echo 'using Pkg; Pkg.add("DataFrames")' | julia
RUN echo 'using Pkg; Pkg.add("DataStructures")' | julia
RUN echo 'using Pkg; Pkg.add("CSV")' | julia
RUN echo 'using Pkg; Pkg.add("YAML")' | julia

ENV PYTHONPATH="/work/scripts:/work/mads_calibration"


# === IMAGE FOR BUILDING (COMPILING) DVMDOSTEM ================================
# A stand-alone container that can be used to compile the dvmdostem binary
# without needing to mount volumes when the container is started. Here the
# required source files are copied directly to the image. This is in constrast
# to the dev image, where there is no source code present in the image instead it
# must be provided by mounting a volume at container run-time.
FROM dvmdostem-dev:${GIT_VERSION} AS dvmdostem-build
ARG UNAME
ARG UID
ARG GID

COPY src/ /work/src
COPY Makefile /work/Makefile
COPY include/ /work/include

# Needed for running git describe w/in the Makefile. Without the config setting
# git gives an error about trusted directories. Possible security concern?
# There is probably a better way to handle this situation. Maybe pass the git
# version to the Makefile as an argument?
COPY .git /work/.git
RUN git config --global --add safe.directory /work

COPY scripts/ /work/scripts
COPY calibration/ /work/calibration
COPY parameters/ /work/parameters
COPY config/ /work/config
USER root

# During development, it can be faster to test by copying in the binary rather
# than waiting for it to build each time
#COPY dvmdostem /work/dvmdostem
RUN make

# Not sure how the USERNAME should be used with this image
# So setting to the passed in ARG value like the other images, though
# this might not be important for the usecases we have...
USER $UNAME
# Use this to keep container going when doing docker compose up
# CMD ["tail -f /dev/null"]


# === IMAGE FOR RUNNING (NOT DEVELOPING) DVMDOSTEM ============================
# This is designed to be a production image: lightweight in size, and with
# minimal tools. Only the dvmdostem binary and required shared libraries, and
# python install are installed on top of a bare ubuntu installation. No tools
# (git, make, etc) are included. No source code. Just the compiled dvmdostem
# application and supporting libriaries are included.
#
# Note that excluding python could significantly reduce the image size!
#
# A container run from this images will need to have data supplied (i.e. one or
# more mounted volumes) in order to run dvmdostem.
#
FROM ubuntu:jammy AS dvmdostem-run
ARG UNAME
ARG UID
ARG GID

WORKDIR /work

COPY --from=dvmdostem-build /work/dvmdostem ./

COPY --from=dvmdostem-build /work/scripts ./scripts
COPY --from=dvmdostem-build /work/calibration ./calibration
COPY --from=dvmdostem-build /work/parameters ./parameters
COPY --from=dvmdostem-build /work/config ./config

# This seems to gets the whole python install, although I expect at some
# point when an extension is needed, will have to find that shared lib and 
# copy it in... 
#  ~800MB
RUN echo ${UNAME}
# There is some kind of bug or oddity with how the file gets copied.
# Doing it like below with the "as" construct allows us to set the 
# correct username in the copy step...
FROM ${UNAME} AS uname
COPY --from=dvmdostem-build /home/uname/.pyenv /home/uname/.pyenv

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
# In order for the resulting container to be able to mount host directories 
# as volumes and have read/write access, we must be sure that the new user 
# here has the same UID and GID as the user on the machine hosting the
# container. Here we have default values for the UNAME, UID and GID, but
# if you need to you can override them by passing --build-arg to the docker
# build command.
RUN groupadd -g $GID -o $UNAME
RUN useradd -m -u$UID -g$GID -s /bin/bash $UNAME
RUN echo "$UNAME   ALL=(ALL:ALL) ALL" >> /etc/sudoers
USER $UNAME

ENV HOME=/home/$UNAME
ENV PYENV_ROOT=$HOME/.pyenv
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# Set a few environemnt variables for ease of use...
ENV PATH="/work:$PATH"
ENV PATH="/work/scripts:$PATH"
ENV PATH="/work/scripts/util:$PATH"


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

