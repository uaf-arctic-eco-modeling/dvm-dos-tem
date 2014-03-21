#!/usr/bin/env python

import os
import glob
import json
import logging
import time

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import selutil

from IPython import embed


# The directory to look for json files.
TMPDIR = '/tmp/cal-dvmdostem'

# some logging stuff
LOG_FORMAT = '%(levelname)-7s %(name)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

class FixedWindow(object):
  def __init__(self, traceslist, timerange=1212, viewport=240, sprows=1,
               spcols=1, figtitle="Placeholder"):
    #initialize limits
    self.timerange = timerange
    self.sprows = sprows
    self.spcols = spcols
    self.viewport = viewport

    #figure and subplots
    self.fig, self.axes = plt.subplots(sprows, spcols, sharex='all')
    self.fig.suptitle(figtitle)

    self.traces = traceslist
    self.setup_traces()

    for ax in self.axes:
      ax.legend()

    self.ani = animation.FuncAnimation(self.fig, self.update, interval=100,
                                       init_func=self.setup_plot, blit=True)


  def update(self, frame):
    '''Update plots from all json files in /tmp/cal-dvmdostem/'''
    logging.info("Frame %7i" %frame)

    #wait until there are files?
    #ok, this is ugly - need to fabricate a do-while somehow...
    while True:
#      print "no files"
      time.sleep(.1)#seconds
      jsonfiles = sorted(glob.glob(TMPDIR + "/*.json"))
      if len(jsonfiles) > 0:
        break

    selutil.assert_zero_start(jsonfiles)
    idx = 0

    for file in jsonfiles:
      idx = selutil.jfname2idx(os.path.splitext(os.path.basename(file))[0])
      for trace in self.traces:
        try:
          if(np.isnan(trace['data'][idx])):
            with open(file) as f:
              try:
                new_data = json.load(f)
              except ValueError as ex:
                pass
                #embed()#rar
            trace['data'][idx] = new_data[trace['jsontag']]
        except IndexError as e:
          logging.error("Index out of bounds")
          logging.error("Length of data container: %i"%len(trace['data']))
          logging.error("Index: %i"%idx)

    for trace in self.traces:
      a = trace['artist'][0]
      artistlength = min(idx, self.viewport)
      #Allow for there to be fewer data points than the width of the viewport
      a.set_data(np.arange(1, artistlength+1),
                 trace['data'][max(0,idx-self.viewport):idx])
    return [trace['artist'][0] for trace in self.traces]

  def setup_plot(self):
    '''Initial drawing of plot. Limits & labels set.'''
    for ax in self.axes:
      ax.set_ylim(0, 200)
      ax.set_xlim(1, self.viewport)
      ax.set_xlabel('Months') #ylabel is per trace
      ax.legend()
    return [trace['artist'][0] for trace in self.traces]


  def setup_traces(self):
    logging.info("Setting up traces")
    empty_container = np.nan * np.empty(self.timerange)
    for trace in self.traces:
      logging.info("  data/tag: %s  -->  plot number %i" % (trace['jsontag'], trace['pnum']))
      trace['data'] = empty_container.copy()
      trace['artist'] = self.axes[trace['pnum']].plot([],[], label=trace['jsontag'])
      #This will overwrite if the traces have different units. Possible?
      self.axes[trace['pnum']].set_ylabel(trace['unit'])


  def show(self):
    logging.info("Beginning render")
    plt.show()
  


if __name__ == '__main__':

  traces = [
    # pnum: which sub plot to be on, 0 based  
    { 'jsontag': 'Rainfall', 'pnum': 0, 'unit': 'mm', },
    { 'jsontag': 'Snowfall', 'pnum': 0, 'unit': 'mm', },
    { 'jsontag': 'WaterTable', 'pnum': 1, 'unit': 'unit', },
  ]

  logging.warn("Starting main app...")

  data_check = FixedWindow(traces, sprows=2, figtitle="Stuff")
  data_check.show()
  
  #testing that the module importing works...
  selutil.jfname2idx('0000_00.json')
  
  logging.info("Done with main app...")

