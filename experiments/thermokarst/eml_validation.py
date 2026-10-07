#!/usr/bin/env python3
"""EML CiPEHR subsidence validation harness (Phases 0–4)."""
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

CLIMATE_PKG = Path(__file__).resolve().parent / "eml_validation"
sys.path.insert(0, str(CLIMATE_PKG))
from healy_climate import (  # noqa: E402
    TREATMENT_BIAS,
    build_eml_climate,
    prepare_monthly_csv,
)

import numpy as np
from netCDF4 import Dataset

ROOT = Path(__file__).resolve().parents[2]
OBS_DIR = CLIMATE_PKG / "obs"
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

TREATMENTS = ["control", "air_warming", "soil_warming", "air_soil_warming"]
PHASE0_CELLS = [(0, 0), (0, 1), (1, 0), (1, 1)]
PHASE1_CELL = (0, 0)
CMT = 21
DRAINAGE = 1
TR_YEARS = 9
RESTART_SPLIT = 4

# Rodenhizer et al. 2020 subsidence-rate gates (cm yr⁻¹).
OBS_RATES = {
    "control": (0.7, 1.7, 1.2),
    "air_warming": (0.9, 2.0, 1.4),
    "soil_warming": (4.8, 5.9, 5.4),
    "air_soil_warming": (5.6, 6.7, 6.1),
}
RATIO_GATE = (3.0, 6.0)

PHASE1_DIR = ROOT / "experiments/thermokarst/eml_phase1_validation_results"
PHASE2_DIR = ROOT / "experiments/thermokarst/eml_phase2_validation_results"
PHASE2_TR_SENSITIVITY = 15
PHASE3_TR_EXTENDED = 15
PHASE4_DIR = ROOT / "experiments/thermokarst/eml_phase4_validation_results"
PHASE5_DIR = ROOT / "experiments/thermokarst/eml_phase5_validation_results"

PHASES = {
    0: {
        "cells": PHASE0_CELLS,
        "eq_yrs": 5,
        "tr_years": TR_YEARS,
        "ice_mass": 100.0,
        "ice_depth": 0.10,
        "climate_nyears": 20,
        "default_output": ROOT / "experiments/thermokarst/eml_validation_results",
    },
    1: {
        "cells": [PHASE1_CELL],
        "eq_yrs": 30,
        "tr_years": TR_YEARS,
        "ice_top_m": 0.10,
        "ice_shallow_bottom_m": 0.35,
        "ice_deep_bottom_m": 1.20,
        "climate_nyears": 40,
        "calibration_fractions": [0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "default_output": PHASE1_DIR,
    },
    2: {
        "cells": [PHASE1_CELL],
        "eq_yrs": 30,
        "tr_years": TR_YEARS,
        "tr_sensitivity_years": PHASE2_TR_SENSITIVITY,
        "ice_top_m": 0.10,
        "ice_shallow_bottom_m": 0.35,
        "ice_deep_bottom_m": 1.20,
        "climate_nyears": 40,
        "calibration_fractions": [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60],
        "default_output": PHASE2_DIR,
        "phase1_dir": PHASE1_DIR,
    },
    3: {
        "cells": [PHASE1_CELL],
        "eq_yrs": 30,
        "tr_years": TR_YEARS,
        "tr_extended_years": PHASE3_TR_EXTENDED,
        "ice_top_m": 0.10,
        "ice_shallow_bottom_m": 0.35,
        "ice_deep_bottom_m": 1.20,
        "climate_nyears": 40,
        "soil_bias_scales": [1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
        "deep_scales": [2.0, 3.0, 4.0, 5.0, 6.0],
        "bias_profile": "snow_fence",
        "default_output": ROOT / "experiments/thermokarst/eml_phase3_validation_results",
        "phase1_dir": PHASE1_DIR,
        "phase2_dir": PHASE2_DIR,
    },
    4: {
        "cells": [PHASE1_CELL],
        "eq_yrs": 30,
        "tr_years": TR_YEARS,
        "tr_extended_years": PHASE3_TR_EXTENDED,
        "ice_top_m": 0.10,
        "ice_shallow_bottom_m": 0.35,
        "ice_deep_bottom_m": 1.20,
        "climate_nyears": 40,
        "soil_bias_scales": [2.0, 2.5, 3.0],
        "deep_scales": [4.0, 5.0, 6.0, 8.0],
        "snow_fence_winter_extra": [1.5],
        "snow_fence_summer_extra": [0.0, 0.75, 1.5],
        "slopes": [0.0],
        "bias_profile": "snow_fence",
        "default_output": PHASE4_DIR,
        "phase1_dir": PHASE1_DIR,
        "phase2_dir": PHASE2_DIR,
    },
    5: {
        "cells": [PHASE1_CELL],
        "eq_yrs": 30,
        "tr_years": TR_YEARS,
        "tr_start_yr": 5,
        "tr_extended_years": PHASE3_TR_EXTENDED,
        "ice_top_m": 0.10,
        "ice_shallow_bottom_m": 0.35,
        "ice_deep_bottom_m": 1.20,
        "climate_nyears": 40,
        "soil_bias_scales": [2.0, 2.5, 3.0],
        "deep_scales": [4.0, 5.0, 6.0, 8.0],
        "snow_fence_winter_extra": [1.5],
        "snow_fence_summer_extra": [0.0, 0.75, 1.5],
        "slopes": [0.0],
        "bias_profile": "snow_fence",
        "snow_profile": "cipehr",
        "annual_snow_swe_mm": 100.0,
        "snow_swe_calibration": [85.0, 95.0, 100.0, 105.0, 115.0, 125.0],
        "snow_target_peak_cm": 40.0,
        "soil_snow_multiplier": 2.0,
        "default_output": PHASE5_DIR,
        "phase1_dir": PHASE1_DIR,
        "phase2_dir": PHASE2_DIR,
    },
}

SHALLOW_TREATMENTS = {"control", "air_warming"}
DEEP_TREATMENTS = {"soil_warming", "air_soil_warming"}

INK = "#171717"
TEAL = "#1F6F5F"
BLUE = "#4C78A8"
ORANGE = "#D55E00"
MUTED = "#777772"
GRID = "#E4E7E5"
TREAT_COLOR = {
    "control": TEAL,
    "air_warming": BLUE,
    "soil_warming": ORANGE,
    "air_soil_warming": MUTED,
}

EML_TAIR = np.array([-12., -10., -6., 0., 8., 14., 16., 12., 6., -2., -8., -11.])
EML_PRECIP = np.array([18., 16., 14., 16., 22., 35., 45., 40., 28., 22., 20., 18.])
EML_NIRR = np.array([0., 2., 6., 14., 20., 22., 18., 12., 6., 2., 0., 0.])


def absolute_io(base):
    for key, value in list(base["IO"].items()):
        if not value:
            continue
        if key.endswith("_file") or key == "parameter_dir":
            base["IO"][key] = str((ROOT / value).resolve())


def copy_spatial(base, out, cells, slope=5.0):
    out.mkdir(parents=True, exist_ok=True)
    label = "four-cells" if len(cells) > 1 else "one-cell"
    mask = out / f"run-mask-{label}.nc"
    if Path(base["IO"]["runmask_file"]).resolve() != mask.resolve():
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
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        with Dataset(dst, "r+") as dataset:
            for y, x in cells:
                if var == "veg_class":
                    dataset[var][y, x] = CMT
                elif var == "drainage_class":
                    dataset[var][y, x] = DRAINAGE
                else:
                    dataset[var][y, x] = slope
        base["IO"][key] = str(dst)


def make_synthetic_climate(source, dest, nyears):
    shutil.copy2(source, dest)
    with Dataset(dest, "r+") as dataset:
        nmonths = nyears * 12
        for name in ["tair", "precip", "nirr", "vapor_press"]:
            if name not in dataset.variables:
                continue
            shape = list(dataset[name].shape)
            shape[0] = nmonths
            data = np.zeros(shape, dtype=np.float64)
            for i in range(nmonths):
                month = i % 12
                if name == "tair":
                    data[i] = EML_TAIR[month]
                elif name == "precip":
                    data[i] = EML_PRECIP[month]
                elif name == "nirr":
                    data[i] = EML_NIRR[month]
                else:
                    data[i] = 100.0
            dataset[name][:] = data
    return dest


def make_spec(
    source, dest, extra_yearly=(), include_front=True, include_watertab=False,
    include_profile=False,
):
    rows = list(csv.DictReader(source.open()))
    daily_names = set(bgc.TK) | {"SNOWTHICK", "TKPOND", "TKSURFICE", "TKSUBSIDENCE"}
    profile_names = {"TLAYER", "LAYERDEPTH", "LAYERDZ"}
    if include_front:
        daily_names |= {"TKFRONT", "TKFRONTTYPE"}
    if include_watertab:
        daily_names.add("WATERTAB")
    yearly_names = {"TKSUBSIDENCE"} | set(extra_yearly)
    if include_front:
        yearly_names.add("TKFRONT")
    if include_watertab:
        yearly_names.add("WATERTAB")
    for row in rows:
        row["Yearly"] = row["Monthly"] = row["Daily"] = row["Layers"] = ""
        if row["Name"] in daily_names:
            row["Daily"] = "d"
        if row["Name"] in profile_names and include_profile:
            row["Monthly"] = "m"
            row["Layers"] = "forced"
        if row["Name"] in yearly_names:
            row["Yearly"] = "y"
    with dest.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def config(base, directory, cells, restart=None, thermokarst=False, output=True, tr_start=0):
    cfg = json.loads(json.dumps(base))
    io = cfg["IO"]
    io["output_dir"] = str(directory) + "/"
    io["restart_from"] = str(restart) if restart else ""
    io["output_nc_eq"] = io["output_nc_pr"] = io["output_nc_sp"] = 0
    io["output_nc_tr"] = int(output)
    io["output_nc_sc"] = 0
    io["output_interval"] = 1
    io["output_monthly"] = 0
    cfg["model_settings"]["thermokarst"] = {
        "enabled": bool(thermokarst),
        "excess_fraction": 0.0,
        "top_depth": 0.35,
        "bottom_depth": 1.20,
    }
    for stage in ["pr", "eq", "sp", "tr", "sc"]:
        cfg["stage_settings"][stage].update({
            "env": True,
            "bgc": False,
            "nfeed": False,
            "avlnflg": False,
            "baseline": stage == "eq",
            "dsb": False,
            "dsl": True,
            "dyn_lai": False,
        })
    cfg["stage_settings"]["tr_start_yr"] = int(tr_start)
    cfg["_cells"] = [list(c) for c in cells]
    return cfg


def layer_thickness(dataset, y, x, j):
    matrix = float(dataset["TKmatrix"][y, x, j])
    if matrix > 0.0:
        return matrix
    return float(dataset["DZsoil"][y, x, j])


def resolve_ice_depth(restart, cells, target):
    for cell in cells:
        y, x = cell
        with Dataset(restart) as dataset:
            n = int(dataset["numsl"][y, x])
            z = 0.0
            found = False
            for j in range(n):
                thickness = layer_thickness(dataset, y, x, j)
                if thickness <= 0.0:
                    continue
                if z <= target < z + thickness:
                    found = True
                    break
                z += thickness
            if not found:
                raise RuntimeError(f"target depth {target} m missing at cell {cell}")
    return target


def inject_excess_band(source, dest, fraction, top, bottom, cells):
    """Fill [top, bottom) with excess ice at ``fraction`` of layer volume."""
    if not (0.0 <= fraction < 1.0):
        raise ValueError("fraction must be in [0, 1)")
    if Path(source).resolve() != Path(dest).resolve():
        shutil.copy2(source, dest)
    added = {}
    with Dataset(dest, "r+") as dataset:
        for cell in cells:
            y, x = cell
            n = int(dataset["numsl"][y, x])
            z = 0.0
            total = 0.0
            for j in range(n):
                matrix = layer_thickness(dataset, y, x, j)
                overlap = max(0.0, min(z + matrix, bottom) - max(z, top))
                if overlap > 0.0:
                    temperature = float(dataset["TSsoil"][y, x, j])
                    if temperature > 1.0e-8:
                        raise RuntimeError(f"injection layer is thawed: {cell} layer {j}")
                    if temperature > 0.0:
                        dataset["TSsoil"][y, x, j] = 0.0
                    mass = 917.0 * overlap * fraction / (1.0 - fraction)
                    existing = float(dataset["TKexcess"][y, x, j])
                    dataset["TKexcess"][y, x, j] = existing + float(mass)
                    dataset["DZsoil"][y, x, j] = float(dataset["DZsoil"][y, x, j]) + mass / 917.0
                    total += mass
                z += matrix
            added[str(cell)] = total
    return added


def inject_excess_mass(source, dest, mass, depth, cells):
    if not (np.isfinite(mass) and mass >= 0.0):
        raise ValueError("invalid excess-ice mass")
    shutil.copy2(source, dest)
    added = {}
    with Dataset(dest, "r+") as dataset:
        for cell in cells:
            y, x = cell
            n = int(dataset["numsl"][y, x])
            z = 0.0
            placed = False
            for j in range(n):
                matrix = layer_thickness(dataset, y, x, j)
                if matrix <= 0.0:
                    continue
                contains = z <= depth < z + matrix or (j == n - 1 and z + matrix >= depth)
                if contains:
                    temperature = float(dataset["TSsoil"][y, x, j])
                    if mass and temperature > 1.0e-8:
                        raise RuntimeError(f"injection layer is thawed: {cell} layer {j}")
                    if temperature > 0.0:
                        dataset["TSsoil"][y, x, j] = 0.0
                    dataset["TKexcess"][y, x, j] = float(mass)
                    dataset["DZsoil"][y, x, j] = matrix + mass / 917.0
                    added[str(cell)] = float(mass)
                    placed = True
                    break
                z += matrix
            if not placed:
                raise RuntimeError(f"no layer contains depth {depth} m at {cell}")
    return added


def run(binary, out, name, cfg, args, cells):
    run_dir = out / name
    if run_dir.exists():
        shutil.rmtree(run_dir)
    path = out / f"{name}.json"
    path.write_text(json.dumps({k: v for k, v in cfg.items() if k != "_cells"}, indent=2) + "\n")
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


def completed(out, name, cells):
    path = out / name / "run_status.nc"
    if not path.exists():
        return None
    with Dataset(path) as dataset:
        status = [int(dataset["run_status"][y, x]) for y, x in cells]
    expected = [100] * len(cells)
    return status if status == expected else None


def read_daily(directory, name):
    with Dataset(directory / f"{name}_daily_tr.nc") as dataset:
        return np.asarray(np.ma.asarray(dataset[name][:]).filled(np.nan), float)


def cell_series(array, cell):
    return array[(slice(None),) + cell]


def monotonic(series):
    return bool(np.all(np.diff(series) >= -1.0e-12))


def subsidence_metrics(daily, cell, tr_years):
    series = cell_series(daily, cell)
    total_cm = float(series[-1] * 100.0)
    rate = total_cm / tr_years
    return {
        "total_cm": total_cm,
        "rate_cm_yr": rate,
        "monotonic": monotonic(series),
    }


def yearly_subsidence_cm(daily, cell, tr_years):
    series = cell_series(daily, cell) * 100.0
    return [float(series[(y + 1) * 365 - 1]) for y in range(tr_years)]


def september_max_thaw_cm(directory, cell, tr_years):
    """September max thaw-front depth (cm) per transient year."""
    front = read_daily(directory, "TKFRONT")
    ftype = read_daily(directory, "TKFRONTTYPE")
    depths = cell_series(front, cell)
    types = cell_series(ftype, cell)
    values = []
    for year in range(tr_years):
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


def thaw_penetration_end_cm(directory, cell, tr_years):
    """End-of-window thaw penetration = September ALT + cumulative subsidence (cm)."""
    alt = september_max_thaw_cm(directory, cell, tr_years)
    sub = read_daily(directory, "TKSUBSIDENCE")
    sub_cm = float(cell_series(sub, cell)[-1] * 100.0)
    alt_end = alt[-1] if alt else float("nan")
    tp = alt_end + sub_cm if np.isfinite(alt_end) else float("nan")
    return {
        "alt_cm": alt_end,
        "subsidence_cm": sub_cm,
        "thaw_penetration_cm": tp,
        "yearly_alt_cm": alt,
        "yearly_subsidence_cm": yearly_subsidence_cm(sub, cell, tr_years),
    }


def load_obs_thaw(path):
    obs = {}
    for row in csv.DictReader(path.open()):
        obs[row["treatment"]] = {
            "alt_cm": float(row["alt_cm"]),
            "se_alt_cm": float(row["se_alt_cm"]),
            "thaw_penetration_cm": float(row["thaw_penetration_cm"]),
            "se_thaw_penetration_cm": float(row["se_thaw_penetration_cm"]),
            "thaw_penetration_increase_pct": float(row["thaw_penetration_increase_pct"]),
        }
    return obs


def load_gps_obs(path):
    """Return {treatment: {year: mean_subsidence_cm}} from BNZ:729 obs CSV."""
    by_treatment = {}
    for row in csv.DictReader(path.open()):
        treatment = row["treatment"]
        year = int(row["year"])
        by_treatment.setdefault(treatment, {})[year] = float(row["mean_subsidence_cm"])
    return by_treatment


def load_phase1_ice_params(phase1_dir):
    summary_path = phase1_dir / "summary.json"
    if not summary_path.exists():
        raise RuntimeError(f"Phase 1 summary missing: {summary_path}")
    summary = json.loads(summary_path.read_text())
    return {
        "ice_fraction": summary["chosen_ice_fraction"],
        "deep_scale": summary["deep_scale_calibration"]["scale"],
        "settings": PHASES[1],
    }


def load_phase2_ice_params(phase2_dir):
    summary_path = phase2_dir / "summary.json"
    if not summary_path.exists():
        raise RuntimeError(f"Phase 2 summary missing: {summary_path}")
    summary = json.loads(summary_path.read_text())
    return {
        "ice_fraction": summary["chosen_ice_fraction"],
        "deep_scale": summary["deep_scale"],
        "deep_scale_calibration": summary.get("deep_scale_calibration", {}),
    }


def load_obs_water_table(path):
    obs = {}
    for row in csv.DictReader(path.open()):
        key = (row["treatment"], int(row["year"]))
        obs[key] = {
            "depth_cm": float(row["water_table_depth_cm"]),
            "se_cm": float(row["se_cm"]),
        }
    return obs


def summer_mean_wtd_cm(directory, cell, tr_years, year_idx):
    """Mean Jun–Aug water-table depth (cm) for transient year index."""
    try:
        wtab = read_daily(directory, "WATERTAB")
    except FileNotFoundError:
        return float("nan")
    series = cell_series(wtab, cell) * 100.0
    start = year_idx * 365 + 151
    end = year_idx * 365 + 243
    chunk = series[start:end + 1]
    if not np.any(np.isfinite(chunk)):
        return float("nan")
    return float(np.nanmean(chunk))


def summer_wtd_trajectory(directory, cell, tr_years, start_year=2009):
    """Return {calendar_year: mean Jun–Aug WTD (cm)} for each transient year."""
    return {
        start_year + year_idx: summer_mean_wtd_cm(directory, cell, tr_years, year_idx)
        for year_idx in range(tr_years)
    }


def load_bnz554_trajectory(path):
    """Return {treatment: {year: mean_wtd_cm}} from BNZ:554 summer obs."""
    by_treatment = {}
    for row in csv.DictReader(path.open()):
        treatment = row["treatment"]
        year = int(row["year"])
        by_treatment.setdefault(treatment, {})[year] = float(row["mean_wtd_cm"])
    return by_treatment


def wtd_trajectory_rmse(sim_traj, obs_traj, years, treatment):
    """RMSE (cm) between simulated and observed summer WTD trajectories."""
    diffs = []
    for year in years:
        if year not in obs_traj.get(treatment, {}):
            continue
        sim = sim_traj.get(year, float("nan"))
        if not np.isfinite(sim):
            continue
        diffs.append(sim - obs_traj[treatment][year])
    if not diffs:
        return float("inf")
    return float(np.sqrt(np.mean(np.square(diffs))))


def phase4_calibration_score(
    soil_rate,
    control_wtd,
    soil_wtd,
    soil_tp,
    obs_wtd_traj,
    obs_tp,
    *,
    wtd_years=None,
):
    wtd_years = wtd_years or range(2009, 2019)
    """Composite score (lower is better) for snow-fence + deep-scale tuning."""
    lo, hi, target = OBS_RATES["soil_warming"]
    if soil_rate < lo:
        sub_score = (lo - soil_rate) * 3.0 + abs(soil_rate - target)
    elif soil_rate > hi:
        sub_score = (soil_rate - hi) * 3.0 + abs(soil_rate - target)
    else:
        sub_score = abs(soil_rate - target)

    wtd_score = (
        wtd_trajectory_rmse(control_wtd, obs_wtd_traj, wtd_years, "control")
        + wtd_trajectory_rmse(soil_wtd, obs_wtd_traj, wtd_years, "soil_warming")
    )
    soil18 = soil_wtd.get(2018, float("nan"))
    ctrl18 = control_wtd.get(2018, float("nan"))
    direction_penalty = 0.0
    if np.isfinite(soil18) and np.isfinite(ctrl18) and soil18 >= ctrl18:
        direction_penalty = (soil18 - ctrl18) * 2.0

    obs_tp_cm = obs_tp["soil_warming"]["thaw_penetration_cm"]
    tp_score = abs(soil_tp - obs_tp_cm) / max(obs_tp_cm, 1.0) * 50.0

    return sub_score + 0.15 * wtd_score + direction_penalty + tp_score


def pick_soil_bias_scale(results, target=5.4):
    lo, hi, _ = OBS_RATES["soil_warming"]
    in_band = [r for r in results if lo <= r["rate_cm_yr"] <= hi]
    pool = in_band if in_band else results
    return min(pool, key=lambda r: abs(r["rate_cm_yr"] - target))


def pick_deep_scale(results, target=5.4):
    lo, hi, _ = OBS_RATES["soil_warming"]
    in_band = [r for r in results if lo <= r["rate_cm_yr"] <= hi]
    pool = in_band if in_band else results
    return min(pool, key=lambda r: abs(r["rate_cm_yr"] - target))


def copy_phase1_spinup(phase1_dir, out):
    """Copy Phase 1 EQ spin-up only (initialization/restart-eq.nc)."""
    src = phase1_dir / "initialization"
    dst = out / "initialization"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def calibrate_shallow_fraction(binary, init_base, out, cells, settings, initial,
                             ice_fractions, cell):
    """Sweep shallow-band fraction on control climate; return calibration list + chosen."""
    calibration = []
    for fraction in ice_fractions:
        restart, added = treatment_restart(initial, out, "control", fraction, settings, cells)
        run_name = f"calibration-{fraction:.2f}"
        run(
            binary, out, run_name,
            config(init_base, out / run_name, cells, restart, thermokarst=True),
            ["--tr-yrs", str(settings["tr_years"])], cells)
        daily = read_daily(out / run_name, "TKSUBSIDENCE")
        metrics = subsidence_metrics(daily, cell, settings["tr_years"])
        calibration.append({
            "fraction": fraction,
            "injected_kg_m2": added[str(cell)],
            **metrics,
        })
        print(f"calibration fraction={fraction:.2f}: "
              f"{metrics['rate_cm_yr']:.3f} cm yr-1", file=sys.stderr)
    chosen = pick_calibrated_fraction(calibration)
    return calibration, chosen["fraction"]


def save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=240, bbox_inches="tight")
    fig.savefig(out / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def pick_calibrated_fraction(results, target=1.2):
    """Choose shallow-band excess-ice fraction closest to Rodenhizer control rate."""
    in_band = [r for r in results if OBS_RATES["control"][0] <= r["rate_cm_yr"] <= OBS_RATES["control"][1]]
    pool = in_band if in_band else results
    return min(pool, key=lambda r: abs(r["rate_cm_yr"] - target))


def inject_excess_profile(source, dest, lenses, cells):
    """Place multiple ``(depth_m, mass_kg_m2)`` excess-ice lenses."""
    shutil.copy2(source, dest)
    added = {}
    with Dataset(dest, "r+") as dataset:
        for cell in cells:
            y, x = cell
            total = 0.0
            for depth, mass in lenses:
                n = int(dataset["numsl"][y, x])
                z = 0.0
                placed = False
                for j in range(n):
                    matrix = layer_thickness(dataset, y, x, j)
                    contains = z <= depth < z + matrix or (j == n - 1 and z + matrix >= depth)
                    if contains:
                        temperature = float(dataset["TSsoil"][y, x, j])
                        if mass and temperature > 1.0e-8:
                            raise RuntimeError(f"injection layer thawed: {cell} layer {j}")
                        if temperature > 0.0:
                            dataset["TSsoil"][y, x, j] = 0.0
                        dataset["TKexcess"][y, x, j] += float(mass)
                        dataset["DZsoil"][y, x, j] = matrix + float(mass) / 917.0
                        total += float(mass)
                        placed = True
                        break
                    z += matrix
                if mass and not placed:
                    raise RuntimeError(f"no layer contains depth {depth} m at {cell}")
            added[str(cell)] = total
    return added


def treatment_restart(initial, out, treatment, fraction, settings, cells, deep_scale=1.0):
    top = settings["ice_top_m"]
    shallow_bottom = settings["ice_shallow_bottom_m"]
    deep_bottom = settings["ice_deep_bottom_m"]
    tag = f"f{fraction:.2f}"
    if treatment in DEEP_TREATMENTS:
        tag += f"-d{deep_scale:.1f}"
    path = out / f"restart-{treatment}-{tag}.nc"
    if treatment in DEEP_TREATMENTS:
        # Shallow band shared with control plus deeper band for soil-warming thaw penetration.
        added_shallow = inject_excess_band(initial, path, fraction, top, shallow_bottom, cells)
        deep_fraction = min(0.65, fraction * 0.85 * deep_scale)
        added_deep = inject_excess_band(
            path, path, deep_fraction, shallow_bottom, deep_bottom, cells)
        added = {k: added_shallow[k] + added_deep[k] for k in added_shallow}
    else:
        added = inject_excess_band(initial, path, fraction, top, shallow_bottom, cells)
    return path, added


def calibrate_deep_scale(binary, base, out, cells, settings, monthly_csv, template,
                         ice_fraction, init_base):
    """Increase deep-band ice for soil treatments until rate brackets Rodenhizer soil warming."""
    lo, hi, target = OBS_RATES["soil_warming"]
    best = {"scale": 1.0, "rate": 0.0, "distance": float("inf")}
    in_band = None
    climates, _, _ = prepare_phase1_climates(
        base, out, settings, monthly_csv, template,
        bias_scales={"control": 1.0, "air_warming": 1.0,
                     "soil_warming": 1.0, "air_soil_warming": 1.0})
    for scale in np.linspace(1.0, 6.0, 6):
        restart, _ = treatment_restart(
            out / "initialization/restart-eq.nc", out, "soil_warming",
            ice_fraction, settings, cells, deep_scale=scale)
        metrics = run_treatment_tr(
            binary, base, out, cells, "soil_warming",
            climates["soil_warming"], restart, settings["tr_years"])
        rate = metrics["rate_cm_yr"]
        print(f"deep scale={scale:.1f}: soil rate={rate:.3f} cm yr-1", file=sys.stderr)
        distance = abs(rate - target)
        if lo <= rate <= hi and (in_band is None or distance < in_band["distance"]):
            in_band = {"scale": float(scale), "rate": rate, "distance": distance}
        if distance < best["distance"]:
            best = {"scale": float(scale), "rate": rate, "distance": distance}
    chosen = in_band or best
    return chosen


def prepare_phase1_climates(
    base, out, settings, monthly_csv, template,
    bias_scales=None, bias_profile="default", climate_kwargs=None,
    snow_kwargs=None,
):
    bias_scales = bias_scales or {t: 1.0 for t in TREATMENTS}
    climate_kwargs = climate_kwargs or {}
    snow_kwargs = snow_kwargs or {}
    climates = {}
    meta = {}
    for treatment in TREATMENTS:
        path = out / f"eml-climate-{treatment}.nc"
        report = build_eml_climate(
            template, path, monthly_csv,
            treatment=treatment,
            nyears=settings["climate_nyears"],
            bias_scale=bias_scales.get(treatment, 1.0),
            bias_profile=bias_profile,
            **climate_kwargs,
            **snow_kwargs)
        climates[treatment] = path
        meta[treatment] = report.to_dict()
    return climates, base["IO"]["co2_file"], meta


def snow_kwargs_from_settings(settings: dict) -> dict:
    if not settings.get("snow_profile"):
        return {}
    return {
        "snow_profile": settings["snow_profile"],
        "annual_snow_swe_mm": settings.get("annual_snow_swe_mm", 110.0),
        "snow_target_peak_cm": settings.get("snow_target_peak_cm", 40.0),
        "soil_snow_multiplier": settings.get("soil_snow_multiplier", 2.0),
    }


def tr_start_from_settings(settings: dict) -> int:
    return int(settings.get("tr_start_yr", 0))


def snow_peak_metrics(daily_snow, cell, tr_years, tr_start_yr=0):
    """Yearly max snow depth (cm) over the transient window."""
    del tr_start_yr  # output is indexed from transient start (already calendar-aligned)
    series = bgc.cell_series(daily_snow, cell)
    window = series[:tr_years * 365]
    peaks = []
    melt_months = []
    for i in range(tr_years):
        chunk = window[i * 365:(i + 1) * 365]
        peak_i = int(np.argmax(chunk))
        peaks.append(float(chunk[peak_i]) * 100.0)
        # day-of-year → approximate melt month (0=Jan 1).
        melt_months.append(peak_i // 30 + 1)
    return {
        "yearly_peak_cm": peaks,
        "median_peak_cm": float(np.median(peaks)),
        "mean_peak_cm": float(np.mean(peaks)),
        "min_peak_cm": float(np.min(peaks)),
        "max_peak_cm": float(np.max(peaks)),
    }


def calibrate_annual_snow_swe(
    binary, base, out, cells, settings, initial, monthly_csv, template,
    ice_fraction, cell,
):
    """Pick annual SWE (mm) that yields ~40 cm peak snow on control (2009–2018)."""
    target = settings.get("snow_target_peak_cm", 40.0)
    swe_grid = settings.get("snow_swe_calibration", [110.0])
    tr_start = tr_start_from_settings(settings)
    snow_kw = {
        "snow_profile": settings["snow_profile"],
        "snow_target_peak_cm": target,
        "soil_snow_multiplier": settings.get("soil_snow_multiplier", 2.0),
    }
    results = []
    restart, _ = treatment_restart(
        initial, out, "control", ice_fraction, settings, cells, deep_scale=1.0)
    for swe in swe_grid:
        snow_kw["annual_snow_swe_mm"] = swe
        climates, _, _ = prepare_phase1_climates(
            base, out, settings, monthly_csv, template,
            bias_scales={"control": 1.0, "air_warming": 1.0,
                         "soil_warming": 1.0, "air_soil_warming": 1.0},
            bias_profile="default",
            snow_kwargs=snow_kw)
        run_name = f"snow-swe-calibration-{swe:.0f}"
        tbase = json.loads(json.dumps(base))
        tbase["IO"]["hist_climate_file"] = str(climates["control"])
        run(
            binary, out, run_name,
            config(tbase, out / run_name, cells, restart, thermokarst=True,
                   tr_start=tr_start),
            ["--tr-yrs", str(settings["tr_years"])], cells)
        snow = read_daily(out / run_name, "SNOWTHICK")
        metrics = snow_peak_metrics(snow, cell, settings["tr_years"], tr_start)
        row = {"annual_snow_swe_mm": float(swe), **metrics}
        results.append(row)
        print(
            f"snow SWE={swe:.0f} mm: median peak={metrics['median_peak_cm']:.1f} cm "
            f"(range {metrics['min_peak_cm']:.1f}–{metrics['max_peak_cm']:.1f})",
            file=sys.stderr,
        )
    best = min(results, key=lambda r: abs(r["median_peak_cm"] - target))
    return results, best["annual_snow_swe_mm"]


def soil_bias_scales_dict(scale: float) -> dict[str, float]:
    return {
        "control": 1.0,
        "air_warming": 1.0,
        "soil_warming": scale,
        "air_soil_warming": scale,
    }


def calibrate_soil_bias_scale(binary, base, out, cells, settings, initial,
                              monthly_csv, template, ice_fraction, deep_scale, cell):
    """Sweep snow-fence bias scale on soil-warming climate (9 TR yr)."""
    results = []
    for scale in settings["soil_bias_scales"]:
        climates, _, _ = prepare_phase1_climates(
            base, out, settings, monthly_csv, template,
            bias_scales=soil_bias_scales_dict(scale),
            bias_profile=settings.get("bias_profile", "default"))
        restart, _ = treatment_restart(
            initial, out, "soil_warming", ice_fraction, settings, cells, deep_scale=deep_scale)
        run_name = f"bias-calibration-{scale:.1f}"
        tbase = json.loads(json.dumps(base))
        tbase["IO"]["hist_climate_file"] = str(climates["soil_warming"])
        run(
            binary, out, run_name,
            config(tbase, out / run_name, cells, restart, thermokarst=True),
            ["--tr-yrs", str(settings["tr_years"])], cells)
        daily = read_daily(out / run_name, "TKSUBSIDENCE")
        metrics = subsidence_metrics(daily, cell, settings["tr_years"])
        results.append({"scale": scale, **metrics})
        print(f"soil bias scale={scale:.1f}: {metrics['rate_cm_yr']:.3f} cm yr-1",
              file=sys.stderr)
    chosen = pick_soil_bias_scale(results)
    return results, chosen["scale"]


def calibrate_deep_scale_phase3(binary, base, out, cells, settings, monthly_csv, template,
                              ice_fraction, initial, soil_bias_scale, cell):
    """Re-sweep deep-band scale with tuned soil-warming bias."""
    lo, hi, target = OBS_RATES["soil_warming"]
    best = {"scale": settings["deep_scales"][0], "rate": 0.0, "distance": float("inf")}
    in_band = None
    bias_scales = soil_bias_scales_dict(soil_bias_scale)
    for scale in settings["deep_scales"]:
        climates, _, _ = prepare_phase1_climates(
            base, out, settings, monthly_csv, template,
            bias_scales=bias_scales, bias_profile=settings.get("bias_profile", "default"))
        restart, _ = treatment_restart(
            initial, out, "soil_warming", ice_fraction, settings, cells, deep_scale=scale)
        run_name = f"deep-calibration-{scale:.1f}"
        tbase = json.loads(json.dumps(base))
        tbase["IO"]["hist_climate_file"] = str(climates["soil_warming"])
        run(
            binary, out, run_name,
            config(tbase, out / run_name, cells, restart, thermokarst=True),
            ["--tr-yrs", str(settings["tr_years"])], cells)
        daily = read_daily(out / run_name, "TKSUBSIDENCE")
        rate = subsidence_metrics(daily, cell, settings["tr_years"])["rate_cm_yr"]
        print(f"deep scale={scale:.1f}: soil rate={rate:.3f} cm yr-1", file=sys.stderr)
        distance = abs(rate - target)
        row = {"scale": float(scale), "rate": rate, "distance": distance}
        if lo <= rate <= hi and (in_band is None or distance < in_band["distance"]):
            in_band = row
        if distance < best["distance"]:
            best = row
    return in_band or best


def calibrate_phase4_multi_objective(
    binary, base, out, cells, settings, initial, monthly_csv, template,
    ice_fraction, obs_wtd_traj, obs_thaw, cell, slope=0.0,
    snow_kwargs=None,
):
    """Grid search: subsidence + BNZ:554 WTD trajectories + thaw penetration."""
    results = []
    bias_profile = settings.get("bias_profile", "snow_fence")
    tr_start = tr_start_from_settings(settings)
    snow_kwargs = snow_kwargs if snow_kwargs is not None else snow_kwargs_from_settings(settings)
    cal_prefix = "p5" if settings.get("snow_profile") else "p4"
    for winter_extra in settings.get("snow_fence_winter_extra", [1.5]):
        for summer_extra in settings.get("snow_fence_summer_extra", [0.0]):
            climate_kwargs = {
                "winter_extra_c": winter_extra,
                "summer_extra_c": summer_extra,
            }
            for bias_scale in settings["soil_bias_scales"]:
                bias_scales = soil_bias_scales_dict(bias_scale)
                for deep_scale in settings["deep_scales"]:
                    climates, _, _ = prepare_phase1_climates(
                        base, out, settings, monthly_csv, template,
                        bias_scales=bias_scales,
                        bias_profile=bias_profile,
                        climate_kwargs=climate_kwargs,
                        snow_kwargs=snow_kwargs)
                    restarts = {}
                    for treatment in ("control", "soil_warming"):
                        restart, _ = treatment_restart(
                            initial, out, treatment, ice_fraction, settings, cells,
                            deep_scale=deep_scale if treatment in DEEP_TREATMENTS else 1.0)
                        restarts[treatment] = restart
                    run_metrics = {}
                    wtd_traj = {}
                    tp_cm = float("nan")
                    for treatment in ("control", "soil_warming"):
                        tag = (f"{cal_prefix}-w{winter_extra:.1f}-s{summer_extra:.1f}-"
                               f"b{bias_scale:.1f}-d{deep_scale:.1f}-{treatment}")
                        tbase = json.loads(json.dumps(base))
                        tbase["IO"]["hist_climate_file"] = str(climates[treatment])
                        # Spatial inputs live outside run_dir; run() rmtree's the run folder.
                        spatial_dir = out / "cal-spatial" / tag
                        copy_spatial(tbase, spatial_dir, cells, slope=slope)
                        run(
                            binary, out, tag,
                            config(tbase, out / tag, cells, restarts[treatment],
                                   thermokarst=True, tr_start=tr_start),
                            ["--tr-yrs", str(settings["tr_years"])], cells)
                        daily = read_daily(out / tag, "TKSUBSIDENCE")
                        run_metrics[treatment] = subsidence_metrics(
                            daily, cell, settings["tr_years"])
                        wtd_traj[treatment] = summer_wtd_trajectory(
                            out / tag, cell, settings["tr_years"])
                        if treatment == "soil_warming":
                            tp_cm = thaw_penetration_end_cm(
                                out / tag, cell, settings["tr_years"])["thaw_penetration_cm"]
                    score = phase4_calibration_score(
                        run_metrics["soil_warming"]["rate_cm_yr"],
                        wtd_traj["control"],
                        wtd_traj["soil_warming"],
                        tp_cm,
                        obs_wtd_traj,
                        obs_thaw,
                        wtd_years=range(2009, 2009 + settings["tr_years"]),
                    )
                    row = {
                        "winter_extra_c": winter_extra,
                        "summer_extra_c": summer_extra,
                        "bias_scale": bias_scale,
                        "deep_scale": deep_scale,
                        "slope": slope,
                        "score": score,
                        "soil_rate_cm_yr": run_metrics["soil_warming"]["rate_cm_yr"],
                        "control_rate_cm_yr": run_metrics["control"]["rate_cm_yr"],
                        "soil_thaw_penetration_cm": tp_cm,
                        "control_wtd_end_cm": wtd_traj["control"].get(
                            2009 + settings["tr_years"] - 1, float("nan")),
                        "soil_wtd_end_cm": wtd_traj["soil_warming"].get(
                            2009 + settings["tr_years"] - 1, float("nan")),
                    }
                    results.append(row)
                    print(
                        f"Phase4 cal w={winter_extra:.1f} s={summer_extra:.1f} "
                        f"bias={bias_scale:.1f} deep={deep_scale:.1f}: "
                        f"score={score:.2f} soil_rate={row['soil_rate_cm_yr']:.2f} "
                        f"tp={tp_cm:.1f} wtd_end={row['soil_wtd_end_cm']:.1f}",
                        file=sys.stderr,
                    )
    chosen = min(results, key=lambda r: r["score"])
    return results, chosen


def run_treatment_tr(binary, base, out, cells, treatment, climate_path, restart, tr_years):
    tbase = json.loads(json.dumps(base))
    tbase["IO"]["hist_climate_file"] = str(climate_path)
    run_name = f"treatment-{treatment}"
    run(
        binary, out, run_name,
        config(tbase, out / run_name, cells, restart, thermokarst=True),
        ["--tr-yrs", str(tr_years)], cells)
    daily = read_daily(out / run_name, "TKSUBSIDENCE")
    return subsidence_metrics(daily, cells[0], tr_years)


def run_phase0(args):
    settings = PHASES[0]
    cells = settings["cells"]
    out = args.output.resolve()
    if out.exists() and not args.reuse:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    base = production.parse_json_with_comments(ROOT / "config/config.js")
    absolute_io(base)
    copy_spatial(base, out, cells)

    climate = make_synthetic_climate(
        Path(base["IO"]["hist_climate_file"]),
        out / "eml-climate-synthetic.nc",
        settings["climate_nyears"],
    )
    base["IO"]["hist_climate_file"] = str(climate)
    co2 = out / "eml-co2.nc"
    bgc.slice_driver_years(Path(base["IO"]["co2_file"]), co2, 0, settings["climate_nyears"])
    base["IO"]["co2_file"] = str(co2)

    spec = out / "eml-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec)
    base["IO"]["output_spec_file"] = str(spec)

    statuses = {}
    if args.reuse and completed(out, "initialization", cells):
        statuses["initialization"] = completed(out, "initialization", cells)
    else:
        statuses["initialization"] = run(
            args.binary.resolve(), out, "initialization",
            config(base, out / "initialization", cells, output=False, thermokarst=True),
            ["--pr-yrs", "1", "--eq-yrs", str(settings["eq_yrs"])], cells)

    initial = out / "initialization/restart-eq.nc"
    ice_depth = resolve_ice_depth(initial, cells, settings["ice_depth"])
    injected = out / "restart-uniform-ice.nc"
    added = inject_excess_mass(initial, injected, settings["ice_mass"], ice_depth, cells)

    for name, restart, thermokarst in [("ref", initial, True), ("uniform-ice", injected, True)]:
        if args.reuse and completed(out, name, cells):
            statuses[name] = completed(out, name, cells)
        else:
            statuses[name] = run(
                args.binary.resolve(), out, name,
                config(base, out / name, cells, restart, thermokarst=thermokarst),
                ["--tr-yrs", str(settings["tr_years"])], cells)

    sub_ref = read_daily(out / "ref", "TKSUBSIDENCE")
    sub_ice = read_daily(out / "uniform-ice", "TKSUBSIDENCE")
    cell_metrics = {}
    for i, cell in enumerate(cells):
        key = str(cell)
        cell_metrics[key] = {
            "treatment": TREATMENTS[i],
            **subsidence_metrics(sub_ice, cell, settings["tr_years"]),
            "ref_subsidence_m": float(cell_series(sub_ref, cell)[-1]),
            "injected_kg_m2": added[key],
        }

    checks = []

    def gate(test, observed, criterion, ok):
        checks.append({"test": test, "observed": observed, "criterion": criterion,
                       "status": "PASS" if ok else "FAIL"})

    gate("production completion", statuses, "all cells status 100",
         all(v == [100] * len(cells) for v in statuses.values()))
    gate("reference subsidence", {k: v["ref_subsidence_m"] for k, v in cell_metrics.items()},
         "< 1 mm", all(v["ref_subsidence_m"] < 0.001 for v in cell_metrics.values()))
    gate("ice subsidence", {k: v["total_cm"] for k, v in cell_metrics.items()},
         "> 5 mm", all(v["total_cm"] > 0.05 for v in cell_metrics.values()))

    summary = {"phase": 0, "cells": cell_metrics, "checks_passed": sum(c["status"] == "PASS" for c in checks),
               "checks_total": len(checks), "statuses": statuses}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (out / "checks.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=checks[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)
    print(json.dumps(summary, indent=2))
    failed = [x for x in checks if x["status"] == "FAIL"]
    if failed:
        raise RuntimeError(f"{len(failed)} gates failed")


def run_phase1(args):
    settings = PHASES[1]
    cells = settings["cells"]
    cell = cells[0]
    out = args.output.resolve()
    if out.exists() and not args.reuse:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    monthly_csv = OBS_DIR / "eml_healy_monthly_2004-2018.csv"
    if args.fetch or not monthly_csv.exists():
        monthly_csv, source = prepare_monthly_csv(CLIMATE_PKG / "data/cache", OBS_DIR)
    else:
        source = "cached_monthly_csv"

    base = production.parse_json_with_comments(ROOT / "config/config.js")
    absolute_io(base)
    copy_spatial(base, out, cells, slope=0.0)

    template = Path(base["IO"]["hist_climate_file"])
    co2_path = out / "eml-co2.nc"
    if not co2_path.exists():
        bgc.slice_driver_years(Path(base["IO"]["co2_file"]), co2_path, 0,
                                   settings["climate_nyears"])
    base["IO"]["co2_file"] = str(co2_path)

    control_climate = out / "eml-climate-control.nc"
    if not control_climate.exists():
        build_eml_climate(template, control_climate, monthly_csv,
                          treatment="control", nyears=settings["climate_nyears"])

    spec = out / "eml-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec)
    base["IO"]["output_spec_file"] = str(spec)

    init_base = json.loads(json.dumps(base))
    init_base["IO"]["hist_climate_file"] = str(control_climate)
    if args.reuse and completed(out, "initialization", cells):
        statuses = {"initialization": completed(out, "initialization", cells)}
    else:
        statuses = {
            "initialization": run(
                args.binary.resolve(), out, "initialization",
                config(init_base, out / "initialization", cells, output=False, thermokarst=True),
                ["--pr-yrs", "1", "--eq-yrs", str(settings["eq_yrs"])], cells),
        }

    initial = out / "initialization/restart-eq.nc"

    summary_path = out / "summary.json"
    prior = json.loads(summary_path.read_text()) if args.reuse and summary_path.exists() else {}
    calibration = prior.get("calibration", [])
    if calibration and args.reuse and prior.get("calibration_mode") == "shallow_band_fraction":
        chosen = pick_calibrated_fraction(calibration)
        print(f"reusing ice calibration: fraction={chosen['fraction']:.2f}", file=sys.stderr)
        ice_fraction = chosen["fraction"]
    else:
        calibration = []
        climates, _, _ = prepare_phase1_climates(
            base, out, settings, monthly_csv, template)
        for fraction in settings["calibration_fractions"]:
            restart, added = treatment_restart(
                initial, out, "control", fraction, settings, cells)
            run_name = f"calibration-{fraction:.2f}"
            run(
                args.binary.resolve(), out, run_name,
                config(init_base, out / run_name, cells, restart, thermokarst=True),
                ["--tr-yrs", str(settings["tr_years"])], cells)
            daily = read_daily(out / run_name, "TKSUBSIDENCE")
            metrics = subsidence_metrics(daily, cell, settings["tr_years"])
            calibration.append({
                "fraction": fraction,
                "injected_kg_m2": added[str(cell)],
                **metrics,
            })
            print(f"calibration fraction={fraction:.2f}: "
                  f"{metrics['rate_cm_yr']:.3f} cm yr-1", file=sys.stderr)
        chosen = pick_calibrated_fraction(calibration)
        ice_fraction = chosen["fraction"]

    deep_cal = calibrate_deep_scale(
        args.binary.resolve(), base, out, cells, settings,
        monthly_csv, template, ice_fraction, init_base)
    deep_scale = deep_cal["scale"]
    climates, co2_path, climate_meta = prepare_phase1_climates(
        base, out, settings, monthly_csv, template)
    base["IO"]["co2_file"] = co2_path

    treatment_results = {}
    treatment_restarts = {}
    for treatment in TREATMENTS:
        restart, added = treatment_restart(
            initial, out, treatment, ice_fraction, settings, cells,
            deep_scale=deep_scale if treatment in DEEP_TREATMENTS else 1.0)
        treatment_restarts[treatment] = {
            "path": str(restart),
            "injected_kg_m2": added[str(cell)],
            "band_m": [
                settings["ice_top_m"],
                settings["ice_deep_bottom_m"] if treatment in DEEP_TREATMENTS
                else settings["ice_shallow_bottom_m"],
            ],
        }
        treatment_results[treatment] = run_treatment_tr(
            args.binary.resolve(), base, out, cells, treatment,
            climates[treatment], restart, settings["tr_years"])

    ctrl_rate = treatment_results["control"]["rate_cm_yr"]
    soil_rate = treatment_results["soil_warming"]["rate_cm_yr"]
    ratio = soil_rate / ctrl_rate if ctrl_rate > 0 else float("inf")

    checks = []

    def gate(test, observed, criterion, ok, priority="high"):
        checks.append({"test": test, "observed": observed, "criterion": criterion,
                       "status": "PASS" if ok else "FAIL", "priority": priority})

    lo, hi, target = OBS_RATES["control"]
    gate("control subsidence rate", round(ctrl_rate, 3), f"{lo}–{hi} cm yr⁻¹",
         lo <= ctrl_rate <= hi)
    lo, hi, target = OBS_RATES["soil_warming"]
    gate("soil warming subsidence rate", round(soil_rate, 3), f"{lo}–{hi} cm yr⁻¹",
         lo <= soil_rate <= hi, priority="high")
    lo, hi, target = OBS_RATES["air_soil_warming"]
    air_soil_rate = treatment_results["air_soil_warming"]["rate_cm_yr"]
    gate("air+soil subsidence rate", round(air_soil_rate, 3), f"{lo}–{hi} cm yr⁻¹",
         lo <= air_soil_rate <= hi, priority="high")
    gate("soil/control subsidence ratio", round(ratio, 2), f"{RATIO_GATE[0]}–{RATIO_GATE[1]}×",
         RATIO_GATE[0] <= ratio <= RATIO_GATE[1], priority="high")
    air_rate = treatment_results["air_warming"]["rate_cm_yr"]
    gate("air warming ≈ control", round(abs(air_rate - ctrl_rate), 3), "< 0.5 cm yr⁻¹",
         abs(air_rate - ctrl_rate) < 0.5, priority="medium")

    summary = {
        "phase": 1,
        "reference": "Rodenhizer et al. 2020",
        "climate_source": source,
        "monthly_csv": str(monthly_csv),
        "climate_meta": climate_meta,
        "calibration_mode": "shallow_band_fraction",
        "calibration": calibration,
        "chosen_ice_fraction": ice_fraction,
        "deep_scale_calibration": deep_cal,
        "treatment_restarts": treatment_restarts,
        "ice_bands_m": {
            "shallow": [settings["ice_top_m"], settings["ice_shallow_bottom_m"]],
            "deep": [settings["ice_top_m"], settings["ice_deep_bottom_m"]],
        },
        "treatment_results": treatment_results,
        "soil_control_ratio": ratio,
        "checks_passed": sum(c["status"] == "PASS" for c in checks),
        "checks_total": len(checks),
        "statuses": statuses,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (out / "checks.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=checks[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5,
                         "figure.facecolor": "white", "savefig.facecolor": "white"})
    fig, ax = plt.subplots(figsize=(7.2, 4.0), layout="constrained")
    labels = [t.replace("_", "\n") for t in TREATMENTS]
    sim = [treatment_results[t]["rate_cm_yr"] for t in TREATMENTS]
    obs = [OBS_RATES[t][2] for t in TREATMENTS]
    x = np.arange(len(TREATMENTS))
    ax.bar(x - 0.18, sim, 0.36, label="TEM", color=[TREAT_COLOR[t] for t in TREATMENTS])
    ax.bar(x + 0.18, obs, 0.36, label="Rodenhizer 2020", color=MUTED, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Subsidence rate (cm yr⁻¹)")
    ax.set_title(f"Phase 1 EML validation (fraction={ice_fraction:.2f}, "
                 f"shallow/deep bands)")
    ax.legend()
    ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, "eml-subsidence-rates-vs-obs")

    print(json.dumps({
        "phase": 1,
        "checks_passed": summary["checks_passed"],
        "checks_total": summary["checks_total"],
        "chosen_ice_fraction": ice_fraction,
        "rates_cm_yr": {t: treatment_results[t]["rate_cm_yr"] for t in TREATMENTS},
        "soil_control_ratio": ratio,
    }, indent=2))

    failed = [x for x in checks if x["status"] == "FAIL" and x["priority"] == "high"]
    if failed and not args.allow_fail:
        raise RuntimeError(f"{len(failed)} high-priority gates failed: {[x['test'] for x in failed]}")


def run_phase2(args):
    settings = PHASES[2]
    cells = settings["cells"]
    cell = cells[0]
    out = args.output.resolve()
    phase1_dir = Path(args.phase1_dir).resolve()
    if out.exists() and not args.reuse:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    if args.fetch or not (OBS_DIR / "eml_healy_monthly_2004-2018.csv").exists():
        monthly_csv, source = prepare_monthly_csv(CLIMATE_PKG / "data/cache", OBS_DIR, force=args.fetch)
    else:
        monthly_csv = OBS_DIR / "eml_healy_monthly_2004-2018.csv"
        prov = monthly_csv.with_suffix(".provenance.json")
        source = json.loads(prov.read_text())["source"] if prov.exists() else "cached_monthly_csv"

    gps_obs_path = OBS_DIR / "bnz729-gps-subsidence-by-treatment.csv"
    if args.fetch or not gps_obs_path.exists():
        from fetch_bnz729 import build_subsidence_obs  # noqa: E402
        gps_meta = build_subsidence_obs(CLIMATE_PKG / "data/cache", gps_obs_path)
    else:
        prov = gps_obs_path.with_suffix(".provenance.json")
        gps_meta = json.loads(prov.read_text()) if prov.exists() else {}

    copy_phase1_spinup(phase1_dir, out)

    base = production.parse_json_with_comments(ROOT / "config/config.js")
    absolute_io(base)
    copy_spatial(base, out, cells, slope=0.0)

    template = Path(base["IO"]["hist_climate_file"])
    co2_path = out / "eml-co2.nc"
    if not co2_path.exists():
        bgc.slice_driver_years(Path(base["IO"]["co2_file"]), co2_path, 0, settings["climate_nyears"])
    base["IO"]["co2_file"] = str(co2_path)

    climates, _, climate_meta = prepare_phase1_climates(
        base, out, settings, monthly_csv, template)
    spec = out / "eml-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec, include_front=True)
    base["IO"]["output_spec_file"] = str(spec)

    initial = out / "initialization/restart-eq.nc"
    init_base = json.loads(json.dumps(base))
    init_base["IO"]["hist_climate_file"] = str(climates["control"])

    summary_path = out / "summary.json"
    prior = json.loads(summary_path.read_text()) if args.reuse and summary_path.exists() else {}
    do_calibrate = not args.reuse_calibration
    if args.reuse and prior.get("calibration_mode") == "bnz_shallow_band_fraction":
        do_calibrate = False
    if args.recalibrate:
        do_calibrate = True

    calibration = prior.get("calibration", [])
    if do_calibrate:
        calibration, ice_fraction = calibrate_shallow_fraction(
            args.binary.resolve(), init_base, out, cells, settings, initial,
            settings["calibration_fractions"], cell)
        deep_cal = calibrate_deep_scale(
            args.binary.resolve(), base, out, cells, settings,
            monthly_csv, template, ice_fraction, init_base)
        deep_scale = deep_cal["scale"]
        climates, _, climate_meta = prepare_phase1_climates(
            base, out, settings, monthly_csv, template)
    elif prior.get("chosen_ice_fraction") is not None:
        ice_fraction = prior["chosen_ice_fraction"]
        deep_scale = prior.get("deep_scale", load_phase1_ice_params(phase1_dir)["deep_scale"])
        deep_cal = prior.get("deep_scale_calibration", {"scale": deep_scale})
        print(f"reusing BNZ calibration: fraction={ice_fraction:.2f}, "
              f"deep_scale={deep_scale:.1f}", file=sys.stderr)
    else:
        fallback = load_phase1_ice_params(phase1_dir)
        ice_fraction = fallback["ice_fraction"]
        deep_scale = fallback["deep_scale"]
        deep_cal = {"scale": deep_scale, "note": "phase1 fallback (no BNZ recalibration)"}
        print("warning: using Phase 1 ice params; run with --recalibrate for BNZ tuning",
              file=sys.stderr)

    treatment_restarts = {}
    for treatment in TREATMENTS:
        restart, added = treatment_restart(
            initial, out, treatment, ice_fraction, settings, cells,
            deep_scale=deep_scale if treatment in DEEP_TREATMENTS else 1.0)
        treatment_restarts[treatment] = {
            "path": str(restart),
            "injected_kg_m2": added[str(cell)],
            "band_m": [
                settings["ice_top_m"],
                settings["ice_deep_bottom_m"] if treatment in DEEP_TREATMENTS
                else settings["ice_shallow_bottom_m"],
            ],
        }

    statuses = {"initialization": [100]}
    treatment_results = {}
    thaw_results = {}
    for treatment in TREATMENTS:
        run_name = f"treatment-{treatment}"
        if args.reuse and completed(out, run_name, cells):
            statuses[run_name] = completed(out, run_name, cells)
        else:
            tbase = json.loads(json.dumps(base))
            tbase["IO"]["hist_climate_file"] = str(climates[treatment])
            statuses[run_name] = run(
                args.binary.resolve(), out, run_name,
                config(tbase, out / run_name, cells,
                       Path(treatment_restarts[treatment]["path"]), thermokarst=True),
                ["--tr-yrs", str(settings["tr_years"])], cells)
        daily = read_daily(out / run_name, "TKSUBSIDENCE")
        treatment_results[treatment] = subsidence_metrics(daily, cell, settings["tr_years"])
        thaw_results[treatment] = thaw_penetration_end_cm(
            out / run_name, cell, settings["tr_years"])

    # Longer TR sensitivity for soil warming (deep-ice thaw).
    sens_years = settings["tr_sensitivity_years"]
    sens_name = f"sensitivity-soil-warming-{sens_years}yr"
    if args.reuse and completed(out, sens_name, cells):
        statuses[sens_name] = completed(out, sens_name, cells)
    else:
        tbase = json.loads(json.dumps(base))
        tbase["IO"]["hist_climate_file"] = str(climates["soil_warming"])
        statuses[sens_name] = run(
            args.binary.resolve(), out, sens_name,
            config(tbase, out / sens_name, cells,
                   Path(treatment_restarts["soil_warming"]["path"]), thermokarst=True),
            ["--tr-yrs", str(sens_years)], cells)
    sens_daily = read_daily(out / sens_name, "TKSUBSIDENCE")
    sensitivity = {
        "tr_years": sens_years,
        **subsidence_metrics(sens_daily, cell, sens_years),
        **thaw_penetration_end_cm(out / sens_name, cell, sens_years),
    }

    obs_thaw = load_obs_thaw(OBS_DIR / "rodenhizer-thaw-penetration-2018.csv")
    gps_obs = load_gps_obs(gps_obs_path)
    ctrl_rate = treatment_results["control"]["rate_cm_yr"]
    soil_rate = treatment_results["soil_warming"]["rate_cm_yr"]
    ratio = soil_rate / ctrl_rate if ctrl_rate > 0 else float("inf")

    checks = []

    def gate(test, observed, criterion, ok, priority="high"):
        checks.append({"test": test, "observed": observed, "criterion": criterion,
                       "status": "PASS" if ok else "FAIL", "priority": priority})

    lo, hi, _ = OBS_RATES["control"]
    gate("control subsidence rate", round(ctrl_rate, 3), f"{lo}–{hi} cm yr⁻¹",
         lo <= ctrl_rate <= hi)
    lo, hi, _ = OBS_RATES["soil_warming"]
    gate("soil warming subsidence rate", round(soil_rate, 3), f"{lo}–{hi} cm yr⁻¹",
         lo <= soil_rate <= hi, priority="high")
    gate("soil/control subsidence ratio", round(ratio, 2), f"{RATIO_GATE[0]}–{RATIO_GATE[1]}×",
         RATIO_GATE[0] <= ratio <= RATIO_GATE[1], priority="high")

    for treatment in ("control", "soil_warming"):
        obs = obs_thaw[treatment]
        sim = thaw_results[treatment]
        tol = 2.0 * obs["se_thaw_penetration_cm"]
        lo_tp = obs["thaw_penetration_cm"] - tol
        hi_tp = obs["thaw_penetration_cm"] + tol
        tp = round(sim["thaw_penetration_cm"], 1)
        gate(f"{treatment} thaw penetration 2018", tp,
             f"{lo_tp:.1f}–{hi_tp:.1f} cm (obs {obs['thaw_penetration_cm']:.1f})",
             lo_tp <= sim["thaw_penetration_cm"] <= hi_tp, priority="high")
        tol_alt = 2.0 * obs["se_alt_cm"]
        gate(f"{treatment} ALT (Sept max) 2018", round(sim["alt_cm"], 1),
             f"{obs['alt_cm'] - tol_alt:.1f}–{obs['alt_cm'] + tol_alt:.1f} cm",
             obs["alt_cm"] - tol_alt <= sim["alt_cm"] <= obs["alt_cm"] + tol_alt,
             priority="medium")

    ctrl_tp = thaw_results["control"]["thaw_penetration_cm"]
    soil_tp = thaw_results["soil_warming"]["thaw_penetration_cm"]
    if ctrl_tp > 0 and np.isfinite(soil_tp):
        sim_pct = 100.0 * (soil_tp - ctrl_tp) / ctrl_tp
        obs_pct = obs_thaw["soil_warming"]["thaw_penetration_increase_pct"]
        gate("soil vs control TP increase", round(sim_pct, 1),
             f"~{obs_pct:.0f}% (Rodenhizer 2018)", abs(sim_pct - obs_pct) <= 20.0,
             priority="medium")

    gate(f"soil warming {sens_years}-yr rate", round(sensitivity["rate_cm_yr"], 3),
         f"> {soil_rate:.2f} cm yr⁻¹ (9-yr run)",
         sensitivity["rate_cm_yr"] >= soil_rate, priority="medium")

    summary = {
        "phase": 2,
        "reference": "Rodenhizer et al. 2020",
        "climate_source": source,
        "monthly_csv": str(monthly_csv),
        "climate_meta": climate_meta,
        "phase1_dir": str(phase1_dir),
        "calibration_mode": "bnz_shallow_band_fraction" if do_calibrate or prior.get("calibration_mode") else "phase1_fallback",
        "calibration": calibration,
        "chosen_ice_fraction": ice_fraction,
        "deep_scale_calibration": deep_cal,
        "deep_scale": deep_scale,
        "treatment_restarts": treatment_restarts,
        "treatment_results": treatment_results,
        "thaw_penetration": thaw_results,
        "tr_sensitivity": sensitivity,
        "gps_obs_meta": gps_meta,
        "soil_control_ratio": ratio,
        "checks_passed": sum(c["status"] == "PASS" for c in checks),
        "checks_total": len(checks),
        "statuses": statuses,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (out / "checks.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=checks[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5,
                         "figure.facecolor": "white", "savefig.facecolor": "white"})

    fig, ax = plt.subplots(figsize=(7.2, 4.0), layout="constrained")
    labels = [t.replace("_", "\n") for t in TREATMENTS]
    sim = [treatment_results[t]["rate_cm_yr"] for t in TREATMENTS]
    obs_rates = [OBS_RATES[t][2] for t in TREATMENTS]
    x = np.arange(len(TREATMENTS))
    ax.bar(x - 0.18, sim, 0.36, label="TEM (BNZ climate)", color=[TREAT_COLOR[t] for t in TREATMENTS])
    ax.bar(x + 0.18, obs_rates, 0.36, label="Rodenhizer 2020", color=MUTED, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Subsidence rate (cm yr⁻¹)")
    ax.set_title(f"Phase 2 EML validation (BNZ:453, f={ice_fraction:.2f}, d={deep_scale:.1f})")
    ax.legend()
    ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, "eml-subsidence-rates-vs-obs")

    fig, ax = plt.subplots(figsize=(7.2, 4.0), layout="constrained")
    gps_years = sorted(gps_obs.get("control", {}))
    tem_years = list(range(2009, 2009 + settings["tr_years"]))
    for treatment, color, label in [
            ("control", TEAL, "Control"),
            ("soil_warming", ORANGE, "Soil warming")]:
        if treatment in gps_obs:
            gy = [y for y in gps_years if y in gps_obs[treatment]]
            ax.plot(gy, [gps_obs[treatment][y] for y in gy], "o-", color=color,
                    label=f"{label} GPS (BNZ:729)", ms=4)
        run_name = f"treatment-{treatment}"
        sub = read_daily(out / run_name, "TKSUBSIDENCE")
        cum = yearly_subsidence_cm(sub, cell, settings["tr_years"])
        ax.plot(tem_years, cum, "--", color=color, label=f"{label} TEM")
    ax.set_xlabel("Calendar year")
    ax.set_ylabel("Cumulative subsidence (cm)")
    ax.set_title("GPS vs TEM cumulative subsidence (2009 baseline)")
    ax.legend(fontsize=7)
    ax.grid(color=GRID, lw=0.6)
    save(fig, out, "eml-gps-vs-tem-subsidence")

    print(json.dumps({
        "phase": 2,
        "climate_source": source,
        "checks_passed": summary["checks_passed"],
        "checks_total": summary["checks_total"],
        "rates_cm_yr": {t: treatment_results[t]["rate_cm_yr"] for t in TREATMENTS},
        "thaw_penetration_cm": {t: thaw_results[t]["thaw_penetration_cm"] for t in TREATMENTS},
        "sensitivity_rate_cm_yr": sensitivity["rate_cm_yr"],
    }, indent=2))

    failed = [x for x in checks if x["status"] == "FAIL" and x["priority"] == "high"]
    if failed and not args.allow_fail:
        raise RuntimeError(f"{len(failed)} high-priority gates failed: {[x['test'] for x in failed]}")


def run_phase3(args):
    settings = PHASES[3]
    cells = settings["cells"]
    cell = cells[0]
    out = args.output.resolve()
    phase1_dir = Path(args.phase1_dir).resolve()
    phase2_dir = Path(args.phase2_dir).resolve()

    if out.exists() and not args.reuse:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    if args.fetch or not (OBS_DIR / "eml_healy_monthly_2004-2018.csv").exists():
        monthly_csv, source = prepare_monthly_csv(
            CLIMATE_PKG / "data/cache", OBS_DIR, force=args.fetch)
    else:
        monthly_csv = OBS_DIR / "eml_healy_monthly_2004-2018.csv"
        prov = monthly_csv.with_suffix(".provenance.json")
        source = json.loads(prov.read_text())["source"] if prov.exists() else "cached_monthly_csv"

    gps_obs_path = OBS_DIR / "bnz729-gps-subsidence-by-treatment.csv"
    if args.fetch or not gps_obs_path.exists():
        from fetch_bnz729 import build_subsidence_obs  # noqa: E402
        gps_meta = build_subsidence_obs(CLIMATE_PKG / "data/cache", gps_obs_path)
    else:
        prov = gps_obs_path.with_suffix(".provenance.json")
        gps_meta = json.loads(prov.read_text()) if prov.exists() else {}

    wtd_obs_path = OBS_DIR / "bnz554-water-table-by-treatment.csv"
    if args.fetch or not wtd_obs_path.exists():
        from fetch_bnz554 import build_water_table_obs  # noqa: E402
        wtd_meta = build_water_table_obs(CLIMATE_PKG / "data/cache", wtd_obs_path)
    else:
        prov = wtd_obs_path.with_suffix(".provenance.json")
        wtd_meta = json.loads(prov.read_text()) if prov.exists() else {}

    ice = load_phase2_ice_params(phase2_dir)
    ice_fraction = ice["ice_fraction"]
    copy_phase1_spinup(phase1_dir, out)

    base = production.parse_json_with_comments(ROOT / "config/config.js")
    absolute_io(base)
    copy_spatial(base, out, cells, slope=0.0)
    template = Path(base["IO"]["hist_climate_file"])
    co2_path = out / "eml-co2.nc"
    if not co2_path.exists():
        bgc.slice_driver_years(Path(base["IO"]["co2_file"]), co2_path, 0, settings["climate_nyears"])
    base["IO"]["co2_file"] = str(co2_path)

    spec = out / "eml-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec,
              include_front=True, include_watertab=True, include_profile=True)
    base["IO"]["output_spec_file"] = str(spec)

    initial = out / "initialization/restart-eq.nc"
    summary_path = out / "summary.json"
    prior = json.loads(summary_path.read_text()) if args.reuse and summary_path.exists() else {}

    do_tune = not args.reuse_calibration
    if args.reuse and prior.get("calibration_mode") == "snow_fence_bias_deep":
        do_tune = False
    if args.recalibrate:
        do_tune = True

    soil_bias_cal = prior.get("soil_bias_calibration", [])
    if do_tune:
        soil_bias_cal, soil_bias_scale = calibrate_soil_bias_scale(
            args.binary.resolve(), base, out, cells, settings, initial,
            monthly_csv, template, ice_fraction, ice["deep_scale"], cell)
        deep_cal = calibrate_deep_scale_phase3(
            args.binary.resolve(), base, out, cells, settings,
            monthly_csv, template, ice_fraction, initial, soil_bias_scale, cell)
        deep_scale = deep_cal["scale"]
    else:
        soil_bias_scale = prior.get("chosen_soil_bias_scale", 2.0)
        deep_scale = prior.get("deep_scale", ice["deep_scale"])
        deep_cal = prior.get("deep_scale_calibration", {"scale": deep_scale})
        print(f"reusing Phase 3 tuning: bias_scale={soil_bias_scale:.1f}, "
              f"deep_scale={deep_scale:.1f}", file=sys.stderr)

    bias_scales = soil_bias_scales_dict(soil_bias_scale)
    climates, _, climate_meta = prepare_phase1_climates(
        base, out, settings, monthly_csv, template,
        bias_scales=bias_scales, bias_profile=settings["bias_profile"])

    treatment_restarts = {}
    for treatment in TREATMENTS:
        restart, added = treatment_restart(
            initial, out, treatment, ice_fraction, settings, cells,
            deep_scale=deep_scale if treatment in DEEP_TREATMENTS else 1.0)
        treatment_restarts[treatment] = {
            "path": str(restart),
            "injected_kg_m2": added[str(cell)],
        }

    statuses = {"initialization": [100]}
    treatment_results = {}
    thaw_results = {}
    water_table = {}
    for treatment in TREATMENTS:
        run_name = f"treatment-{treatment}"
        if args.reuse and completed(out, run_name, cells):
            statuses[run_name] = completed(out, run_name, cells)
        else:
            tbase = json.loads(json.dumps(base))
            tbase["IO"]["hist_climate_file"] = str(climates[treatment])
            statuses[run_name] = run(
                args.binary.resolve(), out, run_name,
                config(tbase, out / run_name, cells,
                       Path(treatment_restarts[treatment]["path"]), thermokarst=True),
                ["--tr-yrs", str(settings["tr_years"])], cells)
        daily = read_daily(out / run_name, "TKSUBSIDENCE")
        treatment_results[treatment] = subsidence_metrics(daily, cell, settings["tr_years"])
        thaw_results[treatment] = thaw_penetration_end_cm(
            out / run_name, cell, settings["tr_years"])
        water_table[treatment] = {
            "2009_summer_cm": summer_mean_wtd_cm(out / run_name, cell, settings["tr_years"], 0),
            "2018_summer_cm": summer_mean_wtd_cm(
                out / run_name, cell, settings["tr_years"], settings["tr_years"] - 1),
        }

    ext_years = settings["tr_extended_years"]
    extended = {}
    for treatment in DEEP_TREATMENTS:
        run_name = f"extended-{treatment}-{ext_years}yr"
        if args.reuse and completed(out, run_name, cells):
            statuses[run_name] = completed(out, run_name, cells)
        else:
            tbase = json.loads(json.dumps(base))
            tbase["IO"]["hist_climate_file"] = str(climates[treatment])
            statuses[run_name] = run(
                args.binary.resolve(), out, run_name,
                config(tbase, out / run_name, cells,
                       Path(treatment_restarts[treatment]["path"]), thermokarst=True),
                ["--tr-yrs", str(ext_years)], cells)
        daily = read_daily(out / run_name, "TKSUBSIDENCE")
        extended[treatment] = {
            "tr_years": ext_years,
            **subsidence_metrics(daily, cell, ext_years),
            **thaw_penetration_end_cm(out / run_name, cell, ext_years),
        }

    obs_thaw = load_obs_thaw(OBS_DIR / "rodenhizer-thaw-penetration-2018.csv")
    obs_wtd = load_obs_water_table(OBS_DIR / "rodenhizer-water-table.csv")
    gps_obs = load_gps_obs(gps_obs_path)
    ctrl_rate = treatment_results["control"]["rate_cm_yr"]
    soil_rate = treatment_results["soil_warming"]["rate_cm_yr"]
    ratio = soil_rate / ctrl_rate if ctrl_rate > 0 else float("inf")

    checks = []

    def gate(test, observed, criterion, ok, priority="high"):
        checks.append({"test": test, "observed": observed, "criterion": criterion,
                       "status": "PASS" if ok else "FAIL", "priority": priority})

    lo, hi, _ = OBS_RATES["control"]
    gate("control subsidence rate", round(ctrl_rate, 3), f"{lo}–{hi} cm yr⁻¹",
         lo <= ctrl_rate <= hi)
    lo, hi, _ = OBS_RATES["soil_warming"]
    gate("soil warming subsidence rate", round(soil_rate, 3), f"{lo}–{hi} cm yr⁻¹",
         lo <= soil_rate <= hi, priority="high")
    gate("soil/control subsidence ratio", round(ratio, 2), f"{RATIO_GATE[0]}–{RATIO_GATE[1]}×",
         RATIO_GATE[0] <= ratio <= RATIO_GATE[1], priority="high")

    for treatment in ("control", "soil_warming"):
        obs = obs_thaw[treatment]
        sim = thaw_results[treatment]
        tol = 2.0 * obs["se_thaw_penetration_cm"]
        gate(f"{treatment} thaw penetration 2018", round(sim["thaw_penetration_cm"], 1),
             f"{obs['thaw_penetration_cm'] - tol:.1f}–{obs['thaw_penetration_cm'] + tol:.1f} cm",
             obs["thaw_penetration_cm"] - tol <= sim["thaw_penetration_cm"] <= obs["thaw_penetration_cm"] + tol,
             priority="high")

    for treatment in ("control", "soil_warming"):
        for year_label, year_idx, cal_year in [("2009", 0, 2009), ("2018", settings["tr_years"] - 1, 2018)]:
            obs_key = (treatment, cal_year)
            if obs_key not in obs_wtd:
                continue
            obs = obs_wtd[obs_key]
            sim = water_table[treatment][f"{cal_year}_summer_cm"]
            tol = 2.0 * obs["se_cm"]
            gate(f"{treatment} water table {year_label}",
                 round(sim, 1) if np.isfinite(sim) else "nan",
                 f"{obs['depth_cm'] - tol:.1f}–{obs['depth_cm'] + tol:.1f} cm",
                 np.isfinite(sim) and obs["depth_cm"] - tol <= sim <= obs["depth_cm"] + tol,
                 priority="medium")

    soil18 = water_table["soil_warming"].get("2018_summer_cm", float("nan"))
    ctrl18 = water_table["control"].get("2018_summer_cm", float("nan"))
    if np.isfinite(soil18) and np.isfinite(ctrl18):
        gate("soil WTD shallower than control (2018)", round(soil18 - ctrl18, 1),
             "< 0 cm (soil closer to surface)", soil18 < ctrl18, priority="medium")

    ext_soil = extended.get("soil_warming", {})
    if ext_soil:
        gate(f"soil {ext_years}-yr subsidence total", round(ext_soil.get("total_cm", 0), 1),
             f"> {treatment_results['soil_warming']['total_cm']:.1f} cm (9-yr)",
             ext_soil.get("total_cm", 0) > treatment_results["soil_warming"]["total_cm"],
             priority="medium")

    summary = {
        "phase": 3,
        "reference": "Rodenhizer et al. 2020",
        "climate_source": source,
        "bias_profile": settings["bias_profile"],
        "chosen_soil_bias_scale": soil_bias_scale,
        "soil_bias_calibration": soil_bias_cal,
        "phase2_dir": str(phase2_dir),
        "chosen_ice_fraction": ice_fraction,
        "deep_scale_calibration": deep_cal,
        "deep_scale": deep_scale,
        "calibration_mode": "snow_fence_bias_deep",
        "treatment_restarts": treatment_restarts,
        "treatment_results": treatment_results,
        "thaw_penetration": thaw_results,
        "water_table": water_table,
        "tr_extended": extended,
        "gps_obs_meta": gps_meta,
        "wtd_obs_meta": wtd_meta,
        "soil_control_ratio": ratio,
        "checks_passed": sum(c["status"] == "PASS" for c in checks),
        "checks_total": len(checks),
        "statuses": statuses,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (out / "checks.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=checks[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5,
                         "figure.facecolor": "white", "savefig.facecolor": "white"})

    fig, ax = plt.subplots(figsize=(7.2, 4.0), layout="constrained")
    x = np.arange(len(TREATMENTS))
    sim = [treatment_results[t]["rate_cm_yr"] for t in TREATMENTS]
    obs_rates = [OBS_RATES[t][2] for t in TREATMENTS]
    ax.bar(x - 0.18, sim, 0.36, label="TEM Phase 3", color=[TREAT_COLOR[t] for t in TREATMENTS])
    ax.bar(x + 0.18, obs_rates, 0.36, label="Rodenhizer 2020", color=MUTED, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace("_", "\n") for t in TREATMENTS])
    ax.set_ylabel("Subsidence rate (cm yr⁻¹)")
    ax.set_title(f"Phase 3 (snow-fence bias×{soil_bias_scale:.1f}, f={ice_fraction:.2f}, d={deep_scale:.1f})")
    ax.legend()
    ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, "eml-subsidence-rates-vs-obs")

    fig, ax = plt.subplots(figsize=(8.0, 4.2), layout="constrained")
    for treatment, color, label in [
            ("control", TEAL, "Control"),
            ("soil_warming", ORANGE, "Soil warming")]:
        if treatment in gps_obs:
            gy = sorted(gps_obs[treatment])
            ax.plot(gy, [gps_obs[treatment][y] for y in gy], "o-", color=color,
                    label=f"{label} GPS", ms=3, lw=1)
        run_9 = f"treatment-{treatment}"
        sub9 = read_daily(out / run_9, "TKSUBSIDENCE")
        ax.plot(list(range(2009, 2009 + settings["tr_years"])),
                yearly_subsidence_cm(sub9, cell, settings["tr_years"]),
                "--", color=color, lw=1, label=f"{label} TEM 9 yr")
        if treatment in extended:
            run_ext = f"extended-{treatment}-{ext_years}yr"
            sub_ext = read_daily(out / run_ext, "TKSUBSIDENCE")
            ax.plot(list(range(2009, 2009 + ext_years)),
                    yearly_subsidence_cm(sub_ext, cell, ext_years),
                    ":", color=color, lw=1.2, label=f"{label} TEM {ext_years} yr")
    ax.set_xlabel("Calendar year")
    ax.set_ylabel("Cumulative subsidence (cm)")
    ax.set_title("GPS (2009–2024) vs TEM cumulative subsidence")
    ax.legend(fontsize=6, ncol=2)
    ax.grid(color=GRID, lw=0.6)
    save(fig, out, "eml-gps-vs-tem-subsidence-extended")

    print(json.dumps({
        "phase": 3,
        "checks_passed": summary["checks_passed"],
        "checks_total": summary["checks_total"],
        "chosen_soil_bias_scale": soil_bias_scale,
        "deep_scale": deep_scale,
        "rates_cm_yr": {t: treatment_results[t]["rate_cm_yr"] for t in TREATMENTS},
        "extended_soil_rate_cm_yr": extended.get("soil_warming", {}).get("rate_cm_yr"),
    }, indent=2))

    _maybe_generate_thermal_plots(args, out, settings, cell)

    failed = [x for x in checks if x["status"] == "FAIL" and x["priority"] == "high"]
    if failed and not args.allow_fail:
        raise RuntimeError(f"{len(failed)} high-priority gates failed: {[x['test'] for x in failed]}")


def run_phase4(args, phase=4):
    settings = PHASES[phase]
    phase_label = f"Phase {phase}"
    cells = settings["cells"]
    cell = cells[0]
    out = args.output.resolve()
    phase1_dir = Path(args.phase1_dir).resolve()
    phase2_dir = Path(args.phase2_dir).resolve()

    if out.exists() and not args.reuse:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    if args.fetch or not (OBS_DIR / "eml_healy_monthly_2004-2018.csv").exists():
        monthly_csv, source = prepare_monthly_csv(
            CLIMATE_PKG / "data/cache", OBS_DIR, force=args.fetch)
    else:
        monthly_csv = OBS_DIR / "eml_healy_monthly_2004-2018.csv"
        prov = monthly_csv.with_suffix(".provenance.json")
        source = json.loads(prov.read_text())["source"] if prov.exists() else "cached_monthly_csv"

    gps_obs_path = OBS_DIR / "bnz729-gps-subsidence-by-treatment.csv"
    if args.fetch or not gps_obs_path.exists():
        from fetch_bnz729 import build_subsidence_obs  # noqa: E402
        gps_meta = build_subsidence_obs(CLIMATE_PKG / "data/cache", gps_obs_path)
    else:
        prov = gps_obs_path.with_suffix(".provenance.json")
        gps_meta = json.loads(prov.read_text()) if prov.exists() else {}

    wtd_obs_path = OBS_DIR / "bnz554-water-table-by-treatment.csv"
    if args.fetch or not wtd_obs_path.exists():
        from fetch_bnz554 import build_water_table_obs  # noqa: E402
        wtd_meta = build_water_table_obs(CLIMATE_PKG / "data/cache", wtd_obs_path)
    else:
        prov = wtd_obs_path.with_suffix(".provenance.json")
        wtd_meta = json.loads(prov.read_text()) if prov.exists() else {}

    obs_wtd_traj = load_bnz554_trajectory(wtd_obs_path)
    obs_thaw = load_obs_thaw(OBS_DIR / "rodenhizer-thaw-penetration-2018.csv")
    obs_wtd_point = load_obs_water_table(OBS_DIR / "rodenhizer-water-table.csv")

    ice = load_phase2_ice_params(phase2_dir)
    ice_fraction = ice["ice_fraction"]
    copy_phase1_spinup(phase1_dir, out)

    base = production.parse_json_with_comments(ROOT / "config/config.js")
    absolute_io(base)
    slope = settings["slopes"][0]
    copy_spatial(base, out, cells, slope=slope)
    template = Path(base["IO"]["hist_climate_file"])
    co2_path = out / "eml-co2.nc"
    if not co2_path.exists():
        bgc.slice_driver_years(Path(base["IO"]["co2_file"]), co2_path, 0, settings["climate_nyears"])
    base["IO"]["co2_file"] = str(co2_path)

    spec = out / "eml-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec,
              include_front=True, include_watertab=True, include_profile=True)
    base["IO"]["output_spec_file"] = str(spec)

    initial = out / "initialization/restart-eq.nc"
    summary_path = out / "summary.json"
    prior = json.loads(summary_path.read_text()) if args.reuse and summary_path.exists() else {}
    tr_start = tr_start_from_settings(settings)

    annual_snow_swe_mm = prior.get(
        "annual_snow_swe_mm", settings.get("annual_snow_swe_mm", 110.0))
    snow_cal_results = prior.get("snow_swe_calibration", [])
    do_snow_tune = (
        settings.get("snow_profile")
        and not args.reuse_calibration
        and (args.recalibrate or not prior.get("annual_snow_swe_mm"))
    )
    if do_snow_tune:
        snow_cal_results, annual_snow_swe_mm = calibrate_annual_snow_swe(
            args.binary.resolve(), base, out, cells, settings, initial,
            monthly_csv, template, ice_fraction, cell)
        settings = dict(settings)
        settings["annual_snow_swe_mm"] = annual_snow_swe_mm
        (out / "snow-swe-calibration.json").write_text(
            json.dumps({"chosen_annual_snow_swe_mm": annual_snow_swe_mm,
                        "grid": snow_cal_results}, indent=2) + "\n")
        print(f"chosen annual snow SWE: {annual_snow_swe_mm:.0f} mm", file=sys.stderr)

    snow_kwargs = snow_kwargs_from_settings(settings)
    if snow_kwargs:
        snow_kwargs["annual_snow_swe_mm"] = annual_snow_swe_mm

    do_tune = not args.reuse_calibration
    if args.reuse and prior.get("calibration_mode") == "multi_objective_wtd_tp":
        do_tune = False
    if args.recalibrate:
        do_tune = True

    if do_tune:
        cal_results, chosen = calibrate_phase4_multi_objective(
            args.binary.resolve(), base, out, cells, settings, initial,
            monthly_csv, template, ice_fraction, obs_wtd_traj, obs_thaw, cell,
            slope=slope, snow_kwargs=snow_kwargs)
        soil_bias_scale = chosen["bias_scale"]
        deep_scale = chosen["deep_scale"]
        winter_extra = chosen["winter_extra_c"]
        summer_extra = chosen["summer_extra_c"]
        slope = chosen["slope"]
        if slope != settings["slopes"][0]:
            copy_spatial(base, out, cells, slope=slope)
        (out / "calibration-chosen.json").write_text(json.dumps(chosen, indent=2) + "\n")
    else:
        cal_results = prior.get("multi_objective_calibration", [])
        chosen_path = out / "calibration-chosen.json"
        chosen_prior = json.loads(chosen_path.read_text()) if chosen_path.exists() else {}
        soil_bias_scale = prior.get(
            "chosen_soil_bias_scale", chosen_prior.get("bias_scale", 2.5))
        deep_scale = prior.get("deep_scale", chosen_prior.get("deep_scale", 2.0))
        winter_extra = prior.get(
            "snow_fence_winter_extra_c", chosen_prior.get("winter_extra_c", 1.5))
        summer_extra = prior.get(
            "snow_fence_summer_extra_c", chosen_prior.get("summer_extra_c", 0.0))
        slope = prior.get("slope", chosen_prior.get("slope", settings["slopes"][0]))
        annual_snow_swe_mm = prior.get(
            "annual_snow_swe_mm", settings.get("annual_snow_swe_mm", 110.0))
        snow_cal_results = prior.get("snow_swe_calibration", snow_cal_results)
        print(
            f"reusing {phase_label} tuning: bias={soil_bias_scale:.1f}, deep={deep_scale:.1f}, "
            f"winter+={winter_extra:.1f}, summer+={summer_extra:.1f}, slope={slope:.1f}, "
            f"snow_swe={annual_snow_swe_mm:.0f} mm",
            file=sys.stderr,
        )

    climate_kwargs = {"winter_extra_c": winter_extra, "summer_extra_c": summer_extra}
    bias_scales = soil_bias_scales_dict(soil_bias_scale)
    climates, _, climate_meta = prepare_phase1_climates(
        base, out, settings, monthly_csv, template,
        bias_scales=bias_scales,
        bias_profile=settings["bias_profile"],
        climate_kwargs=climate_kwargs,
        snow_kwargs=snow_kwargs)

    if settings.get("snow_profile"):
        from write_snow_precip_csv import write_cipehr_snow_precip_csv  # noqa: E402
        snow_csv = OBS_DIR / "eml_cipehr_snow_precip_2009-2018.csv"
        write_cipehr_snow_precip_csv(
            monthly_csv, snow_csv, annual_swe_mm=annual_snow_swe_mm)

    treatment_restarts = {}
    for treatment in TREATMENTS:
        restart, added = treatment_restart(
            initial, out, treatment, ice_fraction, settings, cells,
            deep_scale=deep_scale if treatment in DEEP_TREATMENTS else 1.0)
        treatment_restarts[treatment] = {
            "path": str(restart),
            "injected_kg_m2": added[str(cell)],
        }

    statuses = {"initialization": [100]}
    treatment_results = {}
    thaw_results = {}
    water_table = {}
    wtd_trajectories = {}
    for treatment in TREATMENTS:
        run_name = f"treatment-{treatment}"
        if args.reuse and completed(out, run_name, cells):
            statuses[run_name] = completed(out, run_name, cells)
        else:
            tbase = json.loads(json.dumps(base))
            tbase["IO"]["hist_climate_file"] = str(climates[treatment])
            statuses[run_name] = run(
                args.binary.resolve(), out, run_name,
                config(tbase, out / run_name, cells,
                       Path(treatment_restarts[treatment]["path"]), thermokarst=True,
                       tr_start=tr_start),
                ["--tr-yrs", str(settings["tr_years"])], cells)
        daily = read_daily(out / run_name, "TKSUBSIDENCE")
        treatment_results[treatment] = subsidence_metrics(daily, cell, settings["tr_years"])
        thaw_results[treatment] = thaw_penetration_end_cm(
            out / run_name, cell, settings["tr_years"])
        wtd_trajectories[treatment] = summer_wtd_trajectory(
            out / run_name, cell, settings["tr_years"])
        water_table[treatment] = {
            "2009_summer_cm": wtd_trajectories[treatment].get(2009, float("nan")),
            "2018_summer_cm": wtd_trajectories[treatment].get(2018, float("nan")),
        }

    snow_metrics = {}
    for treatment in ("control", "soil_warming"):
        snow = read_daily(out / f"treatment-{treatment}", "SNOWTHICK")
        snow_metrics[treatment] = snow_peak_metrics(
            snow, cell, settings["tr_years"], tr_start)

    ext_years = settings["tr_extended_years"]
    extended = {}
    for treatment in DEEP_TREATMENTS:
        run_name = f"extended-{treatment}-{ext_years}yr"
        if args.reuse and completed(out, run_name, cells):
            statuses[run_name] = completed(out, run_name, cells)
        else:
            tbase = json.loads(json.dumps(base))
            tbase["IO"]["hist_climate_file"] = str(climates[treatment])
            statuses[run_name] = run(
                args.binary.resolve(), out, run_name,
                config(tbase, out / run_name, cells,
                       Path(treatment_restarts[treatment]["path"]), thermokarst=True,
                       tr_start=tr_start),
                ["--tr-yrs", str(ext_years)], cells)
        daily = read_daily(out / run_name, "TKSUBSIDENCE")
        extended[treatment] = {
            "tr_years": ext_years,
            **subsidence_metrics(daily, cell, ext_years),
            **thaw_penetration_end_cm(out / run_name, cell, ext_years),
        }

    gps_obs = load_gps_obs(gps_obs_path)
    ctrl_rate = treatment_results["control"]["rate_cm_yr"]
    soil_rate = treatment_results["soil_warming"]["rate_cm_yr"]
    ratio = soil_rate / ctrl_rate if ctrl_rate > 0 else float("inf")

    checks = []

    def gate(test, observed, criterion, ok, priority="high"):
        checks.append({"test": test, "observed": observed, "criterion": criterion,
                       "status": "PASS" if ok else "FAIL", "priority": priority})

    lo, hi, _ = OBS_RATES["control"]
    gate("control subsidence rate", round(ctrl_rate, 3), f"{lo}–{hi} cm yr⁻¹",
         lo <= ctrl_rate <= hi)
    lo, hi, _ = OBS_RATES["soil_warming"]
    gate("soil warming subsidence rate", round(soil_rate, 3), f"{lo}–{hi} cm yr⁻¹",
         lo <= soil_rate <= hi, priority="high")
    gate("soil/control subsidence ratio", round(ratio, 2), f"{RATIO_GATE[0]}–{RATIO_GATE[1]}×",
         RATIO_GATE[0] <= ratio <= RATIO_GATE[1], priority="high")

    for treatment in ("control", "soil_warming"):
        obs = obs_thaw[treatment]
        sim = thaw_results[treatment]
        tol = 2.0 * obs["se_thaw_penetration_cm"]
        gate(f"{treatment} thaw penetration 2018", round(sim["thaw_penetration_cm"], 1),
             f"{obs['thaw_penetration_cm'] - tol:.1f}–{obs['thaw_penetration_cm'] + tol:.1f} cm",
             obs["thaw_penetration_cm"] - tol <= sim["thaw_penetration_cm"] <= obs["thaw_penetration_cm"] + tol,
             priority="high")

    wtd_years = range(2009, 2019)
    for treatment in ("control", "soil_warming"):
        rmse = wtd_trajectory_rmse(wtd_trajectories[treatment], obs_wtd_traj, wtd_years, treatment)
        gate(f"{treatment} BNZ:554 WTD trajectory RMSE", round(rmse, 1),
             "< 8 cm (2009–2018 summer)", rmse < 8.0, priority="medium")

    for treatment in ("control", "soil_warming"):
        for cal_year in (2009, 2018):
            obs_key = (treatment, cal_year)
            if obs_key not in obs_wtd_point:
                continue
            obs = obs_wtd_point[obs_key]
            sim = water_table[treatment].get(f"{cal_year}_summer_cm", float("nan"))
            tol = 2.0 * obs["se_cm"]
            gate(f"{treatment} water table {cal_year}",
                 round(sim, 1) if np.isfinite(sim) else "nan",
                 f"{obs['depth_cm'] - tol:.1f}–{obs['depth_cm'] + tol:.1f} cm",
                 np.isfinite(sim) and obs["depth_cm"] - tol <= sim <= obs["depth_cm"] + tol,
                 priority="medium")

    soil18 = water_table["soil_warming"].get("2018_summer_cm", float("nan"))
    ctrl18 = water_table["control"].get("2018_summer_cm", float("nan"))
    if np.isfinite(soil18) and np.isfinite(ctrl18):
        gate("soil WTD shallower than control (2018)", round(soil18 - ctrl18, 1),
             "< 0 cm (soil closer to surface)", soil18 < ctrl18, priority="medium")

    if settings.get("snow_profile"):
        target = settings.get("snow_target_peak_cm", 40.0)
        mult = settings.get("soil_snow_multiplier", 2.0)
        ctrl_peak = snow_metrics["control"]["median_peak_cm"]
        soil_peak = snow_metrics["soil_warming"]["median_peak_cm"]
        gate("control snow peak (2009–2018)", round(ctrl_peak, 1),
             f"{target - 8:.0f}–{target + 8:.0f} cm", abs(ctrl_peak - target) <= 8.0,
             priority="medium")
        gate("soil warming snow peak (2×)", round(soil_peak, 1),
             f"{target * mult - 16:.0f}–{target * mult + 16:.0f} cm",
             abs(soil_peak - target * mult) <= 16.0, priority="medium")

    summary = {
        "phase": phase,
        "reference": "Rodenhizer et al. 2020",
        "model_notes": "Richards WTD coupled to daily thermokarst subsidence",
        "climate_source": source,
        "bias_profile": settings["bias_profile"],
        "chosen_soil_bias_scale": soil_bias_scale,
        "snow_fence_winter_extra_c": winter_extra,
        "snow_fence_summer_extra_c": summer_extra,
        "slope": slope,
        "tr_start_yr": tr_start,
        "snow_profile": settings.get("snow_profile"),
        "annual_snow_swe_mm": annual_snow_swe_mm if settings.get("snow_profile") else None,
        "snow_swe_calibration": snow_cal_results if settings.get("snow_profile") else None,
        "snow_metrics": snow_metrics if settings.get("snow_profile") else None,
        "multi_objective_calibration": cal_results,
        "phase2_dir": str(phase2_dir),
        "chosen_ice_fraction": ice_fraction,
        "deep_scale": deep_scale,
        "calibration_mode": "multi_objective_wtd_tp",
        "treatment_restarts": treatment_restarts,
        "treatment_results": treatment_results,
        "thaw_penetration": thaw_results,
        "water_table": water_table,
        "wtd_trajectories": wtd_trajectories,
        "tr_extended": extended,
        "gps_obs_meta": gps_meta,
        "wtd_obs_meta": wtd_meta,
        "climate_meta": climate_meta,
        "soil_control_ratio": ratio,
        "checks_passed": sum(c["status"] == "PASS" for c in checks),
        "checks_total": len(checks),
        "statuses": statuses,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (out / "checks.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=checks[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5,
                         "figure.facecolor": "white", "savefig.facecolor": "white"})

    fig, ax = plt.subplots(figsize=(8.0, 4.2), layout="constrained")
    years = sorted(set(obs_wtd_traj.get("control", {})) & set(range(2009, 2019)))
    for treatment, color, label in [
            ("control", TEAL, "Control"),
            ("soil_warming", ORANGE, "Soil warming")]:
        if treatment in obs_wtd_traj:
            ax.plot(years, [obs_wtd_traj[treatment][y] for y in years],
                    "o-", color=color, alpha=0.5, label=f"{label} BNZ:554", ms=3)
        if treatment in wtd_trajectories:
            ax.plot(years, [wtd_trajectories[treatment].get(y, float("nan")) for y in years],
                    "--", color=color, lw=1.2, label=f"{label} TEM {phase_label}")
    ax.set_xlabel("Year")
    ax.set_ylabel("Summer mean WTD (cm)")
    ax.set_title(f"BNZ:554 vs TEM water-table trajectories ({phase_label})")
    ax.legend(fontsize=6, ncol=2)
    ax.grid(color=GRID, lw=0.6)
    save(fig, out, "eml-wtd-trajectories-bnz554")

    fig, ax = plt.subplots(figsize=(7.2, 4.0), layout="constrained")
    x = np.arange(len(TREATMENTS))
    sim = [treatment_results[t]["rate_cm_yr"] for t in TREATMENTS]
    obs_rates = [OBS_RATES[t][2] for t in TREATMENTS]
    ax.bar(x - 0.18, sim, 0.36, label=f"TEM {phase_label}", color=[TREAT_COLOR[t] for t in TREATMENTS])
    ax.bar(x + 0.18, obs_rates, 0.36, label="Rodenhizer 2020", color=MUTED, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace("_", "\n") for t in TREATMENTS])
    ax.set_ylabel("Subsidence rate (cm yr⁻¹)")
    snow_note = (
        f", snow SWE {annual_snow_swe_mm:.0f} mm"
        if settings.get("snow_profile") else "")
    ax.set_title(
        f"{phase_label} (bias×{soil_bias_scale:.1f}, deep×{deep_scale:.1f}, "
        f"summer+{summer_extra:.1f}°C{snow_note})")
    ax.legend()
    ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, "eml-subsidence-rates-vs-obs")

    print(json.dumps({
        "phase": phase,
        "checks_passed": summary["checks_passed"],
        "checks_total": summary["checks_total"],
        "chosen_soil_bias_scale": soil_bias_scale,
        "deep_scale": deep_scale,
        "summer_extra_c": summer_extra,
        "annual_snow_swe_mm": annual_snow_swe_mm if settings.get("snow_profile") else None,
        "snow_metrics": snow_metrics if settings.get("snow_profile") else None,
        "rates_cm_yr": {t: treatment_results[t]["rate_cm_yr"] for t in TREATMENTS},
        "thaw_penetration_cm": {
            t: thaw_results[t]["thaw_penetration_cm"] for t in ("control", "soil_warming")},
        "wtd_2018_cm": {
            t: water_table[t].get("2018_summer_cm") for t in ("control", "soil_warming")},
    }, indent=2))

    failed = [x for x in checks if x["status"] == "FAIL" and x["priority"] == "high"]
    if failed and not args.allow_fail:
        raise RuntimeError(f"{len(failed)} high-priority gates failed: {[x['test'] for x in failed]}")

    _maybe_generate_thermal_plots(args, out, settings, cell)


def _maybe_generate_thermal_plots(args, out, settings, cell):
    if getattr(args, "skip_thermal_plots", False):
        return
    from eml_thermal_plots import generate_thermal_figures, has_profile_outputs  # noqa: E402

    for treatment in ("control", "soil_warming"):
        run_dir = out / f"treatment-{treatment}"
        if not has_profile_outputs(run_dir):
            print(f"warning: {run_dir} lacks TLAYER; run --plot-thermal to refresh",
                  file=sys.stderr)
            return
    stems = generate_thermal_figures(
        out, tr_years=settings["tr_years"], cell=cell, copy_to_report=True)
    print(f"thermal figures: {stems}", file=sys.stderr)


def run_plot_thermal(args):
    """Re-run control + soil-warming TR with layer profiles, then plot."""
    from eml_thermal_plots import generate_thermal_figures, has_profile_outputs  # noqa: E402

    out = args.output.resolve()
    if not (out / "summary.json").exists():
        raise RuntimeError(f"no summary.json in {out}; run phase 3/4 first")
    summary = json.loads((out / "summary.json").read_text())
    settings = PHASES.get(summary.get("phase", 4), PHASES[4])
    cell = settings["cells"][0]
    tr_years = settings["tr_years"]

    spec = out / "eml-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec,
              include_front=True, include_watertab=True, include_profile=True)

    run_json = out / "treatment-control.json"
    if not run_json.exists():
        raise RuntimeError(f"missing {run_json}")
    base = json.loads(run_json.read_text())
    base["IO"]["output_spec_file"] = str(spec)

    restarts = summary.get("treatment_restarts", {})
    for treatment in ("control", "soil_warming"):
        run_dir = out / f"treatment-{treatment}"
        if has_profile_outputs(run_dir) and not args.recalibrate:
            print(f"reusing profile outputs: {run_dir}", file=sys.stderr)
            continue
        if treatment not in restarts:
            raise RuntimeError(f"missing restart for {treatment}")
        tbase = json.loads(json.dumps(base))
        climate = out / f"eml-climate-{treatment}.nc"
        if not climate.exists():
            raise RuntimeError(f"missing climate {climate}")
        tbase["IO"]["hist_climate_file"] = str(climate)
        run(
            args.binary.resolve(), out, f"treatment-{treatment}",
            config(tbase, run_dir, [cell], Path(restarts[treatment]["path"]), thermokarst=True),
            ["--tr-yrs", str(tr_years)], [cell])

    stems = generate_thermal_figures(
        out, tr_years=tr_years, cell=cell, copy_to_report=True)
    print(json.dumps({"thermal_figures": stems, "output_dir": str(out)}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, default=0, choices=[0, 1, 2, 3, 4, 5])
    parser.add_argument("--binary", type=Path, default=ROOT / "dvmdostem")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--fetch", action="store_true", help="Download BNZ/LTER obs data")
    parser.add_argument("--phase1-dir", type=Path, default=PHASE1_DIR,
                        help="Phase 1 results dir for EQ spin-up (restart-eq.nc)")
    parser.add_argument("--phase2-dir", type=Path, default=PHASE2_DIR,
                        help="Phase 2 results dir for BNZ ice calibration (Phase 3)")
    parser.add_argument("--recalibrate", action="store_true",
                        help="Re-run calibration sweeps for the current phase")
    parser.add_argument("--reuse-calibration", action="store_true",
                        help="Skip calibration; reuse prior phase summary.json")
    parser.add_argument("--allow-fail", action="store_true",
                        help="Do not exit nonzero when soft validation gates fail")
    parser.add_argument("--plot-thermal", action="store_true",
                        help="Refresh TLAYER outputs and generate soil thermal contour plots")
    parser.add_argument("--plot-climate", action="store_true",
                        help="Generate EML climate input driver figure")
    parser.add_argument("--skip-thermal-plots", action="store_true",
                        help="Skip automatic thermal figure generation at end of phase 3/4")
    args = parser.parse_args()
    if args.plot_climate:
        if args.output is None:
            args.output = PHASE4_DIR
        from eml_climate_plots import generate_climate_figures  # noqa: E402
        stem = generate_climate_figures(args.output.resolve())
        print(json.dumps({"climate_figure": stem, "output_dir": str(args.output.resolve())},
                         indent=2))
        return
    if args.plot_thermal:
        if args.output is None:
            args.output = PHASE4_DIR
        os.environ["OPENBLAS_NUM_THREADS"] = "1"
        os.environ["OMP_NUM_THREADS"] = "1"
        run_plot_thermal(args)
        from eml_climate_plots import generate_climate_figures  # noqa: E402
        generate_climate_figures(args.output.resolve())
        return
    if args.output is None:
        args.output = PHASES[args.phase]["default_output"]
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"
    if args.phase == 0:
        run_phase0(args)
    elif args.phase == 1:
        run_phase1(args)
    elif args.phase == 2:
        run_phase2(args)
    elif args.phase == 3:
        run_phase3(args)
    elif args.phase == 4:
        run_phase4(args, phase=4)
    else:
        run_phase4(args, phase=5)


if __name__ == "__main__":
    main()
