#!/usr/bin/env python

# T. Carman, H. Genet
# Feb, March 2018

import errno            # nice errors
import os               # mkdir, etc
import shutil           # for copying files, removing dirs
import json             # for parsing the config file
import re               # for stripping comments from json files.
import textwrap         # for nicely formatting the inline slurm script
import subprocess       # for calling squeue
import numpy as np      # for generating numeric data
import netCDF4 as nc    # for handling netcdf files

# This script is used to split a dvmdostem run into "sub domains" that can be
# run individually (submitted to the queue manager) and then merged together
# at the end. In this case, the "full domain" is NOT the entire IEM domain, but
# is simply the full area that you are trying to run, i.e. a 10x10 region, or
# a 50x50 region.

# 1) Log on to atlas, cd into your dvmdostem directory.
#
# 2) Checkout desired git version, setup environment.
#
# 3) Compile (make).
#
# 4) Setup your run as though you were going to run serially (single 
#    processor). Configure as necessary the following things:
#      - paths in the config file to the input data and full-domain run mask
#      - adjust the output_spec.csv to your needs
#      - turn outputs on/off for various run-stages (eq, sp, etc)
#      - path to output data is not important - it will be overwritten
#
# 5) Figure out how many cells you want per batch, and set the constant below.
#
# 6) Run this script.
#
# This script will split your run into however many batches are necessary to
# run all the cells and keep the max cells per batch in line with the constant
# you set below. The script will setup two directory hierarchies: one for the 
# outputs of the individual batch runs and one for the "staging" area for each
# batch run. The staging area allows each run to have a different config file
# and different run mask (which is what actually controls which cells are 
# in which batch. Then the script will submit a job to slurm for each batch.
# 
# To process the outputs, use the "batch_merge.sh" script.


# USER SHOULD SET THIS VALUE
IDEAL_CELLS_PER_BATCH = 25 


# Look in the config file to figure out where the full-domain runmask is.
with open("config/config.js", 'r') as f:
    input_str = f.read()
j = json.loads(re.sub('//.*\n','\n', input_str))
BASE_RUNMASK = j['IO']['runmask_file']
BASE_OUTDIR = j['IO']['output_dir']

# Figure out how many batches are necessary to complete the full run.
# This is somewhat restricted by how cells are assigned to processes.
with nc.Dataset(BASE_RUNMASK, 'r') as runmask:
  TOTAL_CELLS_TO_RUN = np.count_nonzero(runmask.variables['run'])  
  print "Total cells to run: {}".format(TOTAL_CELLS_TO_RUN)
  runmasklist = runmask.variables["run"][:,:].flatten()
  runmaskreversed = runmasklist[::-1]
  last_cell_index = len(runmaskreversed) - np.argmax(runmaskreversed) - 1
  # Padded due to the fact that this allows for discontiguous runs
  #  while accounting for the fact that cell assignment is very 
  #  rigid in the model
  padded_cell_count = last_cell_index + 1

nbatches = padded_cell_count / IDEAL_CELLS_PER_BATCH
# If there are extra cells, or fewer cells than IDEAL_CELLS_PER_BATCH
if (padded_cell_count % IDEAL_CELLS_PER_BATCH != 0):
  print "Adding another batch to pick up stragglers!"
  nbatches += 1
   
print "NUMBER OF BATCHES: ", nbatches

# Utility function
def mkdir_p(path):
  '''Provides similar functionality to bash mkdir -p'''
  try:
     os.makedirs(path)
  except OSError as exc:  # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise  

#
# SETUP DIRECTORIES
#
print "Removing any existing staging or batch run directories"
if os.path.isdir(BASE_OUTDIR + '/batch-run'):
  shutil.rmtree(BASE_OUTDIR + '/batch-run')

for batch_id in range(0, nbatches):

  print "Making directories for batch {}".format(batch_id)
  mkdir_p(BASE_OUTDIR + '/batch-run/batch-{}'.format(batch_id))

  work_dir = BASE_OUTDIR + '/batch-run/'
    
  print "Copy run mask, config file, etc for batch {}".format(batch_id)
  shutil.copy(BASE_RUNMASK, work_dir + '/batch-{}/'.format(batch_id))
  shutil.copy('config/config.js', work_dir + '/batch-{}/'.format(batch_id))
  
  print "Reset the run mask for batch {}".format(batch_id)
  with nc.Dataset(work_dir + '/batch-{}/run-mask.nc'.format(batch_id), 'a') as runmask:
    runmask.variables['run'][:] = np.zeros(runmask.variables['run'].shape)
  
#
# BUILD BATCH SPECIFIC RUN-MASKS
#
with nc.Dataset(BASE_RUNMASK, 'r') as runmask:
  nz_ycoords = runmask.variables['run'][:].nonzero()[0]
  nz_xcoords = runmask.variables['run'][:].nonzero()[1]

# For every cell that is turned on in the main run-mask, we assign this cell
# to a batch to be run, and turn on the corresponding cell in the batch's
# run mask.
print "Turning on pixels in each batch's run mask..."
batch = 0
cells_in_sublist = 0
coord_list = zip(nz_ycoords, nz_xcoords)
for i, cell in enumerate(coord_list):

  with nc.Dataset(work_dir + "/batch-{}/run-mask.nc".format(batch), 'a') as grp_runmask:
    grp_runmask.variables['run'][cell] = True
    cells_in_sublist += 1

  if (cells_in_sublist == IDEAL_CELLS_PER_BATCH) or (i == len(coord_list)-1):
    print "Group {} will run {} cells...".format(batch, cells_in_sublist)
    batch += 1
    cells_in_sublist = 0 


#
# SUMMARIZE
#
number_batches = batch
assert (nbatches == number_batches), "PROBLEM: Something is wrong with the batch numbers: {} vs {}".format(nbatches, number_batches)
print "Split cells into {} batches...".format(number_batches)

#
# MODIFY THE CONFIG FILE FOR EACH BATCH
#
print "Modifying each batch's config file; changing path to run mask and to output directory..."
for batch_num in range(0, number_batches):

  with open(work_dir + '/batch-{}/config.js'.format(batch_num), 'r') as f:
    input_string = f.read()
  
  j = json.loads(re.sub('//.*\n','\n', input_string)) # Strip comments from json file
  j['IO']['runmask_file'] = work_dir + '/batch-{}/run-mask.nc'.format(batch_num)
  j['IO']['output_dir'] = work_dir + '/batch-{}/output/'.format(batch_num)
  
  output_str = json.dumps(j, indent=2, sort_keys=True)

  with open(work_dir + '/batch-{}/config.js'.format(batch_num), 'w') as f:
    f.write(output_str)

#
# SUBMIT SBATCH SCRIPT FOR EACH BATCH
#
for batch in range(0, number_batches):

  with nc.Dataset(work_dir + "/batch-{}/run-mask.nc".format(batch), 'r') as runmask:
    cells_in_batch = np.count_nonzero(runmask.variables['run'])

  assert (cells_in_batch > 0), "PROBLEM! Groups with no cells activated to run!"
  
  slurm_runner_scriptlet = textwrap.dedent('''\
  #!/bin/bash -l

  #SBATCH --mail-user=rarutter@alaska.edu
  #SBATCH --mail-type=FAIL

  # Job name, for clarity
  #SBATCH --job-name="ddt-batch-{0}"

  # Time limit
  #SBATCH --time=2:00:00

  # Partition specification
  #SBATCH -p t1standard 

  # Number of MPI tasks
  #SBATCH -n {1}

  echo $SLURM_JOB_NODELIST

  ulimit -s unlimited
  ulimit -l unlimited

  # Load up my custom paths stuff
  . /etc/profile.d/modules.sh
  module purge
  module load slurm
  source ~/dvm-dos-tem/env-setup-scripts/setup-env-for-chinook.sh

  mpirun ./dvmdostem -f {2}/batch-{0}/config.js -l disabled --max-output-volume=-1 -p 100 -e 1000 -s 250 -t 115 -n 85 

  '''.format(batch, cells_in_batch, work_dir))
  print "Writing sbatch script for batch {}".format(batch)
  with open(work_dir + "/batch-{}/slurm_runner.sh".format(batch), 'w') as f:
    f.write(slurm_runner_scriptlet)
  
#  print "STUB::: Submitting sbatch script to squeue for batch {}".format(batch)
#  sbatch_output = subprocess.check_output(["sbatch", "staging-batch-run/batch-{}/slurm_runner.sh".format(batch)])
#  print sbatch_output


