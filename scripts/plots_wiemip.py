"""
Plotting functions for WIEMIP outputs:

    map_plot : circumpolar heatmap with
               country outlines for a 
               given timestep.

    ts_plot  : timeseries plot summarized
               (mean, min, max, etc.) 
               across spatial domain.  

An additional input file (e.g. run-mask.nc) is 
required to provide geopspatial information (e.g.
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

# example input variables
output_file_path="/Users/BenMaglio/Downloads/GPP_monthly_tr.nc"
runmask_file_path="/Users/BenMaglio/Downloads/teminputs-new-run-mask2.nc"
variable_name='gpp'
time_string='1850-08-01'
method = lambda x: x.mean(dim=["x", "y"])

def ts_plot(output_file_path, runmask_file_path, variable_name, method):
    OUTPUT_PNG = 'ts_plot.png'

    output_var_ds = xr.open_dataset(output_file_path)
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
    da = method(da)

    # check if data is monthly or yearly
    dt = da.time.diff('time')
    is_monthly = (dt >= np.timedelta64(28, "D")) & (
        dt <= np.timedelta64(31, "D")
    )
    all_monthly = bool(is_monthly.all())
    if all_monthly:
        da = da.resample(time='YS').sum()
        print('NEED TO ADD CATCH FOR SUM/MEAN FOR FLUX/STOCK')

    fig, ax = plt.subplots(figsize=(9,9))
    ax.plot(da.indexes['time'].to_datetimeindex(), da.values)
    ax.set_ylabel(variable_name+f" [{units}]")
    ax.set_xlabel('Time [years]')
    
    plt.show()

    return

def map_plot(output_file_path, runmask_file_path, variable_name, time_string):
    MAP_OUTPUT_PATH = f'{variable_name}_{time_string}_map.png'
    MAP_PROJECTION = "north_polar"
    NORTH_POLAR_MIN_LAT = None
    OUTPUT_PNG = 'map_plot.png'

    output_var_ds = xr.open_dataset(output_file_path)
    units = output_var_ds[variable_name].attrs['units']
    input_ds = xr.open_dataset(runmask_file_path)

    da = output_var_ds[variable_name].sel(time=time_string)
    
    if 'pft' in da.dims:
        da = da.sum(dim='pft', skipna=True)
    if 'layer' in da.dims:
        da = da.isel('layer'==0)

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

    ax.set_title(time_string)

    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=200, bbox_inches="tight")
    print(f"\nSaved plot to {OUTPUT_PNG}")
    plt.show()

    return

# map_plot(output_file_path, runmask_file_path, 'GPP', '1850-08-01')
ts_plot(output_file_path, runmask_file_path, 'GPP', method)