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

The examples assume that you are running on the ``dvmdostem`` Docker stack.

***********************
Design Specification
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

   I think we may need these too:

      - LAYERDZ, LAYERDEPTH, LAYERTYPE
      - MINEC,
      - DEEPC, DEEPDZ
      - SHLWC, SHLWDZ
      - SOMA, SOMPR, SOMCR, SOMRAWC

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
      $ outspec_utils.py config/output_spec.csv --on SHLWC y 
      $ outspec_utils.py config/output_spec.csv --on DEEPC y 
      $ outspec_utils.py config/output_spec.csv --on MINEC y 
      $ outspec_utils.py config/output_spec.csv --on LAYERDZ y l
      $ outspec_utils.py config/output_spec.csv --on LAYERDEPTH y l
      $ outspec_utils.py config/output_spec.csv --on LAYERTYPE y l 
      $ runmask-util.py --reset run-mask.nc 
      $ runmask-util.py --yx 0 0 run-mask.nc 
      $ runmask-util.py --yx 0 0 run-mask.nc 
      $ runmask-util.py --yx 1 1 run-mask.nc 
      $ runmask-util.py --yx 2 2 run-mask.nc 
      $ dvmdostem --force-cmt 5 -p 100 -s 250 -e 1000 -t 115 -n 85

***************************
Example Python setup
***************************

The Python example solutions share a bunch of code. For this reason, we will put
the common setup here and not need to repeat these lines in each example. The
paths assume that these examples will be run on the TEM Docker stack. Subsequent
Python example solutions assume that these setup commands have been run.

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
        '''Not sure how this should work for PFT and LAYER files???'''
      
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
Explore inputs 
**************************

Exploring the input dataset, determine the start year of the historical, and the
projected climate time series. From the length of the time dimension, compute
the end year and the total number of years of the time series. Note that this
information is used to set the number of transient and scenario years to run.

.. collapse:: Example with ncdump
   :class: working

   .. code:: 

      $ ncdump -h /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_TOOLIK_FIELD_STATION_10x10/historic-climate.nc  | grep time:units
		time:units = "days since 1901-1-1 0:0:0" ;
		time:long_name = "time" ;
		time:calendar = "365_day" ;
   
      $ ncdump -h /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_TOOLIK_FIELD_STATION_10x10/historic-climate.nc  | grep "time\ =\ "
   	time = UNLIMITED ; // (1380 currently)

   So ``1380/12 = 115``. Looks like 115 years. 

.. collapse:: Example input_util.py plot
   :class: working

   .. jupyter-execute::

      import input_util as iu
      import argparse

      args = {'command': 'climate-ts-plot',
        'input_folder': '/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_TOOLIK_FIELD_STATION_10x10/',
        'stitch': False,
        'type': 'spatial-temporal-summary',
        #'yx': [0, 0],
      }

      iu.climate_ts_plot(argparse.Namespace(**args))

**************************
Computing Means
**************************

Compute the mean vegetation and soil carbon stocks for the following decades:
[1990-2010], [2040-2050], [2090-2100].

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

.. .. collapse:: solution
..    :class: broken

..    .. code:: 

..       Find these...
..       Stocks                 [1990-2010] [2040-2050] [2090-2100]
..               Vegetation
      
..                   Fibric
..          Soil      Humic
..                  Mineral

..                    Total


****************************
Computing Monthly NEE
****************************

Compute monthly Net Ecosystem Exchange (NEE) for the historical and scenario
simulations. Indicate how you formulated NEE.

.. collapse:: WRITE THIS
   :class: broken
   
   WRITE THIS...


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
   :class: partial

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




   .. .. code::

   ..    Fluxes                         [1990-2010]    [2040-2050]    [2090-2100]

   ..    GPP
   ..    Autotrophic respiration
   ..    Heterotrophic respiration
   ..    Net Ecosystem Exchange


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
