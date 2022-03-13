#!/bin/bash

#This script requires nccmp, found at http://nccmp.sourceforge.net/

input_dirA=$1
input_dirB=$2

for file in $input_dirA/*.nc; do

  filename=${file##*/}
  echo $filename

  nccmp -d "${input_dirA}/${filename}" "${input_dirB}/${filename}"

done #for each file


