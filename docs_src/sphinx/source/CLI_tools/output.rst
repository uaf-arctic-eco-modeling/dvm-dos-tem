############
pyddt-output
############

Comparing output sets
=====================

Compare dvmdostem outputs in two directories::

   pyddt-output compare-output-sets /path/to/output-a /path/to/output-b

Add ``--verbose`` to include successful file comparisons. Files are matched
by variable, time resolution, and stage using the model output filename
convention. The comparison uses ``compare_nc_with_python`` for the variable
named in each filename, with exact values and matching missing-value locations.
Other variables' data, attributes, and nested groups are not compared.

The report lists common variable names, names exclusive to either directory,
and names with differing data. Findings identify individual missing files,
comparison failures, differences, and matches. A variable can occur in both
directories while some of its stages or time resolutions lack counterparts.
NetCDF files outside the standard naming scheme, including restart and
run-status files, are ignored with warnings. Subdirectories are not scanned.

Exit status is zero when there are no warnings or errors, one when findings
include warnings or errors, and two when an input directory cannot be read.

Python interface
================

``pyddt.util.output.compare_output_sets(dirA, dirB)`` returns an
``OutputSetComparison`` with ``common_variables``, ``only_in_a``, ``only_in_b``,
``different_variables``, and ``findings`` attributes. Variable lists are sorted
and contain no duplicates. Failed comparisons appear in findings; they do not
populate ``different_variables`` because data equality could not be determined.

Command-line reference
======================

.. argparse::
   :module: pyddt.util.output
   :func: cmdline_define
   :prog: pyddt-output
