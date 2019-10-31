import os
import sys
import glob
import json
import logging
import textwrap
import tarfile        # for reading from tar.gz files
import shutil         # for cleaning up a /tmp directory
import numpy as np

# Find the path to the this file so that we can look, relative to this file
# up one directory and into the scripts/ directory
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../'))
print sys.path
import scripts.param_util as pu


def yearly_files(tarfileobj):
  '''Get the */yearly/*.json files...'''
  for tarinfo in tarfileobj:
    if 'yearly' in tarinfo.name:
      yield tarinfo

def monthly_files(tarfileobj):
  '''Get the */monthly/*.json files...'''
  for tarinfo in tarfileobj:
    if 'monthly' in tarinfo.name:
      yield tarinfo


class InputHelper(object):
  '''A class to help abstract some of the details of opening .json files
  '''
  def __init__(self, path, monthly=False):
    logging.debug("Making an InputHelper object...")
    logging.debug("Looking for input files here: %s" % path )

    self._monthly = monthly

    # Assume path is a directory full of .json files
    if os.path.isdir(path):
      if self._monthly:
        self._path = os.path.join(path, "calibration/monthly")
      else:
        self._path = os.path.join(path, "calibration/yearly")

      logging.debug("Set input data path to: %s" % self._path)

    elif os.path.isfile(path):
      # Assume path is a .tar.gz (or other compression) with .json files in it

      logging.info("Looking for input data files here: %s" % path)

      DEFAULT_EXTRACTED_ARCHIVE_LOCATION = os.path.join('/tmp', 'dvmdostem-user-{}'.format(str(os.getuid())), 'extracted-calibration-archive', os.path.basename(path))

      logging.info("Extracting archive to '%s'..." %
          DEFAULT_EXTRACTED_ARCHIVE_LOCATION)

      if ( os.path.isdir(DEFAULT_EXTRACTED_ARCHIVE_LOCATION) or
          os.path.isfile(DEFAULT_EXTRACTED_ARCHIVE_LOCATION) ):

        logging.info("Cleaning up the temporary archive location ('%s')..." %
            DEFAULT_EXTRACTED_ARCHIVE_LOCATION)
        shutil.rmtree(DEFAULT_EXTRACTED_ARCHIVE_LOCATION)

      tf = tarfile.open(path)

      # This is annoying, but when extracting the files, they end up in a
      # directory tree like this (depending on the directory structure of
      # the archive):
      #
      #   {DEFAULT_EXTRACTED_ARCHIVE_LOCATION}/tmp/TESTME/dvmdostem/calibration/yearly/00000.json
      #   {DEFAULT_EXTRACTED_ARCHIVE_LOCATION}/tmp/TESTME/dvmdostem/calibration/yearly/00001.json
      #   ...
      #
      # So the following cryptic lines attempt to figure out the common prefix
      # of all the members of the TarFile and then use that to setup self._path
      # Basically allows self._path to adapt and match whatever the user may have
      # set for 'caldata_tree_loc' in the config file.
      p1 = [i for i in tf.getmembers() if i.isdir()]
      p2 = [i.name for i in p1]
      p3 = os.path.commonprefix(p2)

      if self._monthly:
        self._path = os.path.join(DEFAULT_EXTRACTED_ARCHIVE_LOCATION, p3, 'monthly')
        tf.extractall(DEFAULT_EXTRACTED_ARCHIVE_LOCATION, members=monthly_files(tf))
      else:
        self._path = os.path.join(DEFAULT_EXTRACTED_ARCHIVE_LOCATION, p3, 'yearly')
        tf.extractall(DEFAULT_EXTRACTED_ARCHIVE_LOCATION, members=yearly_files(tf))

      tf.close()
    else:
      logging.error("Unable to find input data files at %s" % path)
      sys.exit(-1)

  def files(self):
    '''Returns a list of files, either in a directory or .tar.gz archive'''
    return sorted( glob.glob('%s/*.json' % self._path) )

  def path(self):
    '''Useful for client programs wanting to show where files are coming from.'''
    return self._path

  def monthly(self):
    return self._monthly


  def coverage_report(self, file_list):
    '''Convenience function to write some info about files to the logs'''

    logging.info( "%i json files in %s" % (len(file_list), self._path) )

    if len(file_list) > 0:

      if self._monthly:
        ffy = int( os.path.splitext(os.path.basename(file_list[0]))[0] ) / 12
        lfy = int( os.path.splitext(os.path.basename(file_list[-1]))[0] ) / 12
        ffm = int( os.path.splitext(os.path.basename(file_list[0]))[0] ) % 12
        lfm = int( os.path.splitext(os.path.basename(file_list[-1]))[0] ) % 12
      else:
        ffy = int(os.path.basename(file_list[0])[0:5])
        lfy = int(os.path.basename(file_list[-1])[0:5])
        ffm = '--'
        lfm = '--'

      logging.debug( "First file: %s (year %s, month %s)" % (file_list[0], ffy, ffm) )
      logging.debug( "Last file: %s (year %s, month %s)" % (file_list[-1], lfy, lfm) )

      if lfy > 0:
        pc = 100 * len(file_list) / len(np.arange(ffy, lfy))
        logging.debug( "%s percent of range covered by existing files" % (pc) )
      else:
        logging.debug("Too few files to calculate % coverage.")

    else:
      logging.warning("No json files! Length of file list: %s." % len(file_list))

  def report(self):

    log = logging.getLogger('inputhelper::reportA')

    log.info( "Path to input files: %s" % (self.path()) )

    files = self.files()

    if len(files) > 0:
      if self._monthly:
        ffy = int( os.path.splitext(os.path.basename(files[0]))[0] ) / 12
        lfy = int( os.path.splitext(os.path.basename(files[-1]))[0] ) / 12
        ffm = int( os.path.splitext(os.path.basename(files[0]))[0] ) % 12
        lfm = int( os.path.splitext(os.path.basename(files[-1]))[0] ) % 12
      else:
        ffy = int(os.path.basename(files[0])[0:5])
        lfy = int(os.path.basename(files[-1])[0:5])
        ffm = '--'
        lfm = '--'

      if (len(files) != ((lfy-ffy)+1)):
        log.warn("SOMETHING IS WRONG WITH THE INPUT DATA: count:%s last:%s first:%s:" % (len(files), lfy, ffy ))

      if ffm != '--' and lfm != '--':
        pass

      self.report_on_file(files[0])
      self.report_on_file(files[-1])
    else:
      logging.warning("No json files! Length of file list: %s." % len(files))

  def report_on_file(self, f0):
    log = logging.getLogger('inputhelper::reportB')
    log.info( "::=> FILE %s" % (f0) )
    try:
      with open(f0) as f:
        fdata = json.load(f)

      "".format(fdata["Runstage"], fdata["CMT"], fdata["Lat"], fdata["Lon"])
      details = "Runstage:%s CMT:%s Coords:(%.2f,%.2f)" % (fdata["Runstage"], fdata["CMT"], fdata["Lat"], fdata["Lon"])
      log.info( "::==> %s" % (details) )
    except (IOError, ValueError) as e:
      log.error("Problem: '%s' reading file '%s'" % (e, f))


