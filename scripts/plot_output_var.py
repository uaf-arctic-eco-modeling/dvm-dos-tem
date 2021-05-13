#!/usr/bin/env python


import sys
import netCDF4 as nc
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


import argparse
import textwrap




if __name__ == '__main__':

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      Script for plotting a single dvm-dos-tem output netCDF file. 

      Options are available for controlling which pixel to plot, which pft(s), 
      which layer(s), and how closely the subplots should be linked for scale,
      panning and zooming.

      Determines variable name by any netCDF var that is not time.
    ''')
  )

  parser.add_argument('--file', nargs='?', metavar=('FILE'),
    help = textwrap.dedent('''The output .nc file to operate on. (Output from 
      dvmdostem, input to this script).'''))

  parser.add_argument('--yx', type=int, nargs=2, required=False, default=[0,0],
    metavar=('Y', 'X'), help=textwrap.dedent('''Select the pixel to plot'''))

  parser.add_argument('--pft', type=int,
    help = textwrap.dedent('''The PFT to plot when plotting by PFT and compartment'''))

  parser.add_argument('--layers', type=int, nargs=2, required=False, default=[0,3],
    metavar=('START', 'END'),
    help = textwrap.dedent('''The range of layers to plot.'''))

  parser.add_argument('--layer-sum', action='store_true',
    help=textwrap.dedent('''Adds a subplot at the top which is the sum of all
      the other layers that are displayed.'''))

  parser.add_argument('--hide-individual-layers', action='store_true',
    help=textwrap.dedent('''Do not show subplots for all the individual layers'''))

  parser.add_argument('--timesteps', type=int, required=False, nargs=2,
    metavar=('START','END'),
    help = textwrap.dedent('''The range of timesteps to plot.'''))

  parser.add_argument('--sharex', action='store_true',
    help=textwrap.dedent('''All plots share an x axes for linked panning and zooming.'''))

  parser.add_argument('--sharey', action='store_true',
    help=textwrap.dedent('''All plots share a y axes for linked panning, zooming, and autoscaling.'''))

  parser.add_argument('--annual-grid', action='store_true',
    help=textwrap.dedent('''Display a vertial grid line every 12 months.
      Generally this is too dense when viewing a long timeseries, but is helpful
      if you plan to zoom in on the data.'''))

  args = parser.parse_args()
  print(args)

  if args.file:

    with nc.Dataset(args.file, 'r') as ncFile:
      nc_dims = [dim for dim in ncFile.dimensions]
      nc_vars = [var for var in ncFile.variables]


      # Should be determined more neatly.
      for var in nc_vars:
        if var == 'time' or 'grid_mapping_name' in ncFile[var].ncattrs():
          pass # Can't plot these...
        else:
          plotting_var = var
          print("plotting var: " + plotting_var)

      if args.timesteps is not None:
        time_start = args.timesteps[0]
        time_end = args.timesteps[1]
        nc_data = ncFile.variables[plotting_var][time_start:time_end,:]
        time_range = np.arange(time_start,time_end)
      else:
        nc_data = ncFile.variables[plotting_var][:,:]
        time_range = np.arange(0, nc_data.shape[0])

      layer_start, layer_end = args.layers

      Y, X = args.yx

      dim_count = len(nc_dims)

      print("pixel(Y,X): ({},{})".format(Y, X))
      print("dim count: " + str(dim_count)) 
      print("dimensions: " + str(nc_dims))
      print("variables: " + str(nc_vars))
      print("shape: " + str(nc_data.shape))
      print("selected time range size: {} start: {} end: {}".format(
          len(time_range), time_range[0], time_range[-1]))

      matplotlib.rc('lines', linewidth=1, markersize=0, marker='o')

      if args.layer_sum and plotting_var not in ['SOC', 'RH']:
        print("WARNING: The sum across layer plot has not been tested on other ")
        print("variables! The plot is only intended to work with variables that ")
        print("have non-negative values!")

      if args.hide_individual_layers and not args.layer_sum:
        print("WARNING! --hide-individual-layers is only applicable with --layer-sum")


      # Variables by time only
      # time, y?, x?
      if(dim_count == 3):
        data = nc_data[:,Y,X]
        fig, axes = plt.subplots(1,1, sharex=args.sharex, sharey=args.sharey)
        axes.plot(time_range, data)


      # Variables by PFT, Compartment, or Layer
      # time, [section], y?, x?
      if(dim_count == 4):
        data = nc_data[:,:,Y,X]

        # By PFT only
        if 'pft' in nc_dims:
          fig, axes = plt.subplots(10,1, sharex=args.sharex, sharey=args.sharey)

          for pft in range(0,10):
            axes[pft].plot(time_range, data[:,pft])
            axes[pft].set_ylabel("pft" + str(pft))

        # By PFT compartment
        if 'pftpart' in nc_dims:
          fig, axes = plt.subplots(3,1, sharex=args.sharex, sharey=args.sharey)

          for pftpart in range(0,3):
            axes[pftpart].plot(time_range, data[:,pftpart])
            axes[pftpart].set_ylabel("pftpart " + str(pftpart))

        # By soil layer
        if 'layer' in nc_dims:
          if layer_end >= nc_data.shape[1]:
            print("ERROR! layer_end={} is out of range. max value for layer_end is: {}".format(layer_end, nc_data.shape[1]-1))
            sys.exit(-1)

          print("displaying layers {} -to-> {}".format(layer_start, layer_end))
          layers = list(range(layer_start, layer_end + 1))

          number_subplots = len(layers)
          if args.layer_sum:
            number_subplots +=1

          if args.hide_individual_layers:
            number_subplots = 1


          fig, axes = plt.subplots(number_subplots, 1,  sharex=args.sharex, sharey=args.sharey)

          # Use a dicrete map with one color for each layer
          # Helpful to have it be a sequential map also so that you can 
          # intuit layer depth from the color
          custom_cmap = plt.cm.get_cmap('plasma_r', len(layers))

          if args.layer_sum and not args.hide_individual_layers:
            sum_ax = axes[0]
            layer_axes = axes[1:]
          elif args.layer_sum and args.hide_individual_layers:
            sum_ax = axes
            layer_axes = []
          else:
            sum_ax = None
            layer_axes = axes

          # plot the individual layer lines each on their own ax
          if len(layers) != len(layer_axes):
            print("WARNING! length(layers){} != len(layer_axes){}".format(len(layers), len(layer_axes)))
          if args.hide_individual_layers:
            pass
          else:
            for i, (layer, ax) in enumerate(zip(layers, layer_axes)):
              #ax.plot(data[:,layer], color=custom_cmap(i))
              ax.fill_between(time_range, 0, data[:,layer], color=custom_cmap(i))
              ax.set_ylabel("L{:2d}".format(layer))


          if sum_ax is not None:
            # plot the basic sum line on the top (sum) ax
            sum_over_chosen_layers = data[:, layer_start:layer_end+1].sum(axis=1)
            sum_ax.plot(time_range, sum_over_chosen_layers, label='sum', color='lightgray')

            # plot the fill_betweens for layers on the top (sum) ax
            for i, layer in enumerate(layers):
              if layer == layer_end:
                lower_bound = np.ma.masked_array(np.zeros(data.shape[0]))
                upper_bound = data[:,layer:layer_end+1].sum(axis=1)
              else:
                lower_bound = data[:,layer+1:layer_end+1].sum(axis=1)
                upper_bound = data[:,layer:layer_end+1].sum(axis=1)

              clean_lower = np.where(lower_bound[:].mask, 0, lower_bound[:])
              clean_upper = np.where(upper_bound[:].mask, 0, upper_bound[:])

              #sum_ax.plot(time_range, clean_upper, color=custom_cmap(i))
              sum_ax.fill_between(time_range, clean_upper, clean_lower, color=custom_cmap(i))


      # Variables by both PFT and Compartment
      # time, pftpart, pft, y?, x?
      if(dim_count == 5):
        if args.pft is not None:
          pft_choice = args.pft
        else:
          pft_choice = 0 

        print("Plotting PFT: " + str(pft_choice))

        data = nc_data[:,:,pft_choice,Y,X]

        fig, axes = plt.subplots(3,1, sharex=args.sharex, sharey=args.sharey)
  
        for pftpart in range(0, 3):
          axes[pftpart].plot(data[:,pftpart])
          axes[pftpart].set_ylabel("pftpart " + str(pftpart))

      if args.annual_grid:
        try:
          _ = (a for a in axes) # just check that axes is a list.
          for ax in axes:
            ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(12))
            ax.grid()
        except TypeError:
          print(axes, 'is not iterable; setting grid on single axes instance')
          axes.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(12))
          axes.grid()


      # All variables share this section
      manager = plt.get_current_fig_manager()
      manager.set_window_title(plotting_var)
      plt.xlabel("time")
      plt.savefig("SAMPLE_plot_output_var.png")
      plt.show()


