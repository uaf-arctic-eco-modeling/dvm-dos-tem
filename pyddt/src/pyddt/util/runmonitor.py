#!/usr/bin/env python3

import argparse
import json
import sys
import textwrap
from pathlib import Path

import matplotlib

# Headless/no-DISPLAY environment: must select the backend before pyplot import.
matplotlib.use('Agg')
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

'''
Monitor the progress of a dvmdostem run (or several).

Reports, for each run directory passed on the command line:
1. the number of active cells in the run mask
2. the distribution of CMTs (vegetation classes), for the whole domain and
   for just the active cells
3. the current size on disk of the output directory
4. the state of the run_status.nc file: completed/remaining cells, successes,
   failures, timeouts, time spent so far, and an ETA based on the mean
   runtime of the completed cells

Only reads/plots existing dvmdostem input and output files, so this module is
standalone - it does not need to run inside the dvmdostem docker container,
though the `--input-catalog-dir`/`--workflows-dir` options are useful for
remapping container-style paths stored in config.js when running on the host.
'''

# dvmdostem run_status codes, from dvm-dos-tem/include/errorcode.h
STATUS_SUCCESS = 100
STATUS_MASKED = 0
STATUS_TIMEOUT = -5
STATUS_FAIL = -100
MISSING_I = -9999


def load_run_config(run_dir):
  '''
  Load a run's config/config.js file.

  Parameters
  ----------
  run_dir : pathlib.Path
    The dvmdostem run directory.

  Returns
  -------
  config : dict or None
    The parsed config.js contents, or None if the file doesn't exist.
  '''
  config_path = run_dir / 'config' / 'config.js'
  if not config_path.is_file():
    return None
  with open(config_path) as f:
    return json.load(f)


def resolve_io_path(raw_path, run_dir, input_catalog_dir=None, workflows_dir=None):
  '''
  Map a config.js IO path to a real path on disk.

  dvmdostem's config.js stores paths as seen from inside the docker
  container (e.g. `/data/input-catalog/...`, `/data/workflows/...`), as other
  absolute paths, or as paths relative to the run directory. When running
  outside the container, pass `input_catalog_dir`/`workflows_dir` to
  substitute the container-only prefixes with the real host directories;
  otherwise absolute paths are used as-is, which is correct when running
  inside the container (or when the path already exists on this machine).

  Parameters
  ----------
  raw_path : str
    Path as stored in config.js.
  run_dir : pathlib.Path
    Directory `raw_path` is resolved relative to, if it isn't absolute.
  input_catalog_dir : str or pathlib.Path, optional
    Host substitute for a leading `/data/input-catalog`.
  workflows_dir : str or pathlib.Path, optional
    Host substitute for a leading `/data/workflows`.

  Returns
  -------
  path : pathlib.Path
  '''
  if input_catalog_dir and raw_path.startswith('/data/input-catalog'):
    return Path(input_catalog_dir) / raw_path[len('/data/input-catalog/'):]
  elif workflows_dir and raw_path.startswith('/data/workflows'):
    return Path(workflows_dir) / raw_path[len('/data/workflows/'):]
  elif raw_path.startswith('/'):
    return Path(raw_path)
  else:
    return run_dir / raw_path


def format_bytes(n):
  '''Human readable byte count, e.g. `1536` -> `'1.50 KB'`.'''
  size = float(n)
  for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
    if size < 1024 or unit == 'TB':
      return f'{size:.2f} {unit}'
    size /= 1024


def total_runtime_to_seconds(raw_values):
  '''total_runtime may come back as raw int seconds or CF-decoded timedelta64, depending on xarray version.'''
  if np.issubdtype(raw_values.dtype, np.timedelta64):
    return raw_values / np.timedelta64(1, 's')
  return raw_values.astype(float)


def format_duration(seconds):
  '''Human readable duration, e.g. `90061` -> `'1d 1h 1m 1s'`.'''
  if seconds is None or not np.isfinite(seconds):
    return 'n/a'
  seconds = int(round(seconds))
  days, seconds = divmod(seconds, 86400)
  hours, seconds = divmod(seconds, 3600)
  minutes, seconds = divmod(seconds, 60)
  parts = []
  if days:
    parts.append(f'{days}d')
  if hours or days:
    parts.append(f'{hours}h')
  if minutes or hours or days:
    parts.append(f'{minutes}m')
  parts.append(f'{seconds}s')
  return ' '.join(parts)


def summarize_run_mask(mask_path):
  '''
  Summarize a dvmdostem run mask file.

  Parameters
  ----------
  mask_path : str or pathlib.Path
    Path to the run-mask.nc file.

  Returns
  -------
  summary : dict
    `total_cells`, `active_cells` (counts), and `active_mask` (boolean
    numpy.ndarray the same shape as the mask).
  '''
  with xr.open_dataset(mask_path) as ds:
    mask_values = ds['run'].values
  active = mask_values != 0
  return {
    'total_cells': active.size,
    'active_cells': int(np.count_nonzero(active)),
    'active_mask': active,
  }


def value_counts(values):
  '''Counts of each distinct value in `values`, as a dict.'''
  unique, counts = np.unique(values, return_counts=True)
  return dict(zip(unique.tolist(), counts.tolist()))


def summarize_vegetation(veg_path, active_mask):
  '''
  Summarize the CMT (vegetation class) distribution of a vegetation.nc file.

  Parameters
  ----------
  veg_path : str or pathlib.Path
    Path to the vegetation.nc file.
  active_mask : numpy.ndarray of bool
    Active-cell mask from `summarize_run_mask`, used to report counts for
    just the active cells.

  Returns
  -------
  summary : dict
    `counts_all` (dict of CMT -> count over the whole file) and
    `counts_active` (same, restricted to active cells, or None if
    `veg_path`'s shape doesn't match `active_mask`).
  '''
  with xr.open_dataset(veg_path) as ds:
    veg_values = ds['veg_class'].values

  counts_all = value_counts(veg_values)
  counts_active = None
  if veg_values.shape == active_mask.shape:
    counts_active = value_counts(veg_values[active_mask])
  return {'counts_all': counts_all, 'counts_active': counts_active}


def directory_size_bytes(path):
  '''Total size in bytes of all files under `path`, or 0 if it isn't a directory.'''
  if not path.is_dir():
    return 0
  return sum(item.stat().st_size for item in path.rglob('*') if item.is_file())


def summarize_run_status(status_path, active_cells):
  '''
  Summarize a dvmdostem run_status.nc file.

  Parameters
  ----------
  status_path : pathlib.Path
    Path to the run_status.nc file.
  active_cells : int
    Number of active cells in the run mask, used to compute `n_remaining`.

  Returns
  -------
  summary : dict or None
    None if `status_path` doesn't exist (run hasn't started). Otherwise a
    dict with `n_success`, `n_failed`, `n_timeout`, `n_masked`,
    `n_completed`, `n_remaining`, `total_runtime_seconds`,
    `mean_runtime_seconds`, and `eta_seconds`.
  '''
  if not status_path.is_file():
    return None

  # mask_and_scale=False: xarray's automatic fill-value handling mishandles
  # these int32 vars (produces an int64 min sentinel instead of NaN), so we
  # compare directly against the raw MISSING_I (-9999) fill value ourselves.
  with xr.open_dataset(status_path, mask_and_scale=False) as ds:
    status_values = ds['run_status'].values
    # total_runtime is only ever written for successful cells (see TEM.cpp)
    runtime_seconds = total_runtime_to_seconds(ds['total_runtime'].values)

  n_success = int(np.count_nonzero(status_values == STATUS_SUCCESS))
  n_failed = int(np.count_nonzero(status_values == STATUS_FAIL))
  n_timeout = int(np.count_nonzero(status_values == STATUS_TIMEOUT))
  n_masked = int(np.count_nonzero(status_values == STATUS_MASKED))
  n_completed = n_success + n_failed + n_timeout
  n_remaining = active_cells - n_completed

  success_runtimes = runtime_seconds[status_values == STATUS_SUCCESS]
  success_runtimes = success_runtimes[np.isfinite(success_runtimes)]
  total_runtime = float(success_runtimes.sum()) if success_runtimes.size else 0.0
  mean_runtime = float(success_runtimes.mean()) if success_runtimes.size else None
  eta_seconds = n_remaining * mean_runtime if mean_runtime is not None else None

  return {
    'n_success': n_success,
    'n_failed': n_failed,
    'n_timeout': n_timeout,
    'n_masked': n_masked,
    'n_completed': n_completed,
    'n_remaining': n_remaining,
    'total_runtime_seconds': total_runtime,
    'mean_runtime_seconds': mean_runtime,
    'eta_seconds': eta_seconds,
  }


def get_cmt_colormap(parameters_dir):
  '''Standard CMT color map (same colors as `pyddt-param --cmt-colormap-qgis`); falls back to tab20.'''
  try:
    import pyddt.util.param as pyddt_param
    return pyddt_param.build_cmt_colormap(str(parameters_dir))
  except Exception as e:
    print(f'  WARNING: falling back to default colormap for CMT plot ({e}). '
          f'Run with the tem-rs conda env active to use the pyddt CMT colormap.')
    return 'tab20', None


def overlay_inactive_mask(ax, active_mask, alpha=0.6):
  '''Draw solid gray over cells outside the run mask, transparent elsewhere.'''
  inactive = np.where(active_mask, np.nan, 1.0)
  ax.imshow(inactive, origin='lower', cmap=mcolors.ListedColormap(['0.5']),
            vmin=0, vmax=1, alpha=alpha)


def plot_run_summary(status_path, veg_path, parameters_dir, active_mask, save_path):
  '''
  Save a 3-panel imshow summary: total runtime, run status, and CMT vegetation map.

  Parameters
  ----------
  status_path : pathlib.Path
    Path to the run_status.nc file.
  veg_path : pathlib.Path
    Path to the vegetation.nc file.
  parameters_dir : pathlib.Path
    Parameter directory, used to build the CMT colormap.
  active_mask : numpy.ndarray of bool
    Active-cell mask from `summarize_run_mask`.
  save_path : pathlib.Path
    Where to save the resulting PNG; parent directories are created as needed.
  '''
  with xr.open_dataset(status_path, mask_and_scale=False) as ds:
    status_values = ds['run_status'].values
    runtime_minutes = total_runtime_to_seconds(ds['total_runtime'].values) / 60.0
  runtime_minutes[status_values != STATUS_SUCCESS] = np.nan
  # cells not yet reached by the (sequential) model run are left at MISSING_I; blank them out
  status_display = np.where(status_values == MISSING_I, np.nan, status_values).astype(float)

  fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(15, 5))

  im0 = axes[0].imshow(runtime_minutes, origin='lower', cmap='viridis')
  fig.colorbar(im0, ax=axes[0], label='minutes')
  axes[0].set_title('Total runtime (completed cells)')

  im1 = axes[1].imshow(status_display, origin='lower', cmap='RdYlGn', vmin=STATUS_FAIL, vmax=STATUS_SUCCESS)
  fig.colorbar(im1, ax=axes[1], label='run_status code')
  axes[1].set_title('Run status')

  if veg_path.is_file():
    with xr.open_dataset(veg_path) as ds:
      veg_values = ds['veg_class'].values
    cmap, norm = get_cmt_colormap(parameters_dir)
    im2 = axes[2].imshow(veg_values, origin='lower', cmap=cmap, norm=norm)
    fig.colorbar(im2, ax=axes[2], label='CMT')
    if veg_values.shape == active_mask.shape:
      overlay_inactive_mask(axes[2], active_mask)
    axes[2].set_title('Vegetation (CMT)\n(gray = outside run mask)')
  else:
    axes[2].set_title('Vegetation (CMT)\nfile not found')

  for ax in axes:
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
  fig.tight_layout()

  save_path.parent.mkdir(parents=True, exist_ok=True)
  fig.savefig(save_path, dpi=150)
  plt.close(fig)


def print_report(run_dir, input_catalog_dir=None, workflows_dir=None, plot=False):
  '''
  Print a progress report for a single dvmdostem run directory.

  Parameters
  ----------
  run_dir : str or pathlib.Path
    The dvmdostem run directory (must contain config/config.js).
  input_catalog_dir : str or pathlib.Path, optional
    Passed through to `resolve_io_path`.
  workflows_dir : str or pathlib.Path, optional
    Passed through to `resolve_io_path`.
  plot : bool
    If True, also save a status summary plot into a plots/ dir alongside the
    run's output directory.
  '''
  run_dir = Path(run_dir).resolve()
  print(f'{"=" * 60}')
  print(f'Run: {run_dir}')
  print(f'{"=" * 60}')

  if not run_dir.is_dir():
    print('  ERROR: run directory does not exist.')
    return

  config = load_run_config(run_dir)
  if config is None:
    print('  ERROR: config/config.js not found - cannot locate inputs/outputs.')
    return
  io = config.get('IO', {})

  run_mask_path = resolve_io_path(io['runmask_file'], run_dir, input_catalog_dir, workflows_dir)
  veg_path = resolve_io_path(io['veg_class_file'], run_dir, input_catalog_dir, workflows_dir)
  output_dir = resolve_io_path(io['output_dir'], run_dir, input_catalog_dir, workflows_dir)
  parameters_dir = resolve_io_path(io['parameter_dir'], run_dir, input_catalog_dir, workflows_dir)
  status_path = output_dir / 'run_status.nc'
  plots_dir = output_dir.parent / 'plots'

  # 1. run mask
  if not run_mask_path.is_file():
    print(f'  ERROR: run mask not found at {run_mask_path}')
    return
  mask_info = summarize_run_mask(run_mask_path)
  active_cells = mask_info['active_cells']
  total_cells = mask_info['total_cells']
  print(f'\nRun mask ({run_mask_path}):')
  print(f'  active cells: {active_cells} / {total_cells} '
        f'({100 * active_cells / total_cells:.1f}%)')

  # 2. vegetation / CMT distribution
  if veg_path.is_file():
    veg_info = summarize_vegetation(veg_path, mask_info['active_mask'])
    print(f'\nVegetation / CMT distribution ({veg_path}):')
    print(f'  whole file: {veg_info["counts_all"]}')
    if veg_info['counts_active'] is not None:
      print(f'  active cells only: {veg_info["counts_active"]}')
    else:
      print('  active cells only: n/a (shape mismatch with run mask)')
  else:
    print(f'\nVegetation file not found at {veg_path}')

  # 3. output directory volume
  print(f'\nOutput directory ({output_dir}):')
  if output_dir.is_dir():
    print(f'  size on disk: {format_bytes(directory_size_bytes(output_dir))}')
  else:
    print('  not found (run has likely not started).')

  # 4. run status
  print(f'\nRun status ({status_path}):')
  status_info = summarize_run_status(status_path, active_cells)
  if status_info is None:
    print('  not found (run has likely not started).')
    return

  print(f'  completed: {status_info["n_completed"]} / {active_cells}')
  print(f'  remaining: {status_info["n_remaining"]}')
  print(f'  succeeded: {status_info["n_success"]}')
  print(f'  failed:    {status_info["n_failed"]}')
  print(f'  timed out: {status_info["n_timeout"]}')
  print(f'  total time so far (successful cells): '
        f'{format_duration(status_info["total_runtime_seconds"])}')
  print(f'  estimated time remaining: '
        f'{format_duration(status_info["eta_seconds"])}')

  if plot:
    plot_path = plots_dir / f'{run_dir.name}_status_summary.png'
    plot_run_summary(status_path, veg_path, parameters_dir, mask_info['active_mask'], plot_path)
    print(f'  status summary plot saved to: {plot_path}')


def cmdline_define():
  '''Define the command line interface and return the parser object.'''
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      Report on the progress of one or more dvmdostem runs: active cells in
      the run mask, CMT (vegetation) distribution, output directory size, and
      run_status.nc completion/failure/timeout counts with an ETA for any
      cells still remaining.
    ''')
  )
  parser.add_argument('run_dirs', nargs='+', metavar='RUN_DIR',
      help=textwrap.dedent('''One or more dvmdostem run directories (each
          must contain a config/config.js file).'''))

  parser.add_argument('--plot', action='store_true',
      help=textwrap.dedent('''Save a runtime/status/vegetation summary plot
          into a plots/ dir alongside each run's output directory.'''))

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
    Always 0; problems with an individual run directory are reported inline
    rather than aborting the whole batch.
  '''
  for run_dir in args.run_dirs:
    print_report(run_dir, input_catalog_dir=args.input_catalog_dir,
                 workflows_dir=args.workflows_dir, plot=args.plot)
    print()
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
