---
name: pyddt-style
description: 'Write or review Python code for the pyddt package (dvm-dos-tem/pyddt) in its established style. Use when adding/editing modules under pyddt/src/pyddt (util, drivers, viewers, calibration), adding a new CLI tool/entry point, exposing a function as both an importable API and a command line script, or writing markdown doctests under pyddt/tests/doctests. Covers indentation, docstrings, imports, the cmdline_define/parse/run/entry/main CLI pattern, pyproject.toml wiring, and standalone-vs-docker code boundaries.'
---

# pyddt Style

`pyddt` is the Python toolkit inside `dvm-dos-tem` for pre/post-processing,
visualizing, and running the `dvmdostem` model. Code here must stay consistent
with the existing package rather than drift toward generic modern-Python
defaults.

## Core conventions

- **Indentation: 2 spaces**, not 4. This is the dominant convention across the
  package (`util/runmask.py`, `util/param.py`, `drivers/basedriver.py`, etc.)
  even though a couple of newer files use 4-space PEP8 — match the 2-space
  convention for new code.
- **Imports**: absolute, e.g. `from pyddt.util import input, param` (not
  relative `from . import input`). Standard library first, then third-party
  (`numpy`, `netCDF4 as nc`, `xarray as xr`), then `pyddt` imports.
- **Docstrings**: numpy-style with `Parameters` / `Returns` sections for any
  non-trivial function, e.g.:

  ```python
  def cell_count(runmask_file, verbose=False):
    '''
    Returns counts for each value appearing in the provided run-mask file.

    Parameters
    ----------
    runmask_file : str
      Filename of the run mask to operate on.

    Returns
    -------
    mask_counts : collections.Counter
      Counts of each distinct value found in the mask.
    '''
  ```

  Single-line docstrings are fine for small helpers. Use `'''` triple quotes
  (matches existing files).
- **String formatting**: either `.format()` or f-strings are both present in
  the codebase; prefer f-strings for new code but don't rewrite surrounding
  code to convert style.
- **No type hints** in existing code — don't add them unless the file already
  uses them.
- **Data access**: prefer `netCDF4.Dataset` (`import netCDF4 as nc`) for
  reading/writing dvmdostem NetCDF files to match existing conventions, using
  `with nc.Dataset(path) as ds:` where practical. `xarray` appears in newer
  files (e.g. `runmonitor.py`) and is fine for read-heavy analysis/plotting
  code, especially when standalone (see below). Don't mix libraries gratuitously
  within one function.
- **Plotting**: `matplotlib`; if a script may run headless (no DISPLAY, e.g. in
  CI or the docker container), call `matplotlib.use('Agg')` immediately after
  `import matplotlib` and before `import matplotlib.pyplot`.

## Standalone vs docker-dependent code

`pyddt` is split between code that works outside the `dvmdostem` docker
container (pure Python + input/output file manipulation — e.g. visualizing
inputs/outputs, mask editing, parameter editing) and code that assumes the
docker run environment (actually invoking `dvmdostem`, reading container paths
like `/data/workflows`, `.env`-based volume mappings).

When adding a new module:
- If it only reads/writes/plots dvmdostem input or output NetCDF/JSON/CSV
  files, keep it dependency-light (`numpy`, `netCDF4`/`xarray`, `matplotlib`,
  `pandas` — all already declared in `pyproject.toml`) and avoid assuming the
  module is run from inside the container or repo checkout. Don't hardcode
  container-only paths (`/data/...`).
- If it needs to actually run or configure `dvmdostem` itself (drivers,
  working-directory setup, run masks tied to a live run), it's fine to assume
  the docker/run environment, but still isolate path-mapping logic (see
  `resolve_io_path` in `util/runmonitor.py`) rather than scattering
  container-path assumptions through the module.
- Mention in the module's top-level docstring/comment whether it's intended to
  run standalone or inside the container, if it's not obvious.

## CLI pattern

Every module that should expose a command line tool follows this exact
five-function shape (see `util/runmask.py`, `util/config.py`):

```python
def cmdline_define():
  '''Define the command line interface and return the parser object.'''
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      One paragraph description of what this tool does.
    ''')
  )
  parser.add_argument('file', nargs='?', metavar=('FILE'),
      help=textwrap.dedent('''Help text for this argument.'''))
  parser.add_argument('--verbose', action='store_true',
      help=textwrap.dedent('''Print info to stdout when script runs.'''))
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
  # validate args here, calling parser.error(...) for invalid combinations
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
    Non-zero if the program cannot complete successfully.
  '''
  # dispatch to the real, importable functions in this module
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
```

Rules:
- `cmdline_run` should dispatch to plain, independently-importable functions
  defined earlier in the module (or imported from elsewhere) — never put real
  logic directly in `cmdline_run`. This is what keeps the module usable as a
  library, not just a script.
- Keep `main(argv=None)` as the thin wrapper used by the `pyproject.toml`
  entry point, and `cmdline_entry` as the testable wrapper used by doctests.
- After adding a new CLI module, wire it into `pyproject.toml`'s
  `[project.scripts]` table following the existing `pyddt-<name> =
  "pyddt.<subpackage>.<module>:main"` naming (e.g. `pyddt-runmask =
  "pyddt.util.runmask:main"`).
- Use `textwrap.dedent('''...''')` for all `help=` and `description=` strings,
  and `argparse.RawDescriptionHelpFormatter` so the dedented text renders as
  written.

## Doctests

New or changed CLI-facing functionality should get/update a markdown doctest
under `pyddt/tests/doctests/<area>.<module>.md` (e.g.
`tests/doctests/util.runmask.md`). Pattern:

- Import the module, set up any temp files/dirs needed (`/tmp/test...`,
  copying from `testing-data/inputs/...`), demonstrate the plain API, then
  demonstrate the CLI path via
  `pyddt.<module>.cmdline_run(pyddt.<module>.cmdline_parse([...]))` and assert
  on its `0`/non-zero return and resulting side effects.
- Prose between doctest blocks should note that the doctest style favors
  calling `cmdline_parse`/`cmdline_run` directly for testability, while normal
  users would invoke the installed console script (e.g. `$ pyddt-runmask
  --help`).

## When reviewing/editing existing files

Match the surrounding file's existing conventions (indentation, quote style,
docstring presence) even if they diverge slightly from the above — don't do
drive-by reformatting of unrelated code in the same file.
