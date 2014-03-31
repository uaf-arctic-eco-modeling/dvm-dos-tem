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
  
    #self.init()
    #self.default_empty_plot()

  
  def update(self, frame):
    logging.info("Frame %7i" % frame)
    return [trace['artists'][0] for trace in self.traces]

  
  def init(self):
    logging.info("Init function for animation")
    
    logging.info("Clear out all existing artists.")
    for ax in self.axes:
      ax.lines = []
    

    return [trace['artists'][0] for trace in self.traces]
  


  def init(self):
    lines2update = []
    for ax in self.axes:
      for line in ax.lines:
        lines2update.append(line)
    return lines2update

  def update(self, frame):
    pass
    logging.info("Frame %7i" % frame)

    #self.describe_existing_axes_and_lines()

    


    lines2update = []
    for ax in self.axes:
      for line in ax.lines:
        lines2update.append(line)
    return lines2update


  def plot_data_in_tmpdir(self):
    # get file listing
    files = sorted( glob.glob('%s/*.json' % YRTMPDIR) )
    
    if len(files) > 0:
      last_file_idx = int( os.path.basename(files[-1])[0:4])
      x = np.arange(0, last_file_idx + 1, 1) # inclusive of end point
    else:
      logging.info("No files present.")
      x = np.arange(0,1,1)
    
    for trace in self.traces:
      ax = self.axes[ trace['axesnum'] ]

      ax.lines = []

      y = x.copy() * np.nan

      for year in x:
        ffname = os.path.join(YRTMPDIR, '%04i.json'%(year))
        try:
          with open(ffname) as f:
            fdata = json.load(f)

          if 'pft' in trace.keys():
            pftdata = fdata[trace['pft']]
            y[year] = pftdata[trace['jsontag']]
          else:
            y[year] = fdata[ trace['jsontag'] ]

        except IOError as e:
          fdata = None
          logging.error("No such file!: %s"%ffname)
          logging.error(e)

      ax.plot(x, y, label=trace['jsontag'], animated=True)





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


def xRangeFromDirListing(files):
  '''Takes a file list, returns an inclusive, continuous range from the first
  to the last file. Does not check if files exist or anything. File names like
  this: 'YYYY*'
  
      x0, xn     result
      -------------------
      0, 0 --> [0]
      0, 1 --> [0, 1]
      0, 3 --> [0, 1, 2, 3]
      2, 2 --> [2]
      2, 5 --> [2, 3, 4, 5]
  '''
  x0 = int( (os.path.basename(files[0]))[0:4] )   # 0...n
  xn = int( (os.path.basename(files[-1]))[0:4] )  # n
  
  x = np.arange(x0, xn+1, 1)
  
  return x



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

#    { 'jsontag': 'VegCarbon', 'axesnum': 0, },
#    { 'jsontag': 'NPPAll', 'axesnum': 0, },
  ]
  
  logging.info("Defining which variables are pft specific...")
  perpftvars = ['GPPAll', 'NPPAll', 'PARAbsorb', 'PARDown']
  for trace in traces:
    if trace['jsontag'] in perpftvars:
      trace['pft'] = 'PFT0'
  
  logging.info("Starting main app...")
 
  ewp = ExpandingWindow(traces, rows=4, cols=1)

  #logging.info("First, load any existing data")
  #ewp.sync_trace_data_with_tmp_dir()

  ewp.plot_data_in_tmpdir()
  ewp.show(dynamic=True)
  
  logging.info("Done with main app...")







#####################################
  '''
  def sync_trace_data_with_tmp_dir(self):
    files = sorted( glob.glob('%s/*.json' % YRTMPDIR) )
    logging.info("%i json files in %s" % (len(files), YRTMPDIR) )
    if len(files) == 0:
      logging.debug("No files present...Nothing to do.")
    else:
      logging.info("Find the first and last indices of the existing files")
      fidx =  int( (os.path.basename(files[0]))[0:4] )   # "First index"
      lidx =  int( (os.path.basename(files[-1]))[0:4] )  # "Last index"

      logging.info("Make an xrange that can encompass all the files.")
      x = np.arange(lidx-fidx+1) # <- Careful! Assume fidx=0 lidx=11 (12 years)
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
        idx = int( (os.path.basename(file))[0:4] )
        try:
          with open(file) as f:
            fdata = json.load(f)
        except IOError as e:
          logging.error("Problem opening file: %s" % file)
          logging.error(e)

        for trace in self.traces:
          if 'pft' in trace.keys():
            pftdata = fdata[ trace['pft'] ]
            trace['tmpdata'][idx] = pftdata[trace['jsontag']]
          else:
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
        ax.autoscale(axis='x')
      self.pretty_ticks()
  '''

  '''
  def resize(self, percent=0.10):
    cxmin = self.axes[0].lines[0].get_xdata()[0]
    cxmax = self.axes[0].lines[0].get_xdata()[-1]
    logging.debug("Current x bounds: %s, %s" % (cxmin, cxmax))
    assert cxmax > cxmin, "The current x axis max bound must be greater than the min bound!"
    cursize = cxmax-cxmin
    newsize = int( cursize + percent*cursize )
    tmp_container = np.empty(newsize) * np.nan
    new_x = np.arange(1, len(tmp_container)+1)
    logging.debug("Current Size: %s. New Size: %s. Length new x: %s."%(cursize, newsize, len(new_x)))

    for ax in self.axes:
      for line in ax.lines:
        new_y = tmp_container.copy()
        new_y[0:len(line.get_ydata())] = line.get_ydata()
        line.set_data(new_x, new_y)

    for ax in self.axes:
      ax.relim()
      ax.autoscale()
  '''




  """
  def init_plot(self):
    # This seems to get called twice. Not sure why.
    logging.info("In init_plot. Doing nothing. What is this function for??")
    return [trace['artists'][0] for trace in self.traces]
  """
  '''
  def update_plot(self, frame):
    logging.info("Frame %8s" % frame)

    # get file listing
    files = sorted( glob.glob('%s/*.json' % YRTMPDIR) )

    if not ( len(files) > 0 ):
      logging.info("No files. Nothing to do.")
      return []

    x = xRangeFromDirListing(files)

    logging.info("%i files (year %i to %i)" % (len(files), x[0], x[-1]) )
    
    logging.info("Making a temporary container for each trace...")
    for trace in self.traces:
      trace['tmpdata'] = x.copy() * np.nan

    logging.info("Updating the temporary data container for trace...")
    for trace in self.traces:
      pft = 'pft' in trace.keys()
      logging.info("Working on trace: %s (pft variable?: %s)" % (trace['jsontag'], 'pft' in trace.keys()) )

      for file in files:
        with open(file) as f:
          fdata = json.load(f)

        idx = int( (os.path.basename(file))[0:4] )

        if 'pft' in trace.keys():
          pftdata = fdata[ trace['pft'] ]
          trace['tmpdata'][idx] = pftdata[ trace['jsontag'] ]
        else:
          trace['tmpdata'][idx] = fdata[ trace['jsontag'] ]
  
  

    logging.info("Checking if exising line (plot size? view?) has enough space to load data in tmp container...")
    for ax in self.axes:
      for line in ax.lines:
        for trace in self.traces:
          if not (trace['jsontag'] == line.get_label()):
            pass # not the right trace/line combo
          else:
            current_size = len( line.get_xdata() ) # No reason this should ever differ from get_ydata()?
            required_size = len( trace['tmpdata'] )

            logging.info("Line %s size x: %i. Trace %s tmpdata size: %i." % (line, current_size, trace['jsontag'], len(trace['tmpdata'])) )

            if not (current_size >= required_size):
              
              self.resize(percent=0.25)
            
            logging.info("Updating line data...")
            line.set_data(x, trace['tmpdata'])


    
    
    logging.info("Deleting the temporary data containers for each trace.")
    for trace in self.traces:
      del trace['tmpdata']
    
    logging.info("Returning a list of artists to update?")
    return [trace['artists'][0] for trace in self.traces]
  '''


#  def size_container_absolute(size=120):
#    x = np.arange(0, size+1)
#    y = np.empty(len(x)) * np.nan
#    for ax in self.axes:
#      placeholder = ax.plot(x, np.empty(len(x)) * np.nan)
#      placeholder.set_visible(False)
#  
#    for ax in self.axes:
#      ax.relim()
#      ax.autoscale()
#
#  def resize_container(percent=.25):
#    pass



  """
  def default_empty_plot(self, xrange=120):

    logging.debug("Creating a default, empty, set of plots with x range: %i" % xrange)
    self.describe_existing_axes_and_lines()

    # http://stackoverflow.com/questions/4981815/how-to-remove-lines-in-a-matplotlib-plot
    # this was kinda tricky. just calling ax.line.remove() didn't work!!
    logging.debug("Removing all existing lines for all axes.")
    for ax in self.axes:
      ax.lines = []

    #self.describe_existing_axes_and_lines()

    x = np.arange(1, xrange+1, 1)
    logging.debug("Created an xrange: %i -> %i" % (x[0], x[-1]) )

    logging.debug("Plot some junk data against x, so that autoscale will pick up the x range.")
    for trace in self.traces:
      ax = self.axes[ trace['axesnum'] ]
      logging.debug("Plotting %s on axes %s..." % (trace['jsontag'], ax) )
      trace['artists'] = ax.plot(x, np.sin(x), label=trace['jsontag'], animated=True)
  
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
  """
