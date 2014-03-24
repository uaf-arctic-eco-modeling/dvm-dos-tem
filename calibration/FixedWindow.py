#!/usr/bin/env python

import os
import glob
import json
import logging
import time

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.font_manager import FontProperties

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
    self.fig, self.axes = plt.subplots(sprows, spcols, sharex='col')
    self.fig.suptitle(figtitle)


    self.traces = traceslist
    self.setup_traces()
#    for row in np.arange(0,3):
#      plt.setp([a.set_xlabel('') for a in self.axes[row, :]], visible=False)

    #Prevents label/tick/plot overlapping
#    self.fig.set_size_inches(9., 7., Forward=True)
#    self.fig.set_dpi(90)
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.09)

    F = plt.gcf()
    DPI = F.get_dpi()
    DefaultSize = F.get_size_inches()
    print "DPI: ", DPI
    print "Default size: ", DefaultSize

    self.ani = animation.FuncAnimation(self.fig, self.update, interval=100,
                                       init_func=self.setup_plot, blit=True)


  def update(self, frame):
    '''Update plots from all json files in /tmp/cal-dvmdostem/'''
    logging.info("Frame %7i" %frame)

    #wait until there are files?
    while True:
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
    fontP = FontProperties()
    fontP.set_size('x-small')
    for row in self.axes:
      for ax in row:
        ax.set_ylim(-30, 100)
        ax.set_xlim(1, self.viewport)
        ax.set_xlabel('Months') #ylabel is per trace
        ax.legend(prop = fontP)
    return [trace['artist'][0] for trace in self.traces]


  def setup_traces(self):
    logging.info("Setting up traces")
    empty_container = np.nan * np.empty(self.timerange)
    for trace in self.traces:
      logging.info("  data/tag: %s  -->  plot number %i" % (trace['jsontag'], trace['pnum']))
      trace['data'] = empty_container.copy()
      xindex = trace['pnum']/self.spcols
      yindex = trace['pnum']%self.spcols
      trace['artist'] = self.axes[xindex,yindex].plot([],[], label=trace['jsontag'])
      #This will overwrite if the traces have different units. Possible?
      self.axes[xindex,yindex].set_ylabel(trace['unit'])


  def show(self):
    logging.info("Beginning render")
    plt.show()


if __name__ == '__main__':

  traces = [
    # pnum: which sub plot to be on, 0 based  
    { 'jsontag': 'Rainfall', 'pnum': 0, 'unit': 'mm', },
    { 'jsontag': 'Snowfall', 'pnum': 0, 'unit': 'mm', },
    { 'jsontag': 'WaterTable', 'pnum': 1, 'unit': 'unit', },
    { 'jsontag': 'VWCOrganicLayer', 'pnum': 2, 'unit': 'unit', },
    { 'jsontag': 'VWCMineralLayer', 'pnum': 2, 'unit': 'unit', },
    { 'jsontag': 'Evapotranspiration', 'pnum' : 3, 'unit': 'unit', },
    { 'jsontag': 'ActiveLayerDepth', 'pnum': 4, 'unit': 'unit', },
    { 'jsontag': 'TempAir', 'pnum': 5, 'unit': 'unit', },
    { 'jsontag': 'TempOrganicLayer', 'pnum': 5, 'unit': 'unit', },
    { 'jsontag': 'TempMineralLayer', 'pnum': 6, 'unit': 'unit', },
    { 'jsontag': 'Year', 'pnum': 7, 'unit': 'unit', },
    #{ 'jsontag': '', 'pnum': , 'unit': 'unit', },
  ]

  logging.warn("Starting main app...")

  data_check = FixedWindow(traces, sprows=4, spcols=2, figtitle="Hydro/Thermal")
  data_check.show()
  
  logging.info("Done with main app...")

