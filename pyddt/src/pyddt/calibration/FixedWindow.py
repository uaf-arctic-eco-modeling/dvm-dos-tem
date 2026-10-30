#!/usr/bin/env python

import os
import sys
import glob
import json
import logging
import time
import math
import argparse
import signal #for graceful exit

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
  def __init__(self, traceslist, startidx=0, timerange=1212, viewport=240,\
               sprows=1, spcols=1, figtitle="Placeholder Title",\
               suptitle="Placeholder suptitle"): 
    #initialize limits
    self.timerange = timerange
    self.sprows = sprows
    self.spcols = spcols
    self.viewport = viewport
    self.startidx = startidx

    self.fig = plt.figure(figsize=(8*1.3,6*1.3))
    self.fig.canvas.set_window_title(figtitle)
    self.fig.suptitle(suptitle)

    #Initialize plots
    for row in np.arange(1,self.sprows+1):
      for col in np.arange(1,self.spcols+1):
        #rows, columns, which plot
        self.fig.add_subplot(sprows,spcols,((row-1)*self.spcols+col))
    self.axes = self.fig.axes

    #Prevents label/tick/plot overlapping
    #left, bottom, right, top, wspace, hspace
    #.09 left should allow units to show even if tick labels are wide (-x.xx)
    plt.subplots_adjust(0.09,0.08,0.98,0.94,0.18,0.20)

    #figure and subplots
    #self.fig, self.axes = plt.subplots(sprows, spcols, sharex='col')

    self.traces = traceslist
    self.setup_traces()
    #plt.setp([a.set_xlabel('') for a in self.axes[1:-self.spcols]], visible=False)


    self.ani = animation.FuncAnimation(self.fig, self.update, interval=100,
                                       init_func=self.setup_plot, blit=True)


  def update(self, frame):
    '''Update plots from json files in /tmp/cal-dvmdostem/'''
    logging.info("Frame %7i" %frame)

    #wait until there are files
    while True:
      jsonfiles = glob.glob(TMPDIR + "/*.json")
      if len(jsonfiles) > 0:
        break
      time.sleep(.1)#seconds

    idx = 0
    newvalues = 0
    redraw_needed = False;#Used to determine if y-axis limits have changed.

    for i in np.arange(0,self.timerange):
      file = TMPDIR + '/' + selutil.idx2jfname(self.startidx+i)
      #print file
      for trace in self.traces:
        try:
          if(np.isnan(trace['data'][i])):
            try:
              while not os.path.isfile(file):
                time.sleep(.1)
              #print file
              with open(file) as f:
                try:
                  new_data = json.load(f)
                except ValueError as ex:
                  pass
              trace['data'][i] = new_data[trace['jsontag']]
              newvalues += 1
            except IOError as e:
              print("file doesn't exist")

            #extract PAR per PFT data. This may not be necessary for now.
            ################################
            # if new_data['Month'] == 7: #July
            #   PARA_perPFT = []
            #   PARD_perPFT = []
            #   for i in np.arange(0,9+1):
            #     PARA_perPFT.append(new_data['PFT' + str(i)]['PARAbsorb'])
            #     PARD_perPFT.append(new_data['PFT' + str(i)]['PARDown'])
            #   PARA_month_total = math.fsum(PARA_perPFT)
            #   PARD_month_total = math.fsum(PARD_perPFT)
            #   PARA_month_percent = [(val / PARA_month_total)*100 for val in PARA_perPFT]
            #   PARD_month_percent = [(val / PARD_month_total)*100 for val in PARD_perPFT]
            ################################
        except IndexError as e:
          logging.error("Index out of bounds")
          logging.error("Length of data container: %i"%len(trace['data']))
          logging.error("Index: %i"%idx)
          embed()
      #To create a 'scrolling' effect
      if (newvalues/len(self.traces)) >= 15:
        newvalues = 0
        break

    # for file in jsonfiles:
    #   idx = selutil.jfname2idx(os.path.splitext(os.path.basename(file))[0])
    #   modidx = idx-self.startidx
    #   if idx >= self.startidx and idx < self.startidx+self.timerange:
    #     for trace in self.traces:
    #       try:
    #         if(np.isnan(trace['data'][modidx])):
    #           with open(file) as f:
    #             try:
    #               new_data = json.load(f)
    #             except ValueError as ex:
    #               pass
    #           trace['data'][modidx] = new_data[trace['jsontag']]
    #           #extract PAR per PFT data. This may not be necessary for now.
    #           ################################
    #           # if new_data['Month'] == 7: #July
    #           #   PARA_perPFT = []
    #           #   PARD_perPFT = []
    #           #   for i in np.arange(0,9+1):
    #           #     PARA_perPFT.append(new_data['PFT' + str(i)]['PARAbsorb'])
    #           #     PARD_perPFT.append(new_data['PFT' + str(i)]['PARDown'])
    #           #   PARA_month_total = math.fsum(PARA_perPFT)
    #           #   PARD_month_total = math.fsum(PARD_perPFT)
    #           #   PARA_month_percent = [(val / PARA_month_total)*100 for val in PARA_perPFT]
    #           #   PARD_month_percent = [(val / PARD_month_total)*100 for val in PARD_perPFT]
    #           ################################
    #       except IndexError as e:
    #         logging.error("Index out of bounds")
    #         logging.error("Length of data container: %i"%len(trace['data']))
    #         logging.error("Index: %i"%idx)
    #         embed()
   
    for trace in self.traces:
      a = trace['artist'][0]
      artistlength = min(i, self.viewport)
      #Allow for there to be fewer data points than the width of the viewport
      try:
        a.set_data(np.arange(1, artistlength+1),
                 trace['data'][max(0,i-self.viewport):i])
        #print str(i-self.viewport) + "    " + str(i)
      except RuntimeError as e:
        print("x and y are different lengths")
        embed()

    for ax in self.axes:
      ax.relim()
      #y-axis
      ymin_pre, ymax_pre = ax.yaxis.get_view_interval()
      ax.autoscale(axis='y')
      ylims_post = ax.yaxis.get_view_interval()
      if (ymin_pre!=ylims_post[0] or ymax_pre!=ylims_post[1]):
        redraw_needed = True
      #x-axis
      xmin_pre, xmax_pre = ax.xaxis.get_view_interval()
      #print str(xmin_pre) + "  " + str(xmax_pre)
      ax.set_xlim()

    if redraw_needed:
      plt.draw()
    
    return [trace['artist'][0] for trace in self.traces]


  def setup_plot(self):
    '''Initial drawing of plot. Limits & labels set.'''
    fontP = FontProperties()
    fontP.set_size('x-small')
    for ax in self.axes:
      ax.set_xlim(0, self.viewport) #rar TODO not sure what to do here
      ax.legend(prop = fontP, ncol=2,\
                bbox_to_anchor=(0.5,1.15), loc='upper center')
      box = ax.get_position()
    for ax in self.axes[-self.spcols:]:
      ax.set_xlabel('Years')#ylabel is per trace
    #For neatness and visibility
    #for ax in self.axes[0:-self.spcols]:
    for ax in self.axes:
      ax.set_xticklabels('',visible=False)
    return [trace['artist'][0] for trace in self.traces]


  def setup_traces(self):
    logging.info("Setting up traces")
    empty_container = np.nan * np.empty(self.timerange)
    for trace in self.traces:
      logging.info("  data/tag: %s  -->  plot number %i"%(trace['jsontag'], trace['pnum']))
      trace['data'] = empty_container.copy()
      #xindex = trace['pnum']/self.spcols
      #yindex = trace['pnum']%self.spcols
      trace['artist'] = self.axes[trace['pnum']].plot([],[],\
                                                      label=trace['jsontag'])
      #This will overwrite if the traces have different units. Possible?
      self.axes[trace['pnum']].set_ylabel(trace['unit'])


  def show(self):
    logging.info("Beginning render")
    plt.show()


def exit_gracefully(signum, frame):
  sys.exit(1)

if __name__ == '__main__':

  original_sigint = signal.getsignal(signal.SIGINT)
  signal.signal(signal.SIGINT, exit_gracefully)

  def positive_int(year):
    year = int(year)
    if year < 0:
      raise argparse.ArgumentTypeError("startyear must be positive.")
    return year

  parser = argparse.ArgumentParser()
  group = parser.add_mutually_exclusive_group()

  group.add_argument('--startyear', default=0, type=positive_int,\
                      help="Which year to start display at.")

  group.add_argument('--end', action='store_true',\
                      help="Display the last 100 years. (Static)")

  parser.add_argument('--data', action='store_true',\
                      help="For now, trigger display of NPP/GPP.")

  args = parser.parse_args()

  #Set default.
  startidx = 0

  if args.startyear:
    startidx = args.startyear*12

  if args.end:
    jsonfiles = sorted(glob.glob(TMPDIR + "/*.json"))
    if len(jsonfiles) == 0:
      print("Must have files")
    else:
      endidx = selutil.jfname2idx(os.path.splitext(os.path.basename(jsonfiles[-1]))[0])
      startidx = max(0,endidx-1212)

  traces = [
    # pnum: which sub plot to be on, 0 based  
    { 'jsontag': 'Rainfall', 'pnum': 0, 'unit': 'mm', },
    { 'jsontag': 'Snowfall', 'pnum': 0, 'unit': 'mm', },
    { 'jsontag': 'WaterTable', 'pnum': 1, 'unit': 'm', },
    { 'jsontag': 'VWCDeep', 'pnum': 2, 'unit': '%', },
    { 'jsontag': 'VWCShlw', 'pnum': 2, 'unit': '%', },
    { 'jsontag': 'EET', 'pnum' : 3, 'unit': 'mm/time unit', },
    { 'jsontag': 'ActiveLayerDepth', 'pnum': 4, 'unit': 'm', },
    { 'jsontag': 'TAir', 'pnum': 5, 'unit': 'degrees C', },
    { 'jsontag': 'TShlw', 'pnum': 5, 'unit': 'degrees C', },
    { 'jsontag': 'TDeep', 'pnum': 6, 'unit': 'degrees C', },
#    { 'jsontag': 'PARDownSum', 'pnum': 7, 'unit': 'W/m2', },
#    { 'jsontag': 'PARAbsorbSum', 'pnum': 7, 'unit': 'W/m2', },
  ]

  if args.data:
    traces.append({'jsontag': 'GPPSum', 'pnum': 6, 'unit': 'unit'})
    traces.append({'jsontag': 'NPPSum', 'pnum': 6, 'unit': 'unit'})

  logging.warn("Starting main app...")

  #Check for directories, and if they don't exist, create them.
  selutil.check_dir("/tmp/year-cal-dvmdostem")
  selutil.check_dir("/tmp/cal-dvmdostem")

  print("start index: %i"%startidx)
  startyear = str(startidx/12)
  endyear = str(startidx/12+100)

  data_check = FixedWindow(traces, startidx=startidx, sprows=4, spcols=2,\
                           figtitle="Monthly Hydro and Thermo Plots",\
                           suptitle="Years " + startyear + " to " + endyear)
  data_check.show()
  
  logging.info("Done with main app...")

