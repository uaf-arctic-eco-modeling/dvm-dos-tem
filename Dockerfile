FROM dvmdostem-build:0.1.0 as build

LABEL stage="intermediate"

WORKDIR /src

RUN git clone https://github.com/ua-snap/dvm-dos-tem.git

ENV SITE_SPECIFIC_INCLUDES="-I/usr/include/jsoncpp"
ENV SITE_SPECIFIC_LIBS="-I/usr/lib"
WORKDIR /src/dvm-dos-tem

RUN git checkout master && make clean && make
CMD ["./dvmdostem --help"]

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
