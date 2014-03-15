#!/usr/bin/env python

import os
import glob
import json
import logging


import matplotlib
matplotlib.use('TkAgg')  # this is the only one that seems to work on Mac OSX
                         # with animation...

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import matplotlib.animation as animation



#from matplotlib.cbook import CallbackRegistry


from IPython import embed

import pdb

# The 'glob' that gets used to build a list of all json files.
TMPDIR = '/tmp/cal-dvmdostem/*.json'

# some logging stuff
LOG_FORMAT = '%(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

class CMF(object):
  ''' CMF - Calibration Monthly Figure.
  
  A generic figure that provides the general display and scaling for
  a dynamically updating "calibration plot" for dvm-dos-tem.
  '''
  
  def __init__(self, traceslist, timerange=120, sprows=4, spcols=1,
               figtitle="Empty plot..."):
    logging.debug("Initializing figure for timerange: %i (months)" % timerange)
    logging.debug("Plot rows: %i cols: %i" %(sprows, spcols))
    self.timerange = timerange
    self.sprows = sprows
    self.spcols = spcols

    self.fig, self.axes = plt.subplots(sprows, spcols ,sharex='all')
    self.fig.suptitle(figtitle)

    self.traces = traceslist

    self.setup_traces()

    self.ani = animation.FuncAnimation(self.fig, self.update, interval=100,
                                       init_func=self.setup_plot, blit=True)
    
  def setup_traces(self):
    '''Set all trace data to empty; assigns artist to subplot.'''
    logging.info("Setting up traces...")
    empty_container = np.nan * np.empty(self.timerange)
    for trace in self.traces:
      logging.info("  data/tag: %s  -->  plot number %i" % (trace['jsontag'], trace['pnum']))
      trace['data'] = empty_container.copy()
      trace['artist'] = self.axes[trace['pnum']].plot( [],[], label=trace['jsontag'] )
      

  def set_trace_artist_data(self):
    logging.debug("For each trace, setting the artist data to whatever is in the trace's data container.")
    for trace in self.traces:
      a = trace['artist'][0]  # <-- not sure why this is a list?
      a.set_data( np.arange(1, self.timerange + 1), trace['data'] )


  def manage_plot_size(self, json_file_list):
    logging.debug("Current number of json files: %7i" % len(json_file_list))
    try:
      # should probably have some try/catch stuff here to make sure we
      # pick up the right file listing...just skip if not
    
      if len(json_file_list) == 0:
        logging.warn("No Json files! Setting first and last indices to 0.")
        fjfi = 0
        ljfi = 0      
    
      elif len(json_file_list) > 0:
        fjfi = YYYY_MM2idx(  # "First Json File Index"
            os.path.splitext( os.path.basename(json_file_list[0]) )[0]
        )
        ljfi = YYYY_MM2idx(  # "Last Json File Index"
            os.path.splitext( os.path.basename(json_file_list[-1]) )[0]
        )
        logging.debug("First json file: %s (idx %i)" % (json_file_list[0], fjfi) )
        logging.debug("Last json file:  %s (idx %i)" % (json_file_list[-1], ljfi) )
    
      else:
        logging.warn("Not sure how you got here? Something must be wrong.")
    
      assert fjfi == 0, "The first json file must be 0000_00.json"
      assert ljfi == (len(json_file_list) - 1), "There must be missing json files!"
    
      logging.debug("Current plot timerange: %7i" % self.timerange)
      if ljfi >= self.timerange:
        logging.debug("Should expand containers: More json files than current timerange.")
        if ljfi >= (self.timerange + self.timerange*0.25):
          self.resize( size=ljfi + 1 ) # <-- Careful!
        else:
          self.resize( percent=0.25 )
        
        if not self.timerange >= ljfi:
          logging.debug("Hmm looks like we didn't make the containers big enough.")
                     
      elif ljfi < (0.5 * self.timerange):
        logging.debug("Should shrink containers: Json files exist for less than half of the timerange.")
        if self.timerange < 12:
          self.resize( size=12 )  # don't resize to < 12 months
        else:
          self.resize( size=max(ljfi, 120) )
      else:
        pass
    except AssertionError as ae:
      logging.warn(ae)


  def update(self, frame):
    '''Update the plots based on data in the /tmp/cal-dvmdostem directory...'''
    logging.info("Frame %7i" % frame)
    
    currentjsonfiles = glob.glob(TMPDIR)
    self.manage_plot_size(currentjsonfiles)
    
    for file in currentjsonfiles:
      idx = YYYY_MM2idx( os.path.splitext(os.path.basename(file))[0] )

      for trace in self.traces:
        if ( np.isnan(trace['data'][idx]) ):
          with open(file) as f:
            new_data = json.load(f)
          #logging.debug(new_data)
          trace['data'][idx] = new_data[ trace['jsontag'] ]
    
    # http://stackoverflow.com/questions/10368371/matplotlib-animated-plot-wont-update-labels-on-axis-using-blit
    for trace in self.traces:
      a = trace['artist'][0]
      a.set_data( np.arange(1, self.timerange+1), trace['data'])
    return [trace['artist'][0] for trace in self.traces]
    
  
  def setup_plot(self):
    '''Initial drawing of the plot'''
    logging.info("Drawing plot background and loading all existing data..??.")
    # load all existing data?
    
    # return list of trace artists to animate
    return [trace['artist'][0] for trace in self.traces]
    
  def resize(self, **kwargs):
    logging.debug("Resizing plots.") 
    if ('size' in kwargs) and ('percent' in kwargs):
      raise ValueError("Can't pass size and percent to resize function!")
    if 'size' in kwargs:
      s = kwargs['size']
      new_container = np.nan * np.empty(s)
    if 'percent' in kwargs:
      p = kwargs['percent']
      new_container = np.nan * np.empty(self.timerange + ( p * self.timerange) )

    self.timerange = new_container.size
    logging.debug("New timerange (months): %i" % self.timerange)
    assert len(new_container) == self.timerange, "Somehow the new container and plot's time range and not in sync."
  
    for trace in self.traces:
      new_trace = new_container.copy()
      if len(new_trace) >= len(trace['data']):
        logging.debug("Expanding. New size is greater than old size.")
        new_trace[0:len(trace['data']) ] = trace['data']
      else:
        logging.debug("Contracting. New size is less than old size.") 
        new_trace[:] = trace['data'][0:len(new_trace)]
      trace['data'] = new_trace
      
    logging.info("Setting x lim for all axes")
    for ax in self.axes:
      ax.set_xlim(1, self.timerange + 1)
    
    logging.info("Setting the xaxis ticks")
    self.set_xax_ticks()

    logging.info("Turning grid on")
    for ax in self.axes:
      ax.grid()
      
    logging.info("Force re-drawing the whole plot since we modified the axes etc.")
    plt.draw()

  def set_xax_ticks(self):
    # valid increments for tick marks in years
    yr_tks = [1, 5, 10, 20, 30, 40, 50, 75, 100, 200, 300, 400, 500, 750, 1000, 2000]

    # ideally ~7 ticks on the x axis
    ideal_yrs_per_tick = self.timerange / 7.0
    
    yr_locater_base = min(yr_tks, key=lambda x:abs(x-ideal_yrs_per_tick) )
    
    logging.debug("ideal tick spacing (yrs): %i" % ideal_yrs_per_tick)
    logging.debug("selected tickspacing (yrs): %i (%i months)" % (yr_locater_base, yr_locater_base*12.0))

    loc = mplticker.MultipleLocator( base=(yr_locater_base * 12) )
    
    for ax in self.axes:
      logging.debug("Setting major locators for axe %s" % ax)
      ax.xaxis.set_major_locator(loc)


  def show(self):
    logging.info("Starting animation.")
    plt.show()
      
      
def idx2YYYY_MMstr(idx):
  yr = int(idx / 12)  
  m = idx % 12
  return '%04i_%02i' % (yr, m)

def YYYY_MM2idx(str):
  '''Convert 'YYYY_MM' string to index, assuming year and month start at 0
     
     0000_00 --> index 0 (jan, year 0)
     0001_00 --> index 12 (jan of year 1)
     etc...
  '''
  year = int(str[0:4])
  month = int(str[5:])
  return (year * 12) + month

def on_xlim_changed(ax):
  logging.debug("x limit changed on axes: %s!" % ax)

      
if __name__ == '__main__':

  traces = [
    { 'jsontag': 'Rainfall', 'pnum': 0, },
    { 'jsontag': 'Snowfall', 'pnum': 0, },
    { 'jsontag': 'WaterTable', 'pnum': 1, },
  ]

  cmf = CMF(traces, sprows=2, figtitle="Monthly Hydro Plot")
  cmf.show()      
      
