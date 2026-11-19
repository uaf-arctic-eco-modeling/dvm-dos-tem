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

from pyddt.util import config as pyddt_config
from pyddt.util import input as pyddt_input
from pyddt.util.layout import DEFAULT_RUN_LAYOUT
from pyddt.util import outspec as pyddt_outspec
from pyddt.util import param as pyddt_param
from pyddt.util import runmonitor
from pyddt.util.test import ERROR, WARNING, Finding, report_findings


def check_directory_layout(run_dir):
  '''
  Check the run directory for the expected files/sub-directories.

  Parameters
  ----------
  run_dir : pathlib.Path

  Returns
  -------
  findings : list of Finding
  '''
  findings = []
  missing_directories = set()
  for relative_path, entry_type in DEFAULT_RUN_LAYOUT.items():
    path = run_dir / relative_path
    # A missing parent directory already explains why its files are absent.
    if any(parent in missing_directories for parent in path.parents):
      continue
    exists = path.is_dir() if entry_type == 'directory' else path.is_file()
    if not exists:
      status = WARNING if relative_path == 'calibration' else ERROR
      if entry_type == 'directory':
        missing_directories.add(path)
        message = f'{relative_path}/ directory not present.'
      elif relative_path == 'run-mask.nc':
        message = f'{relative_path} not present in the run directory.'
      else:
        message = f'{relative_path} not present.'
      findings.append(Finding(status, message, check_name='check_directory_layout'))
    elif relative_path == 'output' and any(path.iterdir()):
      findings.append(Finding(WARNING, 'output/ directory is not empty.', check_name='check_directory_layout'))

  return findings


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
  findings : list of Finding
  '''
  findings = []
  io = config.get('IO', {})

  def check_path(key, default, is_dir, standard_practice):
    '''Resolve io[key] (or `default`), warn if absolute, error if missing.'''
    raw = io.get(key, default)
    if not raw:
      findings.append(Finding(ERROR, f"config.js IO section is missing '{key}'", check_name='check_config_integrity'))
      return
    if Path(raw).is_absolute():
      findings.append(Finding(WARNING, f"IO.{key} ('{raw}') is an absolute path; {standard_practice}", check_name='check_config_integrity'))
    resolved = runmonitor.resolve_io_path(raw, run_dir, input_catalog_dir, workflows_dir)
    exists = resolved.is_dir() if is_dir else resolved.is_file()
    if not exists:
      findings.append(Finding(ERROR, f'IO.{key} not found: {resolved}', check_name='check_config_integrity'))

  check_path('runmask_file', None, is_dir=False,
             standard_practice='common practice is to keep run-mask.nc in the run directory with a relative path.')
  check_path('parameter_dir', 'parameters/', is_dir=True,
             standard_practice='common practice is to keep parameters/ in the run directory with a relative path.')
  check_path('output_dir', 'output/', is_dir=True,
             standard_practice='common practice is to keep output/ in the run directory with a relative path.')

  # the heavier inputs may legitimately be shared/absolute; just check they exist
  for key in pyddt_config.DEFAULT_INPUT_FILE_NAMES:
    if key == 'runmask_file':
      continue  # already checked above, with the relative-path warning
    raw = io.get(key)
    if not raw:
      findings.append(Finding(ERROR, f"config.js IO section is missing or empty '{key}'", check_name='check_config_integrity'))
      continue
    resolved = runmonitor.resolve_io_path(raw, run_dir, input_catalog_dir, workflows_dir)
    if not resolved.is_file():
      findings.append(Finding(ERROR, f'IO.{key} not found: {resolved}', check_name='check_config_integrity'))

  return findings


def check_output_spec(output_spec_path):
  '''
  Check an output_spec.csv file for required columns/consistency, that
  CMTNUM is enabled, and that layer-resolution outputs have LAYERDZ enabled.
  Warn when likely layer outputs are enabled without layer resolution.

  Parameters
  ----------
  output_spec_path : pathlib.Path

  Returns
  -------
  findings : list of Finding
  '''
  findings = []

  try:
    data = pyddt_outspec.csv_file_to_data_dict_list(str(output_spec_path))
  except (OSError, RuntimeError) as e:
    findings.append(Finding(ERROR, f'output_spec.csv is malformed: {e}', check_name='check_output_spec'))
    return findings

  def is_enabled(row):
    return any(row.get(res, '') not in ('', 'invalid') for res in ('Yearly', 'Monthly', 'Daily'))

  by_name = {row['Name']: row for row in data}

  # Does CMTNUM exist in the output_spec and is it enabled
  cmtnum_row = by_name.get('CMTNUM')
  if cmtnum_row is None:
    findings.append(Finding(ERROR, 'output_spec.csv has no CMTNUM row.', check_name='check_output_spec'))
  elif not is_enabled(cmtnum_row):
    findings.append(Finding(ERROR, 'CMTNUM output is not enabled in output_spec.csv.', check_name='check_output_spec'))

  # Are layer outputs (by resolution) enabled without LAYERDZ
  layerdz_row = by_name.get('LAYERDZ')
  layerdz_enabled = layerdz_row is not None and is_enabled(layerdz_row)

  forced_layer_vars = sorted(row['Name'] for row in data
                              if row.get('Layers') == 'forced' and row['Name'] != 'LAYERDZ' and is_enabled(row))
  if forced_layer_vars and not layerdz_enabled:
    findings.append(Finding(ERROR, f'Layer-resolution output(s) enabled ({", ".join(forced_layer_vars)}) but '
                               f'LAYERDZ is not enabled; per-layer values cannot be matched to depths.', check_name='check_output_spec'))

  # Are layer outputs (by name match) enabled without LAYERDZ
  layer_named_vars = sorted(row['Name'] for row in data
                             if 'LAYER' in row['Name'] and row['Name'] != 'LAYERDZ' and is_enabled(row))
  if layer_named_vars and not layerdz_enabled:
    findings.append(Finding(WARNING, f'Layer-description output(s) enabled ({", ".join(layer_named_vars)}) without '
                                 f'LAYERDZ; depths will not be available when interpreting them.', check_name='check_output_spec'))

  # Are layer outputs (by name match) enabled by time but not layer
  missing_layer_resolution = pyddt_outspec.warn_layer_resolution_disabled(data)
  if missing_layer_resolution:
    findings.append(Finding(WARNING, f'Output(s) likely to require layer resolution '
                                 f'({", ".join(missing_layer_resolution)}) are enabled by time '
                                 f'but have no Layers setting in output_spec.csv.', check_name='check_output_spec'))

  return findings


def check_cmt_coverage(run_mask_path, veg_class_path, parameters_dir):
  '''
  Confirm that every CMT present (in the vegetation file, at an active run
  mask cell) has a corresponding data block in every parameter file.

  Parameter coverage is determined by ``pyddt.util.param.get_CMTs_in_dir``.
  Unreadable files, malformed CMT headers, and repeated CMT definitions are
  reported as errors because coverage cannot be confirmed.

  Parameters
  ----------
  run_mask_path, veg_class_path, parameters_dir : pathlib.Path

  Returns
  -------
  findings : list of Finding
  '''
  findings = []

  mask_info = runmonitor.summarize_run_mask(run_mask_path)
  active_mask = mask_info['active_mask']

  try:
    veg_info = pyddt_input.count_cells_by_cmt(veg_class_path, active_mask)
  except (OSError, ValueError, KeyError, TypeError) as e:
    findings.append(Finding(ERROR, f'Cannot check CMT coverage: {e}', check_name='check_cmt_coverage'))
    return findings
  active_counts = veg_info['counts_active']

  active_cmts = sorted(set(int(v) for v in active_counts))

  try:
    available_cmts = set(pyddt_param.get_CMTs_in_dir(parameters_dir))
  except (OSError, UnicodeError, ValueError, AssertionError) as e:
    findings.append(Finding(ERROR, f'Cannot check parameter CMT coverage in {parameters_dir}: {e}', check_name='check_cmt_coverage'))
    return findings

  # The directory helper returns only CMTs present in every parameter file.
  for cmtnum in active_cmts:
    if cmtnum not in available_cmts:
      findings.append(Finding(ERROR, f'CMT{cmtnum:02d} is used by active run mask cell(s) but is not '
                                 f'defined in every parameter file in {parameters_dir}.', check_name='check_cmt_coverage'))

  return findings


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
  findings : list of Finding
  '''
  run_dir = Path(run_dir).resolve()
  findings = []

  findings += check_directory_layout(run_dir)

  config_path = run_dir / 'config' / 'config.js'
  if not config_path.is_file():
    findings.append(Finding(ERROR, f'config/config.js not found at {config_path}; skipping remaining checks.', check_name='load_config'))
    return findings
  try:
    config = pyddt_config.load_config(config_path)
  except (OSError, ValueError) as e:
    findings.append(Finding(ERROR, f'config/config.js could not be read/parsed ({e}); skipping remaining checks.', check_name='load_config'))
    return findings

  findings += check_config_integrity(run_dir, config, input_catalog_dir, workflows_dir)

  io = config.get('IO', {})
  output_spec_path = runmonitor.resolve_io_path(
      io.get('output_spec_file', 'config/output_spec.csv'), run_dir, input_catalog_dir, workflows_dir)
  if output_spec_path.is_file():
    findings += check_output_spec(output_spec_path)
  else:
    findings.append(Finding(ERROR, f'output_spec.csv not found at {output_spec_path}', check_name='check_output_spec'))

  run_mask_path = runmonitor.resolve_io_path(io.get('runmask_file', ''), run_dir, input_catalog_dir, workflows_dir)
  veg_class_path = runmonitor.resolve_io_path(io.get('veg_class_file', ''), run_dir, input_catalog_dir, workflows_dir)
  parameters_dir = runmonitor.resolve_io_path(io.get('parameter_dir', 'parameters/'), run_dir, input_catalog_dir, workflows_dir)
  if run_mask_path.is_file() and veg_class_path.is_file() and parameters_dir.is_dir():
    findings += check_cmt_coverage(run_mask_path, veg_class_path, parameters_dir)

  return findings


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
    Non-zero if any run directory has an ERROR status finding.
  '''
  exit_code = 0
  for run_dir in args.run_dirs:
    findings = run_preflight(run_dir, input_catalog_dir=args.input_catalog_dir,
                            workflows_dir=args.workflows_dir)
    report_findings(findings, title=f'Preflight: {run_dir}')
    print()
    if any(i.status == ERROR for i in findings):
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
