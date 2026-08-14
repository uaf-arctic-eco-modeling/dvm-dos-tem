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
import sys
import textwrap
from pathlib import Path

from pyddt.util.general import breakdown_outfile_name
from pyddt.util.output import convert_units, weighted_combine_veg


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
  # TODO: implement wetland merging (discover matching files, etc.)
  # Example call for one matching variable file from each directory:
  # weighted_combine_veg(
  #   str(directory_a / "VEGC_yearly_tr.nc"),
  #   str(directory_b / "VEGC_yearly_tr.nc"),
  #   str(wetland),
  #   str(output_directory / "VEGC_yearly_tr.nc"),
  # )
  pass


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

def variable_combination(directory_a: Path, directory_b: Path, output_directory: Path) -> None:
  """Combine variables into derived WIEMIP products.

  Parameters
  ----------
  directory_a, directory_b
    Source run/output directories (or intermediates from prior steps).
  output_directory
    Destination for combined / derived products.
  """
  # TODO: implement variable combination
  pass


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
  units_converted_directory.mkdir(parents=True, exist_ok=True)
  variable_combined_directory.mkdir(parents=True, exist_ok=True)

  wetland_merging(directory_a, directory_b, wetland, merged_directory)

  unit_conversion(merged_directory, units_converted_directory)

  variable_combination(directory_a, directory_b, variable_combined_directory)

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
