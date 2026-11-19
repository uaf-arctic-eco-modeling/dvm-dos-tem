#!/usr/bin/env python


import os
import argparse
import sys
import shutil #For non-empty directory tree deletion
import subprocess
import re
import tempfile
import numpy as np
import netCDF4 as nc


def _read_comparison_values(fileA, fileB, varname):
  """Validate two NetCDF files and read their comparison variable.

  Parameters
  ----------
  fileA, fileB : str or os.PathLike
    Paths to the input NetCDF files.
  varname : str
    Nonempty name of a root variable present in both files.

  Returns
  -------
  values_a, values_b : numpy.ma.MaskedArray
    Selected values with matching shapes and real numeric data types.
    NetCDF masking and scaling are applied when reading.

  Raises
  ------
  FileNotFoundError
    If an input does not exist.
  OSError
    If an input is not a regular, readable NetCDF file.
  ValueError
    If root dimensions or variable structures differ, the variable name is
    invalid, or the variable is absent, nonnumeric, empty, or contains
    nonfinite unmasked values.

  Notes
  -----
  Shared by both comparison functions to keep validation consistent. Only
  root dimensions and variable structures are checked; attributes and nested
  groups are excluded. Inputs are opened read-only and closed after reading.
  """
  if not isinstance(varname, str) or not varname:
    raise ValueError("varname must be a nonempty variable name")

  for path in (fileA, fileB):
    if not os.path.exists(path):
      raise FileNotFoundError("NetCDF input does not exist: {}".format(path))
    if not os.path.isfile(path):
      raise OSError("NetCDF input is not a regular file: {}".format(path))

  # Open inputs read-only and close both even if validation fails.
  # Opening the files also checks actual read access and NetCDF validity.
  with nc.Dataset(fileA, 'r') as first, nc.Dataset(fileB, 'r') as second:
    if set(first.dimensions) != set(second.dimensions):
      raise ValueError("Input files have different dimension names")
    for name, dimension in first.dimensions.items():
      other = second.dimensions[name]
      if (len(dimension) != len(other)
          or dimension.isunlimited() != other.isunlimited()):
        raise ValueError("Input dimension differs: {}".format(name))
    if set(first.variables) != set(second.variables):
      raise ValueError("Input files have different variable names")
    for name, variable in first.variables.items():
      other = second.variables[name]
      if (variable.dimensions != other.dimensions
          or variable.shape != other.shape or variable.dtype != other.dtype):
        raise ValueError("Input variable structure differs: {}".format(name))
    if varname not in first.variables:
      raise ValueError("Variable is absent from both inputs: {}".format(varname))
    variable = first.variables[varname]
    if np.dtype(variable.dtype).kind not in "iuf":
      raise ValueError("Comparison requires a real numeric variable")
    values_a = np.ma.asarray(variable[...])
    values_b = np.ma.asarray(second.variables[varname][...])
    if values_a.size == 0:
      raise ValueError("Cannot compare an empty variable")
    if not (np.isfinite(values_a.compressed()).all()
            and np.isfinite(values_b.compressed()).all()):
      raise ValueError("Comparison requires finite unmasked values")
    return values_a, values_b


def compare_nc_with_nco(fileA, fileB, varname, file_cleanup):
  """Compare one numeric variable in two NetCDF files using NCO.

  Parameters
  ----------
  fileA, fileB : str or os.PathLike
    Paths to the readable input NetCDF files.
  varname : str
    Name of a root numeric variable present in both files. Must be a simple
    NCO identifier containing letters, digits, or underscores and beginning
    with a letter or underscore.
  file_cleanup : bool
    If True, remove intermediate files even after a failure. Otherwise retain
    them in a unique directory under ``/tmp``; failures occurring after that
    directory is created include its path in the error message.

  Returns
  -------
  match : bool
    True if unmasked values and missing-value locations match exactly.
    Two entirely masked variables match.

  Raises
  ------
  FileNotFoundError
    If an input file or a required NCO executable is absent.
  OSError
    If an input cannot be opened or temporary files cannot be used.
  ValueError
    If file structures differ, the variable is unsupported, empty, or contains
    nonfinite unmasked values, or its name is invalid.
  RuntimeError
    If an NCO command fails or produces an invalid result. Also wraps failures
    occurring after the temporary directory is created when cleanup is disabled.

  Notes
  -----
  Both files must have matching root dimension names, lengths, and unlimited
  status, and matching variable names, dimensions, shapes, and data types.
  Attributes and nested groups are not compared. NetCDF masking and scaling
  are applied before comparison, without numerical tolerance. The selected
  arrays are loaded into memory. Requires ``ncdiff`` and ``ncap2`` when
  unmasked values need comparison.
  """
  if not isinstance(varname, str) or not re.fullmatch(
      r"[A-Za-z_][A-Za-z0-9_]*", varname):
    raise ValueError("varname must be a simple NCO variable identifier")

  values_a, values_b = _read_comparison_values(fileA, fileB, varname)
  if not np.array_equal(np.ma.getmaskarray(values_a),
                        np.ma.getmaskarray(values_b)):
    return False
  if values_a.count() == 0:
    return True

  executables = {}
  for command in ("ncdiff", "ncap2"):
    executable = shutil.which(command)
    if executable is None:
      raise FileNotFoundError("Required NCO executable not found: " + command)
    executables[command] = executable

  # Isolate each comparison so concurrent calls cannot overwrite files.
  tmp_dir = tempfile.mkdtemp(prefix="pyddt-ncdiff-", dir="/tmp")
  try:
    diff_file = os.path.join(tmp_dir, "difference.nc")
    sum_diff_file = os.path.join(tmp_dir, "total_difference.nc")
    # Sum absolute differences so positive and negative errors cannot
    # cancel. Convert to double before subtraction to avoid integer overflow.
    # Reducing every dimension also supports PFT, layer, and scalar outputs.
    ncap_script = (
      "{0}=double({0});".format(varname))
    converted_a = os.path.join(tmp_dir, "first.nc")
    converted_b = os.path.join(tmp_dir, "second.nc")
    commands = [
      [executables["ncap2"], "-O", "-s", ncap_script,
       os.fspath(fileA), converted_a],
      [executables["ncap2"], "-O", "-s", ncap_script,
       os.fspath(fileB), converted_b],
      [executables["ncdiff"], "-v", varname,
       converted_a, converted_b, diff_file],
      [executables["ncap2"], "-O", "-s",
       "total_diff=abs({}).total()".format(varname),
       diff_file, sum_diff_file],
    ]
    for command in commands:
      try:
        subprocess.run(command, check=True, capture_output=True, text=True)
      except subprocess.CalledProcessError as error:
        raise RuntimeError("{} failed: {}".format(
          os.path.basename(command[0]), error.stderr.strip())) from error
      output_path = command[-1]
      if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError("NCO did not create a nonempty file: " + output_path)

    with nc.Dataset(sum_diff_file, 'r') as result:
      if "total_diff" not in result.variables:
        raise RuntimeError("NCO result is missing total_diff")
      total = np.ma.asarray(result.variables["total_diff"][...])
      if total.size != 1 or np.ma.getmaskarray(total).any():
        raise RuntimeError("NCO result must be one unmasked total")
      total_diff = float(total.item())
      if not np.isfinite(total_diff) or total_diff < 0:
        raise RuntimeError("NCO result must be finite and nonnegative")
      # Preserve exact comparison for large integers that may round
      # to the same value when NCO converts them to double precision.
      return total_diff == 0.0 and np.array_equal(
        values_a.compressed(), values_b.compressed())
  except Exception as error:
    if not file_cleanup:
      raise RuntimeError("Comparison failed; intermediate files retained in "
                         "{}: {}".format(tmp_dir, error)) from error
    raise
  finally:
    if file_cleanup:
      shutil.rmtree(tmp_dir)


def compare_nc_with_python(fileA, fileB, varname):
  """Compare one numeric NetCDF variable directly in Python.

  Parameters
  ----------
  fileA, fileB : str or os.PathLike
    Paths to the readable input NetCDF files.
  varname : str
    Nonempty name of a root numeric variable present in both files.

  Returns
  -------
  match : bool
    True if unmasked values and missing-value locations match exactly.
    Two entirely masked variables match.

  Raises
  ------
  FileNotFoundError
    If an input file does not exist.
  OSError
    If an input cannot be opened as a readable NetCDF file.
  ValueError
    If file structures differ, the variable name is invalid, or the selected
    variable is absent, nonnumeric, empty, or contains nonfinite unmasked values.

  Notes
  -----
  Both files must have matching root dimension names, lengths, and unlimited
  status, and matching variable names, dimensions, shapes, and data types.
  Attributes and nested groups are not compared. NetCDF masking and scaling
  are applied before comparison, without numerical tolerance. The selected
  arrays are loaded into memory; inputs are opened read-only, and no external
  commands or temporary files are used.
  """
  values_a, values_b = _read_comparison_values(fileA, fileB, varname)

  # Check missing-value locations before comparing valid values.
  # Values hidden by a mask are ignored, but a missing value must occur at
  # the same position in both files for the variables to match.
  if not np.array_equal(np.ma.getmaskarray(values_a),
                        np.ma.getmaskarray(values_b)):
    return False

  # Compare values directly to avoid subtraction overflow or rounding
  # large integers through a conversion to floating-point numbers.
  return np.array_equal(values_a.compressed(), values_b.compressed())


class _NetcdfHelpFormatter(argparse.HelpFormatter):
  """Format CLI help for the optional fourth NCO operand.

  Notes
  -----
  Argparse has no built-in argument count for three required values plus one
  optional value belonging to the same flag. Argument parsing validates that
  count separately. Other arguments use the standard help formatting.
  """

  def _format_args(self, action, default_metavar):
    """Format NCO operands, using standard formatting for other arguments.

    Parameters
    ----------
    action : argparse.Action
      Argument definition whose operands are being displayed.
    default_metavar : str
      Placeholder used when the argument has no explicit metavar.

    Returns
    -------
    text : str
      Operand placeholders for use in CLI help.
    """
    if action.dest == "compare_nc_nco":
      return "FILE_A FILE_B VARIABLE [FILE_CLEANUP]"
    return super()._format_args(action, default_metavar)


def cmdline_define():
  """Define operation flags for the NetCDF utility command.

  Returns
  -------
  parser : argparse.ArgumentParser
    Parser requiring one operation and its associated input arguments.
  """
  parser = argparse.ArgumentParser(
    description="Utilities for working with NetCDF files.",
    formatter_class=_NetcdfHelpFormatter,
    epilog=("Comparison exit codes: 0 = match, 1 = different values or masks, "
            "2 = invalid arguments or operation error. "
            "Example: pyddt-netcdf --compare-nc-python "
            "first.nc second.nc GPP"))
  # Each operation owns its arguments so future utilities can accept
  # different inputs. Select one operation per invocation.
  operations = parser.add_mutually_exclusive_group(required=True)
  operations.add_argument(
    "--compare-nc-python", nargs=3,
    metavar=("FILE_A", "FILE_B", "VARIABLE"),
    help="Compare one numeric variable exactly using Python, without "
         "temporary files.")
  operations.add_argument(
    "--compare-nc-nco", nargs="+", metavar="ARG",
    help="Compare one numeric variable exactly using ncdiff and ncap2. "
         "Optional FILE_CLEANUP is true (default) or false. True removes "
         "temporary files, including after failure; false retains them "
         "under /tmp for inspection.")
  return parser


def cmdline_parse(argv=None):
  """Parse arguments for the NetCDF utility command.

  Parameters
  ----------
  argv : list of str or None, optional
    Arguments to parse. If None, use ``sys.argv[1:]``.

  Returns
  -------
  args : argparse.Namespace
    Parsed arguments. NCO operands include a boolean cleanup setting,
    which defaults to True when omitted.

  Raises
  ------
  SystemExit
    If help is requested or arguments are invalid.
  """
  parser = cmdline_define()
  args = parser.parse_args(argv)
  if args.compare_nc_nco is not None:
    values = args.compare_nc_nco
    if len(values) not in (3, 4):
      parser.error("--compare-nc-nco requires FILE_A FILE_B VARIABLE "
                   "[FILE_CLEANUP]")
    cleanup = values[3].lower() if len(values) == 4 else "true"
    if cleanup not in ("true", "false"):
      parser.error("FILE_CLEANUP must be true or false")
    args.compare_nc_nco = (*values[:3], cleanup == "true")
  return args


def cmdline_run(args):
  """Execute the selected NetCDF operation and report its outcome.

  Parameters
  ----------
  args : argparse.Namespace
    Parsed arguments returned by ``cmdline_parse``.

  Returns
  -------
  exit_code : int
    Zero for a match, one for different values or masks, or two for an
    operation error.

  Notes
  -----
  Comparison outcomes are printed to standard output. Operation errors are
  printed to standard error, allowing shell scripts to distinguish failures
  from completed comparisons.
  """
  try:
    if args.compare_nc_python is not None:
      fileA, fileB, varname = args.compare_nc_python
      matches = compare_nc_with_python(fileA, fileB, varname)
    elif args.compare_nc_nco is not None:
      fileA, fileB, varname, file_cleanup = args.compare_nc_nco
      matches = compare_nc_with_nco(
        fileA, fileB, varname, file_cleanup=file_cleanup)
    else:
      raise ValueError("No NetCDF operation selected")
  except (OSError, ValueError, RuntimeError) as error:
    print("NetCDF operation failed: {}".format(error), file=sys.stderr)
    return 2
  print("{}: {}".format(varname, "match" if matches else "differ"))
  return 0 if matches else 1


def cmdline_entry(argv=None):
  """Parse and execute a NetCDF utility command.

  Parameters
  ----------
  argv : list of str or None, optional
    Arguments to parse. If None, use ``sys.argv[1:]``.

  Returns
  -------
  exit_code : int
    Zero for a match, one for different values or masks, or two for an
    operation error.

  Raises
  ------
  SystemExit
    If help is requested or arguments are invalid.
  """
  return cmdline_run(cmdline_parse(argv))


def main(argv=None):
  """Run the installed pyddt-netcdf command.

  Parameters
  ----------
  argv : list of str or None, optional
    Arguments to parse. If None, use ``sys.argv[1:]``.

  Returns
  -------
  exit_code : int
    Zero for a match, one for different values or masks, or two for an
    operation error.

  Raises
  ------
  SystemExit
    If help is requested or arguments are invalid.
  """
  return cmdline_entry(argv)


if __name__ == '__main__':
  sys.exit(main())
