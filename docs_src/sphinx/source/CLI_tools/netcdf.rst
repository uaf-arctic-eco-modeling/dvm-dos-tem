NetCDF utilities
================

Select an operation by its flag. For a comparison using Python::

   pyddt-netcdf --compare-nc-python first.nc second.nc GPP

The equivalent module invocation is::

   python -m pyddt.util.netcdf --compare-nc-python first.nc second.nc GPP

To use the NCO executables ``ncdiff`` and ``ncap2`` instead::

   pyddt-netcdf --compare-nc-nco first.nc second.nc GPP

Each invocation requires exactly one operation flag. Each flag takes its own
arguments; both comparison flags take two file paths and a variable name.

The Python method creates no temporary files. The NCO method creates
intermediate files under ``/tmp`` and removes them after the comparison,
including when an operation fails. The NCO operation accepts an optional fourth
argument, ``FILE_CLEANUP``, which defaults to ``true``::

   --compare-nc-nco FILE_A FILE_B VARIABLE [FILE_CLEANUP] [VARIABLE_B]

Square brackets indicate an optional argument; do not type them. Use ``true``
or ``false`` (case insensitive). To retain intermediate files for inspection::

   pyddt-netcdf --compare-nc-nco first.nc second.nc GPP false

If cleanup is disabled and a comparison fails after creating its temporary
directory, the error reports that directory.

To compare a variable renamed between model versions, supply its name in the
second file as ``VARIABLE_B``. If omitted, the first name is used in both::

   pyddt-netcdf --compare-nc-python first.nc second.nc OLD_NAME NEW_NAME
   pyddt-netcdf --compare-nc-nco first.nc second.nc OLD_NAME true NEW_NAME

The syntax is::

   --compare-nc-python FILE_A FILE_B VARIABLE [VARIABLE_B]
   --compare-nc-nco FILE_A FILE_B VARIABLE [FILE_CLEANUP] [VARIABLE_B]

For NCO, supply ``FILE_CLEANUP`` explicitly before ``VARIABLE_B``. Python API
calls accept ``varnameB=None`` as their final optional parameter; the NCO API
retains ``file_cleanup`` before that parameter.

Both files must have matching root dimensions. Only the selected variable
may have a different name; all other root variable names must match. All root
variables must have matching dimensions, shapes, and data types. The selected
variable must contain real numeric data and must not be empty. Unmasked NaN
and infinite values are rejected. NetCDF masking and scaling are applied;
valid values and missing-value locations must match exactly. No numerical
tolerance is used. Attributes and nested groups are not compared. The selected
arrays are loaded into memory.

Exit codes are ``0`` for a match, ``1`` for different values or missing-value
locations, and ``2`` for invalid arguments, incompatible file structures, or
an operation that failed. Errors are written to standard error.

Use ``pyddt-netcdf --help`` for argument details.
