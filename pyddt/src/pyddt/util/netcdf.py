#!/usr/bin/env python
# Utilities for generic netCDF file manipulation

from pathlib import Path

import netCDF4 as nc

# This is a reasonably generic utility method and should be
# moved to pyddt.
def copy_nc_file_structure(
  src_path: Path,
  dst_path: Path,
  varname: str,
  drop_dims: list[str],
) -> None:
    """Wrapper method to open files when copying netCDF files from the command line"""
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Creating new netCDF file for {varname}")
    with nc.Dataset(str(src_path), 'r') as src, \
         nc.Dataset(str(dst_path), 'w', format='NETCDF4') as dst:
      copy_nc_file_structure_handles(src, dst, varname, drop_dims)


# This is a reasonably generic utility method and should be
# moved to pyddt.
def copy_nc_file_structure_handles(
  src: nc.Dataset,
  dst: nc.Dataset,
  varname: str,
  drop_dims: list[str],
) -> None:
  """Construct a copy of src_path at dst_path, dropping ``drop_dims``"""

  print(f"Copying netCDF file structure for {varname}")

  # Copy dimensions
  for dim_name, dim in src.dimensions.items():
    if dim_name in drop_dims:
      continue
    dst.createDimension(dim_name, None if dim.isunlimited() else len(dim))

  # Copy global attributes
  dst.setncatts(src.__dict__)

  # Copy variables other than the target variable
  for vname, src_var in src.variables.items():
    # Skip the variable to be modified - it will be populated elsewhere
    if vname == varname:
      continue

    # Drop variables whose dimensions are being removed
    if any(dim in drop_dims for dim in src_var.dimensions):
      continue

    fill_value = getattr(src_var, '_FillValue', None)
    kwargs = {'fill_value': fill_value} if fill_value is not None else {}
    dst_var = dst.createVariable(
      vname,
      src_var.dtype,
      src_var.dimensions,
      **kwargs)

    # Copy variable attributes
    dst_var.setncatts(src_var.__dict__)

    # Copy coordinate/metadata variable data
    if src_var.size > 0:
      dst_var[:] = src_var[:]


  # Copy target variable structure/metadata/etc.
  # Fills with _FillValue but no data is copied
  # This could be rolled into the loop above, but is left separate
  # to allow easy modification if the target variable is not wanted
  # in the destination file at all.

#      _copy_variable_attrs(svar, dvar)
#      if svar.size > 0:
#        dvar[:] = svar[:]

#  src_var = src.variables[varname]
#
#  out_dims = tuple(dim for dim in src_var.dimensions if dim not in drop_dims)
#  fill = getattr(src_var, '_FillValue', None)
#  kwargs = {'fill_value': fill} if fill is not None else {}
#
#  dst_var = dst.createVariable(varname, src_var.dtype, out_dims, **kwargs)
#
#  # Copy coordinate/metadata variable data
#  if src_var.size > 0:
#    dst_var[:] = src_var[:]
#
  for attr in src.ncattrs():
    setattr(dst, attr, getattr(src, attr))

  history_note = "Structure copied from source file".format(", ".join(drop_dims))
  if 'history' in dst.ncattrs():
    dst.history = "{}; {}".format(dst.history, history_note)
  else:
    dst.history = history_note

