#!/usr/bin/env python


import os
import shutil #For non-empty directory tree deletion
import subprocess
import re
import tempfile
import numpy as np
import netCDF4 as nc


def _read_comparison_values(fileA, fileB, varname):
  """! @brief Validate two NetCDF files and read their comparison variable.

  @param fileA Path to the first input file.
  @param fileB Path to the second input file.
  @param varname Nonempty name of a root variable in both files.
  @return Pair of masked arrays with matching shapes and numeric data types.
  @throws FileNotFoundError An input does not exist.
  @throws OSError An input is not a regular, readable NetCDF file.
  @throws ValueError The file structures or selected values are unsuitable
    for comparison.

  Shared by both comparison methods to keep their validation consistent.
  Only root dimensions and variable structures are checked; attributes and
  nested groups are excluded. Reading applies NetCDF masking and scaling.
  """
  if not isinstance(varname, str) or not varname:
    raise ValueError("varname must be a nonempty variable name")

  for path in (fileA, fileB):
    if not os.path.exists(path):
      raise FileNotFoundError("NetCDF input does not exist: {}".format(path))
    if not os.path.isfile(path):
      raise OSError("NetCDF input is not a regular file: {}".format(path))

  ## @brief Open inputs read-only and close both even if validation fails.
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
  """! @brief Compare one numeric variable in two NetCDF files using NCO.

  @param fileA Path to the first readable NetCDF file.
  @param fileB Path to the second readable NetCDF file.
  @param varname Name of a numeric variable present in both files.
  @param file_cleanup Remove intermediate files, including after a failure,
    when True. Otherwise retain them in a unique directory under /tmp;
    failed operations include that directory in their error message.
  @return True when all unmasked values match exactly; False when values or
    missing-value locations differ. Two entirely masked variables match.
  @throws FileNotFoundError An input file or required NCO executable is absent.
  @throws OSError An input cannot be opened or temporary files cannot be used.
  @throws ValueError File structures differ, the variable is unsupported,
    empty, or contains nonfinite unmasked values, or its name is invalid.
  @throws RuntimeError An NCO command fails or produces an invalid result.

  Both files must have the same root dimensions and variable names. Each
  variable must have matching dimensions, shape, and data type. Attributes
  and nested groups are not compared. No numerical tolerance is applied.
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

  ## @brief Isolate each comparison so concurrent calls cannot overwrite files.
  tmp_dir = tempfile.mkdtemp(prefix="pyddt-ncdiff-", dir="/tmp")
  try:
    diff_file = os.path.join(tmp_dir, "difference.nc")
    sum_diff_file = os.path.join(tmp_dir, "total_difference.nc")
    ## @brief Sum absolute differences so positive and negative errors cannot
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
      ## @brief Preserve exact comparison for large integers that may round
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
  """! @brief Compare one numeric NetCDF variable directly in Python.

  @param fileA Path to the first readable NetCDF file.
  @param fileB Path to the second readable NetCDF file.
  @param varname Name of a root numeric variable present in both files.
  @return True when unmasked values and missing-value locations match
    exactly; False otherwise. Two entirely masked variables match.
  @throws FileNotFoundError An input file does not exist.
  @throws OSError An input cannot be opened as a readable NetCDF file.
  @throws ValueError File structures differ, the variable name is invalid,
    or the selected variable is absent, nonnumeric, empty, or contains
    nonfinite unmasked values.

  Both files must have matching root dimension names, lengths, and unlimited
  status, and matching variable names, dimensions, shapes, and data types.
  Attributes and nested groups are not compared. NetCDF masking and scaling
  are applied before comparing values. No numerical tolerance is applied.
  The selected arrays are loaded into memory; inputs are opened read-only,
  and no external commands or temporary files are used.
  """
  values_a, values_b = _read_comparison_values(fileA, fileB, varname)

  ## @brief Check missing-value locations before comparing valid values.
  # Values hidden by a mask are ignored, but a missing value must occur at
  # the same position in both files for the variables to match.
  if not np.array_equal(np.ma.getmaskarray(values_a),
                        np.ma.getmaskarray(values_b)):
    return False

  ## @brief Compare values directly to avoid subtraction overflow or rounding
  # large integers through a conversion to floating-point numbers.
  return np.array_equal(values_a.compressed(), values_b.compressed())
