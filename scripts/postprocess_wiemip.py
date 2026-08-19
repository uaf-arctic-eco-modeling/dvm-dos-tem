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

import netCDF4 as nc

from pyddt.util.general import breakdown_outfile_name
from pyddt.util.output import (
  convert_units,
  sum_across_compartments,
  sum_across_layers,
  sum_across_pfts,
  weighted_combine_veg,
)


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

  for filename in only_a:
    print(f"Skipping {filename}: present in {directory_a}, missing from {directory_b}")
  for filename in only_b:
    print(f"Skipping {filename}: present in {directory_b}, missing from {directory_a}")

  for filename in common:
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
  unit_specifiers = {
    'VEGC': 'kg/m2',
  }

  output_directory.mkdir(parents=True, exist_ok=True)

  for nc_path in sorted(directory.glob('*.nc')):
    try:
      _, varname, _, _ = breakdown_outfile_name(str(nc_path))
    except ValueError:
      continue

    if varname not in unit_specifiers:
      shutil.copy2(nc_path, output_directory / nc_path.name)
      continue

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


def _copy_variable_attrs(src, dst) -> None:
  for attr in src.ncattrs():
    if attr == '_FillValue':
      continue
    setattr(dst, attr, getattr(src, attr))


def _write_summed_nc(
  src_path: Path,
  dst_path: Path,
  varname: str,
  summed,
  drop_dims: list[str],
) -> None:
  """Write ``summed`` to ``dst_path``, dropping ``drop_dims`` from the source file."""
  dst_path.parent.mkdir(parents=True, exist_ok=True)

  with nc.Dataset(str(src_path), 'r') as src, \
       nc.Dataset(str(dst_path), 'w', format='NETCDF4') as dst:
    src_var = src.variables[varname]

    for dim_name, dim in src.dimensions.items():
      if dim_name in drop_dims:
        continue
      dst.createDimension(dim_name, None if dim.isunlimited() else len(dim))

    for vname, svar in src.variables.items():
      if vname == varname:
        continue
      if any(d in drop_dims for d in svar.dimensions):
        continue
      fill = getattr(svar, '_FillValue', None)
      kwargs = {'fill_value': fill} if fill is not None else {}
      dvar = dst.createVariable(vname, svar.dtype, svar.dimensions, **kwargs)
      _copy_variable_attrs(svar, dvar)
      if svar.size > 0:
        dvar[:] = svar[:]

    out_dims = tuple(d for d in src_var.dimensions if d not in drop_dims)
    fill = getattr(src_var, '_FillValue', None)
    kwargs = {'fill_value': fill} if fill is not None else {}
    dvar = dst.createVariable(varname, src_var.dtype, out_dims, **kwargs)
    _copy_variable_attrs(src_var, dvar)
    if fill is not None and hasattr(summed, 'filled'):
      dvar[:] = summed.filled(fill)
    else:
      dvar[:] = summed

    for attr in src.ncattrs():
      setattr(dst, attr, getattr(src, attr))
    history_note = "variable_combination: summed across {}".format(
      ", ".join(drop_dims)
    )
    if 'history' in dst.ncattrs():
      dst.history = "{}; {}".format(dst.history, history_note)
    else:
      dst.history = history_note


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
      continue

    if varname in pft_to_ecosystem:
      with nc.Dataset(str(nc_path), 'r') as src:
        if varname not in src.variables:
          continue
        data = src.variables[varname][:]
      drop_dims = []
      # VEGC may be (time, pftpart, pft, y, x); collapse compartments first.
      if data.ndim == 5:
        data = sum_across_compartments(data)
        drop_dims.append('pftpart')
      data = sum_across_pfts(data)
      drop_dims.append('pft')
    elif varname in layer_to_ecosystem:
      with nc.Dataset(str(nc_path), 'r') as src:
        if varname not in src.variables:
          continue
        data = src.variables[varname][:]
      data = sum_across_layers(data)
      drop_dims = ['layer']
    else:
      continue

    output_filepath = output_directory / f"{nc_path.stem}_summed{nc_path.suffix}"
    _write_summed_nc(nc_path, output_filepath, varname, data, drop_dims)

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
# Section 4: Visuals production
# ---------------------------------------------------------------------------

def visuals_production(directory_a: Path, directory_b: Path, output_directory: Path) -> None:
  """Produce plots and other visual summaries of postprocessed outputs.

  Parameters
  ----------
  directory_a, directory_b
    Source run/output directories (or intermediates from prior steps).
  output_directory
    Destination for figures and visual products.
  """
  # TODO: implement visuals production
  pass


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
        4. visuals production
    """),
  )
  parser.add_argument(
    "directory_a",
    type=Path,
    metavar="directoryA",
    help="First input directory (e.g. a model run or output tree).",
  )
  parser.add_argument(
    "directory_b",
    type=Path,
    metavar="directoryB",
    help="Second input directory (e.g. a model run or output tree).",
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
  """Execute the four postprocessing sections from parsed CLI args."""
  directory_a = args.directory_a
  directory_b = args.directory_b
  wetland = args.wetland
  output_directory = args.output_directory

  output_directory.mkdir(parents=True, exist_ok=True)

  merged_directory = output_directory / 'merged'
  units_converted_directory = output_directory / 'units_converted'
  variable_combined_directory = output_directory / 'variable_combined'

  merged_directory.mkdir(parents=True, exist_ok=True)
  print(f"Created directory {merged_directory}")
  units_converted_directory.mkdir(parents=True, exist_ok=True)
  print(f"Created directory {units_converted_directory}")
  variable_combined_directory.mkdir(parents=True, exist_ok=True)
  print(f"Created directory {variable_combined_directory}")

  print("Merging wetland to base")
  wetland_merging(directory_a, directory_b, wetland, merged_directory)
  print("Finished merging wetland to base")

  print("Converting units")
  unit_conversion(merged_directory, units_converted_directory)
  print("Finished converting units")

  print("Combining variables")
  variable_combination(units_converted_directory, variable_combined_directory)
  print("Finished combining variables")

  visuals_production(directory_a, directory_b, output_directory)

  return 0


def cmdline_entry(argv=None) -> int:
  """Parse CLI args and run; convenient for tests and ``main``."""
  args = cmdline_parse(argv)
  return cmdline_run(args)


def main(argv=None) -> int:
  return cmdline_entry(argv=argv)


if __name__ == "__main__":
  sys.exit(main())
