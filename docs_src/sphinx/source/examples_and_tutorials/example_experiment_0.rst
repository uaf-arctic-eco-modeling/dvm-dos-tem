.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs


#######################################
EE 0 - Single Site Run
#######################################

Example Experiment 0: We want to conduct a full single-site simulation, explore
the output data and produce preliminary plots.

The example solutions assume that you are running on the ``dvmdostem`` Docker
stack. Example solutions are presented in collapsable blocks. The blocks are
color coded:

.. collapse:: Full working solution.
  :class: working

  This example should work!

.. collapse:: Partial solution.
  :class: partial

  This example should get you most of the way there.

.. collapse:: Broken solution.
  :class: broken

  This example might have problems. Use at your own risk and expect to debug.

***********************
Experiment Design
***********************

Here we have designed a small experiment with answers to the unknowns posed in
:ref:`setting up a run <examples_and_tutorials/basic_model_run:setting up a dvmdostem run>`

.. list-table::
   :widths: 40 60

   * - **Question**
     - **Answer**
   * - | Where on your computer you want to store
       | your model run(s)?
     - ``/data/workflows/exp0_jan26_test``
   * - | What spatial (geographic) area you want
       | to run?
     - | Toolik, pixels (0,0), (1,1), (2,2)
       | ``/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_TOOLIK_FIELD_STATION_10x10/``
   * - What variables you want to output?
     - | GPP: monthly, by PFT
       | RH, RG, RM: monthly
       | TLAYER: monthly by layer
       | VEGC: yearly
       | ALD: yearly
       | CMTNUM: yearly
       | LAYERDZ, LAYERDEPTH, LAYERTYPE: yearly
       | SHLWC, SHLWDZ: yearly
       | DEEPC, DEEPDZ: yearly
       | MINEC: yearly
   * - Which stages to run and for how many years?
     - All stages, pr 100, eq 1000, sp 250, tr 115, sc 85 
   * - | Is the community type (CMT) fixed or driven by 
       | input vegetation.nc map?
     - Force to CMT05
   * - | For which stages should the output files be 
       | generated and saved?
     - sp, tr, sc
   * - | Calibration settings if necessary
       | (i.e. ``--cal-mode``)?
     - No
   * - | Any other command line options or environment
       | settings?
     - No       

.. warning::

  The ``outspec_utils.py`` script prints some confusing messages when working
  with by-layer files. For outputs that are only availale by layer, (i.e.
  LAYERDZ), the output is flagged as 'invlaid' in the ``output_spec.csv`` file.
  This means that if you provide the ``layer`` resolution specification when
  requesting one of these outputs, ``outspec_utils.py`` will print a message to
  the extent of "Not enabling layer outputs for LAYERDZ". This is true
  (``outspec_utils.py`` finds the "invalid" marker and doesn't enable that
  column in the ``.csv`` file), but it is not a problem - for those outputs, the
  by-layer resolution is enforced internally in the C++ part of the model.


.. collapse:: Example commands for setting up
   :class: working

   .. code:: 

      $ ./scripts/setup_working_directory.py --input-data-path /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_TOOLIK_FIELD_STATION_10x10 /data/workflows/exp0_jan26_test
      $ cd /data/workflows/exp0_jan26_test/
      $ outspec_utils.py config/output_spec.csv --on RH m
      $ outspec_utils.py config/output_spec.csv --on RG m
      $ outspec_utils.py config/output_spec.csv --on RM m
      $ outspec_utils.py config/output_spec.csv --on TLAYER l m
      $ outspec_utils.py config/output_spec.csv --on GPP m p
      $ outspec_utils.py config/output_spec.csv --on VEGC y
      $ outspec_utils.py config/output_spec.csv --on ALD y
      $ outspec_utils.py config/output_spec.csv --on CMTNUM y
      $ outspec_utils.py config/output_spec.csv --on SHLWC y l
      $ outspec_utils.py config/output_spec.csv --on SHLWDZ y l
      $ outspec_utils.py config/output_spec.csv --on DEEPC y l
      $ outspec_utils.py config/output_spec.csv --on DEEPDZ y l
      $ outspec_utils.py config/output_spec.csv --on MINEC y l
      $ outspec_utils.py config/output_spec.csv --on LAYERDZ y
      $ outspec_utils.py config/output_spec.csv --on LAYERDEPTH y
      $ outspec_utils.py config/output_spec.csv --on LAYERTYPE y 
      $ runmask-util.py --reset run-mask.nc 
      $ runmask-util.py --yx 0 0 run-mask.nc 
      $ #runmask-util.py --yx 1 1 run-mask.nc 
      $ #runmask-util.py --yx 2 2 run-mask.nc 
      $ dvmdostem --force-cmt 5 -p 100 -s 250 -e 1000 -t 115 -n 85

***************************
Example Python setup
***************************

The Python example solutions share a bunch of code. For this reason, we will put
the common setup here and not need to repeat these lines in each example. The
paths assume that these examples will be run on the TEM Docker stack. Subsequent
Python example solutions assume that these setup commands have been run. In
other words if you are following along, copy the following code into your Python
interperter and run it before continuing.

.. collapse:: Common Python setup
   :class: working

   .. jupyter-execute::

      import sys
      sys.path.insert(0, '/work/scripts')

      import os
      os.chdir('/data/workflows/exp0_jan26_test')

      import pandas as pd
      import netCDF4 as nc
      
      def get_start_end(timevar):
        '''Returns CF Times. use .strftime() to convert to python datetimes'''
        start = nc.num2date(timevar[0], timevar.units, timevar.calendar)
        end = nc.num2date(timevar[-1], timevar.units, timevar.calendar)
        return start, end
      
      
      def load_trsc(var, timeres):
        '''Returns ``netCDF4.Dataset`` s in a tuple. 
        First item is historic, second item is projected.
        '''
        trds = nc.Dataset(f'output/{var}_{timeres}_tr.nc')
        scds = nc.Dataset(f'output/{var}_{timeres}_sc.nc')
        return (trds, scds)
      
      def build_full_datetimeindex(hds, pds):
        '''Returns a ``pandas.DatetimeIndex`` covering the range of the two
        input datasets. Assumes that the two input datasets are consecutive
        monotonic, and not missing any points.'''
        
        h_start, h_end = get_start_end(hds.variables['time'])
        p_start, p_end = get_start_end(pds.variables['time'])
      
        begin = sorted([h_start, h_end, p_start, p_end])[0]
        end = sorted([h_start, h_end, p_start, p_end])[-1]
      
        dti = pd.DatetimeIndex(pd.date_range(start=begin.strftime(), end=end.strftime(), freq='AS-JAN'))
      
        return dti
      
      def build_full_dataframe(var=None, timeres=None, px_y=None, px_x=None):
        ''' Builds a pandas.DataFrame for the requested output variable with the
        transient and scenario data merged together and a complete
        DatetimeIndex.

        Parameters
        ==========
        var : str
          The variable of interest. Must be a dvmdostem output variable, i.e.
          GPP.

        timeres : str
          String of either 'monthly' or 'yearly' that will be used to find
          and open the approproate files as well as set the DatetimeIndex.

        px_y : int
          Index of the pixel to work with, latitude dimension.

        px_x : int
          Index of pixel to work with, longitude dimension.

        Returns
        ========
        df : pandas.DataFrame
          A DataFrame with data for the requested ``var`` from transient and
          scenario output files. The DataFrame should have a complete
          DatetimeIndex.

        meta : dict
          A small dictionary containing metadata about the datasets in the
          dataframe. Namely, the units.
        '''
      
        if timeres == 'yearly':
          freq = 'AS-JAN'
        elif timeres == 'monthly':
          freq = 'MS'
        else:
          raise RuntimeError("Invalid time resolution")
      
        hds, pds = load_trsc(var, timeres)
      
        timeslice = slice(0, None, 1)
        yslice = slice(px_y, px_y+1, 1)
        xslice = slice(px_x, px_x+1, 1)
        pftslice = None
        layerslice = None
      
      
        if 'pft' in hds.variables[var].dimensions and 'pft' in pds.variables[var].dimensions:
          pftslice = slice(0, None, 1)
        elif 'layer' in hds.variables[var].dimensions and 'layer' in pds.variables[var].dimensions:
          layerslice = slice(0, None, 1)
      
        if pftslice is not None:
          slice_tuple = (timeslice, pftslice, yslice, xslice)
          h_reshape = (hds.dimensions['time'].size, hds.dimensions['pft'].size, )
          p_reshape = (pds.dimensions['time'].size, pds.dimensions['pft'].size, )
        elif layerslice is not None:
          slice_tuple = (timeslice, layerslice, yslice, xslice)
          h_reshape = (hds.dimensions['time'].size, hds.dimensions['layer'].size, )
          p_reshape = (pds.dimensions['time'].size, pds.dimensions['layer'].size, )
        else:
          slice_tuple = (timeslice, yslice, xslice)
          #from IPython import embed; embed()
          #print(hds.dimensions['time'].size, pds.dimensions['time'].size)
          h_reshape = (hds.dimensions['time'].size, )
          p_reshape = (pds.dimensions['time'].size, )
      
        #print(f"USING SLICETUPLE {slice_tuple}")
        #print(f"USING freq={freq}")
        #print(hds.variables[var].shape)
      
        hs, he = get_start_end(hds.variables['time'])
        hdti = pd.DatetimeIndex(pd.date_range(start=hs.strftime(), end=he.strftime(), freq=freq,))
        h_df = pd.DataFrame(hds.variables[var][slice_tuple].reshape( h_reshape ), index=hdti)
      
        ps, pe = get_start_end(pds.variables['time'])
        pdti = pd.DatetimeIndex(pd.date_range(start=ps.strftime(), end=pe.strftime(), freq=freq,))
        p_df = pd.DataFrame(pds.variables[var][slice_tuple].reshape( p_reshape ), index=pdti)
      
        df = pd.concat([h_df, p_df])
      
        meta = dict(
          hds_units=hds.variables[var].units, 
          pds_units=pds.variables[var].units, 
          h_start=hs, h_end=he,
          p_start=ps, p_end=pe
        )
      
        return df, meta



**************************
Explore Input Datasets 
**************************

Exploring the input dataset, determine the start year of the historical, and the
projected climate time series. From the length of the time dimension, compute
the end year and the total number of years of the time series. Note that this
information is used to set the number of transient and scenario years to run.

.. collapse:: Example with ncdump
   :class: working

   .. code:: 

      $ ncdump -h /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_TOOLIK_FIELD_STATION_10x10/historic-climate.nc  | grep "time:units"
          time:units = "days since 1901-1-1 0:0:0" ;

      $ ncdump -h /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_TOOLIK_FIELD_STATION_10x10/projected-climate.nc  | grep "time:units"
          time:units = "days since 2016-1-1 0:0:0" ;
   
      $ ncdump -h /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_TOOLIK_FIELD_STATION_10x10/historic-climate.nc  | grep "time\ =\ "
          time = UNLIMITED ; // (1380 currently)

      $ ncdump -h /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_TOOLIK_FIELD_STATION_10x10/projected-climate.nc  | grep "time\ =\ "
          time = UNLIMITED ; // (1020 currently)

   So ``1380/12 = 115``. Looks like 115 years for the historic and  ``1020/85 =
   85`` for the projected.

.. collapse:: Example input_util.py plot
   :class: working

   This shows how you might plot the driving inputs using one of the existing
   utility scripts. While the graphical view is nice it makes it difficult to 
   figure out the exact start and end years.

   .. jupyter-execute::

      import input_util as iu
      import argparse

      args = {'command': 'climate-ts-plot',
        'input_folder': '/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_TOOLIK_FIELD_STATION_10x10/',
        'stitch': False,
        'type': 'spatial-temporal-summary',
      }

      iu.climate_ts_plot(argparse.Namespace(**args))

**************************
Computing Means
**************************

Compute the mean vegetation and soil carbon stocks for the following time
ranges: [1990-2010], [2040-2050], [2090-2100].

   a. What are the units of these stocks?

.. collapse:: Example Python Solution
   :class: working

   .. jupyter-execute::

      for VAR in ['VEGC', 'SHLWC', 'DEEPC', 'MINEC']:
        TIMERES = 'yearly'
        PX_X = 0
        PX_Y = 0
        decades = ['1990-2010','2040-2050','2090-2100']

        df, meta = build_full_dataframe(var=VAR, timeres=TIMERES, px_y=PX_Y, px_x=PX_X)
        print(meta)
        for d in decades:
           s, e = d.split('-')
           mean = df[s:e].mean()[0]
           print(f'{d}  {VAR}  mean: {mean}')
        print()

.. collapse:: Example NCO solution
  :class: broken

  .. warning::

    Problems?

      * decades don't match question
      * store stock in single file step, error copying scenario files??
      * commands after ``## <--ERROR! fail``

  .. code::

    ### Change into the experiment directory
    cd /data/workflows/exp0_jan26_test

    ### Create a synthesis directory to store all the summary stats
    mkdir /data/workflows/exp0_jan26_test/synthesis

    ### Compute the decadal means of vegetation carbon stocks
    ncwa -O -d time,89,98 -d x,0 -d y,0 -y avg -v VEGC output/VEGC_yearly_tr.nc  synthesis/VEGC_1990_1999.nc
    ncwa -O -d time,35,44 -d x,0 -d y,0 -y avg -v VEGC output/VEGC_yearly_sc.nc  synthesis/VEGC_2040_2059.nc
    ncwa -O -d time,75,84 -d x,0 -d y,0 -y avg -v VEGC output/VEGC_yearly_sc.nc  synthesis/VEGC_2090_2099.nc

    ### Store all soil C stocks to a single file
    cp output/SHLWC_yearly_tr.nc synthesis/SOILC_yearly_tr.nc
    ncks -A -h output/DEEPC_yearly_tr.nc synthesis/SOILC_yearly_tr.nc
    ncks -A -h output/MINEC_yearly_tr.nc synthesis/SOILC_yearly_tr.nc

    cp output/SHLWC_yearly_sc.nc synthesis/SOILC_yearly_sc.nc
    ncks -A -h ./output/DEEPC_yearly_tr.nc synthesis/SOILC_yearly_sc.nc ## <--ERROR!
    ncks -A -h ./output/MINEC_yearly_tr.nc synthesis/SOILC_yearly_sc.nc ## <--ERROR! maybe tr needs to be sc??

    ### Compute total soil carbon
    ncap2 -O -h -s'SOILC = SHLWC + DEEPC + MINEC' synthesis/SOILC_yearly_tr.nc synthesis/SOILC_yearly_tr.nc
    ncap2 -O -h -s'SOILC = SHLWC + DEEPC + MINEC' synthesis/SOILC_yearly_sc.nc synthesis/SOILC_yearly_sc.nc

    ### Compute the decadal means of soil carbon stocks
    ncwa -O -d time,89,98 -d x,0 -d y,0 -y avg -v SHLWC,DEEPC,MINEC,SOILC synthesis/SOILC_yearly_tr.nc  synthesis/SOILC_1990_1999.nc
    ncwa -O -d time,35,44 -d x,0 -d y,0 -y avg -v SHLWC,DEEPC,MINEC,SOILC synthesis/SOILC_yearly_sc.nc  synthesis/SOILC_2040_2059.nc
    ncwa -O -d time,75,84 -d x,0 -d y,0 -y avg -v SHLWC,DEEPC,MINEC,SOILC synthesis/SOILC_yearly_sc.nc  synthesis/SOILC_2090_2099.nc


****************************
Computing Monthly NEE
****************************

Compute monthly Net Ecosystem Exchange (NEE) for the historical and scenario
simulations. Indicate how you formulated NEE.

.. collapse:: Python solution 1
  :class: working

  Autotrophic respiration (RA) is the sum of growth respiration (RG) and
  maintenance respiration (RM). RG and RM encompass all vegetation respiration
  (both above and belowground).

  Heterotrphic respiration (RH) is the microbial respiration in the soil.

  Ecosystem respriation (ER) is the sum of RA and RH.

  Net Ecosystem Exchange (NEE) is Gross Primary Productvity (GPP) less ER.

  ``dvmdostem`` does not have explicit outputs for RA, ER, or NEE, so we will
  derive them from our existing outputs (GPP, RH, RM, RG).

  .. jupyter-execute::

    rh, _ = build_full_dataframe('RH', timeres='monthly', px_y=0, px_x=0)
    rm, _ = build_full_dataframe('RM', timeres='monthly', px_y=0, px_x=0)
    rg, _ = build_full_dataframe('RG', timeres='monthly', px_y=0, px_x=0)
    gpp, _ = build_full_dataframe('GPP', timeres='monthly', px_y=0, px_x=0)

    # GPP is output per PFT, so here we sum across PFTs to get
    # the ecosystem GPP.
    gpp_eco = gpp.sum(axis=1)

    # Add up all the respiration fluxes
    er = (rh + rm + rg)

    nee = gpp_eco - er.squeeze() # <-- collapse single column pandas.DataFrame

  .. collapse:: matplotlib

    .. jupyter-execute::

      import matplotlib.pyplot as plt

      fig, axes = plt.subplots(2,1)

      axes[0].plot(nee, color='black', label='NEE')
      axes[1].plot(nee['1940':'1950'])

      plt.savefig('NEE_SAMPLE.png')


  .. collapse:: bokeh

    .. note:: 

      This does not display properly in all web browsers. Safari in particular
      seems to have issues. It should work fine if you run the code on your own
      machine, but for some reason when embedded in the Sphinx documentation, it
      doesn't behave. 

    .. jupyter-execute::

      import bokeh.plotting as bkp
      import bokeh.resources as bkr
      import bokeh.io as bkio

      # This helps display inline in sphinx document
      bkio.output_notebook(bkr.CDN, verbose=False, 
                           notebook_type='jupyter', hide_banner=True)

      p = bkp.figure(title="NEE", x_axis_type='datetime',
                     sizing_mode="stretch_width", max_width=500, height=150,
                     toolbar_location='above', )

      p.line(nee.index, nee, line_width=1)

      bkp.show(p)


.. collapse:: NCO solution
  :class: partial

  .. code::

    ### Change into the experiment directory
    cd /data/workflows/exp0_jan26_test

    ### Create a synthesis directory to store all the summary stats
    mkdir /data/workflows/exp0_jan26_test/synthesis

    ### Sum up the GPP across PFTs
    ncwa -O -h -v GPP -a pft -y total output/GPP_monthly_tr.nc synthesis/GPP_monthly_tr.nc
    ncwa -O -h -v GPP -a pft -y total output/GPP_monthly_sc.nc synthesis/GPP_monthly_sc.nc
    
    ### Append all the necessary fluxes into single files
    cp synthesis/GPP_monthly_tr.nc synthesis/Cfluxes_monthly_tr.nc
    ncks -A -h output/RM_monthly_tr.nc synthesis/Cfluxes_monthly_tr.nc
    ncks -A -h output/RG_monthly_tr.nc synthesis/Cfluxes_monthly_tr.nc
    ncks -A -h output/RH_monthly_tr.nc synthesis/Cfluxes_monthly_tr.nc
    cp synthesis/GPP_monthly_sc.nc synthesis/Cfluxes_monthly_sc.nc
    ncks -A -h output/RM_monthly_sc.nc synthesis/Cfluxes_monthly_sc.nc
    ncks -A -h output/RG_monthly_sc.nc synthesis/Cfluxes_monthly_sc.nc
    ncks -A -h output/RH_monthly_sc.nc synthesis/Cfluxes_monthly_sc.nc
    
    ### Compute monthly NEE
    ncap2 -O -h -s'NEE = RH + RG + RM - GPP' synthesis/Cfluxes_monthly_tr.nc synthesis/Cfluxes_monthly_tr.nc
    ncap2 -O -h -s'NEE = RH + RG + RM - GPP' synthesis/Cfluxes_monthly_sc.nc synthesis/Cfluxes_monthly_sc.nc
    
    ### Compute yearly sums of fluxes (this is a sum by group, i.e. years, 
    ### so we'll need to indicate the --mro option in ncra)
    # make time dimension unlimited
    ncks -O -h --mk_rec_dmn time synthesis/Cfluxes_monthly_tr.nc synthesis/Cfluxes_monthly_tr.nc
    ncks -O -h --mk_rec_dmn time synthesis/Cfluxes_monthly_sc.nc synthesis/Cfluxes_monthly_sc.nc
    # compute the annual sums
    ncra --mro -O -d time,0,,12,12 -d x,0 -d y,0 -y ttl -v GPP,RG,RM,RH,NEE synthesis/Cfluxes_monthly_tr.nc synthesis/Cfluxes_yearly_tr.nc
    ncra --mro -O -d time,0,,12,12 -d x,0 -d y,0 -y ttl -v GPP,RG,RM,RH,NEE synthesis/Cfluxes_monthly_sc.nc synthesis/Cfluxes_yearly_sc.nc
    # fix back the time dimension 
    ncks -O -h --fix_rec_dmn time synthesis/Cfluxes_monthly_tr.nc synthesis/Cfluxes_yearly_tr.nc
    ncks -O -h --fix_rec_dmn time synthesis/Cfluxes_monthly_sc.nc synthesis/Cfluxes_yearly_sc.nc

    ### Compute decadale averages of C fluxes
    ncwa -O -d time,89,98 -d x,0 -d y,0 -y avg -v GPP,RG,RM,RH,NEE synthesis/Cfluxes_yearly_tr.nc synthesis/Cfluxes_1990_1999.nc
    ncwa -O -d time,35,44 -d x,0 -d y,0 -y avg -v GPP,RG,RM,RH,NEE synthesis/Cfluxes_yearly_sc.nc synthesis/Cfluxes_2040_2059.nc
    ncwa -O -d time,75,84 -d x,0 -d y,0 -y avg -v GPP,RG,RM,RH,NEE synthesis/Cfluxes_yearly_sc.nc synthesis/Cfluxes_2090_2099.nc   

.. collapse:: Python solution 2 (does not use common setup)
  :class: partial

  .. code::

    import xarray as xr
    import pandas as pd
    import glob, os
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    import scipy.stats as stats
    from statsmodels.stats.multicomp import pairwise_tukeyhsd

    # Path to the output directory
    ODir = '/Users/helene/Helene/TEM/DVMDOSTEM/dvmdostem_workflows/exp0_jan26_test/output'

    #list the starting years of the decades over which to compute the means
    declist = [1940,1990,2040, 2090]

    ###### COMPUTING NEE ######
    ###########################

    #Loop through all the modes and variables of interest
    data_mode = pd.DataFrame()
    for mode in ['tr', 'sc']:
      print(mode)
      for VAR in ['GPP','RM','RG','RH']:
        print(VAR)
        # Check the output of the selected mode/variable exists
        if (len(glob.glob(ODir + '/' + VAR + '*' + mode + '.nc')) > 0):
          filename = os.path.basename(glob.glob(ODir + '/' + VAR + '*' + mode + '.nc')[0])
          # Read the dataset
          ds = xr.open_dataset(glob.glob(ODir + '/' + VAR + '*' + mode + '.nc')[0])
          data = ds.to_dataframe()
          data.reset_index(inplace=True)
          # Select pixel of iinterest
          data = data.rename(columns={VAR: 'value'})
          # Sum the fluxes by secondary dimensions
          if (('pft' in data.columns) | ('pftpart' in data.columns) | ('layer' in data.columns)):
            data = data.groupby(['time','x','y'])[['value']].agg(['sum'])
            data.reset_index(inplace=True)
            data.columns = ['time', 'x', 'y','value']
          # Format the time/date dimension
          data['time'] = data['time'].astype('|S80')
          data['time'] = data['time'].astype('|datetime64[ns]')
          data['year'] = data['time'].dt.year
          # Check the outputs are monthly or yearly
          if 'monthly' in filename:
            print('Monthly outputs')
            data['month'] = data['time'].dt.month
            data = data.groupby(['year','x','y'])[['value']].agg(['sum'])
            data.reset_index(inplace=True)
            data.columns = ['year','x','y','value']
          # Add necessary information
          data['variable'] = VAR
          data['mode'] = mode
        data_mode = data_mode.append(data)

    # Reshape the dataset
    final = data_mode.pivot(index=['mode','year','x','y'], columns = 'variable',values = 'value') 
    final.reset_index(inplace=True)

    # Compute NEE
    final['Reco'] = final['RH'] + final['RG'] + final['RM']
    final['NEE'] = final['RH'] + final['RG'] + final['RM'] - final['GPP'] 
    final.reset_index(inplace=True)

    # Compute the decadal averages
    decade = pd.DataFrame()
    for i in declist:
      print(i)
      dec = final[(final['year'] >= i) & (final['year'] < i+10)].groupby(['x','y'])[['GPP','Reco','NEE']].agg(['mean'])
      dec['decade'] = '[' + str(i) + '-' + str(i+9) +']'
      dec.reset_index(inplace=True)
      decade = decade.append(dec)

    decade



****************************
Computing Mean GPP
****************************

Compute the mean GPP, autotrophic and heterotrophic respirations and NEE for the
following decades: [1990-2010], [2040-2050], [2090-2100].

   a. What are the units of these fluxes?

      .. collapse:: Example Python Solution
         :class: working

         .. jupyter-execute:: 

            for v in ['GPP', 'RH', 'RM','RG',]:
                trds = nc.Dataset(f'output/{v}_monthly_tr.nc')
                scds = nc.Dataset(f'output/{v}_monthly_sc.nc')
                tunits = trds.variables[v].units
                sunits = scds.variables[v].units
                print(f'{v} {tunits} {sunits}')
            


.. collapse:: Example Python Solution
   :class: working

   .. jupyter-execute:: 

      VAR = 'GPP'
      TIMERES = 'monthly'
      PX_X = 0
      PX_Y = 0

      df, _ = build_full_dataframe(var=VAR, timeres=TIMERES, px_y=PX_Y, px_x=PX_X)

      for d in ['1990-2010','2040-2050','2090-2100']:
         s, e = d.split('-')
         mean = df[s:e].mean(axis=0)
         long_string = ['{:.3f}'.format(i) for i in mean]
         print(f"{d}  mean (each pft): {long_string}")
         print(f"{d}  mean (across pfts): {mean.mean()}")
         print()



*******************************************
Plot Active Layer Depth
*******************************************

Plot the active layer depth from 1950 to 2100.

.. collapse:: Example Python Solution
   :class: working
   :name: customName

   .. jupyter-execute:: 

    import matplotlib.pyplot as plt

    df, meta = build_full_dataframe(var='ALD', timeres='yearly', px_y=0, px_x=0)

    fig, ax = plt.subplots(1,1)

    ax.plot(df.loc['1950':'2100'].index, df.loc['1950':'2100'][0], label='ALD')
    ax.axvline(meta['h_end'], linestyle='dotted', color='red')

    ax.set_xlabel('year')
    ax.set_ylabel('ALD ({})'.format(meta['hds_units']))

    plt.savefig('ALD_SAMPLE.png')

.. collapse:: NCO Solution
  :class: partial

  .. code::

    ### Concatenate historical and scenario time series of activee layer depth
    # make time dimension unlimited in the ALD output files
    ncks -O -h --mk_rec_dmn time -d x,0 -d y,0 ./output/ALD_yearly_tr.nc ./synthesis/ALD_yearly_tr.nc
    ncks -O -h --mk_rec_dmn time -d x,0 -d y,0 ./output/ALD_yearly_sc.nc ./synthesis/ALD_yearly_sc.nc
    # compute the annual sums
    ncrcat -O -h ./synthesis/ALD_yearly_tr.nc ./synthesis/ALD_yearly_sc.nc ./synthesis/ALD_yearly_total.nc
    # fix back the time dimension 
    ncks -O -h --fix_rec_dmn time ./synthesis/ALD_yearly_total.nc ./synthesis/ALD_yearly_total.nc
    # plot the time series


******************************
Plot Seasonal Dynamic
******************************

Plot the seasonal dynamic of GPP for the same three decades: [1990-2010],
[2040-2050], [2090-2100]. The plot should show the mean monthly GPP computed
across each decade as lines, and the standard deviation across the mean as
envelopes.

.. collapse:: Example Python Solution
   :class: broken

   .. jupyter-execute::

      df, meta = build_full_dataframe(var='GPP', timeres='monthly', px_y=0, px_x=0)
      
      july = df['1901-7'::12]
      fig, ax = plt.subplots()
      for i, pft in enumerate(july.columns):
        ax.boxplot(july[pft], positions=[i+1], notch=True)
      plt.title("July")
      ax.set_ylabel('GPP ({})'.format(meta['hds_units']))
      ax.set_xlabel('PFT')

      # This works too...
      df.plot(kind='box')

      # Or this
      df['1901-08'::12].plot(kind='box')

      # Gets the monthlies 
      #for m in range(0,12):
      #  print(df[m::12])
      #  print()

      # Make timeseries plot
      plt.close()
      fig, ax = plt.subplots(1,1)
      ax.plot(df['1940':'1950'][0])
      plt.savefig('GPP_SAMPLE.png')   

      # Make timeseries of July GPP values
      plt.close()
      fig, ax = plt.subplots(1,1)
      ax.plot(df[6::12][0])
      plt.savefig('SAMPLE.png')  

      # Or this:, gives julys for a decade
      df[6::12]['1940':'1950']

.. collapse:: Python solution 2 (does not use common setup)
  :class: broken

  .. code::

    ###### SEASONAL PLOT OF GPP ######
    ##################################


    # Compute mean monthly GPP by decades
    final = pd.DataFrame()
    for VAR in ['GPP']:
      print(VAR)
      ttl = pd.DataFrame()
      for mode in ['tr', 'sc']:
        print(mode)
        # Check the output of the selected mode/variable exists
        if (len(glob.glob(ODir + '/' + VAR + '*' + mode + '.nc')) > 0):
          filename = os.path.basename(glob.glob(ODir + '/' + VAR + '*' + mode + '.nc')[0])
          # Check the outputs are monthly 
          if 'monthly' in filename:
            # Read the dataset
            ds = xr.open_dataset(glob.glob(ODir + '/' + VAR + '*' + mode + '.nc')[0])
            data = ds.to_dataframe()
            data.reset_index(inplace=True)
            # Select pixel of iinterest
            data = data.rename(columns={VAR: 'value'})
            # Format the time/date dimension
            data['time'] = data['time'].astype('|S80')
            data['time'] = data['time'].astype('|datetime64[ns]')
            data['year'] = data['time'].dt.year
            data['month'] = data['time'].dt.month
            # Sum the fluxes by secondary dimensions
            if (('pft' in data.columns) | ('pftpart' in data.columns) | ('layer' in data.columns)):
              data = data.groupby(['year','month','x','y'])[['value']].agg(['sum'])
              data.reset_index(inplace=True)
              data.columns = ['year','month', 'x', 'y','value']
            ttl = ttl.append(data)
      decade = pd.DataFrame()
      # Compute the monthly averages by decade
      for i in declist:
        dec = ttl[(ttl['year'] >= i) & (ttl['year'] < i+10)].groupby(['x','y','month'])[['value']].agg(['mean','std'])
        dec.reset_index(inplace=True)
        dec.columns = ['x','y','month','mean','std']
        dec['decade'] = '[' + str(i) + '-' + str(i+9) +']'
        dec['variable'] = VAR
        decade = decade.append(dec)
      final = decade.append(decade)

    # Plotting the data
    plot = final[(final['x']==0) & (final['y']==0)]

    plt.plot(plot[plot['decade']=='[1940-1949]']['month'], plot[plot['decade']=='[1940-1949]']['mean'], alpha=0.5, c='blue', label='[1940-1949]')
    plt.fill_between(plot[plot['decade']=='[1940-1949]']['month'], plot[plot['decade']=='[1940-1949]']['mean']-plot[plot['decade']=='[1940-1949]']['std'], plot[plot['decade']=='[1940-1949]']['mean']+plot[plot['decade']=='[1940-1949]']['std'], alpha=0.2,color='blue',linewidth=0.0)

    plt.plot(plot[plot['decade']=='[1990-1999]']['month'], plot[plot['decade']=='[1990-1999]']['mean'], alpha=0.5, c='cyan', label='[1990-1999]')
    plt.fill_between(plot[plot['decade']=='[1990-1999]']['month'], plot[plot['decade']=='[1990-1999]']['mean']-plot[plot['decade']=='[1990-1999]']['std'], plot[plot['decade']=='[1990-1999]']['mean']+plot[plot['decade']=='[1990-1999]']['std'], alpha=0.2,color='cyan',linewidth=0.0)

    plt.plot(plot[plot['decade']=='[2040-2049]']['month'], plot[plot['decade']=='[2040-2049]']['mean'], alpha=0.5, c='orange', label='[2040-2049]')
    plt.fill_between(plot[plot['decade']=='[2040-2049]']['month'], plot[plot['decade']=='[2040-2049]']['mean']-plot[plot['decade']=='[2040-2049]']['std'], plot[plot['decade']=='[2040-2049]']['mean']+plot[plot['decade']=='[2040-2049]']['std'], alpha=0.2,color='orange',linewidth=0.0)

    plt.plot(plot[plot['decade']=='[2090-2099]']['month'], plot[plot['decade']=='[2090-2099]']['mean'], alpha=0.5, c='red', label='[2090-2099]')
    plt.fill_between(plot[plot['decade']=='[2090-2099]']['month'], plot[plot['decade']=='[2090-2099]']['mean']-plot[plot['decade']=='[2090-2099]']['std'], plot[plot['decade']=='[2090-2099]']['mean']+plot[plot['decade']=='[2090-2099]']['std'], alpha=0.2,color='red',linewidth=0.0)

    plt.xlabel('Month')
    plt.ylabel('GPP (g/m2/y)')
    plt.legend()
    plt.show()

*****************************
Plot Soil Temperatures
*****************************

Plot the soil temperature profile for [June-July-August] period for the same
three years: 1990, 2040, 2090. The plot should show the mean summer temperature
computed across each decade as lines, and the standard deviation across the mean
as envelops.

.. collapse:: Example Python Solution
   :class: broken

   Write this...
