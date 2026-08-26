#!/usr/bin/env python3
"""
WIEMIP postprocessing framework for dvm-dos-tem outputs.

Standalone CLI that orchestrates wetland merging, unit conversion,
variable combination, wiemip-specific name and unit conventions,
and visuals production.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import textwrap
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path

import time

import numpy as np
import netCDF4 as nc
import cfunits as ncascms_cfunits #Note that this is not the cf_units from Scitools
#from PIL import Image
from matplotlib.backends.backend_pdf import PdfPages

from pyddt.util.general import breakdown_outfile_name
from pyddt.util.netcdf import (
  copy_nc_file_structure_handles,
  get_compressor
)
from pyddt.util.output import (
  convert_units,
  sum_across_compartments,
  sum_across_layers,
  sum_across_pfts,
  weighted_combine_veg,
)

# Use sys.path.append('/path/to/dvm-dos-tem/scripts/')
# or add that directory to PYTHONPATH
from plots_wiemip import map_plot, ts_plot


@contextmanager
def _staged_output_file(destination: Path, source: Path | None = None):
  """Yield a temporary result path and publish it after successful writing.

  The temporary file is kept beside the destination so large regional files
  use the intended output filesystem. If ``source`` is supplied, its contents
  seed the temporary file before the caller modifies it.
  """
  destination = Path(destination).resolve()
  destination.parent.mkdir(parents=True, exist_ok=True)

  with tempfile.TemporaryDirectory(
    prefix=f".{destination.stem}_",
    dir=destination.parent,
  ) as temporary_directory:
    temporary_path = Path(temporary_directory) / destination.name
    if source is not None:
      shutil.copy2(source, temporary_path)

    try:
      yield temporary_path
    except Exception:
      # Preserve any previous result when processing fails. The temporary
      # directory removes the incomplete file as this exception propagates.
      raise
    else:
      # Writers using this context have closed before this copy occurs, so all
      # NetCDF metadata and buffered array data are complete on disk.
      if destination.exists():
        print(
          f"Skipping {destination.name}: result file already exists at "
          f"{destination}"
        )
      else:
        shutil.copy2(temporary_path, destination)


def _result_exists(destination: Path) -> bool:
  """Report an existing result so a processing loop can safely skip it."""
  destination = Path(destination)
  if destination.exists():
    print(f"Skipping {destination.name}: result file already exists at {destination}")
    return True
  return False

# Test, then move to pyddt?
def _varname_from_outfile(nc_path: Path) -> str | None:
  """Return the dvmdostem variable name, or None if the filename does not match.

  Accepts the standard ``VAR_timeres_stage.nc`` pattern and extra stem suffixes
  such as ``_unitsconverted``.
  """
  try:
    _, varname, _, _ = breakdown_outfile_name(str(nc_path))
    return varname
  except ValueError:
    parts = nc_path.stem.split('_')
    if len(parts) < 3:
      return None
    return parts[0]

# Test, combine with above, then move to pyddt?
def _timestep_from_outfile(nc_path: Path) -> str | None:
  """Return the dvmdostem timestep, or None if the filename does not match.

  Accepts the standard ``VAR_timeres_stage.nc`` pattern and extra stem suffixes
  such as ``_unitsconverted``.
  """
  try:
    _, _, timestep, _ = breakdown_outfile_name(str(nc_path))
    return timestep
  except ValueError:
    parts = nc_path.stem.split('_')
    if len(parts) < 3:
      return None
    return parts[1]


# ---------------------------------------------------------------------------
# Section 1: Wetland merging
# ---------------------------------------------------------------------------

def wetland_merging(
  directory_a: Path,
  directory_b: Path,
  wetland: Path,
  output_directory: Path,
) -> None:
  """Merge wetland-related outputs from the two input directories.

  Uses ``weighted_combine_veg`` with vegetation percent cover from
  ``wetland`` (expects ``veg_pct_cov`` and ``veg_class``).

  Parameters
  ----------
  directory_a, directory_b
    Source run/output directories to merge.
  wetland
    NetCDF with vegetation information (``veg_pct_cov``, ``veg_class``)
    used as weights for the merge.
  output_directory
    Destination for merged products.
  """
  output_directory.mkdir(parents=True, exist_ok=True)

  files_a = {p.name for p in directory_a.glob('*.nc')}
  files_b = {p.name for p in directory_b.glob('*.nc')}

  only_a = sorted(files_a - files_b)
  only_b = sorted(files_b - files_a)
  common = sorted(files_a & files_b)

  #TODO Handle single side variables - weight as usual by wetland pct
  # but with only one file
  burn_only_vars = ['BURNSOIL2AIRC', 'BURNTHICK', 'BURNVEG2AIRC']
  wetland_only_vars = ['CH4EFFLUXTOT']
  base_only_vars = ['SOC0_100cm']

  for filename in only_a:
    print(f"Skipping {filename}: present in {directory_a}, missing from {directory_b}")
  for filename in only_b:
    print(f"Skipping {filename}: present in {directory_b}, missing from {directory_a}")

  for filename in common:
    result_filepath = output_directory / filename
    if _result_exists(result_filepath):
      continue

    print(f"Merging {filename}")
    # weighted_combine_veg completes the NetCDF file in temporary storage and
    # closes all HDF5 handles before copying the result into this directory.
    # A failed merge therefore cannot leave a partial file at the final path.
    weighted_combine_veg(
      str(directory_a / filename),
      str(directory_b / filename),
      wetland_file=str(wetland),
      outfile=str(result_filepath),
    )


# ---------------------------------------------------------------------------
# Section 2: Unit conversion
# ---------------------------------------------------------------------------

def _next_time_coordinate(date, timestep: str):
  """Return the expected boundary following the final time coordinate."""
  if timestep == 'monthly':
    next_month = date.month % 12 + 1
    next_year = date.year + (date.month // 12)
    return date.replace(year=next_year, month=next_month)
  if timestep == 'yearly':
    return date.replace(year=date.year + 1)
  if timestep == 'daily':
    return date + timedelta(days=1)
  raise RuntimeError(f"Cannot infer timestep duration for {timestep!r}")


def _time_step_seconds(dataset: nc.Dataset, timestep: str) -> np.ndarray:
  """Calculate the duration represented by each time coordinate in seconds."""
  if 'time' not in dataset.variables:
    raise RuntimeError("Time-dependent unit conversion requires a time variable")

  time_var = dataset.variables['time']
  if 'units' not in time_var.ncattrs() or 'calendar' not in time_var.ncattrs():
    raise RuntimeError(
      "Time-dependent unit conversion requires time:units and time:calendar"
    )

  time_units = time_var.units
  calendar = time_var.calendar
  bounds_name = getattr(time_var, 'bounds', None)

  if bounds_name and bounds_name in dataset.variables:
    # Explicit bounds are the most direct description of the interval
    # represented by each accumulated flux value.
    bounds = dataset.variables[bounds_name][:]
    if bounds.ndim != 2 or bounds.shape != (len(time_var), 2):
      raise RuntimeError(
        f"Time bounds {bounds_name!r} must have shape ({len(time_var)}, 2); "
        f"found {bounds.shape}"
      )
    starts = nc.num2date(bounds[:, 0], time_units, calendar=calendar)
    stops = nc.num2date(bounds[:, 1], time_units, calendar=calendar)
  else:
    # dvmdostem outputs normally store interval starts without explicit bounds.
    # Adjacent coordinates define every interval except the last; extend the
    # final coordinate by one calendar-aware model timestep.
    starts = list(nc.num2date(time_var[:], time_units, calendar=calendar))
    if not starts:
      return np.asarray([], dtype=float)
    stops = starts[1:] + [_next_time_coordinate(starts[-1], timestep)]

  durations = np.asarray(
    [(stop - start).total_seconds() for start, stop in zip(starts, stops)],
    dtype=float,
  )
  if np.any(durations <= 0):
    raise RuntimeError("Time coordinates must describe positive-duration intervals")
  return durations


def _convert_accumulated_flux_to_rate(
  nc_filepath: Path,
  output_filepath: Path,
  varname: str,
  target_units: str,
) -> None:
  """Convert a per-timestep accumulated flux to a per-second rate."""
  if target_units != 'kg/m2/s':
    raise RuntimeError(
      f"Manual time conversion to {target_units!r} is not implemented"
    )

  # Seed the staged result with all dimensions, coordinates, metadata, and
  # variables from the source file, then modify only the scientific variable.
  shutil.copy2(nc_filepath, output_filepath)
  with nc.Dataset(str(output_filepath), 'r+') as dataset:
    if varname not in dataset.variables:
      raise RuntimeError(f"{varname!r} not found in {nc_filepath}")

    data_var = dataset.variables[varname]
    if not data_var.dimensions or data_var.dimensions[0] != 'time':
      raise RuntimeError(
        f"{varname!r} must use time as its first dimension; "
        f"found {data_var.dimensions}"
      )
    if 'units' not in data_var.ncattrs():
      raise RuntimeError(f"{varname!r} has no units attribute")

    timestep = _timestep_from_outfile(nc_filepath)
    period_by_timestep = {
      'daily': 'day',
      'monthly': 'month',
      'yearly': 'year',
    }
    if timestep not in period_by_timestep:
      raise RuntimeError(f"Unsupported timestep {timestep!r} for {nc_filepath}")

    incoming_units = ncascms_cfunits.Units(data_var.units)
    mass_per_period_units = ncascms_cfunits.Units(
      f"kg/m2/{period_by_timestep[timestep]}"
    )
    if not incoming_units.equivalent(mass_per_period_units):
      raise RuntimeError(
        f"Cannot convert {varname} from {data_var.units!r}; expected units "
        f"equivalent to {mass_per_period_units}"
      )

    seconds_per_step = _time_step_seconds(dataset, timestep)
    if len(seconds_per_step) != data_var.shape[0]:
      raise RuntimeError(
        f"Time axis has {len(seconds_per_step)} entries but {varname} has "
        f"{data_var.shape[0]}"
      )

    # Work in bounded blocks so conversion does not load a regional variable
    # into memory all at once. Ellipsis retains any PFT, layer, y, and x axes.
    block_size = 120
    block_count = data_var.shape[0] / block_size
    for block_start in range(0, data_var.shape[0], block_size):
      block_stop = min(block_start + block_size, data_var.shape[0])
      print(
        f"Converting block {block_start/block_size+1} of {block_count} "
        f"for {varname}"
      )
      data_slice = data_var[block_start:block_stop, ...]
      mass_per_period = ncascms_cfunits.Units.conform(
        data_slice, incoming_units, mass_per_period_units
      )
      duration_shape = (block_stop - block_start,) + (1,) * (data_var.ndim - 1)
      duration_seconds = seconds_per_step[block_start:block_stop].reshape(
        duration_shape
      )
      data_var[block_start:block_stop, ...] = mass_per_period / duration_seconds

    old_units = data_var.units
    data_var.setncattr('units', target_units)
    history_note = (
      f"Converted {varname} from {old_units} accumulated per "
      f"{period_by_timestep[timestep]} "
      f"timestep to {target_units} using time:units={dataset.variables['time'].units!r} "
      f"and time:calendar={dataset.variables['time'].calendar!r}"
    )
    if 'units_history' in dataset.ncattrs():
      dataset.units_history = f"{dataset.units_history}; {history_note}"
    else:
      dataset.units_history = history_note


def unit_conversion(directory: Path, output_directory: Path) -> None:
  """Convert listed variables in ``directory`` to target units.

  For each NetCDF whose variable appears in ``unit_specifiers``, writes a
  file under ``output_directory`` with ``_unitsconverted`` inserted before
  the extension. Accumulated fluxes with per-second targets use the file's
  calendar and time coordinates; other variables use
  ``pyddt.util.output.convert_units``.

  Parameters
  ----------
  directory
    Directory of dvmdostem output NetCDFs to convert.
  output_directory
    Destination directory for unit-converted products.
  """
  # Manually specified target units for the variables that need conversion.
  # Files for the variables not listed here will be copied through to
  # the output directory unchanged.
  # LAI is m2/m2 (unitless) and does not need converting
  # ALD, SNOWTHICK, WATERTAB are already 'm'
  # SWE is already kg/m2
  skip_converting = ['LAI', 'ALD', 'SNOWTHICK', 'WATERTAB', 'SWE']

  # Unit strings for the data calculation part of unit conversion. These
  # aren't exactly what WIEMIP wants because the converting library
  # doesn't handle 'kg/m2/s' to 'kg C/m2/s'. The 'C' and 'N' will be added
  # to the unit strings in a later segment.
  unit_specifiers = {
    'AVLN': 'kg/m2',
    'BURNSOIL2AIRC': 'kg/m2/s',
    'BURNVEG2AIRC': 'kg/m2/s',
    'CH4EFFLUXTOT': 'kg/m2/s',
#    'DWDC': 'kg/m2', #Check what we actually output (g/m2/time)
#    'EET': 'kg/m2/s', #Check what we output (mm/m2/time)
    'GPP': 'kg/m2/s',
    'NETNMIN': 'kg/m2/s',
    'NPP': 'kg/m2/s',
    'ORGN': 'kg/m2',
    'RHSOM': 'kg/m2/s',
#    'SNOWFALL': 'kg/m2/s', #TODO Special handling. TEM units: mm
    'SOC': 'kg/m2',
    'SOC0_100cm': 'kg/m2',
    'SOMA': 'kg/m2',
    'SOMCR': 'kg/m2',
    'SOMPR': 'kg/m2',
    'SOMRAWC': 'kg/m2',
    'TLAYER': 'degree_K',
#    'TRANSPIRATION': 'kg/m2/s', #TODO special handling? TEM units: mm/day
    'VEGC': 'kg/m2',
    'VEGNTOT': 'kg/m2',
#    'VWCLAYER': 'kg/m2', #TODO special handling? TEM units: m3/m3
  }

  # Rates with a per-second target need calendar-aware conversion. A monthly
  # accumulated value cannot use one fixed seconds-per-month constant because
  # month length depends on both month and the file's model calendar.
  time_conversion_specifiers = {
    varname: target_units
    for varname, target_units in unit_specifiers.items()
    if '/s' in target_units
  }
  standard_conversion_specifiers = {
    varname: target_units
    for varname, target_units in unit_specifiers.items()
    if varname not in time_conversion_specifiers
  }


  output_directory.mkdir(parents=True, exist_ok=True)

  for nc_path in sorted(directory.glob('*.nc')):
    try:
      _, varname, _, _ = breakdown_outfile_name(str(nc_path))
    except ValueError:
      continue

    if varname not in unit_specifiers and varname not in skip_converting:
      print(f"{varname} does not have unit conversion, FIX THIS")
      output_filepath = output_directory / nc_path.name
      if _result_exists(output_filepath):
        continue
      with _staged_output_file(output_filepath, source=nc_path):
        # Retain the unconverted input without exposing a partial destination.
        pass
      continue

    if varname not in unit_specifiers:
      print(f"{varname} does not require unit conversion, copying unchanged")
      output_filepath = output_directory / nc_path.name
      if _result_exists(output_filepath):
        continue
      with _staged_output_file(output_filepath, source=nc_path):
        # Supplying source creates the complete temporary copy; no additional
        # scientific processing is required for this variable.
        pass
      continue

    print(f"Converting {varname} to {unit_specifiers[varname]}")
    output_filepath = output_directory / f"{nc_path.stem}_unitsconverted{nc_path.suffix}"
    if _result_exists(output_filepath):
      continue

    if varname in time_conversion_specifiers:
      # Per-timestep accumulated fluxes require the duration represented by
      # each time coordinate, so they are handled locally instead of by the
      # general unit converter.
      with _staged_output_file(output_filepath) as temporary_output_filepath:
        _convert_accumulated_flux_to_rate(
          nc_path,
          temporary_output_filepath,
          varname,
          time_conversion_specifiers[varname],
        )
      continue

    if varname not in standard_conversion_specifiers:
      raise RuntimeError(f"No standard unit conversion configured for {varname}")

    # Variables with units that do not include time
    with _staged_output_file(output_filepath) as temporary_output_filepath:
      convert_units(
        str(nc_path),
        standard_conversion_specifiers[varname],
        output_filepath=str(temporary_output_filepath),
        varname=varname,
      )


# ---------------------------------------------------------------------------
# Section 3: Variable combination
# ---------------------------------------------------------------------------

def variable_combination(directory: Path, output_directory: Path) -> None:
  """Sum PFT- or layer-resolved variables to ecosystem totals.

  For each NetCDF in ``directory`` whose variable appears in
  ``pft_to_ecosystem`` or ``layer_to_ecosystem``, preserves the resolved file
  and writes a second ecosystem-total file under ``output_directory``. Total
  variable names append ``TOT``, except ``VWCLAYER``, which becomes ``VWCTOT``.

  Parameters
  ----------
  directory
    Directory of dvmdostem output NetCDFs (or intermediates from prior steps).
  output_directory
    Destination for summed / derived products.
  """
  output_directory.mkdir(parents=True, exist_ok=True)

  incoming_files = sorted(directory.glob('*.nc'))

  # Multi-file additions
  multi_file_additions = {
    'BURNC2AIR': {
      'input_vars': ['BURNVEG2AIRC', 'BURNSOIL2AIRC'],
      'guide_var': "BURNVEG2AIRC"
    },
    'LFTOTC': {
      'input_vars': ['LFNVC', 'LFVC'],
      'guide_var': "LFNVC"
    },
    'NUPTAKETOT': {
      'input_vars': ['NUPTAKELAB', 'NUPTAKEST'],
      'guide_var': "NUPTAKELAB"
    },
    'SOILPOOLSSUMMED': {
      'input_vars': ['SOMA', 'SOMCR', 'SOMPR', 'SOMRAWC'],
      'guide_var': "SOMA"
    }
  }

  extra_computation = {
    'fCH4Fire': ['BURNVEG2AIRC', 'BURNSOIL2AIRC', 'bonus addition'],
    'fdepth': ['LAYERDZ', 'TLAYER']
  } #TODO

  # Multi-file subtractions
  multi_file_subtractions = {
    'SOCBELOW1M': {
      'input_vars': ['SOC', 'SOC0_100cm'], #SOC - SOC0_100cm
      'guide_var': "SOC"
    },
    'GPPMINUSNPP': {
      'input_vars': ['GPP', 'NPP'], #GPP - NPP
      'guide_var': "GPP"
    }
  }

  # Index inputs by their TEM variable, time resolution, and stage. Extra
  # filename suffixes (for example, ``_unitsconverted``) are intentionally
  # ignored when establishing compatibility between files.
  input_index = {}
  for filepath in incoming_files:
    parts = filepath.stem.split('_')
    if len(parts) < 3:
      continue
    key = tuple(parts[:3])
    if key in input_index:
      raise RuntimeError(
        f"Multiple input files match variable/timestep/stage {key}: "
        f"{input_index[key]} and {filepath}"
      )
    input_index[key] = filepath

  # Combine the dictionaries above into a cohesive single structure
  # with function pointers indicating which operation to use
  composite_specs = [
    (combined_varname, spec, np.ma.add)
    for combined_varname, spec in multi_file_additions.items()
  ] + [
    (combined_varname, spec, np.ma.subtract)
    for combined_varname, spec in multi_file_subtractions.items()
  ]

  for combined_varname, spec, operation in composite_specs:
    guide_varname = spec['guide_var']
    guide_keys = [key for key in input_index if key[0] == guide_varname]

    if not guide_keys:
      print(f"Skipping {combined_varname}: no {guide_varname} guide file found")
      continue

    for _, timeres, stg in guide_keys:
      input_paths = []
      missing_vars = []
      for tem_varname in spec['input_vars']:
        filepath = input_index.get((tem_varname, timeres, stg))
        if filepath is None:
          missing_vars.append(tem_varname)
        else:
          input_paths.append(filepath)

      if missing_vars:
        print(
          f"Skipping {combined_varname}_{timeres}_{stg}: missing "
          f"{', '.join(missing_vars)}"
        )
        continue

      guide_filepath = input_index[(guide_varname, timeres, stg)]
      out_filepath = directory / f"{combined_varname}_{timeres}_{stg}_composite.nc"
      if _result_exists(out_filepath):
        continue
      print(
        f"Creating {out_filepath.name} from "
        f"{', '.join(path.name for path in input_paths)}"
      )

      paths_to_open = list(dict.fromkeys([guide_filepath, *input_paths]))
      file_handles = [nc.Dataset(str(path), 'r') for path in paths_to_open]
      try:
        datasets_by_path = dict(zip(paths_to_open, file_handles))
        input_vars = [
          datasets_by_path[path].variables[tem_varname]
          for path, tem_varname in zip(input_paths, spec['input_vars'])
        ]
        guide_dataset = datasets_by_path[guide_filepath]
        guide_variable = guide_dataset.variables[guide_varname]

        for tem_varname, input_var in zip(spec['input_vars'], input_vars):
          if input_var.dimensions != guide_variable.dimensions:
            raise RuntimeError(
              f"Cannot create {combined_varname}: {tem_varname} dimensions "
              f"{input_var.dimensions} differ from {guide_varname} dimensions "
              f"{guide_variable.dimensions}"
            )
          if input_var.shape != guide_variable.shape:
            raise RuntimeError(
              f"Cannot create {combined_varname}: {tem_varname} shape "
              f"{input_var.shape} differs from {guide_varname} shape "
              f"{guide_variable.shape}"
            )

        # Create output file and variable, using the variable indicated
        # the 'guide' variable
        with _staged_output_file(out_filepath) as temporary_out_filepath, \
             nc.Dataset(str(temporary_out_filepath), 'w') as dst:
          copy_nc_file_structure_handles(
            guide_dataset, dst, guide_varname, drop_dims=[]
          )

          fill_value = getattr(guide_variable, '_FillValue', None)
          kwargs = {'fill_value': fill_value} if fill_value is not None else {}
          filters = guide_variable.filters()
          compressor = get_compressor(filters)
          if compressor == 'zlib':
            kwargs['zlib'] = True
            kwargs['complevel'] = filters['complevel']
            kwargs['shuffle'] = filters.get('shuffle', False)
          chunking = guide_variable.chunking()
          if chunking != 'contiguous':
            kwargs['chunksizes'] = chunking

          output_var = dst.createVariable(
            combined_varname,
            guide_variable.dtype,
            guide_variable.dimensions,
            **kwargs,
          )
          output_var.setncatts({
            name: value for name, value in guide_variable.__dict__.items()
            if name != '_FillValue'
          })
          output_var.setncattr('source_variables', ' '.join(spec['input_vars']))

          # Block size being hardcoded is not ideal, but we're working with
          # it for now
          block_size = 120
          for block_start in range(0, guide_variable.shape[0], block_size):
            block_stop = min(block_start + block_size, guide_variable.shape[0])
            combined_data = input_vars[0][block_start:block_stop, ...]
            for input_var in input_vars[1:]:
              combined_data = operation(
                combined_data, input_var[block_start:block_stop, ...]
              )
            output_var[block_start:block_stop, ...] = combined_data

          symbol = '+' if operation is np.ma.add else '-'
          history_note = (
            f"Created {combined_varname} as "
            f"{f' {symbol} '.join(spec['input_vars'])}"
          )
          if 'history' in dst.ncattrs():
            dst.history = f"{dst.history}; {history_note}"
          else:
            dst.history = history_note
      finally:
        for file_handle in file_handles:
          file_handle.close()

  # Refresh the 'incoming' files due to multi-file composites
  incoming_files = sorted(directory.glob('*.nc'))

  pft_to_ecosystem = {'GPP', 'LAI', 'NPP', 'VEGC'}
  # LAYERDZ and TLAYER are also by-layer, but if we want them summed it will
  # require custom handling.
  layer_to_ecosystem = {'RHSOM', 'SOC', 'VWCLAYER'}

  ignored_files = [
    path for path in incoming_files
    if _varname_from_outfile(path) not in pft_to_ecosystem
    and _varname_from_outfile(path) not in layer_to_ecosystem
  ]
  print(f"Variable combination, ignoring: {ignored_files}")

  # Sum all variables specified to a 'total' file
#  for nc_path in sorted(directory.glob('*.nc')):
  for nc_path in incoming_files:
    varname = _varname_from_outfile(nc_path)
    if varname is None:
      print(f"No variable name parsed from {nc_path}")
      continue

    if varname in pft_to_ecosystem or varname in layer_to_ecosystem:
      drop_dim = 'pft' if varname in pft_to_ecosystem else 'layer'
      # WIEMIP calls the total of VWCLAYER VWCTOT. All other resolved
      # variables retain their full base name and append TOT.
      total_varname = (
        'VWCTOT' if varname == 'VWCLAYER' else f"{varname}TOT"
      )
      total_stem = nc_path.stem.replace(varname, total_varname, 1)
      total_output_filepath = (
        output_directory / f"{total_stem}_summed{nc_path.suffix}"
      )

      # Preserve the PFT- or layer-resolved scientific variable alongside its
      # ecosystem total. These files are independent results, so either one
      # can be produced when the other already exists.
      resolved_output_filepath = output_directory / nc_path.name
      if not _result_exists(resolved_output_filepath):
        with _staged_output_file(resolved_output_filepath, source=nc_path):
          pass

      if _result_exists(total_output_filepath):
        continue

      print(
        f"Combining {varname} across {drop_dim} into {total_varname}"
      )
      with _staged_output_file( \
             total_output_filepath
           ) as temporary_output_filepath, \
           nc.Dataset(str(nc_path), 'r') as src, \
           nc.Dataset(temporary_output_filepath, 'w') as dst:
        if varname not in src.variables:
          raise RuntimeError(f"{varname} not found in {str(nc_path)}")

        src_var = src.variables[varname]
        if drop_dim not in src_var.dimensions:
          raise RuntimeError(
            f"Cannot sum {varname} across {drop_dim}: variable dimensions are "
            f"{src_var.dimensions}"
          )
        if src_var.ndim == 5:
          raise RuntimeError(
            f"{varname} has 5 dimensions and is probably by-compartment; "
            "5-dimensional files are not currently handled"
          )

        drop_dims = [drop_dim]
        copy_nc_file_structure_handles(src, dst, varname, drop_dims)
        out_dims = tuple(
          dim for dim in src_var.dimensions if dim not in drop_dims
        )
        fill_value = getattr(src_var, '_FillValue', None)
        kwargs = {'fill_value': fill_value} if fill_value is not None else {}

        # Remove the aggregated dimension from the source chunk layout while
        # retaining chunk sizes for time and the remaining spatial dimensions.
        source_chunking = src_var.chunking()
        if source_chunking != 'contiguous':
          dst_var_chunking = list(source_chunking)
          del dst_var_chunking[src_var.dimensions.index(drop_dim)]
          kwargs['chunksizes'] = dst_var_chunking
          print(f"Manual dst var chunking: {dst_var_chunking}")

        compressor = get_compressor(src_var.filters())
        if compressor == "zlib":
          kwargs['zlib'] = True
          kwargs['complevel'] = src_var.filters()['complevel']
          kwargs['shuffle'] = src_var.filters().get('shuffle', False)
        elif compressor is not None:
          raise RuntimeError(
            f"kwargs for compressor {compressor} not implemented"
          )

        output_var = dst.createVariable(
          total_varname,
          src_var.dtype,
          out_dims,
          **kwargs,
        )
        output_var.setncatts({
          name: value for name, value in src_var.__dict__.items()
          if name != '_FillValue'
        })
        output_var.setncattr('source_variable', varname)

        # Work in bounded time blocks and retain all remaining dimensions with
        # ellipsis. The aggregation axis is located from the variable metadata
        # rather than assuming PFT or layer is always dimension number one.
        block_size = 120
        aggregation_axis = src_var.dimensions.index(drop_dim)
        for block_start in range(0, src_var.shape[0], block_size):
          block_stop = min(block_start + block_size, src_var.shape[0])
          data_slice = src_var[block_start:block_stop, ...]
          print(data_slice.shape)
          summed_slice = np.ma.sum(data_slice, axis=aggregation_axis)
          output_var[block_start:block_stop, ...] = summed_slice

        print(f"Done creating {total_varname}")
        history_note = (
          f"Created {total_varname} from {varname}; summed across {drop_dim}"
        )
        if 'history' in dst.ncattrs():
          dst.history = f"{dst.history}; {history_note}"
        else:
          dst.history = history_note

    # varname has no summing specified
    else:
      print(f"{varname} has no dimension summing, copying unchanged")
      output_filepath = output_directory / nc_path.name
      if _result_exists(output_filepath):
        continue
      with _staged_output_file(output_filepath, source=nc_path):
        # This variable requires no calculation, but follows the same staged
        # publication rule as newly generated ecosystem totals.
        pass
      continue


# ---------------------------------------------------------------------------
# Section 4: Conform to WIEMIP naming/formatting
# ---------------------------------------------------------------------------
def conform_to_wiemip(
  directory: Path,
  gcm_short: str ("stable"),
  exp_short: str,
  output_directory: Path
) -> None:
  """Final file polishing, including renaming to fit WIEMIP's requested format,
  marking units for some variables as 'C' and 'N', etc.
  """

  output_directory.mkdir(parents=True, exist_ok=True)

#  print(f"gcm_short: {gcm_short}, exp_short: {exp_short}")

  # Match TEM output variable names to WIEMIP
  variable_crosswalk = {
    'ALD': 'alt',
    'AVLN': 'nInorgSoil',
    'BURNC2AIR': 'fFire', # Multi-file composite variable
    'BURNSOIL2AIRC': 'ffirepeatTotal',
    'BURNVEG2AIRC': 'fFireCveg',
    'CH4EFFLUXTOT': 'wetCH4',
    'DWDC': 'cCwd',
    'EET': 'evapotrans',
    'FROZENDEPTH': 'fdepth',
    'GPP': 'gpppft',
    'GPPTOT': 'gpp',
    'GPPMINUSNPP': 'ra', # Multi-file composite variable
    'LAI': 'laipft',
    'LAITOT': 'lai',
    'LFTOTC': 'fVegSoil', # Multi-file composite variable
    'NETNMIN': 'fNnetmin',
    'NPP': 'npppft',
    'NPPTOT': 'npp',
    'NUPTAKETOT': 'fNup', # Multi-file composite variable
    'ORGN': 'nOrgSoil',
    'RHSOM': 'rhLayers',
    'RHSOMTOT': 'rh',
    'SNOWFALL': 'snowf',
    'SNOWTHICK': 'snowDepth',
    'SOC': 'cSoilLayers',
    'SOCTOT': 'cSoil',
    'SOC0_100cm': 'cSoilAbove1m',
    'SOCBELOW1M': 'cSoilBelow1m', # Multi-file composite variable
#    'SOILPOOLSSUMMED': 'cSoilPools', # Multi-file composite variable
    'SWE': 'swe',
    'TLAYER': 'soilT',
    'TRANSPIRATION': 'tveg',
    'VEGC': 'cVegpft',
    'VEGCTOT': 'cVeg',
    'VEGNTOT': 'nVeg',
    'VWCLAYER': 'mrsoLayer',
    'VWCTOT': 'mrso',
    'WATERTAB': 'wtd',
  }

  # Variables that are not needed in the final set and do not need
  # to be converted to WIEMIP standards
  # NLOST: TODO check spreadsheet
  # QRUNOFF: TODO check spreadsheet
  skip_vars = ['LAYERDZ', 'LFNVC', 'LFVC', 'NLOST', 'NUPTAKELAB',
               'NUPTAKEST', 'QRUNOFF', 'SOMA', 'SOMCR', 'SOMPR', 'SOMRAWC']

  # Irrelevant timesteps: '6-hourly': '6hr', 'Fixed': 'fx'
  timestep_crosswalk = {
    'yearly': 'yr',
    'monthly': 'mon',
    'daily': 'day'
  }

  # Variables that need 'N' or 'C' added to units string
  force_SI_units = {
    'AVLN': ['kg/m2', 'kg N m-2'],
    'BURNC2AIR':  ['kg/m2/s', 'kg C m-2 s-1'], # Multi-file composite variable
    'BURNSOIL2AIRC': ['kg/m2/s', 'kg C m-2 s-1'],
    'BURNVEG2AIRC': ['kg/m2/s', 'kg C m-2 s-1'],
    'CH4EFFLUXTOT': ['kg/m2/s', 'kg CH4 m-2 s-1'],
#we produce g/m2/time    'DWDC': ['', 'kg C m-2'], #Unsure, check prior stages and actual units
    'EET': ['kg/m2/s', 'kg m-2 s-1'], # Check that we actually achieve kg/m2/s
    'GPP': ['kg/m2/s', 'kg C m-2 s-1'],
    'GPPTOT': ['kg/m2/s', 'kg C m-2 s-1'],
    'GPPMINUSNPP': ['kg/m2/s', 'kg C m-2 s-1'], # Multi-file composite variable
    'LFTOTC': ['kg/m2/s', 'kg C m-2 s-1'], # Multi-file composite variable
    'NETNMIN': ['kg/m2/s', 'kg N m-2 s-1'],
    'NPP': ['kg/m2/s', 'kg C m-2 s-1'],
    'NPPTOT': ['kg/m2/s', 'kg C m-2 s-1'],
    'NUPTAKETOT': ['kg/m2/s', 'kg N m-2 s-1'], # Multi-file composite variable
    'ORGN': ['kg/m2', 'kg N m-2'],
    'RHSOM': ['kg/m2/s', 'kg C m-2 s-1'],
    'RHSOMTOT': ['kg/m2/s', 'kg C m-2 s-1'],
    'SOC': ['kg/m2', 'kg C m-2'],
    'SOCTOT': ['kg/m2', 'kg C m-2'],
    'SOC0_100cm': ['kg/m2', 'kg C m-2'],
    'SOCBELOW1M': ['kg/m2', 'kg C m-2'], # Multi-file composite variable
#    'SOILPOOLSSUMMED': ['kg/m2', 'kg C/m2'], # Multi-file composite variable
    'SWE': ['kg/m2', 'kg m-2'],
    'TLAYER': ['degree_K', 'K'],
#    'TRANSPIRATION': ['', 'kg m-2 s-1'],
    'VEGC': ['kg/m2', 'kg C m-2'],
    'VEGCTOT': ['kg/m2', 'kg C m-2'],
    'VEGNTOT': ['kg/m2', 'kg N m-2'],
    'VWCLAYER': ['kg/m2', 'kg m-2'],
    'VWCTOT': ['kg/m2', 'kg m-2'],
  }

  # Renaming our output files (and their variables) to fit WIEMIP reqs.
  # <MODEL_NAME>_<gcm_pattern_short_name>_<experiment_short_name>_<variable_name>_<frequency>_<spatial_resolution_short_name>.nc
  # Example: dvmdostem_stable_ctrl_gpp_mon_05.nc
  model_name = "dvmdostem"
  spatial_resolution = "05"

  possible_GCMs = ["stable", "ukesm", "gfdl", "ipsl"]
  if gcm_short not in possible_GCMs:
    print(f"Invalid GCM specified: {gcm_short}")
    print("Options are: {}".format(", ".join(possible_GCMs)))

  # Loop through all files in given directory
  for nc_path in sorted(directory.glob('*.nc')):
    varname = _varname_from_outfile(nc_path)
    if varname is None:
      print(f"No variable name parsed from {nc_path}")
      continue

    if varname in skip_vars:
      print(f"Skipping conforming {varname}")
      continue

    print(f"Conforming {varname}")
    wiemip_varname = variable_crosswalk[varname]

    timestep = _timestep_from_outfile(nc_path)
    frequency = timestep_crosswalk[timestep]

    wiemip_filename = "{}_{}_{}_{}_{}_{}.nc".format(
      model_name, gcm_short, exp_short, wiemip_varname,
      frequency, spatial_resolution
    )

    output_filepath = output_directory / wiemip_filename
    if _result_exists(output_filepath):
      continue

    print(f"Conforming {nc_path.name} to {wiemip_filename}")


    # Modify a temporary copy of the source. The final filename becomes visible
    # only after the NetCDF handle closes and all conformance edits succeed.
    with _staged_output_file( \
           output_filepath, source=nc_path
         ) as temporary_output_filepath, \
         nc.Dataset(str(temporary_output_filepath), 'r+') as dst:
      dst_var = dst.variables[varname]

      unit_history_note = None
      # If the variable units are what we expect for the given variable,
      # update them to include 'C' and 'N' as needed.
      # At this point, file variable name is still TEM-standard
      if varname in force_SI_units:
        file_current_units = ncascms_cfunits.Units(dst_var.units)
        expected_var_units = ncascms_cfunits.Units(force_SI_units[varname][0])

        if file_current_units.equivalent(expected_var_units):
          #print(f"{dst_var.units} equivalent to {force_SI_units[varname][0]}")
          old_units = dst_var.units
          #dst.setncattr('units', force_SI_units[varname][1])
          dst_var.setncattr('units', force_SI_units[varname][1])

          unit_history_note = f"Forced {old_units} to {force_SI_units[varname][1]}"
          print(f"Forced {old_units} to {force_SI_units[varname][1]}")
        else:
          print(f"Something is wrong with the incoming units for {varname}")

      # Rename data variable if needed
      if varname in variable_crosswalk:
        dst.renameVariable(varname, wiemip_varname)
        varname_history_note = f"Renamed {varname} to {wiemip_varname}"

      history_note = f"Renamed {nc_path.name} to {wiemip_filename}"
      if unit_history_note:
        history_note = "{}; {}".format(history_note, unit_history_note)
      if varname_history_note:
        history_note = "{}; {}".format(history_note, varname_history_note)

      if 'conform_history' in dst.ncattrs():
        dst.conform_history = "{}; {}".format(dst.conform_history, history_note)
      else:
        dst.conform_history = history_note


# ---------------------------------------------------------------------------
# Section 5: Visuals production
# ---------------------------------------------------------------------------

def visuals_production(
  base_dir: Path,
  wetland_dir: Path,
  merged_dir: Path,
  units_converted_dir: Path,
  variable_combined_dir: Path,
  run_mask: Path,
  visuals_dir: Path
) -> None:
  """Produce plots and other visual summaries of postprocessed outputs.

  Parameters
  ----------
  base_dir, wetland_dir, merged_dir, units_converted_dir, variable_combined_dir
    Source run/output directories (or intermediates from prior steps).
  visuals_dir
    Destination for figures and visual products.
  """
  intermediate_dirs = [
    base_dir, wetland_dir, merged_dir,
    units_converted_dir, variable_combined_dir]

  print(f"Starting visuals production, main dir = {variable_combined_dir}")

  for nc_path in sorted(variable_combined_dir.glob('*.nc')):
    varname = _varname_from_outfile(nc_path)
    if varname is None:
      print(f"No variable name parsed from {nc_path}")
      continue
    else:
      print(varname)

    map_figures = []
    ts_figures = []

    print(f"Plotting {varname}")

    for directory in intermediate_dirs:
      # Ecosystem totals append TOT to their source variable names,
      # creating intentional prefixes such as NPP/NPPTOT and SOC/SOCTOT. Match
      # the full variable token followed by the filename separator to keep each
      # product associated with its own plots.
      varname_matches = [
        path for path in directory.iterdir()
        if path.is_file()
        and path.name.startswith(f"{varname}_")
      ]

      if len(varname_matches) == 0:
        print(f"{varname} does not exist in subset {directory}")
        continue
      elif len(varname_matches) > 1:
        raise RuntimeError(
          f"Expected exactly one file containing {varname!r} in {directory}, "
          f"found {len(varname_matches)}"
        )

      var_timestep = _timestep_from_outfile(varname_matches[0])
      if var_timestep == "monthly":
        timestep_to_plot = '1850-08-01'
      else:
        timestep_to_plot = '1850-01-01'

      map_fig = map_plot(varname_matches[0], run_mask, varname, timestep_to_plot, visuals_dir)
      map_figures.append(map_fig)

      ts_fig = ts_plot(nc_path, run_mask, varname, visuals_dir)
      ts_figures.append(ts_fig)


    with PdfPages(f"{visuals_dir}/{varname}.pdf") as pdf:
      for fig in map_figures:
        pdf.savefig(fig)
      for fig in ts_figures:
        pdf.savefig(fig)


    # If the plotter simply writes png files and does not return Figures,
    # construct a pdf from the pngs.
    # map_pngs = sorted(visuals_dir.glob(f'{varname}*map*.png'))
    # print(f"map pngs: {map_pngs}")

    # images = [Image.open(png).convert("RGB") for png in map_pngs]

    # images[0].save(
    #   f"{varname}.pdf",
    #   save_all=True,
    #   append_images=images[1:],
    # )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmdline_define() -> argparse.ArgumentParser:
  """Define the command line interface and return the parser object."""
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent("""
      WIEMIP postprocessing for dvm-dos-tem outputs.

      Runs four stages in order:
        1. wetland merging
        2. unit conversion
        3. variable combination
        4. WIEMIP conforming
        5. visuals production
    """),
  )
  parser.add_argument(
    "base_directory",
    type=Path,
    metavar="base_directory",
    help="Base data input directory",
  )
  parser.add_argument(
    "wetland_directory",
    type=Path,
    metavar="wetland_directory",
    help="Wetland data input directory",
  )
  parser.add_argument(
    "wetland",
    type=Path,
    metavar="wetland",
    help=(
      "NetCDF with vegetation information (veg_pct_cov, veg_class) "
      "used to weight wetland merging."
    ),
  )
  parser.add_argument(
    "run_mask",
    type=str,
    metavar="run_mask",
    help=(
      "Relevant run mask for geospatial information and masking"
    ),
  )
  parser.add_argument(
    "gcm_short",
    type=str,
    metavar="gcm_short",
    help=(
      "GCM short name for WIEMIP naming conventions"
    ),
  )
  parser.add_argument(
    "exp_short",
    type=str,
    metavar="exp_short",
    help=(
      "Experiment short name for WIEMIP naming conventions"
    ),
  )
  parser.add_argument(
    "output_directory",
    type=Path,
    metavar="output_directory",
    help="Directory where postprocessed products will be written.",
  )
  return parser


def cmdline_parse(argv=None) -> argparse.Namespace:
  """Parse argv (or sys.argv[1:]) according to the CLI specification."""
  parser = cmdline_define()
  return parser.parse_args(argv)


def cmdline_run(args: argparse.Namespace) -> int:
  """Execute the five postprocessing sections from parsed CLI args."""
  times = {}
  times["launch"] = time.perf_counter()
  base_directory = args.base_directory
  wetland_directory = args.wetland_directory
  wetland = args.wetland
  output_directory = args.output_directory

  output_directory.mkdir(parents=True, exist_ok=True)

  merged_directory = output_directory / 'merged'
  units_converted_directory = output_directory / 'units_converted'
  variable_combined_directory = output_directory / 'variable_combined'
  conformed_dir = output_directory / 'conformed'
  visuals_dir = output_directory / 'visuals'

  # Creating subdirectories
  merged_directory.mkdir(parents=True, exist_ok=True)
  print(f"Created directory {merged_directory}")

  units_converted_directory.mkdir(parents=True, exist_ok=True)
  print(f"Created directory {units_converted_directory}")

  variable_combined_directory.mkdir(parents=True, exist_ok=True)
  print(f"Created directory {variable_combined_directory}")

  conformed_dir.mkdir(parents=True, exist_ok=True)
  print(f"Created directory {conformed_dir}")

  visuals_dir.mkdir(parents=True, exist_ok=True)
  print(f"Created directory {visuals_dir}")

  times["post_setup"] = time.perf_counter()

  # Section 1: Wetland merging
  print("Merging wetland to base")
  wetland_merging(base_directory, wetland_directory, wetland, merged_directory)
  times["post_merge"] = time.perf_counter()
  print(f"Finished merging wetland to base, time taken: "
        f"{times['post_merge']-times['post_setup']:.3f}s "
        f"({(times['post_merge']-times['post_setup'])/60:.3f} min)")

  # Section 2: Unit conversion
  print("Converting units")
  unit_conversion(merged_directory, units_converted_directory)
  times["post_convert"] = time.perf_counter()
  print(f"Finished converting units, time taken: "
        f"{times['post_convert']-times['post_merge']:.3f}s "
        f"({(times['post_convert']-times['post_merge'])/60:.3f} min)")

  # Section 3: Variable combination
  print("Combining variables")
  variable_combination(units_converted_directory, variable_combined_directory)
  print("Finished combining variables")
  times["post_combine"] = time.perf_counter()
  print(f"Finished variable combination, time taken: "
        f"{times['post_combine']-times['post_convert']:.3f}s "
        f"({(times['post_combine']-times['post_convert'])/60:.3f} min)")

  # Section 4: Conform to WIEMIP naming/formatting
  print("Conforming to WIEMIP requirements")
  conform_to_wiemip(variable_combined_directory, args.gcm_short, args.exp_short, conformed_dir)
  print("Finished conforming to WIEMIP requirements")
  times["post_conform"] = time.perf_counter()
  print(f"Finished variable combination, time taken: "
        f"{times['post_conform']-times['post_combine']:.3f}s "
        f"({(times['post_conform']-times['post_combine'])/60:.3f} min)")

  # Section 5: Visuals production
  # This was developed to be run on files that still use TEM's variable names
  # and units. It could probably be modified to also work with the
  # WIEMIP-conformed files, but that is not yet guaranteed.
  print("Producing visuals")
  visuals_production(base_directory, wetland_directory, merged_directory, \
                     units_converted_directory, variable_combined_directory, \
                     args.run_mask, visuals_dir)
  print("Finished producing visuals")

  times["end"] = time.perf_counter()

  print(times)
  print(
    f"Setup: {times['post_setup']-times['launch']:.3f}s\n",
    f"Merge: {times['post_merge']-times['post_setup']:.3f}s\n",
    f"Convert: {times['post_convert']-times['post_merge']:.3f}s\n",
    f"Combine: {times['post_combine']-times['post_convert']:.3f}s\n",
    f"Conform: {times['post_conform']-times['post_combine']:.3f}s\n",
    f"Plot: {times['end']-times['post_conform']:.3f}s\n",
    f"Total: {(times['end']-times['launch']):.3f}s ({(times['end']-times['launch'])/60:.3f} minutes)\n",
  )

  return 0


def cmdline_entry(argv=None) -> int:
  """Parse CLI args and run; convenient for tests and ``main``."""
  args = cmdline_parse(argv)
  return cmdline_run(args)


def main(argv=None) -> int:
  return cmdline_entry(argv=argv)


if __name__ == "__main__":
  sys.exit(main())
