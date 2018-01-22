#!/bin/bash -l

# Job name, for clarity
#SBATCH --job-name="tbc-next"

# Reservation
#SBATCH --reservation=snap_8 

# Partition specification
#SBATCH -p main

# Number of MPI tasks
#SBATCH -n 128

echo $SBATCH_RESERVATION
echo $SLURM_JOB_NODELIST

# Load up my custom paths stuff
module purge
module load jsoncpp/1.8.1-foss-2016a netCDF/4.4.0-foss-2016a Boost/1.55.0-foss-2016a-Python-2.7.11
module load netcdf4-python/1.2.2-foss-2016a-Python-2.7.11


echo "Which MPIRUN: $(which mpirun)"
echo "Which ORTE DAEMON: $(which orted)"
echo "== PATH ============================"
echo $PATH | tr ":" "\n"
echo "== LD_LIBRARY_PATH ============================"
echo $LD_LIBRARY_PATH | tr ":" "\n"
echo "==============================================="

mpirun --mca btl self,tcp --mca btl_tcp_if_include eth2 --mca oob_tcp_if_include eth2 -n 128 ./dvmdostem -l disabled --max-output-volume 25GB -p 100 -e 1000 -s 250 -t 109 -n 91 







