#!/usr/bin/env python
# coding: utf-8

from scipy.interpolate import interp1d

def soil_contourbydepth(df, df_depth, df_dz, start_time=None, end_time=None, 
                  depth_start=None, depth_end=None, n=100, zero=False, ylim=False, col_bar_label='Temperature [$\^circ$C]'):
    '''
    data_path: path to output data to plot
    output_var: variable to plot (technically, doesn't need to be temperature)
    res: time resolution of output data
    px, py: pixel location of data
    output_folder: name of output folder
    start_time, end_time: start and end year of data to plot
    depth_start, depth_end: starting and ending depth to be plotted (in meters)
    n: levels on the colobar
    '''
#     df = interp_var
#     df_depth = depth
#     df_
#     df_depth, meta_depth = load_trsc_dataframe(var='LAYERDEPTH',  timeres=res, px_y=py, px_x=px, fileprefix=data_path+'/'+output_folder)
#     df_dz, meta_dzh = load_trsc_dataframe(var='LAYERDZ',  timeres=res, px_y=py, px_x=px, fileprefix=data_path+'/'+output_folder)
    
    layers = df.columns.astype(float)
    times = pd.to_datetime(df.index)
    
    # Filter data based on start_time and end_time
    if start_time is not None and end_time is not None:
        mask = (times >= start_time) & (times <= end_time)
        df = df.loc[mask]
        times = times[mask]

    # Extract necessary data
    depths = df_depth.iloc[:, :-2].values
    dz = df_dz.iloc[:, :-2].values
    temperature = df.iloc[:, :-2].values
    xp = depths + dz / 2  # Center of each layer, x-coordinates of the data points for interp1d

    # Create a regular grid of depth values
    ii=np.unravel_index(np.argmax(depths), depths.shape)
    maxd=depths.max()+(dz[ii]/2)
    regular_depths = np.arange(0, maxd, 0.01)

    # Interpolate temperature onto the regular grid
    interp_temperature = np.empty((temperature.shape[0], regular_depths.shape[0]))
    for i in range(temperature.shape[0]):
        f = interp1d(xp[i], temperature[i], kind='linear', fill_value='extrapolate')
        interp_temperature[i] = f(regular_depths)

    # Create contour plot
    color_axes = max(np.max(temperature), np.abs(np.min(temperature)))
    plt.contourf(times, regular_depths, interp_temperature.T, cmap='seismic', vmin=-color_axes, vmax=color_axes, levels=n)

    # Add colorbar
    plt.colorbar(label=col_bar_label)

    # Set labels and title
    plt.xlabel('Time')
    plt.ylabel('Depth (m)')

    # Show the plot
    if ylim:
        plt.ylim(ylim[0], ylim[1])
    else:
        plt.ylim(depth_start, depth_end)
        
    
    df_interp = pd.DataFrame(index=times, columns=regular_depths, data=interp_temperature)

    if zero:
        plt.contour(times, regular_depths, interp_temperature.T, colors=('k',), linewidths=(1,), levels=zero)

    plt.gca().invert_yaxis()
    
    return df_interp


def soil_contourbydepth_diff(df, df_depth, df_dz, df_diff=None, df_depth_diff=None, df_dz_diff=None,
                             start_time=None, end_time=None,
                             depth_start=None, depth_end=None,
                             n=100, zero=False, ylim=False, 
                             col_bar_label='Temperature [$\^circ$C]'):
    '''
    data_path: path to output data to plot
    output_var: variable to plot (technically, doesn't need to be temperature)
    res: time resolution of output data
    px, py: pixel location of data
    output_folder: name of output folder
    start_time, end_time: start and end year of data to plot
    depth_start, depth_end: starting and ending depth to be plotted (in meters)
    n: levels on the colobar
    '''
    
    layers = df.columns.astype(float)
    layers_diff = df_diff.columns.astype(float)
    
    times = pd.to_datetime(df.index)
    times_diff = pd.to_datetime(df_diff.index)
        
    # Filter data based on start_time and end_time
    if start_time is not None and end_time is not None:
        mask = (times >= start_time) & (times <= end_time)
        df = df.loc[mask]; df_diff = df_diff.loc[mask]
        times = times[mask]

    # Extract necessary data
    depths = df_depth.iloc[:, :-2].values; depths_diff = df_depth_diff.iloc[:, :-2].values
    dz = df_dz.iloc[:, :-2].values; dz_diff = df_dz_diff.iloc[:, :-2].values
    temperature = df.iloc[:, :-2].values; temperature_diff = df_diff.iloc[:, :-2].values
    xp = depths + dz / 2  # Center of each layer, x-coordinates of the data points for interp1d
    xp_diff = depths_diff + dz_diff / 2
    
    # Create a regular grid of depth values
    ii=np.unravel_index(np.argmax(depths), depths.shape)
    maxd=depths.max()+(dz[ii]/2)
    regular_depths = np.arange(0, maxd, 0.01)

    ii_diff=np.unravel_index(np.argmax(depths_diff), depths_diff.shape)
    maxd_diff=depths_diff.max()+(dz_diff[ii]/2)
    regular_depths_diff = np.arange(0, maxd_diff, 0.01)

    # Interpolate temperature onto the regular grid
    interp_temperature = np.empty((temperature.shape[0], regular_depths.shape[0]))
    for i in range(temperature.shape[0]):
        f = interp1d(xp[i], temperature[i], kind='linear', fill_value='extrapolate')
        interp_temperature[i] = f(regular_depths)

    interp_temperature_diff = np.empty((temperature_diff.shape[0], regular_depths.shape[0]))
    for i in range(temperature_diff.shape[0]):
        f = interp1d(xp_diff[i], temperature_diff[i], kind='linear', fill_value='extrapolate')
        interp_temperature_diff[i] = f(regular_depths)

    # Create contour plot
    color_axes = max(np.max(interp_temperature_diff.T - interp_temperature.T), np.abs(np.min(interp_temperature_diff.T - interp_temperature.T)))
    plt.contourf(times, regular_depths, interp_temperature_diff.T - interp_temperature.T, cmap='seismic', vmin=-color_axes, vmax=color_axes, levels=n)

    # Add colorbar
    plt.colorbar(label=col_bar_label)

    # Set labels and title
    plt.xlabel('Time')
    plt.ylabel('Depth (m)')

    # Show the plot
    if ylim:
        plt.ylim(ylim[0], ylim[1])
    else:
        plt.ylim(depth_start, depth_end)
        
    
    df_interp = pd.DataFrame(index=times, columns=regular_depths, data=interp_temperature_diff - interp_temperature)

    if zero:
        plt.contour(times, regular_depths, interp_temperature.T, colors=('k',), linewidths=(1,), levels=[0])

    plt.gca().invert_yaxis()
    
    return df_interp


# Importing dependencies
import sys
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import netCDF4 as nc

sys.path.insert(0, '/work/scripts/util/')

from output import load_trsc_dataframe

# Setting directory structure

base_dir = "/data/workflows/latent_heat/apparent_heat_cap_ics/"
f_dir = [
    "ref",
    "lhc_happ"
    # "env"
    ]
f_name = [
    "ref",
    "unfroz",
    ]


# Importing variables

units = {}; monthly = {} ; yearly = {}

py = 0; px = 0

yearly_vars = ["ALD"]
monthly_vars = ['WATERTAB', 'SNOWTHICK']

layer_vars = ["LAYERDZ", "LAYERDEPTH", "LAYERTYPE", "LWCLAYER", "IWCLAYER", "TLAYER", "FRONTSDEPTH", "FRONTSTYPE", "TCLAYER"]
layer_data = {key: [] for key in layer_vars}
soil_vars = ["ground", "moss", "shlw", "deep", "mine"]
soil_profiles = {key: [] for key in soil_vars}

for i, DIR in enumerate(f_dir):
    
    df = pd.DataFrame() 
    
    for VAR in yearly_vars:
        
        dfa, meta = load_trsc_dataframe(var=VAR, timeres='yearly', px_y=py,
                                       px_x=px, fileprefix=f'{base_dir+DIR}/output')
        if dfa.columns.stop>1:
            dfa = pd.DataFrame(dfa.sum(axis=1))
        dfa.columns = [VAR];df = pd.concat([df,dfa], axis=1)
        
        if f_dir.index(DIR)==0:
            
            units[VAR]=meta['var_units']
        
    yearly[f_name[i]] = df
    
    df = pd.DataFrame()
    
    for VAR in monthly_vars:
        
        dfa, meta = load_trsc_dataframe(var=VAR, timeres='monthly', px_y=py,
                                       px_x=px, fileprefix=f'{base_dir+DIR}/output')
        if dfa.columns.stop>1:
            dfa = pd.DataFrame(dfa.sum(axis=1))
        dfa.columns = [VAR];df = pd.concat([df,dfa], axis=1)

        if f_dir.index(DIR)==0:
            
            units[VAR]=meta['var_units']
        
    monthly[f_name[i]] = df
    
    for VAR in layer_vars:
        
        dfa, meta = load_trsc_dataframe(var=VAR, timeres='monthly', px_y=py,
                                       px_x=px, fileprefix=f'{base_dir+DIR}/output')
        layer_data[VAR] += [dfa]

        if f_dir.index(DIR)==0:
            
            units[VAR]=meta['var_units']
            
    ground = layer_data["LAYERDEPTH"][i][0]        
    soil_profiles["ground"] += [pd.DataFrame({"ground":ground})]
    
    moss = ground - (layer_data["LAYERDZ"][i].iloc[:,layer_data["LAYERTYPE"][i][:1]
                    .apply(lambda x: layer_data["LAYERTYPE"][i][:1].columns[x==0], axis = 1)
                    .values[0]].sum(axis=1))
    soil_profiles["moss"] += [pd.DataFrame({"moss":moss})]
    
    shlw = moss - (layer_data["LAYERDZ"][i].iloc[:,layer_data["LAYERTYPE"][i][:1]
                    .apply(lambda x: layer_data["LAYERTYPE"][i][:1].columns[x==1], axis = 1)
                    .values[0]].sum(axis=1))
    soil_profiles["shlw"] += [pd.DataFrame({"shlw":shlw})]
    
    deep = shlw - (layer_data["LAYERDZ"][i].iloc[:,layer_data["LAYERTYPE"][i][:1]
                    .apply(lambda x: layer_data["LAYERTYPE"][i][:1].columns[x==2], axis = 1)
                    .values[0]].sum(axis=1))
    soil_profiles["deep"] += [pd.DataFrame({"deep":deep})]
    
    mine = deep - (layer_data["LAYERDZ"][i].iloc[:,layer_data["LAYERTYPE"][i][:1]
                    .apply(lambda x: layer_data["LAYERTYPE"][i][:1].columns[x==3], axis = 1)
                    .values[0]].sum(axis=1))
    soil_profiles["mine"] += [pd.DataFrame({"mine":mine})]


# Plotting temperature
n_layers = 10

date_start = pd.to_datetime("1901")
date_end = pd.to_datetime("1903")

fig, ax = plt.subplots(n_layers, 1, sharex=True, sharey=True)

for i in range(0, n_layers):
    
    ax[i].plot(layer_data["TLAYER"][0][date_start:date_end][i], alpha = 0.5, label="reference")
    ax[i].plot(layer_data["TLAYER"][1][date_start:date_end][i], alpha = 0.5, label="test")
    ax[i].set_title(f'Layer {i+1}')
    
ax[0].legend(bbox_to_anchor=(1.0, 1.05), loc="upper left", fontsize=12)

plt.subplots_adjust(left=None, bottom=None, right=None, top=1.1, wspace=None, hspace=0.5)
fig.text(0.5, 0.01, 'Year', ha='center', fontsize=14)
fig.text(0.01, 0.55, f'Temperature [{units["TLAYER"]}]', va='center', rotation='vertical', fontsize=14)

plt.subplots_adjust(left=None, bottom=None, right=1.5, top=2, wspace=None, hspace=None)

plt.show()


# Plotting liquid water
n_layers = 5

date_start = pd.to_datetime("1901")
date_end = pd.to_datetime("1910")

fig, ax = plt.subplots(n_layers, 1, sharex=True, sharey=True)

for i in range(0, n_layers):
    
    ax[i].plot(layer_data["LWCLAYER"][0][date_start:date_end][i], alpha = 0.5, label="reference")
    ax[i].plot(layer_data["LWCLAYER"][1][date_start:date_end][i], alpha = 0.5, label="test")
    
ax[0].legend(bbox_to_anchor=(1.0, 1.05), loc="upper left", fontsize=12)

plt.subplots_adjust(left=None, bottom=None, right=None, top=1.1, wspace=None, hspace=0.5)
fig.text(0.5, 0.01, 'Year', ha='center', fontsize=14)
fig.text(0.01, 0.55, f'Liquid water content [{units["LWCLAYER"]}]', va='center', rotation='vertical', fontsize=14)
plt.show()


# Plotting ice water content
n_layers = 5

date_start = pd.to_datetime("1901")
date_end = pd.to_datetime("1910")

fig, ax = plt.subplots(n_layers, 1, sharex=True, sharey=True)

for i in range(0, n_layers):
    
    ax[i].plot(layer_data["IWCLAYER"][0][date_start:date_end][i], alpha = 0.5, label="reference")
    ax[i].plot(layer_data["IWCLAYER"][1][date_start:date_end][i], alpha = 0.5, label="test")
    
ax[0].legend(bbox_to_anchor=(1.0, 1.05), loc="upper left", fontsize=12)

plt.subplots_adjust(left=None, bottom=None, right=None, top=1.1, wspace=None, hspace=0.5)
fig.text(0.5, 0.01, 'Year', ha='center', fontsize=14)
fig.text(0.01, 0.55, f'Ice water content [{units["IWCLAYER"]}]', va='center', rotation='vertical', fontsize=14)
plt.show()


# Plotting liquid water against temperature
n_layers = 3

date_start = pd.to_datetime("1901")
date_end = pd.to_datetime("1910")

fig, ax = plt.subplots(n_layers, 1, sharex=True, sharey=True)

for i in range(0, n_layers):
    
    ax[i].scatter(layer_data["TLAYER"][0][date_start:date_end][i],layer_data["LWCLAYER"][0][date_start:date_end][i], alpha = 0.5, label="reference")
    ax[i].scatter(layer_data["TLAYER"][1][date_start:date_end][i], layer_data["LWCLAYER"][1][date_start:date_end][i], alpha = 0.5, label="test")
    
ax[0].legend(bbox_to_anchor=(1.0, 1.05), loc="upper left", fontsize=12)

plt.subplots_adjust(left=None, bottom=None, right=None, top=1.1, wspace=None, hspace=0.5)
fig.text(0.5, 0.01, f"Temperature [{units['TLAYER']}]", ha='center', fontsize=14)
fig.text(0.01, 0.55, f'Liquid water content [{units["LWCLAYER"]}]', va='center', rotation='vertical', fontsize=14)
plt.show()


# Plotting active layer depth

date_start = pd.to_datetime("1901")
date_end = pd.to_datetime("2100")

plt.plot(yearly["ref"]["ALD"][date_start:date_end], alpha = 0.5, label="reference")
plt.plot(yearly["unfroz"]["ALD"][date_start:date_end], alpha = 0.5, label="test")

plt.legend(bbox_to_anchor=(1.0, 1.05), loc="upper left", fontsize=12)
plt.xlabel("Year", fontsize=12)
plt.ylabel(f"Active layer depth [{units['ALD']}]", fontsize=12)
plt.show()


# Plotting water table depth

date_start = pd.to_datetime("1901")
date_end = pd.to_datetime("1910")

plt.plot(monthly["ref"]["WATERTAB"][date_start:date_end], alpha = 0.5, label="reference")
plt.plot(monthly["unfroz"]["WATERTAB"][date_start:date_end], alpha = 0.5, label="test")

plt.legend(bbox_to_anchor=(1.0, 1.05), loc="upper left", fontsize=12)
plt.xlabel("Year", fontsize=12)
plt.ylabel(f"Water table depth [{units['WATERTAB']}]", fontsize=12)
plt.show()


ymin = -0.5;  ymax = 0.3
xmin = pd.to_datetime("1901");  xmax = pd.to_datetime("1910")

fig, axis = plt.subplots(1, 2)

for i, run in enumerate(f_name):
    
    ax = axis[i]
        
    ax.set_facecolor('C0')
    
    ax.fill_between(monthly[run]["SNOWTHICK"].index, np.zeros(len(monthly[run]["SNOWTHICK"])), 
                    monthly[run]["SNOWTHICK"], color='white', label="Snow")
    
    ax.fill_between(soil_profiles["moss"][i].index, soil_profiles["moss"][i]["moss"], 
                    soil_profiles["ground"][i]["ground"],color="darkgreen", label='Moss', zorder=5)
    
    ax.fill_between(soil_profiles["shlw"][i].index, soil_profiles["shlw"][i]["shlw"], 
                    soil_profiles["moss"][i]["moss"],color="chocolate", label='Fibric')
    
    ax.fill_between(soil_profiles["deep"][i].index, soil_profiles["deep"][i]["deep"], 
                    soil_profiles["shlw"][i]["shlw"],color="sienna", label="Humic")
    
    ax.fill_between(soil_profiles["mine"][i].index, soil_profiles["mine"][i]["mine"], 
                    soil_profiles["deep"][i]["deep"],color="tan", label='Mineral')
    
    ax.plot(monthly[run]["WATERTAB"].index, -monthly[run]["WATERTAB"], 'b-.', label="Water table")
    
    ax.plot(yearly[run]["ALD"].index, -yearly[run]["ALD"], 'k-x', label="Permafrost table")
    ax.fill_between(yearly[run]["ALD"].index, -10 * np.ones(len(yearly[run]["ALD"])), -yearly[run]["ALD"], 
                    color='k', alpha=0.5)
    
#     ax.plot(layer_data["FRONTSDEPTH"][i][0].index, -layer_data["FRONTSDEPTH"][i].replace(-9999, np.nan), 'k')

    
    ax.set_title(f_name[i], fontsize=18)
    ax.set_ylim(ymin,ymax)
    ax.set_xlim(xmin, xmax)
    ax.set_xlabel('Year', fontsize=14)
    if i == 0:
        ax.set_ylabel('Soil profile', fontsize=14)
    
    
        
handles, labels = plt.gca().get_legend_handles_labels()

ax.legend(handles=handles, bbox_to_anchor=(1.05, 1.0), loc='upper left', fontsize=12)
        
plt.subplots_adjust(left=None, bottom=None, right=1.5, top=1.2, wspace=None, hspace=None)


layer_data["LAYERTYPE"][1]["1901":"1910"]


# #### Need to incorporate a color dependent line based on FRONTSTYPE value (-1, 1) 

xmin = pd.to_datetime("1901");  xmax = pd.to_datetime("1906")

fig, ax = plt.subplots(1,2)

ax[0].plot(layer_data["FRONTSDEPTH"][0][0][xmin:xmax].index, -layer_data["FRONTSDEPTH"][0][xmin:xmax].replace(-9999, np.nan))
ax[1].plot(layer_data["FRONTSDEPTH"][0][0][xmin:xmax].index, -layer_data["FRONTSTYPE"][0][xmin:xmax].replace(-9999, np.nan))

ax[0].plot(layer_data["FRONTSDEPTH"][1][0][xmin:xmax].index, -layer_data["FRONTSDEPTH"][1][xmin:xmax].replace(-9999, np.nan))
ax[1].plot(layer_data["FRONTSDEPTH"][1][0][xmin:xmax].index, -layer_data["FRONTSTYPE"][1][xmin:xmax].replace(-9999, np.nan))

ax[0].set_xlabel("Year", fontsize=12); ax[1].set_xlabel("Year", fontsize=12)
ax[0].set_ylabel("Front depth", fontsize=12)
ax[1].set_ylabel("Front type", fontsize=12)

plt.subplots_adjust(left=None, bottom=None, right=1.5, top=1.2, wspace=None, hspace=None)

plt.show()


i = 0; var = "TLAYER"; start='1901'; end='1905'; N=50; D1=0;D2=0.5; Z=[0]; Y=False;

fig = plt.figure()
ax = fig.add_subplot(121)

ref_interp_T = soil_contourbydepth(df = layer_data[var][i], df_depth = layer_data["LAYERDEPTH"][i], df_dz = layer_data["LAYERDZ"][i],
                                 start_time=start, end_time=end, depth_start=D1, depth_end=D2, n=N, zero=Z, ylim=Y,col_bar_label=var)

plt.title(f'{f_name[i]}')
ax = fig.add_subplot(122)

j = 1
unf_interp_T = soil_contourbydepth(df = layer_data[var][j], df_depth = layer_data["LAYERDEPTH"][j], df_dz = layer_data["LAYERDZ"][j],
                                 start_time=start, end_time=end, depth_start=D1, depth_end=D2, n=N, zero=Z, ylim=Y,col_bar_label=var)
plt.title(f'{f_name[j]}')
plt.subplots_adjust(left=None, bottom=None, right=1.75, top=1, wspace=None, hspace=None)
plt.show()

fig, ax = plt.subplots(1,1,figsize=(15, 5))
unfroz_interp = soil_contourbydepth_diff(df = layer_data[var][i], df_depth = layer_data["LAYERDEPTH"][i], df_dz = layer_data["LAYERDZ"][i],
                                         df_diff = layer_data[var][j], df_depth_diff = layer_data["LAYERDEPTH"][j], df_dz_diff = layer_data["LAYERDZ"][j],
                                         start_time=start, end_time=end, depth_start=D1, depth_end=D2, n=N, zero=False, ylim=Y,col_bar_label=var)

plt.title(f'{f_name[j]} - {f_name[i]}')

plt.show()


i = 0; var = "TCLAYER"; start='1902'; end='1903'; N=50; D1=0;D2=0.5; Z=False; Y=False;

fig = plt.figure()
ax = fig.add_subplot(121)

ref_interp_T = soil_contourbydepth(df = layer_data[var][i], df_depth = layer_data["LAYERDEPTH"][i], df_dz = layer_data["LAYERDZ"][i],
                                 start_time=start, end_time=end, depth_start=D1, depth_end=D2, n=N, zero=Z, ylim=Y,col_bar_label=var)
plt.title(f'{f_name[i]}')
ax = fig.add_subplot(122)

j = 1
unf_interp_T = soil_contourbydepth(df = layer_data[var][j], df_depth = layer_data["LAYERDEPTH"][j], df_dz = layer_data["LAYERDZ"][j],
                                 start_time=start, end_time=end, depth_start=D1, depth_end=D2, n=N, zero=Z, ylim=Y,col_bar_label=var)
plt.title(f'{f_name[j]}')
plt.subplots_adjust(left=None, bottom=None, right=1.75, top=1, wspace=None, hspace=None)
plt.show()

fig, ax = plt.subplots(1,1,figsize=(15, 5))
unfroz_interp = soil_contourbydepth_diff(df = layer_data[var][i], df_depth = layer_data["LAYERDEPTH"][i], df_dz = layer_data["LAYERDZ"][i],
                                         df_diff = layer_data[var][j], df_depth_diff = layer_data["LAYERDEPTH"][j], df_dz_diff = layer_data["LAYERDZ"][j],
                                         start_time=start, end_time=end, depth_start=D1, depth_end=D2, n=N, zero=Z, ylim=Y,col_bar_label=var)

plt.title(f'{f_name[j]} - {f_name[i]}')

plt.show()


i = 0; var = "LWCLAYER"; start='1902'; end='1903'; N=50; D1=0;D2=0.5; Z=False; Y=False;

fig = plt.figure()
ax = fig.add_subplot(121)

ref_interp_T = soil_contourbydepth(df = layer_data[var][i], df_depth = layer_data["LAYERDEPTH"][i], df_dz = layer_data["LAYERDZ"][i],
                                 start_time=start, end_time=end, depth_start=D1, depth_end=D2, n=N, zero=Z, ylim=Y,col_bar_label=var)
plt.title(f'{f_name[i]}')
ax = fig.add_subplot(122)

j = 1
unf_interp_T = soil_contourbydepth(df = layer_data[var][j], df_depth = layer_data["LAYERDEPTH"][j], df_dz = layer_data["LAYERDZ"][j],
                                 start_time=start, end_time=end, depth_start=D1, depth_end=D2, n=N, zero=Z, ylim=Y,col_bar_label=var)
plt.title(f'{f_name[j]}')
plt.subplots_adjust(left=None, bottom=None, right=1.75, top=1, wspace=None, hspace=None)
plt.show()

fig, ax = plt.subplots(1,1,figsize=(15, 5))
unfroz_interp = soil_contourbydepth_diff(df = layer_data[var][i], df_depth = layer_data["LAYERDEPTH"][i], df_dz = layer_data["LAYERDZ"][i],
                                         df_diff = layer_data[var][j], df_depth_diff = layer_data["LAYERDEPTH"][j], df_dz_diff = layer_data["LAYERDZ"][j],
                                         start_time=start, end_time=end, depth_start=D1, depth_end=D2, n=N, zero=Z, ylim=Y,col_bar_label=var)

plt.title(f'{f_name[j]} - {f_name[i]}')

plt.show()


i = 0; var = "IWCLAYER"; start='1902'; end='1903'; N=50; D1=0;D2=0.5; Z=False; Y=False;

fig = plt.figure()
ax = fig.add_subplot(121)

ref_interp_T = soil_contourbydepth(df = layer_data[var][i], df_depth = layer_data["LAYERDEPTH"][i], df_dz = layer_data["LAYERDZ"][i],
                                 start_time=start, end_time=end, depth_start=D1, depth_end=D2, n=N, zero=Z, ylim=Y,col_bar_label=var)
plt.title(f'{f_name[i]}')
ax = fig.add_subplot(122)

j = 1
unf_interp_T = soil_contourbydepth(df = layer_data[var][j], df_depth = layer_data["LAYERDEPTH"][j], df_dz = layer_data["LAYERDZ"][j],
                                 start_time=start, end_time=end, depth_start=D1, depth_end=D2, n=N, zero=Z, ylim=Y,col_bar_label=var)
plt.title(f'{f_name[j]}')
plt.subplots_adjust(left=None, bottom=None, right=1.75, top=1, wspace=None, hspace=None)
plt.show()

fig, ax = plt.subplots(1,1,figsize=(15, 5))
unfroz_interp = soil_contourbydepth_diff(df = layer_data[var][i], df_depth = layer_data["LAYERDEPTH"][i], df_dz = layer_data["LAYERDZ"][i],
                                         df_diff = layer_data[var][j], df_depth_diff = layer_data["LAYERDEPTH"][j], df_dz_diff = layer_data["LAYERDZ"][j],
                                         start_time=start, end_time=end, depth_start=D1, depth_end=D2, n=N, zero=Z, ylim=Y,col_bar_label=var)

plt.title(f'{f_name[j]} - {f_name[i]}')

plt.show()




































































# ALD = yearly["unfroz"]["ALD"]
# plt.plot(ALD, label='Model output')

# temp = layer_data["TLAYER"][1]
# depth = layer_data["LAYERDEPTH"][1]
# thick = layer_data["LAYERDZ"][1]

# # Final temperature based calculation of ALD
# interp_ald = []

# # looping through year index
# for year in ALD.index.year:
    
#     # setting df as a single year of data
#     T = temp.loc[str(year)]
#     z = depth.loc[str(year)]
#     dz = thick.loc[str(year)]
    
#     # list for storing one year of depths closest to zero degrees
#     year_depth = []
                
#     # looping and subsetting by month    
#     for month in T.index.month:
                
#         # subsetting by a single month
#         Tm = T.iloc[month - 1, :]
#         zm = z.iloc[month - 1, :] + (dz.iloc[month - 1, :]/2)
        
#         # appending the depth with closest to zero degrees for that month
#         if Tm[0]<=0.0:
#             year_depth.append(0.0)
            
#         elif Tm[0]>0.0:
#             for layer in Tm.index:
#                 if Tm[layer]<=0.0:
                    
#                     year_depth.append(np.interp(x=0.0, xp=[Tm[layer], Tm[layer-1]], fp=[zm[layer], zm[layer-1]]))
                    
#                     break
                    
# #                 print(year_depth)
# #                 print(ALD.loc[str(year)])
    
    
                    
            
#     interp_ald.append(max(year_depth))

# interp_ald = pd.DataFrame(index = ALD.index, data=interp_ald)

# plt.plot(interp_ald, label="Temperature interpolation")

# plt.xlabel("Year"); plt.ylabel("Active layer depth")

# plt.legend()


# xmin = pd.to_datetime("1901");  xmax = pd.to_datetime("1906")

# fig, ax = plt.subplots(1,2)

# ax[0].plot(layer_data["FRONTSDEPTH"][0][0][xmin:xmax].index, -layer_data["FRONTSDEPTH"][0][xmin:xmax].replace(-9999, np.nan))
# ax[0].plot(-yearly['ref'][xmin:xmax]['ALD'])

# # ax[1].plot(layer_data["FRONTSDEPTH"][0][0][xmin:xmax].index, -layer_data["FRONTSTYPE"][0][xmin:xmax].replace(-9999, np.nan))

# # ax[0].plot(layer_data["FRONTSDEPTH"][1][0][xmin:xmax].index, -layer_data["FRONTSDEPTH"][1][xmin:xmax].replace(-9999, np.nan))
# # ax[1].plot(layer_data["FRONTSDEPTH"][1][0][xmin:xmax].index, -layer_data["FRONTSTYPE"][1][xmin:xmax].replace(-9999, np.nan))

# ax[0].set_xlabel("Year", fontsize=12); ax[1].set_xlabel("Year", fontsize=12)
# ax[0].set_ylabel("Front depth", fontsize=12)
# ax[1].set_ylabel("Front type", fontsize=12)

# plt.subplots_adjust(left=None, bottom=None, right=1.5, top=1.2, wspace=None, hspace=None)

# plt.show()







