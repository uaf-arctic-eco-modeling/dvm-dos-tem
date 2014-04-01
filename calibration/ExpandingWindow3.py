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
YRTMPDIR = '/tmp/year-cal-dvmdostem'

# some logging stuff
LOG_FORMAT = '%(levelname)-7s %(name)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

class ExpandingWindow(object):
  '''An set of expanding window plots that all share the x axis.
  '''

  def __init__(self, traceslist, figtitle="Expanding Window Plot",
      rows=2, cols=1):

    logging.debug("Ctor for Expanding Window plot...")

    self.traces = traceslist

    self.fig, self.axes = plt.subplots(rows, cols, sharex='all')
    self.fig.suptitle(figtitle)
  
    x = np.arange(0)
    y = x.copy() * np.nan
  
    for trace in self.traces:
      ax = self.axes[ trace['axesnum'] ]
      trace['artists'] = ax.plot(x, y, label=trace['jsontag'], animated=True)
    
    logging.info("Relimiting and autoscaling...")
    for ax in self.axes:
      ax.relim()
      ax.autoscale()
      ax.grid()
      ax.legend()
    
    logging.info("Done creating an expanding window plot object...")

  def init(self):
    logging.info("Init function for animation")
    
    return [trace['artists'][0] for trace in self.traces]

  def update(self, frame):
    logging.info("Frame %7i" % frame)
    
    axvlm = []
    
    logging.info("----------before update-------------------")
    for ax in self.axes:
      logging.info(ax.viewLim)
      axvlm.append(ax.viewLim)
    logging.info("------------------------------------------")
    
    
    files = sorted( glob.glob('%s/*.json' % YRTMPDIR) )
    logging.info("%i json files in %s" % (len(files), YRTMPDIR) )

    # create an x range big enough for every possible file...
    if len(files) == 0:
      x = np.arange(0)
    else:
      end = int( os.path.basename(files[-1])[0:4] )
      x = np.arange(0, end + 1 , 1) # <-- make range inclusive!
    
    # for each trace, create a tmp y container the same size as x
    for trace in self.traces:
      trace['tmpy'] = x.copy() * np.nan
    
    # ----- READ EVERY FILE --------
    logging.info("Read every file and load into trace['tmpy'] container")
    for file in files:
      # try reading the file
      try:
        with open(file) as f:
          fdata = json.load(f)
      except IOError as e:
        logging.error(e)
      
      idx = int(os.path.basename(file)[0:4])

      for trace in self.traces:
        # set the trace's tmpy[idx] to file's data
        if 'pft' in trace.keys():
          pftdata = fdata[trace['pft']]
          trace['tmpy'][idx] = pftdata[trace['jsontag']]
        else:
          trace['tmpy'][idx] = fdata[trace['jsontag']]

      
    # ----- UPDATE EVERY TRACE --------
    logging.info("Load tmp data for every trace to trace's line")
    for trace in self.traces:
      # find the line with the right label
      for line in self.axes[trace['axesnum']].lines:
        # set the line's data to x, and the trace's tmp data
        if line.get_label() == trace['jsontag']:
          line.set_data(x, trace['tmpy'])
        else:
          pass # wrong line...
  
    #self.pretty_ticks()
  
    # clean up temproary storage
    for trace in self.traces:
     del trace['tmpy']
    
    for ax in self.axes:
      ax.relim()
      ax.autoscale()
    
    logging.info("----------after update-------------------")
    for i, ax in enumerate(self.axes):
      logging.info("axes %i: %s" % (i, axvlm[i]))
      logging.info("axes %i: %s" % (i, ax.viewLim))

      if axvlm[i] != ax.viewLim:
        logging.info("Need to re-draw!!")
        ax.relim()
        ax.autoscale()
        plt.draw()
    logging.info("------------------------------------------")

    
    return [trace['artists'][0] for trace in self.traces]

  def pretty_ticks(self):
    logging.info("Try to setup tick marks so they only fall on easy-to-comprehend month/year intervals...")
    acceptable_tic_locs_yrs = (1,5,10,20,30,40,50,75,100,200,300,400,500,750,1000,2000,3000,4000)
    #acceptable_tic_locs_months = [yrs * 12 for yrs in acceptable_tic_locs_yrs ]
    num_visible_ticks = 7
    ideal_yrs_per_tick = (self.axes[0].get_xbound()[1] - self.axes[0].get_xbound()[0]) / num_visible_ticks
    locater_base = min(acceptable_tic_locs_yrs, key=lambda v: abs(v-ideal_yrs_per_tick))

    logging.debug("x axis bounds: %i -> %i" % ( self.axes[0].get_xbound()[0], self.axes[0].get_xbound()[1] ) )
    logging.debug("ideal # of years per tick mark: %i" % ideal_yrs_per_tick )
    logging.debug("chosen # of yrs per tick mark: %i" % locater_base )


    loc = mplticker.MultipleLocator(base=locater_base)

    for ax in self.axes:
      ax.xaxis.set_major_locator(loc)
      ax.grid()





  def show(self, dynamic=True):
    logging.info("Displaying plot with dynamic=%s" % dynamic)

    if dynamic:
      logging.info("Setup animation.")
      self.ani = animation.FuncAnimation(self.fig, self.update, interval=100,
                                       init_func=self.init, blit=True)
  
    plt.show()

      

  def describe_existing_axes_and_lines(self):
    logging.debug("-- Axes and Lines Report ------------------------")
    for i, ax in enumerate(self.axes):
      logging.debug("  axes%i: %s" % (i, ax) )
      for j, line in enumerate(ax.lines):
        logging.debug("    line%i: %s" % (j, line) )
    logging.debug("-------------------------------------------------")

if __name__ == '__main__':

  logging.info("Setting up plot properties dictionary...")
  traces = [
    # axesnum: which sub plot to be on, 0 based
    { 'jsontag': 'GPPAll', 'axesnum': 0, },
    { 'jsontag': 'NPPAll', 'axesnum': 0, },

    { 'jsontag': 'PARAbsorb', 'axesnum': 1, },
    { 'jsontag': 'PARDown', 'axesnum': 1, },

    { 'jsontag': 'Rainfall', 'axesnum': 2, },
    { 'jsontag': 'Snowfall', 'axesnum': 2, },
    
    { 'jsontag': 'WaterTable', 'axesnum': 3, },

    #{ 'jsontag': 'VegCarbon', 'axesnum': 0, },
    #{ 'jsontag': 'NPPAll', 'axesnum': 0, },
  ]
  
  logging.info("Defining which variables are pft specific...")
  perpftvars = ['GPPAll', 'NPPAll', 'PARAbsorb', 'PARDown']
  for trace in traces:
    if trace['jsontag'] in perpftvars:
      trace['pft'] = 'PFT0'
  
  logging.info("Starting main app...")
 
  ewp = ExpandingWindow(traces, rows=4, cols=1)

  ewp.show(dynamic=True)
  
  logging.info("Done with main app...")







