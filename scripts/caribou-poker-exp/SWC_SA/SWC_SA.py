#!/usr/bin/env python
# coding: utf-8

import sys
import os
# setting path
sys.path.append('/work/scripts')
import pandas as pd
import seaborn as sns


import Sensitivity as sa
import output_utils as ou


work_dir='/data/workflows/US-Prr_SWC_SA'


if not os.path.isdir(work_dir):
        os.mkdir(work_dir)


driver = sa.SensitivityDriver(opt_run_setup='--tr-yrs=121 --sp-yrs=300 --eq-yrs=1000 ')
driver.set_work_dir(work_dir)
driver.clean()
driver.set_seed_path('/work/parameters')

driver.design_experiment(Nsamples = 4, cmtnum = 13, params = ['hksat(m)','hksat(f)','hksat(f)','rhq10'], pftnums = [None, None, None, None])


driver.setup_multi()


driver.sample_matrix


driver.run_all_samples()


driver.plot_sensitivity_matrix()


print(LWCLAYER)


def seasonal_profile(VAR, depth, thickness, time_range, months, z):
    LWCLAYER


def seasonal_profile(VAR, depth, thickness, time_range, months, z):
    '''
    VAR : variable dataframe (i.e. TLAYER - temperature by layer)
    depth : associated LAYERDEPTH dataframe
    thickness : associated LAYERDZ dataframe
    time_range : time period to be calculated over -  e.g. ['2011-01-01','2021-01-01']
    months : list of strings - months included in calculation - ['Jan', 'Feb', 'Dec'] (e.g winter season)
    z : array for depth required for interpolation to the same depth profile 
         (typically, np.linspace(min(depth), max(depth), resolution)
    '''
    month_range = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    startyr, endyr = time_range[0], time_range[1]

    #Limiting by time range    
    range_series = VAR[startyr:endyr]
    LD = depth[startyr:endyr]
    LZ = thickness[startyr:endyr]

    #Averaging by layer for months in month_range
    range_series = range_series[range_series.index.month.isin([i+1 for i, e in enumerate(month_range) if e in months])]
    LD = (LD[LD.index.month.isin([i+1 for i, e in enumerate(month_range) if e in months])]).mean()
    LZ = (LZ[LZ.index.month.isin([i+1 for i, e in enumerate(month_range) if e in months])]).mean()

    #Creating lists for interpolation
    mean = range_series.mean().values.tolist()    
    maxi = range_series.max().values.tolist()
    mini = range_series.min().values.tolist()
    std =  range_series.std().values.tolist()

    #Creating list with z position at the center of each layer
    print(LD)
    print(LZ)
    zp = (LD + LZ/2).values.tolist()
    print(zp)
    print(z)
    print(mean)
    
    #Indexes of depths with fill values
    indexes = [i for i,v in enumerate(zp) if v < 0]

    #Removing indexes with fill values
    for index in sorted(indexes, reverse=True):
        del zp[index]
        del mean[index]
        del mini[index]
        del maxi[index]
        del std[index]

    #Interpolating seasonal mean, min, max, and standard deviation
    interp_mean=np.interp(z,zp,mean)
    interp_mini=np.interp(z,zp,mini)
    interp_maxi=np.interp(z,zp,maxi)
    interp_std=np.interp(z,zp,std)
    
    return z, interp_mean, interp_std, interp_mini, interp_maxi


ou.load_trsc_dataframe


LWCLAYER = ou.load_trsc_dataframe(var ='LWCLAYER', timeres='monthly', px_y=0, px_x=1, fileprefix='/data/workflows/US-Prr_SWC_SA/sample_000000000/output/')[0]
TLAYER = ou.load_trsc_dataframe(var ='TLAYER', timeres='monthly', px_y=0, px_x=1, fileprefix='/data/workflows/US-Prr_SWC_SA/sample_000000000/output/')[0]
LAYERDEPTH = ou.load_trsc_dataframe(var ='LAYERDEPTH', timeres='monthly', px_y=0, px_x=1, fileprefix='/data/workflows/US-Prr_SWC_SA/sample_000000000/output/')[0]
LAYERDZ = ou.load_trsc_dataframe(var ='LAYERDZ', timeres='monthly', px_y=0, px_x=1, fileprefix='/data/workflows/US-Prr_SWC_SA/sample_000000000/output/')[0]


LAYERTYPE = ou.load_trsc_dataframe(var ='LAYERTYPE', timeres='monthly', px_y=0, px_x=1, fileprefix='/data/workflows/US-Prr_SWC_SA/sample_000000000/output/')[0]


pf_obs_path = '/data/comparison_data/US-Prr-monthly.csv'
pf_obs= pd.read_csv(pf_obs_path, parse_dates=['m_y'])
pf_obs['Month'] = pf_obs['m_y'].dt.month
pf_obs = pf_obs.set_index('m_y')
swc = pf_obs[['SWC_1_1_1', 'SWC_1_2_1', 'SWC_1_3_1', 'SWC_1_4_1', 'SWC_1_5_1']]/100
#swc['Month'] = pf_obs['Month']
swc_depths = pd.DataFrame({'SWC_1_1_1':[0.05]*len(pf_obs), 'SWC_1_2_1':[0.1]*len(pf_obs), 'SWC_1_3_1':[0.2]*len(pf_obs),
                          'SWC_1_4_1':[0.3]*len(pf_obs), 'SWC_1_5_1':[0.4]*len(pf_obs)})
swc_depths = swc_depths.set_index(swc.index)
swc_thickness = pd.DataFrame({'SWC_1_1_1':[0.75]*len(pf_obs), 'SWC_1_2_1':[0.75]*len(pf_obs), 'SWC_1_3_1':[0.1]*len(pf_obs),
                          'SWC_1_4_1':[0.1]*len(pf_obs), 'SWC_1_5_1':[0.1]*len(pf_obs)})
swc_thickness = swc_thickness.set_index(swc.index)


LAYERDZ


swc


import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots()

z, mean, std, mn, mx = seasonal_profile(
                                        TLAYER, LAYERDEPTH, LAYERDZ, ['1901-01-01', '1902-12-01'], 
                                        ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
                                        np.linspace(min(LAYERDEPTH), max(LAYERDEPTH), 100)
                                        )


ax.plot(mean, z, label="annual mean")
ax.fill_betweenx(z, mn, mx, alpha=0.2, label="annual range")
ax.plot(np.zeros(len(z)), z, 'k--', alpha=0.5) #Zero degree line

plt.legend(loc="lower right", fontsize=12)

ax.xaxis.tick_top()
ax.set_xlabel(f"Temperature [$^\circ$C]", fontsize=14)
ax.xaxis.set_label_position('top') 

ax.set_ylabel(f"Depth [m]", fontsize=14)
plt.ylim(0,1)
ax.invert_yaxis()

plt.show()


import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots()

z, mean, std, mn, mx = seasonal_profile(
                                        LWCLAYER, LAYERDEPTH, LAYERDZ, ['2010-01-01', '2021-12-01'], 
                                        ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
                                        np.linspace(min(LAYERDEPTH), max(LAYERDEPTH), 100)
                                        )


ax.plot(mean, z, label="annual mean")
ax.fill_betweenx(z, mn, mx, alpha=0.2, label="annual range")
ax.plot(np.zeros(len(z)), z, 'k--', alpha=0.5) #Zero degree line

plt.legend(loc="lower right", fontsize=12)

ax.xaxis.tick_top()
ax.set_xlabel(f"Temperature [$^\circ$C]", fontsize=14)
ax.xaxis.set_label_position('top') 

ax.set_ylabel(f"Depth [m]", fontsize=14)
plt.ylim(0,1)
ax.invert_yaxis()


plt.show()


import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots()

z, mean, std, mn, mx = seasonal_profile(
                                        swc, swc_depths, swc_thickness, ['2010-01-01', '2021-12-01'], 
                                        ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
                                        np.linspace(np.nanmin(swc_depths), np.nanmax(swc_depths), 100)
                                        )


ax.plot(mean, z, label="annual mean")
#ax.fill_betweenx(z, mn, mx, alpha=0.2, label="annual range")
ax.plot(np.zeros(len(z)), z, 'k--', alpha=0.5) #Zero degree line

plt.legend(loc="lower right", fontsize=12)

ax.xaxis.tick_top()
ax.set_xlabel(f"Temperature [$^\circ$C]", fontsize=14)
ax.xaxis.set_label_position('top') 

ax.set_ylabel(f"Depth [m]", fontsize=14)
plt.ylim(0,1)
ax.invert_yaxis()


plt.show()


print(mean)


len(swc_groupby)


swc_groupby['depth'] = [-.5, -.1, -.2, -.3, -.4]


sns.lineplot(data=swc_groupby, x='1', y='depth')




