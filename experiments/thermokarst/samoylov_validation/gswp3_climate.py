"""Build Samoylov TEM monthly climate from GSWP3 + Boike bias correction.

Follows Bender et al. (2026) §2.3:
  1. Extract GSWP3 at the Samoylov grid point (or CRU proxy when GSWP3 absent).
  2. Daily-mean T anomaly (obs − reanalysis) by day-of-year for 2002–2014.
  3. Apply DOY anomaly to all years.
  4. Adjust precipitation (summer liquid bias, winter −25 %, target 236 mm yr⁻¹).

Output: TEM-compatible NetCDF with monthly ``tair``, ``precip``, ``nirr``,
``vapor_press`` on ``(time, Y, X)``.
"""
from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

SAMOYLOV_LAT = 72.3667   # 72°22′N
SAMOYLOV_LON = 126.4667  # 126°28′E
CAL_START = 2002
CAL_END = 2014
TR_START = 1901
TR_YEARS = 114
TARGET_ANNUAL_PRECIP_MM = 236.0
WINTER_MONTHS = (12, 1, 2)  # DJF calendar months
SUMMER_MONTHS = (6, 7, 8)   # JJA liquid bias window
DINM = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

# GSWP3 / CLM forcing aliases → TEM names
TAIR_ALIASES = ("tair", "TBOT", "temp", "tas", "air_temperature")
PRECIP_ALIASES = ("precip", "RAIN", "pr", "precipitation")
NIRR_ALIASES = ("nirr", "FSDS", "swdown", "rsds", "shortwave")


@dataclass
class BuildReport:
    source: str
    gswp3_path: str | None
    boike_path: str
    template_path: str
    output_path: str
    start_year: int
    nyears: int
    calibration_years: tuple[int, int]
    mean_annual_precip_mm: float
    mean_annual_tair_C: float
    doy_anomaly_range_C: tuple[float, float]
    precip_scale_factor: float
    notes: list[str]

    def to_dict(self):
        return asdict(self)


def to_celsius(series):
    """Convert Kelvin monthly temperatures to Celsius when needed."""
    values = np.asarray(series, float)
    if np.nanmedian(values) > 150.0:
        return values - 273.15
    return values


def _pick_variable(dataset, aliases):
    for name in aliases:
        if name in dataset.variables:
            return name
    raise KeyError(f"none of {aliases} found in {list(dataset.variables)}")


def _normalize_lon(lon, lon_array):
    lon_array = np.asarray(lon_array, float)
    if lon_array.min() >= 0 and lon < 0:
        lon = lon + 360.0
    if lon_array.max() <= 180 and lon > 180:
        lon = lon - 360.0
    return lon


def nearest_grid(lat, lon, lats, lons):
    lats = np.asarray(lats, float)
    lons = np.asarray(lons, float)
    lon = _normalize_lon(lon, lons)
    if lats.ndim == 1 and lons.ndim == 1:
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        dist = (lat_grid - lat) ** 2 + (lon_grid - lon) ** 2
        return np.unravel_index(int(np.argmin(dist)), dist.shape)
    dist = (lats - lat) ** 2 + (lons - lon) ** 2
    return np.unravel_index(int(np.argmin(dist)), dist.shape)


def read_monthly_series(path, lat=SAMOYLOV_LAT, lon=SAMOYLOV_LON, y=0, x=0):
    """Read monthly tair/precip/nirr from a TEM or lat/lon NetCDF."""
    with Dataset(path) as src:
        if "Y" in src.dimensions and "X" in src.dimensions:
            tair = to_celsius(src[_pick_variable(src, TAIR_ALIASES)][:, y, x])
            precip = np.asarray(src[_pick_variable(src, PRECIP_ALIASES)][:, y, x], float)
            nirr_name = _pick_variable(src, NIRR_ALIASES) if any(
                a in src.variables for a in NIRR_ALIASES) else None
            nirr = np.asarray(src[nirr_name][:, y, x], float) if nirr_name else None
            return tair, precip, nirr

        lat_name = next((n for n in ("lat", "latitude", "LAT") if n in src.variables), None)
        lon_name = next((n for n in ("lon", "longitude", "LON") if n in src.variables), None)
        if lat_name is None or lon_name is None:
            raise ValueError(f"{path} has no Y/X or lat/lon coordinates")
        lats = np.asarray(src[lat_name][:], float)
        lons = np.asarray(src[lon_name][:], float)
        j, i = nearest_grid(lat, lon, lats, lons)
        tair = to_celsius(src[_pick_variable(src, TAIR_ALIASES)][:, j, i])
        precip = np.asarray(src[_pick_variable(src, PRECIP_ALIASES)][:, j, i], float)
        nirr_name = next((a for a in NIRR_ALIASES if a in src.variables), None)
        nirr = np.asarray(src[nirr_name][:, j, i], float) if nirr_name else None
        return tair, precip, nirr


def monthly_to_daily(monthly):
    """Piecewise-constant daily series from monthly values (365-day calendar)."""
    nyears = len(monthly) // 12
    daily = np.zeros(nyears * 365, float)
    for year in range(nyears):
        for month in range(12):
            idx = year * 12 + month
            start = year * 365 + sum(DINM[:month])
            daily[start:start + DINM[month]] = monthly[idx]
    return daily


def daily_to_monthly(daily, start_year=1901):
    """Aggregate daily series to monthly means (tair/nirr) or sums (precip)."""
    nyears = len(daily) // 365
    monthly = np.zeros(nyears * 12, float)
    for year in range(nyears):
        for month in range(12):
            start = year * 365 + sum(DINM[:month])
            chunk = daily[start:start + DINM[month]]
            monthly[year * 12 + month] = float(np.nanmean(chunk))
    return monthly


def daily_precip_to_monthly(daily):
    nyears = len(daily) // 365
    monthly = np.zeros(nyears * 12, float)
    for year in range(nyears):
        for month in range(12):
            start = year * 365 + sum(DINM[:month])
            monthly[year * 12 + month] = float(np.nansum(daily[start:start + DINM[month]]))
    return monthly


def load_boike_monthly(path):
    """Load Boike monthly calibration table (year, month, tair_C, precip_mm)."""
    rows = list(csv.DictReader(path.open()))
    by_key = {}
    for row in rows:
        year = int(row["year"])
        month = int(row["month"])
        by_key[(year, month)] = (
            float(row["tair_C"]),
            float(row.get("precip_mm", row.get("precip", "nan"))),
        )
    return by_key


def load_boike_daily(path):
    """Load Boike daily table (year, month, day, doy, tair_C, precip_mm)."""
    rows = list(csv.DictReader(path.open()))
    by_doy_year = {}
    years = set()
    for row in rows:
        year = int(row["year"])
        doy = int(row["doy"])
        years.add(year)
        by_doy_year[(year, doy)] = (
            float(row["tair_C"]),
            float(row.get("precip_mm", row.get("precip", "0"))),
        )
    return by_doy_year, min(years), max(years)


def boike_daily_to_series(by_doy_year, start_year, end_year):
    """Flatten daily Boike records to consecutive 365-day blocks per year."""
    tair = []
    precip = []
    for year in range(start_year, end_year + 1):
        for doy in range(1, 366):
            key = (year, doy)
            if key in by_doy_year:
                t, p = by_doy_year[key]
            else:
                t, p = float("nan"), 0.0
            tair.append(t)
            precip.append(p)
    return np.asarray(tair, float), np.asarray(precip, float)


def calibration_window(boike_path):
    """Infer calibration years from Boike monthly or daily CSV."""
    daily_path = boike_path.with_name(boike_path.name.replace("monthly", "daily"))
    if not daily_path.exists():
        daily_path = boike_path.with_name(
            boike_path.name.replace("monthly", "daily").replace("_2002-2014", "_2002-2011"))
    if daily_path.exists():
        _, y0, y1 = load_boike_daily(daily_path)
        return y0, y1, daily_path
    by_key = load_boike_monthly(boike_path)
    years = sorted({y for y, _ in by_key})
    return years[0], years[-1], None


def expand_boike_to_daily(by_key, start_year=CAL_START, end_year=CAL_END):
    """Expand monthly Boike table to a daily T series for calibration window."""
    days = []
    tair = []
    precip = []
    for year in range(start_year, end_year + 1):
        for month in range(12):
            if (year, month + 1) not in by_key:
                continue
            t, p = by_key[(year, month + 1)]
            nd = DINM[month]
            days.extend(range(len(tair), len(tair) + nd))
            tair.extend([t] * nd)
            precip.extend([p / nd] * nd)
    return np.asarray(tair, float), np.asarray(precip, float)


def doy_anomalies(obs_daily, model_daily):
    """Mean (obs − model) by day-of-year across calibration period."""
    n_years = len(obs_daily) // 365
    anomaly = np.zeros(365, float)
    counts = np.zeros(365, int)
    for year in range(n_years):
        for doy in range(365):
            obs = obs_daily[year * 365 + doy]
            mod = model_daily[year * 365 + doy]
            if np.isfinite(obs) and np.isfinite(mod):
                anomaly[doy] += obs - mod
                counts[doy] += 1
    good = counts > 0
    anomaly[good] /= counts[good]
    if np.any(~good):
        anomaly[~good] = float(np.nanmean(anomaly[good]))
    return anomaly


def apply_doy_anomaly(daily, anomaly):
    corrected = daily.copy()
    nyears = len(daily) // 365
    for year in range(nyears):
        for doy in range(365):
            corrected[year * 365 + doy] += anomaly[doy]
    return corrected


def adjust_precip_monthly(precip, summer_scale=1.0, winter_scale=0.75,
                          target_annual=TARGET_ANNUAL_PRECIP_MM):
    """Apply seasonal precipitation adjustments and rescale to target annual total."""
    out = precip.copy()
    nyears = len(out) // 12
    for year in range(nyears):
        for month in range(12):
            cal_month = month + 1
            idx = year * 12 + month
            if cal_month in SUMMER_MONTHS:
                out[idx] *= summer_scale
            if cal_month in WINTER_MONTHS:
                out[idx] *= winter_scale
    current = float(out.reshape(nyears, 12).sum(axis=1).mean())
    scale = target_annual / current if current > 0 else 1.0
    out *= scale
    return out, scale


def estimate_summer_liquid_bias(obs_by_key, model_monthly, cal_start=CAL_START, cal_end=CAL_END):
    """Ratio obs/model mean summer liquid precip during calibration years."""
    obs_sum = []
    mod_sum = []
    for year in range(cal_start, cal_end + 1):
        for month in SUMMER_MONTHS:
            key = (year, month)
            if key not in obs_by_key:
                continue
            obs_sum.append(obs_by_key[key][1])
            midx = (year - TR_START) * 12 + (month - 1)
            if 0 <= midx < len(model_monthly):
                mod_sum.append(model_monthly[midx])
    if not obs_sum or not mod_sum or float(np.mean(mod_sum)) <= 0:
        return 1.0
    return float(np.mean(obs_sum) / np.mean(mod_sum))


def write_tem_climate(template, dest, tair, precip, nirr, vapor=100.0, y=0, x=0):
    """Write monthly arrays into a TEM climate NetCDF copied from template."""
    shutil.copy2(template, dest)
    nmonths = len(tair)
    with Dataset(dest, "r+") as dst:
        for name in ("tair", "precip", "nirr", "vapor_press"):
            if name not in dst.variables:
                continue
            shape = list(dst[name].shape)
            shape[0] = nmonths
            data = np.zeros(shape, dtype=np.float64)
            if name == "tair":
                values = tair
            elif name == "precip":
                values = precip
            elif name == "nirr":
                values = nirr if nirr is not None else np.zeros(nmonths)
            else:
                values = np.full(nmonths, vapor)
            for t in range(nmonths):
                data[t, y, x] = values[t]
            dst[name][:] = data
    return dest


def slice_years(template, dest, start_year, nyears, y=0, x=0):
    """Extract ``nyears`` calendar years beginning at ``start_year`` (origin 1901)."""
    start_idx = (start_year - TR_START) * 12
    tair, precip, nirr = read_monthly_series(template, y=y, x=x)
    end_idx = start_idx + nyears * 12
    return (
        tair[start_idx:end_idx],
        precip[start_idx:end_idx],
        nirr[start_idx:end_idx] if nirr is not None else None,
    )


def build_samoylov_climate(
    template,
    output,
    *,
    gswp3_path=None,
    boike_path=None,
    cru_proxy_path=None,
    start_year=TR_START,
    nyears=TR_YEARS,
    cal_start=CAL_START,
    cal_end=CAL_END,
):
    """Build bias-corrected Samoylov climate file.

    If ``gswp3_path`` is None, ``cru_proxy_path`` (default: template) stands in
    for GSWP3 until real forcing is supplied.
    """
    template = Path(template)
    output = Path(output)
    boike_path = Path(boike_path) if boike_path else None
    notes = []

    reanalysis_path = Path(gswp3_path) if gswp3_path else Path(cru_proxy_path or template)
    source_label = "gswp3_boike" if gswp3_path else "cru_proxy_boike"
    if gswp3_path:
        notes.append(f"GSWP3 forcing: {gswp3_path}")
    else:
        notes.append(f"GSWP3 absent; CRU/proxy reanalysis: {reanalysis_path}")

    tair, precip, nirr = read_monthly_series(reanalysis_path)
    if len(tair) < (start_year - TR_START + nyears) * 12:
        raise ValueError(
            f"reanalysis has {len(tair)//12} years; need {start_year - TR_START + nyears}")

    tair = tair[(start_year - TR_START) * 12:(start_year - TR_START + nyears) * 12]
    precip = precip[(start_year - TR_START) * 12:(start_year - TR_START + nyears) * 12]
    if nirr is not None:
        nirr = nirr[(start_year - TR_START) * 12:(start_year - TR_START + nyears) * 12]
    else:
        nirr = np.clip(400.0 * np.maximum(0.0, np.sin(np.linspace(0, nyears * 2 * np.pi, nyears * 12) + np.pi / 2)), 0, 400)
        notes.append("nirr missing in reanalysis; filled with sinusoidal polar curve")

    if boike_path and boike_path.exists():
        cal_start, cal_end, daily_path = calibration_window(boike_path)
        boike = load_boike_monthly(boike_path)
        if daily_path and daily_path.exists():
            by_doy, _, _ = load_boike_daily(daily_path)
            obs_daily, _ = boike_daily_to_series(by_doy, cal_start, cal_end)
            notes.append(f"Boike daily DOY calibration ({daily_path.name}, {cal_start}-{cal_end})")
        else:
            obs_daily, _ = expand_boike_to_daily(boike, cal_start, cal_end)
            notes.append(f"Boike monthly calibration ({boike_path.name}, {cal_start}-{cal_end})")
        cal_offset = (cal_start - start_year) * 365
        cal_len = (cal_end - cal_start + 1) * 365
        model_daily = monthly_to_daily(tair)
        if cal_offset >= 0 and cal_offset + cal_len <= len(model_daily):
            n_years = (cal_end - cal_start + 1)
            obs_block = obs_daily[:n_years * 365]
            mod_block = model_daily[cal_offset:cal_offset + n_years * 365]
            anomaly = doy_anomalies(obs_block, mod_block)
            corrected_daily = apply_doy_anomaly(model_daily, anomaly)
            tair = daily_to_monthly(corrected_daily)
            doy_range = (float(np.nanmin(anomaly)), float(np.nanmax(anomaly)))
        else:
            anomaly = np.zeros(365)
            doy_range = (0.0, 0.0)
            notes.append("calibration window outside climate span; skipped T anomaly")
        summer_scale = estimate_summer_liquid_bias(boike, precip, cal_start, cal_end)
        notes.append(f"summer liquid precip scale={summer_scale:.3f}")
    else:
        anomaly = np.zeros(365)
        doy_range = (0.0, 0.0)
        summer_scale = 1.0
        notes.append("Boike calibration CSV missing; precipitation bias correction only")

    precip, precip_scale = adjust_precip_monthly(
        precip, summer_scale=summer_scale, winter_scale=0.75,
        target_annual=TARGET_ANNUAL_PRECIP_MM)

    write_tem_climate(template, output, tair, precip, nirr)

    report = BuildReport(
        source=source_label,
        gswp3_path=str(gswp3_path) if gswp3_path else None,
        boike_path=str(boike_path) if boike_path else "",
        template_path=str(template),
        output_path=str(output),
        start_year=start_year,
        nyears=nyears,
        calibration_years=(cal_start, cal_end),
        mean_annual_precip_mm=float(precip.reshape(nyears, 12).sum(axis=1).mean()),
        mean_annual_tair_C=float(tair.reshape(nyears, 12).mean(axis=1).mean()),
        doy_anomaly_range_C=doy_range,
        precip_scale_factor=float(precip_scale),
        notes=notes,
    )
    report_path = output.with_suffix(".build-report.json")
    report_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n")
    return report
