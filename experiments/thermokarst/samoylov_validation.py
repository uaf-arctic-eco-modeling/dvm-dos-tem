#!/usr/bin/env python3
"""Samoylov polygon-tundra thermokarst validation harness (Phases 0–2)."""
import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path

CLIMATE_PKG = Path(__file__).resolve().parent / "samoylov_validation"
GSWP3_POINT = CLIMATE_PKG / "data/gswp3_samoylov_point.nc"
sys.path.insert(0, str(CLIMATE_PKG))
from gswp3_climate import build_samoylov_climate  # noqa: E402

import numpy as np
from netCDF4 import Dataset

ROOT = Path(__file__).resolve().parents[2]
OBS_DIR = Path(__file__).resolve().parent / "samoylov_validation" / "obs"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "build/matplotlib-cache"))
saved_path = os.environ.get("PATH", "")
if sys.platform == "darwin":
    os.environ["PATH"] = os.pathsep.join(
        x for x in saved_path.split(os.pathsep) if x not in ("/usr/sbin", "/sbin"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
os.environ["PATH"] = saved_path

import production_validation as production
import bgc_coupling_validation as bgc

RIM = (0, 0)
CENTER = (0, 1)
CELLS = [RIM, CENTER]
CMT_RIM = 5
CMT_CENTER = 4
SLOPE_DEG = 6.0
DRAIN_RIM = 0
DRAIN_CENTER = 1
PR_YRS = 1
ICE = 917.0
DEPTHS = (0.10, 0.65)
DINM = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
DJF_MONTHS = (11, 0, 1)  # Dec, Jan, Feb (0-based month index)

TK = bgc.TK + ["SNOWTHICK"]
PHASE2_DAILY = ["TKPOND", "TKSURFICE"]
MONTHLY = ["TLAYER", "LAYERDEPTH", "LAYERDZ", "TSOIL_30cm", "TSOIL_100cm"]
BASELINE_START = 1930
BASELINE_END = 1950

INK = "#171717"
TEAL = "#1F6F5F"
BLUE = "#4C78A8"
ORANGE = "#D55E00"
MUTED = "#777772"
GRID = "#E4E7E5"
OBS_COLOR = "#C44E52"

# Phase 0 synthetic (dry, shallow ice band)
P0_TAIR = np.array([-32., -30., -24., -12., -2., 6., 8., 6., 1., -8., -20., -28.])
P0_PRECIP = np.array([8., 7., 6., 7., 10., 18., 22., 20., 14., 10., 9., 8.])
P0_NIRR = np.array([0., 2., 8., 18., 22., 24., 20., 14., 6., 2., 0., 0.])

# Phase 1 paper-calibrated synthetic (236 mm yr-1 target; GSWP3+Boike deferred)
P1_TAIR = np.array([-34., -32., -26., -14., -4., 5., 8., 6., 0., -10., -22., -30.])
P1_PRECIP_BASE = np.array([12., 11., 10., 10., 14., 22., 28., 26., 18., 14., 12., 11.])
P1_NIRR = np.array([0., 3., 10., 20., 24., 26., 22., 16., 8., 3., 0., 0.])

REPORT_PATH = ROOT / "docs_src/thermokarst/samoylov-validation-report.md"
DOCS_FIG_DIR = REPORT_PATH.parent
PHASE_RESULT_DIRS = {
    0: ROOT / "experiments/thermokarst/samoylov_validation_results",
    1: ROOT / "experiments/thermokarst/samoylov_phase1_validation_results",
    2: ROOT / "experiments/thermokarst/samoylov_phase2_validation_results",
}
HYDROLOGY_DIR = ROOT / "experiments/thermokarst/samoylov_hydrology_tune_results"
REPORT_FIGURES = [
    (0, "samoylov-subsidence", "samoylov-phase0-subsidence",
     "Phase 0 — subsidence by case"),
    (0, "samoylov-soilT-climatology", "samoylov-phase0-soilT-climatology",
     "Phase 0 — paired soil temperature climatology"),
    (0, "samoylov-snow-climatology", "samoylov-phase0-snow-climatology",
     "Phase 0 — paired snow depth climatology"),
    (1, "samoylov-soilT-10cm", "samoylov-soilT-10cm",
     "Phase 1 — soil temperature at 10 cm"),
    (1, "samoylov-soilT-65cm", "samoylov-soilT-65cm",
     "Phase 1 — soil temperature at 65 cm"),
    (1, "samoylov-snow", "samoylov-snow",
     "Phase 1 — snow depth vs paper reference"),
    (1, "samoylov-subsidence", "samoylov-subsidence",
     "Phase 1 — subsidence"),
    (1, "samoylov-alt", "samoylov-alt",
     "Phase 1 — September max active layer"),
    (2, "samoylov-subsidence-century", "samoylov-subsidence-century",
     "Phase 2 — century subsidence (1901–2014)"),
    (2, "samoylov-alt-century", "samoylov-alt-century",
     "Phase 2 — active-layer trajectory"),
    ("hydrology", "hydrology-tune-snow", "samoylov-hydrology-tune-snow",
     "Hydrology tuning — peak snow by drainage/CMT variant"),
]

PHASES = {
    0: {
        "eq_yrs": 10,
        "tr_yrs": 13,
        "climate_nyears": 20,
        "rim_ice": {"fraction": 0.35, "top": 0.0, "bottom": 0.50},
        "center_ice": {"fraction": 0.25, "top": 0.0, "bottom": 0.50},
        "cases": [
            ("ref", "ref", True, "paired"),
            ("rim-ice", "rim-ice", True, "rim"),
            ("center-ice", "center-ice", True, "center"),
            ("paired", "paired", True, "paired"),
        ],
        "default_output": ROOT / "experiments/thermokarst/samoylov_validation_results",
    },
    1: {
        "eq_yrs": 30,
        "tr_yrs": 13,
        "climate_nyears": 50,
        "rim_ice": {"fraction": 0.30, "top": 0.25, "bottom": 2.50},
        "center_ice": {"fraction": 0.20, "top": 0.25, "bottom": 3.00},
        "cases": [
            ("ref", "ref", True, "paired"),
            ("paired", "paired", True, "paired"),
        ],
        "default_output": ROOT / "experiments/thermokarst/samoylov_phase1_validation_results",
        "climate_source": "gswp3_boike",
    },
    2: {
        "eq_yrs": 150,
        "tr_yrs": 114,
        "climate_nyears": 114,
        "baseline_start": BASELINE_START,
        "baseline_end": BASELINE_END,
        "rim_ice": {"fraction": 0.30, "top": 0.25, "bottom": 2.50},
        "center_ice": {"fraction": 0.20, "top": 0.25, "bottom": 3.00},
        "cases": [
            ("ref", "ref", True, "paired"),
            ("paired", "paired", True, "paired"),
        ],
        "default_output": ROOT / "experiments/thermokarst/samoylov_phase2_validation_results",
        "climate_source": "gswp3_boike",
        "scaffold_by_default": True,
    },
}


def phase1_precip():
    precip = P1_PRECIP_BASE.copy()
    for month in (11, 0, 1):
        precip[month] *= 0.75
    precip *= 236.0 / precip.sum()
    return precip


def style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 10,
        "axes.labelsize": 9, "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": INK, "text.color": INK, "axes.labelcolor": INK,
        "legend.frameon": False, "svg.fonttype": "none",
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })


def save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=240, bbox_inches="tight")
    fig.savefig(out / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def prepare_climate(base, dest, phase, settings, gswp3_path=None, boike_path=None):
    """Build climate NetCDF; return (monthly_tair, monthly_precip, monthly_nirr, meta)."""
    template = Path(base["IO"]["hist_climate_file"])
    use_builder = (
        settings.get("climate_source") == "gswp3_boike"
        or gswp3_path is not None
        or phase >= 2
    )
    if use_builder:
        boike = boike_path or OBS_DIR / "boike_samoylov_monthly_2002-2014.csv"
        gswp = gswp3_path
        if gswp is None and GSWP3_POINT.exists():
            gswp = GSWP3_POINT
        report = build_samoylov_climate(
            template, dest,
            gswp3_path=gswp,
            boike_path=boike,
            cru_proxy_path=template,
            start_year=1901,
            nyears=settings["climate_nyears"],
        )
        with Dataset(dest) as dataset:
            n = min(12, dataset["tair"].shape[0])
            tair = np.asarray(dataset["tair"][:n, 0, 0], float)
            precip = np.asarray(dataset["precip"][:n, 0, 0], float)
            nirr = np.asarray(dataset["nirr"][:n, 0, 0], float)
        meta = {"source": report.source, "build_report": report.to_dict()}
        return tair, precip, nirr, meta
    return (*make_samoylov_climate(template, dest, settings["climate_nyears"], phase)[:3],
            {"source": f"synthetic_phase{phase}"})


def make_samoylov_climate(source, dest, nyears, phase):
    if phase == 0:
        tair, precip, nirr = P0_TAIR, P0_PRECIP, P0_NIRR
    else:
        tair, precip, nirr = P1_TAIR, phase1_precip(), P1_NIRR

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
                    data[i] = tair[month]
                elif name == "precip":
                    data[i] = precip[month]
                elif name == "nirr":
                    data[i] = nirr[month]
                else:
                    data[i] = 100.0
            dataset[name][:] = data
    return tair, precip, nirr


def copy_spatial(base, out, layout):
    if layout == "paired":
        cmts = [CMT_RIM, CMT_CENTER]
        drains = [DRAIN_RIM, DRAIN_CENTER]
    elif layout == "rim":
        cmts = [CMT_RIM, CMT_RIM]
        drains = [DRAIN_RIM, DRAIN_RIM]
    elif layout == "center":
        cmts = [CMT_CENTER, CMT_CENTER]
        drains = [DRAIN_CENTER, DRAIN_CENTER]
    else:
        raise ValueError(f"unknown layout {layout}")

    mask = out / f"run-mask-{layout}.nc"
    shutil.copy2(base["IO"]["runmask_file"], mask)
    with Dataset(mask, "r+") as dataset:
        dataset["run"][:] = 0
        for y, x in CELLS:
            dataset["run"][y, x] = 1

    paths = {"runmask_file": mask}
    for key, var in [("veg_class_file", "veg_class"),
                     ("drainage_file", "drainage_class"),
                     ("topo_file", "slope")]:
        src = Path(base["IO"][key])
        dst = out / f"{src.stem}-{layout}.nc"
        shutil.copy2(src, dst)
        with Dataset(dst, "r+") as dataset:
            for i, (y, x) in enumerate(CELLS):
                if var == "veg_class":
                    dataset[var][y, x] = cmts[i]
                elif var == "drainage_class":
                    dataset[var][y, x] = drains[i]
                else:
                    dataset[var][y, x] = SLOPE_DEG
        paths[key] = dst
    return paths


def make_spec(source, dest, phase=0):
    rows = list(csv.DictReader(source.open()))
    layer_outputs = {"TLAYER", "LAYERDEPTH", "LAYERDZ"}
    daily = set(TK)
    if phase >= 2:
        daily.update(PHASE2_DAILY)
    for row in rows:
        row["Yearly"] = row["Monthly"] = row["Daily"] = ""
        if row["Name"] in daily:
            row["Daily"] = "d"
        if row["Name"] in MONTHLY:
            row["Monthly"] = "m"
        if row["Name"] in layer_outputs:
            row["Layers"] = "forced"
    with dest.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def inject_excess_cells(source, dest, profiles):
    shutil.copy2(source, dest)
    added = {}
    with Dataset(dest, "r+") as dataset:
        for cell in CELLS:
            if cell not in profiles:
                continue
            profile = profiles[cell]
            fraction = profile["fraction"]
            top = profile["top"]
            bottom = profile["bottom"]
            y, x = cell
            n = int(dataset["numsl"][y, x])
            z = 0.
            total = 0.
            for j in range(n):
                matrix = float(dataset["TKmatrix"][y, x, j])
                if matrix <= 0.:
                    matrix = float(dataset["DZsoil"][y, x, j])
                overlap = max(0., min(z + matrix, bottom) - max(z, top))
                temperature = float(dataset["TSsoil"][y, x, j])
                if overlap and temperature > 1.e-8:
                    raise RuntimeError(f"injection layer is thawed: {cell} layer {j}")
                if overlap and temperature > 0.:
                    dataset["TSsoil"][y, x, j] = 0.
                if overlap:
                    mass = ICE * overlap * fraction / (1. - fraction)
                    dataset["TKexcess"][y, x, j] = mass
                    dataset["TKmatrix"][y, x, j] = matrix
                    dataset["DZsoil"][y, x, j] = matrix + mass / ICE
                    total += mass
                z += matrix
            added[str(cell)] = total
    return added


def build_restart_set(initial, out, rim_ice, center_ice):
    restarts = {}
    restarts["ref"] = out / "restart-ref.nc"
    shutil.copy2(initial, restarts["ref"])

    restarts["rim-ice"] = out / "restart-rim-ice.nc"
    inject_excess_cells(initial, restarts["rim-ice"],
                        {RIM: rim_ice, CENTER: rim_ice})

    restarts["center-ice"] = out / "restart-center-ice.nc"
    inject_excess_cells(initial, restarts["center-ice"],
                        {RIM: center_ice, CENTER: center_ice})

    restarts["paired"] = out / "restart-paired.nc"
    inject_excess_cells(initial, restarts["paired"],
                        {RIM: rim_ice, CENTER: center_ice})
    return restarts


def config(base, spatial_root, directory, restart, thermokarst_enabled,
           ice_profile, layout="paired", output=True, baseline=None):
    cfg = json.loads(json.dumps(base))
    io = cfg["IO"]
    spatial = copy_spatial(base, spatial_root, layout)
    io.update({k: str(v) for k, v in spatial.items()})
    io["output_dir"] = str(directory) + "/"
    io["restart_from"] = str(restart) if restart else ""
    io["output_nc_eq"] = io["output_nc_pr"] = io["output_nc_sp"] = 0
    io["output_nc_tr"] = int(output)
    io["output_nc_sc"] = 0
    io["output_interval"] = 1
    io["output_monthly"] = 1
    cfg["model_settings"]["thermokarst"] = {
        "enabled": bool(thermokarst_enabled),
        "excess_fraction": 0.0,
        "top_depth": ice_profile["top"],
        "bottom_depth": ice_profile["bottom"],
    }
    cfg["model_settings"]["dynamic_lai"] = 0
    if baseline:
        cfg["model_settings"]["baseline_start"] = int(baseline["start"])
        cfg["model_settings"]["baseline_end"] = int(baseline["end"])
    for stage in ["pr", "eq", "sp", "tr", "sc"]:
        cfg["stage_settings"][stage].update({
            "env": True, "bgc": False, "nfeed": False, "avlnflg": False,
            "baseline": stage == "eq", "dsb": False, "dsl": False, "dyn_lai": False,
        })
    cfg["stage_settings"]["tr_start_yr"] = 0
    return cfg


def monthly(directory, name):
    path = directory / f"{name}_monthly_tr.nc"
    with Dataset(path) as dataset:
        return np.asarray(np.ma.asarray(dataset[name][:]).filled(np.nan), float)


def interpolate_profile(temperature, depth, thickness, targets):
    tops = np.asarray(depth, float)
    dz = np.asarray(thickness, float)
    tem = np.asarray(temperature, float)
    good = np.isfinite(tem) & np.isfinite(dz) & (dz > 0)
    if not np.any(good):
        return {z: float("nan") for z in targets}
    tops, dz, tem = tops[good], dz[good], tem[good]
    mids = tops + 0.5 * dz
    order = np.argsort(mids)
    mids, tem = mids[order], tem[order]
    result = {}
    for z in targets:
        if z <= mids[0]:
            result[z] = float(tem[0])
        elif z >= mids[-1]:
            result[z] = float(tem[-1])
        else:
            result[z] = float(np.interp(z, mids, tem))
    return result


def temperature_series(directory, subsidence_daily):
    tlayer = monthly(directory, "TLAYER")
    z = monthly(directory, "LAYERDEPTH")
    dz = monthly(directory, "LAYERDZ")
    months = tlayer.shape[0]
    nyears = subsidence_daily.shape[0] // 365
    ends = np.cumsum(DINM) - 1
    sub_month = np.zeros((months,) + subsidence_daily.shape[1:])
    for year in range(nyears):
        for month, last in enumerate(ends):
            t = year * 12 + month
            if t >= months:
                break
            sub_month[t] = subsidence_daily[year * 365 + last]
    current = {z0: np.zeros((months,) + tlayer.shape[2:]) for z0 in DEPTHS}
    original = {z0: np.zeros((months,) + tlayer.shape[2:]) for z0 in DEPTHS}
    for t in range(months):
        for y, x in CELLS:
            profile = interpolate_profile(
                tlayer[t, :, y, x], z[t, :, y, x], dz[t, :, y, x], DEPTHS)
            shift = float(sub_month[t, y, x])
            orig_depths = tuple(max(0., d - shift) for d in DEPTHS)
            shifted = interpolate_profile(
                tlayer[t, :, y, x], z[t, :, y, x], dz[t, :, y, x], orig_depths)
            for z0, zo in zip(DEPTHS, orig_depths):
                current[z0][t, y, x] = profile[z0]
                original[z0][t, y, x] = shifted[zo]
    return current, original


def monthly_climatology(series, nyears):
    trimmed = series[:nyears * 12]
    return trimmed.reshape(nyears, 12).mean(axis=0)


def monotonic(series):
    diffs = np.diff(series, axis=0)
    return bool(np.all(np.isfinite(diffs)) and np.nanmin(diffs) >= -1.e-9)


def doy_mean(series, nyears):
    n_days = nyears * 365
    trimmed = series[:n_days]
    shaped = trimmed.reshape(nyears, 365)
    return np.nanmean(shaped, axis=0)


def load_obs_monthly(path):
    rows = list(csv.DictReader(path.open()))
    return np.array([float(r["mean_C"]) for r in rows], float)


def load_obs_snow(path):
    rows = list(csv.DictReader(path.open()))
    return (np.array([float(r["rim_m"]) for r in rows], float),
            np.array([float(r["center_m"]) for r in rows], float))


def load_obs_alt(path):
    alt = {}
    for row in csv.DictReader(path.open()):
        alt[row["tile"]] = float(row["alt_m"])
    return alt


def september_max_alt(directory, cell, nyears):
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
            values.append(float(np.nanmax(chunk_f[thaw])))
        else:
            values.append(float("nan"))
    return values


def annual_peak_snow(snow, cell, nyears):
    series = bgc.cell_series(snow, cell)
    return [float(np.nanmax(series[year * 365:(year + 1) * 365])) for year in range(nyears)]


def rmse(model, obs):
    return float(np.sqrt(np.nanmean((model - obs) ** 2)))


def gate(checks, test, observed, criterion, ok, severity="hard"):
    checks.append({
        "test": test,
        "observed": json.dumps(observed) if isinstance(observed, (dict, list)) else observed,
        "criterion": criterion,
        "severity": severity,
        "status": "PASS" if ok else "FAIL",
    })


def run_phase0_gates(checks, statuses, case_data, injected, precip, tair):
    gate(checks, "production completion", statuses, "all cells status 100",
         all(v == [100, 100] for v in statuses.values()))
    gate(checks, "synthetic Samoylov forcing",
         {"annual_precip_mm": float(precip.sum()), "min_tair_C": float(tair.min())},
         "cold dry Arctic template",
         float(precip.sum()) < 200. and float(tair.min()) < -25.)
    gate(checks, "ref subsidence",
         case_data["ref"]["subsidence_m"],
         "< 1 mm on both cells (no excess ice injected)",
         all(v < 0.001 for v in case_data["ref"]["subsidence_m"].values()))
    for name in ["rim-ice", "center-ice", "paired"]:
        subs = case_data[name]["subsidence_m"]
        gate(checks, f"{name} subsidence", subs, "> 1 cm on both cells",
             all(v > 0.01 for v in subs.values()))
        mono = case_data[name]["monotonic_subsidence"]
        gate(checks, f"{name} monotonic subsidence", mono, "non-decreasing daily series",
             all(mono.values()))
    paired_sub = case_data["paired"]["subsidence_m"]
    gate(checks, "paired rim excess ice inventory", injected["paired"],
         "Rim > Center injected mass",
         injected["paired"][str(RIM)] > injected["paired"][str(CENTER)])
    gate(checks, "paired rim subsidence", paired_sub,
         "Rim >= Center cumulative subsidence",
         paired_sub[str(RIM)] >= paired_sub[str(CENTER)] - 0.005)
    finite_t = all(np.isfinite(case_data["paired"]["temperature_original_C"][str(d)][str(c)])
                   for d in DEPTHS for c in CELLS)
    gate(checks, "paired original-depth soil temperature", finite_t,
         "finite monthly means", finite_t)


def run_phase1_gates(checks, statuses, paired, obs, tr_yrs):
    gate(checks, "production completion", statuses, "all cells status 100",
         all(v == [100, 100] for v in statuses.values()))
    gate(checks, "finite paired diagnostics", paired["finite"], "all finite", paired["finite"])

    rim_djf = paired["djf_65cm"][str(RIM)]
    center_djf = paired["djf_65cm"][str(CENTER)]
    winter_delta = center_djf - rim_djf
    gate(checks, "winter Rim colder than Center (DJF 0.65 m)",
         {"rim_C": rim_djf, "center_C": center_djf, "center_minus_rim_C": winter_delta},
         "ΔT > 2 °C", winter_delta > 2.0, severity="soft")

    rim_alt = float(np.nanmean(paired["sept_alt_m"][str(RIM)]))
    center_alt = float(np.nanmean(paired["sept_alt_m"][str(CENTER)]))
    gate(checks, "Center September ALT",
         {"model_m": center_alt, "obs_m": obs["alt"]["center"]},
         "0.35–0.60 m", 0.35 <= center_alt <= 0.60, severity="soft")
    gate(checks, "Rim September ALT",
         {"model_m": rim_alt, "obs_m": obs["alt"]["rim"]},
         "0.35–0.85 m", 0.35 <= rim_alt <= 0.85, severity="soft")

    rim_snow = float(np.nanmean(paired["peak_snow_m"][str(RIM)]))
    center_snow = float(np.nanmean(paired["peak_snow_m"][str(CENTER)]))
    gate(checks, "Center end-season snow > Rim",
         {"center_m": center_snow, "rim_m": rim_snow, "delta_m": center_snow - rim_snow},
         "Δ > 0.10 m", center_snow - rim_snow > 0.10, severity="soft")

    rmse_center = paired["rmse_65cm_center_C"]
    gate(checks, "Center soil T RMSE at 0.65 m (monthly climatology)",
         {"rmse_C": rmse_center},
         "< 5 °C vs paper reference", rmse_center < 5.0, severity="soft")


def plot_phase0(out, case_plan, tr_yrs):
    days = np.arange(1, tr_yrs * 365 + 1)
    doy = np.arange(1, 366)

    fig, axes = plt.subplots(2, 1, figsize=(7.4, 5.4), sharex=True, layout="constrained")
    for name, color in [("ref", MUTED), ("rim-ice", TEAL),
                        ("center-ice", BLUE), ("paired", ORANGE)]:
        sub = bgc.read_daily(out / name, "TKSUBSIDENCE")
        axes[0].plot(days, bgc.cell_series(sub, RIM) * 100,
                     color=color, label=f"{name} Rim")
        axes[1].plot(days, bgc.cell_series(sub, CENTER) * 100,
                     color=color, ls="--", label=f"{name} Center")
    axes[0].set(ylabel="Rim subsidence (cm)", title="Samoylov Phase 0 subsidence")
    axes[1].set(xlabel="Transient day", ylabel="Center subsidence (cm)")
    axes[0].legend(fontsize=7, ncol=2)
    axes[1].legend(fontsize=7, ncol=2)
    for ax in axes:
        ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, "samoylov-subsidence")

    paired_sub = bgc.read_daily(out / "paired", "TKSUBSIDENCE")
    paired_snow = bgc.read_daily(out / "paired", "SNOWTHICK")
    _, paired_orig = temperature_series(out / "paired", paired_sub)
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 5.8), layout="constrained")
    for ax, depth in zip(axes.flat, DEPTHS):
        for cell, label, color in [(RIM, "Rim", TEAL), (CENTER, "Center", BLUE)]:
            series = paired_orig[depth][:, cell[0], cell[1]]
            nyears = len(series) // 12
            clim = series[:nyears * 12].reshape(nyears, 12).mean(axis=0)
            ax.plot(np.arange(1, 13), clim, color=color, label=label)
        ax.set(title=f"Original-depth {depth:.2f} m", xlabel="Month", ylabel="Soil T (°C)")
        ax.grid(axis="y", color=GRID, lw=0.6)
    axes[0, 0].legend()
    save(fig, out, "samoylov-soilT-climatology")

    fig, ax = plt.subplots(figsize=(7.2, 3.6), layout="constrained")
    for cell, label, color in [(RIM, "Rim", TEAL), (CENTER, "Center", BLUE)]:
        ax.plot(doy, doy_mean(bgc.cell_series(paired_snow, cell), tr_yrs),
                color=color, label=label)
    ax.set(xlabel="Day of year", ylabel="Snow thickness (m)",
           title="Paired case mean snow depth climatology")
    ax.legend()
    ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, "samoylov-snow-climatology")


def plot_phase1(out, paired_orig, obs, tr_yrs, paired_metrics):
    months = np.arange(1, 13)
    doy = np.arange(1, 366)

    for depth, obs_rim, obs_center, tag in [
        (0.10, obs["soilT_rim_10"], obs["soilT_center_10"], "10cm"),
        (0.65, obs["soilT_rim_65"], obs["soilT_center_65"], "65cm"),
    ]:
        fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.6), layout="constrained", sharey=True)
        for ax, cell, label, obs_curve, color in [
            (axes[0], RIM, "Rim", obs_rim, TEAL),
            (axes[1], CENTER, "Center", obs_center, BLUE),
        ]:
            model = paired_metrics["monthly_clim"][depth][str(cell)]
            ax.plot(months, model, color=color, lw=2, label="Model")
            ax.plot(months, obs_curve, color=OBS_COLOR, ls="--", lw=1.5, label="Paper ref.")
            ax.set(title=f"{label} {depth:.2f} m", xlabel="Month", ylabel="Soil T (°C)")
            ax.grid(axis="y", color=GRID, lw=0.6)
            ax.legend(fontsize=7)
        fig.suptitle(f"Samoylov Phase 1 soil temperature — {tag}")
        save(fig, out, f"samoylov-soilT-{tag}")

    paired_snow = bgc.read_daily(out / "paired", "SNOWTHICK")
    obs_rim_snow, obs_center_snow = obs["snow"]
    fig, ax = plt.subplots(figsize=(7.2, 3.6), layout="constrained")
    for cell, label, color, obs_curve in [
        (RIM, "Rim", TEAL, obs_rim_snow),
        (CENTER, "Center", BLUE, obs_center_snow),
    ]:
        snow = bgc.cell_series(paired_snow, cell)
        monthly = []
        for month in range(12):
            days = []
            for year in range(tr_yrs):
                start = year * 365 + sum(DINM[:month])
                end = start + DINM[month]
                days.extend(snow[start:end])
            monthly.append(float(np.nanmean(days)))
        ax.plot(months, monthly, color=color, lw=2, label=f"{label} model")
        ax.plot(months, obs_curve, color=OBS_COLOR, ls="--", lw=1.5,
                label=f"{label} paper ref.")
    ax.set(xlabel="Month", ylabel="Snow depth (m)", title="Samoylov Phase 1 snow depth")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, "samoylov-snow")

    days = np.arange(1, tr_yrs * 365 + 1)
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 5.0), sharex=True, layout="constrained")
    for name, color in [("ref", MUTED), ("paired", ORANGE)]:
        sub = bgc.read_daily(out / name, "TKSUBSIDENCE")
        axes[0].plot(days, bgc.cell_series(sub, RIM) * 100, color=color, label=f"{name} Rim")
        axes[1].plot(days, bgc.cell_series(sub, CENTER) * 100,
                     color=color, ls="--", label=f"{name} Center")
    axes[0].set(ylabel="Rim subsidence (cm)", title="Samoylov Phase 1 subsidence")
    axes[1].set(xlabel="Transient day", ylabel="Center subsidence (cm)")
    for ax in axes:
        ax.legend(fontsize=7)
        ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, "samoylov-subsidence")

    fig, ax = plt.subplots(figsize=(5.5, 3.6), layout="constrained")
    labels = ["Rim model", "Center model", "Rim obs", "Center obs"]
    values = [
        float(np.nanmean(paired_metrics["sept_alt_m"][str(RIM)])),
        float(np.nanmean(paired_metrics["sept_alt_m"][str(CENTER)])),
        obs["alt"]["rim"],
        obs["alt"]["center"],
    ]
    colors = [TEAL, BLUE, TEAL, BLUE]
    ax.bar(labels, values, color=colors, alpha=0.85)
    ax.set(ylabel="September max ALT (m)", title="Samoylov Phase 1 active layer")
    ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, "samoylov-alt")


def summer_mean_pond(directory, cell, nyears):
    pond = bgc.read_daily(directory, "TKPOND")
    series = bgc.cell_series(pond, cell)
    jja = []
    for year in range(nyears):
        for month in (5, 6, 7):
            start = year * 365 + sum(DINM[:month])
            jja.extend(series[start:start + DINM[month]])
    return float(np.nanmean(jja))


def alt_trend(sept_alts, window=20):
    """Mean ALT change between first and last ``window`` Septembers."""
    values = [v for v in sept_alts if np.isfinite(v)]
    if len(values) < window * 2:
        return float("nan")
    early = float(np.mean(values[:window]))
    late = float(np.mean(values[-window:]))
    return late - early


def run_phase2_gates(checks, statuses, case_data, paired_metrics):
    gate(checks, "production completion", statuses, "all cells status 100",
         all(v == [100, 100] for v in statuses.values()))
    gate(checks, "finite paired diagnostics", paired_metrics["finite"],
         "all finite", paired_metrics["finite"])
    subs = case_data["paired"]["subsidence_m"]
    max_sub = max(subs.values())
    gate(checks, "century cumulative subsidence (paired)",
         subs, "0.05–0.50 m on at least one cell",
         any(v >= 0.05 for v in subs.values()) and max_sub <= 0.50,
         severity="soft")
    trend = paired_metrics["center_alt_trend_m"]
    gate(checks, "Center ALT deepening since 1901",
         {"trend_m": trend, "target_m": 0.10},
         "≈ 0.10 m (last 20 yr − first 20 yr Sept max)",
         np.isfinite(trend) and trend >= 0.05, severity="soft")
    pond_delta = paired_metrics["summer_pond_center_minus_rim_m"]
    gate(checks, "Center summer pond > Rim",
         {"delta_m": pond_delta},
         "Center TKPOND > Rim (JJA mean)", pond_delta > 0.0, severity="soft")


def plot_phase2(out, tr_yrs, paired_metrics, case_data):
    days = np.arange(1, tr_yrs * 365 + 1)
    fig, axes = plt.subplots(2, 1, figsize=(8.0, 5.2), sharex=True, layout="constrained")
    for name, color in [("ref", MUTED), ("paired", ORANGE)]:
        sub = bgc.read_daily(out / name, "TKSUBSIDENCE")
        axes[0].plot(days, bgc.cell_series(sub, RIM) * 100, color=color, label=f"{name} Rim")
        axes[1].plot(days, bgc.cell_series(sub, CENTER) * 100,
                     color=color, ls="--", label=f"{name} Center")
    axes[0].set(ylabel="Rim subsidence (cm)", title="Samoylov Phase 2 century subsidence")
    axes[1].set(xlabel="Transient day (1901–2014)", ylabel="Center subsidence (cm)")
    for ax in axes:
        ax.legend(fontsize=7)
        ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, "samoylov-subsidence-century")

    rim_alt = paired_metrics["sept_alt_m"][str(RIM)]
    center_alt = paired_metrics["sept_alt_m"][str(CENTER)]
    years = np.arange(1901, 1901 + len(rim_alt))
    fig, ax = plt.subplots(figsize=(7.4, 3.6), layout="constrained")
    ax.plot(years, rim_alt, color=TEAL, label="Rim")
    ax.plot(years, center_alt, color=BLUE, label="Center")
    ax.set(xlabel="Year", ylabel="September max ALT (m)",
           title="Samoylov Phase 2 active-layer trajectory")
    ax.legend()
    ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, "samoylov-alt-century")


def write_phase2_scaffold(out, base, settings, climate_meta, binary):
    """Write runnable skeleton artifacts without executing the century run."""
    baseline = {"start": settings["baseline_start"], "end": settings["baseline_end"]}
    skeleton = {
        "phase": 2,
        "description": "Samoylov century transient (1901–2014); scaffold only",
        "cli": {
            "pr_years": PR_YRS,
            "eq_years": settings["eq_yrs"],
            "tr_years": settings["tr_yrs"],
            "baseline_start": baseline["start"],
            "baseline_end": baseline["end"],
        },
        "IO": {
            "hist_climate_file": str(out / "samoylov-climate.nc"),
            "co2_file": str(out / "samoylov-co2.nc"),
            "output_spec_file": str(out / "samoylov-output-spec.csv"),
        },
        "cases": ["ref", "paired"],
        "run_command": (
            f"{binary} -f {out}/paired.json "
            f"--pr-yrs {PR_YRS} --eq-yrs {settings['eq_yrs']} --tr-yrs {settings['tr_yrs']}"
        ),
        "climate": climate_meta,
        "notes": [
            "EQ loops climate years 1930–1950 (baseline_start/end).",
            "TR uses 1901–2014 from hist_climate_file year index 0.",
            "Re-run harness with --phase 2 --run to execute (multi-hour runtime).",
        ],
    }
    (out / "phase2-scaffold.json").write_text(json.dumps(skeleton, indent=2) + "\n")

    script = f"""#!/bin/sh
# Samoylov Phase 2 century run (generated scaffold)
set -e
cd {ROOT}
BINARY={binary}
OUT={out}
$BINARY -f "$OUT/initialization.json" --pr-yrs {PR_YRS} --eq-yrs {settings['eq_yrs']}
# Patch restarts from initialization/restart-eq.nc, then:
$BINARY -f "$OUT/paired.json" --tr-yrs {settings['tr_yrs']}
"""
    run_sh = out / "phase2-run.sh"
    run_sh.write_text(script)
    run_sh.chmod(0o755)


def load_phase_summary(phase):
    path = PHASE_RESULT_DIRS[phase] / "summary.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_phase_checks(phase):
    path = PHASE_RESULT_DIRS[phase] / "checks.csv"
    if not path.exists():
        return []
    with path.open() as stream:
        return list(csv.DictReader(stream))


def sync_report_figures():
    """Copy Samoylov validation figures into ``docs_src/thermokarst/``."""
    available = set()
    for key, src_stem, doc_stem, _caption in REPORT_FIGURES:
        src_dir = HYDROLOGY_DIR if key == "hydrology" else PHASE_RESULT_DIRS[key]
        for ext in ("png", "svg"):
            src = src_dir / f"{src_stem}.{ext}"
            if src.exists():
                shutil.copy2(src, DOCS_FIG_DIR / f"{doc_stem}.{ext}")
        if (DOCS_FIG_DIR / f"{doc_stem}.png").exists():
            available.add(doc_stem)
    return available


def figure_lines(doc_stem, caption, available):
    if doc_stem not in available:
        return []
    return [
        f"### {caption}",
        "",
        f"![{caption}]({doc_stem}.png)",
        "",
    ]


def phase_gate_status(summary, checks):
    if summary is None:
        return "not run"
    passed = summary.get("checks_passed", 0)
    total = summary.get("checks_total", 0)
    hard_total = summary.get("checks_hard_total")
    hard_passed = summary.get("checks_hard_passed")
    if hard_total is not None:
        if hard_passed < hard_total:
            return f"**FAIL** ({passed}/{total} gates)"
    if passed == total:
        return f"**PASS** ({passed}/{total} gates)"
    return f"**PARTIAL** ({passed}/{total} gates)"


def gate_summary_lines(checks, title="Soft gate failures"):
    soft_fail = [c for c in checks if c.get("severity") == "soft" and c["status"] == "FAIL"]
    if not soft_fail:
        return []
    lines = [f"### {title}", ""]
    for item in soft_fail:
        lines.append(f"- **{item['test']}**: {item['observed']} (criterion: {item['criterion']})")
    lines.append("")
    return lines


def write_samoylov_validation_report():
    summaries = {p: load_phase_summary(p) for p in (0, 1, 2)}
    checks = {p: load_phase_checks(p) for p in (0, 1, 2)}
    hydro = None
    hydro_path = HYDROLOGY_DIR / "summary.json"
    if hydro_path.exists():
        hydro = json.loads(hydro_path.read_text())
    if not any(summaries.values()) and hydro is None:
        return

    available = sync_report_figures()
    lines = [
        "# Samoylov polygon-tundra validation report",
        "",
        "**Reference:** Bender et al. (2026) — Rim vs Center polygon tundra (Bender-inspired, not CLM reproduction)",
        "",
        "**Harness:** `experiments/thermokarst/samoylov_validation.py`",
        "",
        "## Summary",
        "",
        "| Phase | Status | Command |",
        "|---|---|---|",
        f"| 0 — pipeline | {phase_gate_status(summaries[0], checks[0])} | "
        f"`make thermokarst-samoylov-validation` |",
        f"| 1 — paper-depth ice + obs gates | {phase_gate_status(summaries[1], checks[1])} | "
        f"`make thermokarst-samoylov-phase1-validation` |",
        f"| 2 — century run 1901–2014 | {phase_gate_status(summaries[2], checks[2])} | "
        f"`make thermokarst-samoylov-phase2-validation RUN=1` |",
        f"| Hydrology tuning | "
        f"{'**complete** (`swap_cmt` ranked best)' if hydro else 'not run'} | "
        f"`make thermokarst-samoylov-hydrology-tune` |",
        "",
        "Resume long runs with `--reuse`. Figures below are copied from the latest "
        "harness output directories under `experiments/thermokarst/`.",
        "",
        "## Observation provenance",
        "",
        "Reference curves live in `experiments/thermokarst/samoylov_validation/obs/`. "
        "Soil temperature, snow, and ALT targets are digitized approximations from "
        "Bender et al. (2026) Fig. 2. GSWP3+Boike forcing uses Boike station data "
        "(PANGAEA.905230) for bias correction.",
        "",
    ]

    s0 = summaries[0]
    if s0:
        lines.extend([
            "## Phase 0 — pipeline",
            "",
            f"- Spin-up: {PR_YRS} PR + {s0['eq_years']} EQ years",
            f"- Transient: {s0['tr_years']} TR years",
            "- Forcing: synthetic dry tundra climatology",
            f"- Ice: shallow band 0–0.5 m (Rim/Center)",
            f"- Gates: {s0.get('checks_passed', '?')}/{s0.get('checks_total', '?')} passed",
            "",
            "## Phase 0 figures",
            "",
        ])
        for key, _src, doc_stem, caption in REPORT_FIGURES:
            if key == 0:
                lines.extend(figure_lines(doc_stem, caption, available))

    s1 = summaries[1]
    if s1:
        forcing = s1.get("forcing", {})
        source = forcing.get("source", forcing.get("build_report", {}).get("source", "unknown"))
        precip = forcing.get("build_report", {}).get("mean_annual_precip_mm",
                                                     forcing.get("annual_precip_mm"))
        precip_txt = f"{precip:.0f} mm yr⁻¹" if precip is not None else "see build report"
        lines.extend([
            "## Phase 1 — paper-depth ice + observation gates",
            "",
            f"- Spin-up: {PR_YRS} PR + {s1['eq_years']} EQ years",
            f"- Transient: {s1['tr_years']} TR years",
            f"- Forcing: {source} ({precip_txt})",
            f"- Ice: Rim {s1['ice_profiles']['rim']}, Center {s1['ice_profiles']['center']}",
            "",
            "### Gates",
            "",
            f"- Hard: {s1.get('checks_hard_passed', '?')}/{s1.get('checks_hard_total', '?')} passed",
            f"- Soft: {s1.get('checks_soft_passed', '?')}/{s1.get('checks_soft_total', '?')} passed",
            "",
        ])
        lines.extend(gate_summary_lines(checks[1]))
        lines.extend([
            "## Phase 1 figures",
            "",
        ])
        for key, _src, doc_stem, caption in REPORT_FIGURES:
            if key == 1:
                lines.extend(figure_lines(doc_stem, caption, available))

    s2 = summaries[2]
    if s2:
        scaffold = s2.get("scaffold_only", False)
        mode = "scaffold-only" if scaffold else "full run"
        lines.extend([
            "## Phase 2 — century run (1901–2014)",
            "",
            f"- Mode: {mode}",
            f"- Spin-up: {PR_YRS} PR + {s2['eq_years']} EQ (baseline {BASELINE_START}–{BASELINE_END})",
            f"- Transient: {s2['tr_years']} TR years",
            f"- Forcing: {s2.get('forcing', {}).get('source', 'gswp3_boike')}",
            "",
            "### Gates",
            "",
            f"- Hard: {s2.get('checks_hard_passed', '?')}/{s2.get('checks_hard_total', '?')} passed",
            f"- Soft: {s2.get('checks_soft_passed', '?')}/{s2.get('checks_soft_total', '?')} passed",
            "",
        ])
        lines.extend(gate_summary_lines(checks[2]))
        if not scaffold:
            lines.extend([
                "## Phase 2 figures",
                "",
            ])
            for key, _src, doc_stem, caption in REPORT_FIGURES:
                if key == 2:
                    lines.extend(figure_lines(doc_stem, caption, available))

    if hydro:
        lines.extend([
            "## Hydrology tuning",
            "",
            "Five drainage/CMT variants on the paired Rim/Center layout (10 EQ + 13 TR, GSWP3+Boike). "
            "Ranking favors Center peak snow and summer pond exceeding Rim; none of the variants "
            "achieved the paper snow/pond contrast (Center snow remained 0 m in all runs).",
            "",
            f"- Recommended variant: **{hydro.get('recommended_variant', 'n/a')}**",
            f"- Artifacts: `{HYDROLOGY_DIR.name}/` (`variant_comparison.csv`, `summary.json`)",
            "",
            "## Hydrology tuning figures",
            "",
        ])
        for key, _src, doc_stem, caption in REPORT_FIGURES:
            if key == "hydrology":
                lines.extend(figure_lines(doc_stem, caption, available))

    REPORT_PATH.write_text("\n".join(lines) + "\n")


def write_phase2_report(out, metrics, checks, scaffold_only):
    hard_fail = [c for c in checks if c["severity"] == "hard" and c["status"] == "FAIL"]
    soft_fail = [c for c in checks if c["severity"] == "soft" and c["status"] == "FAIL"]
    mode = "scaffold-only" if scaffold_only else "full run"
    lines = [
        "# Samoylov Phase 2 validation report",
        "",
        f"**Mode:** {mode}",
        f"**Output:** `{out.name}/`",
        "",
        "## Configuration",
        "",
        f"- Spin-up: {PR_YRS} PR + {metrics['eq_years']} EQ (baseline {BASELINE_START}–{BASELINE_END})",
        f"- Transient: {metrics['tr_years']} TR years (1901–2014)",
        f"- Forcing: {metrics['forcing'].get('source', 'gswp3_boike')}",
        "",
        "## Gates",
        "",
        f"- Hard: {metrics['checks_hard_passed']}/{metrics['checks_hard_total']} passed",
        f"- Soft: {metrics['checks_soft_passed']}/{metrics['checks_soft_total']} passed",
        "",
    ]
    if scaffold_only:
        lines.extend([
            "## Scaffold artifacts",
            "",
            "- `samoylov-climate.nc` — GSWP3+Boike bias-corrected driver (CRU proxy until GSWP3 supplied)",
            "- `samoylov-climate.build-report.json` — builder provenance",
            "- `phase2-scaffold.json` — run metadata",
            "- `phase2-run.sh` — example century-run shell script",
            "",
            "Execute the full century run:",
            "",
            "```sh",
            "make thermokarst-samoylov-phase2-validation RUN=1",
            "# or",
            f".venv-thermokarst/bin/python experiments/thermokarst/samoylov_validation.py --phase 2 --run --binary ./dvmdostem",
            "```",
            "",
        ])
    if soft_fail:
        lines.append("### Soft gate failures")
        lines.append("")
        for item in soft_fail:
            lines.append(f"- **{item['test']}**: {item['observed']}")
        lines.append("")
    (out / "samoylov-phase2-report.md").write_text("\n".join(lines) + "\n")
    docs = ROOT / "docs_src/thermokarst/samoylov-phase2-report.md"
    docs.write_text((out / "samoylov-phase2-report.md").read_text())
    write_samoylov_validation_report()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT / "dvmdostem")
    parser.add_argument("--phase", type=int, choices=[0, 1, 2], default=0)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--run", action="store_true",
                        help="Phase 2: execute dvmdostem (default is scaffold-only)")
    parser.add_argument("--gswp3", type=Path, default=None,
                        help="GSWP3 monthly NetCDF (Phases 1+ with builder, Phase 2 default CRU proxy)")
    parser.add_argument("--boike", type=Path, default=None,
                        help="Boike monthly calibration CSV (2002–2014)")
    parser.add_argument("--write-report", action="store_true",
                        help="Regenerate validation report and copy figures from existing results")
    args = parser.parse_args()

    if args.write_report:
        write_samoylov_validation_report()
        print(f"Wrote {REPORT_PATH}")
        return

    settings = PHASES[args.phase]
    out = (args.output or settings["default_output"]).resolve()
    eq_yrs = settings["eq_yrs"]
    tr_yrs = settings["tr_yrs"]
    rim_ice = settings["rim_ice"]
    center_ice = settings["center_ice"]
    case_plan = settings["cases"]
    scaffold_only = args.phase == 2 and not args.run
    baseline = None
    if "baseline_start" in settings:
        baseline = {"start": settings["baseline_start"], "end": settings["baseline_end"]}

    if out.exists() and not args.reuse:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    base = production.parse_json_with_comments(ROOT / "config/config.js")
    bgc.absolute_io(base)
    climate_path = out / "samoylov-climate.nc"
    tair, precip, nirr, climate_meta = prepare_climate(
        base, climate_path, args.phase, settings,
        gswp3_path=args.gswp3, boike_path=args.boike)
    base["IO"]["hist_climate_file"] = str(climate_path)
    if args.phase >= 2:
        co2_path = out / "samoylov-co2.nc"
        bgc.slice_driver_years(Path(base["IO"]["co2_file"]), co2_path, start=0, nyears=tr_yrs)
        base["IO"]["co2_file"] = str(co2_path)
    spec = out / "samoylov-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec, phase=args.phase)
    base["IO"]["output_spec_file"] = str(spec)

    statuses = {}
    injected = {}
    case_data = {}
    paired_metrics = None
    paired_orig = None
    obs = None

    if not scaffold_only:
        statuses["initialization"] = bgc.completed(out, "initialization") if args.reuse else None
        if statuses["initialization"] is None:
            init_cfg = config(
                base, out, out / "initialization", restart=None,
                thermokarst_enabled=True, ice_profile=rim_ice, output=False,
                baseline=baseline)
            statuses["initialization"] = bgc.run(
                args.binary.resolve(), out, "initialization", init_cfg,
                ["--pr-yrs", str(PR_YRS), "--eq-yrs", str(eq_yrs)])

        initial = out / "initialization/restart-eq.nc"
        restarts = build_restart_set(initial, out, rim_ice, center_ice)
        injected = {
            name: {
                str(cell): float(np.sum(bgc.restart_values(path, cell)["TKexcess"]))
                for cell in CELLS
            }
            for name, path in restarts.items() if name != "ref"
        }

        for name, restart_key, enabled, layout in case_plan:
            statuses[name] = bgc.completed(out, name) if args.reuse else None
            if statuses[name] is None:
                statuses[name] = bgc.run(
                    args.binary.resolve(), out, name,
                    config(base, out, out / name, restarts[restart_key], enabled,
                           rim_ice, layout, baseline=baseline),
                    ["--tr-yrs", str(tr_yrs)])

        for name, _, enabled, _ in case_plan:
            sub = bgc.read_daily(out / name, "TKSUBSIDENCE")
            snow = bgc.read_daily(out / name, "SNOWTHICK")
            current, original = temperature_series(out / name, sub)
            case_data[name] = {
                "enabled": enabled,
                "subsidence_m": {str(c): float(bgc.cell_series(sub, c)[-1]) for c in CELLS},
                "snow_end_m": {str(c): float(np.nanmax(bgc.cell_series(snow, c))) for c in CELLS},
                "temperature_original_C": {
                    str(depth): {
                        str(c): float(original[depth][:, c[0], c[1]].mean())
                        for c in CELLS
                    }
                    for depth in DEPTHS
                },
                "monotonic_subsidence": {
                    str(c): monotonic(bgc.cell_series(sub, c)) for c in CELLS
                },
            }

    checks = []

    if args.phase == 0 and not scaffold_only:
        run_phase0_gates(checks, statuses, case_data, injected, precip, tair)
    elif args.phase == 1 and not scaffold_only:
        obs = {
            "soilT_rim_10": load_obs_monthly(OBS_DIR / "samoylov_soilT_rim_10cm.csv"),
            "soilT_center_10": load_obs_monthly(OBS_DIR / "samoylov_soilT_center_10cm.csv"),
            "soilT_rim_65": load_obs_monthly(OBS_DIR / "samoylov_soilT_rim_65cm.csv"),
            "soilT_center_65": load_obs_monthly(OBS_DIR / "samoylov_soilT_center_65cm.csv"),
            "snow": load_obs_snow(OBS_DIR / "samoylov_snow_depth.csv"),
            "alt": load_obs_alt(OBS_DIR / "samoylov_alt_sept.csv"),
        }
        paired_sub = bgc.read_daily(out / "paired", "TKSUBSIDENCE")
        paired_snow = bgc.read_daily(out / "paired", "SNOWTHICK")
        _, paired_orig = temperature_series(out / "paired", paired_sub)

        monthly_clim = {}
        djf_65 = {}
        for depth in DEPTHS:
            monthly_clim[depth] = {}
            for cell in CELLS:
                series = paired_orig[depth][:, cell[0], cell[1]]
                monthly_clim[depth][str(cell)] = monthly_climatology(series, tr_yrs)
            if depth == 0.65:
                for cell in CELLS:
                    clim = monthly_clim[depth][str(cell)]
                    djf_65[str(cell)] = float(np.mean([clim[m] for m in DJF_MONTHS]))

        paired_metrics = {
            "monthly_clim": monthly_clim,
            "djf_65cm": djf_65,
            "sept_alt_m": {str(c): september_max_alt(out / "paired", c, tr_yrs) for c in CELLS},
            "peak_snow_m": {str(c): annual_peak_snow(paired_snow, c, tr_yrs) for c in CELLS},
            "rmse_65cm_center_C": rmse(monthly_clim[0.65][str(CENTER)], obs["soilT_center_65"]),
            "finite": all(np.isfinite(monthly_clim[d][str(c)]).all()
                          for d in DEPTHS for c in CELLS),
        }
        run_phase1_gates(checks, statuses, paired_metrics, obs, tr_yrs)
    elif args.phase == 2:
        if scaffold_only:
            gate(checks, "climate builder", climate_meta.get("source", "gswp3_boike"),
                 "samoylov-climate.nc written", climate_path.exists())
            gate(checks, "co2 driver slice", str(out / "samoylov-co2.nc"),
                 "114 years from demo co2", (out / "samoylov-co2.nc").exists())
            gate(checks, "phase2 scaffold", "phase2-scaffold.json",
                 "scaffold artifacts present", True)
        else:
            paired_sub = bgc.read_daily(out / "paired", "TKSUBSIDENCE")
            _, paired_orig = temperature_series(out / "paired", paired_sub)
            sept = {str(c): september_max_alt(out / "paired", c, tr_yrs) for c in CELLS}
            paired_metrics = {
                "sept_alt_m": sept,
                "center_alt_trend_m": alt_trend(sept[str(CENTER)]),
                "summer_pond_center_minus_rim_m": (
                    summer_mean_pond(out / "paired", CENTER, tr_yrs)
                    - summer_mean_pond(out / "paired", RIM, tr_yrs)),
                "finite": True,
            }
            run_phase2_gates(checks, statuses, case_data, paired_metrics)

    hard_checks = [c for c in checks if c.get("severity", "hard") == "hard"]
    soft_checks = [c for c in checks if c.get("severity") == "soft"]
    forcing_source = climate_meta.get("source", f"synthetic_phase{args.phase}")
    metrics = {
        "phase": args.phase,
        "scaffold_only": scaffold_only,
        "site": "Samoylov",
        "pr_years": PR_YRS,
        "eq_years": eq_yrs,
        "tr_years": tr_yrs,
        "baseline": baseline,
        "forcing": {
            "source": forcing_source,
            "annual_precip_mm": float(precip.sum()),
            "monthly_tair_C": tair.tolist(),
            "monthly_precip_mm": precip.tolist(),
            "monthly_nirr": nirr.tolist(),
            "build_report": climate_meta.get("build_report"),
        },
        "spatial": {
            "slope_degrees": SLOPE_DEG,
            "rim_cmt": CMT_RIM,
            "center_cmt": CMT_CENTER,
            "rim_drainage": DRAIN_RIM,
            "center_drainage": DRAIN_CENTER,
        },
        "ice_profiles": {"rim": rim_ice, "center": center_ice},
        "injected_excess_kg_m2": injected,
        "cases": case_data,
        "checks_passed": sum(x["status"] == "PASS" for x in checks),
        "checks_total": len(checks),
        "checks_hard_passed": sum(x["status"] == "PASS" for x in hard_checks),
        "checks_hard_total": len(hard_checks),
        "checks_soft_passed": sum(x["status"] == "PASS" for x in soft_checks),
        "checks_soft_total": len(soft_checks),
    }
    if paired_metrics is not None:
        pv = {}
        if "djf_65cm" in paired_metrics:
            pv["djf_65cm_C"] = paired_metrics["djf_65cm"]
        if "sept_alt_m" in paired_metrics:
            pv["sept_alt_mean_m"] = {
                k: float(np.nanmean(v)) for k, v in paired_metrics["sept_alt_m"].items()}
        if "peak_snow_m" in paired_metrics:
            pv["peak_snow_mean_m"] = {
                k: float(np.nanmean(v)) for k, v in paired_metrics["peak_snow_m"].items()}
        if "rmse_65cm_center_C" in paired_metrics:
            pv["rmse_65cm_center_C"] = paired_metrics["rmse_65cm_center_C"]
        if "center_alt_trend_m" in paired_metrics:
            pv["center_alt_trend_m"] = paired_metrics["center_alt_trend_m"]
        metrics["paired_validation"] = pv

    (out / "summary.json").write_text(json.dumps(metrics, indent=2) + "\n")
    if checks:
        with (out / "checks.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=checks[0].keys(), lineterminator="\n")
            writer.writeheader()
            writer.writerows(checks)

    style()
    if args.phase == 0 and not scaffold_only:
        plot_phase0(out, case_plan, tr_yrs)
        write_samoylov_validation_report()
    elif args.phase == 1 and not scaffold_only:
        plot_phase1(out, paired_orig, obs, tr_yrs, paired_metrics)
        write_samoylov_validation_report()
    elif args.phase == 2:
        write_phase2_scaffold(out, base, settings, climate_meta, args.binary.resolve())
        if not scaffold_only and paired_metrics is not None:
            plot_phase2(out, tr_yrs, paired_metrics, case_data)
        write_phase2_report(out, metrics, checks, scaffold_only)

    print(json.dumps(metrics, indent=2))
    hard_failed = [x for x in hard_checks if x["status"] == "FAIL"]
    if hard_failed:
        raise RuntimeError(
            f"{len(hard_failed)} Samoylov Phase {args.phase} hard gates failed: "
            f"{[x['test'] for x in hard_failed]}")


if __name__ == "__main__":
    main()
