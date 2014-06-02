#!/usr/bin/env python

import os
import time
import sys
import glob
import json
import logging
import argparse
import textwrap


if (sys.platform == 'darwin') and (os.name == 'posix'):
  # this is the only one that seems to work on Mac OSX with animation...
  import matplotlib
  matplotlib.use('TkAgg')

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import matplotlib.animation as animation

import matplotlib.widgets

import selutil

# The directories to look in for json files.
TMPDIR = '/tmp/cal-dvmdostem'
YRTMPDIR = '/tmp/year-cal-dvmdostem'

#
# Disable some buttons on the default toobar that freeze the program.
# There might be a better way to do this. Inspired from here:
# http://matplotlib.1069221.n5.nabble.com/Overriding-Save-button-on-Toolbar-td40864.html
#
# More info here:
# http://stackoverflow.com/questions/14896580/matplotlib-hooking-in-to-home-back-forward-button-events
#
# This does not seem to work flawlessly - I am still getting freeze-ups!!
#
from matplotlib.backend_bases import NavigationToolbar2

def home_overload(self, *args, **kwargs):
  logging.info("HOME button pressed. DISABLED; doing nothing.")
  return 'break'

def back_overload(self, *args, **kwargs):
  logging.info("BACK button pressed. DISABLED; doing nothing.")
  return 'break'

def forward_overload(self, *args, **kwargs):
  logging.info("FORWARD button pressed. DISABLED; doing nothing.")
  return 'break'

NavigationToolbar2.home = home_overload
NavigationToolbar2.back = back_overload
NavigationToolbar2.forward = forward_overload


def log_file_stats(file_list):
  '''convenience function to write some info about files to the logs'''

  logging.info( "%i json files in %s" % (len(file_list), YRTMPDIR) )

  if len(file_list) > 0:
    ffy = int(os.path.basename(file_list[0])[0:4])
    lfy = int(os.path.basename(file_list[-1])[0:4])
    logging.debug( "First file: %s (year %s)" % (file_list[0], ffy) )
    logging.debug( "Last file: %s (year %s)" % (file_list[-1], lfy) )

    if lfy > 0:
      pc = 100 * len(file_list) / len(np.arange(ffy, lfy))
      logging.debug( "%s percent of range covered by existing files" % (pc) )
    else:
      logging.debug("Too few files to calculate % coverage.")

  else:
    logging.warning("No json files! Length of file list: %s." % len(file_list))


class ExpandingWindow(object):
  '''A set of expanding window plots that all share the x axis.
  '''

  def __init__(self, traceslist, figtitle="Expanding Window Plot",
      rows=2, cols=1, targets={}):

    logging.debug("Ctor for Expanding Window plot...")

    self.window_size_yrs = None

    self.traces = traceslist

    self.fig, self.axes = plt.subplots(rows, cols, sharex='all')
    self.fig.suptitle(figtitle)
    
    self.fig.canvas.mpl_connect('key_press_event', self.key_press_event)

    logging.debug("Setting up a radio button pft chooser...")
    #                           l    b    w     h
    self.pftradioax = plt.axes([0.9, 0.25, 0.1, 0.65 ], axisbg='lightgoldenrodyellow')
    self.pftradio = matplotlib.widgets.RadioButtons( self.pftradioax,
                                                     ['PFT%i'%(i) for i in range(0,10)],
                                                     active=int(self.get_currentpft()[-1])
                                                     )
    self.pftradio.on_clicked(self.pftchooser_func)

    # Set the x label for the last (lowest) subplot
    self.axes[-1].set_xlabel("Years")

    x = np.arange(0)
    y = x.copy() * np.nan
  
    logging.debug("Setting up empty x,y data for every trace...")
    for trace in self.traces:
      ax = self.axes[ trace['axesnum'] ]
      if 'pftpart' in trace.keys():
        lbl = '%s %s' % (trace['jsontag'], trace['pftpart'])
        trace['artists'] = ax.plot(x,y,label=lbl)
      else:
        trace['artists'] = ax.plot(x, y, label=trace['jsontag'])

    logging.debug("Plotting the target lines for calibrated parameters...")
    for trace in self.traces:

      if trace['jsontag'] in targets:
        logging.debug("Found a target for %s" % trace['jsontag'])
        ax = self.axes[ trace['axesnum'] ]

        # Get a handle to the appropriate line on the plot
        # and get the color of the line.
        if 'pftpart' in trace.keys():
          lbl = '%s %s' % (trace['jsontag'], trace['pftpart'])
        else:
          lbl = trace['jsontag']
        for line in ax.lines:
          if line.get_label() == lbl:
            tc = line.get_color()
          else:
            pass # nothing to do; wrong line

        # find correct target value...
        target = targets[ trace['jsontag'] ]

        if isinstance(target, dict):
          # must be a partition variable, gotta look up which partition
          pftnum = int(trace['pft'][-1]) # <- BRITTLE!
          target = target[ trace['pftpart'] ][pftnum]
        elif isinstance(target, list):
          # must be a plain 'ol pft variable
          pftnum = int(trace['pft'][-1])  # <- BRITTLE!
          target = target[pftnum]
        else:
          pass # must be a plain 'ol target value; non-pft or pft part.

        # plot a hz line for the target
        logging.debug("Plotting a hz line")
        ax.axhline(target, color=tc, linestyle='--')

    logging.debug("Set the backgrond pft text for for pft specific variables..")
    self.set_bg_pft_txt()

    logging.debug("Label the y axes with units if available")
    for i, ax in enumerate(self.axes):
      for trace in self.traces:
        if trace['axesnum'] == i:
          if 'units' in trace.keys():
            ax.set_ylabel("%s" % trace['units'])
          else:
            logging.debug("No units are set in this trace!!")

    self.relim_autoscale_draw()
    self.grid_and_legend()
    
    self.load_data2plot(relim=True, autoscale=True)
  
    logging.info("Done creating an expanding window plot object...")


  def init(self):
    logging.info("Init function for animation")

    return [trace['artists'][0] for trace in self.traces]


  def load_data2plot(self, relim, autoscale):
    log = logging.getLogger('dataloader')

    log.info("Load data to plot. Relimit data?: %s  Autoscale?: %s", relim, autoscale)
    
    files = sorted( glob.glob('%s/*.json' % YRTMPDIR) )
    log_file_stats(files)

    if self.window_size_yrs:
      log.info("Reducing files list to last %i files..." % self.window_size_yrs)
      files = files[-self.window_size_yrs:]

    log_file_stats(files)

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
          if 'pftpart' in trace.keys():
            trace['tmpy'][idx] = pftdata[trace['jsontag']][trace['pftpart']]
          else:
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
        elif 'pftpart' in trace.keys():
          if line.get_label() == ('%s %s' % (trace['jsontag'], trace['pftpart'])):
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

    log.info("Finished loading data.")

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
      self.load_data2plot(relim=True, autoscale=False)
      return []  # nothing to re-draw when zoomed in.
    else:
      logging.info("Data limits are inside view limits. Load data and redraw.")
      self.load_data2plot(relim=True, autoscale=True)
      return [trace['artists'][0] for trace in self.traces]

  def pftchooser_func(self, label):
    '''A callback for the radio button that changes which pft is being plotted.'''
    n = int(label[-1])
    self.set_pft_number(n)
    self.clear_bg_pft_txt()
    self.set_bg_pft_txt()
    logging.info("Updated the pft number to %i" % n)

  def key_press_event(self, event):
    logging.debug("You pressed: %s. Cursor at x: %s y: %s" % (event.key, event.xdata, event.ydata))
    if event.key == 'ctrl+r':
      logging.info("RELOAD / RESET VIEW. Load all data, relimit, and autoscale.")
      self.load_data2plot(relim=True, autoscale=True)
    if event.key == 'ctrl+q':
      logging.info("QUIT")
      plt.close()
    if event.key == 'ctrl+p':
      n = 100
      files = sorted( glob.glob('%s/*.json' % YRTMPDIR) )
      if n < len(files):
        logging.warning( "Deleting first %s json files from %s..." % (n, YRTMPDIR) )
        for f in files[0:n]:
          os.remove(f)
      else:
        logging.warning("Fewer than %s json files present - don't do anything." % n)
    if event.key == 'ctrl+j':
      # could add while true here to force user to
      # enter some kind of valid input?
      try:
        ws = int(raw_input("Window Size (years)?: "))
        self.window_size_yrs = ws
        logging.info("Changed to 'fixed window' (window size: %s)" % ws)
      except ValueError as e:
        logging.warning("Invalid Entry! (%s)" % e)
    if event.key == 'ctrl+J':
      logging.info("Changed to 'expanding window' mode.")
      self.window_size_yrs = None

    if event.key == 'alt+p':
      try:
        n = int(raw_input("PFT NUMBER?> "))
        self.set_pft_number(n)
        self.clear_bg_pft_txt()
        self.set_bg_pft_txt()
        logging.info("Updated the pft number to %i" % n)
      except ValueError as e:
        logging.warning("Invalid Entry! (%s)" % e)



  def clear_bg_pft_txt(self):
    logging.info("Clearing all the background 'PFTx' texts")
    for ax in self.axes:
      ax.texts = []


  def set_pft_number(self, pftnumber):
    logger.info("Set the pft number in any trace that has the 'pft' as a key")
    for trace in self.traces:
      if 'pft' in trace.keys():
        trace['pft'] = 'PFT%i' % pftnumber


  def set_bg_pft_txt(self):
    logging.info("Set the background 'PFTx' text for axes that are plotting pft specific variables.")

    font = {'family' : 'sans-serif',
            'color'  : 'black',
            'weight' : 'bold',
            'size'   : 24,
            'alpha'  : 0.1,
            }

    for trace in self.traces:
      if 'pft' in trace.keys():
        ax = self.axes[trace['axesnum']]
        ax.text(
                  0.5, 0.5,
                  "%s" % trace['pft'],
                  fontdict=font,
                  horizontalalignment='center',
                  #verticalalignment='center',
                  transform=ax.transAxes,
                  #bbox=dict(facecolor='red', alpha=0.2)
                )

  def get_currentpft(self):
    '''return the current pft. currently assumes that all traces have the same pft'''
    pft = None
    for trace in self.traces:
      if 'pft' in trace.keys():
        return trace['pft']

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
      ax.legend(prop={'size':10.0}, loc='upper left')

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

  from configured_suites import configured_suites
  import calibration_targets
  
  logger = logging.getLogger(__name__)
  
  parser = argparse.ArgumentParser(

    formatter_class=argparse.RawDescriptionHelpFormatter,
      
      description=textwrap.dedent('''\
        Dynamically updating yearly data plots that show data from 
        dvm-dos-tem when it is running with --calibrationmode=on
        '''),
        
      epilog=textwrap.dedent('''\
        Program tries to read json files from 
            
            %s
        
        and plot the resulting data. The plots expand as more and
        more json files are discovered. The plot will be
        displayed in an "interactive" window provided by which-
        ever matplotlib backend you are using. 

        The different "suites" of plots refer to differnt
        assembelages of variables that you would like plotted.
        There is a seperate config file for "suites" of plots.

        There are also command line options for showing target
        value lines on the plots. If you specify that target
        value lines should be shown (by name or number), the 
        program will 1) search thru the calibration_targets.py file
        that is provided in this directory for the appropriate
        values, and 2) if the suite you specify contains variables
        that have associated targets, then there will be dashed line
        on the plot showing the target value.

        I expereienced some problems with the interactive window
        provided by matplotloib. Especially with the Home, Back,
        and Forward buttons. They have been disabled in the code.
        If you run the program with a high enough log level you 
        should be able to find messages to this extent whenever
        the buttons are clicked. Unfortunately the work around at
        this time is to kill the plotting program (Ctrl-C in the 
        controlling terminal window that started it) and start  the
        program over. It can be helpful to pause DVMDOSTEM while
        you are doing this.

        When using the program, if you change the zoom, or pan, 
        the plot will stop updating, even as more json data becomes
        available. To resume the updating, use "Ctrl-r" (on the 
        plot window, not the controlling terminal).
        
            Keyboard Shortcuts
            ------------------
            ctrl + r    reset view, resume auto-expand

            ctrl + q    quit

            ctrl + p    purge json files - deletes first 100 json
                        files if more than 100 json files exist in
                        the /tmp directorty

            ctrl + j    change to fixed window plot - prompts for
                        desired window size in controlling terminal
            ctrl + J    reset to expanding window plot

            alt + p     change the pft being plotted - prompts for 
                        desired window size in controlling terminal


        The link below lists more keyboard shortcuts (provided by 
        matplotlib) that allow for handy things like turning the grid 
        on and off and switching between log and linear axes:
    
            http://matplotlib.org/1.3.1/users/navigation_toolbar.html

        I am sure we forgot to mention something?
        ''' % YRTMPDIR)
      )

  parser.add_argument('--pft', default=0, type=int,
      choices=[0,1,2,3,4,5,6,7,8,9],
      help="Which pft to display")
  
  parser.add_argument('--suite', default='standard',
      choices=[k for k in configured_suites.keys()],
      help="Which suite of variables/plot configurations to show.")

  parser.add_argument('--list-suites', action='store_true',
      help="print out configured suites")


  group = parser.add_mutually_exclusive_group()
  group.add_argument('--tar-cmtname', default=None,
      choices=[cmtname for cmtname in calibration_targets.calibration_targets.keys()],
      help="The name of the community type that should be used to display target values lines.")

  group.add_argument('--tar-cmtnum', default=None, type=int,
      choices=[cmt['cmtnumber'] for k, cmt in calibration_targets.calibration_targets.iteritems()],
      help="The number of the community type that should be used to display target values lines.")

  parser.add_argument('--list-caltargets', action='store_true',
      help="print out a list of known calibration target communities")


  parser.add_argument('-l', '--loglevel', default="warning",
      help="What logging level to use. (debug, info, warning, error, critical")



  print "Parsing command line arguments..."
  args = parser.parse_args()
  #print args

  if args.list_suites:
    # Print all the known suites to the console with descriptions and then quit.
    for key, value in configured_suites.iteritems():
      if 'desc' in value.keys():
        print "{0:<12s} {1:<s}".format(key, value['desc'])
      else:
        print "{0:<12s} ?? no desc. text found...".format(key)
    sys.exit()

  if args.list_caltargets:
    print calibration_targets.caltargets2prettystring()
    sys.exit()

  loglevel = args.loglevel
  suite = configured_suites[args.suite]
  pft = args.pft

  print "Setting up logging..."
  LOG_FORMAT = '%(levelname)-7s %(name)-8s %(message)s'
  numeric_level = getattr(logging, loglevel.upper(), None)
  if not isinstance(numeric_level, int):
      raise ValueError('Invalid log level: %s' % loglevel)
  
  logging.basicConfig(level=numeric_level, format=LOG_FORMAT)

  logging.info("Setting up calibration target display...")
  if args.tar_cmtname:
    logging.info("displaying target values for '%s' community" % args.tar_cmtname)
    caltargets = calibration_targets.calibration_targets[args.tar_cmtname]
  elif args.tar_cmtnum or args.tar_cmtnum == 0:
    logging.info("displaying target values for community number %s" % args.tar_cmtnum)
    for cmtname, data in calibration_targets.calibration_targets.iteritems():
      if data['cmtnumber'] == args.tar_cmtnum:
        logging.info("community #%s --commnunity name--> '%s'" % (args.tar_cmtnum, cmtname))
        caltargets = data
      else:
        pass
  else:
    logging.info("Not displaying target data")
    caltargets = {}



  logger.info("Set the right pft in the suite's traces list..")
  for trace in suite['traces']:
    if 'pft' in trace.keys():
      trace['pft'] = 'PFT%i' % pft

  logger.info("Starting main app...")

  ewp = ExpandingWindow(
                        suite['traces'],
                        rows=suite['rows'],
                        cols=suite['cols'],
                        targets=caltargets,
                        figtitle="Some %s graphs..." % (args.suite)
                       )

  ewp.show(dynamic=True)
  
  logger.info("Done with main app...")






