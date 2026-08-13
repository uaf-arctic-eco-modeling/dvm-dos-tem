#!/usr/bin/env python3
"""
WIEMIP postprocessing framework for dvm-dos-tem outputs.

Standalone CLI that orchestrates wetland merging, unit conversion,
variable combination, and visuals production. Uses pyddt utilities
where helpful; section bodies are intentionally left as stubs.

Example
-------
  ./postprocess-wiemip.py directoryA directoryB output_directory
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

# Prefer installed package imports (see pyddt/context.md).
# Uncomment / extend as section implementations need them:
# import pyddt.util.output
# import pyddt.util.general


# ---------------------------------------------------------------------------
# Section 1: Wetland merging
# ---------------------------------------------------------------------------

def wetland_merging(directory_a: Path, directory_b: Path, output_directory: Path) -> None:
  """Merge wetland-related outputs from the two input directories.

  Parameters
  ----------
  directory_a, directory_b
    Source run/output directories to merge.
  output_directory
    Destination for merged products.
  """
  # TODO: implement wetland merging
  pass


# ---------------------------------------------------------------------------
# Section 2: Unit conversion
# ---------------------------------------------------------------------------

def unit_conversion(directory_a: Path, directory_b: Path, output_directory: Path) -> None:
  """Convert output variable units to WIEMIP / analysis targets.

  Parameters
  ----------
  directory_a, directory_b
    Source run/output directories (or intermediates from prior steps).
  output_directory
    Destination for unit-converted products.
  """
  # TODO: implement unit conversion (e.g. via pyddt.util.output.convert_units)
  pass


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
  output_directory = args.output_directory

  output_directory.mkdir(parents=True, exist_ok=True)

  wetland_merging(directory_a, directory_b, output_directory)

  unit_conversion(directory_a, directory_b, output_directory)

  variable_combination(directory_a, directory_b, output_directory)

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
