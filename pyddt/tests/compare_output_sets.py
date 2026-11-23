#!/usr/bin/env python3
"""Compare two existing dvmdostem output sets as a regression-test suite.

This initial suite compares directories supplied by the user. Future stages
may generate output sets and produce comparison plots, potentially through
``simulation_comparison_report.py``.
"""

import argparse
import sys

from pyddt.util import output
from pyddt.util.test import ERROR, WARNING, report_findings


def run_suite(dirA, dirB):
  """Compare existing output sets and return their results.

  Parameters
  ----------
  dirA, dirB : str or os.PathLike
    Directories containing dvmdostem outputs.

  Returns
  -------
  result : pyddt.util.output.OutputSetComparison
    Common, exclusive, and differing variable lists, plus per-file findings.

  Raises
  ------
  OSError
    If either directory cannot be read.

  Notes
  -----
  Output generation and plotting can be added as stages around this
  comparison. Findings are returned for the caller to report or inspect.
  """
  return output.compare_output_sets(dirA, dirB)


def main(argv=None):
  """Run the output-comparison suite from the command line.

  Parameters
  ----------
  argv : list of str or None, optional
    Arguments to parse. If None, use ``sys.argv[1:]``.

  Returns
  -------
  exit_code : int
    Zero if there are no warnings or errors, one if findings include warnings
    or errors, or two if either input directory cannot be read.

  Raises
  ------
  SystemExit
    If help is requested or arguments are invalid.
  """
  parser = argparse.ArgumentParser(description=__doc__,
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('dirA', help='First existing model output directory.')
  parser.add_argument('dirB', help='Second existing model output directory.')
  parser.add_argument('-v', '--verbose', action='store_true',
                      help='Include successful file comparisons in the report.')
  args = parser.parse_args(argv)

  try:
    result = run_suite(args.dirA, args.dirB)
  except OSError as error:
    print(f'Cannot compare output sets: {error}', file=sys.stderr)
    return 2

  report_findings(result.findings, title=f'Output comparison: {args.dirA} vs {args.dirB}',
                  verbose=args.verbose)
  return int(any(finding.status in (ERROR, WARNING) for finding in result.findings))


if __name__ == '__main__':
  sys.exit(main())
