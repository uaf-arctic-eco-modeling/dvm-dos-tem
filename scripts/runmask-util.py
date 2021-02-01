#!/usr/bin/env python

# Tobey Carman
# Dec 2016

import netCDF4 as nc
import argparse
import textwrap
import os
import numpy as np

import input_util

'''
This script is for creating, modifying, and viewing run masks for dvmdostem. 
The script can carry out modifications to a run-mask that give it certain 
properties in relation to a set of dvmdostem input data.

For example this script can be used to create a run mask that will exclude any
pixels where any of the input data is missing or invalid.
'''


def report(taglist, masklist):
  '''
  Make various printouts about the masks
  
  Parameters
  ----------
  taglist : list of strings/tags
  masklist : list of masks (numpy arrays of bool)

  Returns: None
  '''

  # E.g.:
  #             masked 
  # run mask      1308
  # veg             24
  print("{:>20}".format('# masked'))
  for tag, mask in zip(taglist, masklist):
    print("{:10}{:>10}".format(tag, np.count_nonzero(mask)))

  # Other ideas for interesting stuff to report...
  # # Set of all masked coords in topo file and run-mask
  # s_tm_c = set(zip(*np.nonzero(all_topo_m)))
  # s_rm_c = set(zip(*np.nonzero(rm_m)))

  # # Show all coords that are not present in the other mask:
  # print "Symetric difference in masked coords sets: ", s_tm_c.symmetric_difference(s_rm_c)

  # # Show coords masked in topo, but not the run mask:
  # print "Coords of px masked in topo file, but not the run mask: ", s_tm_c.difference(s_rm_c)

  # # Show which pixels are different 
  # print "Here is(are) the differing pixel(s): \n", np.logical_xor(all_topo_m, rm_m).astype(int)

def conform_mask_timeseries(rm_m, data):
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

  datam = np.ma.getmaskarray(data)

  for tidx, m in enumerate(datam): # only over 1st dimension?
    prev = np.copy(rm_m)
    rm_m = ( rm_m | m )
    modcoords = np.nonzero(np.logical_xor(rm_m, prev))
    if len(list(zip(*modcoords))) > 0:
      print("At timestep {} modify mask at coords: {}".format(tidx, list(zip(*modcoords))))

  # mc = np.nonzero(np.logical_xor(original_rm_m, rm_m).astype(int))
  # print "Summary of modified coords:"
  # for i, c in enumerate(zip(*mc)):
  #   print c

  return rm_m


def conform_mask_to_inputs(in_folder):
  '''
  Loops over a set of dvmdostem inputs and masks any pixel in the run-mask
  where any of the data for that pixel in the inputs is bad or missing.
  '''

  input_util.verify_input_files(in_folder)

  ###########################################################
  # First set the run mask based on the veg map
  ###########################################################
  veg = nc.Dataset(os.path.join(in_folder, 'vegetation.nc'), 'r')

  # make a mask the same shape as the veg file, with every pixel turned off.
  rm_m = np.zeros((veg.variables['veg_class'].shape), dtype=int)

  # Get just the masks - we dont really need the data at this point
  # For the veg, mask anything less than zero. CMT 0 is rock/snow/water, while
  # anything negative is ocean (or out of geographic domain)
  vm = np.ma.getmaskarray(np.ma.masked_less(veg.variables['veg_class'][:], 0))

  # Mask anything that is masked in the veg map or the run mask.
  rm_m = (rm_m | vm)

  # Optional: show the distrubution of various veg classes in the map as a 1D histogram:
  #plt.hist(veg.variables['veg_class'][:].flatten())

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

  report(['veg mask','run mask'],[vm, rm_m])

  ###########################################################
  # Mask off any pixels not availbe in the topo file
  ###########################################################
  topo = nc.Dataset(os.path.join(in_folder, 'topo.nc'), 'r')

  # create masked arrays for each individual variable
  am = np.ma.getmaskarray(np.ma.masked_less(topo.variables['aspect'][:], 0))
  em = np.ma.getmaskarray(np.ma.masked_less(topo.variables['elevation'][:], -100))
  sm = np.ma.getmaskarray(np.ma.masked_less(topo.variables['slope'][:], 0))

  # make a full mask for the whole file - mask any pixel missing in any of the variables
  all_topo_m = ( am | em | sm ) # should be same as np.logical_or(...)

  # Now set the run mask to be any pixel in either array that should be masked
  rm_m = (rm_m | all_topo_m)

  report(["aspect", "elevation", "slope", "all topo", 'run mask'], [am, em, sm, (am|em|sm), rm_m])

   
  ###########################################################
  # Mask off any pixels not availbe in the soil file
  ###########################################################
  soil = nc.Dataset(os.path.join(in_folder, "soil-texture.nc"), 'r')

  # Using getmaskarray helps with the case where all values in the array are good
  # and calling .mask returns "False" when what you are looking for is an array of
  # booleans indicating that the mask is false for all values in the array.
  sandm = np.ma.getmaskarray(np.ma.MaskedArray(soil.variables['pct_sand'][:]))
  siltm = np.ma.getmaskarray(np.ma.MaskedArray(soil.variables['pct_silt'][:]))
  claym = np.ma.getmaskarray(np.ma.MaskedArray(soil.variables['pct_clay'][:]))

  # Make sure any bad pixels are transfered to the run mask
  rm_m = (rm_m | sandm | siltm | claym)

  report(['sand', 'silt', 'clay', 'all soil', 'run mask'],[sandm, siltm, claym, (sandm|siltm|claym), rm_m])

  ###########################################################
  # Mask anything not available in the drainage file
  ###########################################################
  dr = nc.Dataset(os.path.join(in_folder, "drainage.nc"), 'r')
  drm = np.ma.getmaskarray(dr.variables['drainage_class'][:])
  rm_m = ( rm_m | drm )
  report(['drainage','run mask'],[drm, rm_m])

  ###########################################################
  # Handle FRI fire...
  ###########################################################
  print("Handling FRI fire...")
  ff = nc.Dataset(os.path.join(in_folder, "fri-fire.nc"), 'r')
  frim = np.ma.getmaskarray(ff.variables['fri'][:])
  friaobm = np.ma.getmaskarray(ff.variables['fri_area_of_burn'][:])
  frijdobm = np.ma.getmaskarray(ff.variables['fri_jday_of_burn'][:])
  frisevm = np.ma.getmaskarray(ff.variables['fri_severity'][:])

  rm_m = ( rm_m | frim | friaobm | frijdobm | frisevm)
  report(['fri','fri aob','fri dob','fri sev','run mask'],[frim, friaobm, frijdobm, frisevm, rm_m])

  ###########################################################
  # Handle the climate
  ###########################################################
  for file in ["historic-climate", "projected-climate"]:
    ds = nc.Dataset( os.path.join(in_folder,"{}.nc".format(file)) )
    for v in ['tair', 'precip', 'nirr', 'vapor_press']:
      print("[{}] Updating mask for variable {}...".format(file, v))
      v_m = np.ma.MaskedArray(ds.variables[v][:])
      rm_m = conform_mask_timeseries(rm_m, v_m)

  ###########################################################
  # Handle the explicit fire
  ###########################################################
  for file in ["historic-explicit-fire.nc", "projected-explicit-fire.nc"]:
    ds = nc.Dataset(os.path.join(in_folder, file))
    for v in ['exp_burn_mask', 'exp_jday_of_burn', 'exp_area_of_burn','exp_fire_severity']:
      print("[{}] Updating mask for variable {}...".format(file, v))
      v_m = np.ma.getmaskarray(np.ma.MaskedArray(ds.variables[v][:]))
      rm_m = conform_mask_timeseries(rm_m, v_m)

  print("FINAL MASK")
  print(rm_m.astype(int))
  print("Inverted to match the style we use with dvmdostem:")
  print(np.invert(rm_m.astype(bool)).astype(int))

  return rm_m




def show_mask(file, note):
  with nc.Dataset(file, 'r') as mask:
    print("========== %s ==================================" % (note))
    print("** Keep in mind that in this display the origin is the upper ")
    print("** left of the grid! This is opposite of the way that ncdump ")
    print("** and ncview display data (origin is lower left)!!")
    print("")
    print("'%s'" % (file))
    print(mask.variables['run'])
    print(mask.variables['run'][:])
    print("")

if __name__ == '__main__':

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      Helper script for modifying a dvm-dos-tem runmask netcdf file.
    ''')
  )
  parser.add_argument('file', nargs='?', metavar=('FILE'), 
      help=textwrap.dedent('''The runmask.nc file to operate on.'''))

  parser.add_argument('--reset', action='store_true', 
      help=textwrap.dedent('''Set all pixels to zero (don't run).'''))

  parser.add_argument('--all-on', action='store_true', 
      help=textwrap.dedent('''Set all pixels to 1 (run). Inverse of --reset.'''))

  parser.add_argument("--yx", nargs=2, type=int, metavar=('Y','X'),
      help=textwrap.dedent('''The y, x  (row, col) position of the pixel to turn on.'''))

  parser.add_argument("--yx-off", nargs=2, type=int, metavar=('Y','X'),
      help=textwrap.dedent('''The y, x  (row, col) position of the pixel to turn OFF.'''))

  parser.add_argument("--show", action='store_true',
      help=textwrap.dedent('''Print the mask after modification.'''))

  parser.add_argument("--conform-mask-to-inputs", metavar=('FOLDER'), #nargs=1,
      help=textwrap.dedent('''Operate on the run-mask and conform it to all the 
          input files in %(metavar)s. Makes sure that the run-mask will disable
          any pixel (set to 0) where any of the input files contain bad or 
          missing data. NOTE!!: modifies run-mask.nc found in %(metavar)s, and
          ignores the files specified 'FILE' argument!'''))

  parser.add_argument("--select-only-cmt", metavar=('FOLDER','CMT'), nargs=2,
    help=textwrap.dedent('''Select only pixels with a certain CMT number. This
          will honor any pixels that are alreay masked in the run-mask. As such, 
          you should probably conform the mask to the inputs before running the
          script again with this option to select only certain CMTs.'''))

  parser.add_argument("--mask-out-cmt", metavar=('FOLDER','CMT'), nargs=2,
    help=textwrap.dedent('''Mask out pixels with a certain CMT. This will
         maintain any pixels already masked.'''))

  args = parser.parse_args()

  if args.select_only_cmt:
    input_folder_path = args.select_only_cmt[0]
    cmt = int(args.select_only_cmt[1])

    with nc.Dataset(os.path.join(input_folder_path, 'vegetation.nc')) as vm:
      cmt_mask = np.ma.masked_not_equal(vm.variables['veg_class'][:], cmt)

    with nc.Dataset(os.path.join(input_folder_path, 'run-mask.nc')) as runmask:
      rm = runmask.variables['run'][:]

    # At this point, rm is a 2D array with '1's as "yes, run this pixel"
    # This is opposite of how numpy masked arrays works, where a mask value 
    # of '1' (True) means "yes mask the value" or "no, don't run the pixel"
    # So to make future operations easier, we flip the run mask so it matches
    # the numpy mask concept.
    rm_m = np.invert(rm.astype(bool)).astype(int)

    with nc.Dataset(os.path.join(input_folder_path, 'run-mask.nc'), 'r+') as runmask:
      runmask.variables['run'][:] = np.invert((rm_m | cmt_mask.mask).astype(bool)).astype(int)

    show_mask(os.path.join(input_folder_path, "run-mask.nc"), "New mask file showing only cmt {}".format(cmt))
    exit(0)


  if args.mask_out_cmt:
    input_folder_path = args.mask_out_cmt[0]
    cmt = int(args.mask_out_cmt[1])

    with nc.Dataset(os.path.join(input_folder_path, 'vegetation.nc')) as vm:
      cmt_mask = np.ma.masked_equal(vm.variables['veg_class'][:], cmt)

    with nc.Dataset(os.path.join(input_folder_path, 'run-mask.nc')) as runmask:
      rm = runmask.variables['run'][:]

    # At this point, rm is a 2D array with '1's as "yes, run this pixel"
    # This is opposite of how numpy masked arrays works, where a mask value 
    # of '1' (True) means "yes mask the value" or "no, don't run the pixel"
    # So to make future operations easier, we flip the run mask so it matches
    # the numpy mask concept.
    rm_m = np.invert(rm.astype(bool)).astype(int)

    with nc.Dataset(os.path.join(input_folder_path, 'run-mask.nc'), 'r+') as runmask:
      runmask.variables['run'][:] = np.invert((rm_m | cmt_mask.mask).astype(bool)).astype(int)

    show_mask(os.path.join(input_folder_path, "run-mask.nc"), "New mask file showing only cmt {}".format(cmt))
    exit(0)


  if args.conform_mask_to_inputs:

    input_folder_path = args.conform_mask_to_inputs

    new_mask = conform_mask_to_inputs(input_folder_path)

    sizey, sizex = new_mask.shape

    # (Over) write the file back out
    with nc.Dataset(os.path.join(input_folder_path, "run-mask.nc"), 'w') as nf:
      Y = nf.createDimension('Y', sizey)
      X = nf.createDimension('X', sizex)
      run = nf.createVariable('run', np.int, ('Y', 'X',))

      run[:] = np.invert(new_mask.astype(bool))

    show_mask(os.path.join(input_folder_path, "run-mask.nc"), "New, conforming mask file")
    exit(0)


  if args.show:
    show_mask(args.file, "BEFORE")

  with nc.Dataset(args.file, 'a') as mask:

    if args.reset:
      print("Setting all pixels in runmask to '0' (OFF).")
      mask.variables['run'][:] = 0

    if args.yx:
      Y,X = args.yx
      print("Turning pixel(y,x) ({},{}) to '1', (ON).".format(Y,X))
      mask.variables['run'][Y,X] = 1

    if args.all_on:
      print("Setting all pixels in runmask to '1' (ON).")
      mask.variables['run'][:] = 1

    if args.yx_off:
      Y, X = args.yx_off
      print("Setting pixel (y, x) ({},{}) to '0', (OFF).".format(Y,X))
      mask.variables['run'][Y,X] = 0

  # Show the after state
  if args.show:
    show_mask(args.file, "AFTER")


