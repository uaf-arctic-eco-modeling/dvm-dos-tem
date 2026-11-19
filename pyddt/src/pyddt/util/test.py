"""Generic utilities for tests and checks.

Provides shared finding types, status constants, and reporting helpers for
collecting and presenting the results of tests or validation checks.
"""

from dataclasses import dataclass

SUCCESS = 'SUCCESS'
WARNING = 'WARNING'
ERROR = 'ERROR'
SKIPPED = 'SKIPPED'


@dataclass
class Finding:
  """Record one observation produced by a validation check.

  Parameters
  ----------
  status : str
    Outcome category: ``SUCCESS``, ``WARNING``, ``ERROR``, or ``SKIPPED``.
  message : str
    Human-readable description of the observation.
  check_name : str
    Name identifying the check that produced this finding. One check can
    produce several findings with the same name.

  Attributes
  ----------
  status : str
    Outcome category, independent of how the report displays it.
  message : str
    Description of the observation.
  check_name : str
    Identifier of the originating check.
  """

  status: str
  message: str
  check_name: str


def report_findings(findings, title='Test findings', verbose=False):
  """Print findings grouped by status, followed by error and warning counts.

  Parameters
  ----------
  findings : list of Finding
    Observations produced by tests or checks. Errors and warnings are always
    displayed. Successes are displayed only in verbose mode; skipped findings
    are not printed.
  title : str, optional
    Heading identifying the test suite or subject of the report. Defaults
    to ``Test findings``.
  verbose : bool, optional
    If True, print SUCCESS findings. Defaults to False.

  Returns
  -------
  None

  Notes
  -----
  Prints to standard output without modifying the findings. Order within
  each displayed status group is preserved.
  """
  print(f'{"=" * 60}')
  print(title)
  print(f'{"=" * 60}')

  errors = [i for i in findings if i.status == ERROR]
  warnings = [i for i in findings if i.status == WARNING]

  if not findings:
    print('  No issues found.')
    return

  if verbose:
    for finding in findings:
      if finding.status == SUCCESS:
        print(f'  SUCCESS: {finding.message}')

  for finding in errors:
    print(f'  ERROR:   {finding.message}')
  for finding in warnings:
    print(f'  WARNING: {finding.message}')

  print(f'\n{len(errors)} error(s), {len(warnings)} warning(s).')
