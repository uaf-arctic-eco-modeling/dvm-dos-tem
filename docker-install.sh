#!/bin/bash 
# This script will install the docker. 
# Note: The installation could take a while, please be patient.

docker build --target cpp-dev --tag cpp-dev:0.0.1 .
docker build --target dvmdostem-build --tag dvmdostem-build:0.0.1 .
docker build --target dvmdostem-run --tag dvmdostem-run:0.0.1 .
docker build --tag dvmdostem-mapping-support:0.0.1 -f Dockerfile-mapping-support .
