#!/usr/bin/env python3
"""
WIEMIP postprocessing framework for dvm-dos-tem outputs.

Standalone CLI that orchestrates wetland merging, unit conversion,
variable combination, and visuals production. Uses pyddt utilities
where helpful; section bodies are intentionally left as stubs.

Example
-------
  ./postprocess-wiemip.py directoryA directoryB wetland.nc output_directory
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import textwrap
from contextlib import contextmanager
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

def unit_conversion(directory: Path, output_directory: Path) -> None:
  """Convert listed variables in ``directory`` to target units.

  For each NetCDF whose variable appears in ``unit_specifiers``, writes a
  file under ``output_directory`` with ``_unitsconverted`` inserted before
  the extension via ``pyddt.util.output.convert_units``.

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
    with _staged_output_file(output_filepath) as temporary_output_filepath:
      convert_units(
        str(nc_path),
        unit_specifiers[varname],
        output_filepath=str(temporary_output_filepath),
        varname=varname,
      )


# ---------------------------------------------------------------------------
# Section 3: Variable combination
# ---------------------------------------------------------------------------

def variable_combination(directory: Path, output_directory: Path) -> None:
  """Sum PFT- or layer-resolved variables to ecosystem totals.

  For each NetCDF in ``directory`` whose variable appears in
  ``pft_to_ecosystem`` or ``layer_to_ecosystem``, applies
  ``sum_across_pfts`` or ``sum_across_layers`` and writes a file under
  ``output_directory`` with ``_summed`` inserted before the extension.

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

    output_stem = nc_path.stem
    if varname == 'VWCLAYER':
      # The layer-resolved input is named VWCLAYER, while its ecosystem total
      # is identified as VWCTOT in the result filename.
      output_stem = output_stem.replace('VWCLAYER', 'VWCTOT', 1)
    output_filepath = output_directory / f"{output_stem}_summed{nc_path.suffix}"

    if varname == 'VWCLAYER':
      # Preserve the original by-layer data alongside the newly calculated
      # ecosystem total. Check this result independently so a missing layer
      # file can still be copied when VWCTOT already exists, and vice versa.
      layer_output_filepath = output_directory / nc_path.name
      if not _result_exists(layer_output_filepath):
        with _staged_output_file(layer_output_filepath, source=nc_path):
          pass

    if _result_exists(output_filepath):
      continue

    # Handling PFT variables
    if varname in pft_to_ecosystem:
      print(f"Combining {varname} to ecosystem level")

      with _staged_output_file(output_filepath) as temporary_output_filepath, \
           nc.Dataset(str(nc_path), 'r') as src, \
           nc.Dataset(temporary_output_filepath, 'w') as dst:
        if varname not in src.variables:
          raise RuntimeError(f"{varname} not found in {str(nc_path)}")

        src_var = src.variables[varname]

        if src_var.ndim == 5:
          raise RuntimeError(
            f"{varname} has 5 dimensions and is probably by-compartment; "
            "5-dimensional files are not currently handled"
          )
          # VEGC may be (time, pftpart, pft, y, x); collapse compartments first.
          #if data.ndim == 5:
          #  print("Five dimensions, summing across compartments")
          #  data = sum_across_compartments(data)
          #  drop_dims.append('pftpart')

        drop_dims = ['pft']
        # Create structure for the destination file
        copy_nc_file_structure_handles(src, dst, varname, drop_dims)

        # Define output file variable
        out_dims = tuple(dim for dim in src_var.dimensions if dim not in drop_dims)
        fill_value = getattr(src_var, '_FillValue', None)
        kwargs = {'fill_value': fill_value} if fill_value is not None else {}

        # Manually define output variable chunking due to lost dimension
        # THIS IS PROBLEMATIC TODO: Fix
        dst_var_chunking = src_var.chunking()
        del dst_var_chunking[1]
        print(f"Manual dst var chunking: {dst_var_chunking}")

        # Get incoming compression scheme and level
        compressor = get_compressor(src_var.filters())
        if compressor == "zlib":
          kwargs['zlib'] = True
          kwargs['complevel'] = src_var.filters()['complevel']
          kwargs['shuffle'] = src_var.filters().get('shuffle', False)
          kwargs['chunksizes'] = dst_var_chunking
        else:
          raise RuntimeError(
            f"kwargs for compressor {compressor} not implemented"
          )

        output_var = dst.createVariable(
          varname,
          src_var.dtype,
          out_dims,
          **kwargs)

        # Copy variable attributes
        output_var.setncatts(src_var.__dict__)

        # Working on chunks of the file to allow for handling
        # larger files. The '120' is a harcoded value based on
        # prior knowledge of the GPP file block setup and
        # should be changed to use dynamic information from the
        # incoming file.
        for timestep in range(0, src_var.shape[0], 120):
          data_slice = src_var[timestep:timestep+120, :, :, :]
          print(data_slice.shape)
          summed_slice = np.ma.sum(data_slice, axis=1)

          # Immediately write result slice out
          output_var[timestep:timestep+120, :, :] = summed_slice

        print(f"Done summing {varname}")
        history_note = "Summed across {}".format(", ".join(drop_dims))
        if 'history' in dst.ncattrs():
          dst.history = f"{dst.history}; {history_note}"
        else:
          dst.history = history_note

    # Handling layer variables
    # There is a lot of duplicate code here, it should
    # be generalized and moved to pyddt when time permits.
    elif varname in layer_to_ecosystem:
      print(f"Combining {varname} to ecosystem level")

      with _staged_output_file(output_filepath) as temporary_output_filepath, \
           nc.Dataset(str(nc_path), 'r') as src, \
           nc.Dataset(temporary_output_filepath, 'w') as dst:
        if varname not in src.variables:
          raise RuntimeError(f"{varname} not found in {str(nc_path)}")

        src_var = src.variables[varname]

        drop_dims = ['layer']
        # Create structure for the destination file
        copy_nc_file_structure_handles(src, dst, varname, drop_dims)

        # Define output file variable
        out_dims = tuple(dim for dim in src_var.dimensions if dim not in drop_dims)
        fill_value = getattr(src_var, '_FillValue', None)
        kwargs = {'fill_value': fill_value} if fill_value is not None else {}

        # Manually define output variable chunking due to lost dimension
        # THIS IS PROBLEMATIC TODO: Fix
        dst_var_chunking = src_var.chunking()
        del dst_var_chunking[1]
        print(f"Manual dst var chunking: {dst_var_chunking}")

        # Get incoming compression scheme and level
        compressor = get_compressor(src_var.filters())
        if compressor == "zlib":
          kwargs['zlib'] = True
          kwargs['complevel'] = src_var.filters()['complevel']
          kwargs['shuffle'] = src_var.filters().get('shuffle', False)
          kwargs['chunksizes'] = dst_var_chunking
        else:
          raise RuntimeError(
            f"kwargs for compressor {compressor} not implemented"
          )

        output_var = dst.createVariable(
          varname,
          src_var.dtype,
          out_dims,
          **kwargs)

        # Copy variable attributes
        output_var.setncatts(src_var.__dict__)

        # Working on chunks of the file to allow for handling
        # larger files. The '120' is a harcoded value based on
        # prior knowledge of the GPP file block setup and
        # should be changed to use dynamic information from the
        # incoming file.
        for timestep in range(0, src_var.shape[0], 120):
          data_slice = src_var[timestep:timestep+120, :, :, :]
          print(data_slice.shape)
          summed_slice = np.ma.sum(data_slice, axis=1)

          # Immediately write result slice out
          output_var[timestep:timestep+120, :, :] = summed_slice

        print(f"Done summing {varname}")
        history_note = "Summed across {}".format(", ".join(drop_dims))
        if 'history' in dst.ncattrs():
          dst.history = f"{dst.history}; {history_note}"
        else:
          dst.history = history_note

    # varname has no summing specified
    else:
      print(f"{varname} has no dimension summing, copying unchanged")
      output_filepath = output_directory / nc_path.name
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
    'BURNSOIL2AIRC': 'fFireCsoil', # Spreadsheet gave two options
    'BURNVEG2AIRC': 'fFireCveg',
    'CH4EFFLUXTOT': 'wetCH4',
    'DWDC': 'cCwd',
    'EET': 'evapotrans',
    'GPP': 'gpp',
    'GPPMINUSNPP': 'ra', # Multi-file composite variable
    'LAI': 'lai',
    'LFTOTC': 'fVegLitter', # Multi-file composite variable
    'NETNMIN': 'fNnetmin',
    'NPP': 'npp',
    'NUPTAKETOT': 'fNup' # Multi-file composite variable
    'ORGN': 'nOrgSoil',
    'RHSOM': 'rh',
    'SNOWFALL': 'snowf',
    'SNOWTHICK': 'snowDepth',
    'SOC': 'cSoil',
    'SOC0_100cm': 'cSoilAbove1m',
    'SOCBELOW1M': 'cSoilBelow1m', # Multi-file composite variable
    'SOILPOOLSSUMMED': 'cSoilPools', # Multi-file composite variable
    'SWE': 'swe',
    'TLAYER': 'soilT',
    'TRANSPIRATION': 'tveg',
    'VEGC': 'cVeg',
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
    'AVLN': ['kg/m2', 'kg N/m2'],
    'BURNC2AIR':  ['kg/m2/s', 'kg C/m2/s'], # Multi-file composite variable
    'BURNSOIL2AIRC': ['kg/m2/s', 'kg C/m2/s'],
    'BURNVEG2AIRC': ['kg/m2/s', 'kg C/m2/s'],
    'CH4EFFLUXTOT': ['kg/m2/s', 'kg CH4/m2/s'],
#    'DWDC': ['', 'kg C/m2'], #Unsure, check prior stages and actual units
#    'EET': ['', 'kg/m2/s'], #Unsure, check prior stages and actual units
    'GPP': ['kg/m2/s', 'kg C/m2/s'],
    'GPPMINUSNPP': ['kg/m2/s', 'kg C/m2/s'], # Multi-file composite variable
    'LFTOTC': ['kg/m2/s', 'kg C/m2/s'], # Multi-file composite variable
    'NETNMIN': ['kg/m2/s', 'kg N/m2/s'],
    'NPP': ['kg/m2/s', 'kg C/m2/s'],
    'NUPTAKETOT': ['kg/m2/s', 'kg N/m2/s'], # Multi-file composite variable
    'ORGN': ['kg/m2', 'kg N/m2'],
    'RHSOM': ['kg/m2/s', 'kg C/m2/s'],
#    'SNOWFALL': ['', 'kg/m2/s'], #Special handling, TEM units: mm
    'SOC': ['kg/m2', 'kg C/m2'],
    'SOC0_100cm': ['kg/m2', 'kg C/m2'],
    'SOCBELOW1M': ['kg/m2', 'kg C/m2'], # Multi-file composite variable
    'SOILPOOLSSUMMED': ['kg/m2', 'kg C/m2'], # Multi-file composite variable
    'VEGC': ['kg/m2', 'kg C/m2'],
    'VEGNTOT': ['kg/m2', 'kg N/m2'],
    'SOILPOOLSSUMMED': ['kg/m2', 'kg C/m2'], # Multi-file composite variable
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
      # SOC is a prefix of SOC0_100cm, so a general substring search would
      # select both products. For these two variables, require the complete
      # TEM variable name followed by the filename's underscore separator.
      overlapping_soc_names = {'SOC', 'SOC0_100cm'}
      varname_matches = [
        path for path in directory.iterdir()
        if path.is_file()
        and (
          path.name.startswith(f"{varname}_")
          if varname in overlapping_soc_names
          else varname in path.name
        )
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
