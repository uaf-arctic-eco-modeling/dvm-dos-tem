#!/usr/bin/env python3

import argparse
import os
import shutil
import sys
import textwrap
from datetime import datetime
from pathlib import Path

import netCDF4 as nc
import numpy as np
import xarray as xr

from pyddt.util import runmonitor

'''
This module provides utilties for resuming regional runs. If a region fails for
some reason (or the user interrupts it), this module helps in resuming the run
from the point of failure.

Generally when a dvmdostem run starts it clears the output directory, so in this
case we want to preserve the existing output and resume the run from where it
left off.

The tool starts by creating a new run mask that masks out all pixels from the
previous run that succeeded and enabled all unprocessed pixels from the previous
run.

Then the tool moves the existing output files to a temporary location, so that
the new run can start with a clean output directory while still preserving the
results from the previous run. Then the new run proceeds, processing only the
unprocessed pixels while keeping the results from the previous run intact.

Finally the tool merges the output files from the two runs, ensuring that the
results from both the previous and the new run are combined into a single
coherent output.

This module assumes it is running alongside (or inside) the dvmdostem docker
container: detecting whether a run is still active reads /proc (Linux only)
looking for `dvmdostem` processes, and `--workflows-dir` is used to translate
a host run directory into the container working directory a live process
would report.
'''


def load_run_status_values(status_path):
  '''Raw `run_status` values; see `runmonitor.summarize_run_status` for why mask_and_scale=False.'''
  with xr.open_dataset(status_path, mask_and_scale=False) as ds:
    return ds['run_status'].values


def find_dvmdostem_pids(run_dir, workflows_dir=None):
  '''
  Find pids of running `dvmdostem` processes that appear to be working on
  `run_dir`, by checking each process's current working directory.

  This only works on Linux (reads /proc) and only sees processes visible to
  the current user/pid-namespace - appropriate for checking from inside, or
  alongside, the dvmdostem docker container.

  Parameters
  ----------
  run_dir : str or pathlib.Path
    Host-side run directory to check for an active run.
  workflows_dir : str or pathlib.Path, optional
    Host directory mounted as `/data/workflows` in the dvmdostem container.
    If given and `run_dir` is under it, used to compute the exact
    in-container working directory a matching process should report.
    Otherwise falls back to a weaker heuristic: the process's cwd has the
    same final path component as `run_dir`.

  Returns
  -------
  pids : list of int
  '''
  run_dir = Path(run_dir).resolve()

  container_cwd_guess = None
  if workflows_dir is not None:
    workflows_dir = Path(workflows_dir).resolve()
    try:
      container_cwd_guess = Path('/data/workflows') / run_dir.relative_to(workflows_dir)
    except ValueError:
      pass

  proc_dir = Path('/proc')
  if not proc_dir.is_dir():
    return []

  pids = []
  for entry in proc_dir.iterdir():
    if not entry.name.isdigit():
      continue
    try:
      comm = (entry / 'comm').read_text().strip()
    except OSError:
      continue
    if comm != 'dvmdostem':
      continue
    try:
      cwd = Path(os.readlink(entry / 'cwd'))
    except OSError:
      continue
    if cwd == run_dir or cwd == container_cwd_guess or cwd.name == run_dir.name:
      pids.append(int(entry.name))
  return pids


def is_run_active(run_dir, workflows_dir=None):
  '''True if a `dvmdostem` process appears to be actively working on `run_dir`.'''
  return len(find_dvmdostem_pids(run_dir, workflows_dir)) > 0


def compute_resume_mask(active_mask, status_values, retry_failed=True):
  '''
  Which cells should be enabled in a resumed run: previously active cells
  that did not succeed.

  Parameters
  ----------
  active_mask : numpy.ndarray of bool
    Active-cell mask from `runmonitor.summarize_run_mask`.
  status_values : numpy.ndarray
    Raw `run_status` values, same shape as `active_mask`.
  retry_failed : bool
    If True (default), cells with FAIL or TIMEOUT status are also re-enabled
    for the resume run, not just cells that were never reached.

  Returns
  -------
  enable_mask : numpy.ndarray of bool
  '''
  not_done = status_values != runmonitor.STATUS_SUCCESS
  if not retry_failed:
    not_done &= (status_values != runmonitor.STATUS_FAIL) & (status_values != runmonitor.STATUS_TIMEOUT)
  return active_mask & not_done


def check_run(run_dir, input_catalog_dir=None, workflows_dir=None):
  '''
  Determine whether a run is actively running and/or stalled.

  Parameters
  ----------
  run_dir : str or pathlib.Path
  input_catalog_dir, workflows_dir : str or pathlib.Path, optional
    Passed through to `runmonitor.resolve_io_path` / `find_dvmdostem_pids`.

  Returns
  -------
  summary : dict
    `running` (bool), `pids` (list of int), `active_cells`, `n_completed`,
    `n_remaining`, and `stalled` (True if not running and cells remain).
  '''
  run_dir = Path(run_dir).resolve()
  config = runmonitor.load_run_config(run_dir)
  if config is None:
    raise RuntimeError(f'{run_dir}: config/config.js not found.')
  io = config.get('IO', {})

  run_mask_path = runmonitor.resolve_io_path(io['runmask_file'], run_dir, input_catalog_dir, workflows_dir)
  output_dir = runmonitor.resolve_io_path(io['output_dir'], run_dir, input_catalog_dir, workflows_dir)
  status_path = output_dir / 'run_status.nc'

  mask_info = runmonitor.summarize_run_mask(run_mask_path)
  status_info = runmonitor.summarize_run_status(status_path, mask_info['active_cells'])
  n_remaining = status_info['n_remaining'] if status_info else mask_info['active_cells']

  pids = find_dvmdostem_pids(run_dir, workflows_dir)

  return {
    'running': len(pids) > 0,
    'pids': pids,
    'active_cells': mask_info['active_cells'],
    'n_completed': status_info['n_completed'] if status_info else 0,
    'n_remaining': n_remaining,
    'stalled': len(pids) == 0 and n_remaining > 0,
  }


def backup_run_mask(run_mask_path):
  '''Copy the run mask aside before overwriting it, timestamped so repeated resumes don't clobber each other.'''
  timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
  backup_path = run_mask_path.with_name(f'{run_mask_path.stem}_pre-resume_{timestamp}{run_mask_path.suffix}')
  shutil.copy2(run_mask_path, backup_path)
  return backup_path


def write_resume_mask(run_mask_path, enable_mask):
  '''Write `enable_mask` (bool, same shape as the mask) into the `run` variable of `run_mask_path`.'''
  with nc.Dataset(run_mask_path, 'a') as ds:
    ds.variables['run'][:] = enable_mask.astype(ds.variables['run'].dtype)


def backup_output_dir(output_dir, backup_dir=None):
  '''Move `output_dir` aside so a resumed run can start with a clean output directory.'''
  if backup_dir is None:
    timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
    backup_dir = output_dir.parent / f'{output_dir.name}_pre-resume_{timestamp}'
  backup_dir = Path(backup_dir)
  if backup_dir.exists():
    raise RuntimeError(f'{backup_dir} already exists; choose a different backup directory.')
  shutil.move(str(output_dir), str(backup_dir))
  return backup_dir


def prepare_resume(run_dir, input_catalog_dir=None, workflows_dir=None, retry_failed=True,
                    backup_dir=None, force=False):
  '''
  Get a stalled run ready to resume: build a run mask that only enables cells
  that didn't succeed, and move the existing output directory aside so the
  resumed run starts clean.

  Parameters
  ----------
  run_dir : str or pathlib.Path
  input_catalog_dir, workflows_dir : str or pathlib.Path, optional
  retry_failed : bool
    See `compute_resume_mask`.
  backup_dir : str or pathlib.Path, optional
    Where to move the existing output directory; defaults to a timestamped
    sibling directory.
  force : bool
    Proceed even if a `dvmdostem` process still appears to be working on
    `run_dir`.

  Returns
  -------
  summary : dict
    `n_to_resume`, `run_mask_backup_path`, `output_backup_dir` (the latter
    two are None if there was nothing to resume).
  '''
  run_dir = Path(run_dir).resolve()

  if not force and is_run_active(run_dir, workflows_dir):
    raise RuntimeError(f'{run_dir}: a dvmdostem process is still running against this '
                        f'directory; pass force=True (--force) if this is wrong.')

  config = runmonitor.load_run_config(run_dir)
  if config is None:
    raise RuntimeError(f'{run_dir}: config/config.js not found.')
  io = config.get('IO', {})

  run_mask_path = runmonitor.resolve_io_path(io['runmask_file'], run_dir, input_catalog_dir, workflows_dir)
  output_dir = runmonitor.resolve_io_path(io['output_dir'], run_dir, input_catalog_dir, workflows_dir)
  status_path = output_dir / 'run_status.nc'

  mask_info = runmonitor.summarize_run_mask(run_mask_path)
  status_values = load_run_status_values(status_path)
  enable_mask = compute_resume_mask(mask_info['active_mask'], status_values, retry_failed=retry_failed)
  n_to_resume = int(np.count_nonzero(enable_mask))

  if n_to_resume == 0:
    return {'n_to_resume': 0, 'run_mask_backup_path': None, 'output_backup_dir': None}

  run_mask_backup_path = backup_run_mask(run_mask_path)
  write_resume_mask(run_mask_path, enable_mask)
  output_backup_dir = backup_output_dir(output_dir, backup_dir)

  return {
    'n_to_resume': n_to_resume,
    'run_mask_backup_path': run_mask_backup_path,
    'output_backup_dir': output_backup_dir,
  }


def merge_netcdf_file(old_path, new_path, success_mask):
  '''
  Patch `new_path` in place: for every (Y,X)-shaped variable also present in
  `old_path`, cells where `success_mask` is True are overwritten with the
  value from `old_path`; every other cell keeps the value already written in
  `new_path`. Variables without both a Y-like and X-like dimension (e.g. the
  `time` coordinate) are left untouched.
  '''
  with nc.Dataset(old_path) as old_ds, nc.Dataset(new_path, 'a') as new_ds:
    for name, var in new_ds.variables.items():
      if name not in old_ds.variables:
        continue
      dims = var.dimensions
      y_axis = next((i for i, d in enumerate(dims) if d.lower() == 'y'), None)
      x_axis = next((i for i, d in enumerate(dims) if d.lower() == 'x'), None)
      if y_axis is None or x_axis is None:
        continue

      new_values = var[:]
      old_values = old_ds.variables[name][:]
      if old_values.shape != new_values.shape:
        print(f'  WARNING: skipping "{name}" in {new_path.name} (shape mismatch between old and new files)')
        continue

      bcast_shape = [1] * new_values.ndim
      bcast_shape[y_axis] = success_mask.shape[0]
      bcast_shape[x_axis] = success_mask.shape[1]
      bcast_mask = success_mask.reshape(bcast_shape)

      var[:] = np.where(bcast_mask, old_values, new_values)


def merge_outputs(run_dir, backup_output_dir, input_catalog_dir=None, workflows_dir=None,
                   merged_output_dir=None, status_path_before=None):
  '''
  Merge a backed-up (pre-resume) output directory with the freshly produced
  output from a resumed run, into a new, complete output directory.

  Parameters
  ----------
  run_dir : str or pathlib.Path
  backup_output_dir : str or pathlib.Path
    The output directory saved off by `prepare_resume` (contains the results
    for the cells that had already succeeded).
  input_catalog_dir, workflows_dir : str or pathlib.Path, optional
  merged_output_dir : str or pathlib.Path, optional
    Where to write the merged output; defaults to a new
    `<output_dir>_merged` directory. Must not already exist.
  status_path_before : str or pathlib.Path, optional
    run_status.nc to use for deciding which cells came from the backup;
    defaults to `run_status.nc` inside `backup_output_dir`.

  Returns
  -------
  merged_output_dir : pathlib.Path
  '''
  run_dir = Path(run_dir).resolve()
  backup_output_dir = Path(backup_output_dir).resolve()

  config = runmonitor.load_run_config(run_dir)
  if config is None:
    raise RuntimeError(f'{run_dir}: config/config.js not found.')
  io = config.get('IO', {})
  new_output_dir = runmonitor.resolve_io_path(io['output_dir'], run_dir, input_catalog_dir, workflows_dir)

  if status_path_before is None:
    status_path_before = backup_output_dir / 'run_status.nc'
  old_status_values = load_run_status_values(Path(status_path_before))
  success_mask = old_status_values == runmonitor.STATUS_SUCCESS

  if merged_output_dir is None:
    merged_output_dir = new_output_dir.parent / f'{new_output_dir.name}_merged'
  merged_output_dir = Path(merged_output_dir)
  if merged_output_dir.exists():
    raise RuntimeError(f'{merged_output_dir} already exists; remove it or choose a '
                        f'different merged output directory.')
  shutil.copytree(new_output_dir, merged_output_dir)

  old_files = {p.name for p in backup_output_dir.glob('*.nc')}
  new_files = {p.name for p in merged_output_dir.glob('*.nc')}

  for filename in sorted(old_files & new_files):
    merge_netcdf_file(backup_output_dir / filename, merged_output_dir / filename, success_mask)

  # files the resumed run never touched (e.g. no cells left requiring them) - just restore as-is
  for filename in sorted(old_files - new_files):
    shutil.copy2(backup_output_dir / filename, merged_output_dir / filename)

  return merged_output_dir


def cmdline_define():
  '''Define the command line interface and return the parser object.'''
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      Detect stalled dvmdostem runs and help resume them: check whether a run
      is actively running and whether run_status.nc shows incomplete cells,
      build a run mask that only re-enables the cells that never succeeded,
      back up the partial output, and (after the resumed run finishes) merge
      the two sets of output back into one complete output directory.
    ''')
  )
  parser.add_argument('--workflows-dir', metavar='DIR',
      help=textwrap.dedent('''Host directory mounted as /data/workflows in
          the dvmdostem container. Improves detection of whether a run is
          still active when running outside the container.'''))

  subparsers = parser.add_subparsers(dest='command')

  status_parser = subparsers.add_parser('status',
      help=textwrap.dedent('''Report whether a run is actively running and/or
          stalled (not running, with incomplete cells).'''))
  status_parser.add_argument('run_dir', metavar='RUN_DIR')

  prepare_parser = subparsers.add_parser('prepare',
      help=textwrap.dedent('''Prepare a stalled run to be resumed: update the
          run mask and back up the existing output directory.'''))
  prepare_parser.add_argument('run_dir', metavar='RUN_DIR')
  prepare_parser.add_argument('--retry-failed', dest='retry_failed', action='store_true', default=True,
      help=textwrap.dedent('''Also re-enable cells that previously failed or
          timed out, not just cells that were never reached (default).'''))
  prepare_parser.add_argument('--no-retry-failed', dest='retry_failed', action='store_false',
      help=textwrap.dedent('''Only re-enable cells that were never reached;
          leave failed/timed-out cells masked out.'''))
  prepare_parser.add_argument('--backup-dir', metavar='DIR',
      help=textwrap.dedent('''Where to move the existing output directory.
          Defaults to a timestamped sibling of the output directory.'''))
  prepare_parser.add_argument('--force', action='store_true',
      help=textwrap.dedent('''Proceed even if a dvmdostem process still
          appears to be running against this run directory.'''))

  merge_parser = subparsers.add_parser('merge',
      help=textwrap.dedent('''Merge a resumed run's output back together with
          the output directory backed up by 'prepare'.'''))
  merge_parser.add_argument('run_dir', metavar='RUN_DIR')
  merge_parser.add_argument('backup_output_dir', metavar='BACKUP_OUTPUT_DIR',
      help=textwrap.dedent('''The output directory produced by the 'prepare'
          command.'''))
  merge_parser.add_argument('--merged-output-dir', metavar='DIR',
      help=textwrap.dedent('''Where to write the merged output. Defaults to a
          new "<output_dir>_merged" directory next to the resumed run's
          output directory.'''))

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
  if args.command is None:
    parser.error('a sub command is required (status, prepare, or merge).')
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
    Non-zero if the program cannot complete successfully (or, for `status`,
    if the run is found to be stalled).
  '''
  if args.command == 'status':
    info = check_run(args.run_dir, workflows_dir=args.workflows_dir)
    pid_note = f' (pids: {info["pids"]})' if info['pids'] else ''
    print(f'Run: {args.run_dir}')
    print(f'  running:   {info["running"]}{pid_note}')
    print(f'  completed: {info["n_completed"]} / {info["active_cells"]}')
    print(f'  remaining: {info["n_remaining"]}')
    print(f'  stalled:   {info["stalled"]}')
    return 1 if info['stalled'] else 0

  if args.command == 'prepare':
    try:
      result = prepare_resume(args.run_dir, workflows_dir=args.workflows_dir,
                               retry_failed=args.retry_failed, backup_dir=args.backup_dir,
                               force=args.force)
    except RuntimeError as e:
      print(f'ERROR: {e}')
      return 1
    if result['n_to_resume'] == 0:
      print('Nothing to resume: all active cells already succeeded.')
      return 0
    print(f'Cells to resume: {result["n_to_resume"]}')
    print(f'Run mask backed up to: {result["run_mask_backup_path"]}')
    print(f'Previous output moved to: {result["output_backup_dir"]}')
    print("Run mask updated in place. Start the model again to resume, then run the "
          "'merge' command once it finishes.")
    return 0

  if args.command == 'merge':
    try:
      merged_dir = merge_outputs(args.run_dir, args.backup_output_dir,
                                  workflows_dir=args.workflows_dir,
                                  merged_output_dir=args.merged_output_dir)
    except RuntimeError as e:
      print(f'ERROR: {e}')
      return 1
    print(f'Merged output written to: {merged_dir}')
    return 0

  return 0


def cmdline_entry(argv=None):
  '''Wrapper allowing for easier testing of the cmdline run and parse functions.'''
  args = cmdline_parse(argv)
  return cmdline_run(args)


# adding this allows the script to be run standalone when installed with pip...
def main(argv=None):
  return cmdline_entry(argv=argv)


if __name__ == '__main__':
  sys.exit(cmdline_entry())