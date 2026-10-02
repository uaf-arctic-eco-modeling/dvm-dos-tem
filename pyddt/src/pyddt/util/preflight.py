#!/usr/bin/env python3

'''
This tool is for preflight checks of dvmdostem runs. It should accept a path to
a run directory as an argument. The tool should provide a report with items
flagged as either WARNING or ERROR. Items that are ERRORS must be addressed
before you can expect the dvmdostem run to actually complete. Items that are
WARNING may not prevent the run from completing, but should be reviewed because
they may make the outputs questionable.

Here is a list of checks:

Layout of the run directory, expected files and directories:
  calibration/ (directory, not really used at this time) (warning if not
  present) config/ (has a config.js file, as well as output_spec.csv) (error)
  output/ (empty directory)  (warn if not empty) parameters/ (folder of
  parameter files) (error if not present) run-mask.nc (file) (error if not
  present)
    - note that the run-mask.nc file is required for the run and common practice
      is to keep the run mask in the run folder (with relative path in the
      config.js file, but it could also be valid to keep it elsewhere with an
      absolute path in the config file...))

Note that for checking the paths to the input files (and parameters, output/
etc) there is the question of execution context of this pre-flight check tool vs
the execution context of the dvmdostem run itself. Sometimes the preflight tool
might be run from inside the docker container in which case, the paths in the
config file can be checked directly. But other times the user might wish to run
the preflight from outside the docker container in which case the paths in the
config file may need to be interpreted relative to the host system rather than
the container. This same problem is present with the pyddt-runmonitor and
pyddt-resume-region tooling, so following the same pattern as used in those
tools might be helpful.
    

Integrity of config.js file
  - run-mask.nc exists (error)
  - parameters/ exists (error)
  - output/ exists (error)
  - config/config.js exists and is readable (error)
  - check the IO section of the config for:
  - output is relative path (warning)
  - parameters is relative path (warning)
  - run-mask.nc is relative path (warning)
  - all input paths exist (error)

The current "standard" way to setup a dvmdostem run is to have a working
directory that contains the config/, output/, parameters/ directories and the
run-mask.nc file. Then in the config/config.js file, the paths to these
directories and files should be specified relative to this working directory.
while the paths to the "heavier" inputs may be specified either relative to this
working directory or as absolute paths. However note that the user could have
specified a run that used absolute paths to the config file, output_spec file,
parameter files, etc. This would allow sharing these resources between runs.
Perhaps this merits a warning because there are some valid use cases for sharing
these resources.


Output specification:
   - Check the output_spec.csv file for required columns and consistency (error)
   - Check that the user has enabled CMTNUM as an output (error)
   - Check that if the user has enabled any layer outputs, then at least LAYERDZ
     is also enabled (error)
   - Warn user of other LAYER description outputs that are enabled without
     LAYERDZ (warning)

Then we need to open the run-mask file and the vegetation file and the parameter
files. We should confirm that for every enabled grid cell in the run mask, there
is a corresponding CMT entry in the parameter files corresponding to the CMT
number that is in the vegetation.nc file. For example if cell 1,1 is ON in the
run mask and cell 1,1 in the vegetation.nc file has value 234, then the
parameters files must have a valid block of data for CMT234. This must exist in
all the parameter files. Please make use of the pyddt-param (`pyddt.util.param`)
module to parse and query the parameter files.

'''

import argparse
import textwrap
from pathlib import Path

import commentjson
import numpy as np

from pyddt.util import outspec as pyddt_outspec
from pyddt.util import param as pyddt_param
from pyddt.util import runmonitor

ERROR = 'ERROR'
WARNING = 'WARNING'

# Keys expected under config['IO'] that point at the "heavier" input files
# (climate, vegetation, fire, etc), as opposed to the run's own
# parameters/output_spec/run-mask, which are checked separately.
INPUT_FILE_KEYS = [
  'hist_climate_file', 'proj_climate_file', 'veg_class_file', 'drainage_file',
  'soil_texture_file', 'co2_file', 'proj_co2_file', 'runmask_file', 'topo_file',
  'fri_fire_file', 'hist_exp_fire_file', 'proj_exp_fire_file',
]


class Issue:
  '''A single preflight finding: a `level` (`ERROR` or `WARNING`) and message.'''
  def __init__(self, level, message):
    self.level = level
    self.message = message

  def __repr__(self):
    return f'{self.level}: {self.message}'


def check_directory_layout(run_dir):
  '''
  Check the run directory for the expected files/sub-directories.

  Parameters
  ----------
  run_dir : pathlib.Path

  Returns
  -------
  issues : list of Issue
  '''
  raise NotImplementedError


def load_config(run_dir):
  '''
  Load `run_dir`/config/config.js.

  Parameters
  ----------
  run_dir : pathlib.Path

  Returns
  -------
  config : dict or None
    None if the file is missing or unreadable.
  issues : list of Issue
  '''
  raise NotImplementedError


def check_config_integrity(run_dir, config, input_catalog_dir=None, workflows_dir=None):
  '''
  Check the IO section of `config` for missing/misconfigured paths.

  Parameters
  ----------
  run_dir : pathlib.Path
  config : dict
    Parsed config.js contents.
  input_catalog_dir, workflows_dir : str or pathlib.Path, optional
    Passed through to `runmonitor.resolve_io_path`.

  Returns
  -------
  issues : list of Issue
  '''
  raise NotImplementedError


def check_output_spec(output_spec_path):
  '''
  Check an output_spec.csv file for required columns/consistency, that
  CMTNUM is enabled, and that layer-resolution outputs have LAYERDZ enabled.

  Parameters
  ----------
  output_spec_path : pathlib.Path

  Returns
  -------
  issues : list of Issue
  '''
  raise NotImplementedError


def check_cmt_coverage(run_mask_path, veg_class_path, parameters_dir):
  '''
  Confirm that every CMT present (in the vegetation file, at an active run
  mask cell) has a corresponding data block in every parameter file.

  Parameters
  ----------
  run_mask_path, veg_class_path, parameters_dir : pathlib.Path

  Returns
  -------
  issues : list of Issue
  '''
  raise NotImplementedError


def run_preflight(run_dir, input_catalog_dir=None, workflows_dir=None):
  '''
  Run all preflight checks against a dvmdostem run directory.

  Later checks that depend on earlier ones (e.g. config integrity depends on
  config.js being present/parseable) are skipped if their prerequisite failed,
  rather than raising.

  Parameters
  ----------
  run_dir : str or pathlib.Path
  input_catalog_dir, workflows_dir : str or pathlib.Path, optional
    Passed through to `runmonitor.resolve_io_path`.

  Returns
  -------
  issues : list of Issue
  '''
  run_dir = Path(run_dir).resolve()
  issues = []

  issues += check_directory_layout(run_dir)

  config, config_issues = load_config(run_dir)
  issues += config_issues
  if config is None:
    return issues

  issues += check_config_integrity(run_dir, config, input_catalog_dir, workflows_dir)

  io = config.get('IO', {})
  output_spec_path = runmonitor.resolve_io_path(
      io.get('output_spec_file', 'config/output_spec.csv'), run_dir, input_catalog_dir, workflows_dir)
  if output_spec_path.is_file():
    issues += check_output_spec(output_spec_path)
  else:
    issues.append(Issue(ERROR, f'output_spec.csv not found at {output_spec_path}'))

  run_mask_path = runmonitor.resolve_io_path(io.get('runmask_file', ''), run_dir, input_catalog_dir, workflows_dir)
  veg_class_path = runmonitor.resolve_io_path(io.get('veg_class_file', ''), run_dir, input_catalog_dir, workflows_dir)
  parameters_dir = runmonitor.resolve_io_path(io.get('parameter_dir', 'parameters/'), run_dir, input_catalog_dir, workflows_dir)
  if run_mask_path.is_file() and veg_class_path.is_file() and parameters_dir.is_dir():
    issues += check_cmt_coverage(run_mask_path, veg_class_path, parameters_dir)

  return issues


def print_report(run_dir, issues):
  '''Print a human readable preflight report for `run_dir`.'''
  print(f'{"=" * 60}')
  print(f'Preflight: {run_dir}')
  print(f'{"=" * 60}')

  errors = [i for i in issues if i.level == ERROR]
  warnings = [i for i in issues if i.level == WARNING]

  if not issues:
    print('  No issues found.')
    return

  for issue in errors:
    print(f'  ERROR:   {issue.message}')
  for issue in warnings:
    print(f'  WARNING: {issue.message}')

  print(f'\n{len(errors)} error(s), {len(warnings)} warning(s).')


def cmdline_define():
  '''Define the command line interface and return the parser object.'''
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      Preflight checks for a dvmdostem run directory: directory layout,
      config.js integrity, output_spec.csv consistency, and that the
      parameter files cover every CMT present in the vegetation file at
      active run mask cells.
    ''')
  )
  parser.add_argument('run_dirs', nargs='+', metavar='RUN_DIR',
      help=textwrap.dedent('''One or more dvmdostem run directories to check.'''))

  parser.add_argument('--input-catalog-dir', metavar='DIR',
      help=textwrap.dedent('''Host directory to substitute for config.js
          paths starting with /data/input-catalog. Only needed when running
          outside the dvmdostem docker container; otherwise such paths are
          used as-is.'''))

  parser.add_argument('--workflows-dir', metavar='DIR',
      help=textwrap.dedent('''Host directory to substitute for config.js
          paths starting with /data/workflows. Only needed when running
          outside the dvmdostem docker container; otherwise such paths are
          used as-is.'''))

  return parser


def cmdline_parse(argv=None):
  '''
  Parameters
  ----------
  argv : None or list of strings
    arguments that argparse library will parse; if None, then sys.argv[1:]
    are parsed.

  Returns
  -------
  args : Namespace generated by argparse
  '''
  parser = cmdline_define()
  args = parser.parse_args(argv)
  return args


def cmdline_run(args):
  '''
  Executes based on the command line arguments.

  Parameters
  ----------
  args : Namespace

  Returns
  -------
  exit_code : int
    Non-zero if any run directory has an ERROR level issue.
  '''
  exit_code = 0
  for run_dir in args.run_dirs:
    issues = run_preflight(run_dir, input_catalog_dir=args.input_catalog_dir,
                            workflows_dir=args.workflows_dir)
    print_report(run_dir, issues)
    print()
    if any(i.level == ERROR for i in issues):
      exit_code = 1
  return exit_code


def cmdline_entry(argv=None):
  '''Wrapper allowing for easier testing of the cmdline run and parse functions.'''
  args = cmdline_parse(argv)
  return cmdline_run(args)


# adding this allows the script to be run standalone when installed with pip...
def main(argv=None):
  return cmdline_entry(argv=argv)


if __name__ == '__main__':
  import sys
  sys.exit(main())