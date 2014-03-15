#!/usr/bin/env python

import os
import glob
import json
import logging


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import matplotlib.animation as animation


#from matplotlib.cbook import CallbackRegistry


from IPython import embed

import pdb

# The 'glob' that gets used to build a list of all json files.
TMPDIR = '/tmp/cal-dvmdostem/*.json'
FORMAT = '%(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

class CMF(object):
  ''' CMF - Calibration Monthly Figure.
  
  A generic figure that provides the general display and scaling for
  a dynamically updating "calibration plot" for dvm-dos-tem.
  '''
  
  def __init__(self, traceslist, timerange=120, sprows=4, spcols=1):
    logging.debug("Initializing figure for timerange: %i (months)" % timerange)
    logging.debug("Plot rows: %i cols: %i" %(sprows, spcols))
    self.timerange = timerange
    self.sprows = sprows
    self.spcols = spcols

    self.fig, self.axes = plt.subplots(sprows, spcols ,sharex='all')
    self.fig.suptitle('%i empty plots...' % (sprows*spcols))

    self.traces = traceslist

    self.setup_traces()

    self.ani = animation.FuncAnimation(self.fig, self.update, interval=100,
                                       init_func=self.setup_plot, blit=True)
    
  def setup_traces(self):
    '''Set all trace data to empty; assigns artist to subplot.'''
    logging.debug("Setting up traces...")
    empty_container = np.nan * np.empty(self.timerange)
    for trace in self.traces:
      trace['data'] = empty_container.copy()
      trace['artist'] = self.axes[trace['pnum']].plot( [],[], label=trace['jsontag'] )
      



  def set_trace_artist_data(self):
    logging.debug("For each trace, setting the artist data to whatever is in the trace's data container.")
    for trace in self.traces:
      a = trace['artist'][0]  # <-- not sure why this is a list?
      a.set_data( np.arange(1, self.timerange + 1), trace['data'] )

  def update(self, frame):
    '''Update the plots based on data in the /tmp/ directory...'''
    logging.info("Animation Frame %7i" % frame)
    
    artists2update = []
    
    currentjsonfiles = glob.glob(TMPDIR)
    logging.debug("Current number of json files: %7i" % len(currentjsonfiles))
    
    if len(currentjsonfiles) == 0:
      logging.warn("No Json files! Setting first and last indices to 0. Plots will be empty.")
      fjfi = 0
      ljfi = 0      
    
    elif len(currentjsonfiles) > 0:
      fjfi = YYYY_MM2idx(  # "First Json File Index"
          os.path.splitext( os.path.basename(currentjsonfiles[0]) )[0]
      )
      ljfi = YYYY_MM2idx(  # "Last Json File Index"
          os.path.splitext( os.path.basename(currentjsonfiles[-1]) )[0]
      )
      logging.debug("First json file: %s (idx %i)" % (currentjsonfiles[0], fjfi) )
      logging.debug("Last json file:  %s (idx %i)" % (currentjsonfiles[-1], ljfi) )
    
    assert fjfi == 0, "The first json file should be 0000_00.json"
    assert ljfi == (len(currentjsonfiles) - 1), "There must be missing json files!"
    logging.debug("Current plot timerange: %7i" % self.timerange)

    if ljfi >= self.timerange:
      logging.debug("Should expand containers: More json files than current timerange.")
      artists2update += self.resize( percent=0.25 ) # increase by 25% 
                       #self.resize( size=200 )     # fixed sixe
    
    if ljfi < (0.5 * self.timerange):
      logging.debug("Should shrink containers: Json files exist for less than half of the timerange.")
      if self.timerange < 12:
        artists2update += self.resize( size=12 )  # don't resize to < 12 months
      else:
        artists2update += self.resize( size=self.timerange )
      
    logging.debug("Length of artists2update: %i Artists: %s" % \
        (len(artists2update), artists2update) )

    # http://stackoverflow.com/questions/10368371/matplotlib-animated-plot-wont-update-labels-on-axis-using-blit
    if not self.timerange >= ljfi:
      logging.debug("Hmm looks like we didn't make the containers big enough.")

    return []
    
  
  def setup_plot(self):
    '''Initial drawing of the plot'''
    logging.info("Drawing plot background and loading all existing data..??.")
    # load all existing data?
    
    # return list of trace artists to animate
    return [trace['artist'] for trace in self.traces]
    
  def resize(self, **kwargs):
    logging.debug("Resizing plots (containers, artists, axes, etc)") 
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
        logging.debug("Contracting. New size is less than old sixe.") 
        new_trace[:] = trace['data'][0:len(new_trace)]
      trace['data'] = new_trace
      

    # set artists data to trace data?
    self.set_trace_artist_data()

    for ax in self.axes:
      ax.set_xlim(1, self.timerange + 1)
    
    self.set_xax_ticks()
    
    for ax in self.axes:
      ax.grid()
    
    #self.set_all_axis_limits_and_tickers()
    return []

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

  cmf = CMF(traces)
  cmf.show()      
      
