#!/usr/bin/env python

import os
import errno
import glob
import netCDF4 as nc

import argparse
import textwrap


def mkdir_p(path):
  '''Emulates the shell's `mkdir -p`.'''
  try:
    os.makedirs(path)
  except OSError as exc:  # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise


'''
Utility functions for working with dvmdostem inputs.
'''

#################################################################
# Define custom errors that are relevant for this application
#################################################################
class BadInputFilesValueError(ValueError):
  '''Raise when there is a problem with the input files.'''

class MissingInputFilesValueError(ValueError):
  '''Raise when not enough files are present.'''


def verify_input_files(in_folder):
  '''
  Raises various exceptions if there are problems with the files in the in_folder.

  Parameters
  ----------
  in_folder : str
    A path to a folder of dvmdostem inputs.

  Throws
  ------  
  BadInputFilesValueError, 

  Returns
  -------
  None
  '''
  required_files = set(['co2.nc', 'drainage.nc', 'fri-fire.nc', 
      'historic-climate.nc', 'historic-explicit-fire.nc',
      'projected-climate.nc', 'projected-explicit-fire.nc', 'run-mask.nc',
      'soil-texture.nc', 'topo.nc', 'vegetation.nc'])

  files = set([f for f in os.listdir(in_folder) if os.path.isfile(os.path.join(in_folder, f))])
  dirs = [d for d in os.listdir(in_folder) if os.path.isdir(os.path.join(in_folder, d))]

  # any 
  #print "Symetric difference: ", files.symmetric_difference(required_files)
  
  if len(files.difference(required_files)) > 0:
    print "WARNING: extra files present: ", files.difference(required_files)

  if len(required_files.difference(files)):
    msg = "Missing files: {}".format(required_files.difference(files))
    raise MissingInputFilesValueError(msg)

  if 'output' not in dirs:
    raise MissingInputFilesValueError("'output/' directory not present!")


def crop_attr_string(ys='', xs='', yo='', xo='', msg=''):
  '''
  Returns a string to be included as a netCDF global attribute named "crop".

  The string will start with the filename and function name responsible for
  creating the (new) input file, and if provided, will include values for size
  and offset. The size attributes are relatively self-explanatory (by looking
  at the size of the resulting file), and so can generally be ignored. The
  offset arguments are much more important to include.

  Parameters
  ----------
  ys, xs : str
    Strings denoting the spatial size of the domain.
  yo, xo : str
    Strings denoting the pixel offsets used to crop the data from the input dataset
  msg : str
    An additional message string to be included.

  Returns
  -------
  s : str
    A string something like:
    "./scripts/input_util.py::crop_file --ysize 3 --xsize 4 --yx 0 0
  '''
  import inspect
  cf = inspect.currentframe().f_back # <-- gotta look up one frame.

  # Start with the file name and function name
  s = "{}::{}".format(cf.f_code.co_filename, cf.f_code.co_name,)

  # add other info if present.
  for t, val in zip(['--ysize','--xsize','--yx',''],[ys,xs,' '.join([str(yo), str(xo)]), msg]):
    if val != '':
      s += " {} {}".format(t, val)

  return s


def crop_file(infile, outfile, y, x, ysize, xsize):
  '''
  Creates a new `outfile` and copys data from the `infile` to the new outfile
  according to `y`, `x`, and respective size parameters. Copys all attributes
  and adds a new attribute describing this crop step.
  '''

  with nc.Dataset(infile, 'r') as src, nc.Dataset(outfile, 'w') as dst:

    # copy global attributes all at once
    dst.setncatts(src.__dict__)

    # add the crop attribute string
    dst.crop = crop_attr_string(yo=y, xo=x, ys=ysize, xs=xsize)

    # next, create dimensions in the new file, mirroring the old dims
    for name, dimension in src.dimensions.items():
      if name == 'X':
        dst.createDimension(name, xsize)
      elif name == 'Y':
        dst.createDimension(name, ysize)
      else:
        dst.createDimension(name, (len(dimension) if not dimension.isunlimited() else None))

    for name, var in src.variables.items():
      print "  copying variable {} with dimensions {}".format(name, var.dimensions)
      newvar = dst.createVariable(name, var.datatype, var.dimensions)

      # Copy all attributes for the variable over
      newvar.setncatts(var.__dict__)

      # Now work on copying data...
      if var.dimensions == ('Y','X'):
        newvar[:] = var[y:y+ysize,x:x+xsize]
      elif var.dimensions == ('time','Y','X'):
        newvar[:] = var[:,y:y+ysize,x:x+xsize]
      elif 'Y' in var.dimensions and len(var.dimensions) == 1:
        newvar[:] = var[y:y+ysize]
      elif 'X' in var.dimensions and len(var.dimensions) == 1:
        newvar[:] = var[x:x+xsize]
      elif 'time' in var.dimensions and len(var.dimensions) == 1:
        newvar[:] = var[:]
      elif 'year' in var.dimensions and len(var.dimensions) == 1:
        newvar[:] = var[:]
      else:
        print "NOT SURE WHAT TO DO WITH VARIABLE: {} HAVING DIMS: {}".format(name, var.dimensions)




def crop_wrapper(args):
  '''
  Parses input folder name to find tag, and creates appropriately named
  output directory alongside the input directory. Calls the crop_file
  function for each netcdf file found in the input directory.
  '''
  infolder = args.input_folder

  filelist = glob.glob(os.path.join(infolder, "*.nc"))

  # Assume infolder is of the form: some/long/path/<tag>_<Ysize>x<Xsize>
  # Then grab the last element of the path, split it on underscores and 
  # take the first element to get the tag:
  tag = os.path.split(infolder)[-1].split('_')[0:-1]
  tag = '_'.join(os.path.basename(os.path.normpath(infolder)).split('_')[0:-1])
  outfolder = os.path.join(os.path.dirname(os.path.normpath(infolder)), "{}_{}x{}".format(tag, args.ysize, args.xsize))

  print "Creating output folder: ", outfolder
  mkdir_p(outfolder)

  for srcfile in filelist:
    infile = srcfile
    outfile = os.path.join(outfolder, os.path.basename(srcfile))
    print "input file: {}  -->  output file: {}".format(infile, outfile)
    y, x = args.yx
    crop_file(infile, outfile, y, x, args.ysize, args.xsize)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    formatter_class = argparse.RawDescriptionHelpFormatter,

      description=textwrap.dedent('''\
        Command line interface for utility functions that work on 
        dvmdostem inputs. This script may also be imported and used
        from other scripts (if you wish to import functions without 
        using this command line interface).

        The command line interface contains (or will in the future)
        different sub-commands for different types of operations.
        '''.format("")),

      epilog=textwrap.dedent(''''''),
  )
  subparsers = parser.add_subparsers(help='sub commands', dest='command')


  crop_parser = subparsers.add_parser('crop',help=textwrap.dedent('''\
      Crop an input dataset, using offset and size. The reason we need this in
      addition to the create_region_input.py script is because the 
      create_region_input.py script uses gdal_translate (or gdalwarp) to subset
      the original tif files, and for some reason that has problems creating 
      regions smaller than about 5x5 pixels. So in order to get a single pixel
      input dataset, we have to first create a larger dataset, and then crop it
      using this tool. Someday it might make sense to merge this script with the
      create_region_input.py script.'''))
  crop_parser.add_argument('--yx', type=int, nargs=2, required=True, help="The Y, X position to start cropping")
  crop_parser.add_argument('--ysize', type=int, default=1, help="The number of pixels to take in the y dimension.")
  crop_parser.add_argument('--xsize', type=int, default=1, help="The number of pixels to take in the x dimension.")
  crop_parser.add_argument('input_folder', help="Path to a folder containing a set of dvmdostem inputs.")

  # EXAMPLES
  # ./input_utils.py crop --yx 0 0 --ysize 1 --xsize 1 DATA/Toolik_10x10

  args = parser.parse_args()

  print args

  if args.command == 'crop':
    verify_input_files(args.input_folder)
    crop_wrapper(args)



