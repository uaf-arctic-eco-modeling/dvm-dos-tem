FROM dvmdostem-build:0.1.0 as build

LABEL stage="intermediate"

WORKDIR /src

RUN git clone https://github.com/ua-snap/dvm-dos-tem.git

ENV SITE_SPECIFIC_INCLUDES="-I/usr/include/jsoncpp"
ENV SITE_SPECIFIC_LIBS="-I/usr/lib"
WORKDIR /src/dvm-dos-tem

RUN git checkout master && make clean && make
CMD ["./dvmdostem --help"]

