#!/usr/bin/env python

# T. Carman, Nov 2018

# Fix up veg files. Source input map from here:
# /atlas_scratch/ALFRESCO/ALFRESCO_Master_Dataset_v2_1/ALFRESCO_Model_Input_Datasets/IEM_for_TEM_inputs/ancillary/land_cover/v_0_4/iem_vegetation_model_input_v0_4.tif
# has values for CMT 08 that should be CMT07

import sys
import os
import shutil
import datetime
import textwrap
import numpy as np
import netCDF4 as nc

veg_file = sys.argv[1]
veg_file = os.path.abspath(veg_file)

#from IPython import embed; embed()

print "Opening {}".format(veg_file)
with nc.Dataset(veg_file, 'r') as vds:
  original = vds.variables['veg_class'][:]

print "Copying data..."
fixed_version = original.copy()

print "Replacing data..."
fixed_version[fixed_version==8]=7

print "Displaying difference..."
print np.abs(original-fixed_version)

print "Copying original file..."
backup_file_name = os.path.join(os.path.dirname(veg_file), "original-{}".format(os.path.basename(veg_file)))
shutil.copyfile(veg_file, backup_file_name)

print "Writing new data back to original file..."
with nc.Dataset(veg_file, 'a') as vds:
  vds.variables['veg_class'][:] = fixed_version

print "Writing notes file..."
os.path.join(os.path.dirname(veg_file), "notes.txt")
with open(os.path.join(os.path.dirname(veg_file), "notes.txt"), 'a') as f:
  msg_string = textwrap.dedent('''\
  {}
  =====================
  Modified the vegetation file to set all CMT 08 pixels to CMT 07.
  Saved a copy of the original, just in case.
  '''.format(datetime.datetime.now().isoformat()))
  f.write(msg_string)
  
