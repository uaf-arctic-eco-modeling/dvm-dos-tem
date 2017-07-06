#!/usr/bin/env python

# June 2017
# Tobey Carman, 
# Institute of Arctic Biology

import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt

def conform_mask(rm_m, datam):
  pass

def conform_mask_timeseries(rm_m, datam):
  '''
  A pixel that is masked anywhere along the time axis will result in the
  pixel being masked in the returned array.

  Parameters
  ----------
  rm_m : 2D numpy array of booleans, with dimensions (y, x)
    The main run-mask
  datam : 3D array of booleans with  dimensions (time, y, x)
  attempt_gapfill : bool

  Returns
  -------
  new_runmask: 2D numpy array of booleans with dimensions (y, x). 
  '''

  for tidx, m in enumerate(datam): # only over 1st dimension?
    prev = np.copy(rm_m)
    rm_m = ( rm_m | m )
    modcoords = np.nonzero(np.logical_xor(rm_m, prev))
    if len(zip(*modcoords)) > 0:
      print "At timestep {} modify mask at coords: {}".format(tidx, zip(*modcoords))

  # mc = np.nonzero(np.logical_xor(original_rm_m, rm_m).astype(int))
  # print "Summary of modified coords:"
  # for i, c in enumerate(zip(*mc)):
  #   print c

  return rm_m

###########################################################
# First set the run mask based on the veg map
###########################################################
# NOTE: don't really need to open the existing run-mask - could just initialize
#       an array of all ones and then start masking it...
#       rm = np.ma.core.MaskedArray(np.ones((10,10)).astype(int), mask=np.zeros((10,10)))
rm = nc.Dataset('DATA/SouthBarrow_10x10/run-mask.nc', mode='r') 
veg = nc.Dataset("DATA/SouthBarrow_10x10/vegetation.nc")

# Optional: show the distrubution of various veg classes in the map as a 1D histogram:
#plt.hist(veg.variables['veg_class'][:].flatten())

# Get just the masks - we don;t really need the data at this point
vm = np.ma.getmaskarray(np.ma.masked_less(veg.variables['veg_class'][:], 0))
rm_m = np.ma.getmaskarray(rm.variables['run'][:])

rm_m = (rm_m | vm)

# select all the data, mask anything less than zero, return the mask, invert it and make new array
#rm.variables['run'][:] = np.array(~vm.mask, dtype=int) # This sets the run mask...


# This turns the run mask (plain int array) into a masked array that is 
# easier to deal with in comparison to the other masks (masked arrays) we are
# going to create. The trickery is in inverting and type casting the original
# array to create the mask - the mask has the inverse logic of our run-mask
# as a result of the different approaches taken by numpy's masked arrays (True
# indicating, than yes a value should be masked), while for dvmdostem, we are 
# using 1 (True) to indicate "yes the cell should be run".
#rm_m = np.ma.MaskedArray(rm.variables['run'], mask=np.invert(rm.variables['run'][:].astype(bool)))


# At this point the run mask should match the veg map.
assert np.array_equal(vm.astype(int), rm_m.astype(int)), "Something is wrong!!"

###########################################################
# Further mask off any pixels not availbe in the topo file
###########################################################

# Read in the topo file
topo = nc.Dataset('DATA/SouthBarrow_10x10/topo.nc')

# create masked arrays for each individual variable
am = np.ma.getmaskarray(np.ma.masked_less(topo.variables['aspect'][:], 0))
em = np.ma.getmaskarray(np.ma.masked_less(topo.variables['elevation'][:], -100))
sm = np.ma.getmaskarray(np.ma.masked_less(topo.variables['slope'][:], 0))

# SERIOUS!
# Might want to loop over am, em, sm here and check that the returned value
# has a mask - if all the data is good, the returned item is a numpy masked
# array, but the mask property is set to false - instead, we want the mask to 
# be set to an array of all "False" (not masked).
# THIS MIGHT NOT WORK:
#for a in [am, em, sm]:
#  if type(a) != np.ma.core.MaskedArray:
#    a = np.ma.core.MaskedArray(a, np.zeros(a.shape, dtype = bool))
# NEED TO USE np.ma.getmaskarray()!?


# make a full mask for the whole file - mask any pixel missing in any of the variables
all_topo_m = ( am | em | sm ) # should be same as np.logical_or(...)

# Report on how we are doing
print "Number of masked elements in topo file: ", np.count_nonzero(all_topo_m)
print "Number of masked elements in run mask: ", np.count_nonzero(rm_m)

# Set of all masked coords in topo file and run-mask
s_tm_c = set(zip(*np.nonzero(all_topo_m)))
s_rm_c = set(zip(*np.nonzero(rm_m)))

# Show all coords that are not present in the other mask:
print "Symetric difference in masked coords sets: ", s_tm_c.symmetric_difference(s_rm_c)

# Show coords masked in topo, but not the run mask:
print "Coords of px masked in topo file, but not the run mask: ", s_tm_c.difference(s_rm_c)

# Show which pixels are different 
print "Here is(are) the differing pixel(s): \n", np.logical_xor(all_topo_m, rm_m).astype(int)

# Now set the run mask to be any pixel in either array that should be masked
rm_m = (rm_m | all_topo_m)

# Handle the soil
soil = nc.Dataset("DATA/SouthBarrow_10x10/soil-texture.nc")

# Using getmaskarray helps with the case where all values in the array are good
# and calling .mask returns "False" when what you are looking for is an array of
# booleans indicating that the mask is false for all values in the array.
sandm = np.ma.getmaskarray(np.ma.MaskedArray(soil.variables['pct_sand'][:]))
siltm = np.ma.getmaskarray(np.ma.MaskedArray(soil.variables['pct_silt'][:]))
claym = np.ma.getmaskarray(np.ma.MaskedArray(soil.variables['pct_clay'][:]))
# .... Go thru reporting stuff as above ...
# Make sure any bad pixels are transfered to the run mask
rm_m = (rm_m | sandm | siltm | claym)

# Handle the climate
for file in ["historic-climate", "projected-climate"]:
  ds = nc.Dataset("DATA/SouthBarrow_10x10/{}.nc".format(file))
  for v in ['tair', 'precip', 'nirr', 'vapor_press']:
    print "[{}] Updating mask for variable {}...".format(file, v)
    v_m = np.ma.getmaskarray(np.ma.MaskedArray(ds.variables[v][:]))
    rm_m = conform_mask_timeseries(rm_m, v_m)

# Handle the fire
for file in ["historic-explicit-fire", "projected-explicit-fire"]:
  ds = nc.Dataset("DATA/SouthBarrow_10x10/{}.nc".format(file))
  for v in ['exp_burn_mask', 'exp_jday_of_burn', 'exp_area_of_burn','exp_fire_severity']:
    print "[{}] Updating mask for variable {}...".format(file, v)
    v_m = np.ma.getmaskarray(np.ma.MaskedArray(ds.variables[v][:]))
    rm_m = conform_mask_timeseries(rm_m, v_m)

# Handle FRI fire...
print "Handling FRI fire..."
ff = nc.Dataset("DATA/SouthBarrow_10x10/fri-fire.nc")
frim = np.ma.getmaskarray(ff.variables['fri'][:])
friaobm = np.ma.getmaskarray(ff.variables['fri_area_of_burn'][:])
frijdobm = np.ma.getmaskarray(ff.variables['fri_jday_of_burn'][:])
frisevm = np.ma.getmaskarray(ff.variables['fri_severity'][:])

rm_m = ( rm_m | frim | friaobm | frijdobm | frisevm)

# Handle drainage...
print "Handling drainage..."
dr = nc.Dataset("DATA/SouthBarrow_10x10/drainage.nc")
drm = np.ma.getmaskarray(dr.variables['drainage_class'][:])
rm_m = ( rm_m | drm )

print "FINAL MASK"
print rm_m.astype(int)
print "Inverted to match the style we use with dvmdostem:"
print np.invert(rm_m).astype(int)

# Still need to apply the mask to the actual run-mask data and write and close file...



