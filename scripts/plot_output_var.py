#!/usr/bin/env python


# import os
import netCDF4 as nc
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


import argparse
import textwrap




if __name__ == '__main__':

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      Script for plotting a single dvm-dos-tem output netCDF file. It is hardcoded to cell 0,0 and determines variable name by any netCDF var that is not time.
    ''')
  )

  parser.add_argument('--file', nargs='?', metavar=('FILE'),
    help = textwrap.dedent('''The output .nc file to operate on'''))

  parser.add_argument('--pft', type=int,
    help = textwrap.dedent('''The PFT to plot when plotting by PFT and compartment'''))

  parser.add_argument('--layers', type=int,
    help = textwrap.dedent('''Number of layers to plot. Starts at the surface.'''))


  args = parser.parse_args()

  if args.file:

    with nc.Dataset(args.file, 'r') as ncFile:
      nc_dims = [dim for dim in ncFile.dimensions]
      nc_vars = [var for var in ncFile.variables]

      #Should be determined more neatly.
      for var in nc_vars:
        if var != 'time':
          plotting_var = var
          print "plotting var: " + plotting_var

      nc_data = ncFile.variables[plotting_var][:,:]

      dim_count = len(nc_dims)

      print "dim count: " + str(dim_count) 
      print "dimensions: " + str(nc_dims)
      print "variables: " + str(nc_vars)
      print "shape: " + str(nc_data.shape)

      mpl.rc('lines', linewidth=1, markersize=3, marker='o')

      #Variables by time only
      #time, y?, x?
      if(dim_count == 3):
        data = nc_data[:,0,0]
        fig, ax = plt.subplots(1,1)
        ax.plot(data)


      #Variables by PFT, Compartment, or Layer
      #time, [section], y?, x?
      if(dim_count == 4):
        data = nc_data[:,:,0,0]

        #By PFT only
        if 'pft' in nc_dims:
          fig, ax = plt.subplots(10,1)

          for pft in range(0,10):
            ax[pft].plot(data[:,pft])
            ax[pft].set_ylabel("pft" + str(pft))

        #By PFT compartment
        if 'pftpart' in nc_dims:
          fig, ax = plt.subplots(3,1)

          for pftpart in range(0,3):
            ax[pftpart].plot(data[:,pftpart])
            ax[pftpart].set_ylabel("pftpart " + str(pftpart))

        #By soil layer
        if 'layer' in nc_dims:
          if args.layers:
            layer_count = args.layers
          else:
            layer_count = 3
          fig, ax = plt.subplots(layer_count,1)

          for layer in range(0, layer_count):
            ax[layer].plot(data[:,layer])
            ax[layer].set_ylabel("layer " + str(layer))


      #Variables by both PFT and Compartment
      #time, pftpart, pft, y?, x?
      if(dim_count == 5):
        if args.pft is not None:
          pft_choice = args.pft
        else:
          pft_choice = 0 

        print "Plotting PFT: " + str(pft_choice)

        data = nc_data[:,:,pft_choice,0,0]

        fig, ax = plt.subplots(3,1)
  
        for pftpart in range(0, 3):
          ax[pftpart].plot(data[:,pftpart])
          ax[pftpart].set_ylabel("pftpart " + str(pftpart))


      #All variables share this section
      fig.canvas.set_window_title(plotting_var)
      plt.xlabel("time")
      plt.show()


