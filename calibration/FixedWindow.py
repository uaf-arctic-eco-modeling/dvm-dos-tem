#!/usr/bin/env python

import os
import sys
import glob
import json
import logging
import time

if (sys.platform == 'darwin') and (os.name == 'posix'):
  # this is the only one that seems to work on Mac OSX with animation...
  import matplotlib
  matplotlib.use('TkAgg')


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

    self.fig = plt.figure(figsize=(8*1.3,6*1.3))
    for row in np.arange(1,self.sprows+1):
      for col in np.arange(1,self.spcols+1):
        #rows, columns, which plot
        self.fig.add_subplot(sprows,spcols,((row-1)*self.spcols+col))
    self.axes = self.fig.axes

    #figure and subplots
    #self.fig, self.axes = plt.subplots(sprows, spcols, sharex='col')
    self.fig.suptitle(figtitle)

    self.traces = traceslist
    self.setup_traces()
    #plt.setp([a.set_xlabel('') for a in self.axes[1:-self.spcols]], visible=False)

    #Prevents label/tick/plot overlapping
#    plt.subplots_adjust(bottom=0.09)
    #left, bottom, right, top, wspace, hspace
    plt.subplots_adjust(0.06,0.08,0.98,0.94,0.18,0.20)

    F = plt.gcf()
    DPI = F.get_dpi()
    DefaultSize = F.get_size_inches()
    print "DPI: ", DPI
    print "Default size: ", DefaultSize

    xinch = DefaultSize[0]
    yinch = DefaultSize[1]


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

############################################
    #x is supposed to be the length of json file list
    # fidx = selutil.jfname2idx(os.path.splitext(os.path.basename(jsonfiles[0]))[0])
    # lidx = selutil.jfname2idx(os.path.splitext(os.path.basename(jsonfiles[-1]))[0])
    # x = np.arange(max(self.viewport,lidx-fidx+1))
    # x = x+1
    # tmpdata = np.empty(len(x))*np.nan
    # for trace in self.traces:
    #   trace['tmpdata'] = tmpdata.copy()
    # for file in jsonfiles:
    #   idx = selutil.jfname2idx(os.path.splitext(os.path.basename(file))[0])
    #   with open(file) as f:
    #     fdata = json.load(f)
    #   for trace in self.traces:
    #     trace['tmpdata'][idx] = fdata[trace['jsontag']]
    # for ax in self.axes:
    #   for line in ax.lines:
    #     for trace in self.traces:
    #       if line.get_label() == trace['jsontag']:
    #         line.set_data(x, trace['tmpdata'])
    #       else:
    #         pass
    # for trace in self.traces:
    #   del trace['tmpdata']

    # for ax in self.axes:
    #   ax.relim()
    #   ax.autoscale(axis='y')
    #   ax.set_xlim(max(0,lidx-self.viewport),max(lidx,self.viewport))
    #   limits = ax.get_xlim()
    #   print limits
    #   #embed()

####################################################

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
    for ax in self.axes:
      ax.relim()
      ax.autoscale(axis='y')
      ymin, ymax = ax.yaxis.get_view_interval()
      #ax.set_ylim(ymin, ymax)
      #ax.autoscale_view(True,True,True)
    return [trace['artist'][0] for trace in self.traces]

  def setup_plot(self):
    '''Initial drawing of plot. Limits & labels set.'''
    fontP = FontProperties()
    fontP.set_size('x-small')
    for ax in self.axes:
      #ax.set_ylim(-30, 100)
      ax.set_xlim(1, self.viewport)
      ax.legend(prop = fontP, ncol=2,\
                bbox_to_anchor=(0.5,1.15), loc='upper center')
      box = ax.get_position()
    for ax in self.axes[-self.spcols:]:
      ax.set_xlabel('Months')#ylabel is per trace
    for ax in self.axes[0:-2]:
      ax.set_xticklabels('',visible=False)
    #legend(self.axes[0,1],"testing", loc=(0.85,0.65), prop=fontP)
    return [trace['artist'][0] for trace in self.traces]


  def setup_traces(self):
    logging.info("Setting up traces")
    empty_container = np.nan * np.empty(self.timerange)
    for trace in self.traces:
      logging.info("  data/tag: %s  -->  plot number %i" % (trace['jsontag'], trace['pnum']))
      trace['data'] = empty_container.copy()
      xindex = trace['pnum']/self.spcols
      yindex = trace['pnum']%self.spcols
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
    { 'jsontag': 'WaterTable', 'pnum': 1, 'unit': 'm', },
    { 'jsontag': 'VWCOrganicLayer', 'pnum': 2, 'unit': 'unit', },
    { 'jsontag': 'VWCMineralLayer', 'pnum': 2, 'unit': 'unit', },
    { 'jsontag': 'Evapotranspiration', 'pnum' : 3, 'unit': 'unit', 'ylims': [0,70]},
    { 'jsontag': 'ActiveLayerDepth', 'pnum': 4, 'unit': 'm', },
    { 'jsontag': 'TempAir', 'pnum': 5, 'unit': 'degrees C', },
    { 'jsontag': 'TempOrganicLayer', 'pnum': 5, 'unit': 'degrees C', },
    { 'jsontag': 'TempMineralLayer', 'pnum': 6, 'unit': 'degrees C', },
    { 'jsontag': 'Year', 'pnum': 7, 'unit': 'W/m2', },#placeholder for PAR
    #{ 'jsontag': '', 'pnum': , 'unit': 'unit', },
  ]

  logging.warn("Starting main app...")

  selutil.check_dir("/tmp/year-cal-dvmdostem")
  selutil.check_dir("/tmp/cal-dvmdostem")

  data_check = FixedWindow(traces, sprows=4, spcols=2, figtitle="Hydro/Thermal")
  data_check.show()
  
  logging.info("Done with main app...")

