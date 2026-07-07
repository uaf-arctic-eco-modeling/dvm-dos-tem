#!/usr/bin/env python
# -*- coding: utf-8 -*-

# T. Carman March 2017

import sys
import os
import re
import argparse
import textwrap
import numpy as np
import matplotlib.pyplot as plt
import netCDF4 as nc
import matplotlib.ticker

from mpl_toolkits.basemap import Basemap


def dms2dd(degrees, minutes, seconds, direction):
  dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60)
  if direction == 'S' or direction == 'W':
    dd *= -1.0
  return dd

def parse_dms(dms):
  #parts = re.split('[°\'"]+', dms)
  parts = dms.strip().split(' ')
  print(parts)
  return parts


def discrete_cmap(N, base_cmap=None):
    """Create an N-bin discrete colormap from the specified input map
    From: Jake VanderPlas
    License: BSD-style
    https://gist.github.com/jakevdp/91077b0cae40f8f8244a
    """

    # Note that if base_cmap is a string or None, you can simply do
    #    return plt.cm.get_cmap(base_cmap, N)
    # The following works for string, None, or a colormap instance:

    base = plt.cm.get_cmap(base_cmap)
    color_list = base(np.linspace(0, 1, N))
    cmap_name = base.name + str(N)
    return base.from_list(cmap_name, color_list, N)


if __name__ == '__main__':

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      Script for viewing dvmdostem input files.
    ''')
  )
  parser.add_argument('file', nargs='?', 
      #type=argparse.FileType('r'),
      metavar=('FILE'), 
      help=textwrap.dedent('''The input file to display.'''))

  parser.add_argument('--dms2dd', nargs=4, metavar=("DD", "MM", "SS", "D"),
      # default=,
      # const=,
      help=textwrap.dedent('''Convert degrees minutes seconds to decimal degrees.'''))


  args = parser.parse_args()
  #print sys.argv
  #print len(sys.argv)
  #print args

  if args.dms2dd:
    coords = args.dms2dd
    dd = dms2dd(coords[0],coords[1],coords[2],coords[3])
    print (dd)
    sys.exit(-1)

  # if args.file == None:
  #   print "ERROR: You must provide a file argument!"
  #   sys.exit(-1)

  d = nc.Dataset(args.file)

  lats = d.variables['lat'][:]
  lons = d.variables['lon'][:]
  lons2 = 180+(180-(-1*lons))

  fig, (ax0, ax1) = plt.subplots(ncols=2)

  ax0.set_title("General Overview")
  m = Basemap(lat_0=65, lon_0=-151, width=1600*1000, height=1400*1000, 
              projection='aeqd', resolution=None, ax=ax0)
  m.bluemarble()
  x, y = m(lons2, lats)
  points = m.scatter(x, y, marker='o', color='r')


  if 'veg_class' in list(d.variables.keys()):
    CMTNAMES = [ 
      "Bare Ground Rock Water",
      "Black Spruce",
      "White Spruce",
      "Boreal Deciduous",
      "Shrub Tundra",
      "Tussock Tundra",
      "Wet Sedge Tundra",
      "Heath Tundra",
      "Maritime Forest",
    ]

    N = len(CMTNAMES)

    file_max = d.variables['veg_class'][:,:].max()
    file_min = d.variables['veg_class'][:,:].min()
    data2show = d.variables['veg_class']
    color_map = discrete_cmap(N, 'Set1')

  if 'tair' in list(d.variables.keys()):
    data2show = d.variables['tair'][0]
    color_map = plt.cm.get_cmap('Reds')



  ax1.set_title("Area of Interest")
  print(data2show.shape)
  img = ax1.imshow(data2show[:,:], 
                   origin='lower', interpolation='none', 
                   cmap=color_map)
  img.set_clim(-0.5, N-0.5)

  if 'veg_class' in list(d.variables.keys()):
    cbar = fig.colorbar(img, ax=ax1)
    cbar.set_ticks(list(range(len(CMTNAMES))))
    cbar.set_ticklabels(CMTNAMES)

  if 'tair' in list(d.variables.keys()):
    pass


  fig.suptitle('??')

  fig.tight_layout()

  plt.show(block=True)



# Offset info
# ===========

# ncview - (0,0) is lower left
# ----------------------------
# i --> x --> lon
# j --> y --> lat

# matplotlib - (0,0) is upper left
# --------------------------------
# Even when using plt.imshow(.., origin-'lower', ...) it seems to take slices
# from the upper left.


