#!/bin/bash

#parameters: output directory, index of first batch, index of last batch

if [ $# == 0 ]; then
  echo "usage: $0 batchdir firstindex lastindex"
  exit 1
fi

#for index in $(eval echo {$2..$3}); do
  # echo "$index"
  #construct batch directory prefix
#  echo "${1}/batch-run/batch-$index/slurm_runner.sh"
#  sbatch "${1}/batch-run/batch-$index/slurm_runner.sh"
#done

echo "Working on batch directory: $1"

for index in $(eval echo {$2..$3}); do
  #echo "$index"
  while [ $(squeue | grep -c rarutter) -ge 15 ];
  do
    sleep 30
  done
    
#  echo "${1}/batch-run/batch-$index/slurm_runner.sh"
  sbatch "${1}/batch-run/batch-$index/slurm_runner.sh"
done


