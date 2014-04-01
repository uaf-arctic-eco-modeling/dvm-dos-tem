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
    
    plt.xlabel("Years")
    
    x = np.arange(0)
    y = x.copy() * np.nan
  
    logging.info("Setting up empty x,y data for every trace...")
    for trace in self.traces:
      ax = self.axes[ trace['axesnum'] ]
      trace['artists'] = ax.plot(x, y, label=trace['jsontag'])
    self.relim_autoscale_draw()
    self.grid_and_legend()
    
    self.loademupskis()
  
    logging.info("Done creating an expanding window plot object...")

  def init(self):
    logging.info("Init function for animation")

    return [trace['artists'][0] for trace in self.traces]




  def report_view_and_data_lims(self):
    logging.info("{0:-^56s}".format("Report Data and View Limits"))
    for i, ax in enumerate(self.axes):
      (dx0,dy0),(dx1,dy1) = ax.dataLim.get_points()
      (vx0,vy0),(vx1,vy1) = ax.viewLim.get_points()
      logging.info("{0:>10s} {1:>10.3f} {2:>10.3f} {3:>10.3f} {4:>10.3f}".format('Axes%i X:'%i, dx0,dx1, vx0,vx1))
      logging.info("{0:>10s} {1:>10.3f} {2:>10.3f} {3:>10.3f} {4:>10.3f}".format('Axes%i Y:'%i, dy0,dy1, vy0, vy1))



  def loademupskis(self):
    logging.info("LOAD 'EM UPSKIS!")
    
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
  
    # clean up temproary storage
    for trace in self.traces:
      del trace['tmpy']


    # ----- RElIMIT and SCALE
    self.relim_autoscale_draw()
    self.grid_and_legend()
    self.report_view_and_data_lims()
  
    logging.info("Done loading 'em upskis.")




  def update(self, frame):
    logging.info("Frame %7i" % frame)
    
    # get current data and view limits
    for i, ax in enumerate(self.axes):
      (dx0,dy0),(dx1,dy1) = ax.dataLim.get_points()
      (vx0,vy0),(vx1,vy1) = ax.viewLim.get_points()
    

    files = sorted( glob.glob('%s/*.json' % YRTMPDIR) )
    logging.info("%i json files in %s" % (len(files), YRTMPDIR) )
    
    if int( os.path.basename(files[-1])[0:4] ) > dx1:
      pass
      # the largest year file will not fit in the data container...
      # must resize, then try again
        
    else:
      pass
      # start at the last file and put it in the
    

    # create an x range big enough for every possible file...
    if len(files) == 0:
      x = np.arange(0)
    else:
      end = int( os.path.basename(files[-1])[0:4] )
      x = np.arange(0, end + 1 , 1) # <-- make range inclusive!

    self.report_view_and_data_lims()
    
    self.loademupskis()

    return [trace['artists'][0] for trace in self.traces]


  def relim_autoscale_draw(self):
    logging.debug("Relimit axes, autoscale axes.")
    for ax in self.axes:
      ax.relim()
      ax.autoscale()
    logging.info("Redraw plot")
    plt.draw()

  def grid_and_legend(self):
    logging.debug("Turn on grid and legend.")
    for ax in self.axes:
      ax.grid(True) # <-- w/o parameter, this toggles!!
      ax.legend(prop={'size':10})


  def show(self, dynamic=True):
    logging.info("Displaying plot, dynamic=%s" % dynamic)

    if dynamic:
      logging.info("Setup animation.")
      self.ani = animation.FuncAnimation(self.fig, self.update, interval=100,
                                       init_func=self.init, blit=True)
  
    plt.show()

      

  def describe_existing_axes_and_lines(self, detail=0):
    logging.debug("-- Axes and Lines Report ------------------------")
    for i, ax in enumerate(self.axes):
      logging.debug("  axes%i: %s" % (i, ax) )
      for j, line in enumerate(ax.lines):
        logging.debug("    line%i: %s" % (j, line) )
        if detail >= 1:
          x = line.get_xdata()
          if len(x) > 0:
            logging.debug("      x data (len %s): [%s..%s]" % (len(x), x[0], x[-1] ))
          y = line.get_ydata()
          if len(y) > 0:
            logging.debug("      y data(len %s): [%s..%s]" % (len(y), y[0], y[-1] ))
    logging.debug("-------------------------------------------------")

if __name__ == '__main__':

  logging.info("Setting up plot properties dictionary...")
  traces = [
    # axesnum: which sub plot to be on, 0 based
    { 'jsontag': 'GPPAll', 'axesnum': 0, 'pft': 'PFT0', },
    { 'jsontag': 'NPPAll', 'axesnum': 0, 'pft': 'PFT0', },

    { 'jsontag': 'GPPAllIgnoringNitrogen', 'axesnum': 1, 'pft': 'PFT0', },
    { 'jsontag': 'NPPAllIgnoringNitrogen', 'axesnum': 1, 'pft': 'PFT0', },

    { 'jsontag': 'PARAbsorb', 'axesnum': 2, 'pft': 'PFT0', },
    { 'jsontag': 'PARDown', 'axesnum': 2, 'pft': 'PFT0', },

    { 'jsontag': 'WaterTable', 'axesnum': 3, },

    { 'jsontag': 'MossdeathCarbon', 'axesnum': 4, },
    { 'jsontag': 'MossdeathNitrogen', 'axesnum': 4, },
  ]
  
  logging.info("Starting main app...")
 
  ewp = ExpandingWindow(traces, rows=5, cols=1)

  ewp.show(dynamic=True)
  
  logging.info("Done with main app...")







