#!/usr/bin/env python3
"""Anaktuvuk River fire validation — Phase 0 pipeline and Phase 1 Jones et al. window."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parent / "anaktuvuk_validation"
OBS_DIR = PKG / "obs"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "build/matplotlib-cache"))
saved = os.environ.get("PATH", "")
if sys.platform == "darwin":
    os.environ["PATH"] = os.pathsep.join(
        x for x in saved.split(os.pathsep) if x not in ("/usr/sbin", "/sbin"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
os.environ["PATH"] = saved

import production_validation as production
import bgc_coupling_validation as bgc
import fire_topology_validation as fire_topo

_nsc_spec = importlib.util.spec_from_file_location(
    "north_slope_climate", PKG / "north_slope_climate.py")
_nsc = importlib.util.module_from_spec(_nsc_spec)
sys.modules[_nsc_spec.name] = _nsc
_nsc_spec.loader.exec_module(_nsc)

_dplots_spec = importlib.util.spec_from_file_location(
    "anaktuvuk_diagnostic_plots", PKG / "diagnostic_plots.py")
_dplots = importlib.util.module_from_spec(_dplots_spec)
sys.modules[_dplots_spec.name] = _dplots
_dplots_spec.loader.exec_module(_dplots)

CELLS = [(0, 0), (0, 1)]
ROLES = ["burned", "control"]
CMT = 5
BURNED_CELL = (0, 0)
CONTROL_CELL = (0, 1)
FIRE_YEAR = 0
SPLIT = 7
PRIMARY_START = 2
PRIMARY_END = 7
STAB_START = 8
STAB_END = 14
DINM = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
INK = "#171717"
TEAL = "#1F6F5F"
BLUE = "#4C78A8"
ORANGE = "#D55E00"
MUTED = "#777772"
GRID = "#E4E7E5"

PHASE0_OUT = ROOT / "experiments/thermokarst/anaktuvuk_validation_results"
PHASE1_OUT = ROOT / "experiments/thermokarst/anaktuvuk_phase1_validation_results"
MAX_ORGANIC_BURN_OUT = ROOT / "experiments/thermokarst/anaktuvuk_max_organic_burn_results"

PHASE0_TR_YEARS = 15
PHASE0_EQ_YEARS = 5
PHASE0_FIRE_JDAY = 180
PHASE0_ICE_TOP = 0.15
PHASE0_ICE_BOTTOM = 0.90
PHASE0_ICE_FRACTION = 0.32

PHASE1_TR_YEARS = 15
PHASE1_EQ_YEARS = 30
PHASE1_TR_START = 106
ORGANIC_LAYER_START = 2000
ORGANIC_LAYER_END = 2023
SPINUP_OUT = ROOT / "experiments/thermokarst/anaktuvuk_spinup_results"
SPINUP_PR_YEARS = 100
SPINUP_EQ_YEARS = 1000
SPINUP_SP_YEARS = 100
TRANSIENT_SP_YEARS = 20
TRANSIENT_TR_YEARS = 24
TRANSIENT_TR_CALENDAR_START = 2000
TRANSIENT_FIRE_TR_YEAR = 2007 - TRANSIENT_TR_CALENDAR_START
TRANSIENT_PRIMARY_START = 2009 - TRANSIENT_TR_CALENDAR_START
TRANSIENT_PRIMARY_END = 2014 - TRANSIENT_TR_CALENDAR_START
TRANSIENT_STAB_START = 2014 - TRANSIENT_TR_CALENDAR_START
TRANSIENT_STAB_END = 2021 - TRANSIENT_TR_CALENDAR_START
TRANSIENT_VALIDATION_END = 2021 - TRANSIENT_TR_CALENDAR_START
TRANSIENT_RESTART_SPLIT = 7
TK_RESTART_VERSION = 3
TK_STATE_COUNT = 18
SPINUP_THERMOKARST = False
PHASE1_FIRE_JDAY = 240
PHASE1_ICE_TOP = 0.30
PHASE1_ICE_BOTTOM = 1.00
PHASE1_ICE_FRACTION = 0.28
# Thaw-depth bracket: ice protected pre-fire, melted on burned post-fire only.
ICE_BRACKET_TOP_DEFAULT = 0.50
ICE_BRACKET_BOTTOM_DEFAULT = 0.68
ICE_BRACKET_FRACTION_DEFAULT = 0.36
ICE_TOP_BRACKET_CANDIDATES = [0.40, 0.45, 0.50, 0.55, 0.60]
ALT_MIN_CM = 30.0
ALT_JONES_MAX_CM = 75.0
ALT_BRACKET_TARGET_CM = 55.0
TARGET_PEAK_SNOW_DEPTH_CM = 40.0
BASELINE_PEAK_SNOW_DEPTH_CM = 7.2
# Empirical: scale 5.56 → ~108 cm peak; depth ≈ 19.4 cm per unit winter scale.
SNOW_DEPTH_CM_PER_WINTER_SCALE = 108.1 / (TARGET_PEAK_SNOW_DEPTH_CM / BASELINE_PEAK_SNOW_DEPTH_CM)
WINTER_PRECIP_SCALE = TARGET_PEAK_SNOW_DEPTH_CM / SNOW_DEPTH_CM_PER_WINTER_SCALE
CLIMATE_BIAS_CANDIDATES = [2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5]
CALIBRATION_PATH = PKG / "anaktuvuk-climate-calibration.json"
FIRE_CALIBRATION_PATH = PKG / "anaktuvuk-fire-calibration.json"
ICE_CALIBRATION_PATH = PKG / "anaktuvuk-ice-calibration.json"
ICE_CALIBRATION_OUT = ROOT / "experiments/thermokarst/anaktuvuk_ice_calibration_results"
BRACKET_CLIMATE_CALIBRATION_PATH = PKG / "anaktuvuk-bracket-climate-calibration.json"
BRACKET_CLIMATE_CALIBRATION_OUT = (
    ROOT / "experiments/thermokarst/anaktuvuk_bracket_climate_calibration_results")
ICE_BRACKET_OUT = ROOT / "experiments/thermokarst/anaktuvuk_ice_bracket_results"
ICE_TOP_CANDIDATES = [0.15, 0.20, 0.25, 0.30]
ICE_CALIB_BOTTOM = 0.55
ICE_CALIB_FRACTION = 0.32
CAL_EQ_YEARS = 10
PHASE2_OUT = ROOT / "experiments/thermokarst/anaktuvuk_phase2_validation_results"
PHASE2_CELLS = [(0, 0), (0, 1), (1, 0), (1, 1)]
PHASE2_CELL_META = {
    (0, 0): {"role": "upland_burned", "fire": True, "slope": 0.0, "drainage": 0,
             "ice_top": 0.30, "ice_bottom": 1.00, "ice_frac": 0.28},
    (0, 1): {"role": "upland_control", "fire": False, "slope": 0.0, "drainage": 0,
             "ice_top": 0.30, "ice_bottom": 1.00, "ice_frac": 0.28},
    (1, 0): {"role": "slope_burned", "fire": True, "slope": 3.0, "drainage": 0,
             "ice_top": 0.30, "ice_bottom": 1.00, "ice_frac": 0.30},
    (1, 1): {"role": "dlb_burned", "fire": True, "slope": 0.0, "drainage": 1,
             "ice_top": 0.25, "ice_bottom": 0.80, "ice_frac": 0.24},
}
FIRE_SEVERITY_CANDIDATES = [2, 3, 4]
DEFAULT_FIRE_SEVERITY = 3
SNOW_RATIO_MIN = 0.85
SNOW_RATIO_MAX = 1.15
MAX_ORGANIC_BURN_FOSLBURN = 1.0
MAX_ORGANIC_BURN_VSMBURN = 1.0
MAX_ORGANIC_BURN_R_RETAIN_C = 0.0
MAX_ORGANIC_BURN_FIRE_SEVERITY = 4

PHASE0_TAIR = np.array([-24., -23., -20., -12., 0., 6., 10., 8., 2., -6., -16., -22.])
PHASE0_PRECIP = np.array([5., 4., 4., 5., 8., 14., 18., 12., 8., 6., 5., 5.])
PHASE0_NIRR = np.array([0., 1., 4., 12., 18., 20., 16., 10., 4., 1., 0., 0.])


def copy_spatial(base, out, cells=None, cell_meta=None):
    cells = cells or CELLS
    cell_meta = cell_meta or {}
    label = "four-cells" if len(cells) > 2 else "two-cells"
    mask = out / f"run-mask-{label}.nc"
    shutil.copy2(base["IO"]["runmask_file"], mask)
    with Dataset(mask, "r+") as dataset:
        dataset["run"][:] = 0
        for y, x in cells:
            dataset["run"][y, x] = 1
    base["IO"]["runmask_file"] = str(mask)

    for key, var in [
            ("veg_class_file", "veg_class"),
            ("drainage_file", "drainage_class"),
            ("topo_file", "slope"),
    ]:
        src = Path(base["IO"][key])
        dst = out / src.name
        shutil.copy2(src, dst)
        with Dataset(dst, "r+") as dataset:
            for y, x in cells:
                meta = cell_meta.get((y, x), {})
                if var == "veg_class":
                    dataset[var][y, x] = CMT
                elif var == "drainage_class":
                    dataset[var][y, x] = meta.get("drainage", 0)
                else:
                    dataset[var][y, x] = meta.get("slope", 0.0)
        base["IO"][key] = str(dst)


def run_cells(binary, out, name, cfg, args, cells):
    run_dir = out / name
    if run_dir.exists():
        shutil.rmtree(run_dir)
    path = out / f"{name}.json"
    path.write_text(json.dumps(cfg, indent=2) + "\n")
    cmd = [str(binary), "-f", str(path), "--log-level", "warn",
           "--max-output-volume=-1"] + args
    with (out / f"{name}.log").open("w") as log:
        done = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    if done.returncode:
        raise RuntimeError(f"{name} exited {done.returncode}; see {out / f'{name}.log'}")
    expected = [100] * len(cells)
    with Dataset(run_dir / "run_status.nc") as dataset:
        status = [int(dataset["run_status"][y, x]) for y, x in cells]
    if status != expected:
        raise RuntimeError(f"{name} statuses {status}")
    return status


def completed_cells(out, name, cells):
    path = out / name / "run_status.nc"
    if not path.exists():
        return None
    with Dataset(path) as dataset:
        status = [int(dataset["run_status"][y, x]) for y, x in cells]
    expected = [100] * len(cells)
    return status if status == expected else None


def expand_restart_for_phase2(source, dest, template=BURNED_CELL, targets=None):
    """Copy EQ restart state from Phase 1 active cells onto new Phase 2 grid cells."""
    targets = targets or [(1, 0), (1, 1)]
    shutil.copy2(source, dest)
    with Dataset(dest, "r+") as dataset:
        ty, tx = template
        for var in dataset.variables.values():
            if len(var.dimensions) < 2 or var.dimensions[0] != "Y" or var.dimensions[1] != "X":
                continue
            template_data = np.asarray(var[ty, tx])
            for y, x in targets:
                if var.ndim == 2:
                    var[y, x] = template_data
                else:
                    var[y, x, ...] = template_data


def inject_excess_cells(source, dest, profiles):
    """Inject excess ice per cell: profiles maps cell -> (fraction, top, bottom)."""
    shutil.copy2(source, dest)
    added = {}
    with Dataset(dest, "r+") as dataset:
        for cell, (fraction, top, bottom) in profiles.items():
            y, x = cell
            n = _restart_scalar(dataset, "numsl", y, x, default=0)
            z = 0.0
            total = 0.0
            for j in range(n):
                matrix = _layer_matrix(dataset, y, x, j)
                overlap = max(0.0, min(z + matrix, bottom) - max(z, top))
                if overlap > 0.0:
                    temperature = float(dataset["TSsoil"][y, x, j])
                    if temperature > 1.0e-8:
                        raise RuntimeError(f"injection layer is thawed: {cell} layer {j}")
                    if temperature > 0.0:
                        dataset["TSsoil"][y, x, j] = 0.0
                    mass = 917.0 * overlap * fraction / (1.0 - fraction)
                    dataset["TKexcess"][y, x, j] = mass
                    dataset["DZsoil"][y, x, j] = matrix + mass / 917.0
                    total += mass
                z += matrix
            added[str(cell)] = total
    return added


def make_phase0_climate(source, dest, nyears):
    shutil.copy2(source, dest)
    with Dataset(dest, "r+") as dataset:
        offsets = np.linspace(-0.6, 0.6, nyears)
        for year in range(nyears):
            for month in range(12):
                idx = year * 12 + month
                dataset["tair"][idx, :, :] = float(PHASE0_TAIR[month] + offsets[year])
                dataset["precip"][idx, :, :] = PHASE0_PRECIP[month]
                dataset["nirr"][idx, :, :] = PHASE0_NIRR[month]
                if "vapor_press" in dataset.variables:
                    dataset["vapor_press"][idx, :, :] = 100.0
        nmonths = nyears * 12
        for name in ["tair", "precip", "nirr", "vapor_press"]:
            if name in dataset.variables and dataset[name].shape[0] > nmonths:
                dataset[name][nmonths:] = 0.0
    monthly = PHASE0_TAIR.reshape(1, 12) + np.linspace(-0.6, 0.6, nyears)[:, None]
    return {
        "years": nyears,
        "mean_annual_tair_C": [float(x) for x in monthly.mean(axis=1)],
        "year_to_year_tair_range_C": float(np.ptp(monthly.mean(axis=1))),
        "template_mat_C": float(PHASE0_TAIR.mean()),
        "source": "synthetic North Slope thaw-capable (Phase 0)",
    }


def make_fire(source, dest, event_year=None, fire_jday=PHASE0_FIRE_JDAY,
              burned_cells=None, severity=4):
    shutil.copy2(source, dest)
    with Dataset(dest, "r+") as dataset:
        for name in ["exp_burn_mask", "exp_jday_of_burn",
                     "exp_fire_severity", "exp_area_of_burn"]:
            dataset[name][:] = 0
        if event_year is not None:
            cells = burned_cells if burned_cells is not None else [BURNED_CELL]
            for y, x in cells:
                dataset["exp_burn_mask"][event_year, y, x] = 1
                dataset["exp_jday_of_burn"][event_year, y, x] = fire_jday
                dataset["exp_fire_severity"][event_year, y, x] = severity
                dataset["exp_area_of_burn"][event_year, y, x] = 1000000


def make_spec(source, dest):
    rows = list(csv.DictReader(source.open()))
    extra_daily = set(bgc.TK) | {"SNOWTHICK", "TKPOND", "TKSURFICE"}
    extra_yearly = set(bgc.BGC)
    extra_monthly = {
        "BURNTHICK", "BURNSOIL2AIRC", "BURNSOIL2AIRN",
        "TLAYER", "LAYERDEPTH", "LAYERDZ", "LAYERTYPE",
        "IWCLAYER", "LWCLAYER", "VWCLAYER", "SOC",
        "TSOIL_30cm", "TSOIL_100cm",
    }
    extra_layers = {
        "TLAYER", "LAYERDEPTH", "LAYERDZ", "LAYERTYPE",
        "IWCLAYER", "LWCLAYER", "VWCLAYER", "SOC",
    }
    for row in rows:
        row["Yearly"] = row["Monthly"] = row["Daily"] = ""
        if row["Name"] in extra_daily:
            row["Daily"] = "d"
        if row["Name"] in extra_yearly:
            row["Yearly"] = "y"
        if row["Name"] in extra_monthly:
            row["Monthly"] = "m"
        if row["Name"] in extra_layers:
            row["Layers"] = "forced"
    with dest.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def spinup_config(base, directory):
    """Stage A: legacy thermal path (thermokarst off) for fast BGC equilibration."""
    cfg = json.loads(json.dumps(base))
    io = cfg["IO"]
    io["output_dir"] = str(directory) + "/"
    io["restart_from"] = ""
    io["output_nc_eq"] = io["output_nc_pr"] = io["output_nc_sp"] = 0
    io["output_nc_tr"] = 0
    io["output_nc_sc"] = 0
    io["output_interval"] = 1
    io["output_monthly"] = 0
    cfg["model_settings"].pop("thermokarst", None)
    for stage in ["pr", "eq", "sp", "tr", "sc"]:
        cfg["stage_settings"][stage].update({
            "env": True, "bgc": True, "nfeed": True, "avlnflg": True,
            "baseline": False, "dsb": False, "dsl": False, "dyn_lai": True,
        })
    cfg["stage_settings"]["tr_start_yr"] = 0
    return cfg


def config(base, directory, restart, fire_file, output=True, tr_start=0,
           ice_top=PHASE0_ICE_TOP, ice_bottom=PHASE0_ICE_BOTTOM):
    cfg = bgc.config(base, directory, restart, dsl=True, output=output, tr_start=tr_start)
    cfg["IO"]["hist_exp_fire_file"] = str(fire_file)
    cfg["model_settings"]["thermokarst"] = {
        "enabled": True,
        "excess_fraction": 0.0,
        "top_depth": ice_top,
        "bottom_depth": ice_bottom,
    }
    for stage in ["tr", "sc"]:
        cfg["stage_settings"][stage]["dsb"] = True
    return cfg


def _restart_scalar(dataset, name, y, x, default=0):
    if name not in dataset.variables:
        return default
    value = np.ma.asarray(dataset[name][y, x]).filled(default)
    return int(value) if name in ("TKversion", "TKactive", "numsl") else float(value)


def _layer_matrix(dataset, y, x, j):
    dz = float(np.ma.asarray(dataset["DZsoil"][y, x, j]).filled(0.0))
    if "TKmatrix" not in dataset.variables:
        return dz
    matrix = float(np.ma.asarray(dataset["TKmatrix"][y, x, j]).filled(0.0))
    if matrix > 0.0:
        return matrix
    if "TKexcess" in dataset.variables:
        excess = float(np.ma.asarray(dataset["TKexcess"][y, x, j]).filled(0.0))
        if excess > 0.0:
            return max(0.0, dz - excess / 917.0)
    return dz


def _layer_porosity(dataset, y, x, j, matrix):
    if "TKporosity" in dataset.variables:
        porosity = float(np.ma.asarray(dataset["TKporosity"][y, x, j]).filled(0.0))
        if porosity > 0.0:
            return porosity
    if matrix <= 0.0:
        return 0.0
    ice = float(np.ma.asarray(dataset["ICEsoil"][y, x, j]).filled(0.0))
    liq = float(np.ma.asarray(dataset["LIQsoil"][y, x, j]).filled(0.0))
    pore = (ice / 917.0 + liq / 1000.0) / matrix
    return float(np.clip(pore, 0.05, 0.95))


def prepare_thermokarst_restart(source, dest, cells=CELLS):
    """Bridge a light spin-up restart for Stage B thermokarst + offline ice injection."""
    shutil.copy2(source, dest)
    with Dataset(dest, "r+") as dataset:
        for y, x in cells:
            if "TKversion" in dataset.variables:
                dataset["TKversion"][y, x] = TK_RESTART_VERSION
            if "TKactive" in dataset.variables:
                dataset["TKactive"][y, x] = 1
            n = _restart_scalar(dataset, "numsl", y, x, default=0)
            if n <= 0:
                raise RuntimeError(f"inactive or empty restart cell ({y}, {x}) in {source}")
            for j in range(n):
                matrix = _layer_matrix(dataset, y, x, j)
                dz = float(np.ma.asarray(dataset["DZsoil"][y, x, j]).filled(0.0))
                if "TKmatrix" in dataset.variables:
                    dataset["TKmatrix"][y, x, j] = matrix
                if "TKporosity" in dataset.variables:
                    dataset["TKporosity"][y, x, j] = _layer_porosity(dataset, y, x, j, matrix)
                if "TKexcess" in dataset.variables:
                    dataset["TKexcess"][y, x, j] = 0.0
                if abs(dz - matrix) > 1.0e-9 and "TKexcess" not in dataset.variables:
                    dataset["DZsoil"][y, x, j] = matrix
            if "TKstate" in dataset.variables:
                state = dataset["TKstate"]
                if state.ndim == 3 and state.shape[2] >= TK_STATE_COUNT:
                    state[y, x, :TK_STATE_COUNT] = 0.0
            if "TKpuddle" in dataset.variables:
                dataset["TKpuddle"][y, x] = 0.0
    return dest


def save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=240, bbox_inches="tight")
    fig.savefig(out / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def load_obs_csv(path):
    rows = []
    with path.open() as stream:
        for line in stream:
            if line.startswith("#") or not line.strip():
                continue
            rows.append(line)
    return list(csv.DictReader(rows))


def subsidence_window(sub, cell, year_start, year_end):
    baseline_day = max(0, year_start * 365 - 1)
    end_day = min((year_end + 1) * 365 - 1, sub.shape[0] - 1)
    y, x = cell
    return float(sub[end_day, y, x] - sub[baseline_day, y, x])


def cumulative_at_year(sub, cell, year):
    day = min((year + 1) * 365 - 1, sub.shape[0] - 1)
    y, x = cell
    return float(sub[day, y, x])


def monthly(directory, name):
    with Dataset(directory / f"{name}_monthly_tr.nc") as dataset:
        return np.asarray(np.ma.asarray(dataset[name][:]).filled(np.nan), float)


def approximate_tdd_from_monthly(temp_monthly, cell):
    y, x = cell
    series = temp_monthly[:, y, x]
    nyears = series.size // 12
    tdd = []
    for year in range(nyears):
        total = 0.0
        for month in range(12):
            t = float(series[year * 12 + month])
            if np.isfinite(t) and t > 0.0:
                total += t * DINM[month]
        tdd.append(total)
    return tdd


def tdd_ratio_series(tdd_burned, tdd_control, year_start, year_end):
    ratios = []
    for year in range(year_start, year_end + 1):
        if year >= len(tdd_burned) or year >= len(tdd_control):
            break
        ctl = tdd_control[year]
        if ctl <= 1.0:
            continue
        ratios.append(tdd_burned[year] / ctl)
    return ratios


def magt_from_monthly(temp_monthly, cell):
    y, x = cell
    series = temp_monthly[:, y, x]
    nyears = series.size // 12
    return [float(np.nanmean(series[y * 12:(y + 1) * 12])) for y in range(nyears)]


def mean_window(series, year_start, year_end):
    vals = []
    for year in range(year_start, year_end + 1):
        chunk = series[year * 12:(year + 1) * 12]
        if chunk.size:
            vals.append(float(np.nanmean(chunk)))
    return float(np.mean(vals)) if vals else float("nan")


def max_seasonal_thaw_cm(front_daily, cell, tr_year):
    """Max seasonal thaw-front depth (cm) for one transient year."""
    start = tr_year * 365
    end = min((tr_year + 1) * 365, front_daily.shape[0])
    y, x = cell
    chunk = front_daily[start:end, y, x]
    if chunk.size == 0:
        return float("nan")
    return float(np.nanmax(chunk) * 100.0)


def september_max_thaw_cm(directory, cell, nyears):
    """September max thaw-front depth (cm) per transient year."""
    front = bgc.read_daily(directory, "TKFRONT")
    ftype = bgc.read_daily(directory, "TKFRONTTYPE")
    depths = bgc.cell_series(front, cell)
    types = bgc.cell_series(ftype, cell)
    values = []
    for year in range(nyears):
        start = year * 365 + 243
        end = year * 365 + 272
        chunk_f = depths[start:end + 1]
        chunk_t = types[start:end + 1]
        thaw = chunk_t <= -0.5
        if np.any(thaw):
            values.append(float(np.nanmax(chunk_f[thaw]) * 100.0))
        else:
            values.append(float("nan"))
    return values


def alt_summary_cm(directory, cell, nyears, sub_daily=None):
    """September ALT series and max (cm); corrected = thaw + subsidence if provided."""
    sept = september_max_thaw_cm(directory, cell, nyears)
    if sub_daily is not None:
        y, x = cell
        corrected = []
        for year in range(nyears):
            day = min((year + 1) * 365 - 1, sub_daily.shape[0] - 1)
            corrected.append(float(sept[year] + sub_daily[day, y, x] * 100.0))
        sept = corrected
    finite = [v for v in sept if np.isfinite(v)]
    return {
        "september_cm": sept,
        "max_cm": float(max(finite)) if finite else float("nan"),
        "mean_cm": float(np.mean(finite)) if finite else float("nan"),
    }


def snow_metrics(out, tr_years, fire_tr_year=FIRE_YEAR):
    """Post-fire winter snow-depth ratio burned / control (month-end max per TR year)."""
    snow_b = bgc.read_daily(out / "burned", "SNOWTHICK")
    snow_c = bgc.read_daily(out / "control", "SNOWTHICK")
    by, bx = BURNED_CELL
    cy, cx = CONTROL_CELL
    sb = snow_b[:, by, bx]
    sc = snow_c[:, cy, cx]
    ratios = []
    for year in range(fire_tr_year + 1, tr_years):
        start = year * 365
        end = min((year + 1) * 365, sb.shape[0])
        max_b = float(np.nanmax(sb[start:end]))
        max_c = float(np.nanmax(sc[start:end]))
        if max_c > 1.0e-6:
            ratios.append(max_b / max_c)
    mean_ratio = float(np.mean(ratios)) if ratios else float("nan")
    return {
        "post_fire_winter_max_ratios": ratios,
        "post_fire_mean_ratio": mean_ratio,
        "post_fire_min_ratio": float(np.min(ratios)) if ratios else float("nan"),
        "post_fire_max_ratio": float(np.max(ratios)) if ratios else float("nan"),
    }


def load_fire_calibration():
    if not FIRE_CALIBRATION_PATH.exists():
        return None
    return json.loads(FIRE_CALIBRATION_PATH.read_text())


def load_ice_calibration():
    if not ICE_CALIBRATION_PATH.exists():
        return None
    return json.loads(ICE_CALIBRATION_PATH.read_text())


def load_bracket_climate_calibration():
    if not BRACKET_CLIMATE_CALIBRATION_PATH.exists():
        return None
    return json.loads(BRACKET_CLIMATE_CALIBRATION_PATH.read_text())


def ice_bracket_active(args) -> bool:
    return bool(getattr(args, "ice_bracket", False))


def yearly_alt_max_cm(iso_metrics, year_indices):
    if not iso_metrics:
        return float("nan")
    yearly = iso_metrics.get("yearly_cm") or []
    vals = [
        yearly[y] for y in year_indices
        if y < len(yearly) and np.isfinite(yearly[y])
    ]
    return float(max(vals)) if vals else float("nan")


def alt_bracket_metrics(out, tr_years, fire_tr_year):
    """Pre/post-fire max 0 °C isotherm ALT (cm) for thaw-depth bracket checks."""
    control_iso = _dplots.isotherm_alt_metrics(out / "control", CONTROL_CELL, tr_years)
    burned_iso = _dplots.isotherm_alt_metrics(out / "burned", BURNED_CELL, tr_years)
    pre_years = list(range(fire_tr_year))
    post_years = list(range(fire_tr_year, tr_years))
    return {
        "alt_control_pre_fire_max_cm": yearly_alt_max_cm(control_iso, pre_years),
        "alt_burned_pre_fire_max_cm": yearly_alt_max_cm(burned_iso, pre_years),
        "alt_control_post_fire_max_cm": yearly_alt_max_cm(control_iso, post_years),
        "alt_burned_post_fire_max_cm": yearly_alt_max_cm(burned_iso, post_years),
    }


def bracket_ice_score(row, ice_top_m):
    """Score thaw-depth bracket quality (higher = better burned-only melt)."""
    ice_top_cm = ice_top_m * 100.0
    score = 0.0
    pre = row.get("alt_control_pre_fire_max_cm")
    post_b = row.get("alt_burned_post_fire_max_cm")
    post_c = row.get("alt_control_post_fire_max_cm")
    if np.isfinite(pre) and pre < ice_top_cm:
        score += 1.0
    if np.isfinite(post_b) and post_b > ice_top_cm:
        score += 2.0
    if np.isfinite(post_c) and post_c < ice_top_cm:
        score += 2.0
    contrast = row.get("subsidence_contrast_cm")
    if np.isfinite(contrast):
        score += max(0.0, contrast) / 10.0
    control_sub = row.get("subsidence_2009_2014_control_cm")
    if np.isfinite(control_sub) and control_sub < 5.0:
        score += 1.0
    return score


def resolve_ice_top(args):
    if args.ice_top is not None:
        return args.ice_top
    calib = load_ice_calibration()
    if calib and calib.get("selected_ice_top_m") is not None:
        return float(calib["selected_ice_top_m"])
    if ice_bracket_active(args):
        return ICE_BRACKET_TOP_DEFAULT
    return PHASE1_ICE_TOP


def resolve_ice_bottom(args):
    if args.ice_bottom is not None:
        return args.ice_bottom
    calib = load_ice_calibration()
    if calib and calib.get("selected_ice_bottom_m") is not None:
        return float(calib["selected_ice_bottom_m"])
    if ice_bracket_active(args):
        return ICE_BRACKET_BOTTOM_DEFAULT
    return PHASE1_ICE_BOTTOM


def resolve_ice_fraction(args):
    if args.ice_fraction is not None:
        return args.ice_fraction
    calib = load_ice_calibration()
    if calib and calib.get("selected_ice_fraction") is not None:
        return float(calib["selected_ice_fraction"])
    if ice_bracket_active(args):
        return ICE_BRACKET_FRACTION_DEFAULT
    return PHASE1_ICE_FRACTION


def figure_prefix(args) -> str:
    if ice_bracket_active(args):
        return "anaktuvuk-ice-bracket"
    if max_organic_burn_active(args):
        return "anaktuvuk-max-organic-burn"
    if getattr(args, "phase", 1) == 0:
        return "anaktuvuk"
    return "anaktuvuk-phase1"


def max_organic_burn_active(args) -> bool:
    return bool(getattr(args, "max_organic_burn", False))


def _set_param_value(line, value):
    if "//" not in line:
        return line
    comment = line[line.index("//"):]
    return f"{value:<20}{comment.rstrip()}"


def ensure_max_organic_burn_parameter_dir(out: Path) -> Path:
    """Copy CMT parameter files and patch CMT05 fire params for full organic burn."""
    param_dir = out / "parameters"
    param_dir.mkdir(parents=True, exist_ok=True)
    for src in (ROOT / "parameters").glob("cmt_*.txt"):
        shutil.copy2(src, param_dir / src.name)
    path = param_dir / "cmt_firepar.txt"
    lines = path.read_text().splitlines()
    current_cmt = None
    patched = []
    for line in lines:
        if line.startswith("// CMT"):
            match = re.search(r"CMT(\d+)", line)
            current_cmt = int(match.group(1)) if match else None
        if current_cmt == CMT:
            if "foslburn_sev" in line:
                line = _set_param_value(line, MAX_ORGANIC_BURN_FOSLBURN)
            elif "vsmburn:" in line or "vsmburn://" in line:
                line = _set_param_value(line, MAX_ORGANIC_BURN_VSMBURN)
            elif "r_retain_c:" in line or "r_retain_c://" in line:
                line = _set_param_value(line, MAX_ORGANIC_BURN_R_RETAIN_C)
        patched.append(line)
    path.write_text("\n".join(patched) + "\n")
    return param_dir


def apply_max_organic_burn_parameters(base, args, out: Path | None = None):
    if not max_organic_burn_active(args):
        return None
    if out is None:
        raise ValueError("max-organic-burn requires an output directory for parameter overrides")
    param_dir = ensure_max_organic_burn_parameter_dir(out)
    base["IO"]["parameter_dir"] = str(param_dir.resolve()) + "/"
    manifest = {
        "mode": "max_organic_burn",
        "parameter_dir": str(param_dir.resolve()),
        "cmt": CMT,
        "overrides": {
            "foslburn_sev1..5": MAX_ORGANIC_BURN_FOSLBURN,
            "vsmburn": MAX_ORGANIC_BURN_VSMBURN,
            "r_retain_c": MAX_ORGANIC_BURN_R_RETAIN_C,
        },
        "fire_severity": MAX_ORGANIC_BURN_FIRE_SEVERITY,
        "snow_gate": "relaxed (informational only)",
        "note": (
            "CMT05 foslburn indices patched to 1.0; fire file severity 4 maps to "
            "foslburn[4]. VSM cap relaxed so wet organic layers can burn."
        ),
    }
    (out / "max-organic-burn.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def resolve_fire_severity(args):
    if max_organic_burn_active(args):
        return MAX_ORGANIC_BURN_FIRE_SEVERITY
    if args.fire_severity is not None:
        return int(args.fire_severity)
    calib = load_fire_calibration()
    if calib and calib.get("selected_severity") is not None:
        return int(calib["selected_severity"])
    return DEFAULT_FIRE_SEVERITY


def json_safe(value):
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    return value


def gate(checks, test, observed, criterion, ok, hard=False):
    checks.append({
        "test": test,
        "observed": observed,
        "criterion": criterion,
        "status": "PASS" if ok else "FAIL",
        "hard": hard,
    })


def write_checks(out, checks):
    (out / "checks.csv").write_text("")
    with (out / "checks.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=checks[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)


def setup_out(out, reuse):
    if out.exists() and not reuse:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)


def make_co2_tr(source, dest, start, nyears):
    """Slice CO2 from ``start``; pad with the last available year if the record is short."""
    shutil.copy2(source, dest)
    with Dataset(source) as src, Dataset(dest, "r+") as dst:
        for name, var in dst.variables.items():
            if var.dimensions and var.dimensions[0] in ("year", "time"):
                data = np.asarray(src[name][:])
                end = min(data.shape[0], start + nyears)
                chunk = data[start:end]
                if chunk.shape[0] < nyears:
                    chunk = np.concatenate([
                        chunk,
                        np.repeat(chunk[-1:], nyears - chunk.shape[0], axis=0),
                    ])
                var[:nyears] = chunk[:nyears]
    return dest


def ensure_initialization(args, out, base, eq_years, reuse):
    statuses = {}
    statuses["initialization"] = bgc.completed(out, "initialization") if reuse else None
    if statuses["initialization"] is None:
        statuses["initialization"] = bgc.run(
            args.binary.resolve(), out, "initialization",
            bgc.config(base, out / "initialization", output=False),
            ["--pr-yrs", "1", "--eq-yrs", str(eq_years)])
    return statuses


def run_transient_runs(args, out, base, initial, injected, fire_on, fire_off,
                       tr_years, ice_top, ice_bottom, ice_on_both, reuse):
    statuses = {}
    control_restart = injected if ice_on_both else initial
    for name, restart, fire, years in [
            ("control", control_restart, fire_off, tr_years),
            ("burned", injected, fire_on, tr_years),
            ("split-first", injected, fire_on, SPLIT)]:
        statuses[name] = bgc.completed(out, name) if reuse else None
        if statuses[name] is None:
            statuses[name] = bgc.run(
                args.binary.resolve(), out, name,
                config(base, out / name, restart, fire,
                       ice_top=ice_top, ice_bottom=ice_bottom),
                ["--tr-yrs", str(years)])

    statuses["resumed"] = bgc.completed(out, "resumed") if reuse else None
    if statuses["resumed"] is None:
        statuses["resumed"] = bgc.run(
            args.binary.resolve(), out, "resumed",
            config(base, out / "resumed", out / "split-first/restart-tr.nc", fire_on,
                   tr_start=SPLIT, ice_top=ice_top, ice_bottom=ice_bottom),
            ["--tr-yrs", str(tr_years - SPLIT)])
    return statuses


def collect_metrics(
        out, tr_years, fire_jday, *,
        fire_tr_year=FIRE_YEAR,
        primary_start=PRIMARY_START,
        primary_end=PRIMARY_END,
        stab_start=STAB_START,
        stab_end=STAB_END,
        calendar_start=2007,
        validation_tr_year=None,
        early_tdd_start=3,
        early_tdd_end=7,
        late_tdd_start=12,
        late_tdd_end=14,
        check_restart=True):
    sub_burned = bgc.read_daily(out / "burned", "TKSUBSIDENCE")
    sub_control = bgc.read_daily(out / "control", "TKSUBSIDENCE")
    burn = monthly(out / "burned", "BURNTHICK")
    t30_b = monthly(out / "burned", "TSOIL_30cm")
    t30_c = monthly(out / "control", "TSOIL_30cm")
    t100_b = monthly(out / "burned", "TSOIL_100cm")
    t100_c = monthly(out / "control", "TSOIL_100cm")
    front_b = bgc.read_daily(out / "burned", "TKFRONT")
    alt_control_front = alt_summary_cm(out / "control", CONTROL_CELL, tr_years, sub_control)
    alt_burned_front = alt_summary_cm(out / "burned", BURNED_CELL, tr_years, sub_burned)
    alt_control_iso = _dplots.isotherm_alt_metrics(out / "control", CONTROL_CELL, tr_years)
    alt_burned_iso = _dplots.isotherm_alt_metrics(out / "burned", BURNED_CELL, tr_years)
    alt_control = alt_control_iso if alt_control_iso else alt_control_front
    alt_burned = alt_burned_iso if alt_burned_iso else alt_burned_front

    resumed_daily = None
    if check_restart and (out / "split-first").exists() and (out / "resumed").exists():
        first = {name: bgc.read_daily(out / "split-first", name) for name in bgc.TK}
        second = {name: bgc.read_daily(out / "resumed", name) for name in bgc.TK}
        resumed_daily = {
            name: np.concatenate([first[name], second[name]], axis=0) for name in bgc.TK}

    by, bx = BURNED_CELL
    cy, cx = CONTROL_CELL
    validation_tr_year = (tr_years - 1 if validation_tr_year is None
                          else validation_tr_year)

    primary_b = cumulative_at_year(sub_burned, BURNED_CELL, primary_end)
    primary_c = cumulative_at_year(sub_control, CONTROL_CELL, primary_end)
    fire_year_b = cumulative_at_year(sub_burned, BURNED_CELL, fire_tr_year)
    fire_year_c = cumulative_at_year(sub_control, CONTROL_CELL, fire_tr_year)
    lidar_epoch_b = subsidence_window(sub_burned, BURNED_CELL, primary_start, primary_end)
    lidar_epoch_c = subsidence_window(sub_control, CONTROL_CELL, primary_start, primary_end)
    stab_b = subsidence_window(sub_burned, BURNED_CELL, stab_start, stab_end)
    stab_c = subsidence_window(sub_control, CONTROL_CELL, stab_start, stab_end)

    tdd_b = approximate_tdd_from_monthly(t30_b, BURNED_CELL)
    tdd_c = approximate_tdd_from_monthly(t30_c, CONTROL_CELL)
    early_ratios = tdd_ratio_series(tdd_b, tdd_c, early_tdd_start, early_tdd_end)
    late_ratios = tdd_ratio_series(tdd_b, tdd_c, late_tdd_start, late_tdd_end)
    early_t30_b = mean_window(t30_b[:, by, bx], early_tdd_start, early_tdd_end)
    early_t30_c = mean_window(t30_c[:, cy, cx], early_tdd_start, early_tdd_end)
    late_t30_b = mean_window(t30_b[:, by, bx], late_tdd_start, late_tdd_end)
    late_t30_c = mean_window(t30_c[:, cy, cx], late_tdd_start, late_tdd_end)
    magt_b = magt_from_monthly(t100_b, BURNED_CELL)
    magt_c = magt_from_monthly(t100_c, CONTROL_CELL)
    magt_offset_last = (magt_b[validation_tr_year] - magt_c[validation_tr_year]
                        if len(magt_b) > validation_tr_year else float("nan"))

    burn_depth = float(np.sum(burn[:, by, bx]))
    burn_after_fire_year = float(np.sum(burn[(fire_tr_year + 1) * 12:, by, bx]))
    thaw_front_2021_cm = max_seasonal_thaw_cm(front_b, BURNED_CELL, validation_tr_year)
    val_day = min((validation_tr_year + 1) * 365 - 1, sub_burned.shape[0] - 1)
    thaw_pen_2021_cm = thaw_front_2021_cm + float(sub_burned[val_day, by, bx] * 100.0)

    diffs = {}
    inventory_relative = 0.0
    sub_resume_diff = float("nan")
    sub_end_diff = float("nan")
    if resumed_daily is not None:
        final_b = out / "burned/restart-tr.nc"
        final_r = out / "resumed/restart-tr.nc"
        physical = ["TKmatrix", "TKporosity", "TKexcess", "DZsoil"]
        diffs = {
            name: bgc.maxdiff(
                fire_topo.restart(final_b, name, BURNED_CELL),
                fire_topo.restart(final_r, name, BURNED_CELL))
            for name in physical
        }
        ia = bgc.inventory(final_b, BURNED_CELL)
        ib = bgc.inventory(final_r, BURNED_CELL)
        for name in ["C", "N"]:
            inventory_relative = max(
                inventory_relative,
                abs(ia[name] - ib[name]) / max(abs(ia[name]), 1.0))
        sub_resume_diff = bgc.maxdiff(
            sub_burned[:, by, bx], resumed_daily["TKSUBSIDENCE"][:, by, bx])
        sub_end_diff = abs(float(sub_burned[-1, by, bx])
                           - float(resumed_daily["TKSUBSIDENCE"][-1, by, bx]))

    obs_tdd = load_obs_csv(OBS_DIR / "jones2024-ground-temperature-annual.csv")
    obs_early_tdd = []
    for row in obs_tdd:
        if row["sensor_depth_m"] != "0.15":
            continue
        year = int(row["year"])
        if 2010 <= year <= 2014 and row["thawing_degree_days_C"]:
            if row["location"] == "burned":
                b = float(row["thawing_degree_days_C"])
                u = next(float(r["thawing_degree_days_C"])
                         for r in obs_tdd
                         if int(r["year"]) == year
                         and r["location"] == "unburned"
                         and r["sensor_depth_m"] == "0.15")
                obs_early_tdd.append(b / u)
    obs_early_tdd_mean = float(np.mean(obs_early_tdd)) if obs_early_tdd else float("nan")
    stabilization_ratio = stab_b / lidar_epoch_b if lidar_epoch_b > 1e-9 else 0.0

    return {
        "sub_burned": sub_burned,
        "sub_control": sub_control,
        "burn": burn,
        "tdd_b": tdd_b,
        "tdd_c": tdd_c,
        "magt_b": magt_b,
        "magt_c": magt_c,
        "primary_b": primary_b,
        "primary_c": primary_c,
        "fire_year_b": fire_year_b,
        "fire_year_c": fire_year_c,
        "lidar_epoch_b": lidar_epoch_b,
        "lidar_epoch_c": lidar_epoch_c,
        "stab_b": stab_b,
        "stab_c": stab_c,
        "early_ratios": early_ratios,
        "late_ratios": late_ratios,
        "early_t30_b": early_t30_b,
        "early_t30_c": early_t30_c,
        "late_t30_b": late_t30_b,
        "late_t30_c": late_t30_c,
        "magt_offset_last": magt_offset_last,
        "burn_depth": burn_depth,
        "burn_after_fire_year": burn_after_fire_year,
        "thaw_pen_2021_cm": thaw_pen_2021_cm,
        "thaw_front_2021_cm": thaw_front_2021_cm,
        "diffs": diffs,
        "inventory_relative": inventory_relative,
        "sub_resume_diff": sub_resume_diff,
        "sub_end_diff": sub_end_diff,
        "obs_early_tdd_mean": obs_early_tdd_mean,
        "stabilization_ratio": stabilization_ratio,
        "resumed_daily": resumed_daily,
        "alt_control": alt_control,
        "alt_burned": alt_burned,
        "alt_control_front": alt_control_front,
        "alt_burned_front": alt_burned_front,
        "alt_control_isotherm": alt_control_iso,
        "alt_burned_isotherm": alt_burned_iso,
        "alt_max_control_cm": alt_control["max_cm"],
        "alt_max_burned_cm": alt_burned["max_cm"],
        "alt_method": "isotherm" if alt_control_iso else "tkfront",
        "snow": snow_metrics(out, tr_years, fire_tr_year=fire_tr_year),
        "calendar_start": calendar_start,
        "fire_tr_year": fire_tr_year,
        **alt_bracket_metrics(out, tr_years, fire_tr_year),
    }


def staged_metrics_kwargs():
    """TR-year windows for production SP(20)+TR(24) workflow (calendar 2000–2023)."""
    return {
        "fire_tr_year": TRANSIENT_FIRE_TR_YEAR,
        "primary_start": TRANSIENT_PRIMARY_START,
        "primary_end": TRANSIENT_PRIMARY_END,
        "stab_start": TRANSIENT_STAB_START,
        "stab_end": TRANSIENT_STAB_END,
        "calendar_start": TRANSIENT_TR_CALENDAR_START,
        "validation_tr_year": TRANSIENT_VALIDATION_END,
        "early_tdd_start": 2010 - TRANSIENT_TR_CALENDAR_START,
        "early_tdd_end": 2014 - TRANSIENT_TR_CALENDAR_START,
        "late_tdd_start": 2019 - TRANSIENT_TR_CALENDAR_START,
        "late_tdd_end": 2021 - TRANSIENT_TR_CALENDAR_START,
    }


def write_figures(out, metrics, tr_years, fire_jday, phase_label, *,
                  calendar_start=2007, fire_tr_year=FIRE_YEAR,
                  primary_start=PRIMARY_START, primary_end=PRIMARY_END,
                  stab_start=STAB_START, stab_end=STAB_END,
                  prefix=None):
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 10,
        "axes.labelsize": 9, "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "svg.fonttype": "none",
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })
    sub_burned = metrics["sub_burned"]
    sub_control = metrics["sub_control"]
    by, bx = BURNED_CELL
    cy, cx = CONTROL_CELL
    calendar_years = calendar_start + np.arange(sub_burned.shape[0]) / 365.0
    fire_line = calendar_start + fire_tr_year + (fire_jday - 1) / 365.0
    prefix = prefix or ("anaktuvuk" if phase_label == 0 else "anaktuvuk-phase1")

    fig, ax = plt.subplots(figsize=(7.4, 3.8), layout="constrained")
    ax.plot(calendar_years, sub_control[:, cy, cx] * 100.0, "--", color=MUTED, lw=1.4,
            label="Unburned control")
    ax.plot(calendar_years, sub_burned[:, by, bx] * 100.0, color=TEAL, lw=1.8,
            label="Burned CMT05")
    ax.axvline(fire_line, color=ORANGE, lw=1.0, ls=":", label="2007 fire")
    ax.axvspan(calendar_start + primary_start, calendar_start + primary_end + 1,
               color=BLUE, alpha=0.08, label="2009–2014 LiDAR window")
    ax.axvspan(calendar_start + stab_start, calendar_start + stab_end + 1,
               color=ORANGE, alpha=0.06, label="2014–2021 stabilization")
    ax.set(xlabel=f"Calendar year (TR 0 = {calendar_start})",
           ylabel="Cumulative subsidence (cm)",
           title=f"Anaktuvuk Phase {phase_label}: burned vs unburned Yedoma tussock")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.legend(loc="upper left")
    save(fig, out, f"{prefix}-subsidence-burned-vs-control")

    fig, ax = plt.subplots(figsize=(7.0, 3.6), layout="constrained")
    bars = ["LiDAR window\nburned", "LiDAR window\ncontrol",
            "Cumulative\n2014 burned", "Stabilization\n2014–2021"]
    vals = [
        metrics["lidar_epoch_b"] * 100,
        metrics["lidar_epoch_c"] * 100,
        metrics["primary_b"] * 100,
        metrics["stab_b"] * 100,
    ]
    ax.bar(bars, vals, color=[TEAL, MUTED, BLUE, ORANGE], width=0.55)
    ax.set_ylabel("Subsidence (cm)")
    ax.set_title("LiDAR-window and cumulative subsidence")
    ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, f"{prefix}-subsidence-by-window")

    years = np.arange(tr_years)
    fig, ax = plt.subplots(figsize=(7.0, 3.6), layout="constrained")
    ratio = [b / c if c > 1.0 else float("nan")
             for b, c in zip(metrics["tdd_b"][:tr_years], metrics["tdd_c"][:tr_years])]
    ax.plot(years + calendar_start, ratio, "o-", color=TEAL, lw=1.5,
            label="Model (TSOIL_30cm proxy)")
    if np.isfinite(metrics["obs_early_tdd_mean"]):
        ax.axhline(metrics["obs_early_tdd_mean"], color=ORANGE, ls="--", lw=1.1,
                   label=f"Obs early mean ({metrics['obs_early_tdd_mean']:.1f}×)")
    ax.axhline(1.0, color=MUTED, lw=0.8)
    ax.set(xlabel="Calendar year", ylabel="TDD ratio burned / control",
           title="Thawing degree-day contrast (0.15 m proxy)")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.legend(loc="upper right")
    save(fig, out, f"{prefix}-tdd-ratio")

    fig, ax = plt.subplots(figsize=(7.0, 3.6), layout="constrained")
    ax.plot(years + calendar_start, metrics["magt_b"][:tr_years], color=TEAL, lw=1.6,
            label="Burned 1 m")
    ax.plot(years + calendar_start, metrics["magt_c"][:tr_years], "--", color=MUTED, lw=1.4,
            label="Control 1 m")
    ax.plot(years + calendar_start,
            np.array(metrics["magt_b"][:tr_years]) - np.array(metrics["magt_c"][:tr_years]),
            color=ORANGE, lw=1.2, label="Burned − control")
    ax.axvline(calendar_start + fire_tr_year + fire_jday / 365.0, color=ORANGE, ls=":", lw=0.9)
    ax.set(xlabel="Calendar year", ylabel="Mean annual ground temperature (°C)",
           title="1 m soil temperature (TSOIL_100cm monthly mean)")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.legend(loc="best")
    save(fig, out, f"{prefix}-magt-1m")


def load_climate_calibration():
    if not CALIBRATION_PATH.exists():
        return None
    return json.loads(CALIBRATION_PATH.read_text())


def resolve_climate_bias(args):
    if args.climate_bias is not None:
        return float(args.climate_bias)
    if ice_bracket_active(args):
        bracket_calib = load_bracket_climate_calibration()
        if bracket_calib and bracket_calib.get("selected_bias_C") is not None:
            return float(bracket_calib["selected_bias_C"])
    calib = load_climate_calibration()
    if calib and "selected_bias_C" in calib:
        return float(calib["selected_bias_C"])
    return float(_nsc.INLAND_TAIR_BIAS_C)


def prepare_climates(base, out, bias_c):
    obs_csv = OBS_DIR / "jones2024-north-slope-climate-monthly.csv"
    tag = f"{bias_c:.1f}".replace(".", "p")
    full_climate = out / f"north-slope-climate-full-{tag}.nc"
    tr_climate = out / f"north-slope-climate-tr-{tag}.nc"
    cache = out / "climate-cache"
    full_report = _nsc.make_full_north_slope_climate(
        Path(base["IO"]["hist_climate_file"]),
        full_climate,
        obs_csv,
        cache,
        inland_bias_c=bias_c,
    )
    tr_report = _nsc.make_tr_climate_from_obs(
        Path(base["IO"]["hist_climate_file"]),
        tr_climate,
        obs_csv,
        start_year=2007,
        nyears=PHASE1_TR_YEARS,
        inland_bias_c=bias_c,
    )
    co2_full = out / "north-slope-co2-full.nc"
    if not co2_full.exists():
        shutil.copy2(Path(base["IO"]["co2_file"]), co2_full)
    co2_tr = out / f"north-slope-co2-tr-{tag}.nc"
    make_co2_tr(co2_full, co2_tr, PHASE1_TR_START, PHASE1_TR_YEARS)
    return full_climate, tr_climate, co2_full, co2_tr, full_report, tr_report


def run_control_alt_probe(args, base, out, full_climate, tr_climate, co2_full, co2_tr,
                            eq_years, bias_c, reuse):
    """Unburned control transient without excess ice — ALT precondition probe."""
    tag = f"{bias_c:.1f}".replace(".", "p")
    probe_out = out / f"bias-{tag}"
    if probe_out.exists() and not reuse:
        shutil.rmtree(probe_out)
    probe_out.mkdir(parents=True, exist_ok=True)

    local = json.loads(json.dumps(base))
    copy_spatial(local, probe_out)
    spec = probe_out / "anaktuvuk-output-spec.csv"
    if not spec.exists():
        make_spec(ROOT / "config/output_spec.csv", spec)
    local["IO"]["output_spec_file"] = str(spec)

    source_fire = Path(local["IO"]["hist_exp_fire_file"])
    fire_off = probe_out / "no-fire.nc"
    make_fire(source_fire, fire_off)

    local["IO"]["hist_climate_file"] = str(full_climate)
    local["IO"]["co2_file"] = str(co2_full)
    init_name = "initialization"
    status = bgc.completed(probe_out, init_name) if reuse else None
    if status is None:
        status = bgc.run(
            args.binary.resolve(), probe_out, init_name,
            bgc.config(local, probe_out / init_name, output=False),
            ["--pr-yrs", "1", "--eq-yrs", str(eq_years)])

    initial = probe_out / init_name / "restart-eq.nc"
    local["IO"]["hist_climate_file"] = str(tr_climate)
    local["IO"]["co2_file"] = str(co2_tr)
    run_name = "control-alt-probe"
    run_status = bgc.completed(probe_out, run_name) if reuse else None
    if run_status is None:
        run_status = bgc.run(
            args.binary.resolve(), probe_out, run_name,
            config(local, probe_out / run_name, initial, fire_off),
            ["--tr-yrs", str(PHASE1_TR_YEARS)])

    alt = alt_summary_cm(probe_out / run_name, CONTROL_CELL, PHASE1_TR_YEARS)
    return {
        "bias_C": bias_c,
        "eq_years": eq_years,
        "mat_C": float(_nsc.BARROW_MONTHLY_TAIR.mean() + bias_c),
        "alt_max_control_cm": alt["max_cm"],
        "alt_mean_control_cm": alt["mean_cm"],
        "september_alt_cm": alt["september_cm"],
        "status": run_status,
    }


def run_calibrate_fire_snow(args, base, full_climate, tr_climate, co2_full, co2_tr,
                            climate_bias, reuse):
    """Pick fire severity so post-fire snow depth matches the unburned control."""
    out = ROOT / "experiments/thermokarst/anaktuvuk_fire_calibration_results"
    out = out.resolve()
    setup_out(out, reuse)

    local = json.loads(json.dumps(base))
    copy_spatial(local, out)
    spec = out / "anaktuvuk-output-spec.csv"
    if not spec.exists():
        make_spec(ROOT / "config/output_spec.csv", spec)
    local["IO"]["output_spec_file"] = str(spec)
    source_fire = Path(local["IO"]["hist_exp_fire_file"])
    fire_off = out / "no-fire.nc"
    make_fire(source_fire, fire_off)

    phase1_init = PHASE1_OUT / "initialization/restart-eq.nc"
    local["IO"]["hist_climate_file"] = str(full_climate)
    local["IO"]["co2_file"] = str(co2_full)
    init_name = "initialization"
    status = bgc.completed(out, init_name) if reuse else None
    if status is None:
        if phase1_init.exists() and args.reuse:
            out.joinpath(init_name).mkdir(parents=True, exist_ok=True)
            shutil.copy2(phase1_init, out / init_name / "restart-eq.nc")
            status = [100, 100]
        else:
            status = bgc.run(
                args.binary.resolve(), out, init_name,
                bgc.config(local, out / init_name, output=False),
                ["--pr-yrs", "1", "--eq-yrs", str(CAL_EQ_YEARS)])
    initial = out / init_name / "restart-eq.nc"
    injected = out / "restart-yedoma-ice.nc"
    if not injected.exists() or not reuse:
        bgc.inject_excess(
            initial, injected,
            fraction=PHASE1_ICE_FRACTION,
            top=PHASE1_ICE_TOP,
            bottom=PHASE1_ICE_BOTTOM)
    local["IO"]["hist_climate_file"] = str(tr_climate)
    local["IO"]["co2_file"] = str(co2_tr)

    results = []
    selected = None
    for severity in FIRE_SEVERITY_CANDIDATES:
        tag = f"sev{severity}"
        fire_on = out / f"fire-{tag}.nc"
        make_fire(source_fire, fire_on, FIRE_YEAR, PHASE1_FIRE_JDAY, severity=severity)
        probe_out = out / tag
        probe_out.mkdir(parents=True, exist_ok=True)
        for name, restart, fire in [
                ("control", injected, fire_off),
                ("burned", injected, fire_on)]:
            run_name = f"{tag}-{name}"
            run_status = bgc.completed(probe_out, run_name) if reuse else None
            if run_status is None:
                cfg = config(local, probe_out / run_name, restart, fire,
                             ice_top=PHASE1_ICE_TOP, ice_bottom=PHASE1_ICE_BOTTOM)
                run_status = bgc.run(
                    args.binary.resolve(), probe_out, run_name, cfg,
                    ["--tr-yrs", str(PHASE1_TR_YEARS)])

        paired = out / f"paired-{tag}"
        if paired.exists() and not reuse:
            shutil.rmtree(paired)
        paired.mkdir(parents=True, exist_ok=True)
        for name in ["control", "burned"]:
            src = probe_out / f"{tag}-{name}"
            dst = paired / name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        snow = snow_metrics(paired, PHASE1_TR_YEARS)
        burn = monthly(paired / "burned", "BURNTHICK")
        burn_depth = float(np.sum(burn[:, BURNED_CELL[0], BURNED_CELL[1]]))
        row = {
            "severity": severity,
            "post_fire_mean_snow_ratio": snow["post_fire_mean_ratio"],
            "post_fire_snow_ratios": snow["post_fire_winter_max_ratios"],
            "burn_depth_m": burn_depth,
            "snow_distance_from_unity": abs(snow["post_fire_mean_ratio"] - 1.0)
            if np.isfinite(snow["post_fire_mean_ratio"]) else float("inf"),
        }
        results.append(row)
        print(json.dumps(row, indent=2))
        in_band = (np.isfinite(snow["post_fire_mean_ratio"])
                   and SNOW_RATIO_MIN <= snow["post_fire_mean_ratio"] <= SNOW_RATIO_MAX)
        if in_band and burn_depth > 0.0:
            selected = row
            break

    if selected is None:
        eligible = [r for r in results if r["burn_depth_m"] > 0.0]
        if eligible:
            selected = min(eligible, key=lambda r: r["snow_distance_from_unity"])

    calib = {
        "climate_bias_C": climate_bias,
        "snow_ratio_band": [SNOW_RATIO_MIN, SNOW_RATIO_MAX],
        "candidates": FIRE_SEVERITY_CANDIDATES,
        "results": results,
        "selected_severity": selected["severity"] if selected else DEFAULT_FIRE_SEVERITY,
        "selected_post_fire_mean_snow_ratio":
            selected["post_fire_mean_snow_ratio"] if selected else None,
    }
    FIRE_CALIBRATION_PATH.write_text(json.dumps(json_safe(calib), indent=2) + "\n")
    (out / "fire-calibration.json").write_text(json.dumps(json_safe(calib), indent=2) + "\n")
    return calib


def run_hybrid_control_alt_probe(args, out, bias_c, reuse):
    """Control-only hybrid SP+TR from bridged spin-up — Jones-scale ALT probe."""
    tag = f"bias-{bias_c:.1f}".replace(".", "p")
    probe_out = out / tag
    if probe_out.exists() and not reuse:
        shutil.rmtree(probe_out)
    probe_out.mkdir(parents=True, exist_ok=True)

    spinup_dir = (args.spinup_dir or SPINUP_OUT).resolve()
    bridged = ensure_bridged_restart(spinup_dir)
    base = production.parse_json_with_comments(ROOT / "config/config.js")
    bgc.absolute_io(base)
    copy_spatial(base, probe_out)
    combined, co2_tr, tr_start_yr, _, _ = prepare_transient_climates(
        base, probe_out, bias_c, tr_end_year=ORGANIC_LAYER_END)

    spec = probe_out / "anaktuvuk-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec)
    base["IO"]["output_spec_file"] = str(spec)
    base["IO"]["hist_climate_file"] = str(combined)
    base["IO"]["co2_file"] = str(co2_tr)

    source_fire = Path(base["IO"]["hist_exp_fire_file"])
    fire_off = probe_out / "no-fire.nc"
    make_fire(source_fire, fire_off)

    run_name = "control"
    run_status = bgc.completed(probe_out, run_name) if reuse else None
    if run_status is None:
        run_status = bgc.run(
            args.binary.resolve(), probe_out, run_name,
            transient_config(base, probe_out / run_name, bridged, fire_off, tr_start_yr,
                             PHASE1_ICE_TOP, PHASE1_ICE_BOTTOM),
            ["--sp-yrs", str(TRANSIENT_SP_YEARS),
             "--tr-yrs", str(TRANSIENT_TR_YEARS)])

    iso = _dplots.isotherm_alt_metrics(probe_out / run_name, CONTROL_CELL, TRANSIENT_TR_YEARS)
    alt_max = iso["max_cm"] if iso else float("nan")
    return {
        "bias_C": bias_c,
        "alt_max_control_cm": alt_max,
        "alt_mean_control_cm": iso["mean_cm"] if iso else float("nan"),
        "distance_from_target_cm": abs(alt_max - ALT_BRACKET_TARGET_CM)
        if np.isfinite(alt_max) else float("inf"),
        "in_jones_range": (
            np.isfinite(alt_max)
            and ALT_MIN_CM <= alt_max <= ALT_JONES_MAX_CM
        ),
    }


def run_calibrate_climate_bracket(args):
    """Pick climate bias so hybrid control ALT is in Jones range (30–75 cm)."""
    out = (args.output or BRACKET_CLIMATE_CALIBRATION_OUT).resolve()
    setup_out(out, args.reuse)
    spinup_dir = (args.spinup_dir or SPINUP_OUT).resolve()
    if not spinup_restart_path(spinup_dir).exists():
        raise FileNotFoundError(
            f"Missing spin-up restart-sp.nc at {spinup_dir}; run --stage spinup first.")

    results = []
    selected = None
    for bias in CLIMATE_BIAS_CANDIDATES:
        row = run_hybrid_control_alt_probe(args, out, bias, reuse=args.reuse)
        results.append(row)
        print(json.dumps(row, indent=2))

    in_range = [r for r in results if r["in_jones_range"]]
    if in_range:
        selected = min(in_range, key=lambda r: r["distance_from_target_cm"])
    else:
        finite = [r for r in results if np.isfinite(r["alt_max_control_cm"])]
        if finite:
            selected = min(
                finite,
                key=lambda r: abs(r["alt_max_control_cm"] - ALT_BRACKET_TARGET_CM))

    calib = {
        "mode": "ice_bracket",
        "alt_min_cm": ALT_MIN_CM,
        "alt_jones_max_cm": ALT_JONES_MAX_CM,
        "alt_target_cm": ALT_BRACKET_TARGET_CM,
        "candidates_C": CLIMATE_BIAS_CANDIDATES,
        "workflow": "hybrid SP(20)+TR(24) control-only from restart-sp-tk-ready",
        "results": results,
        "selected_bias_C": selected["bias_C"] if selected else None,
        "selected_alt_max_control_cm": selected["alt_max_control_cm"] if selected else None,
        "note": (
            "Prefer control max 0 °C isotherm ALT in 30–75 cm (Jones coring); "
            "else closest to 55 cm target."
        ),
    }
    BRACKET_CLIMATE_CALIBRATION_PATH.write_text(
        json.dumps(json_safe(calib), indent=2) + "\n")
    (out / "bracket-climate-calibration.json").write_text(
        json.dumps(json_safe(calib), indent=2) + "\n")
    if selected is None:
        raise RuntimeError("No finite ALT from hybrid control probes")
    return calib


def run_calibrate_ice(args):
    """Sweep excess-ice top depth for LiDAR-window subsidence contrast."""
    bracket = ice_bracket_active(args)
    out = (args.output or (ICE_BRACKET_OUT if bracket else ICE_CALIBRATION_OUT)).resolve()
    setup_out(out, args.reuse)
    spinup_dir = (args.spinup_dir or SPINUP_OUT).resolve()
    if not spinup_restart_path(spinup_dir).exists():
        raise FileNotFoundError(
            f"Missing spin-up restart-sp.nc at {spinup_dir}; run --stage spinup first.")
    climate_bias = resolve_climate_bias(args)
    if bracket:
        ice_bottom = args.ice_bottom if args.ice_bottom is not None else ICE_BRACKET_BOTTOM_DEFAULT
        ice_fraction = (args.ice_fraction if args.ice_fraction is not None
                        else ICE_BRACKET_FRACTION_DEFAULT)
        top_candidates = ICE_TOP_BRACKET_CANDIDATES
    else:
        ice_bottom = args.ice_bottom if args.ice_bottom is not None else ICE_CALIB_BOTTOM
        ice_fraction = args.ice_fraction if args.ice_fraction is not None else ICE_CALIB_FRACTION
        top_candidates = ICE_TOP_CANDIDATES
    staged = staged_metrics_kwargs()

    results = []
    selected = None
    for ice_top in top_candidates:
        tag = f"top{int(round(ice_top * 100)):02d}"
        probe_out = out / tag
        probe_args = argparse.Namespace(**{
            **vars(args),
            "output": probe_out,
            "ice_top": ice_top,
            "ice_bottom": ice_bottom,
            "ice_fraction": ice_fraction,
            "ice_bracket": bracket,
            "max_organic_burn": True,
            "paired_only": True,
            "reuse": args.reuse,
            "climate_end_year": args.climate_end_year or ORGANIC_LAYER_END,
        })
        run_transient(probe_args)
        injected = probe_out / "restart-yedoma-ice.nc"
        initial_mass = _dplots.total_excess_ice_kg_m2(injected, BURNED_CELL)
        metrics = collect_metrics(
            probe_out, TRANSIENT_TR_YEARS, PHASE1_FIRE_JDAY,
            check_restart=False, **staged)
        contrast_cm = (metrics["lidar_epoch_b"] - metrics["lidar_epoch_c"]) * 100.0
        row = {
            "ice_top_m": ice_top,
            "ice_bottom_m": ice_bottom,
            "ice_fraction": ice_fraction,
            "initial_excess_kg_m2": initial_mass,
            "subsidence_2009_2014_burned_cm": metrics["lidar_epoch_b"] * 100.0,
            "subsidence_2009_2014_control_cm": metrics["lidar_epoch_c"] * 100.0,
            "subsidence_contrast_cm": contrast_cm,
            "tdd_ratio_2010_2014_mean": float(np.nanmean(metrics["early_ratios"])),
            "magt_1m_offset_last_year_C": metrics["magt_offset_last"],
            "alt_max_burned_cm": metrics["alt_max_burned_cm"],
            "alt_max_control_cm": metrics["alt_max_control_cm"],
            "alt_control_pre_fire_max_cm": metrics["alt_control_pre_fire_max_cm"],
            "alt_burned_post_fire_max_cm": metrics["alt_burned_post_fire_max_cm"],
            "alt_control_post_fire_max_cm": metrics["alt_control_post_fire_max_cm"],
        }
        row["bracket_score"] = bracket_ice_score(row, ice_top)
        results.append(row)
        print(json.dumps(row, indent=2))
        if bracket:
            if (row["bracket_score"] >= 5.0 and contrast_cm >= 5.0
                    and metrics["lidar_epoch_c"] < 0.05):
                selected = row
                break
        elif (contrast_cm >= 5.0 and metrics["lidar_epoch_c"] < 0.05
              and np.isfinite(contrast_cm)):
            selected = row
            break

    if selected is None:
        if bracket:
            eligible = [r for r in results if np.isfinite(r.get("bracket_score"))]
            if eligible:
                selected = max(eligible, key=lambda r: r["bracket_score"])
        else:
            eligible = [r for r in results if r["subsidence_contrast_cm"] > 0.0]
            if eligible:
                selected = max(eligible, key=lambda r: r["subsidence_contrast_cm"])

    default_top = ICE_BRACKET_TOP_DEFAULT if bracket else PHASE1_ICE_TOP
    calib = {
        "climate_bias_C": climate_bias,
        "mode": "ice_bracket" if bracket else "max_organic_burn",
        "ice_bottom_m": ice_bottom,
        "ice_fraction": ice_fraction,
        "candidates_top_m": top_candidates,
        "results": results,
        "selected_ice_top_m": selected["ice_top_m"] if selected else default_top,
        "selected_ice_bottom_m": ice_bottom,
        "selected_ice_fraction": ice_fraction,
        "selected_subsidence_contrast_cm":
            selected["subsidence_contrast_cm"] if selected else None,
        "selected_bracket_score": selected.get("bracket_score") if selected else None,
        "note": (
            "Thaw-depth bracket: ice top 0.40–0.60 m, max-organic-burn; "
            "score pre-fire ALT < ice_top, post-fire burned > ice_top, control < ice_top."
            if bracket else
            "Shallow ice band (top 0.15–0.30 m) with max-organic-burn transient; "
            "select first candidate with burned−control ≥ 5 cm and control < 5 cm, "
            "else maximize contrast."
        ),
    }
    ICE_CALIBRATION_PATH.write_text(json.dumps(json_safe(calib), indent=2) + "\n")
    (out / "ice-calibration.json").write_text(json.dumps(json_safe(calib), indent=2) + "\n")
    return calib


def run_calibrate_climate(args):
    out = (args.output or (ROOT / "experiments/thermokarst/anaktuvuk_climate_calibration_results"))
    out = out.resolve()
    setup_out(out, args.reuse)

    base = production.parse_json_with_comments(ROOT / "config/config.js")
    bgc.absolute_io(base)

    results = []
    selected = None
    for bias in CLIMATE_BIAS_CANDIDATES:
        full, tr, co2_full, co2_tr, _, tr_report = prepare_climates(base, out, bias)
        row = run_control_alt_probe(
            args, base, out, full, tr, co2_full, co2_tr,
            CAL_EQ_YEARS, bias, reuse=args.reuse)
        row["tr_mat_C"] = tr_report.mean_annual_tair_C
        results.append(row)
        print(json.dumps(row, indent=2))
        if np.isfinite(row["alt_max_control_cm"]) and row["alt_max_control_cm"] >= ALT_MIN_CM:
            selected = row
            break

    calib = {
        "alt_min_cm": ALT_MIN_CM,
        "eq_years_probe": CAL_EQ_YEARS,
        "candidates_C": CLIMATE_BIAS_CANDIDATES,
        "results": results,
        "selected_bias_C": selected["bias_C"] if selected else None,
        "selected_alt_max_control_cm": selected["alt_max_control_cm"] if selected else None,
    }
    CALIBRATION_PATH.write_text(json.dumps(json_safe(calib), indent=2) + "\n")
    (out / "climate-calibration.json").write_text(json.dumps(json_safe(calib), indent=2) + "\n")

    if selected is None:
        raise RuntimeError(
            f"No climate bias in {CLIMATE_BIAS_CANDIDATES} yielded control ALT >= {ALT_MIN_CM} cm")
    return calib


def run_phase0(args):
    out = args.output.resolve()
    setup_out(out, args.reuse)
    probe = fire_topo.compile_probe(out)
    base = production.parse_json_with_comments(ROOT / "config/config.js")
    bgc.absolute_io(base)
    copy_spatial(base, out)

    climate_path = out / "anaktuvuk-north-slope-climate.nc"
    weather = make_phase0_climate(
        Path(base["IO"]["hist_climate_file"]), climate_path, PHASE0_TR_YEARS)
    base["IO"]["hist_climate_file"] = str(climate_path)

    spec = out / "anaktuvuk-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec)
    base["IO"]["output_spec_file"] = str(spec)

    source_fire = Path(base["IO"]["hist_exp_fire_file"])
    fire_on = out / "anaktuvuk-fire-2007.nc"
    fire_off = out / "no-fire.nc"
    make_fire(source_fire, fire_on, FIRE_YEAR, PHASE0_FIRE_JDAY)
    make_fire(source_fire, fire_off)

    init_status = ensure_initialization(
        args, out, base, PHASE0_EQ_YEARS, args.reuse)
    initial = out / "initialization/restart-eq.nc"
    injected = out / "restart-with-excess.nc"
    added = bgc.inject_excess(
        initial, injected,
        fraction=PHASE0_ICE_FRACTION, top=PHASE0_ICE_TOP, bottom=PHASE0_ICE_BOTTOM)
    run_status = run_transient_runs(
        args, out, base, initial, injected, fire_on, fire_off,
        PHASE0_TR_YEARS, PHASE0_ICE_TOP, PHASE0_ICE_BOTTOM,
        ice_on_both=False, reuse=args.reuse)
    statuses = {**init_status, **run_status}

    control_added = {str(CONTROL_CELL): 0.0}
    metrics = collect_metrics(out, PHASE0_TR_YEARS, PHASE0_FIRE_JDAY)
    checks = []

    gate(checks, "synthetic fire water closure", abs(probe["water_residual_kg_m2"]),
         "<=1e-12 kg m-2", abs(probe["water_residual_kg_m2"]) <= 1e-12, hard=True)
    gate(checks, "synthetic fire energy closure", abs(probe["energy_residual_J_m2"]),
         "<=1e-6 J m-2", abs(probe["energy_residual_J_m2"]) <= 1e-6, hard=True)
    gate(checks, "production completion", statuses, "both cells status 100",
         all(v == [100, 100] for v in statuses.values()), hard=True)
    gate(checks, "North Slope climate variation", weather["year_to_year_tair_range_C"],
         ">0.05 C among TR years", weather["year_to_year_tair_range_C"] > 0.05)
    gate(checks, "fire-year subsidence on burned cell", metrics["fire_year_b"],
         ">=5 mm in TR year 0 (2007)", metrics["fire_year_b"] >= 0.005)
    gate(checks, "fire-year burned exceeds control",
         metrics["fire_year_b"] - metrics["fire_year_c"],
         ">5 mm more than control in 2007",
         (metrics["fire_year_b"] - metrics["fire_year_c"]) > 0.005)
    gate(checks, "control cell unburned",
         float(np.sum(metrics["burn"][:, CONTROL_CELL[0], CONTROL_CELL[1]])),
         "0 m burn depth",
         float(np.sum(metrics["burn"][:, CONTROL_CELL[0], CONTROL_CELL[1]])) < 1e-9)
    gate(checks, "burned minus control cumulative subsidence at 2014",
         metrics["primary_b"] - metrics["primary_c"],
         ">5 mm by end of 2014", (metrics["primary_b"] - metrics["primary_c"]) > 0.005)
    gate(checks, "control cumulative subsidence at 2014", metrics["primary_c"],
         "<1 cm without fire (soft Phase 0)", metrics["primary_c"] < 0.01)
    gate(checks, "burned cumulative subsidence at 2014", metrics["primary_b"],
         ">1 cm (soft Phase 0)", metrics["primary_b"] > 0.01)
    gate(checks, "1 m MAGT offset finite by 2021", metrics["magt_offset_last"],
         "finite diagnostic", np.isfinite(metrics["magt_offset_last"]))
    gate(checks, "stabilization slowdown", metrics["stabilization_ratio"],
         "2014-2021 / 2009-2014 <0.75 on burned cell (soft)",
         np.isfinite(metrics["stabilization_ratio"]) and metrics["stabilization_ratio"] < 0.75)
    gate(checks, "restart geometry", max(metrics["diffs"].values()),
         "<=0.15 m with dsl (Phase 0 soft)", max(metrics["diffs"].values()) <= 0.15)
    gate(checks, "restart subsidence endpoint", metrics["sub_end_diff"],
         "<=2e-4 m (Phase 0 soft)", metrics["sub_end_diff"] <= 2e-4)
    gate(checks, "restart subsidence daily max", metrics["sub_resume_diff"],
         "<=5e-4 m thaw-season lag", metrics["sub_resume_diff"] <= 5e-4)

    summary = {
        "phase": 0,
        "experiment": "anaktuvuk_phase0",
        "calendar": {
            "tr_year_0": 2007,
            "fire_jday": PHASE0_FIRE_JDAY,
            "primary_window_tr_years": [PRIMARY_START, PRIMARY_END],
            "stabilization_window_tr_years": [STAB_START, STAB_END],
        },
        "weather": weather,
        "ice_injection": {
            "fraction": PHASE0_ICE_FRACTION,
            "top_m": PHASE0_ICE_TOP,
            "bottom_m": PHASE0_ICE_BOTTOM,
            "added_kg_m2_burned_cell": added[str(BURNED_CELL)],
            "control_restart": "no excess-ice injection (unburned paired column)",
        },
        "probe": probe,
        "statuses": statuses,
        "contrasts": {
            "subsidence_fire_year_burned_minus_control_m":
                metrics["fire_year_b"] - metrics["fire_year_c"],
            "subsidence_cumulative_2014_burned_minus_control_m":
                metrics["primary_b"] - metrics["primary_c"],
            "subsidence_increment_2009_2014_burned_minus_control_m":
                metrics["lidar_epoch_b"] - metrics["lidar_epoch_c"],
            "subsidence_increment_2014_2021_burned_minus_control_m":
                metrics["stab_b"] - metrics["stab_c"],
            "stabilization_ratio_burned": metrics["stabilization_ratio"],
            "obs_early_tdd_ratio_mean": metrics["obs_early_tdd_mean"],
            "early_t30_offset_C": metrics["early_t30_b"] - metrics["early_t30_c"],
            "late_t30_offset_C": metrics["late_t30_b"] - metrics["late_t30_c"],
            "magt_1m_offset_last_year_C": metrics["magt_offset_last"],
            "thaw_penetration_2021_cm": metrics["thaw_pen_2021_cm"],
        },
        "restart_max_difference": metrics["diffs"],
        "restart_inventory_relative_difference": metrics["inventory_relative"],
        "restart_subsidence_difference_m": metrics["sub_resume_diff"],
        "restart_subsidence_endpoint_difference_m": metrics["sub_end_diff"],
        "checks_passed": sum(x["status"] == "PASS" for x in checks),
        "checks_total": len(checks),
    }
    (out / "summary.json").write_text(json.dumps(json_safe(summary), indent=2) + "\n")
    write_checks(out, checks)
    write_figures(out, metrics, PHASE0_TR_YEARS, PHASE0_FIRE_JDAY, 0)
    if _dplots._etp.has_profile_outputs(out / "burned"):
        _dplots.generate_diagnostic_figures(
            out, tr_years=PHASE0_TR_YEARS, start_year=2007,
            fire_jday=PHASE0_FIRE_JDAY, restart=out / "restart-with-excess.nc",
            prefix="anaktuvuk", copy_to_report=True)
    return summary, checks


def run_phase1(args):
    out = args.output.resolve()
    setup_out(out, args.reuse)
    spinup_dir = (args.spinup_dir or SPINUP_OUT).resolve()
    if not spinup_restart_path(spinup_dir).exists():
        print(f"Spin-up restart missing; running Stage A in {spinup_dir}", file=sys.stderr)
        spin_args = argparse.Namespace(**{**vars(args), "output": spinup_dir})
        run_spinup(spin_args)

    tr_summary = run_transient(args)
    probe = fire_topo.compile_probe(out)
    climate_bias = resolve_climate_bias(args)
    tr_end_year = args.climate_end_year or ORGANIC_LAYER_END
    fire_severity = resolve_fire_severity(args)
    ice_fraction = resolve_ice_fraction(args)
    ice_top = resolve_ice_top(args)
    ice_bottom = resolve_ice_bottom(args)
    fig_prefix = figure_prefix(args)
    injected = out / "restart-yedoma-ice.nc"
    added = tr_summary.get("ice_injection", {}).get("added_kg_m2_both_cells", {})
    if not added and injected.exists():
        with Dataset(injected) as dataset:
            added = {
                str(BURNED_CELL): float(np.sum(dataset["TKexcess"][BURNED_CELL])),
                str(CONTROL_CELL): float(np.sum(dataset["TKexcess"][CONTROL_CELL])),
            }

    weather = {
        "source": "North Slope monthly obs + seasonal SP block",
        "climate_bias_C": climate_bias,
        "tr_window": {
            "start_year": TRANSIENT_TR_CALENDAR_START,
            "years": TRANSIENT_TR_YEARS,
            "end_year": tr_end_year,
        },
        "sp_years": TRANSIENT_SP_YEARS,
        "spinup": {
            "mode": "hybrid",
            "thermokarst_during_spinup": SPINUP_THERMOKARST,
            "pr_years": SPINUP_PR_YEARS,
            "eq_years": SPINUP_EQ_YEARS,
            "sp_years": SPINUP_SP_YEARS,
            "restart_sp": str(spinup_restart_path(spinup_dir)),
            "restart_sp_tk_ready": str(bridged_restart_path(spinup_dir)),
        },
        "transient_climate": tr_summary.get("climate", {}),
    }
    if load_climate_calibration():
        weather["climate_calibration"] = load_climate_calibration()
    if ice_bracket_active(args) and load_bracket_climate_calibration():
        weather["bracket_climate_calibration"] = load_bracket_climate_calibration()

    statuses = tr_summary.get("statuses", {})
    staged = staged_metrics_kwargs()
    metrics = collect_metrics(
        out, TRANSIENT_TR_YEARS, PHASE1_FIRE_JDAY, **staged)
    contrast_lidar = metrics["lidar_epoch_b"] - metrics["lidar_epoch_c"]
    early_tdd_mean = float(np.mean(metrics["early_ratios"])) if metrics["early_ratios"] else float("nan")
    late_tdd_mean = float(np.mean(metrics["late_ratios"])) if metrics["late_ratios"] else float("nan")

    checks = []
    gate(checks, "synthetic fire water closure", abs(probe["water_residual_kg_m2"]),
         "<=1e-12 kg m-2", abs(probe["water_residual_kg_m2"]) <= 1e-12, hard=True)
    gate(checks, "synthetic fire energy closure", abs(probe["energy_residual_J_m2"]),
         "<=1e-6 J m-2", abs(probe["energy_residual_J_m2"]) <= 1e-6, hard=True)
    gate(checks, "production completion", statuses, "both cells status 100",
         all(v == [100, 100] for v in statuses.values()), hard=True)
    gate(checks, "North Slope climate window",
         weather["tr_window"],
         f"{TRANSIENT_TR_CALENDAR_START}–{tr_end_year} TR + {TRANSIENT_SP_YEARS} yr seasonal SP",
         True)
    gate(checks, "identical Yedoma ice on both cells",
         {str(c): added[str(c)] for c in CELLS},
         f"same band {ice_top:.2f}–{ice_bottom:.2f} m",
         abs(added[str(BURNED_CELL)] - added[str(CONTROL_CELL)]) < 1.0)
    gate(checks, "ALT precondition (control max, 0 °C isotherm)",
         metrics["alt_max_control_cm"],
         f">= {ALT_MIN_CM:.0f} cm (TLAYER) before ALT/subsidence calibration",
         np.isfinite(metrics["alt_max_control_cm"])
         and metrics["alt_max_control_cm"] >= ALT_MIN_CM,
         hard=True)
    gate(checks, "control cell unburned",
         float(np.sum(metrics["burn"][:, CONTROL_CELL[0], CONTROL_CELL[1]])),
         "0 m burn depth",
         float(np.sum(metrics["burn"][:, CONTROL_CELL[0], CONTROL_CELL[1]])) < 1e-9)
    if max_organic_burn_active(args):
        gate(checks, "post-fire snow depth burned/control",
             metrics["snow"]["post_fire_mean_ratio"],
             "informational only (max-organic-burn mode; snow pairing gate relaxed)",
             np.isfinite(metrics["snow"]["post_fire_mean_ratio"]))
        gate(checks, "organic burn depth (max-organic-burn)",
             metrics["burn_depth"],
             ">= 0.08 m cumulative BURNTHICK (soft)",
             metrics["burn_depth"] >= 0.08)
    else:
        gate(checks, "post-fire snow depth burned/control",
             metrics["snow"]["post_fire_mean_ratio"],
             f"{SNOW_RATIO_MIN:.2f}–{SNOW_RATIO_MAX:.2f} (seasonal peak, TR years 1+)",
             np.isfinite(metrics["snow"]["post_fire_mean_ratio"])
             and SNOW_RATIO_MIN <= metrics["snow"]["post_fire_mean_ratio"] <= SNOW_RATIO_MAX,
             hard=True)
    gate(checks, "burned minus control subsidence 2009–2014",
         contrast_lidar * 100.0,
         "10–35 cm (soft Phase 1)",
         0.10 <= contrast_lidar <= 0.35)
    gate(checks, "control subsidence 2009–2014",
         metrics["lidar_epoch_c"] * 100.0,
         "<5 cm (soft Phase 1)",
         metrics["lidar_epoch_c"] < 0.05)
    gate(checks, "TDD ratio 2010–2014 mean", early_tdd_mean,
         ">2.0 (soft Phase 1)", np.isfinite(early_tdd_mean) and early_tdd_mean > 2.0)
    gate(checks, "TDD ratio 2019–2021 mean", late_tdd_mean,
         "1.1–1.5 (soft Phase 1)",
         np.isfinite(late_tdd_mean) and 1.1 <= late_tdd_mean <= 1.5)
    gate(checks, "MAGT offset 1 m (last TR year)", metrics["magt_offset_last"],
         "0.4–1.0 °C (soft Phase 1)",
         np.isfinite(metrics["magt_offset_last"])
         and 0.4 <= metrics["magt_offset_last"] <= 1.0)
    gate(checks, "thaw penetration 2021", metrics["thaw_pen_2021_cm"],
         "45–75 cm (soft Phase 1)",
         np.isfinite(metrics["thaw_pen_2021_cm"])
         and 45.0 <= metrics["thaw_pen_2021_cm"] <= 75.0)
    if ice_bracket_active(args):
        ice_top_cm = ice_top * 100.0
        gate(checks, "bracket: pre-fire ALT below ice top (control)",
             metrics["alt_control_pre_fire_max_cm"],
             f"< {ice_top_cm:.0f} cm (soft)",
             np.isfinite(metrics["alt_control_pre_fire_max_cm"])
             and metrics["alt_control_pre_fire_max_cm"] < ice_top_cm)
        gate(checks, "bracket: post-fire burned ALT exceeds ice top",
             metrics["alt_burned_post_fire_max_cm"],
             f"> {ice_top_cm:.0f} cm (soft)",
             np.isfinite(metrics["alt_burned_post_fire_max_cm"])
             and metrics["alt_burned_post_fire_max_cm"] > ice_top_cm)
        gate(checks, "bracket: post-fire control ALT below ice top",
             metrics["alt_control_post_fire_max_cm"],
             f"< {ice_top_cm:.0f} cm (soft)",
             np.isfinite(metrics["alt_control_post_fire_max_cm"])
             and metrics["alt_control_post_fire_max_cm"] < ice_top_cm)
        gate(checks, "bracket: control max ALT in Jones range",
             metrics["alt_max_control_cm"],
             f"{ALT_MIN_CM:.0f}–{ALT_JONES_MAX_CM:.0f} cm (soft)",
             np.isfinite(metrics["alt_max_control_cm"])
             and ALT_MIN_CM <= metrics["alt_max_control_cm"] <= ALT_JONES_MAX_CM)
    if metrics["diffs"]:
        gate(checks, "restart geometry", max(metrics["diffs"].values()),
             "<=0.15 m with dsl", max(metrics["diffs"].values()) <= 0.15, hard=True)
        gate(checks, "restart subsidence endpoint", metrics["sub_end_diff"],
             "<=1e-4 m", metrics["sub_end_diff"] <= 1e-4, hard=True)

    summary = {
        "phase": 1,
        "experiment": "anaktuvuk_phase1",
        "staging": "spinup_sp_transient",
        "calendar": {
            "tr_year_0": TRANSIENT_TR_CALENDAR_START,
            "fire_tr_year": TRANSIENT_FIRE_TR_YEAR,
            "fire_jday": PHASE1_FIRE_JDAY,
            "primary_window_tr_years": [TRANSIENT_PRIMARY_START, TRANSIENT_PRIMARY_END],
            "stabilization_window_tr_years": [TRANSIENT_STAB_START, TRANSIENT_STAB_END],
        },
        "weather": weather,
        "ice_injection": {
            "fraction": ice_fraction,
            "top_m": ice_top,
            "bottom_m": ice_bottom,
            "added_kg_m2_both_cells": added,
            "control_restart": "identical Yedoma excess-ice inventory",
        },
        "spinup_years": {
            "pr": SPINUP_PR_YEARS,
            "eq": SPINUP_EQ_YEARS,
            "sp": SPINUP_SP_YEARS,
        },
        "transient_years": {"sp": TRANSIENT_SP_YEARS, "tr": TRANSIENT_TR_YEARS},
        "fire_severity": fire_severity,
        "fire_calibration": None if max_organic_burn_active(args) else load_fire_calibration(),
        "ice_bracket": ice_bracket_active(args),
        "max_organic_burn": tr_summary.get("max_organic_burn"),
        "probe": probe,
        "statuses": statuses,
        "transient_summary": tr_summary,
        "contrasts": {
            "subsidence_increment_2009_2014_burned_m": metrics["lidar_epoch_b"],
            "subsidence_increment_2009_2014_control_m": metrics["lidar_epoch_c"],
            "subsidence_increment_2009_2014_burned_minus_control_m": contrast_lidar,
            "subsidence_increment_2014_2021_burned_minus_control_m":
                metrics["stab_b"] - metrics["stab_c"],
            "stabilization_ratio_burned": metrics["stabilization_ratio"],
            "tdd_ratio_2010_2014_mean": early_tdd_mean,
            "tdd_ratio_2019_2021_mean": late_tdd_mean,
            "obs_early_tdd_ratio_mean": metrics["obs_early_tdd_mean"],
            "magt_1m_offset_last_year_C": metrics["magt_offset_last"],
            "thaw_penetration_2021_cm": metrics["thaw_pen_2021_cm"],
            "thaw_front_max_2021_cm": metrics["thaw_front_2021_cm"],
            "alt_max_control_cm": metrics["alt_max_control_cm"],
            "alt_max_burned_cm": metrics["alt_max_burned_cm"],
            "alt_method": metrics["alt_method"],
            "alt_control_pre_fire_max_cm": metrics["alt_control_pre_fire_max_cm"],
            "alt_burned_post_fire_max_cm": metrics["alt_burned_post_fire_max_cm"],
            "alt_control_post_fire_max_cm": metrics["alt_control_post_fire_max_cm"],
            "climate_bias_C": climate_bias,
            "post_fire_mean_snow_ratio": metrics["snow"]["post_fire_mean_ratio"],
        },
        "restart_max_difference": metrics["diffs"],
        "restart_inventory_relative_difference": metrics["inventory_relative"],
        "restart_subsidence_difference_m": metrics["sub_resume_diff"],
        "restart_subsidence_endpoint_difference_m": metrics["sub_end_diff"],
        "checks_passed": sum(x["status"] == "PASS" for x in checks),
        "checks_total": len(checks),
    }
    (out / "summary.json").write_text(json.dumps(json_safe(summary), indent=2) + "\n")
    write_checks(out, checks)
    figure_kwargs = {k: staged[k] for k in (
        "calendar_start", "fire_tr_year", "primary_start", "primary_end",
        "stab_start", "stab_end") if k in staged}
    write_figures(
        out, metrics, TRANSIENT_TR_YEARS, PHASE1_FIRE_JDAY, 1,
        prefix=fig_prefix, **figure_kwargs)
    tag = f"{climate_bias:.1f}".replace(".", "p")
    seasonal = out / f"anaktuvuk-seasonal-climate-{TRANSIENT_SP_YEARS}y-{tag}.nc"
    tr_only = out / f"north-slope-climate-tr-{tag}.nc"
    diag_stems = _dplots.generate_diagnostic_figures(
        out, tr_years=TRANSIENT_TR_YEARS,
        start_year=TRANSIENT_TR_CALENDAR_START,
        tr_end_year=tr_end_year,
        fire_jday=PHASE1_FIRE_JDAY, fire_year=2007,
        bias_c=climate_bias, restart=injected,
        full_climate=seasonal if seasonal.exists() else None,
        tr_climate=tr_only if tr_only.exists() else None,
        profile_probe_dir=out,
        profile_start_year=TRANSIENT_TR_CALENDAR_START,
        profile_tr_years=TRANSIENT_TR_YEARS,
        plot_start_year=TRANSIENT_TR_CALENDAR_START,
        prefix=fig_prefix, copy_to_report=True)
    summary["diagnostic_figures"] = diag_stems
    (out / "summary.json").write_text(json.dumps(json_safe(summary), indent=2) + "\n")
    return summary, checks


def collect_phase2_metrics(out, run_name, tr_years):
    sub = bgc.read_daily(out / run_name, "TKSUBSIDENCE")
    burn = monthly(out / run_name, "BURNTHICK")
    veg = bgc.read_yearly(out / run_name, "VEGC")
    cells = {}
    for cell, meta in PHASE2_CELL_META.items():
        y, x = cell
        lidar_m = subsidence_window(sub, cell, PRIMARY_START, PRIMARY_END)
        stab_m = subsidence_window(sub, cell, STAB_START, STAB_END)
        veg_series = [float(veg[year, y, x]) for year in range(min(tr_years, veg.shape[0]))]
        cells[meta["role"]] = {
            "cell": list(cell),
            "lidar_epoch_cm": lidar_m * 100.0,
            "stab_epoch_cm": stab_m * 100.0,
            "cumulative_2014_cm": cumulative_at_year(sub, cell, PRIMARY_END) * 100.0,
            "burn_depth_m": float(np.sum(burn[:, y, x])),
            "veg_series_g_m2": veg_series,
            "veg_2010_g_m2": float(veg[3, y, x]) if veg.shape[0] > 3 else float("nan"),
            "veg_2021_g_m2": float(veg[tr_years - 1, y, x]),
        }
    upland = cells["upland_burned"]
    stab_ratio = (upland["stab_epoch_cm"] / upland["lidar_epoch_cm"]
                  if upland["lidar_epoch_cm"] > 1.0 else float("nan"))
    return cells, stab_ratio


def spinup_restart_path(out=None):
    root = (out or SPINUP_OUT).resolve()
    canonical = root / "restart-sp.nc"
    if canonical.exists():
        return canonical
    nested = root / "spinup" / "restart-sp.nc"
    if nested.exists():
        return nested
    return canonical


def bridged_restart_path(out=None):
    root = (out or SPINUP_OUT).resolve()
    return root / "restart-sp-tk-ready.nc"


def ensure_bridged_restart(spinup_dir):
    """Return thermokarst-ready restart, rebuilding when spin-up is newer."""
    spinup_dir = spinup_dir.resolve()
    source = spinup_restart_path(spinup_dir)
    if not source.exists():
        raise FileNotFoundError(f"Missing spin-up restart-sp.nc at {source}")
    dest = bridged_restart_path(spinup_dir)
    if dest.exists() and dest.stat().st_mtime >= source.stat().st_mtime:
        return dest
    prepare_thermokarst_restart(source, dest)
    return dest


def prepare_transient_climates(base, out, bias_c, tr_end_year=ORGANIC_LAYER_END,
                             winter_precip_scale=WINTER_PRECIP_SCALE):
    """Build 24-yr TR, seasonal climatology, combined SP+TR hist file, and CO₂ slice."""
    obs_csv = OBS_DIR / "jones2024-north-slope-climate-monthly.csv"
    _nsc.append_obs_years_from_ncei(
        obs_csv, out / "climate-cache", start_year=2022, end_year=tr_end_year)
    tag = f"{bias_c:.1f}".replace(".", "p")
    template = Path(base["IO"]["hist_climate_file"])
    tr_only = out / f"north-slope-climate-tr-{tag}.nc"
    _nsc.make_tr_climate_from_obs(
        template, tr_only, obs_csv,
        start_year=TRANSIENT_TR_CALENDAR_START,
        nyears=TRANSIENT_TR_YEARS, inland_bias_c=bias_c,
        winter_precip_scale=winter_precip_scale)
    seasonal_only = out / f"anaktuvuk-seasonal-climate-{TRANSIENT_SP_YEARS}y-{tag}.nc"
    combined = out / f"anaktuvuk-transient-climate-{tag}.nc"
    clim = _nsc.monthly_climatology_from_tr(tr_only, TRANSIENT_TR_YEARS)
    _nsc.make_repeated_seasonal_climate(
        template, seasonal_only, clim, TRANSIENT_SP_YEARS)
    _, clim, tr_start_yr = _nsc.make_combined_transient_climate(
        template, combined, tr_only,
        seasonal_repeat_years=TRANSIENT_SP_YEARS, tr_years=TRANSIENT_TR_YEARS)
    figure = out / "anaktuvuk-seasonal-forcing"
    _nsc.plot_seasonal_forcing(
        clim, figure,
        title=("Anaktuvuk seasonal mean forcing "
               f"({TRANSIENT_TR_YEARS}-yr TR average, {TRANSIENT_TR_CALENDAR_START}–"
               f"{tr_end_year})"))
    co2_full = out / "north-slope-co2-full.nc"
    if not co2_full.exists():
        co2_full = Path(base["IO"]["co2_file"])
    co2_tr = out / f"anaktuvuk-transient-co2-{tag}.nc"
    total_years = TRANSIENT_SP_YEARS + TRANSIENT_TR_YEARS
    make_co2_tr(co2_full, co2_tr, TRANSIENT_TR_CALENDAR_START - 1901, total_years)
    report = {
        "tr_climate": str(tr_only),
        "seasonal_climate": str(seasonal_only),
        "combined_climate": str(combined),
        "tr_start_yr": tr_start_yr,
        "winter_precip_scale": winter_precip_scale,
        "target_peak_snow_depth_cm": TARGET_PEAK_SNOW_DEPTH_CM,
        "seasonal_figure": str(figure.with_suffix(".png")),
        "co2_transient": str(co2_tr),
    }
    (out / "transient-climate-build.json").write_text(json.dumps(report, indent=2) + "\n")
    return combined, co2_tr, tr_start_yr, clim, report


def run_spinup(args):
    """One-time PR+EQ+SP spin-up; saves restart-sp.nc for all later transient runs."""
    out = (args.output or SPINUP_OUT).resolve()
    out.mkdir(parents=True, exist_ok=True)
    base = production.parse_json_with_comments(ROOT / "config/config.js")
    bgc.absolute_io(base)
    copy_spatial(base, out)
    bias_c = resolve_climate_bias(args)
    full_climate, _, co2_full, _, _, _ = prepare_climates(base, out, bias_c)
    base["IO"]["hist_climate_file"] = str(full_climate)
    base["IO"]["co2_file"] = str(co2_full)
    fire_off = out / "no-fire.nc"
    make_fire(Path(base["IO"]["hist_exp_fire_file"]), fire_off)

    run_name = "spinup"
    status = bgc.completed(out, run_name) if args.reuse else None
    if status is None:
        status = bgc.run(
            args.binary.resolve(), out, run_name,
            spinup_config(base, out / run_name),
            ["--pr-yrs", str(SPINUP_PR_YEARS),
             "--eq-yrs", str(SPINUP_EQ_YEARS),
             "--sp-yrs", str(SPINUP_SP_YEARS)])
    restart = out / run_name / "restart-sp.nc"
    if not restart.exists():
        raise FileNotFoundError(f"Spin-up did not write restart-sp.nc: {restart}")
    canonical = out / "restart-sp.nc"
    if restart.resolve() != canonical.resolve():
        shutil.copy2(restart, canonical)
    bridged = ensure_bridged_restart(out)
    summary = {
        "stage": "spinup",
        "mode": "hybrid",
        "thermokarst_during_spinup": SPINUP_THERMOKARST,
        "pr_years": SPINUP_PR_YEARS,
        "eq_years": SPINUP_EQ_YEARS,
        "sp_years": SPINUP_SP_YEARS,
        "restart_sp": str(canonical),
        "restart_sp_tk_ready": str(bridged),
        "status": status,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def transient_config(base, directory, restart, fire_file, tr_start_yr, ice_top, ice_bottom):
    cfg = config(base, directory, restart, fire_file, tr_start=tr_start_yr,
                 ice_top=ice_top, ice_bottom=ice_bottom)
    cfg["IO"]["output_nc_sp"] = 1
    cfg["stage_settings"]["tr_start_yr"] = int(tr_start_yr)
    cfg["stage_settings"]["eq"]["baseline"] = True
    return cfg


def run_transient(args):
    """Transient-only paired run: restart-sp → bridge → ice inject → SP(20) + TR(24)."""
    out = (args.output or PHASE1_OUT).resolve()
    out.mkdir(parents=True, exist_ok=True)
    spinup_dir = (args.spinup_dir or SPINUP_OUT).resolve()
    restart_sp = spinup_restart_path(spinup_dir)
    if not restart_sp.exists():
        raise FileNotFoundError(
            f"Missing spin-up restart-sp.nc at {restart_sp}; run --stage spinup first.")
    bridged = ensure_bridged_restart(spinup_dir)

    base = production.parse_json_with_comments(ROOT / "config/config.js")
    bgc.absolute_io(base)
    max_organic_burn = apply_max_organic_burn_parameters(base, args, out)
    copy_spatial(base, out)
    bias_c = resolve_climate_bias(args)
    tr_end_year = args.climate_end_year or ORGANIC_LAYER_END
    winter_scale = (args.winter_precip_scale if args.winter_precip_scale is not None
                    else WINTER_PRECIP_SCALE)
    combined, co2_tr, tr_start_yr, _, climate_report = prepare_transient_climates(
        base, out, bias_c, tr_end_year=tr_end_year,
        winter_precip_scale=winter_scale)

    spec = out / "anaktuvuk-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec)
    base["IO"]["output_spec_file"] = str(spec)
    base["IO"]["hist_climate_file"] = str(combined)
    base["IO"]["co2_file"] = str(co2_tr)

    source_fire = Path(base["IO"]["hist_exp_fire_file"])
    fire_off = out / "no-fire.nc"
    make_fire(source_fire, fire_off)
    fire_severity = resolve_fire_severity(args)
    fire_on = out / "anaktuvuk-fire-2007.nc"
    # Explicit fire indices match combined-climate year indices (SP block + TR slice).
    fire_climate_index = tr_start_yr + TRANSIENT_FIRE_TR_YEAR
    make_fire(source_fire, fire_on, fire_climate_index, PHASE1_FIRE_JDAY,
              severity=fire_severity)

    ice_fraction = resolve_ice_fraction(args)
    ice_top = resolve_ice_top(args)
    ice_bottom = resolve_ice_bottom(args)
    injected = out / "restart-yedoma-ice.nc"
    added = bgc.inject_excess(
        bridged, injected,
        fraction=ice_fraction, top=ice_top, bottom=ice_bottom)

    statuses = {}
    for name, fire in [("control", fire_off), ("burned", fire_on)]:
        statuses[name] = bgc.completed(out, name) if args.reuse else None
        if statuses[name] is None:
            statuses[name] = bgc.run(
                args.binary.resolve(), out, name,
                transient_config(base, out / name, injected, fire, tr_start_yr,
                                 ice_top, ice_bottom),
                ["--sp-yrs", str(TRANSIENT_SP_YEARS),
                 "--tr-yrs", str(TRANSIENT_TR_YEARS)])

    if not args.paired_only:
        split = TRANSIENT_RESTART_SPLIT
        statuses["split-first"] = bgc.completed(out, "split-first") if args.reuse else None
        if statuses["split-first"] is None:
            statuses["split-first"] = bgc.run(
                args.binary.resolve(), out, "split-first",
                transient_config(base, out / "split-first", injected, fire_on, tr_start_yr,
                                 ice_top, ice_bottom),
                ["--sp-yrs", str(TRANSIENT_SP_YEARS),
                 "--tr-yrs", str(split)])
        statuses["resumed"] = bgc.completed(out, "resumed") if args.reuse else None
        if statuses["resumed"] is None:
            resumed_cfg = transient_config(
                base, out / "resumed", out / "split-first/restart-tr.nc", fire_on,
                tr_start_yr + split, ice_top, ice_bottom)
            statuses["resumed"] = bgc.run(
                args.binary.resolve(), out, "resumed", resumed_cfg,
                ["--tr-yrs", str(TRANSIENT_TR_YEARS - split)])

    summary = {
        "stage": "transient",
        "spinup_restart": str(restart_sp),
        "bridged_restart": str(bridged),
        "sp_years": TRANSIENT_SP_YEARS,
        "tr_years": TRANSIENT_TR_YEARS,
        "tr_start_yr": tr_start_yr,
        "fire_climate_index": fire_climate_index,
        "tr_calendar": f"{TRANSIENT_TR_CALENDAR_START}–{tr_end_year}",
        "climate": climate_report,
        "ice_injection": {
            "fraction": ice_fraction,
            "top_m": ice_top,
            "bottom_m": ice_bottom,
            "added_kg_m2_both_cells": added,
        },
        "statuses": statuses,
    }
    if max_organic_burn:
        summary["max_organic_burn"] = max_organic_burn
        summary["fire_severity"] = fire_severity
    (out / "transient-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def ensure_organic_layer_probe(args, out, bias_c, end_year=ORGANIC_LAYER_END, reuse=False):
    """Paired control/burned transient (2000+) with LAYERTYPE output for organic-layer figures."""
    probe = out / "organic-layer-probe"
    probe.mkdir(parents=True, exist_ok=True)
    tr_years = end_year - ORGANIC_LAYER_START + 1
    fire_tr_year = 2007 - ORGANIC_LAYER_START

    injected = out / "restart-yedoma-ice.nc"
    if not injected.exists():
        raise FileNotFoundError(f"Missing Phase 1 restart with ice: {injected}")

    base = production.parse_json_with_comments(ROOT / "config/config.js")
    bgc.absolute_io(base)
    copy_spatial(base, probe)

    obs_csv = OBS_DIR / "jones2024-north-slope-climate-monthly.csv"
    _nsc.append_obs_years_from_ncei(
        obs_csv, out / "climate-cache", start_year=2022, end_year=end_year)
    tag = f"{bias_c:.1f}".replace(".", "p")
    template = Path(base["IO"]["hist_climate_file"])
    tr_climate = probe / f"north-slope-climate-tr-{tag}.nc"
    co2_full = out / "north-slope-co2-full.nc"
    if not co2_full.exists():
        co2_full = Path(base["IO"]["co2_file"])
    co2_tr = probe / f"north-slope-co2-tr-{tag}.nc"
    _nsc.make_tr_climate_from_obs(
        template, tr_climate, obs_csv,
        start_year=ORGANIC_LAYER_START, nyears=tr_years, inland_bias_c=bias_c)
    make_co2_tr(co2_full, co2_tr, ORGANIC_LAYER_START - 1901, tr_years)

    spec = out / "anaktuvuk-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec)
    base["IO"]["output_spec_file"] = str(spec)
    base["IO"]["hist_climate_file"] = str(tr_climate)
    base["IO"]["co2_file"] = str(co2_tr)

    source_fire = Path(base["IO"]["hist_exp_fire_file"])
    fire_on = probe / "anaktuvuk-fire-2007.nc"
    fire_off = probe / "no-fire.nc"
    make_fire(source_fire, fire_on, fire_tr_year, PHASE1_FIRE_JDAY,
              severity=resolve_fire_severity(args))
    make_fire(source_fire, fire_off)

    ice_top = PHASE1_ICE_TOP
    ice_bottom = PHASE1_ICE_BOTTOM
    statuses = {}
    profile_marker = probe / "burned" / "IWCLAYER_monthly_tr.nc"
    probe_reuse = reuse and profile_marker.exists()
    for name, restart, fire in [
            ("control", injected, fire_off),
            ("burned", injected, fire_on)]:
        statuses[name] = bgc.completed(probe, name) if probe_reuse else None
        if statuses[name] is None:
            statuses[name] = bgc.run(
                args.binary.resolve(), probe, name,
                config(base, probe / name, restart, fire,
                       ice_top=ice_top, ice_bottom=ice_bottom),
                ["--tr-yrs", str(tr_years)])
    return probe, tr_years, statuses


def run_phase2(args):
    out = args.output.resolve()
    setup_out(out, args.reuse)
    phase1_dir = (args.phase1_dir or PHASE1_OUT).resolve()
    probe = fire_topo.compile_probe(out)
    base = production.parse_json_with_comments(ROOT / "config/config.js")
    bgc.absolute_io(base)
    copy_spatial(base, out, PHASE2_CELLS, PHASE2_CELL_META)

    climate_bias = resolve_climate_bias(args)
    full_climate, tr_climate, co2_full, co2_tr, _, tr_report = prepare_climates(
        base, out, climate_bias)
    _nsc.write_build_report(out / "climate-build.json", tr_report)

    spec = out / "anaktuvuk-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec)
    base["IO"]["output_spec_file"] = str(spec)

    source_fire = Path(base["IO"]["hist_exp_fire_file"])
    fire_severity = resolve_fire_severity(args)
    burned_cells = [cell for cell, meta in PHASE2_CELL_META.items() if meta["fire"]]
    fire_on = out / "anaktuvuk-fire-phase2.nc"
    fire_off = out / "no-fire.nc"
    make_fire(source_fire, fire_on, FIRE_YEAR, PHASE1_FIRE_JDAY,
              burned_cells=burned_cells, severity=fire_severity)
    make_fire(source_fire, fire_off)

    phase1_init = phase1_dir / "initialization/restart-eq.nc"
    if not phase1_init.exists():
        raise FileNotFoundError(
            f"Phase 1 initialization missing at {phase1_init}; run Phase 1 first.")
    init_dir = out / "initialization"
    init_dir.mkdir(parents=True, exist_ok=True)
    initial = init_dir / "restart-eq.nc"
    expand_restart_for_phase2(phase1_init, initial)
    injected = out / "restart-yedoma-ice.nc"
    profiles = {
        cell: (meta["ice_frac"], meta["ice_top"], meta["ice_bottom"])
        for cell, meta in PHASE2_CELL_META.items()
    }
    added = inject_excess_cells(initial, injected, profiles)

    base["IO"]["hist_climate_file"] = str(tr_climate)
    base["IO"]["co2_file"] = str(co2_tr)
    run_name = "terrain"
    statuses = {"initialization": [100] * len(PHASE2_CELLS)}
    statuses[run_name] = completed_cells(out, run_name, PHASE2_CELLS) if args.reuse else None
    if statuses[run_name] is None:
        statuses[run_name] = run_cells(
            args.binary.resolve(), out, run_name,
            config(base, out / run_name, injected, fire_on,
                   ice_top=PHASE1_ICE_TOP, ice_bottom=PHASE1_ICE_BOTTOM),
            ["--tr-yrs", str(PHASE1_TR_YEARS)],
            PHASE2_CELLS)

    cell_metrics, stab_ratio = collect_phase2_metrics(out, run_name, PHASE1_TR_YEARS)
    upland_b = cell_metrics["upland_burned"]
    upland_c = cell_metrics["upland_control"]
    slope_b = cell_metrics["slope_burned"]
    dlb_b = cell_metrics["dlb_burned"]
    veg_trend_up = (np.isfinite(upland_b["veg_2010_g_m2"])
                    and np.isfinite(upland_b["veg_2021_g_m2"])
                    and upland_b["veg_2021_g_m2"] > upland_b["veg_2010_g_m2"])

    checks = []
    gate(checks, "synthetic fire water closure", abs(probe["water_residual_kg_m2"]),
         "<=1e-12 kg m-2", abs(probe["water_residual_kg_m2"]) <= 1e-12, hard=True)
    gate(checks, "synthetic fire energy closure", abs(probe["energy_residual_J_m2"]),
         "<=1e-6 J m-2", abs(probe["energy_residual_J_m2"]) <= 1e-6, hard=True)
    gate(checks, "production completion", statuses, "four cells status 100",
         all(v == [100] * len(PHASE2_CELLS) for v in statuses.values()), hard=True)
    gate(checks, "upland control unburned", upland_c["burn_depth_m"],
         "0 m burn depth", upland_c["burn_depth_m"] < 1e-9, hard=True)
    gate(checks, "burned cells receive fire", [cell_metrics[r]["burn_depth_m"]
         for r in ["upland_burned", "slope_burned", "dlb_burned"]],
         ">0 m on each burned terrain cell", all(
             cell_metrics[r]["burn_depth_m"] > 0.0
             for r in ["upland_burned", "slope_burned", "dlb_burned"]), hard=True)
    gate(checks, "stabilization ratio upland burned", stab_ratio,
         "2014–2021 / 2009–2014 < 0.25 (soft Phase 2)",
         np.isfinite(stab_ratio) and stab_ratio < 0.25)
    gate(checks, "slope vs upland subsidence 2009–2014",
         slope_b["lidar_epoch_cm"] - upland_b["lidar_epoch_cm"],
         "slope ≥ upland (cm, soft Phase 2)",
         slope_b["lidar_epoch_cm"] >= upland_b["lidar_epoch_cm"])
    gate(checks, "vegetation recovery upland burned",
         {"veg_2010": upland_b["veg_2010_g_m2"], "veg_2021": upland_b["veg_2021_g_m2"]},
         "VEGC upward post-2010 (sign only, soft Phase 2)", veg_trend_up)

    summary = {
        "phase": 2,
        "experiment": "anaktuvuk_phase2",
        "phase1_init": str(phase1_init),
        "calendar": {
            "tr_year_0": 2007,
            "fire_jday": PHASE1_FIRE_JDAY,
            "primary_window_tr_years": [PRIMARY_START, PRIMARY_END],
            "stabilization_window_tr_years": [STAB_START, STAB_END],
        },
        "weather": tr_report.to_dict(),
        "fire_severity": fire_severity,
        "ice_injection": {
            "profiles": {str(k): v for k, v in added.items()},
            "cell_meta": {str(k): v for k, v in PHASE2_CELL_META.items()},
        },
        "probe": probe,
        "statuses": statuses,
        "cells": cell_metrics,
        "contrasts": {
            "upland_burned_minus_control_lidar_cm":
                upland_b["lidar_epoch_cm"] - upland_c["lidar_epoch_cm"],
            "slope_minus_upland_lidar_cm":
                slope_b["lidar_epoch_cm"] - upland_b["lidar_epoch_cm"],
            "dlb_upland_lidar_cm": dlb_b["lidar_epoch_cm"],
            "stabilization_ratio_upland_burned": stab_ratio,
            "veg_recovery_upland_burned": veg_trend_up,
        },
        "checks_passed": sum(x["status"] == "PASS" for x in checks),
        "checks_total": len(checks),
    }
    (out / "summary.json").write_text(json.dumps(json_safe(summary), indent=2) + "\n")
    write_checks(out, checks)

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 10,
        "axes.labelsize": 9, "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "svg.fonttype": "none",
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })
    sub = bgc.read_daily(out / run_name, "TKSUBSIDENCE")
    fig, ax = plt.subplots(figsize=(8.0, 3.8), layout="constrained")
    colors = {"upland_burned": TEAL, "upland_control": MUTED,
              "slope_burned": BLUE, "dlb_burned": ORANGE}
    for role, meta in cell_metrics.items():
        y, x = meta["cell"]
        ax.plot(np.arange(sub.shape[0]) / 365.0, sub[:, y, x] * 100.0,
                lw=1.4, color=colors.get(role, INK), label=role.replace("_", " "))
    ax.axvline(FIRE_YEAR + (PHASE1_FIRE_JDAY - 1) / 365.0, color=ORANGE, ls=":", lw=0.9)
    ax.set(xlabel="Transient year (0 = 2007)", ylabel="Cumulative subsidence (cm)",
           title="Anaktuvuk Phase 2: terrain-unit columns")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.legend(loc="upper left", fontsize=7)
    save(fig, out, "anaktuvuk-phase2-subsidence-four-cells")
    return summary, checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT / "dvmdostem")
    parser.add_argument("--phase", type=int, choices=[0, 1, 2], default=0)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--allow-fail", action="store_true",
                        help="Do not exit nonzero on soft gate failures (Phase 1)")
    parser.add_argument("--ice-fraction", type=float, default=None,
                        help="Override Phase 1 Yedoma excess-ice fraction")
    parser.add_argument("--ice-top", type=float, default=None,
                        help="Override Phase 1 excess-ice top depth (m)")
    parser.add_argument("--ice-bottom", type=float, default=None,
                        help="Override Phase 1 excess-ice bottom depth (m)")
    parser.add_argument("--climate-bias", type=float, default=None,
                        help="Inland tair bias (°C) added to Barrow climatology")
    parser.add_argument("--calibrate-climate", action="store_true",
                        help="Sweep climate bias until unburned control ALT >= 30 cm")
    parser.add_argument("--calibrate-fire", action="store_true",
                        help="Sweep fire severity so post-fire snow matches unburned control")
    parser.add_argument("--fire-severity", type=int, default=None,
                        help="Override fire severity (2–4); default from fire calibration")
    parser.add_argument("--phase1-dir", type=Path, default=None,
                        help="Phase 1 output directory to resume EQ spin-up (Phase 2)")
    parser.add_argument("--plot-diagnostics", action="store_true",
                        help="Generate climate/thermal diagnostic figures from existing output")
    parser.add_argument("--climate-end-year", type=int, default=None,
                        help="Extend/replot TR climate through this calendar year (e.g. 2023)")
    parser.add_argument("--organic-layers", action="store_true",
                        help="Run/build 2000+ organic-layer probe and plot moss/fibric/humic depths")
    parser.add_argument("--plot-start-year", type=int, default=ORGANIC_LAYER_START,
                        help="Left edge of organic-layer and climate plot windows")
    parser.add_argument("--stage", choices=["spinup", "transient"], default=None,
                        help="Run long spin-up once (spinup) or transient-only SP+TR (transient)")
    parser.add_argument("--spinup-dir", type=Path, default=None,
                        help="Directory containing restart-sp.nc from spin-up")
    parser.add_argument("--paired-only", action="store_true",
                        help="Stage B: run control+burned only (skip restart split/resumed)")
    parser.add_argument("--winter-precip-scale", type=float, default=None,
                        help="Scale snow-month precip (default targets ~40 cm peak snow)")
    parser.add_argument("--max-organic-burn", action="store_true",
                        help="Patch CMT05 fire params for full organic burn; relax snow gate")
    parser.add_argument("--calibrate-ice", action="store_true",
                        help="Sweep ice-top depth for LiDAR-window subsidence contrast")
    parser.add_argument("--ice-bracket", action="store_true",
                        help="Thaw-depth bracket ice band (deeper top, Jones ALT targets)")
    parser.add_argument("--calibrate-climate-bracket", action="store_true",
                        help="Hybrid control ALT probe; select bias for 30–75 cm isotherm ALT")
    args = parser.parse_args()
    if args.ice_bracket:
        args.max_organic_burn = True
    if args.ice_bracket and args.output is None:
        if args.calibrate_ice:
            args.output = ICE_BRACKET_OUT
        elif args.calibrate_climate_bracket:
            args.output = BRACKET_CLIMATE_CALIBRATION_OUT
        elif args.stage == "transient" or args.phase == 1:
            args.output = ICE_BRACKET_OUT
    elif args.max_organic_burn and args.output is None:
        if args.stage == "transient" or args.phase == 1:
            args.output = MAX_ORGANIC_BURN_OUT
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"

    if args.calibrate_climate:
        if args.output is None:
            args.output = ROOT / "experiments/thermokarst/anaktuvuk_climate_calibration_results"
        calib = run_calibrate_climate(args)
        print(json.dumps(calib, indent=2))
        return

    if args.calibrate_fire:
        base = production.parse_json_with_comments(ROOT / "config/config.js")
        bgc.absolute_io(base)
        out = ROOT / "experiments/thermokarst/anaktuvuk_fire_calibration_results"
        climate_bias = resolve_climate_bias(args)
        full, tr, co2_full, co2_tr, _, _ = prepare_climates(base, out, climate_bias)
        calib = run_calibrate_fire_snow(
            args, base, full, tr, co2_full, co2_tr, climate_bias, reuse=args.reuse)
        print(json.dumps(calib, indent=2))
        return

    if args.calibrate_ice:
        calib = run_calibrate_ice(args)
        print(json.dumps(calib, indent=2))
        return

    if args.calibrate_climate_bracket:
        calib = run_calibrate_climate_bracket(args)
        print(json.dumps(calib, indent=2))
        return

    if args.stage == "spinup":
        summary = run_spinup(args)
        print(json.dumps(summary, indent=2))
        return

    if args.stage == "transient":
        summary = run_transient(args)
        print(json.dumps(summary, indent=2))
        return

    if args.plot_diagnostics:
        if args.output is None:
            args.output = PHASE1_OUT
        out = args.output.resolve()
        bias_c = resolve_climate_bias(args)
        tr_end_year = args.climate_end_year or ORGANIC_LAYER_END
        if not (out / "burned").exists():
            raise FileNotFoundError(
                f"No transient output in {out}; run --stage transient or --phase 1 first.")
        base = production.parse_json_with_comments(ROOT / "config/config.js")
        bgc.absolute_io(base)
        tag = f"{bias_c:.1f}".replace(".", "p")
        if not (out / f"north-slope-climate-tr-{tag}.nc").exists():
            prepare_transient_climates(base, out, bias_c, tr_end_year=tr_end_year)
        seasonal = out / f"anaktuvuk-seasonal-climate-{TRANSIENT_SP_YEARS}y-{tag}.nc"
        tr_only = out / f"north-slope-climate-tr-{tag}.nc"
        injected = out / "restart-yedoma-ice.nc"
        stems = _dplots.generate_diagnostic_figures(
            out, tr_years=TRANSIENT_TR_YEARS,
            start_year=TRANSIENT_TR_CALENDAR_START,
            tr_end_year=tr_end_year,
            fire_jday=PHASE1_FIRE_JDAY, fire_year=2007,
            bias_c=bias_c, restart=injected,
            full_climate=seasonal if seasonal.exists() else None,
            tr_climate=tr_only if tr_only.exists() else None,
            profile_probe_dir=out,
            profile_start_year=TRANSIENT_TR_CALENDAR_START,
            profile_tr_years=TRANSIENT_TR_YEARS,
            plot_start_year=args.plot_start_year,
            prefix=figure_prefix(args),
            copy_to_report=True)
        print(json.dumps({"diagnostic_figures": stems}, indent=2))
        return

    if args.output is None:
        args.output = {0: PHASE0_OUT, 1: PHASE1_OUT, 2: PHASE2_OUT}[args.phase]

    if args.phase == 0:
        summary, checks = run_phase0(args)
    elif args.phase == 1:
        summary, checks = run_phase1(args)
    else:
        summary, checks = run_phase2(args)

    print(json.dumps({
        "phase": summary["phase"],
        "checks_passed": summary["checks_passed"],
        "checks_total": summary["checks_total"],
        "contrasts": summary["contrasts"],
    }, indent=2))

    hard_failed = [x for x in checks if x.get("hard") and x["status"] == "FAIL"]
    if hard_failed:
        raise RuntimeError(
            f"{len(hard_failed)} hard gates failed: {[x['test'] for x in hard_failed]}")
    soft_failed = [x for x in checks if not x.get("hard") and x["status"] == "FAIL"]
    if soft_failed:
        print("WARNING: soft gate failures:",
              [x["test"] for x in soft_failed], file=sys.stderr)
        if args.phase in (1, 2) and not args.allow_fail:
            raise RuntimeError(
                f"{len(soft_failed)} soft gates failed: {[x['test'] for x in soft_failed]}")


if __name__ == "__main__":
    main()
