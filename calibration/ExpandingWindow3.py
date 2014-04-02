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
    
    self.fig.canvas.mpl_connect('key_press_event', self.key_press_event)

    plt.xlabel("Years")
    
    x = np.arange(0)
    y = x.copy() * np.nan
  
    logging.info("Setting up empty x,y data for every trace...")
    for trace in self.traces:
      ax = self.axes[ trace['axesnum'] ]
      trace['artists'] = ax.plot(x, y, label=trace['jsontag'])
    self.relim_autoscale_draw()
    self.grid_and_legend()
    
    self.loademupskis(relim=True, autoscale=True)
  
    logging.info("Done creating an expanding window plot object...")


  def init(self):
    logging.info("Init function for animation")

    return [trace['artists'][0] for trace in self.traces]

  def loademupskis(self, relim, autoscale):
    log = logging.getLogger('dataloader')

    log.info("LOAD 'EM UPSKIS!")
    
    files = sorted( glob.glob('%s/*.json' % YRTMPDIR) )
    log.info("%i json files in %s" % (len(files), YRTMPDIR) )

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
    log.info("Read every file and load into trace['tmpy'] container")
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
    log.info("Load tmp data for every trace to trace's line")
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


    # ----- RELIMIT and SCALE
    if relim:
      log.info("Recomputing data limits based on artist data")
      for ax in self.axes:
        ax.relim()
    if autoscale:
      for ax in self.axes:
        ax.autoscale(enable=True, axis='both', tight=False)
      log.info("Force draw after autoscale")
      plt.draw()

    log.info("Done loading 'em upskis.")

  def update(self, frame):
    '''The animation updating function. Loads new data, but only upates view
    if the user is "zoomed out" (data limits are w/in view limits).
    
    Returns a list of artists to re-draw.
    '''
    logging.info("Animation Frame %7i" % frame)
    
    logging.debug("Listing json files in %s" % YRTMPDIR)
    files = sorted( glob.glob('%s/*.json' % YRTMPDIR) )
    logging.info("%i json files in %s" % (len(files), YRTMPDIR) )

    #self.report_view_and_data_lims()

    logging.debug("Collecting data/view limits.")
    for i, ax in enumerate(self.axes):
      (dx0,dy0),(dx1,dy1) = ax.dataLim.get_points()
      (vx0,vy0),(vx1,vy1) = ax.viewLim.get_points()

    logging.debug("Checking data and view limits.")
    if vx0 > dx0 or vx1 < dx1 or vy0 > dy0 or vy1 < dy1:
      logging.info("View limits are inside data limits. User must be zoomed in!")
      logging.info("Upate artists, recompute data limits, but don't touch the view.")
      self.loademupskis(relim=True, autoscale=False)
      return []  # nothing to re-draw when zoomed in.
    else:
      logging.info("Data limits are inside view limits. Load data and redraw.")
      self.loademupskis(relim=True, autoscale=True)
      return [trace['artists'][0] for trace in self.traces]

  def key_press_event(self, event):
    logging.debug("You pressed: %s. Cursor at x: %s y: %s" % (event.key, event.xdata, event.ydata))
    if event.key == 'ctrl+r':
      self.loademupskis(relim=True, autoscale=True)

  def relim_autoscale_draw(self):
    '''Relimit the axes, autoscale the axes, and try to force a re-draw.'''
    logging.debug("Relimit axes, autoscale axes.")
    for ax in self.axes:
      ax.relim()
      ax.autoscale(enable=True, axis='both', tight=False)
    logging.info("Redraw plot")
    try:
      plt.draw()
    except Exception as e:
      logging.error(e)

  def grid_and_legend(self):
    '''Turn on the grid and legend.'''
    logging.debug("Turn on grid and legend.")
    for ax in self.axes:
      ax.grid(True) # <-- w/o parameter, this toggles!!
      ax.legend(prop={'size':10.0})

  def show(self, dynamic=True):
    '''Show the figure. If dynamic=True, then setup an animation.'''
    logging.info("Displaying plot, dynamic=%s" % dynamic)

    if dynamic:
      logging.info("Setup animation.")
      self.ani = animation.FuncAnimation(self.fig, self.update, interval=100,
                                       init_func=self.init, blit=True)
  
    plt.show()

  def report_view_and_data_lims(self):
    '''Print a log report showing data and view limits.'''
    logging.debug("{0:>10s} {1:>10s} {2:>10s} {3:>10s} {4:>10s}".format('---','d0', 'd1', 'v0', 'v1'))
    for i, ax in enumerate(self.axes):
      (dx0,dy0),(dx1,dy1) = ax.dataLim.get_points()
      (vx0,vy0),(vx1,vy1) = ax.viewLim.get_points()
      logging.debug("{0:>10s} {1:>10.3f} {2:>10.3f} {3:>10.3f} {4:>10.3f}".format('Axes%i X:'%i, dx0,dx1, vx0,vx1))
      logging.debug("{0:>10s} {1:>10.3f} {2:>10.3f} {3:>10.3f} {4:>10.3f}".format('Axes%i Y:'%i, dy0,dy1, vy0, vy1))

  def describe_existing_axes_and_lines(self, detail=0):
    '''Print a log report describing all the axes and lines in the figure.'''
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

    { 'jsontag': 'LitterfallCarbonAll', 'axesnum': 4, 'pft': 'PFT0', },
    { 'jsontag': 'LitterfallNitrogenAll', 'axesnum': 4, 'pft': 'PFT0', },



# gotta figure out how to handle nan. maybe set to null on encoder side?
#    { 'jsontag': 'CarbonShallow', 'axesnum': 4, },
#    { 'jsontag': 'CarbonDeep', 'axesnum': 4, },
#    { 'jsontag': 'CarbonMineralSum', 'axesnum': 4, },

#    { 'jsontag': 'MossdeathCarbon', 'axesnum': 4, },
#    { 'jsontag': 'MossdeathNitrogen', 'axesnum': 4, },
  ]
  
  logging.info("Starting main app...")
 
  ewp = ExpandingWindow(traces, rows=5, cols=1)

  ewp.show(dynamic=True)
  
  logging.info("Done with main app...")







