###########################
pyddt-input
###########################

.. argparse::
   :module: pyddt.util.input
   :func: cmdline_define
   :prog: pyddt-input

Counting cells by community type
===============================

To print cell counts for each community type (CMT), provide the vegetation
file and, optionally, the run mask::

   pyddt-input count-cells-by-cmt /path/to/vegetation.nc
   pyddt-input count-cells-by-cmt /path/to/vegetation.nc /path/to/run-mask.nc

Without a run mask, the table includes only whole-grid counts. With a run
mask, it also includes active-cell counts (nonzero values of the run mask's ``run`` variable). The two grids must have
matching shapes. The command returns a nonzero exit status if the files cannot
be read or their grid shapes differ.
