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
import textwrap
from pathlib import Path

import time

import numpy as np
import netCDF4 as nc
import cfunits as ncascms_cfunits #Note that this is not the cf_units from Scitools
#from PIL import Image
from matplotlib.backends.backend_pdf import PdfPages

from pyddt.util.general import breakdown_outfile_name
from pyddt.util.netcdf import copy_nc_file_structure_handles
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

  burn_only_vars = ['BURNSOIL2AIRC', 'BURNTHICK', 'BURNVEG2AIRC']
  wetland_only_vars = ['CH4EFFLUXTOT']
  base_only_vars = ['SOC0_100cm']

  for filename in only_a:
    print(f"Skipping {filename}: present in {directory_a}, missing from {directory_b}")
  for filename in only_b:
    print(f"Skipping {filename}: present in {directory_b}, missing from {directory_a}")

  for filename in common:
    print(f"Merging {filename}")
    weighted_combine_veg(
      str(directory_a / filename),
      str(directory_b / filename),
      wetland_file=str(wetland),
      outfile=str(output_directory / filename),
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
    'SOC': 'kg C/m2',
    'SOC0_100cm': 'kg/m2',
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
      continue

    if varname not in unit_specifiers:
      print(f"{varname} does not require unit conversion, copying unchanged")
      shutil.copy2(nc_path, output_directory / nc_path.name)
      continue

    print(f"Converting {varname} to {unit_specifiers[varname]}")
    output_filepath = output_directory / f"{nc_path.stem}_unitsconverted{nc_path.suffix}"
    convert_units(
      str(nc_path),
      unit_specifiers[varname],
      output_filepath=str(output_filepath),
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
  pft_to_ecosystem = {'GPP', 'LAI', 'NPP', 'VEGC'}
  layer_to_ecosystem = {'RHSOM', 'SOC', 'VWCLAYER'}

  output_directory.mkdir(parents=True, exist_ok=True)

  for nc_path in sorted(directory.glob('*.nc')):
    varname = _varname_from_outfile(nc_path)
    if varname is None:
      print(f"No variable name parsed from {nc_path}")
      continue

    output_filepath = output_directory / f"{nc_path.stem}_summed{nc_path.suffix}"

    # Handling PFT variables
    if varname in pft_to_ecosystem:
      print(f"Combining {varname} to ecosystem level")

      with nc.Dataset(str(nc_path), 'r') as src, \
           nc.Dataset(output_filepath, 'w') as dst:
        if varname not in src.variables:
          print(f"{varname} not found in {str(nc_path)}")
          continue

        src_var = src.variables[varname]

        if src_var.dimensions == 5:
          print(f"{varname} has 5 dimensions. Probably by-compartment.")
          print("5-dimensional files are not currently handled.")
          continue
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

      with nc.Dataset(str(nc_path), 'r') as src, \
           nc.Dataset(output_filepath, 'w') as dst:
        if varname not in src.variables:
          print(f"{varname} not found in {str(nc_path)}")
          continue

        src_var = src.variables[varname]

        drop_dims = ['layer']
        # Create structure for the destination file
        copy_nc_file_structure_handles(src, dst, varname, drop_dims)

        # Define output file variable
        out_dims = tuple(dim for dim in src_var.dimensions if dim not in drop_dims)
        fill_value = getattr(src_var, '_FillValue', None)
        kwargs = {'fill_value': fill_value} if fill_value is not None else {}

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
      continue


  # Combining multi-file variables
  # wiemip/trendy variable name: variables to combine for it
  multi_file_additions = {
#    'fFire': ['BURNVEG2AIRC', 'BURNSOIL2AIRC'],
    'cSoilPools': ['SOMA', 'SOMCR', 'SOMPR', 'SOMRAWC']
  }

  multi_file_subtractions = {
    'cSoilBelow1m': ['SOC', 'SOC0_100cm'], #SOC - SOC0_100cm
    'ra': ['GPP', 'NPP'] #GPP - NPP
  }


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

  # TODO INCOMPLETE
  variable_crosswalk = {
    'GPP': 'gpp',
    'LAI': 'lai',
    'SOC': 'cSoil',
    'SOC0_100cm': 'cSoilAbove1m',
    'VEGC': 'cVeg'
  }

  # Irrelevant timesteps: '6-hourly': '6hr', 'Fixed': 'fx'
  timestep_crosswalk = {
    'yearly': 'yr',
    'monthly': 'mon',
    'daily': 'day'
  }

#Variables that for sure need things like 'N' and 'C' added to units
#AVLN, BURNSOIL2AIRC, BURNVEG2AIRC, CH4EFFLUXTOT, DWDC, GPP, NETNMIN, NPP
#ORGN, SOC, SOC0_100cm, VEGC, VEGNTOT
  force_SI_units = {
    'GPP': ['kg/m2/s', 'kg C/m2/s'], #Which varname here?
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

    print(f"Conforming {varname}")
    wiemip_varname = variable_crosswalk[varname]

    timestep = _timestep_from_outfile(nc_path)
    frequency = timestep_crosswalk[timestep]

    wiemip_filename = "{}_{}_{}_{}_{}_{}.nc".format(
      model_name, gcm_short, exp_short, wiemip_varname,
      frequency, spatial_resolution
    )

    output_filepath = output_directory / wiemip_filename
    shutil.copy2(nc_path, output_filepath)

    print(f"Conforming {nc_path.name} to {wiemip_filename}")


    # Updating output file
    with nc.Dataset(str(output_filepath), 'r+') as dst:
      dst_var = dst.variables[varname]

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
    timestep_to_plot = '1850-08-01'
    ts_method = lambda x: x.mean(dim=["x", "y"])

    for directory in intermediate_dirs:
      varname_matches = [
        path for path in directory.iterdir()
        if path.is_file() and varname in path.name
      ]

      if len(varname_matches) != 1:
        raise RuntimeError(
          f"Expected exactly one file containing {varname!r} in {directory}, "
          f"found {len(varname_matches)}"
        )

      map_fig = map_plot(varname_matches[0], run_mask, varname, timestep_to_plot, visuals_dir)
      map_figures.append(map_fig)

      ts_fig = ts_plot(nc_path, run_mask, varname, ts_method, visuals_dir)
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

  # Section :
  print("Combining variables")
  variable_combination(units_converted_directory, variable_combined_directory)
  print("Finished combining variables")
  times["post_combine"] = time.perf_counter()

  # Section :
  print("Conforming to WIEMIP requirements")
  conform_to_wiemip(variable_combined_directory, args.gcm_short, args.exp_short, conformed_dir)
  print("Finished conforming to WIEMIP requirements")
  times["post_conform"] = time.perf_counter()

  # Section :
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
    f"Total: {(times['end']-times['launch'])/60:.3f}s ({(times['end']-times['launch'])/60:.3f} minutes)\n",
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
