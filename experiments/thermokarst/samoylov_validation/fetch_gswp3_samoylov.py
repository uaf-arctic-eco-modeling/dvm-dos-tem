#!/usr/bin/env python3
"""Download GSWP3-W5E5 monthly fields and extract Samoylov grid point."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.request
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
sys.path.insert(0, str(PKG))
from gswp3_climate import (  # noqa: E402
    SAMOYLOV_LAT,
    SAMOYLOV_LON,
    nearest_grid,
    to_celsius,
    write_tem_climate,
    _pick_variable,
    TAIR_ALIASES,
    PRECIP_ALIASES,
)

CACHE = PKG / "data/cache"
DATA = PKG / "data"
DEFAULT_TEMPLATE = ROOT / "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/historic-climate.nc"

GSWP3_BASE = "https://cluster.klima.uni-bremen.de/~lschuster/isimip3a/_old_to_remove/monthly"
REMOTE = {
    "tas": "gswp3-w5e5_obsclim_tas_global_monthly_1901_2019.nc",
    "pr": "gswp3-w5e5_obsclim_pr_global_monthly_1901_2019.nc",
}
CACHE_NAMES = {
    "tas": "gswp3_tas_global_monthly_1901_2019.nc",
    "pr": "gswp3_pr_global_monthly_1901_2019.nc",
}
ALIASES = {"tas": TAIR_ALIASES, "pr": PRECIP_ALIASES}
DINM = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"Using cached {dest}", file=sys.stderr)
        return dest
    print(f"Downloading {url}", file=sys.stderr)
    tmp = dest.with_suffix(".part")
    req = urllib.request.Request(url, headers={"User-Agent": "TEM-samoylov-validation/1.0"})
    with urllib.request.urlopen(req, timeout=3600) as response, tmp.open("wb") as stream:
        shutil.copyfileobj(response, stream)
    tmp.rename(dest)
    return dest


def extract_point_series(global_path, var_aliases, lat, lon):
    """Lazy-read nearest grid-cell time series from a global lat/lon NetCDF."""
    with Dataset(global_path) as src:
        lat_name = next(n for n in ("lat", "latitude") if n in src.variables)
        lon_name = next(n for n in ("lon", "longitude") if n in src.variables)
        lats = np.asarray(src[lat_name][:], float)
        lons = np.asarray(src[lon_name][:], float)
        j, i = nearest_grid(lat, lon, lats, lons)
        vname = _pick_variable(src, var_aliases)
        series = to_celsius(src[vname][:, j, i])
        actual_lat = float(lats[j] if lats.ndim == 1 else lats.flat[j])
        actual_lon = float(lons[i] if lons.ndim == 1 else lons.flat[i])
    return series, actual_lat, actual_lon, vname


def pr_to_mm_month(series):
    """Convert GSWP3-W5E5 monthly pr (kg m-2 s-1) to mm month-1."""
    out = np.zeros_like(series)
    for idx, value in enumerate(series):
        ndays = DINM[idx % 12]
        out[idx] = float(value) * ndays * 86400.0
    return out


def build_point_climate(tas, pr, template, dest):
    """Write TEM climate from GSWP3 point tas/pr; nirr from CRU template."""
    n = min(len(tas), len(pr), 114 * 12)
    tair = tas[:n]
    precip = pr_to_mm_month(pr[:n])
    with Dataset(template) as src:
        nirr = np.asarray(src["nirr"][:n, 0, 0], float)
    write_tem_climate(template, dest, tair, precip, nirr)
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=CACHE)
    parser.add_argument("--output", type=Path, default=DATA / "gswp3_samoylov_point.nc")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--lat", type=float, default=SAMOYLOV_LAT)
    parser.add_argument("--lon", type=float, default=SAMOYLOV_LON)
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()

    tas_global = args.cache_dir / CACHE_NAMES["tas"]
    pr_global = args.cache_dir / CACHE_NAMES["pr"]
    if not args.skip_download:
        download(f"{GSWP3_BASE}/{REMOTE['tas']}", tas_global)
        download(f"{GSWP3_BASE}/{REMOTE['pr']}", pr_global)

    tas, tas_lat, tas_lon, tas_var = extract_point_series(
        tas_global, ALIASES["tas"], args.lat, args.lon)
    pr, pr_lat, pr_lon, pr_var = extract_point_series(
        pr_global, ALIASES["pr"], args.lat, args.lon)

    build_point_climate(tas, pr, args.template, args.output)

    report = {
        "lat_requested": args.lat,
        "lon_requested": args.lon,
        "grid_tas": {"lat": tas_lat, "lon": tas_lon, "variable": tas_var},
        "grid_pr": {"lat": pr_lat, "lon": pr_lon, "variable": pr_var},
        "tas_global": str(tas_global),
        "pr_global": str(pr_global),
        "output": str(args.output),
        "nmonths": int(min(len(tas), len(pr))),
        "source": "GSWP3-W5E5 ISIMIP3a obsclim monthly 1901-2019",
    }
    args.output.with_suffix(".fetch-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
