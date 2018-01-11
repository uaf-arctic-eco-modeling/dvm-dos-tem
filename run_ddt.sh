#!/bin/bash -l

# Job name, for clarity
#SBATCH --job-name="ddtToolikPoC"

# Reservation
#SBATCH --reservation=snap_8 

# Partition specification
#SBATCH -p main

# Number of MPI tasks
#SBATCH -n 200

echo $SBATCH_RESERVATION
echo $SLURM_JOB_NODELIST

mpirun -n 200 ./dvmdostem -l disabled -p 100 -e 1000 -s 250 -t 109 -n 91 
