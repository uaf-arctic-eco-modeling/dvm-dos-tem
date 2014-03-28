#!/usr/bin/env python

import os
import time
import sys
import glob
import json
import logging


if (sys.platform == 'darwin') and (os.name == 'posix'):
  # this is the only one that seems to work on Mac OSX with animation...
  import matplotlib
  matplotlib.use('TkAgg')

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import matplotlib.animation as animation

import selutil

from IPython import embed
import pdb

# The directory to look for json files.
TMPDIR = '/tmp/cal-dvmdostem'

# some logging stuff
LOG_FORMAT = '%(levelname)-7s %(name)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

class ExpandingWindow(object):
  '''An set of expanding window plots that all share the x axis.

  ???
  '''

  def __init__(self, traceslist, figtitle="Expanding Window Plot",
      rows=2, cols=1):

    logging.debug("Ctor for Expanding Window plot...")

    self.traces = traceslist

    self.fig, self.axes = plt.subplots(rows, cols, sharex='all')
    self.fig.suptitle(figtitle)

    self.default_empty_plot()

  def default_empty_plot(self, xrange=120):

    logging.debug("Creating a default, empty, set of plots with x range: %i" % xrange)
    self.describe_existing_axes_and_lines()

    logging.debug("Removing all existing lines for all axes.")
    # http://stackoverflow.com/questions/4981815/how-to-remove-lines-in-a-matplotlib-plot
    # this was kinda tricky. just calling ax.line.remove() didn't work!!
    for ax in self.axes:
      ax.lines = []

    self.describe_existing_axes_and_lines()

    x = np.arange(1, xrange+1, 1)
    logging.debug("Created an xrange: %i -> %i" % (x[0], x[-1]) )

    logging.debug("Plot some junk data so the autoscale will pick up the ranges.")
    for trace in self.traces:
      ax = self.axes[ trace['axesnum'] ]
      logging.debug("Plotting %s on axes %s..." % (trace['jsontag'], ax) )
      trace['artists'] = ax.plot(x, np.sin(x), label=trace['jsontag'])
  
    self.describe_existing_axes_and_lines()

    logging.debug("Auto scaling all x axes.")
    for ax in self.axes:
      ax.relim()
      ax.autoscale()

    logging.debug("Remove the junk data (set y data to nan).")
    for trace in self.traces:
      ax = self.axes[ trace['axesnum'] ]
      for artist in trace['artists']:
        artist.set_ydata(np.nan*x)
  
    logging.debug("Turning on legend")
    for ax in self.axes:
      ax.legend()

    self.pretty_ticks()



  def pretty_ticks(self):
    logging.info("Try to setup tick marks so they only fall on easy-to-comprehend month/year intervals...")
    acceptable_tic_locs_yrs = (1,5,10,20,30,40,50,75,100,200,300,400,500,750,1000,2000,3000,4000)
    acceptable_tic_locs_months = [yrs * 12 for yrs in acceptable_tic_locs_yrs ]
    num_visible_ticks = 7
    ideal_months_per_tick = (self.axes[0].get_xbound()[1] - self.axes[0].get_xbound()[0]) / num_visible_ticks
    locater_base = min(acceptable_tic_locs_months, key=lambda v: abs(v-ideal_months_per_tick))

    logging.debug("x axis bounds: %i -> %i" % ( self.axes[0].get_xbound()[0], self.axes[0].get_xbound()[1] ) )
    logging.debug("ideal # of months per tick mark: %i" % ideal_months_per_tick )
    logging.debug("chosen # of months per tick mark: %i" % locater_base )


    loc = mplticker.MultipleLocator(base=locater_base)

    for ax in self.axes:
      ax.xaxis.set_major_locator(loc)
      ax.grid()




  def init_plot(self):
    # This seems to get called twice. Not sure why.
    logging.info("In init_plot. Doing nothing. What is this function for??")
    return [trace['artists'][0] for trace in self.traces]

  def update_plot(self, frame):
    logging.info("Frame %8s" % frame)
    
    self.sync_trace_data_with_tmp_dir() 
    #logging.info("Returning a list of artists to get re-drawn.")
    return [trace['artists'][0] for trace in self.traces]

  def show(self, dynamic=True):
    if dynamic:
      logging.info("Showing DYNAMIC plot (animation)...")
      self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=100,
                                       init_func=self.init_plot, blit=True)
    else:
      logging.info("Showing STATIC plot...")

    plt.show()


  def sync_trace_data_with_tmp_dir(self):
    files = sorted( glob.glob('%s/*.json' % TMPDIR) )
    logging.info("%i json files in %s" % (len(files), TMPDIR) )
    if len(files) == 0:
      logging.debug("No files present...Nothing to do.")
    else:
      logging.info("Find the first and last indices of the existing files")
      fidx = selutil.jfname2idx( os.path.basename(files[0]) )  # "First index"
      lidx = selutil.jfname2idx( os.path.basename(files[-1]) ) # "Last index"

      logging.info("Make an xrange that can encompass all the files.")
      x = np.arange(lidx-fidx+1) # <- Careful! Assume fidx=0 lidx=11 (one year)
                                 # lidx-fidx -> 11, np.arange(11) ->  [0...10]
                                 # hence need to add 1.

      x = x+1                    # make the x range be one based [1...12]

      logging.info("Make temporary data containers for each trace.")
      tmpdata = np.empty(len(x))*np.nan
      assert len(x) == len(tmpdata)
      for trace in self.traces:
        trace['tmpdata'] = tmpdata.copy()

      logging.info("Now look at each file and for each trace, load the right data into the temporary data container.")
      for file in files:
        idx = selutil.jfname2idx( os.path.basename(file) )
        try:
          with open(file) as f:
            fdata = json.load(f)
        except IOError as e:
          logging.error("Problem opening file: %s" % file)
          logging.error(e)


        for trace in self.traces:
          trace['tmpdata'][idx] = fdata[trace['jsontag']]

      logging.info("Now look at all the plotted lines and find (based on the line's label) the right tmp data container.")
      logging.info("Then set the line's ydata to the data container, and the x data to the x we just built (should be ")
      logging.info("enough to span the range between the start and end file, even if there are missing files)")
      for ax in self.axes:
        for line in ax.lines:
          for trace in self.traces:
            if line.get_label() == trace['jsontag']:
              logging.debug("Setting x and y data for %s" % trace['jsontag'])
              line.set_data(x, trace['tmpdata'])
            else:
              pass

      logging.info("Clean up the temporary data containers for each trace")
      for trace in self.traces:
        del trace['tmpdata']

      logging.info("Auto scale the axes...")
      for ax in self.axes:
        ax.relim()
        ax.autoscale(axis='y')
        


      

  def describe_existing_axes_and_lines(self):
    logging.debug("-- Axes and Lines Report ------------------------")
    for i, ax in enumerate(self.axes):
      logging.debug("  axes%i: %s" % (i, ax) )
      for j, line in enumerate(ax.lines):
        logging.debug("    line%i: %s" % (j, line) )
    logging.debug("-------------------------------------------------")





if __name__ == '__main__':

  traces = [
    # axesnum: which sub plot to be on, 0 based
    { 'jsontag': 'Rainfall', 'axesnum': 0,  },
    { 'jsontag': 'Snowfall', 'axesnum': 0, },
    { 'jsontag': 'WaterTable', 'axesnum': 1, },
  ]
  logging.info("Starting main app...")
 
  ewp = ExpandingWindow(traces)
  
  
  ewp.sync_trace_data_with_tmp_dir()
  
  
  ewp.show(dynamic=True)
  
  logging.info("Done with main app...")

