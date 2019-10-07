#!/usr/bin/env python

import os
import sys
import json
import logging
import argparse
import textwrap
import tarfile        # for reading from tar.gz files
import shutil         # for cleaning up a /tmp directory
import signal         # for a graceful exit

import multiprocessing

if (sys.platform == 'darwin') and (os.name == 'posix'):
  # TkAgg is the only one that seems to work on Mac OSX with animation...
  import matplotlib
  matplotlib.use('TkAgg') # <-- MUST BE SIMPLY 'Agg' to work with multi-processing!

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec

import matplotlib.widgets

# our own custom classes
from InputHelper import InputHelper

# Find the path to the this file so that we can look, relative to this file
# up one directory and into the scripts/ directory
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../'))
print sys.path
import scripts.param_util as pu

# Keep the detailed documentation here. Can be accessed via command
# line --extended-help flag.
def generate_extened_help():
  help_text = textwrap.dedent('''\
  By default, the program tries to read json files from your /tmp
  directory and plot the resulting data. 

  When plotting dynamically the plot will expand to fit data that
  it finds in the directory or archive. Unless using the 
  '--no-show' flag, the plot will be displayed in an "interactive" 
  window provided by which-ever matplotlib backend you are using.

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
  controlling terminal window that started it) and start the
  program over. It can be helpful to pause DVMDOSTEM while
  you are doing this.

  When using the program, if you change the zoom, or pan, 
  the plot will stop updating, even as more json data becomes
  available. To resume the updating, use "Ctrl-r" (on the 
  plot window, not the controlling terminal).

      Keyboard Shortcuts
      ------------------
      ctrl + g    Quit. Plot window must be active to recieve the signal.

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
                  (buggy)


  The link below lists more keyboard shortcuts (provided by 
  matplotlib) that allow for handy things like turning the grid 
  on and off and switching between log and linear axes:

      http://matplotlib.org/1.3.1/users/navigation_toolbar.html

  I am sure we forgot to mention something?
  ''' % ())

  print help_text

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

def stylize_buttons(r, sizefrac=1.0):
    "stylize all radio buttons in `r` collection."
    [c.set_radius(c.get_radius()*sizefrac) for c in r.circles]
    [c.set_linestyle('solid') for c in r.circles]
    [c.set_edgecolor('black') for c in r.circles]
    [c.set_linewidth(0.5) for c in r.circles] # not sure if this has any affect

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

def exit_gracefully(signum, frame):
  '''A function for quitting w/o leaving a stacktrace on the users console.'''
  logging.info("Caught signal='%s', frame='%s'. Quitting - gracefully." % (signum, frame))
  sys.exit(1)

def do_nothing(signal_number, frame):
  print "Doing nothing with signal number: ", signal_number


def worker(in_helper, the_suite, calib_targets, title, add_in_helpers, save_fname, save_fmt):

  logging.info("Build the plot object...")
  ewp = ExpandingWindow(
                        in_helper,
                        S['traces'],
                        rows=S['rows'],
                        cols=S['cols'],
                        targets=calib_targets,
                        figtitle=title,
                        no_show=True,
                        extrainput=add_in_helpers
                       )

  logging.info("Show the plot object...")
  ewp.show(dynamic=False, save_name=save_fname, format=save_fmt)
  return


class ExpandingWindow(object):
  '''A set of expanding window plots that all share the x axis.'''

  def __init__(self, input_helper, traceslist, figtitle="Expanding Window Plot",
      rows=2, cols=1, targets={}, no_show=False, extrainput=[], no_blit=False):

    logging.debug("Ctor for Expanding Window plot...")

    self.input_helper = input_helper

    self.extra_input_helpers = extrainput

    self.window_size_yrs = None

    self.traces = traceslist

    self.targets = targets

    self.no_show = no_show

    self.no_blit = no_blit

    # Setting controlling where this program will look for reference parameters 
    # that are used for finding PFT names. The default setting is to look for 
    # in a parameters/ directory relative to the current location (location 
    # from which this calibration_viewer.py script was run). An alternate value 
    # for this setting is 'relative_to_dvmdostem' in which this program will
    # look for the parameters/ directory that ships with dvmdostem.
    self.reference_param_loc = 'relative_to_curdir'

    self.fig = plt.figure(figsize=(6*1.3, 8*1.3))
    self.ewp_title = self.fig.suptitle(figtitle)

    if no_show:
      # NO NEED FOR ANY SPACE FOR VARIOUS RADIO BUTTONS
      self.gs = gridspec.GridSpec(rows, cols)

    else:
      # MAKE SPACE FOR VARIOUS CONTROL BUTTONS
      self.gs = gridspec.GridSpec(rows, cols+1, width_ratios=[8,1])

      # figure out the index of the button that should be selected
      # this is horribly ugly, but seems to work...
      idx = [i for i,v in enumerate([configured_suites[k]['traces']==traceslist for k,v in configured_suites.iteritems()]) if v]
      active_idx = idx[0]

      # SUITE Selection
      logging.debug("Set up radio buttons for picking the SUITE to display...")
      self.suiteradioax = plt.subplot(self.gs[0:2, -1])
      self.suiteradio = matplotlib.widgets.RadioButtons(
          self.suiteradioax,
          [ k for k, v in configured_suites.iteritems() ],
          active=active_idx
      )
      self.suiteradio.on_clicked(self.suite_changer)
      stylize_buttons(self.suiteradio, sizefrac=0.75)

      # PFT Selection
      pfttraces = []
      for trace in self.traces:
        if 'pft' in trace.keys():
          pfttraces.append(trace['jsontag'])

      if ( (len(pfttraces) > 0) ):
        logging.debug("Setup radio buttons for picking the PFT to display...")
        self.pftradioax = plt.subplot(self.gs[2:4, -1])
        self.pftradio = matplotlib.widgets.RadioButtons(
            self.pftradioax,
            ['PFT%i'%(i) for i in range(0,10)],
            active=int(self.get_currentpft()[-1])
        )
        self.pftradio.on_clicked(self.pftchanger)
        stylize_buttons(self.pftradio, sizefrac=0.75)

    self.setup_axes_ticks_events_and_load_data()

    logging.info("Done creating an expanding window plot object...")


  def init(self):
    logging.info("Init function for animation")

    return [trace['artists'][0] for trace in self.traces]


  def load_data2plot(self, relim, autoscale):
    log = logging.getLogger('dataloader')

    log.info("Load data to plot. Relimit data?: %s  Autoscale?: %s", relim, autoscale)
    
    # storage for tracking module state changes...
    module_state_dict = {}

    # gets a sorted list of json files...
    files = self.input_helper.files()

    for inhelper in self.extra_input_helpers:
      log.info("Loading data from extra input helpers...")
      files += inhelper.files()

    self.input_helper.report()
    for inhelper in self.extra_input_helpers:
      inhelper.report()

    if self.window_size_yrs:  # seems broken TKinter Exception about 'can't enter readline'
      log.info("Reducing files list to cover only the last %i years..." % self.window_size_yrs)

      if self.input_helper.monthly():
        logging.debug("No. of monthly files available: %s" % len(files))
        logging.debug("Years represented: %s" % (len(files)/12))
        logging.debug("current window size, years: %s" % self.window_size_yrs)
        logging.debug("No. of monthly files to use from back of list: %s" % (int(self.window_size_yrs)*12))

        first_file_idx = int(self.window_size_yrs) * 12
        files = files[-first_file_idx:]

      else:
        files = files[-self.window_size_yrs:]

    self.input_helper.coverage_report(files)

    # create an x range big enough for every possible file...
    log.info("Creating x range of appropriate size...(%s)" % len(files))
    if len(files) == 0:
      x = np.arange(0)
    else:
      end = int( os.path.splitext( os.path.basename(files[-1]) )[0] )
      #x = np.arange(0, end + 1 , 1) # <-- make range inclusive!
      x = np.arange(0, len(files))
    

    # ----- READ FIRST FILE FOR TITLE ------
    self.set_title_from_first_file(files)
    # for each trace, create a tmp y container the same size as x
    for trace in self.traces:
      trace['tmpy'] = x.copy() * np.nan
    
    # ----- READ EVERY FILE --------
    log.info("Read every file...")
    log.info("Load data to trace['tmpy'] container; find module state-changes.")

    for fnum, file in enumerate(files):
      # try reading the file
      try:
        with open(file) as f:
          fdata = json.load(f)

        #idx = int(os.path.splitext( os.path.basename(file) )[0])
        idx = fnum

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

        # Look at the previous file and see if the state of any
        # modules or flags has changed...
        if (fnum > 0):
          with open(files[fnum-1]) as pfile:
            pfdata = json.load(pfile)

          for k in ["Nfeed", "AvlNFlag", "Baseline", "EnvModule", "BgcModule",
                    "DynLaiModule", "DslModule", "DsbModule"]:

            cstate = fdata[k]
            pstate = pfdata[k]
            if cstate != pstate:
              module_state_dict[idx] = (k, cstate)

      except (IOError, ValueError) as e:
        logging.error("Problem: '%s' reading file '%s'" % (e, file))

      
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

    # ----- MODULE CHANGE MARKERS ------
    # Clean up any existing 'module change markers' (vertical lines marking
    # when modules turn on or off)
    for ax in self.axes:
      for line in ax.lines:
        if line.get_label() == '__mscm':
          ax.lines.remove(line)

    # ----- STAGE CHANGE MARKERS -------
    stage_changes = [len(inhelper.files()) for inhelper in self.extra_input_helpers]
    stage_changes.insert(0, len(self.input_helper.files()))

    for ax in self.axes:
      # clean up anything existing...
      for line in ax.lines:
        if line.get_label() == '__scm':
          ax.lines.remove(line)

      # Assumes that all the data in the archives is complete and consistent.
      for idx in np.cumsum(stage_changes)[0:-1]:
        logging.info("Adding stage change line at year %s" % idx)
        ax.axvline(idx, label='__scm', linestyle='--', color="red", alpha=1.0)

    # Then loop over the dictionary and plot a vertical line wherever necessary.
    # The module stage dictionary could looks something like this:
    # { 12: ('DslModule', true), 54: ('DynLaiModule', false)}
    for ax in self.axes:
      for k, val in module_state_dict.iteritems():
        ax.axvline(k, linestyle='--', linewidth=0.3, color='blue', label='__mscm')

    # ------ FORMAT AXES --------------
    # prevent scientific notation and "offset" labels for axes
    for ax in self.axes:
      ax.ticklabel_format(useOffset=False, style='plain')

    # ----- RELIMIT and SCALE ----------
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

    # ----- SETUP PFT BG TEXT -----------
    self.clear_bg_pft_txt()
    self.set_bg_pft_txt()


  def update(self, frame):
    '''The animation updating function. Loads new data, but only upates view
    if the user is "zoomed out" (data limits are w/in view limits).
    
    Returns a list of artists to re-draw.
    '''
    logging.info("Animation Frame %7i" % frame)
    
    # gets a sorted list of json files...
    files = self.input_helper.files()

    self.input_helper.coverage_report(files)

    self.report_view_and_data_lims()

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

  def setup_axes_ticks_events_and_load_data(self):
    '''A catch-all setup function'''

    # Make the first axes, then all others, sharing x on the first axes.
    self.axes = [ plt.subplot(self.gs[0,0]) ]
    for r in range(1, self.gs.get_geometry()[0]):
      self.axes.append(plt.subplot(self.gs[r, 0], sharex=self.axes[0]))

    # Turn off all tick labels on x axis
    for r in range(self.gs.get_geometry()[0]):
      plt.setp(self.axes[r].get_xticklabels(), visible=False)

    # Set the x label and ticks for the last (lowest) subplot
    if self.input_helper.monthly():
      self.axes[-1].set_xlabel("Month")
    else:
      self.axes[-1].set_xlabel("Years")

    plt.setp(self.axes[-1].get_xticklabels(), visible=True)
                                         # L     B     W     H
    self.gs.tight_layout(self.fig, rect=[0.05, 0.00, 1.00, 0.95])

    self.fig.canvas.mpl_connect('key_press_event', self.key_press_event)

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

    self.plot_target_lines()

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


  def suite_changer(self, suite):
    '''Changes which plot suite is being shown/updated'''

    logging.info("Changing to view the %s plot suite." % suite)
    # get the index of the selected button
    keys = [k for k, v in configured_suites.iteritems()]
    for i, k in enumerate(keys):
      if k == suite:
        n = i

    # Deal with the title. First get the old title, pull out the suite, (
    # first element in first line), replace it with the new suite, and then
    # make a new string and set the title.
    title_tokens = [l.split() for l in self.ewp_title.get_text().splitlines()]
    title_tokens[0][0] = suite
    self.ewp_title.set_text("\n".join([' '.join(w) for w in title_tokens]))

    # Now clear the old figure
    self.fig.clear()

    # Set the new title
    self.fig.suptitle(self.ewp_title.get_text())

    # Update the traces list based on the new suite
    self.traces = configured_suites[suite]['traces']

    # Set up the grid spec with room for the pft and suite buttons on the right
    self.gs = gridspec.GridSpec(configured_suites[suite]['rows'], configured_suites[suite]['cols']+1, width_ratios=[8,1])

    # Setup the radio button suite
    logging.info("Setting up a radio button SUITE chooser...")
    self.suiteradioax = plt.subplot(self.gs[0:2, -1]) # just a few rows, last column
    self.suiteradio = matplotlib.widgets.RadioButtons(
        self.suiteradioax,
        [ k for k, v in configured_suites.iteritems() ],
        active=n
    )
    self.suiteradio.on_clicked(self.suite_changer)
    stylize_buttons(self.suiteradio, sizefrac=0.75)

    # Should really figure out what the old pft number was?
    self.set_pft_number(0)

    # build a list of the pft specific traces
    pfttraces = []
    for trace in self.traces:
      if 'pft' in trace.keys():
        pfttraces.append(trace['jsontag'])

    if ( (len(pfttraces) > 0) ):
      logging.info("Setting up a radio button pft chooser...")
      self.pftradioax = plt.subplot(self.gs[2:4, -1]) # just a few rows, last column
      self.pftradio = matplotlib.widgets.RadioButtons(
          self.pftradioax,
          ['PFT%i'%(i) for i in range(0,10)],
          active=int(self.get_currentpft()[-1])
        )

      self.pftradio.on_clicked(self.pftchanger)
      stylize_buttons(self.pftradio, sizefrac=0.75)

    self.setup_axes_ticks_events_and_load_data()


  def pftchanger(self, label):
    '''Changes which pft is being plotted.'''
    self.clear_target_lines() # gotta do this to get rid of target lines
    n = int(label[-1])
    self.set_pft_number(n)
    self.clear_bg_pft_txt()
    self.set_bg_pft_txt()
    logging.info("Updated the pft number to %i" % n)
    self.plot_target_lines()

    logging.info("Reload all the data to the plot...")
    self.load_data2plot(relim=True, autoscale=True)

  def key_press_event(self, event):
    logging.debug("You pressed: %s. Cursor at x: %s y: %s" % (event.key, event.xdata, event.ydata))

    if event.key == 'ctrl+r':
      logging.info("RELOAD / RESET VIEW. Load all data, relimit, and autoscale.")
      self.load_data2plot(relim=True, autoscale=True)

    if event.key == 'ctrl+q':
      logging.info("QUIT")
      plt.close()

    if event.key == 'ctrl+p':
      logging.info("PRUNE")

      if len(self.extra_input_helpers) > 0:
        logging.warning("You can't prune while viewing archives. Do Nothing.")
        pass

      else:
        n = 100
        files = self.input_helper.files()

        if n < len(files):
          logging.warning("Deleting first %s json files from '%s'!" %
              (n, self.input_helper.path()))
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

    if event.key == 'ctrl+g':
      logging.debug("Captured Ctrl-g. Quit nicely.")
      exit_gracefully(event.key, None) # <-- need to pass something for frame ??


  def set_title_from_first_file(self, files):
    if len(files) > 0:
      try:
        with open(files[0]) as f:
          fdata = json.load(f)

        title_lines = self.ewp_title.get_text().splitlines()
        first_line = title_lines[0]
        cmt_latlon_list = first_line.split()[1:]

        details = "%s (%.2f,%.2f)" % (fdata["CMT"], fdata["Lat"], fdata["Lon"])

        if not ' '.join( cmt_latlon_list ) == details:
          new_first_line = "%s %s" % (first_line, details)
          title_lines[0] = new_first_line
          new_title_string = "\n".join(title_lines)

          self.fig.suptitle(new_title_string)
        else:
          pass # nothing to do - title already has CMT, lat and lon...

      except (IOError, ValueError) as e:
        logging.error("Problem: '%s' reading file '%s'" % (e, f))

    else:
      pass # Nothing to do; no files, so can't find CMT or lat/lon

  def plot_target_lines(self):
    logging.debug("Plotting the target lines for calibrated parameters...")

    for trace in self.traces:

      if trace['jsontag'] in self.targets:
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
        target = self.targets[ trace['jsontag'] ]

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
        ax.axhline(target, color=tc, linestyle='--') # can't use label= or
                                                     # each will show in legend

  def clear_target_lines(self):
    logging.info("Clearing all target lines from axe(s)...")
    for ax in self.axes:
      ax.lines[:] = [l for l in ax.lines if not (l.get_linestyle() == '--')]

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

        logger.debug("Setting the verbose name for the PFT!")
        # Split the lines and look in the first line; the second line of the
        # title will have the CMT code for the target lines. The first line
        # of the title has CMT code read from first file in the file list.
        t_line0 = self.ewp_title.get_text().split('\n')[0]
        spos = t_line0.find('CMT')
        if spos < 0: # did not find the CMT code yet in the title...
          logger.warn("Did not find CMT text in title - can't lookup PFT verbose name!")
          vname = ''
        else:
          cmtkey = t_line0[spos:spos+5]
          vname = "(%s)" % pu.get_pft_verbose_name(pftkey=trace['pft'], cmtkey=cmtkey, lookup_path=self.reference_param_loc)
        logger.debug("verbose PFT name is: %s" % vname)

        ax.text(
                  0.5, 0.5,
                  "%s %s" % (trace['pft'], vname),
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
      if self.input_helper.monthly():
        loc = mplticker.MultipleLocator(base=12)
        ax.xaxis.set_major_locator(loc)

      ax.grid(True) # <-- w/o parameter, this toggles!!
      ax.legend(prop={'size':8.0}, loc='upper left')

  def show(self, save_name="", dynamic=True, format="pdf"):
    '''Show the figure. If dynamic=True, then setup an animation.'''

    logging.info("Displaying plot: dynamic=%s, no_show=%s, save_name=%s, format=%s" % (dynamic, self.no_show, save_name, format))
    if (dynamic and self.no_show):
      logging.warn("no_show=%s implies static. Generating static file only." % (self.no_show))

    if dynamic:
      logging.info("Setup animation.")
      self.ani = animation.FuncAnimation(self.fig, self.update, interval=100,
                                         init_func=self.init, blit=(not self.no_blit))

    if save_name != "":
      # the saved file will represent a snapshot of the state of the json
      # directory at the time the animation was started
      full_name = save_name + "." + format
      logging.info("Saving plot to '%s'" % (full_name))
      plt.savefig(full_name) # pdf may be smaller than png?

    if not self.no_show:
      plt.show(block=True)


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
  
  # Callback for SIGINT. Allows exit w/o printing stacktrace to users screen
  original_sigint = signal.getsignal(signal.SIGINT)
  signal.signal(signal.SIGINT, do_nothing)

  logger = logging.getLogger(__name__)

  #
  # Setup the command line interface...
  #
  parser = argparse.ArgumentParser(

    formatter_class=argparse.RawDescriptionHelpFormatter,
      
      description=textwrap.dedent('''\
        A viewer for dvmdostem calibration. Can create and or display
          (1) Dynamically updating plots from data written out by
              dvmdostem when it is running with --cal-mode=on.
          (2) Static plots created as dvmdostem is running or from an
              archived calibration run.
          (3) A set of plots that stitches together outputs from different
              run stages; data for each stage is must be provided as a set of
              .tar.gz archives.
        '''),
      epilog="" # moved content to extended help
    )

  parser.add_argument('--extended-help', action='store_true',
      help="Show a detailed description of the program.")

  parser.add_argument('--pft', default=0, type=int,
      choices=[0,1,2,3,4,5,6,7,8,9],
      help="Which pft to display")
  
  parser.add_argument('--suite', default='Vegetation',
      choices=[k for k in configured_suites.keys()],
      help="Which suite of variables/plot configurations to show.")

  parser.add_argument('--list-suites', action='store_true',
      help="print out configured suites")

  parser.add_argument('--no-blit', action='store_true',
      help=textwrap.dedent('''\
        Some systems have difficulty with blitting which is a technique used to 
        speed up animations. If blitting works, then you should use it; if you
        are having problems then use this option to turn blitting off.
        '''))

  targetgroup = parser.add_mutually_exclusive_group()

  targetgroup.add_argument('--targets', action='store_true',
      help=textwrap.dedent('''\
          Display target value lines on the plots. Target values are looked up
          in the calibration_targets.py file (same directory as this viewer
          program) and the CMT code listed in the first input file (in the
          first series if inputs are to be read from multiple series).'''))

  parser.add_argument('--list-caltargets', action='store_true',
      help="print out a list of known calibration target communities")

  parser.add_argument('--ref-targets', default=None,
     help=textwrap.dedent('''Path to a calibration_targets.py file that will be
      used for dsiplaying target lines. If this argument is not provided, then
      the program will look for an use the calibration targets file that is
      expected to live alongside this program (in dvm-dos-tem/calibration/
      directory).''')) 

  parser.add_argument('-l', '--loglevel', default="warning",
      help="What logging level to use. (debug, info, warning, error, critical")

  parser.add_argument('--static', action='store_true',
      help="Don't animate the output. The plots will *NOT* automatically update!")

  parser.add_argument('--save-name', default="",
      help="A file name prefix to use for saving plots.")

  parser.add_argument('--save-format', default="pdf",
      help="Choose a file format to use for saving plots.")

  parser.add_argument('--no-show', action='store_true',
      help=textwrap.dedent('''Don't show the plots in the interactive viewer.
          Implies '--static'. Useful for scripts, or automatically saving output
          images.'''))

  parser.add_argument('--from-archive', default=False,
      help=textwrap.dedent('''Generate plots from an archive of json files, 
          instead of the normal /tmp directory.'''))

  parser.add_argument('--archive-series', default=[], nargs='+',
      help=textwrap.dedent("""Stitch data from the provided archive series onto
          the end of the plot, after the data from the archive specifed in 
          --from-archive. Will show vertical lines at the boundary of each
          provided archive. Useful for showing data from multiple stages on
          one plot."""))

  parser.add_argument('--monthly', action='store_true', #default='/tmp/cal-dvmdostem',
      help=textwrap.dedent('''Read and disply monthly json files instead of 
          yearly. NOTE: may be slow!!'''))

  parser.add_argument('--data-path', default=None,
      help=textwrap.dedent('''Look for json files in the specified path'''))

  parser.add_argument('--bulk', action='store_true',
      help=textwrap.dedent('''With this flag, the viewer will attempt to
          generate a multitude of plots - one plot for each PFT for each suite.
          This option uses the multiprocessing module so will use more than one
          core on your computer. The --no-show and --save-name options are 
          implied. The final --save-name is assembled from the --save-name option
          passed on the command line (if any), the suite, and the PFT,
          resulting in something like this: '_Environment_PFT0.pdf' if no
          --save-name is specified on the command line. NOTE: With some versions
          of python and matplotlib, running with --bulk will be extremely slow!
          '''))


  print "Parsing command line arguments..."
  args = parser.parse_args()
  #print args

  #
  # Keep reporting and testing functions that should print info and quit here.
  #
  if args.extended_help:
    parser.print_help()
    print ""
    print generate_extened_help()
    sys.exit(0)

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

  #
  # Made it past the reporting? Keep looking at args, and setting up the plots.
  #

  loglevel = args.loglevel
  suite = configured_suites[args.suite]
  pft = args.pft

  print "Setting up logging..."
  LOG_FORMAT = '%(levelname)-7s %(name)-8s %(message)s'
  numeric_level = getattr(logging, loglevel.upper(), None)
  if not isinstance(numeric_level, int):
      raise ValueError('Invalid log level: %s' % loglevel)
  
  logging.basicConfig(level=numeric_level, format=LOG_FORMAT)

  logger.info("Set the right pft in the suite's traces list..")
  for trace in suite['traces']:
    if 'pft' in trace.keys():
      trace['pft'] = 'PFT%i' % pft

  if args.save_format not in plt.gcf().canvas.get_supported_filetypes().keys():
    logging.error("%s' is not a supported format for saving plots!" % args.save_format)
    logging.error("Please use one of: %s" % (' '.join(plt.gcf().canvas.get_supported_filetypes().keys())))
    sys.exit(-1)


  logger.info("Starting main app...")

  logging.info("Dynamic=%s Static=%s Blitting=%s No-show=%s Save-name='%s'" %
      (not args.static, args.static, (not args.no_blit), args.no_show, args.save_name))



  logging.info("Setting up the input data source...")

  if (args.from_archive) or (len(args.archive_series) > 0):
    if not args.static:
      logging.warning("Forcing to a static plot. Dynamic updating (animation) not currently possible when plotting from archives.")
      args.static = True

  additional_input_helpers = []

  if len(args.archive_series) > 0:
    if not args.from_archive:
      logging.error("If you provide an archive-series, you must provide --from-archive!")
      sys.exit(-1)

  if args.archive_series:
    for arc in args.archive_series:
      additional_input_helpers.append(InputHelper(path=arc, monthly=args.monthly))

  if args.from_archive:
    input_helper = InputHelper(path=args.from_archive, monthly=args.monthly)
  else:
    if args.data_path is None:
      parser.error("You must specify --data-path so the program knows which files to plot!")
    if os.path.basename(args.data_path) != 'dvmdostem':
      logging.info("Adding 'dvmdostem' to data path...")
      dp = os.path.join(args.data_path, 'dvmdostem')
    else:
      dp = args.data_path
    input_helper = InputHelper(path=dp, monthly=args.monthly)

  #logging.info("from_archive=%s" % args.from_archive)
  #logging.info("data_path=%s" % args.data_path)

  # Do we need to worry about a case where the different input archives
  # represent differnt community types - and therefore should have different
  # target values displayed?
  if args.targets:
    logging.info("Setting up calibration target display...")
    if len(input_helper.files()) > 0:
      # Figure out which CMT we are dealing with
      try:
        with open(input_helper.files()[0], 'r') as ff:
          fdata = json.load(ff)
          cmtstr = fdata["CMT"] # returns string like "CMT05"
      except (IOError, ValueError) as e:
        logging.error("Problem: '%s' reading file '%s'" % (e, f))

      # Figure out where to find the targets.
      found_targets = False
      if args.ref_targets:
        # May want to save path, clear it, add only the new target location
        # and try the import. on success, print something... and show lines??
        # if it fails then log message, and restore path, and continue
        try:
          print "Trying to look for targets here: {}".format(os.path.abspath(args.ref_targets))
          orig_path = sys.path
          sys.path = [os.path.abspath(args.ref_targets)]
          import calibration_targets
          sys.path = orig_path
          found_targets = True
          print "Restoring path..."
        except (ImportError, NameError) as e:
          logging.error("Can't display target lines!! Can't find targets! {}".format(e.message))

      else:
        try:
          print "Trying to look for targets here: {}".format(os.path.abspath(args.ref_targets))
          import calibration_targets
          found_targets = True
        except (ImportError, NameError) as e:
          logging.error("Can't display target lines!! Can't find targets! {}".format(e.message))

      if found_targets:
        for cmtname, data in calibration_targets.calibration_targets.iteritems():
          if cmtstr == 'CMT{:02d}'.format(data['cmtnumber']):
            caltargets = data
            target_title_tag = "CMT {} ({:})".format(data['cmtnumber'], cmtname)
          else:
            pass # wrong cmt
      else:
        caltargets = {}
        target_title_tag = "--"

    else:
      print logging.warn("No files. Can't figure out which CMT to display targets for without files.")
      target_title_tag = "--"

  else:
    target_title_tag = "--"
    logging.info("Not displaying target data")
    caltargets = {}

  if args.bulk:
    logging.warning("Attempting to switch backends.")
    logging.warning("Apparently this is an experimental feature; your mileage may vary.")
    plt.switch_backend("Agg")

    logging.info("Building a bunch of plot objects...")

    jobs = []

    for PFT in range(0,10):

      for k, S in configured_suites.iteritems():

        logger.info("Set the right pft in the suite's traces list..")
        for trace in S['traces']:
          if 'pft' in trace.keys():
            trace['pft'] = 'PFT%i' % PFT

        # SETUP THE WORKER PROCESS
        p = multiprocessing.Process(
            target=worker,
            args=(
                input_helper,
                S,
                caltargets,
                "%s\nTargets Values for: %s" % (k, target_title_tag),
                additional_input_helpers,
                "%s_%s_pft%s"%(args.save_name,k,PFT),
                args.save_format
            )
        )
        jobs.append(p)
        p.start()


  else:
    logging.info("Build a single plot object...")
    ewp = ExpandingWindow(
                          input_helper,
                          suite['traces'],
                          rows=suite['rows'],
                          cols=suite['cols'],
                          targets=caltargets,
                          figtitle="%s\nTargets Values for: %s" % (args.suite, target_title_tag),
                          no_show=args.no_show,
                          extrainput=additional_input_helpers,
                          no_blit=args.no_blit,
                         )

    logging.info("Show the plot object...")
    ewp.show(dynamic=(not args.static), save_name=args.save_name, format=args.save_format)

  logger.info("Done with main app...")





