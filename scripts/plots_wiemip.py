"""
Plotting functions for WIEMIP outputs:

    map_plot : circumpolar heatmap with
               country outlines for a 
               given timestep.

    ts_plot  : timeseries plot summarized
               (mean, min, max, etc.) 
               across spatial domain.  

An additional input file (e.g. run-mask.nc) is 
required to provide geospatial information (e.g.
lat, lon, projection, etc) and mask pixels which
were not run.

Requirements: xarray, matplotlib, cartopy
    pip install xarray cartopy matplotlib
"""

import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import argparse

from pathlib import Path

# example input variables
# output_file_path="/Users/BenMaglio/Downloads/SOC_yearly_tr_unitsconverted_summed.nc"
# runmask_file_path="/Users/BenMaglio/Downloads/teminputs-new-run-mask2.nc"
# variable_name='SOC'
# time_string='1850-01-01'

def ts_plot(output_file_path, runmask_file_path, variable_name,
            plot_dir, preview=False, save=True, label=''):

    flux_list = ['BURNC2AIR','fFire','BURNSOIL2AIRC','fFireCsoil',
                             'BURNVEG2AIRC', 'fFireCveg','CH4EFFLUXTOT','wetCH4',
                             'EET','evapotrans','GPP','gpp','GPPMINUSNPP','ra',
                             'LFTOTC','fVegLitter','NETNMIN','fNnetmin','NPP','npp',
                             'NUPTAKETOT','fNup','RHSOM','rh','TRANSPIRATION','tveg',
                             'LFNVC', 'LFVC', 'NLOST', 'NUPTAKELAB','NUPTAKEST', 
                             'QRUNOFF']
    
    stock_list = ['AVLN','nInorgSoil','DWDC','cCwd','ORGN',
                               'nOrgSoil','SOC','cSoil','SOC0_100cm','cSoilAbove1m',
                               'SOCBELOW1M','cSoilBelow1m','SOILPOOLSSUMMED','cSoilPools',
                               'VEGC','cVeg','VEGNTOT','nVeg','VWCLAYER', 
                               'mrsoLayer','VWCTOT','mrso','SOMA', 'SOMCR', 
                               'SOMPR', 'SOMRAWC']
    
    misc_list = ['LAI','lai','SNOWFALL','snowf','SNOWTHICK','snowDepth',
                               'TLAYER','soilT','SWE','swe','WATERTAB','wtd']

    flux_method = lambda x: x.mean(dim=["x", "y"])
    stock_method = lambda x: x.sum(dim=["x", "y"])

    if plot_dir:
      OUTPUT_PNG = f'{str(plot_dir)}/label_{variable_name}_ts_plot.png'
    else:
      OUTPUT_PNG = 'ts_plot.png'

    output_var_ds = xr.open_dataset(output_file_path, decode_times=True)
    units = output_var_ds[variable_name].attrs['units']
    input_ds = xr.open_dataset(runmask_file_path)

    da = output_var_ds[variable_name]

    if 'pft' in da.dims:
        da = da.sum(dim='pft', skipna=True)
    if 'layer' in da.dims:
        da = da.isel('layer'==0)

    da = da.squeeze()
    # mask out pixels which were not run
    da = da.where(input_ds['run'].values != 0)

    # check if data is monthly or yearly
    dt = da.time.diff('time')
    is_monthly = (dt >= np.timedelta64(28, "D")) & (
        dt <= np.timedelta64(31, "D")
    )    

    all_monthly = bool(is_monthly.all())

    if all_monthly: 
       if variable_name in flux_list:
           da = flux_method(da)
           da = da.resample(time='YS').sum()
       elif variable_name in stock_list:
           da = stock_method(da) 
           da = da.resample(time='YS').mean()

       elif variable_name in misc_list:
           da = flux_method(da) 
           da = da.resample(time='YS').mean()
           
       else:
           print("Variable name may need to be added to yearly sum / mean calculations")
    if not all_monthly:
       if variable_name in flux_list:
           da = flux_method(da)
   
       elif variable_name in stock_list:
           da = stock_method(da) 
   
       elif variable_name in misc_list:
           da = flux_method(da) 
           
       else:
           print("Variable name may have additional dimensions which need handling...")
       

    if variable_name in ['LAYERDZ']:
       print("Skipping LAYERDZ for plotting...")
    else:
        fig, ax = plt.subplots(figsize=(9,9))
        ax.plot(da.indexes['time'].to_datetimeindex(unsafe=True, time_unit='s'), da.values)
        ax.set_ylabel(variable_name+f" [{units}]")
        ax.set_xlabel('Time [years]')

        if label!='':
            ax.set_title(label)

        plt.tight_layout()

        if save:
            plt.savefig(OUTPUT_PNG, dpi=200, bbox_inches="tight")
        if preview:
            plt.show()
    return fig

def map_plot(output_file_path, runmask_file_path, variable_name, time_string,
             plot_dir, preview=False, save=True, label=''):
    MAP_OUTPUT_PATH = f'{variable_name}_{time_string}_map.png'
    MAP_PROJECTION = "north_polar"
    NORTH_POLAR_MIN_LAT = None

    if plot_dir:
      OUTPUT_PNG = f'{str(plot_dir)}/label_{variable_name}_{time_string}_map.png'
    else:
      OUTPUT_PNG = 'map_plot.png'

    output_var_ds = xr.open_dataset(output_file_path)
    units = output_var_ds[variable_name].attrs['units']
    input_ds = xr.open_dataset(runmask_file_path)

    da = output_var_ds[variable_name].sel(time=time_string)

    if 'pft' in da.dims:
        da = da.sum(dim='pft', skipna=True)
        print("Summing across PFTs for mapped result...")
    if 'layer' in da.dims:
#        da = da.sel('layer'==0)
      da = da[:,0,:,:]

    da = da.squeeze()

    # mask out pixels which were not run
    da = da.where(input_ds['run'].values != 0)

    lat = input_ds['lat']
    lon = input_ds['lon']

    lat2d = lat.values.astype(float)
    lon2d = lon.values.astype(float)

    # ---- Plot ------------------------------------------------------------
    central_lon = float(np.nanmedian(lon2d))
    lon_min, lon_max = np.nanmin(lon2d), np.nanmax(lon2d)
    lat_min, lat_max = np.nanmin(lat2d), np.nanmax(lat2d)
    pad_lon = 0#max((lon_max - lon_min) * 0.05, 0.5)
    pad_lat = 0#max((lat_max - lat_min) * 0.05, 0.5)

    fig = plt.figure(figsize=(9, 9) if MAP_PROJECTION == "north_polar" else (12, 7))

    proj = ccrs.NorthPolarStereo(central_longitude=central_lon)
    ax = plt.axes(projection=proj)

    min_lat = NORTH_POLAR_MIN_LAT if NORTH_POLAR_MIN_LAT is not None else max(
        lat_min - pad_lat, -90
    )
    ax.set_extent([-180, 180, 45, 90], crs=ccrs.PlateCarree())

    # Clip the axes to a circle so it renders as a proper polar view
    # instead of a square with the pole tucked in a corner.
    theta = np.linspace(0, 2 * np.pi, 100)
    center, radius = [0.5, 0.5], 0.5
    verts = np.vstack([np.sin(theta), np.cos(theta)]).T
    circle = mpath.Path(verts * radius + center)
    ax.set_boundary(circle, transform=ax.transAxes)

    gl = ax.gridlines(draw_labels=True, linewidth=0.3, alpha=0.5)

    mesh = ax.pcolormesh(
        lon2d,
        lat2d,
        da.values,
        transform=ccrs.PlateCarree(),  # data itself is always plain lat/lon
        cmap="viridis",
        shading="auto",
    )

    # 10m resolution lines up much better than the 110m default for
    # regional/high-latitude grids.
    ax.add_feature(cfeature.BORDERS.with_scale("10m"), linewidth=0.6, edgecolor="black")
    ax.add_feature(cfeature.COASTLINE.with_scale("10m"), linewidth=0.6)

    cbar = plt.colorbar(mesh, ax=ax, orientation="vertical", pad=0.03, shrink=0.8)
    cbar.set_label(variable_name+f" {' [' + units + ']' if units else ''}")

    if label!='':
       ax.set_title(label+' - '+time_string)
    else:
       ax.set_title(time_string)
       

    plt.tight_layout()
    if save:
        plt.savefig(OUTPUT_PNG, dpi=200, bbox_inches="tight")
    if preview:
        plt.show()

    return fig

def main(output_file_path, runmask_file_path, variable_name, time_string, plot_dir, preview=True, save=False, label=''):
   
   map_plot(output_file_path, runmask_file_path, variable_name, time_string, plot_dir, preview=preview, save=save, label=label)
   ts_plot(output_file_path, runmask_file_path, variable_name, plot_dir, preview=preview, save=save, label=label)

# CLI
if __name__ == "__main__":
   parser = argparse.ArgumentParser(description="Plot map or timeseries of WIEMIP output. \n " \
   "E.g python plots_wiemip.py /Users/BenMaglio/Downloads/SOC_yearly_tr_unitsconverted_summed.nc --runmask /Users/BenMaglio/Downloads/teminputs-new-run-mask2.nc --variable SOC --time 1850-01-01 --outdir ./ --preview True --save False --label Test_label")
   parser.add_argument("output_file_path", type=str, help="Path to file for plotting.")

   parser.add_argument("--runmask", type=str, help="Path to runmask used for masking out un-run pixels.")
   parser.add_argument("--variable", type=str, help="Name of variable for plotting (e.g. GPP).")
   parser.add_argument("--time", type=str, help="Time string used for map plot at fixed temporal step")
   parser.add_argument("--outdir", type=str, help="Directory path to output .png files.")
   parser.add_argument("--preview", type=bool, help="True/False as to whether to preview plot.")
   parser.add_argument("--save", type=bool, help="True/False as to whether to save plot.")
   parser.add_argument("--label", type=str, help="Label added to plot file name and title.")
   args = parser.parse_args()

   main(args.output_file_path, args.runmask, args.variable, args.time, args.outdir, preview=args.preview, save=args.save, label=args.label)