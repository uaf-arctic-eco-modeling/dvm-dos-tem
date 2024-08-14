  .. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs


#########################################
Data Summary and Processing
#########################################

***********************
Common Tools
***********************

NCOs
==============

The NetCDF Operators (NCOs) are suite of command-line tools that can efficiently
manipulate well-formed NetCDF datasets (e.g. compute statistics, concatenate,
edit metadata, compression) and produce outputs or display results to your
console. To our knowledge, NCOs are among the most efficient tools to manipulate
large NetCDF files. You’ll  find a full description of the dozen existing
operators in the nco user guide (https://nco.sourceforge.net/#RTFM). If you have
questions on how to use an operator that is not addressed in the user guide, you
can post them on the nco help forum:
https://sourceforge.net/p/nco/discussion/9830. 

Additional examples of file manipulation using nco can be found here
(http://research.jisao.washington.edu/data_sets/nco/). 

Unidata
==========

Unidata also provides several very useful command-line utilities to manipulate
NetCDF files, ``ncdump`` and ``nccopy``, more info here:

https://docs.unidata.ucar.edu/nug/current/netcdf_utilities_guide.html

Unidata also maintains a list of NetCDF compatible software:

https://www.unidata.ucar.edu/software/netcdf/software.html



Python ``netCDF4`` package
=============================
This is the de-facto standard Python interface to netCDF files. There are some 
higher level wrappers, but at the end of the day everything you want to do 
can be done with this package.

https://unidata.github.io/netcdf4-python/

Python ``xarray`` package
============================
``xarray`` aims to bring a ``pandas`` like interface to netCDF files (and earth
science data in general). Pandas has become a standard in the Python data
community, but it was originally developed for users in the FINTECH space, and
so has some awkward aspects for earth science data. ``xarray`` aims to fix this.

https://xarray.dev


R
================
There are several client libraries for handling NetCDF in ``R``, including:

 - https://cran.r-project.org/web/packages/RNetCDF/index.html
 - https://cran.r-project.org/web/packages/ncdf4/index.html

***********************
Common Operations
***********************

Collected here are a few examples of common data manipulation operations. The
examples here are far from exhaustive. If you encounter or develop a useful
solution that you'd like to see here, plese send us a Pull Request!


Explore structure of NetCDF file
===================================

.. collapse:: ncdump

  This command will list the dimensions, variables and metadata of a file. The
  ``-h`` specify to only display headers.

  .. code:: 

      $ ncdump -h input.nc

.. collapse:: ncdump details

  This command will list the dimensions, variables and metadata of a file AND
  the values for the coordinate variables. 	

  .. code::

      $ ncdump -c input.nc

Compress NetCDF file
===========================

.. collapse:: nccopy

  Compress NetCDF files using ``nccopy``. This will copy and compress a netcdf
  file without loss of data.

  .. code::

      $ nccopy -u -d1 input.nc output.nc This command




Subset netcdf files by dimensions
====================================

Example: we want to subset the last 10 years of an annual historical simulation
115 years long.

.. collapse:: ncks

  The flag ``-O`` will overwrite any existing output file. The flag ``-h`` will
  not include this command in the global attribute of the output file to
  document the history of its creation.

  .. code::

      $ ncks -O -h -d time,104,114,1 input.nc output.nc

  .. note::

    Caution: As in python, the indexing in nco starts at zero. So the index of
    the 115th time step is actually 114. 
  

.. collapse:: python netCDF4

  .. code:: 

    >>> import netCDF4 as nc
    >>> ds = nc.Dataset('GPP_yearly_tr.nc')
    >>> last_10yrs = ds.variables['GPP'][-10:,:,:]


Display variable values to terminal
======================================

Example: we want to display the annual active layer depth (ALD) values for upper
left corner pixel of a regional run.

.. collapse:: ncks

  .. code:: 

      $ ncks -d x,0 -d y,0 -v ALD input.nc

  If you are not sure about the names of the dimensions and variables, you can
  always display the files structure using ``ncdump`` as described below.

.. collapse:: python netCDF4

  .. code::

    >>> import netCDF4 as nc
    >>> ds = nc.Dataset('ALD_yearly_tr.nc')
    >>> print(ds.variables['ALD'][:.0,0])
    

Compute sum, average and standard deviation across dimensions
==================================================================

Example: Model simulation produces monthly GPP time series partitioned by plant
functional types and compartments. We now want to compute GPP at the community
level by summing across plant functional types (dimension named pft) and
compartments (dimensions named pftpart).

.. collapse:: ncwa

  .. code::

      $ ncwa -O -h -v GPP -a pftpart, pft -y ttl input.nc output.nc

  This command will produce sums of GPP across two dimensions listed after the
  ``-a`` flag. The variable to be summed is specified after the flag ``-v``.
  Finally, the flag ``-y`` is used to indicate the type of operation to be done.

.. collapse:: python netCDF4

  .. code::

    >>> import netCDF4 as nc
    >>> ds = nc.Dataset('GPP_yearly_tr.nc')
    >>> a = ds.variables['GPP'][:].sum(axis=1).sum(axis=1)

Computations can also be done across a subset of the data. For instance the
following command will compute the annual mean temperature for the months of
June, July and August. To do so, you will need to make the time dimension as
unlimited, as it is done with the ``ncks`` operator.

.. collapse:: ncks, ncra

  .. code::

      $ ncks -O -h --mk_rec_dmn time input.nc input1.nc
      $ ncra --mro -O -d time,5,,12,3 -y avg -v tair input1.nc output.nc

  The ``-d`` flag indicate which dimension should the computation be done across.
  The indices following the dimension name indicate how to group and subset the
  dataset. The first index indicate where to start the operation (i.e. the month
  of June of the first year). The second indicate where to end the operation
  (nothing indicated means that the operation should be conducted across the
  entire time series). The third index indicate how to group the data (i.e. 12
  months chunks for yearly computations). Finally, the fifth index indicate the
  number of time step to do the operation for for every group (i.e. 3 months, from
  June to August). The ``-v`` flag indicate what variable to use for the operation.
  The ``-y`` flag indicate what type of operation to conduct. The option ``--mro``
  instructs ncra to output its results for each sub-group (in that case, each
  year).




Append files of same dimensions
=================================
``dvmdostem`` output variables are stored in single files. To append multiple
variables from the same simulation in a single file, you can use the following
command. 

.. collapse:: ncks

  .. code::

      $ ncks -A -h file1.nc file2.ncs

  The ``-A`` flag indicate that the output file (file2.nc in this case), should
  append (vs overwrite) data. Caution: the files need to be the same exact
  structure (the dimensions in common between files should have the same length,
  name and attributes). The data in file1.nc will be appended to file2.nc. This
  command processes files twice at a time.


Operations with multiple variables
=====================================

Example: model simulations produced annual thickness of the fibric and the humic
horizons (namely SHLWDZ and DEEPDZ) of the organic layer and you want to compute
the total organic layer thickness (OLDZ)

.. collapse:: ncks, ncap2

  .. code::

      $ ncks -A -h SHLWDZ.nc DEEPDZ.nc
      $ ncap2 -O -h -s 'OLDZ = DEEPDZ + SHLWDZ' DEEPDZ.nc OLDZ.nc

  The first command append the two variables in a single file. The second command
  is the arithmetic processor, accepting short scripts to create new variables. In
  this case, we create the variable OLDZ as the sum of two existing DEEPDZ and
  SHLWDZ.


Concatenate files along the record dimension
==============================================

Whole model simulations consist of a succession of runs, i.e. pre-run,
equilibrium, spin-up, transient (i.e. historical) and scenario. For analysis
purposes, you may wat to concatenate the historical ad scenario runs into a
single file. To do so, you will need to make the time dimension as unlimited, so
additional records can be added to it, before you can do the concatenation.

.. collapse:: ncks, ncrcat

  .. code::
    
    $ ncks -O -h --mk_rec_dmn time input1.nc output1.nc
    $ ncks -O -h --mk_rec_dmn time input2.nc output2.nc
    $ ncrcat -O -h output1.nc output2.nc output.nc



