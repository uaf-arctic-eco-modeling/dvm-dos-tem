#!/usr/bin/env python

# Started by T. Carman, 2024
# Quick stab at animated layer report viewer.

import curses
import sys
import os


def load_reports(log_file):
  '''
  Opens a log file (saved console output from dvmdostem) and extracts
  all the "Layer Report" tables. Returns a list of lists. Each sub list
  is the list of lines that makes up the layer report.
  '''
  with open(log_file) as data:
    lines = data.readlines()
  
  reports = []
  for i, line in enumerate(lines):
     if 'LAYER REPORT' in line:
        reports.append(lines[i:i+28])

  return reports

def report_animator(stdscr, reports):
  '''
  Makes a curses application for paging thru the list of reports.
  See here: 
   - https://docs.python.org/3/howto/curses.html
   - https://stackoverflow.com/questions/38689323/how-should-i-be-going-about-exiting-python-script-when-user-types-q

  '''

  try:
    stdscr.clear()
    for i, report in enumerate(reports):
      stdscr.addstr(0,0, ''.join(report))
      stdscr.refresh()
      curses.napms(50)

      # With this enabled, rather than quit, it pauses and when user hits
      # enter, it moves to next frame.
      #if stdscr.getch() == ord('q'):
      #  break

    curses.endwin()

  except KeyboardInterrupt:
    curses.endwin()
    print("Bye!")
    sys.exit()

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print("must pass log file")
    sys.exit(-1)
  if not os.path.isfile(sys.argv[1]):
    print("Bad file")
    sys.exit(-1)

  reports = load_reports(sys.argv[1])

  curses.wrapper(report_animator, reports)
