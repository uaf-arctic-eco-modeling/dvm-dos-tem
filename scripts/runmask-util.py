#!/usr/bin/env python

# Tobey Carman
# Dec 2016

import netCDF4 as nc
import argparse
import textwrap

def show_mask(file, note):
  with nc.Dataset(file, 'r') as mask:
    print "========== %s ==================================" % (note)
    print "'%s'" % (file)
    print mask.variables['run']
    print mask.variables['run'][:]
    print ""

if __name__ == '__main__':

  parser = argparse.ArgumentParser(
	  formatter_class=argparse.RawDescriptionHelpFormatter,
 		description=textwrap.dedent('''
    	Helper script for modifying a dvm-dos-tem runmask netcdf file.
    ''')
  )
  parser.add_argument('file', metavar=('file'), 
      help=textwrap.dedent('''The runmask.nc file to operate on.'''))

  parser.add_argument('--reset', action='store_true', 
      help=textwrap.dedent('''Set all pixels to zero (don't run).'''))

  parser.add_argument("--xy", nargs=2,
  		help=textwrap.dedent('''The x, y position of the pixel to turn on.'''))

  parser.add_argument("--show", action='store_true',
  		help=textwrap.dedent('''Print the mask after modification.'''))

  args = parser.parse_args()

  if args.show:
  	show_mask(args.file, "BEFORE")

  with nc.Dataset(args.file, 'a') as mask:

	  if args.reset:
	  	print "Setting all pixels in runmask to '0' (OFF)."
	  	mask.variables['run'][:] = 0

	  if args.xy:
	  	X,Y = args.xy
	  	print "Turning pixel(x,y) to '1', (ON)."
	  	mask.variables['run'][X,Y] = 1

  # Show the after state
  if args.show:
    show_mask(args.file, "AFTER")


