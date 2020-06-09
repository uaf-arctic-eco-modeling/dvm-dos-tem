#!/bin/bash -l

# This script is for records only, and not currently used.

#SBATCH --mail-user=rarutter@alaska.edu
#SBATCH --mail-type=BEGIN
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL

# Job name, for clarity
#SBATCH --job-name="ddt50squarePoC"

# Time limit (since we're requesting a lot of resources)
#SBATCH --time=12:00:00

# Partition specification
#SBATCH -p t2standard 

# Number of MPI tasks
#SBATCH -n 1250 

#    SBATCH --test-only

ulimit -s unlimited
ulimit -l unlimited

. /etc/profile.d/modules.sh
module purge
module load slurm
source env-setup-scripts/setup-env-for-chinook.sh

echo $SLURM_JOB_NODELIST

# srun -l /bin/hostname | sort -n | awk '{print $2}' > ./nodes.$SLURM_JOB_ID

# mpirun -n 1 -machinefile ./nodes.$SLURM_JOB_ID ./dvmdostem -l disabled -p 100 -e 1000 -s 250 -t 109 -n 91 
mpirun -n 1250 ./dvmdostem -l disabled -p 100 -e 1000 -s 250 -t 109 -n 91 
