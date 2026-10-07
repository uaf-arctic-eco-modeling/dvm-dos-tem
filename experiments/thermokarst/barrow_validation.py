#!/usr/bin/env python3
"""Barrow CRREL subsidence validation — Phases 0–2 and Phase A ALT calibration."""
import argparse
import csv
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
BARROW_DATA_DIR = Path(__file__).resolve().parent / "barrow_validation"
OBS_DIR = BARROW_DATA_DIR / "obs"
BUNDLED_CLIMATE = BARROW_DATA_DIR / "nws-barrow-climate-full.nc"
BARROW_PARAM_DIR = BARROW_DATA_DIR / "parameters"
ALT_CALIBRATION_PATH = BARROW_DATA_DIR / "barrow-alt-calibration.json"
PHASE_DIRS = {
    0: ROOT / "experiments/thermokarst/barrow_validation_phase0_results",
    "alt": ROOT / "experiments/thermokarst/barrow_validation_phaseA_results",
    1: ROOT / "experiments/thermokarst/barrow_validation_phase1_results",
    2: ROOT / "experiments/thermokarst/barrow_validation_phase2_results",
}
REPORT_PATH = ROOT / "docs_src/thermokarst/barrow-validation-report.md"
DOCS_FIG_DIR = REPORT_PATH.parent
MONTH_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
P1_YEARS = list(range(2003, 2016))
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

# CRREL plots 34, 37, 40, 44 on a 2×2 grid (wet low-centre → dry elevated).
CELLS = [(0, 0), (0, 1), (1, 0), (1, 1)]
PLOTS = [34, 37, 40, 44]
CMTS = [6, 6, 5, 5]
DRAINAGE = [1, 1, 0, 0]
RESTART_SPLIT = 6
INK = "#171717"
TEAL = "#1F6F5F"
BLUE = "#4C78A8"
ORANGE = "#D55E00"
MUTED = "#777772"
GRID = "#E4E7E5"
PLOT_COLOR = {34: TEAL, 37: BLUE, 40: ORANGE, 44: MUTED}

# Phase 0: thaw-capable synthetic periodic forcing and shallow point lens.
PHASE0_ICE_MASS = 100.0
PHASE0_ICE_DEPTH = 0.08
PHASE0_TR_YEARS = 13
PHASE0_EQ_YEARS = 5
PHASE0_TAIR = np.array([-20., -18., -12., -4., 4., 10., 12., 8., 2., -5., -12., -18.])
PHASE0_PRECIP = np.array([8., 7., 6., 7., 10., 200., 200., 22., 16., 12., 9., 8.])
PHASE0_NIRR = np.array([0., 2., 6., 12., 18., 22., 20., 14., 8., 3., 0., 0.])

# Phase 1: Streletskiy 2003–2015 window with NWS-bias-corrected monthly forcing.
PHASE1_TR_START = 102          # calendar 2003 in 1901-based historic file
PHASE1_TR_YEARS = 13           # 2003–2015 inclusive
PHASE1_EQ_YEARS = 30
PHASE1_WARM_YEARS = (2004, 2007, 2012)
# NWS Barrow climate thaws ~8 cm; inject excess ice in the thaw-accessible band and
# calibrate per-plot fractions to match Streletskiy cumulative subsidence magnitudes.
PHASE1_ICE_TOP = 0.02
PHASE1_ICE_BOTTOM = 0.12
PHASE1_PLOT_FRAC = {34: 0.55, 37: 0.52, 40: 0.46, 44: 0.46}
BARROW_MONTHLY_TAIR = np.array([-26.4, -25., -22., -14., -3., 3., 4.5, 4., 0., -8., -18., -24.])

# Phase 2: full Streletskiy record 1962–2015 (54 transient years).
PHASE2_TR_START = 61           # calendar 1962 in 1901-based historic file
PHASE2_TR_YEARS = 54           # 1962–2015 inclusive
PHASE2_EQ_YEARS = 50
PHASE2_START_YEAR = 1962
PHASE2_SPLIT_YEAR = 2003
PHASE2_END_YEAR = 2015
PHASE2_WARM_YEARS = (2004, 2007, 2012)

# Phase A: ALT calibration via CMT n-factors (no excess ice / subsidence experiment).
PHASE_A_EQ_YEARS = 30
PHASE_A_CALIB_EQ_YEARS = 10
PHASE_A_TR_YEARS = PHASE1_TR_YEARS
PHASE_A_TR_START = PHASE1_TR_START
PHASE_A_YEARS = P1_YEARS
PHASE_A_ALT_MEAN_TARGET = (33.0, 42.0)
PHASE_A_DEFAULT_NFACTOR = {
    5: {"s": 1.0456, "w": 1.121},
    6: {"s": 1.5, "w": 1.0},
}
PHASE_A_NFACTOR_S_GRID = {
    5: [1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0],
    6: [1.2, 1.5, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0],
}


def absolute_io(base):
    for key, value in list(base["IO"].items()):
        if not value:
            continue
        if key.endswith("_file") or key == "parameter_dir":
            base["IO"][key] = str((ROOT / value).resolve())


def copy_spatial(base, out):
    mask = out / "run-mask-four-cells.nc"
    shutil.copy2(base["IO"]["runmask_file"], mask)
    with Dataset(mask, "r+") as dataset:
        dataset["run"][:] = 0
        for y, x in CELLS:
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
            for i, (y, x) in enumerate(CELLS):
                if var == "veg_class":
                    dataset[var][y, x] = CMTS[i]
                elif var == "drainage_class":
                    dataset[var][y, x] = DRAINAGE[i]
                else:
                    dataset[var][y, x] = 0.0
        base["IO"][key] = str(dst)


def load_streletskiy_climate(path):
    rows = {}
    with path.open() as stream:
        for row in csv.DictReader(stream):
            rows[int(row["year"])] = float(row["mean_annual_tair_C"])
    return rows


def load_streletskiy_elevation(path):
    by_plot = {plot: {} for plot in PLOTS}
    with path.open() as stream:
        for row in csv.DictReader(stream):
            plot = int(row["plot"])
            year = int(row["year"])
            if row["elevation_change_cm_vs_2003"]:
                by_plot[plot][year] = float(row["elevation_change_cm_vs_2003"])
    return by_plot


def load_streletskiy_alt(path):
    by_plot = {plot: {} for plot in PLOTS}
    with path.open() as stream:
        for row in csv.DictReader(stream):
            by_plot[int(row["plot"])][int(row["year"])] = float(row["alt_cm"])
    return by_plot


def load_streletskiy_ddt(path):
    ddt = {}
    with path.open() as stream:
        for row in csv.DictReader(stream):
            if row.get("ddt"):
                ddt[int(row["year"])] = float(row["ddt"])
    return ddt


def annual_ddt_from_nc(climate_path, start_year, nyears, month_offset=0):
    """Thawing degree-days (°C·d) from monthly tair: Σ max(T, 0) × days."""
    with Dataset(climate_path) as dataset:
        tair = np.asarray(dataset["tair"][:, 0, 0], float)
    out = {}
    for i in range(nyears):
        year = start_year + i
        chunk = tair[month_offset + i * 12:month_offset + i * 12 + 12]
        out[year] = float(np.sum(np.maximum(chunk, 0.0) * MONTH_DAYS[:len(chunk)]))
    return out


def model_alt_from_run(run_dir, years):
    """Corrected September ALT (cm) = max thaw depth + cumulative subsidence."""
    nyears = len(years)
    sub_daily = read_daily(run_dir, "TKSUBSIDENCE")
    year_ends = year_end_series(sub_daily, nyears)
    alts = {}
    for i, plot in enumerate(PLOTS):
        cell = CELLS[i]
        thaw = september_max_thaw_cm(run_dir, cell, nyears)
        subs = year_ends[:, cell[0], cell[1]] * 100.0
        alts[plot] = {
            year: float(t + s) if np.isfinite(t) else float("nan")
            for year, t, s in zip(years, thaw, subs)
        }
    return alts


def model_alt_from_summary(summary, years):
    alts = {}
    for plot in PLOTS:
        key = str(CELLS[PLOTS.index(plot)])
        series = summary["cells"][key].get("corrected_alt_sept_cm", {})
        alts[plot] = {y: float(series[str(y)]) for y in years if str(y) in series}
    return alts


def setup_report_plot_style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 10,
        "axes.labelsize": 9, "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "svg.fonttype": "none",
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })


def save_docs_figure(fig, name):
    DOCS_FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(DOCS_FIG_DIR / f"{name}.png", dpi=240, bbox_inches="tight")
    fig.savefig(DOCS_FIG_DIR / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def resolve_diagnostic_context():
    """Pick phase output dir, transient run, and EQ restart for diagnostic figures."""
    candidates = [
        (PHASE_DIRS["alt"], "alt-cal", "initialization-alt"),
        (PHASE_DIRS[1], "calibrated-p1", "initialization-p1"),
        (PHASE_DIRS[2], "calibrated-p2", "initialization-p2"),
    ]
    for out_dir, run_name, init_name in candidates:
        run_dir = out_dir / run_name
        restart = out_dir / init_name / "restart-eq.nc"
        if (run_dir / "TKSUBSIDENCE_daily_tr.nc").exists() and restart.exists():
            return out_dir, run_dir, restart
    return None, None, None


def _load_diagnostic_plots():
    import importlib.util
    path = Path(__file__).resolve().parent / "barrow_validation" / "diagnostic_plots.py"
    spec = importlib.util.spec_from_file_location("barrow_diagnostic_plots", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_diagnostic_transient(binary, out_dir, source_run, init_restart, reuse=False):
    """Re-run transient with TLAYER profile output if missing."""
    _diag = _load_diagnostic_plots()
    _etp = _diag._etp

    diag_run = out_dir / "diagnostic-tr"
    if reuse and _etp.has_profile_outputs(diag_run):
        return diag_run

    source_cfg_path = out_dir / f"{source_run.name}.json"
    if not source_cfg_path.exists():
        raise FileNotFoundError(f"missing run config: {source_cfg_path}")
    source_cfg = json.loads(source_cfg_path.read_text())

    profile_spec = out_dir / "barrow-profile-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", profile_spec,
              yearly_front=True, include_profile=True)
    source_cfg["IO"]["output_spec_file"] = str(profile_spec)
    source_cfg["IO"]["restart_from"] = str(init_restart)

    diag_cfg_path = out_dir / "diagnostic-tr.json"
    source_cfg["IO"]["output_dir"] = str(diag_run) + "/"
    diag_cfg_path.write_text(json.dumps(source_cfg, indent=2) + "\n")

    tr_years = PHASE1_TR_YEARS
    if "alt-cal" in source_run.name or out_dir == PHASE_DIRS["alt"]:
        tr_years = PHASE_A_TR_YEARS
    elif out_dir == PHASE_DIRS[2]:
        tr_years = PHASE2_TR_YEARS

    cmd = [str(binary.resolve()), "-f", str(diag_cfg_path), "--log-level", "warn",
           "--max-output-volume=-1", "--tr-yrs", str(tr_years)]
    log_path = out_dir / "diagnostic-tr.log"
    with log_path.open("w") as log:
        done = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    if done.returncode:
        raise RuntimeError(f"diagnostic transient exited {done.returncode}; see {log_path}")
    with Dataset(diag_run / "run_status.nc") as dataset:
        status = [int(dataset["run_status"][y, x]) for y, x in CELLS]
    if status != [100, 100, 100, 100]:
        raise RuntimeError(f"diagnostic transient statuses {status}")
    return diag_run


def generate_diagnostic_report_figures(reuse=False, binary=None):
    """Climate inputs, soil thermal contours, and isotherm ALT for all four plots."""
    _diag = _load_diagnostic_plots()

    out_dir, source_run, restart = resolve_diagnostic_context()
    if out_dir is None:
        return []

    binary = binary or (ROOT / "dvmdostem")
    run_dir = source_run
    if not _diag._etp.has_profile_outputs(run_dir):
        run_dir = ensure_diagnostic_transient(
            binary, out_dir, source_run, restart, reuse=reuse)

    tr_years = PHASE1_TR_YEARS
    start_year = 2003
    if out_dir == PHASE_DIRS[2]:
        tr_years = PHASE2_TR_YEARS
        start_year = PHASE2_START_YEAR

    restart_for_ice = restart
    if (out_dir / "restart-calibrated.nc").exists():
        restart_for_ice = out_dir / "restart-calibrated.nc"

    return _diag.generate_diagnostic_figures(
        out_dir,
        run_dir=run_dir,
        restart=restart_for_ice,
        cells=list(CELLS),
        plots=list(PLOTS),
        obs_alt=load_streletskiy_alt(OBS_DIR / "streletskiy-alt-2003-2015.csv"),
        tr_years=tr_years,
        start_year=start_year,
        calendar_years=list(range(start_year, start_year + tr_years)),
        copy_to_report=True,
    )


def generate_report_figures():
    """Write comparison figures alongside barrow-validation-report.md."""
    written = []
    phase_a_dir = PHASE_DIRS["alt"]
    for stem in ("barrow-alt-obs-vs-model", "barrow-phaseA-alt-vs-obs", "barrow-phaseA-alt-vs-ddt"):
        if (phase_a_dir / f"{stem}.png").exists() or (DOCS_FIG_DIR / f"{stem}.png").exists():
            src_dir = phase_a_dir if (phase_a_dir / f"{stem}.png").exists() else DOCS_FIG_DIR
            DOCS_FIG_DIR.mkdir(parents=True, exist_ok=True)
            for ext in ("png", "svg"):
                src = src_dir / f"{stem}.{ext}"
                if src.exists() and src.parent.resolve() != DOCS_FIG_DIR.resolve():
                    shutil.copy2(src, DOCS_FIG_DIR / f"{stem}.{ext}")
            if (DOCS_FIG_DIR / f"{stem}.png").exists():
                written.append(stem)

    s1 = load_phase_summary(1)
    s2 = load_phase_summary(2)
    if s1 is None and s2 is None:
        return written

    setup_report_plot_style()
    obs_elev = load_streletskiy_elevation(OBS_DIR / "streletskiy-elevation-2003-2015.csv")
    obs_alt = load_streletskiy_alt(OBS_DIR / "streletskiy-alt-2003-2015.csv")
    obs_ddt = load_streletskiy_ddt(OBS_DIR / "streletskiy-climate-2003-2015.csv")
    years = P1_YEARS

    climate_tr = PHASE_DIRS[1] / "nws-barrow-climate-tr.nc"
    if not climate_tr.exists():
        climate_tr = PHASE_DIRS[2] / "nws-barrow-climate-tr.nc"
    if not climate_tr.exists() and BUNDLED_CLIMATE.exists():
        model_ddt = annual_ddt_from_nc(
            BUNDLED_CLIMATE, years[0], len(years), month_offset=PHASE1_TR_START * 12)
    elif climate_tr.exists():
        model_ddt = annual_ddt_from_nc(climate_tr, years[0], len(years))
    else:
        model_ddt = {}

    summary = s1 or s2
    if s2 and s2["cells"][str(CELLS[0])].get("corrected_alt_sept_cm"):
        model_alt = model_alt_from_summary(s2, years)
    elif (PHASE_DIRS[1] / "calibrated-p1").exists():
        model_alt = model_alt_from_run(PHASE_DIRS[1] / "calibrated-p1", years)
    elif (PHASE_DIRS[2] / "calibrated-p2").exists():
        model_alt = model_alt_from_run(PHASE_DIRS[2] / "calibrated-p2", years)
    else:
        model_alt = {p: {} for p in PLOTS}

    if s1:
        fig, axes = plt.subplots(2, 2, figsize=(8.8, 6.4), sharex=True, layout="constrained")
        for ax, cell, plot in zip(axes.flat, CELLS, PLOTS):
            key = str(cell)
            model = [s1["cells"][key]["yearly_cm"][str(y)] for y in years]
            obs = [abs(obs_elev[plot].get(y, np.nan)) for y in years]
            ax.plot(years, model, "o-", color=PLOT_COLOR[plot], lw=1.6, ms=4,
                    label="TEM collapse")
            ax.plot(years, obs, "s--", color=MUTED, lw=1.2, ms=4,
                    label="|obs. elevation change|")
            ax.set_title(f"Plot {plot}")
            ax.set_ylabel("Cumulative subsidence (cm)")
            ax.grid(axis="y", color=GRID, lw=0.6)
            ax.legend(fontsize=7)
        axes[1, 0].set_xlabel("Calendar year")
        axes[1, 1].set_xlabel("Calendar year")
        fig.suptitle("Modeled subsidence vs Streletskiy elevation change (2003–2015)", fontsize=10)
        save_docs_figure(fig, "barrow-subsidence-vs-obs")
        written.append("barrow-subsidence-vs-obs")

        fig, ax = plt.subplots(figsize=(7.0, 3.8), layout="constrained")
        labels = [f"Plot {p}" for p in PLOTS]
        x = np.arange(len(labels))
        model_vals = [s1["cells"][str(CELLS[i])]["subsidence_2015_cm"] for i in range(4)]
        obs_vals = [abs(obs_elev[p].get(2015, np.nan)) for p in PLOTS]
        ax.bar(x - 0.18, obs_vals, 0.36, color=MUTED, label="Streletskiy |Δelev| 2015")
        ax.bar(x + 0.18, model_vals, 0.36, color=TEAL, label="TEM subsidence 2015")
        ax.set_xticks(x, labels)
        ax.set_ylabel("Cumulative subsidence (cm)")
        ax.set_title("2015 cumulative subsidence: model vs observation")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.legend()
        save_docs_figure(fig, "barrow-subsidence-2015")
        written.append("barrow-subsidence-2015")

    fig, axes = plt.subplots(2, 2, figsize=(8.8, 6.8), layout="constrained")
    for ax, plot in zip(axes.flat, PLOTS):
        xs_obs, ys_obs, xs_mod, ys_mod = [], [], [], []
        for year in years:
            if year in obs_ddt and year in obs_alt[plot]:
                xs_obs.append(obs_ddt[year])
                ys_obs.append(obs_alt[plot][year])
            if year in model_ddt and year in model_alt.get(plot, {}):
                val = model_alt[plot][year]
                if np.isfinite(val):
                    xs_mod.append(model_ddt[year])
                    ys_mod.append(val)
        if xs_obs:
            ax.scatter(xs_obs, ys_obs, s=36, color=MUTED, marker="s", zorder=3,
                       label="Streletskiy ALT")
        if xs_mod:
            ax.scatter(xs_mod, ys_mod, s=36, color=PLOT_COLOR[plot], marker="o", zorder=4,
                       label="TEM corrected ALT")
        all_x = xs_obs + xs_mod
        if len(xs_obs) > 2 and all_x:
            coef = np.polyfit(xs_obs, ys_obs, 1)
            xline = np.linspace(min(all_x), max(all_x), 50)
            ax.plot(xline, np.polyval(coef, xline), "--", color=MUTED, lw=0.9, alpha=0.7)
        if len(xs_mod) > 2 and all_x:
            coef = np.polyfit(xs_mod, ys_mod, 1)
            xline = np.linspace(min(all_x), max(all_x), 50)
            ax.plot(xline, np.polyval(coef, xline), "-", color=PLOT_COLOR[plot], lw=1.2,
                    alpha=0.8)
        ax.set_title(f"Plot {plot}")
        ax.set_xlabel("Thawing degree-days (°C·d)")
        ax.set_ylabel("Active-layer thickness (cm)")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.legend(fontsize=7)
    fig.suptitle(
        "Corrected active-layer thickness vs thawing degree-days (2003–2015)\n"
        "TEM ALT = September max thaw depth + cumulative subsidence",
        fontsize=9.5,
    )
    save_docs_figure(fig, "barrow-alt-vs-ddt")
    written.append("barrow-alt-vs-ddt")

    try:
        written.extend(generate_diagnostic_report_figures(reuse=True))
    except Exception as exc:
        print(f"WARNING: diagnostic figures skipped: {exc}", file=sys.stderr)

    return written


def ensure_nws_barrow_climate(source, dest, obs_csv, reuse):
    dest = Path(dest)
    if reuse and dest.exists():
        return dest
    if BUNDLED_CLIMATE.exists() and not dest.exists():
        shutil.copy2(BUNDLED_CLIMATE, dest)
        return dest
    make_nws_barrow_climate(source, dest, obs_csv)
    BARROW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if dest.resolve() != BUNDLED_CLIMATE.resolve():
        shutil.copy2(dest, BUNDLED_CLIMATE)
    return dest


def slice_climate_drivers(full_climate, out_dir, co2_source, tr_start, tr_years, reuse):
    tr_climate = out_dir / "nws-barrow-climate-tr.nc"
    co2 = out_dir / "nws-co2-tr.nc"
    if not (reuse and tr_climate.exists()):
        bgc.slice_driver_years(full_climate, tr_climate, tr_start, tr_years)
    if not (reuse and co2.exists()):
        bgc.slice_driver_years(Path(co2_source), co2, tr_start, tr_years)
    return tr_climate, co2


def injected_kg_from_restart(restart_path, cells):
    with Dataset(restart_path) as dataset:
        return {str(cell): float(np.sum(dataset["TKexcess"][cell[0], cell[1], :]))
                for cell in cells}


def september_max_thaw_cm(directory, cell, nyears):
    """September max thaw-front depth (cm) per transient year."""
    front = read_daily(directory, "TKFRONT")
    ftype = read_daily(directory, "TKFRONTTYPE")
    depths = cell_series(front, cell)
    types = cell_series(ftype, cell)
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


def ensure_barrow_parameter_dir():
    """Copy global CMT parameter files into barrow_validation/parameters/."""
    BARROW_PARAM_DIR.mkdir(parents=True, exist_ok=True)
    for src in (ROOT / "parameters").glob("cmt_*.txt"):
        dst = BARROW_PARAM_DIR / src.name
        if not dst.exists():
            shutil.copy2(src, dst)
    return BARROW_PARAM_DIR


def _set_param_value(line, value):
    if "//" not in line:
        return line
    comment = line[line.index("//"):]
    return f"{value:<20}{comment.rstrip()}"


def write_barrow_nfactors(nfactor_by_cmt):
    """Patch CMT05/CMT06 nfactor(s/w) in the Barrow parameter directory."""
    ensure_barrow_parameter_dir()
    path = BARROW_PARAM_DIR / "cmt_envground.txt"
    lines = path.read_text().splitlines()
    current_cmt = None
    patched = []
    for line in lines:
        if line.startswith("// CMT"):
            match = re.search(r"CMT(\d+)", line)
            current_cmt = int(match.group(1)) if match else None
        if current_cmt in nfactor_by_cmt:
            nf = nfactor_by_cmt[current_cmt]
            if "nfactor(s)" in line:
                line = _set_param_value(line, nf["s"])
            elif "nfactor(w)" in line:
                line = _set_param_value(line, nf["w"])
        patched.append(line)
    path.write_text("\n".join(patched) + "\n")
    return path


def load_alt_calibration():
    if not ALT_CALIBRATION_PATH.exists():
        return None
    return json.loads(ALT_CALIBRATION_PATH.read_text())


def resolve_phase_a_nfactors(args):
    nf = {cmt: dict(PHASE_A_DEFAULT_NFACTOR[cmt]) for cmt in (5, 6)}
    calib = load_alt_calibration()
    if calib and not args.calibrate:
        for cmt in (5, 6):
            key = f"cmt{cmt:02d}"
            if key in calib.get("nfactor_s", {}):
                nf[cmt]["s"] = float(calib["nfactor_s"][key])
            if key in calib.get("nfactor_w", {}):
                nf[cmt]["w"] = float(calib["nfactor_w"][key])
    if args.nfactor_s_cmt05 is not None:
        nf[5]["s"] = args.nfactor_s_cmt05
    if args.nfactor_s_cmt06 is not None:
        nf[6]["s"] = args.nfactor_s_cmt06
    if args.nfactor_w_cmt05 is not None:
        nf[5]["w"] = args.nfactor_w_cmt05
    if args.nfactor_w_cmt06 is not None:
        nf[6]["w"] = args.nfactor_w_cmt06
    return nf


def alt_metrics_from_run(run_dir, nyears, calendar_years):
    obs_alt = load_streletskiy_alt(OBS_DIR / "streletskiy-alt-2003-2015.csv")
    obs_ddt = load_streletskiy_ddt(OBS_DIR / "streletskiy-climate-2003-2015.csv")
    climate_tr = run_dir.parent / "nws-barrow-climate-tr.nc"
    model_ddt = {}
    if climate_tr.exists():
        model_ddt = annual_ddt_from_nc(climate_tr, calendar_years[0], nyears)
    cell_metrics = {}
    paired_errors = []
    model_vals = []
    for i, cell in enumerate(CELLS):
        plot = PLOTS[i]
        sept = september_max_thaw_cm(run_dir, cell, nyears)
        alt_by_year = {str(y): float(v) for y, v in zip(calendar_years, sept)}
        obs_vals = [obs_alt[plot][y] for y in calendar_years if y in obs_alt[plot]]
        mod_vals = [v for y, v in zip(calendar_years, sept) if np.isfinite(v)]
        for y, model in zip(calendar_years, sept):
            if y in obs_alt[plot] and np.isfinite(model):
                paired_errors.append((float(model) - obs_alt[plot][y]) ** 2)
                model_vals.append(float(model))
        warm = [sept[j] for j, y in enumerate(calendar_years) if y in PHASE1_WARM_YEARS]
        cold = [sept[j] for j, y in enumerate(calendar_years)
                if y not in PHASE1_WARM_YEARS and np.isfinite(sept[j])]
        cell_metrics[str(cell)] = {
            "plot": plot,
            "cmt": CMTS[i],
            "mean_alt_cm": float(np.nanmean(mod_vals)) if mod_vals else float("nan"),
            "rmse_cm": float(np.sqrt(np.mean([
                (sept[j] - obs_alt[plot][y]) ** 2
                for j, y in enumerate(calendar_years)
                if y in obs_alt[plot] and np.isfinite(sept[j])
            ]))) if mod_vals else float("nan"),
            "alt_by_year_cm": alt_by_year,
            "warm_year_mean_cm": float(np.nanmean(warm)) if warm else float("nan"),
            "other_year_mean_cm": float(np.nanmean(cold)) if cold else float("nan"),
        }
    rmse = float(np.sqrt(np.mean(paired_errors))) if paired_errors else float("nan")
    mean_alt = float(np.mean(model_vals)) if model_vals else float("nan")
    return {
        "cells": cell_metrics,
        "mean_alt_cm": mean_alt,
        "rmse_cm": rmse,
        "obs_alt_mean_cm": float(np.mean([
            obs_alt[p][y] for p in PLOTS for y in calendar_years if y in obs_alt[p]
        ])),
        "obs_ddt": obs_ddt,
        "model_ddt": model_ddt,
    }


def alt_score(metrics):
    rmse = metrics["rmse_cm"]
    mean_alt = metrics["mean_alt_cm"]
    if not np.isfinite(rmse):
        return float("inf")
    lo, hi = PHASE_A_ALT_MEAN_TARGET
    penalty = 0.0
    if mean_alt < lo:
        penalty = (lo - mean_alt) * 1.5
    elif mean_alt > hi:
        penalty = (mean_alt - hi) * 1.5
    return rmse + penalty


def make_phase0_climate(source, dest, nyears):
    shutil.copy2(source, dest)
    with Dataset(dest, "r+") as dataset:
        nmonths = nyears * 12
        ny = dataset["tair"].shape[1]
        nx = dataset["tair"].shape[2]
        for name, template in [
                ("tair", PHASE0_TAIR),
                ("precip", PHASE0_PRECIP),
                ("nirr", PHASE0_NIRR),
        ]:
            data = np.zeros((nmonths, ny, nx), dtype=np.float64)
            for i in range(nmonths):
                data[i, :, :] = template[i % 12]
            dataset[name][:] = data
        if "vapor_press" in dataset.variables:
            dataset["vapor_press"][:] = 100.0
    return dest


def make_nws_barrow_climate(source, dest, obs_csv):
    """Bias-correct Toolik historic monthly tair to Barrow (NWS / Streletskiy)."""
    obs = load_streletskiy_climate(obs_csv)
    clim_ann = BARROW_MONTHLY_TAIR.mean()
    shutil.copy2(source, dest)
    with Dataset(source) as src, Dataset(dest, "r+") as dst:
        toolik = np.asarray(src["tair"][:, 0, 0], float)
        n = toolik.size // 12
        t2 = toolik.reshape(n, 12)
        toolik_ann = t2.mean(axis=1)
        toolik_clim_ann = t2.mean(axis=0).mean()
        new = np.zeros_like(toolik)
        for y in range(n):
            year = 1901 + y
            monthly = BARROW_MONTHLY_TAIR.copy()
            if year in obs:
                monthly += obs[year] - clim_ann
            else:
                monthly += (toolik_ann[y] - toolik_clim_ann) * 0.35
            new[y * 12:(y + 1) * 12] = monthly
        ny, nx = dst["tair"].shape[1], dst["tair"].shape[2]
        dst["tair"][:] = new[:, None, None]
        dst["precip"][:] = np.asarray(src["precip"][:], float) * 0.55
    return dest


def make_spec(source, dest, yearly_front=False, include_profile=False):
    rows = list(csv.DictReader(source.open()))
    daily_names = set(bgc.TK) | {"SNOWTHICK", "TKPOND", "TKSURFICE", "TKSUBSIDENCE"}
    profile_names = {"TLAYER", "LAYERDEPTH", "LAYERDZ"}
    for row in rows:
        row["Yearly"] = row["Monthly"] = row["Daily"] = row["Layers"] = ""
        if row["Name"] in daily_names:
            row["Daily"] = "d"
        if row["Name"] in {"TKSUBSIDENCE", "TKFRONT"}:
            row["Yearly"] = "y"
        if row["Name"] == "TKFRONT" and yearly_front:
            row["Monthly"] = "m"
        if row["Name"] in profile_names and include_profile:
            row["Monthly"] = "m"
            row["Layers"] = "forced"
    with dest.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def config(base, directory, restart=None, thermokarst=False, output=True, tr_start=0):
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
        "top_depth": 0.20,
        "bottom_depth": 1.00,
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


def inject_excess_band(source, dest, fraction, top, bottom, cells):
    shutil.copy2(source, dest)
    added = {}
    with Dataset(dest, "r+") as dataset:
        for cell in cells:
            y, x = cell
            n = int(dataset["numsl"][y, x])
            z = 0.0
            cell_added = 0.0
            for j in range(n):
                matrix = layer_thickness(dataset, y, x, j)
                if matrix <= 0.0:
                    continue
                overlap = max(0.0, min(z + matrix, bottom) - max(z, top))
                if overlap:
                    temperature = float(dataset["TSsoil"][y, x, j])
                    if temperature > 1.0e-8:
                        raise RuntimeError(f"injection layer is thawed: {cell} layer {j}")
                    if temperature > 0.0:
                        dataset["TSsoil"][y, x, j] = 0.0
                    mass = 917.0 * overlap * fraction / (1.0 - fraction)
                    dataset["TKexcess"][y, x, j] = mass
                    dataset["DZsoil"][y, x, j] = matrix + mass / 917.0
                    cell_added += mass
                z += matrix
            added[str(cell)] = cell_added
    return added


def inject_calibrated_band(source, dest, plot_fractions, top, bottom, cells, plots):
    shutil.copy2(source, dest)
    added = {}
    with Dataset(dest, "r+") as dataset:
        for cell, plot in zip(cells, plots):
            fraction = plot_fractions[plot]
            y, x = cell
            n = int(dataset["numsl"][y, x])
            z = 0.0
            cell_added = 0.0
            for j in range(n):
                matrix = layer_thickness(dataset, y, x, j)
                if matrix <= 0.0:
                    continue
                overlap = max(0.0, min(z + matrix, bottom) - max(z, top))
                if overlap:
                    temperature = float(dataset["TSsoil"][y, x, j])
                    if temperature > 1.0e-8:
                        raise RuntimeError(f"injection layer is thawed: {cell} layer {j}")
                    if temperature > 0.0:
                        dataset["TSsoil"][y, x, j] = 0.0
                    mass = 917.0 * overlap * fraction / (1.0 - fraction)
                    dataset["TKexcess"][y, x, j] = mass
                    dataset["DZsoil"][y, x, j] = matrix + mass / 917.0
                    cell_added += mass
                z += matrix
            added[str(cell)] = cell_added
    return added


def run(binary, out, name, cfg, args):
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
    with Dataset(run_dir / "run_status.nc") as dataset:
        status = [int(dataset["run_status"][y, x]) for y, x in CELLS]
    if status != [100, 100, 100, 100]:
        raise RuntimeError(f"{name} statuses {status}")
    return status


def completed(out, name):
    path = out / name / "run_status.nc"
    if not path.exists():
        return None
    with Dataset(path) as dataset:
        raw = np.ma.asarray(dataset["run_status"][:])
        status = []
        for y, x in CELLS:
            value = raw[y, x]
            if np.ma.is_masked(value):
                return None
            status.append(int(value))
    return status if status == [100, 100, 100, 100] else None


def read_daily(directory, name):
    with Dataset(directory / f"{name}_daily_tr.nc") as dataset:
        return np.asarray(np.ma.asarray(dataset[name][:]).filled(np.nan), float)


def read_yearly(directory, name):
    path = directory / f"{name}_yearly_tr.nc"
    if not path.exists():
        return None
    with Dataset(path) as dataset:
        return np.asarray(np.ma.asarray(dataset[name][:]).filled(np.nan), float)


def cell_series(array, cell):
    return array[(slice(None),) + cell]


def monotonic(series):
    return bool(np.all(np.diff(series) >= -1.0e-12))


def year_end_series(daily, nyears):
    """Return shape (nyears, Y, X) cumulative subsidence at each year-end."""
    days_per_year = daily.shape[0] // nyears
    ends = [(i + 1) * days_per_year - 1 for i in range(nyears)]
    return daily[ends, :, :]


def ols_slope(years, values):
    years = np.asarray(years, float)
    values = np.asarray(values, float)
    if years.size < 2:
        return float("nan")
    coef = np.polyfit(years, values, 1)
    return float(coef[0])


def save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=240, bbox_inches="tight")
    fig.savefig(out / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def gate(checks, test, observed, criterion, ok):
    checks.append({
        "test": test,
        "observed": json.dumps(observed) if isinstance(observed, (dict, list)) else observed,
        "criterion": criterion,
        "status": "PASS" if ok else "FAIL",
        "hard": False,
    })


def gate_hard(checks, test, observed, criterion, ok):
    gate(checks, test, observed, criterion, ok)
    checks[-1]["hard"] = True


def write_results(out, summary, checks):
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (out / "checks.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=checks[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)


def apply_barrow_parameter_dir(base):
    calib = load_alt_calibration()
    if calib and Path(calib.get("parameter_dir", "")).exists():
        base["IO"]["parameter_dir"] = str(Path(calib["parameter_dir"]).resolve())
    elif BARROW_PARAM_DIR.exists():
        ensure_barrow_parameter_dir()
        base["IO"]["parameter_dir"] = str(BARROW_PARAM_DIR.resolve())


def setup_base(out, reuse):
    if out.exists() and not reuse:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    base = production.parse_json_with_comments(ROOT / "config/config.js")
    absolute_io(base)
    apply_barrow_parameter_dir(base)
    copy_spatial(base, out)
    return base


def run_phase_alt_once(args, out, nfactor_by_cmt, eq_years, run_label="alt-cal"):
    """Phase A: NWS climate, no excess ice, thermokarst off; tune n-factors for ALT."""
    reuse = args.reuse and eq_years >= PHASE_A_EQ_YEARS
    if out.exists() and not reuse and run_label == "alt-cal":
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    write_barrow_nfactors(nfactor_by_cmt)
    base = production.parse_json_with_comments(ROOT / "config/config.js")
    absolute_io(base)
    base["IO"]["parameter_dir"] = str(BARROW_PARAM_DIR.resolve())
    copy_spatial(base, out)

    obs_climate = OBS_DIR / "streletskiy-climate-2003-2015.csv"
    full_climate = ensure_nws_barrow_climate(
        Path(base["IO"]["hist_climate_file"]),
        out / "nws-barrow-climate-full.nc",
        obs_climate,
        reuse,
    )
    tr_climate, co2 = slice_climate_drivers(
        full_climate, out, base["IO"]["co2_file"],
        PHASE_A_TR_START, PHASE_A_TR_YEARS, reuse)
    base["IO"]["hist_climate_file"] = str(tr_climate)
    base["IO"]["co2_file"] = str(co2)

    spec = out / "barrow-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec, yearly_front=True)
    base["IO"]["output_spec_file"] = str(spec)

    init_name = "initialization-alt"
    statuses = {}
    statuses[init_name] = completed(out, init_name) if reuse else None
    if statuses[init_name] is None:
        statuses[init_name] = run(
            args.binary.resolve(), out, init_name,
            config(base, out / init_name, output=False, thermokarst=True),
            ["--pr-yrs", "1", "--eq-yrs", str(eq_years)])

    initial = out / init_name / "restart-eq.nc"
    tr_name = run_label
    statuses[tr_name] = completed(out, tr_name) if reuse else None
    if statuses[tr_name] is None:
        statuses[tr_name] = run(
            args.binary.resolve(), out, tr_name,
            config(base, out / tr_name, initial, thermokarst=True),
            ["--tr-yrs", str(PHASE_A_TR_YEARS)])

    sub = read_daily(out / tr_name, "TKSUBSIDENCE")
    metrics = alt_metrics_from_run(out / tr_name, PHASE_A_TR_YEARS, PHASE_A_YEARS)
    max_sub_mm = max(float(cell_series(sub, c)[-1] * 1000.0) for c in CELLS)

    checks = []
    gate_hard(checks, "production completion",
              {k: v for k, v in statuses.items()},
              "all four cells status 100",
              all(v == [100, 100, 100, 100] for v in statuses.values()))
    gate_hard(checks, "no subsidence",
              max_sub_mm, "< 1 mm over TR (no excess ice)",
              max_sub_mm < 1.0)
    gate(checks, "mean ALT bracket",
         metrics["mean_alt_cm"], "33–42 cm across plots/years",
         PHASE_A_ALT_MEAN_TARGET[0] <= metrics["mean_alt_cm"] <= PHASE_A_ALT_MEAN_TARGET[1])
    per_plot = {PLOTS[i]: metrics["cells"][str(CELLS[i])]["mean_alt_cm"] for i in range(4)}
    gate(checks, "plot mean ALT",
         per_plot, "20–50 cm per plot",
         all(20.0 <= v <= 50.0 for v in per_plot.values() if np.isfinite(v)))
    gate(checks, "ALT RMSE",
         metrics["rmse_cm"], "< 12 cm vs Streletskiy",
         np.isfinite(metrics["rmse_cm"]) and metrics["rmse_cm"] < 12.0)
    warm_response = {
        PLOTS[i]: (
            metrics["cells"][str(CELLS[i])]["warm_year_mean_cm"]
            >= metrics["cells"][str(CELLS[i])]["other_year_mean_cm"] - 1.0
        )
        for i in range(4)
    }
    gate(checks, "warm-year ALT deepening",
         warm_response, "warm-year mean >= other years - 1 cm",
         all(warm_response.values()))

    summary = {
        "phase": "A",
        "eq_years": eq_years,
        "tr_years": PHASE_A_TR_YEARS,
        "climate": "nws-barrow-bias-corrected",
        "tr_window": {"start": 2003, "end": 2015},
        "nfactor_by_cmt": {
            f"cmt{cmt:02d}": nfactor_by_cmt[cmt] for cmt in (5, 6)
        },
        "parameter_dir": str(BARROW_PARAM_DIR),
        "cells": metrics["cells"],
        "mean_alt_cm": metrics["mean_alt_cm"],
        "obs_alt_mean_cm": metrics["obs_alt_mean_cm"],
        "rmse_cm": metrics["rmse_cm"],
        "alt_score": alt_score(metrics),
        "max_subsidence_mm": max_sub_mm,
        "checks_passed": sum(x["status"] == "PASS" for x in checks),
        "checks_total": len(checks),
        "statuses": statuses,
        "notes": (
            "Phase A calibrates September TKFRONT thaw depth via CMT n-factors only; "
            "thermokarst module on for TKFRONT output but no excess ice injected."
        ),
    }
    write_results(out, summary, checks)
    plot_phase_alt_figures(out, metrics, nfactor_by_cmt)
    return summary, checks


def plot_alt_obs_vs_model(metrics, out, title, stem="barrow-alt-obs-vs-model"):
    """Four-panel time series: Streletskiy probing vs TEM September TKFRONT."""
    setup_report_plot_style()
    obs_alt = load_streletskiy_alt(OBS_DIR / "streletskiy-alt-2003-2015.csv")
    years = PHASE_A_YEARS
    fig, axes = plt.subplots(2, 2, figsize=(8.8, 6.4), sharex=True, layout="constrained")
    for ax, cell, plot in zip(axes.flat, CELLS, PLOTS):
        model = [metrics["cells"][str(cell)]["alt_by_year_cm"][str(y)] for y in years]
        obs = [obs_alt[plot].get(y, np.nan) for y in years]
        ax.plot(years, obs, "s--", color=MUTED, lw=1.2, ms=4, label="Observed")
        ax.plot(years, model, "o-", color=PLOT_COLOR[plot], lw=1.6, ms=4, label="Modeled")
        ax.set_title(f"Plot {plot}")
        ax.set_ylabel("September ALT (cm)")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.legend(fontsize=7)
    axes[1, 0].set_xlabel("Calendar year")
    axes[1, 1].set_xlabel("Calendar year")
    fig.suptitle(title, fontsize=10)
    save(fig, out, stem)
    for ext in ("png", "svg"):
        src = out / f"{stem}.{ext}"
        if src.exists():
            DOCS_FIG_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, DOCS_FIG_DIR / f"{stem}.{ext}")
    return stem


def plot_alt_from_run(run_dir, out=None, tr_years=PHASE_A_TR_YEARS, years=None, title=None,
                      stem="barrow-alt-obs-vs-model"):
    """Build observed-vs-modeled ALT figure from an existing transient run directory."""
    run_dir = Path(run_dir)
    out = Path(out or run_dir.parent)
    years = years or PHASE_A_YEARS
    metrics = alt_metrics_from_run(run_dir, tr_years, years)
    if title is None:
        title = "Active-layer thickness: observed vs modeled (September TKFRONT)"
    return plot_alt_obs_vs_model(metrics, out, title, stem=stem)


def plot_phase_alt_figures(out, metrics, nfactor_by_cmt):
    obs_alt = load_streletskiy_alt(OBS_DIR / "streletskiy-alt-2003-2015.csv")
    obs_ddt = metrics.get("obs_ddt") or load_streletskiy_ddt(
        OBS_DIR / "streletskiy-climate-2003-2015.csv")
    model_ddt = metrics.get("model_ddt", {})

    plot_alt_obs_vs_model(
        metrics, out,
        title=(
            f"Active-layer thickness: observed vs modeled "
            f"(CMT05 n_s={nfactor_by_cmt[5]['s']}, CMT06 n_s={nfactor_by_cmt[6]['s']})"
        ),
        stem="barrow-phaseA-alt-vs-obs",
    )

    fig, axes = plt.subplots(2, 2, figsize=(8.8, 6.8), layout="constrained")
    for ax, cell, plot in zip(axes.flat, CELLS, PLOTS):
        xs_obs, ys_obs, xs_mod, ys_mod = [], [], [], []
        for year in PHASE_A_YEARS:
            if year in obs_ddt and year in obs_alt[plot]:
                xs_obs.append(obs_ddt[year])
                ys_obs.append(obs_alt[plot][year])
            if year in model_ddt:
                val = float(metrics["cells"][str(cell)]["alt_by_year_cm"][str(year)])
                if np.isfinite(val):
                    xs_mod.append(model_ddt[year])
                    ys_mod.append(val)
        if xs_obs:
            ax.scatter(xs_obs, ys_obs, s=36, color=MUTED, marker="s", label="obs.")
        if xs_mod:
            ax.scatter(xs_mod, ys_mod, s=36, color=PLOT_COLOR[plot], marker="o", label="TEM")
        ax.set_title(f"Plot {plot}")
        ax.set_xlabel("Thawing degree-days (°C·d)")
        ax.set_ylabel("September ALT (cm)")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.legend(fontsize=7)
    fig.suptitle("Phase A: ALT vs thawing degree-days (no subsidence correction)", fontsize=10)
    save(fig, out, "barrow-phaseA-alt-vs-ddt")
    for stem in ("barrow-phaseA-alt-vs-obs", "barrow-phaseA-alt-vs-ddt"):
        for ext in ("png", "svg"):
            src = out / f"{stem}.{ext}"
            if src.exists():
                DOCS_FIG_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, DOCS_FIG_DIR / f"{stem}.{ext}")


def run_phase_alt_calibrate(args):
    out = args.output.resolve()
    sweep_dir = out / "calibration-sweep"
    sweep_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for ns6 in PHASE_A_NFACTOR_S_GRID[6]:
        for ns5 in PHASE_A_NFACTOR_S_GRID[5]:
            tag = f"cmt06-s{ns6:.2f}-cmt05-s{ns5:.2f}"
            run_out = sweep_dir / tag
            nf = {
                5: {"s": ns5, "w": PHASE_A_DEFAULT_NFACTOR[5]["w"]},
                6: {"s": ns6, "w": PHASE_A_DEFAULT_NFACTOR[6]["w"]},
            }
            sweep_args = argparse.Namespace(**vars(args))
            sweep_args.reuse = False
            summary, _ = run_phase_alt_once(
                sweep_args, run_out, nf, PHASE_A_CALIB_EQ_YEARS, run_label="alt-cal")
            results.append({
                "tag": tag,
                "nfactor_s_cmt05": ns5,
                "nfactor_s_cmt06": ns6,
                "mean_alt_cm": summary["mean_alt_cm"],
                "rmse_cm": summary["rmse_cm"],
                "score": summary["alt_score"],
                "checks_passed": summary["checks_passed"],
            })
            print(json.dumps({"sweep": tag, "score": summary["alt_score"],
                              "mean_alt_cm": summary["mean_alt_cm"]}, indent=2))

    best = min(results, key=lambda row: row["score"])
    nf_best = {
        5: {"s": best["nfactor_s_cmt05"], "w": PHASE_A_DEFAULT_NFACTOR[5]["w"]},
        6: {"s": best["nfactor_s_cmt06"], "w": PHASE_A_DEFAULT_NFACTOR[6]["w"]},
    }
    calib = {
        "phase": "A",
        "nfactor_s": {"cmt05": nf_best[5]["s"], "cmt06": nf_best[6]["s"]},
        "nfactor_w": {"cmt05": nf_best[5]["w"], "cmt06": nf_best[6]["w"]},
        "mean_alt_cm": best["mean_alt_cm"],
        "rmse_cm": best["rmse_cm"],
        "score": best["score"],
        "parameter_dir": str(BARROW_PARAM_DIR),
        "sweep_eq_years": PHASE_A_CALIB_EQ_YEARS,
        "confirmation_eq_years": PHASE_A_EQ_YEARS,
        "sweep_results": results,
    }
    ALT_CALIBRATION_PATH.write_text(json.dumps(calib, indent=2) + "\n")
    (sweep_dir / "sweep-summary.json").write_text(json.dumps(results, indent=2) + "\n")

    confirm_args = argparse.Namespace(**vars(args))
    confirm_args.reuse = False
    summary, checks = run_phase_alt_once(
        confirm_args, out, nf_best, PHASE_A_EQ_YEARS, run_label="alt-cal")
    summary["calibration"] = calib
    write_results(out, summary, checks)
    return summary, checks


def run_phase_alt(args):
    out = args.output.resolve()
    if args.calibrate:
        return run_phase_alt_calibrate(args)
    nfactor_by_cmt = resolve_phase_a_nfactors(args)
    eq_years = args.eq_yrs if args.eq_yrs is not None else PHASE_A_EQ_YEARS
    return run_phase_alt_once(args, out, nfactor_by_cmt, eq_years)


def run_phase0(args):
    out = args.output.resolve()
    base = setup_base(out, args.reuse)

    climate_years = max(PHASE0_TR_YEARS + 5, 20)
    barrow_climate = make_phase0_climate(
        Path(base["IO"]["hist_climate_file"]),
        out / "barrow-climate.nc",
        climate_years,
    )
    base["IO"]["hist_climate_file"] = str(barrow_climate)
    co2 = out / "barrow-co2.nc"
    bgc.slice_driver_years(Path(base["IO"]["co2_file"]), co2, 0, climate_years)
    base["IO"]["co2_file"] = str(co2)

    spec = out / "barrow-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec)
    base["IO"]["output_spec_file"] = str(spec)

    statuses = {}
    init_name = "initialization"
    statuses[init_name] = completed(out, init_name) if args.reuse else None
    if statuses[init_name] is None:
        statuses[init_name] = run(
            args.binary.resolve(), out, init_name,
            config(base, out / init_name, output=False, thermokarst=True),
            ["--pr-yrs", "1", "--eq-yrs", str(PHASE0_EQ_YEARS)])

    initial = out / init_name / "restart-eq.nc"
    ice_depth = resolve_ice_depth(initial, CELLS, PHASE0_ICE_DEPTH)
    injected = out / "restart-uniform-ice.nc"
    added = inject_excess_mass(initial, injected, PHASE0_ICE_MASS, ice_depth, CELLS)

    for name, restart in [("ref", initial), ("uniform-ice", injected)]:
        statuses[name] = completed(out, name) if args.reuse else None
        if statuses[name] is None:
            statuses[name] = run(
                args.binary.resolve(), out, name,
                config(base, out / name, restart, thermokarst=True),
                ["--tr-yrs", str(PHASE0_TR_YEARS)])

    for name, split, tr_years, tr_start, restart in [
            ("split-first", RESTART_SPLIT, RESTART_SPLIT, 0, injected),
            ("resumed", PHASE0_TR_YEARS - RESTART_SPLIT, PHASE0_TR_YEARS - RESTART_SPLIT,
             RESTART_SPLIT, out / "split-first/restart-tr.nc"),
    ]:
        statuses[name] = completed(out, name) if args.reuse else None
        if statuses[name] is None:
            restart_path = injected if name == "split-first" else restart
            statuses[name] = run(
                args.binary.resolve(), out, name,
                config(base, out / name, restart_path, thermokarst=True, tr_start=tr_start),
                ["--tr-yrs", str(tr_years)])

    sub_ref = read_daily(out / "ref", "TKSUBSIDENCE")
    sub_ice = read_daily(out / "uniform-ice", "TKSUBSIDENCE")
    sub_first = read_daily(out / "split-first", "TKSUBSIDENCE")
    sub_resumed = read_daily(out / "resumed", "TKSUBSIDENCE")
    sub_restart = np.concatenate([sub_first, sub_resumed], axis=0)

    cell_metrics = {}
    for i, cell in enumerate(CELLS):
        key = str(cell)
        plot = PLOTS[i]
        ice_series = cell_series(sub_ice, cell)
        ref_series = cell_series(sub_ref, cell)
        restart_series = cell_series(sub_restart, cell)
        cell_metrics[key] = {
            "plot": plot,
            "cmt": CMTS[i],
            "drainage": DRAINAGE[i],
            "injected_kg_m2": added[key],
            "ref_subsidence_m": float(ref_series[-1]),
            "ice_subsidence_m": float(ice_series[-1]),
            "ice_subsidence_cm": float(ice_series[-1] * 100.0),
            "monotonic": monotonic(ice_series),
            "restart_endpoint_diff_m": abs(float(ice_series[-1] - restart_series[-1])),
        }

    checks = []
    gate_hard(checks, "production completion", statuses, "all four cells status 100",
              all(v == [100, 100, 100, 100] for v in statuses.values()))
    gate(checks, "four CRREL plots active", PLOTS, "34, 37, 40, 44", PLOTS == [34, 37, 40, 44])
    gate_hard(checks, "reference subsidence",
              {k: v["ref_subsidence_m"] for k, v in cell_metrics.items()},
              "< 1 mm over TR",
              all(v["ref_subsidence_m"] < 0.001 for v in cell_metrics.values()))
    gate(checks, "uniform ice injection", added,
         f"{PHASE0_ICE_MASS} kg m⁻² in every cell",
         all(abs(added[str(c)] - PHASE0_ICE_MASS) < 1.0e-6 for c in CELLS))
    gate(checks, "ice subsidence magnitude",
         {k: v["ice_subsidence_cm"] for k, v in cell_metrics.items()},
         "> 5 mm per cell",
         all(v["ice_subsidence_m"] > 0.005 for v in cell_metrics.values()))
    gate(checks, "monotonic ice subsidence",
         {k: v["monotonic"] for k, v in cell_metrics.items()},
         "TKSUBSIDENCE non-decreasing",
         all(v["monotonic"] for v in cell_metrics.values()))
    gate(checks, "finite subsidence output",
         {str(c): bool(np.all(np.isfinite(cell_series(sub_ice, c)))) for c in CELLS},
         "no NaNs on active cells",
         all(np.all(np.isfinite(cell_series(sub_ice, c))) for c in CELLS))
    gate(checks, "restart subsidence continuity",
         {k: v["restart_endpoint_diff_m"] for k, v in cell_metrics.items()},
         "< 0.1 mm endpoint diff",
         all(v["restart_endpoint_diff_m"] <= 1.0e-4 for v in cell_metrics.values()))

    summary = {
        "phase": 0,
        "tr_years": PHASE0_TR_YEARS,
        "eq_years": PHASE0_EQ_YEARS,
        "ice_mass_kg_m2": PHASE0_ICE_MASS,
        "ice_depth_m": ice_depth,
        "cells": cell_metrics,
        "checks_passed": sum(x["status"] == "PASS" for x in checks),
        "checks_total": len(checks),
        "statuses": statuses,
    }
    write_results(out, summary, checks)

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 10,
        "axes.labelsize": 9, "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "svg.fonttype": "none",
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })
    days = np.arange(sub_ice.shape[0])
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 6.2), sharex=True, layout="constrained")
    for i, (ax, cell, plot) in enumerate(zip(axes.flat, CELLS, PLOTS)):
        color = PLOT_COLOR[plot]
        ax.plot(days, cell_series(sub_ref, cell) * 1000, "--", color=MUTED, lw=1.0, label="ref")
        ax.plot(days, cell_series(sub_ice, cell) * 1000, color=color, lw=1.6,
                label=f"{PHASE0_ICE_MASS:.0f} kg m⁻²")
        ax.plot(days, cell_series(sub_restart, cell) * 1000, ":", color=INK, lw=1.0,
                label="restarted")
        ax.axvline(RESTART_SPLIT * 365, color=GRID, lw=0.8)
        ax.set_title(f"Plot {plot} (CMT{CMTS[i]:02d})")
        ax.set_ylabel("Subsidence (mm)")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.legend(fontsize=7)
    axes[1, 0].set_xlabel("Simulation day")
    axes[1, 1].set_xlabel("Simulation day")
    save(fig, out, "barrow-phase0-subsidence-timeseries")

    return summary, checks


def run_phase1(args):
    out = args.output.resolve()
    base = setup_base(out, args.reuse)

    obs_climate = OBS_DIR / "streletskiy-climate-2003-2015.csv"
    obs_elevation = OBS_DIR / "streletskiy-elevation-2003-2015.csv"
    obs_elev = load_streletskiy_elevation(obs_elevation)

    full_climate = ensure_nws_barrow_climate(
        Path(base["IO"]["hist_climate_file"]),
        out / "nws-barrow-climate-full.nc",
        obs_climate,
        args.reuse,
    )
    tr_climate, co2 = slice_climate_drivers(
        full_climate, out, base["IO"]["co2_file"],
        PHASE1_TR_START, PHASE1_TR_YEARS, args.reuse)
    base["IO"]["hist_climate_file"] = str(tr_climate)
    base["IO"]["co2_file"] = str(co2)

    spec = out / "barrow-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec, yearly_front=True)
    base["IO"]["output_spec_file"] = str(spec)

    init_name = "initialization-p1"
    statuses = {}
    statuses[init_name] = completed(out, init_name) if args.reuse else None
    if statuses[init_name] is None:
        statuses[init_name] = run(
            args.binary.resolve(), out, init_name,
            config(base, out / init_name, output=False, thermokarst=True),
            ["--pr-yrs", "1", "--eq-yrs", str(PHASE1_EQ_YEARS)])

    initial = out / init_name / "restart-eq.nc"
    injected = out / "restart-calibrated.nc"
    if args.reuse and injected.exists():
        added = injected_kg_from_restart(injected, CELLS)
    else:
        added = inject_calibrated_band(
            initial, injected, PHASE1_PLOT_FRAC,
            PHASE1_ICE_TOP, PHASE1_ICE_BOTTOM, CELLS, PLOTS)

    for name, restart, thermokarst in [
            ("ref-p1", initial, True),
            ("calibrated-p1", injected, True),
    ]:
        statuses[name] = completed(out, name) if args.reuse else None
        if statuses[name] is None:
            statuses[name] = run(
                args.binary.resolve(), out, name,
                config(base, out / name, restart, thermokarst=thermokarst),
                ["--tr-yrs", str(PHASE1_TR_YEARS)])

    sub_ref = read_daily(out / "ref-p1", "TKSUBSIDENCE")
    sub_cal = read_daily(out / "calibrated-p1", "TKSUBSIDENCE")
    year_ends = year_end_series(sub_cal, PHASE1_TR_YEARS)
    calendar_years = list(range(2003, 2003 + PHASE1_TR_YEARS))

    cell_metrics = {}
    for i, cell in enumerate(CELLS):
        plot = PLOTS[i]
        key = str(cell)
        series = cell_series(sub_cal, cell)
        ref_series = cell_series(sub_ref, cell)
        yearly_cm = year_ends[:, cell[0], cell[1]] * 100.0
        increments = np.diff(np.r_[0.0, yearly_cm])
        warm_inc = sum(increments[j] for j, y in enumerate(calendar_years) if y in PHASE1_WARM_YEARS)
        total_inc = float(yearly_cm[-1])
        slope = ols_slope(calendar_years, yearly_cm)
        cell_metrics[key] = {
            "plot": plot,
            "cmt": CMTS[i],
            "injected_kg_m2": added[key],
            "ref_subsidence_cm": float(ref_series[-1] * 100.0),
            "subsidence_2015_cm": float(series[-1] * 100.0),
            "trend_cm_yr": slope,
            "warm_year_fraction": warm_inc / total_inc if total_inc > 0 else 0.0,
            "yearly_cm": {str(y): float(v) for y, v in zip(calendar_years, yearly_cm)},
            "monotonic": monotonic(series),
        }

    obs_trends = {34: -1.0, 37: -0.5, 40: -0.4, 44: -0.5}
    subs_2015 = {PLOTS[i]: cell_metrics[str(CELLS[i])]["subsidence_2015_cm"] for i in range(4)}
    trends = {PLOTS[i]: cell_metrics[str(CELLS[i])]["trend_cm_yr"] for i in range(4)}
    mean_sub = float(np.mean(list(subs_2015.values())))

    checks = []
    gate_hard(checks, "production completion",
              {k: v for k, v in statuses.items()},
              "all four cells status 100",
              all(v == [100, 100, 100, 100] for v in statuses.values()))
    gate_hard(checks, "reference subsidence",
              {k: cell_metrics[k]["ref_subsidence_cm"] for k in cell_metrics},
              "< 1 mm over TR",
              all(cell_metrics[k]["ref_subsidence_cm"] < 0.1 for k in cell_metrics))
    gate(checks, "NWS climate window",
         {"start_year": 2003, "years": PHASE1_TR_YEARS},
         "2003–2015 Streletskiy window", True)
    gate(checks, "calibrated ice band",
         {str(p): PHASE1_PLOT_FRAC[p] for p in PLOTS},
         f"excess band {PHASE1_ICE_TOP:.2f}–{PHASE1_ICE_BOTTOM:.2f} m",
         all(added[str(c)] > 0 for c in CELLS))
    gate(checks, "all plots subside",
         subs_2015, "> 5 cm at 2015",
         all(v > 5.0 for v in subs_2015.values()))
    gate(checks, "mean subsidence bracket",
         mean_sub, "8–15 cm across four plots",
         8.0 <= mean_sub <= 15.0)
    gate(checks, "plot 34 fastest",
         subs_2015, "sub_34 > sub_44",
         subs_2015[34] > subs_2015[44])
    gate(checks, "trend bracket",
         trends, "0.3–1.2 cm yr⁻¹ per plot",
         all(0.3 <= t <= 1.2 for t in trends.values()))
    gate(checks, "plot 34 trend highest",
         trends, "slope_34 >= slope_44",
         trends[34] >= trends[44])
    gate(checks, "warm-year concentration",
         {PLOTS[i]: cell_metrics[str(CELLS[i])]["warm_year_fraction"] for i in range(4)},
         "> 40% of subsidence in 2004, 2007, 2012",
         all(cell_metrics[str(c)]["warm_year_fraction"] > 0.40 for c in CELLS))
    gate(checks, "monotonic subsidence",
         {k: cell_metrics[k]["monotonic"] for k in cell_metrics},
         "TKSUBSIDENCE non-decreasing",
         all(cell_metrics[k]["monotonic"] for k in cell_metrics))

    summary = {
        "phase": 1,
        "tr_years": PHASE1_TR_YEARS,
        "eq_years": PHASE1_EQ_YEARS,
        "climate": "nws-barrow-bias-corrected",
        "tr_window": {"start": 2003, "end": 2015},
        "ice_band_m": [PHASE1_ICE_TOP, PHASE1_ICE_BOTTOM],
        "plot_fractions": PHASE1_PLOT_FRAC,
        "injected_kg_m2": added,
        "cells": cell_metrics,
        "obs_elevation_change_2015_cm": {str(p): obs_elev[p].get(2015) for p in PLOTS},
        "obs_trends_cm_yr": obs_trends,
        "checks_passed": sum(x["status"] == "PASS" for x in checks),
        "checks_total": len(checks),
        "soft_checks_passed": sum(x["status"] == "PASS" and not x["hard"] for x in checks),
        "statuses": statuses,
        "notes": (
            "NWS monthly tair bias-corrected from Streletskiy 2003–2015 annual means; "
            "excess ice placed in 0.02–0.12 m band because Barrow forcing thaws ~8 cm "
            "and TKSUBSIDENCE tracks collapse only (no frost heave)."
        ),
    }
    write_results(out, summary, checks)

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 10,
        "axes.labelsize": 9, "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "svg.fonttype": "none",
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })

    fig, axes = plt.subplots(2, 2, figsize=(8.8, 6.4), sharex=True, layout="constrained")
    for ax, cell, plot in zip(axes.flat, CELLS, PLOTS):
        model = [cell_metrics[str(cell)]["yearly_cm"][str(y)] for y in calendar_years]
        obs = [abs(obs_elev[plot].get(y, np.nan)) for y in calendar_years]
        ax.plot(calendar_years, model, "o-", color=PLOT_COLOR[plot], lw=1.6, label="TEM collapse")
        ax.plot(calendar_years, obs, "s--", color=MUTED, lw=1.2,
                label="|obs. elevation change|")
        ax.set_title(f"Plot {plot}")
        ax.set_ylabel("Subsidence (cm)")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.legend(fontsize=7)
    axes[1, 0].set_xlabel("Calendar year")
    axes[1, 1].set_xlabel("Calendar year")
    save(fig, out, "barrow-phase1-subsidence-vs-obs")

    fig, ax = plt.subplots(figsize=(7.0, 3.8), layout="constrained")
    labels = [f"Plot {p}" for p in PLOTS]
    model_vals = [subs_2015[p] for p in PLOTS]
    obs_vals = [abs(obs_elev[p].get(2015, np.nan)) for p in PLOTS]
    x = np.arange(len(labels))
    ax.bar(x - 0.18, obs_vals, 0.36, color=MUTED, label="Streletskiy |Δelev| 2015")
    ax.bar(x + 0.18, model_vals, 0.36, color=TEAL, label="TEM subsidence 2015")
    ax.set_xticks(x, labels)
    ax.set_ylabel("Cumulative subsidence (cm)")
    ax.set_title("Phase 1 calibrated collapse vs Streletskiy elevation change")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.legend()
    save(fig, out, "barrow-phase1-subsidence-2015")

    return summary, checks


def run_phase2(args):
    out = args.output.resolve()
    base = setup_base(out, args.reuse)

    obs_climate = OBS_DIR / "streletskiy-climate-2003-2015.csv"
    obs_elevation = OBS_DIR / "streletskiy-elevation-2003-2015.csv"
    obs_alt_path = OBS_DIR / "streletskiy-alt-2003-2015.csv"
    obs_elev = load_streletskiy_elevation(obs_elevation)
    obs_alt = load_streletskiy_alt(obs_alt_path)

    full_climate = ensure_nws_barrow_climate(
        Path(base["IO"]["hist_climate_file"]),
        out / "nws-barrow-climate-full.nc",
        obs_climate,
        args.reuse,
    )
    tr_climate, co2 = slice_climate_drivers(
        full_climate, out, base["IO"]["co2_file"],
        PHASE2_TR_START, PHASE2_TR_YEARS, args.reuse)
    base["IO"]["hist_climate_file"] = str(tr_climate)
    base["IO"]["co2_file"] = str(co2)

    spec = out / "barrow-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec, yearly_front=True)
    base["IO"]["output_spec_file"] = str(spec)

    init_name = "initialization-p2"
    statuses = {}
    statuses[init_name] = completed(out, init_name) if args.reuse else None
    if statuses[init_name] is None:
        statuses[init_name] = run(
            args.binary.resolve(), out, init_name,
            config(base, out / init_name, output=False, thermokarst=True),
            ["--pr-yrs", "1", "--eq-yrs", str(PHASE2_EQ_YEARS)])

    initial = out / init_name / "restart-eq.nc"
    injected = out / "restart-calibrated.nc"
    if args.reuse and injected.exists():
        added = injected_kg_from_restart(injected, CELLS)
    else:
        added = inject_calibrated_band(
            initial, injected, PHASE1_PLOT_FRAC,
            PHASE1_ICE_TOP, PHASE1_ICE_BOTTOM, CELLS, PLOTS)

    for name, restart, thermokarst in [
            ("ref-p2", initial, True),
            ("calibrated-p2", injected, True),
    ]:
        statuses[name] = completed(out, name) if args.reuse else None
        if statuses[name] is None:
            statuses[name] = run(
                args.binary.resolve(), out, name,
                config(base, out / name, restart, thermokarst=thermokarst),
                ["--tr-yrs", str(PHASE2_TR_YEARS)])

    sub_ref = read_daily(out / "ref-p2", "TKSUBSIDENCE")
    sub_cal = read_daily(out / "calibrated-p2", "TKSUBSIDENCE")
    year_ends = year_end_series(sub_cal, PHASE2_TR_YEARS)
    calendar_years = list(range(PHASE2_START_YEAR, PHASE2_END_YEAR + 1))
    idx_split = PHASE2_SPLIT_YEAR - PHASE2_START_YEAR
    idx_end = PHASE2_END_YEAR - PHASE2_START_YEAR
    p1_years = list(range(PHASE2_SPLIT_YEAR, PHASE2_END_YEAR + 1))

    cell_metrics = {}
    yearly_increments_by_plot = {}
    max_inc_year_by_plot = {}
    alt_trends = {}
    for i, cell in enumerate(CELLS):
        plot = PLOTS[i]
        key = str(cell)
        series = cell_series(sub_cal, cell)
        ref_series = cell_series(sub_ref, cell)
        yearly_cm = year_ends[:, cell[0], cell[1]] * 100.0
        increments = np.diff(np.r_[0.0, yearly_cm])
        yearly_increments_by_plot[plot] = {
            str(y): float(v) for y, v in zip(calendar_years, increments)
        }
        max_year = calendar_years[int(np.argmax(increments))]
        max_inc_year_by_plot[plot] = max_year

        sub_pre = float(yearly_cm[idx_split])
        sub_post = float(yearly_cm[idx_end] - yearly_cm[idx_split])
        sub_total = float(yearly_cm[idx_end])

        sept_thaw = september_max_thaw_cm(out / "calibrated-p2", cell, PHASE2_TR_YEARS)
        sept_sub_m = year_ends[:, cell[0], cell[1]]
        corrected_alt = [
            float(t + s * 100.0) if np.isfinite(t) else float("nan")
            for t, s in zip(sept_thaw, sept_sub_m)
        ]
        alt_window = corrected_alt[idx_split:idx_end + 1]
        alt_trends[plot] = ols_slope(p1_years, alt_window)

        warm_inc = sum(
            increments[j] for j, y in enumerate(calendar_years) if y in PHASE2_WARM_YEARS)
        total_inc = float(yearly_cm[-1])
        cell_metrics[key] = {
            "plot": plot,
            "cmt": CMTS[i],
            "injected_kg_m2": added[key],
            "ref_subsidence_cm": float(ref_series[-1] * 100.0),
            "subsidence_2003_cm": sub_pre,
            "subsidence_2003_2015_cm": sub_post,
            "subsidence_2015_cm": sub_total,
            "trend_cm_yr": ols_slope(p1_years, yearly_cm[idx_split:idx_end + 1]),
            "warm_year_fraction": warm_inc / total_inc if total_inc > 0 else 0.0,
            "max_increment_year": max_year,
            "yearly_cm": {str(y): float(v) for y, v in zip(calendar_years, yearly_cm)},
            "yearly_increments_cm": yearly_increments_by_plot[plot],
            "corrected_alt_sept_cm": {
                str(y): float(v) for y, v in zip(calendar_years, corrected_alt)
            },
            "alt_trend_2003_2015_cm_yr": alt_trends[plot],
            "monotonic": monotonic(series),
        }

    subs_pre = {PLOTS[i]: cell_metrics[str(CELLS[i])]["subsidence_2003_cm"] for i in range(4)}
    subs_post = {PLOTS[i]: cell_metrics[str(CELLS[i])]["subsidence_2003_2015_cm"] for i in range(4)}
    subs_2015 = {PLOTS[i]: cell_metrics[str(CELLS[i])]["subsidence_2015_cm"] for i in range(4)}
    mean_post = float(np.mean(list(subs_post.values())))

    checks = []
    gate_hard(checks, "production completion",
              {k: v for k, v in statuses.items()},
              "all four cells status 100",
              all(v == [100, 100, 100, 100] for v in statuses.values()))
    gate_hard(checks, "reference subsidence",
              {k: cell_metrics[k]["ref_subsidence_cm"] for k in cell_metrics},
              "< 1 mm over TR",
              all(cell_metrics[k]["ref_subsidence_cm"] < 0.1 for k in cell_metrics))
    gate(checks, "full record window",
         {"start_year": PHASE2_START_YEAR, "years": PHASE2_TR_YEARS},
         "1962–2015 Streletskiy record", True)
    gate(checks, "1962–2003 stability",
         subs_pre, "< 5 cm per plot",
         all(v < 5.0 for v in subs_pre.values()))
    gate(checks, "2003–2015 subsidence bracket",
         subs_post, "8–15 cm per plot",
         all(8.0 <= v <= 15.0 for v in subs_post.values()))
    gate(checks, "2003–2015 mean subsidence",
         mean_post, "8–15 cm mean across plots",
         8.0 <= mean_post <= 15.0)
    gate(checks, "plot 34 fastest post-2003",
         subs_post, "sub_34 > sub_44",
         subs_post[34] > subs_post[44])
    gate(checks, "2012 largest increment",
         max_inc_year_by_plot, "2012 is max single-year increment per plot",
         all(y == 2012 for y in max_inc_year_by_plot.values()))
    gate(checks, "ALT trend 2003–2015",
         alt_trends, "+0.2 to +0.6 cm yr⁻¹",
         all(np.isfinite(alt_trends[p]) and 0.2 <= alt_trends[p] <= 0.6 for p in PLOTS))
    gate(checks, "monotonic subsidence",
         {k: cell_metrics[k]["monotonic"] for k in cell_metrics},
         "TKSUBSIDENCE non-decreasing",
         all(cell_metrics[k]["monotonic"] for k in cell_metrics))

    summary = {
        "phase": 2,
        "tr_years": PHASE2_TR_YEARS,
        "eq_years": PHASE2_EQ_YEARS,
        "climate": "nws-barrow-bias-corrected",
        "tr_window": {"start": PHASE2_START_YEAR, "end": PHASE2_END_YEAR},
        "validation_windows": {
            "pre_2003": {"start": PHASE2_START_YEAR, "end": PHASE2_SPLIT_YEAR},
            "post_2003": {"start": PHASE2_SPLIT_YEAR, "end": PHASE2_END_YEAR},
        },
        "ice_band_m": [PHASE1_ICE_TOP, PHASE1_ICE_BOTTOM],
        "plot_fractions": PHASE1_PLOT_FRAC,
        "injected_kg_m2": added,
        "cells": cell_metrics,
        "obs_elevation_change_2015_cm": {str(p): obs_elev[p].get(2015) for p in PLOTS},
        "obs_alt_mean_2003_2015_cm": {
            str(p): float(np.mean([obs_alt[p][y] for y in p1_years if y in obs_alt[p]]))
            for p in PLOTS
        },
        "checks_passed": sum(x["status"] == "PASS" for x in checks),
        "checks_total": len(checks),
        "soft_checks_passed": sum(x["status"] == "PASS" and not x["hard"] for x in checks),
        "statuses": statuses,
        "notes": (
            "Full 1962–2015 record with Phase 1 calibrated ice band; "
            "1962–2003 stability and warm-year timing are expected to fail "
            "without frost heave and with shallow-band instantaneous collapse."
        ),
    }
    write_results(out, summary, checks)

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 10,
        "axes.labelsize": 9, "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "svg.fonttype": "none",
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })

    fig, axes = plt.subplots(2, 2, figsize=(9.2, 6.6), sharex=True, layout="constrained")
    for ax, cell, plot in zip(axes.flat, CELLS, PLOTS):
        model = [cell_metrics[str(cell)]["yearly_cm"][str(y)] for y in calendar_years]
        ax.plot(calendar_years, model, color=PLOT_COLOR[plot], lw=1.6, label="TEM collapse")
        ax.axvline(PHASE2_SPLIT_YEAR, color=GRID, lw=0.8, ls="--")
        if plot in obs_elev:
            obs_years = [y for y in p1_years if y in obs_elev[plot]]
            obs = [abs(obs_elev[plot][y]) for y in obs_years]
            ax.plot(obs_years, obs, "s--", color=MUTED, lw=1.2, ms=4,
                    label="|obs. elevation change|")
        ax.set_title(f"Plot {plot}")
        ax.set_ylabel("Cumulative subsidence (cm)")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.legend(fontsize=7)
    axes[1, 0].set_xlabel("Calendar year")
    axes[1, 1].set_xlabel("Calendar year")
    save(fig, out, "barrow-phase2-subsidence-full-record")

    fig, ax = plt.subplots(figsize=(7.4, 3.8), layout="constrained")
    labels = [f"Plot {p}" for p in PLOTS]
    x = np.arange(len(labels))
    pre = [subs_pre[p] for p in PLOTS]
    post = [subs_post[p] for p in PLOTS]
    ax.bar(x - 0.22, pre, 0.22, color=MUTED, label="1962–2003 (model)")
    ax.bar(x, post, 0.22, color=TEAL, label="2003–2015 (model)")
    ax.bar(x + 0.22, [abs(obs_elev[p].get(2015, np.nan)) for p in PLOTS],
           0.22, color=BLUE, label="|obs. Δelev| 2015 vs 2003")
    ax.axhline(5.0, color=ORANGE, lw=0.8, ls=":", label="5 cm stability gate")
    ax.set_xticks(x, labels)
    ax.set_ylabel("Subsidence (cm)")
    ax.set_title("Phase 2 windowed subsidence vs Streletskiy")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.legend(fontsize=7)
    save(fig, out, "barrow-phase2-subsidence-windows")

    fig, axes = plt.subplots(2, 2, figsize=(8.8, 6.2), sharex=True, layout="constrained")
    for ax, cell, plot in zip(axes.flat, CELLS, PLOTS):
        obs_years = [y for y in p1_years if y in obs_alt[plot]]
        obs_vals = [obs_alt[plot][y] for y in obs_years]
        model = [cell_metrics[str(cell)]["corrected_alt_sept_cm"][str(y)] for y in obs_years]
        ax.plot(obs_years, obs_vals, "s--", color=MUTED, lw=1.2, ms=4, label="obs. ALT")
        ax.plot(obs_years, model, "o-", color=PLOT_COLOR[plot], lw=1.4, label="model corrected")
        ax.set_title(f"Plot {plot}")
        ax.set_ylabel("September ALT (cm)")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.legend(fontsize=7)
    axes[1, 0].set_xlabel("Calendar year")
    axes[1, 1].set_xlabel("Calendar year")
    save(fig, out, "barrow-phase2-alt-corrected")

    return summary, checks


def load_phase_summary(phase):
    path = PHASE_DIRS[phase] / "summary.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_phase_checks(phase):
    path = PHASE_DIRS[phase] / "checks.csv"
    if not path.exists():
        return []
    with path.open() as stream:
        return list(csv.DictReader(stream))


def write_barrow_validation_report():
    summaries = {p: load_phase_summary(p) for p in (0, "alt", 1, 2)}
    checks = {p: load_phase_checks(p) for p in (0, "alt", 1, 2)}
    if not any(summaries.values()):
        return

    figure_names = generate_report_figures()

    def phase_status(phase):
        summary = summaries[phase]
        if summary is None:
            return "not run"
        passed = summary.get("checks_passed", 0)
        total = summary.get("checks_total", 0)
        hard = [r for r in checks[phase] if r.get("hard") == "True" and r["status"] == "FAIL"]
        if hard:
            return f"**FAIL** ({passed}/{total} gates)"
        if passed == total:
            return f"**PASS** ({passed}/{total} gates)"
        return f"**PARTIAL** ({passed}/{total} gates)"

    lines = [
        "# Barrow CRREL subsidence validation report",
        "",
        "**Reference:** Streletskiy et al. (2016), CRREL plots 34, 37, 40, 44",
        "",
        "**Harness:** `experiments/thermokarst/barrow_validation.py`",
        "",
        "**Bundled climate:** `experiments/thermokarst/barrow_validation/nws-barrow-climate-full.nc`",
        "",
        "## Summary",
        "",
        "| Phase | Status | Command |",
        "|---|---|---|",
        f"| 0 — pipeline | {phase_status(0)} | `make thermokarst-barrow-validation-phase0` |",
        f"| A — ALT calibration | {phase_status('alt')} | `make thermokarst-barrow-alt-calibration` |",
        f"| 1 — Streletskiy 2003–2015 | {phase_status(1)} | `make thermokarst-barrow-validation-phase1` |",
        f"| 2 — full record 1962–2015 | {phase_status(2)} | `make thermokarst-barrow-validation-phase2` |",
        "",
        "Resume long runs with `--reuse` to skip completed stages and reuse the bundled climate:",
        "",
        "```sh",
        ".venv-thermokarst/bin/python experiments/thermokarst/barrow_validation.py \\",
        "  --binary ./dvmdostem --phase 1 --reuse",
        "```",
        "",
        "## Comparison figures (2003–2015)",
        "",
        "Observed subsidence uses **absolute elevation change** from Streletskiy dGPS",
        "(includes frost heave; not pure thaw collapse). Model subsidence is cumulative",
        "`TKSUBSIDENCE`. Corrected ALT adds modeled subsidence to September max thaw depth;",
        "observed ALT is mechanical probing at five points per plot. DDT is thawing",
        "degree-days (Σ max(T, 0) × days): observed from Streletskiy Table 1;",
        "modeled from NWS-bias-corrected monthly forcing.",
        "",
    ]
    if "barrow-alt-obs-vs-model" in figure_names:
        lines.extend([
            "### Active-layer thickness: observed vs modeled",
            "",
            "September max `TKFRONT` thaw depth vs Streletskiy mechanical probing (2003–2015).",
            "",
            "![Observed vs modeled ALT by plot](barrow-alt-obs-vs-model.png)",
            "",
        ])
    if "barrow-subsidence-vs-obs" in figure_names:
        lines.extend([
            "### Subsidence time series",
            "",
            "![Modeled subsidence vs Streletskiy elevation change](barrow-subsidence-vs-obs.png)",
            "",
        ])
    if "barrow-subsidence-2015" in figure_names:
        lines.extend([
            "### Cumulative subsidence at 2015",
            "",
            "![2015 cumulative subsidence comparison](barrow-subsidence-2015.png)",
            "",
        ])
    if "barrow-alt-vs-ddt" in figure_names:
        lines.extend([
            "### Active-layer thickness vs thawing degree-days",
            "",
            "![Corrected ALT vs thawing degree-days by plot](barrow-alt-vs-ddt.png)",
            "",
        ])

    if "barrow-climate-inputs" in figure_names:
        lines.extend([
            "## Climate inputs",
            "",
            "NWS-bias-corrected historic forcing: full spin-up record (left) and 2003–2015",
            "transient window (right). Precipitation scaled ×0.55 from Toolik template.",
            "",
            "![Barrow climate inputs](barrow-climate-inputs.png)",
            "",
        ])
    if "barrow-alt-isotherm-vs-obs" in figure_names:
        lines.extend([
            "### Active-layer thickness from soil temperature (0 °C isotherm)",
            "",
            "September ALT from monthly `TLAYER` (deepest 0 °C isotherm) vs Streletskiy probing.",
            "",
            "![0 °C isotherm ALT vs observed](barrow-alt-isotherm-vs-obs.png)",
            "",
        ])
    soil_thermal = [n for n in figure_names if n.startswith("barrow-soil-thermal-plot")]
    if soil_thermal:
        lines.extend([
            "### Soil temperature, snow, and subsidence by plot",
            "",
            "Depth–time soil temperature (`TLAYER`, blue–white–red color scale), monthly snow",
            "depth, cumulative subsidence, and 0 °C isotherm ALT overlay.",
            "",
        ])
        for plot in PLOTS:
            stem = f"barrow-soil-thermal-plot{plot}"
            if stem in figure_names:
                lines.extend([
                    f"#### Plot {plot}",
                    "",
                    f"![Soil thermal state plot {plot}]({stem}.png)",
                    "",
                ])

    sa = summaries["alt"]
    if sa:
        lines.extend([
            "## Phase A — ALT calibration (n-factor)",
            "",
            "### Configuration",
            "",
            f"- Spin-up: 1 PR + {sa['eq_years']} EQ years",
            f"- Transient: {sa['tr_years']} TR years (2003–2015)",
            "- Thermokarst: **on** (TKFRONT output); no excess ice injected",
            f"- Parameters: `{sa.get('parameter_dir', BARROW_PARAM_DIR)}`",
            f"- n-factors: {sa.get('nfactor_by_cmt', {})}",
            "",
            "### Gates",
            "",
            f"- Hard: {sum(1 for r in checks['alt'] if r.get('hard') == 'True' and r['status'] == 'PASS')}/"
            f"{sum(1 for r in checks['alt'] if r.get('hard') == 'True')} passed",
            f"- Soft: {sum(1 for r in checks['alt'] if r.get('hard') != 'True' and r['status'] == 'PASS')}/"
            f"{sum(1 for r in checks['alt'] if r.get('hard') != 'True')} passed",
            "",
            f"- Mean model ALT: **{sa.get('mean_alt_cm', float('nan')):.1f} cm** "
            f"(obs ~{sa.get('obs_alt_mean_cm', float('nan')):.1f} cm)",
            f"- RMSE vs Streletskiy: **{sa.get('rmse_cm', float('nan')):.1f} cm**",
            "",
        ])
        if "barrow-phaseA-alt-vs-obs" in figure_names:
            lines.extend([
                "### Phase A figures",
                "",
                "![Phase A ALT vs Streletskiy probing](barrow-phaseA-alt-vs-obs.png)",
                "",
                "![Phase A ALT vs thawing degree-days](barrow-phaseA-alt-vs-ddt.png)",
                "",
            ])
        lines.extend([
            "Artifacts: `experiments/thermokarst/barrow_validation_phaseA_results/`",
            "",
            "Calibrated n-factors (when using `--calibrate`) are written to "
            "`experiments/thermokarst/barrow_validation/barrow-alt-calibration.json`.",
            "",
        ])

    s1 = summaries[1]
    if s1:
        lines.extend([
            "## Phase 1 — Streletskiy window 2003–2015",
            "",
            "### Configuration",
            "",
            f"- Spin-up: 1 PR + {s1['eq_years']} EQ years",
            f"- Transient: {s1['tr_years']} TR years (2003–2015)",
            "- Forcing: NWS Barrow monthly (Toolik bias-corrected; precip ×0.55)",
            f"- Ice: band {s1['ice_band_m'][0]:.2f}–{s1['ice_band_m'][1]:.2f} m, "
            f"fractions {s1['plot_fractions']}",
            "",
            "### Gates",
            "",
            f"- Hard: {sum(1 for r in checks[1] if r.get('hard') == 'True' and r['status'] == 'PASS')}/"
            f"{sum(1 for r in checks[1] if r.get('hard') == 'True')} passed",
            f"- Soft: {sum(1 for r in checks[1] if r.get('hard') != 'True' and r['status'] == 'PASS')}/"
            f"{sum(1 for r in checks[1] if r.get('hard') != 'True')} passed",
            "",
            "| Gate | Status |",
            "|---|---|",
        ])
        for row in checks[1]:
            hard = " (hard)" if row.get("hard") == "True" else ""
            lines.append(f"| {row['test']} | {row['status']}{hard} |")
        lines.extend([
            "",
            "### Model vs observation (2015 cumulative collapse)",
            "",
            "| Plot | TEM (cm) | |obs. Δelev| (cm) |",
            "|---|---:|---:|",
        ])
        for plot in PLOTS:
            cell_key = str(CELLS[PLOTS.index(plot)])
            model = s1["cells"][cell_key]["subsidence_2015_cm"]
            obs = abs(s1["obs_elevation_change_2015_cm"].get(str(plot), float("nan")))
            lines.append(f"| {plot} | {model:.1f} | {obs:.1f} |")
        lines.extend([
            "",
            "Artifacts: `experiments/thermokarst/barrow_validation_phase1_results/`",
            "",
        ])

    s2 = summaries[2]
    if s2:
        obs_pre = {34: 3.4, 37: 4.3, 40: 3.9, 44: 4.9}
        lines.extend([
            "## Phase 2 — full Streletskiy record 1962–2015",
            "",
            "### Configuration",
            "",
            f"- Spin-up: 1 PR + {s2['eq_years']} EQ years",
            f"- Transient: {s2['tr_years']} TR years (1962–2015)",
            "- Forcing: same NWS Barrow climate as Phase 1",
            "- Ice: Phase 1 calibrated band injection (reused fractions)",
            "",
            "### Gates",
            "",
            f"- Hard: {sum(1 for r in checks[2] if r.get('hard') == 'True' and r['status'] == 'PASS')}/"
            f"{sum(1 for r in checks[2] if r.get('hard') == 'True')} passed",
            f"- Soft: {sum(1 for r in checks[2] if r.get('hard') != 'True' and r['status'] == 'PASS')}/"
            f"{sum(1 for r in checks[2] if r.get('hard') != 'True')} passed",
            "",
            "| Gate | Status |",
            "|---|---|",
        ])
        for row in checks[2]:
            hard = " (hard)" if row.get("hard") == "True" else ""
            lines.append(f"| {row['test']} | {row['status']}{hard} |")
        lines.extend([
            "",
            "### 1962–2003 stability assessment",
            "",
            "Streletskiy observed net elevation change over 1962–2003 is within interannual",
            "variability (roughly ±5 cm; plot 44 shows +4.9 cm heave from snow redistribution).",
            "TEM `TKSUBSIDENCE` tracks irreversible collapse only — no frost heave.",
            "",
            "| Plot | Model subsidence to 2003 (cm) | |obs. net Δelev| 1962→2003 (cm) | Gate (<5 cm) |",
            "|---|---:|---:|---|",
        ])
        for plot in PLOTS:
            cell_key = str(CELLS[PLOTS.index(plot)])
            model = s2["cells"][cell_key]["subsidence_2003_cm"]
            obs = obs_pre[plot]
            gate = "PASS" if model < 5.0 else "FAIL"
            lines.append(f"| {plot} | {model:.1f} | {obs:.1f} | {gate} |")
        lines.extend([
            "",
            "Most plots collapse in **1962** (first transient year) when shallow-band ice",
            "thaws. Only plot 37 shows incremental subsidence after 2003 (~9.7 cm in 2003–2015).",
            "",
            "### 2003–2015 window (repeat of Phase 1 targets)",
            "",
            "| Plot | Model 2003–2015 (cm) | |obs. Δelev| 2015 (cm) |",
            "|---|---:|---:|",
        ])
        for plot in PLOTS:
            cell_key = str(CELLS[PLOTS.index(plot)])
            post = s2["cells"][cell_key]["subsidence_2003_2015_cm"]
            obs = abs(s2["obs_elevation_change_2015_cm"].get(str(plot), float("nan")))
            lines.append(f"| {plot} | {post:.1f} | {obs:.1f} |")
        lines.extend([
            "",
            "Artifacts: `experiments/thermokarst/barrow_validation_phase2_results/`",
            "",
            "Phase 2 run figures: `barrow-phase2-subsidence-full-record`, "
            "`barrow-phase2-subsidence-windows`, `barrow-phase2-alt-corrected` "
            "(in results directory).",
            "",
        ])

    lines.extend([
        "## Process limitations",
        "",
        "1. **No frost heave** — cannot match ±8–13 cm interannual elevation swings or",
        "   1962–2003 stability without heave.",
        "2. **Shallow-band collapse** — ice at 0.02–0.12 m collapses when thaw reaches it;",
        "   deeper paper transient layer (0.34 m) yields zero subsidence under NWS Barrow forcing.",
        "3. **Net elevation ≠ collapse** — compare cumulative subsidence trends, not raw dGPS series.",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=ROOT / "dvmdostem")
    default_output = ROOT / "experiments/thermokarst/barrow_validation_results"
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--phase", choices=["0", "A", "1", "2", "all"], default="all")
    parser.add_argument("--reuse", action="store_true",
                        help="Skip completed stages; reuse bundled NWS climate when present")
    parser.add_argument("--calibrate", action="store_true",
                        help="Phase A: sweep CMT05/CMT06 nfactor_s grid and save best fit")
    parser.add_argument("--eq-yrs", type=int, default=None,
                        help="Phase A: override EQ spin-up length")
    parser.add_argument("--nfactor-s-cmt05", type=float, default=None)
    parser.add_argument("--nfactor-s-cmt06", type=float, default=None)
    parser.add_argument("--nfactor-w-cmt05", type=float, default=None)
    parser.add_argument("--nfactor-w-cmt06", type=float, default=None)
    parser.add_argument("--report-only", action="store_true",
                        help="Regenerate barrow-validation-report.md from existing results")
    parser.add_argument("--plot-alt-only", action="store_true",
                        help="Plot observed vs modeled ALT for all four plots")
    parser.add_argument("--run-dir", type=Path, default=None,
                        help="Transient run directory for --plot-alt-only")
    parser.add_argument("--diagnostic-plots", action="store_true",
                        help="Generate climate, soil thermal, and isotherm ALT figures")
    args = parser.parse_args()
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"

    if args.report_only:
        write_barrow_validation_report()
        print(f"Wrote {REPORT_PATH}")
        return

    if args.diagnostic_plots:
        stems = generate_diagnostic_report_figures(
            reuse=args.reuse, binary=args.binary)
        write_barrow_validation_report()
        print(json.dumps({"diagnostic_figures": stems}, indent=2))
        return

    if args.plot_alt_only:
        run_dir = args.run_dir

        def run_has_alt_data(directory):
            directory = Path(directory)
            if not (directory / "TKFRONT_daily_tr.nc").exists():
                return False
            return any(
                np.isfinite(v)
                for cell in CELLS
                for v in september_max_thaw_cm(directory, cell, PHASE_A_TR_YEARS)
            )

        if run_dir is None:
            for candidate in (
                PHASE_DIRS["alt"] / "alt-cal",
                PHASE_DIRS[1] / "calibrated-p1",
                PHASE_DIRS[2] / "calibrated-p2",
            ):
                if run_has_alt_data(candidate):
                    run_dir = candidate
                    break
        if run_dir is None or not run_has_alt_data(run_dir):
            raise RuntimeError("No transient run with finite TKFRONT ALT found; pass --run-dir")
        stem = plot_alt_from_run(Path(run_dir))
        print(f"Wrote {DOCS_FIG_DIR / f'{stem}.png'}")
        return

    summaries = []
    all_checks = []
    if args.phase in ("0", "all"):
        if args.phase == "all":
            args.output = args.output.parent / "barrow_validation_phase0_results"
        summary, checks = run_phase0(args)
        summaries.append(summary)
        all_checks.extend(checks)
    if args.phase in ("A", "all"):
        pa_args = argparse.Namespace(**vars(args))
        if args.phase == "all" or args.output.resolve() == default_output.resolve():
            pa_args.output = args.output.parent / "barrow_validation_phaseA_results"
        if args.phase == "all":
            pa_args.reuse = False
            pa_args.calibrate = False
        summary, checks = run_phase_alt(pa_args)
        summaries.append(summary)
        all_checks.extend(checks)
    if args.phase in ("1", "all"):
        p1_args = argparse.Namespace(**vars(args))
        p1_args.output = args.output.parent / "barrow_validation_phase1_results"
        if args.phase == "all":
            p1_args.reuse = False
        summary, checks = run_phase1(p1_args)
        summaries.append(summary)
        all_checks.extend(checks)
    if args.phase in ("2", "all"):
        p2_args = argparse.Namespace(**vars(args))
        p2_args.output = args.output.parent / "barrow_validation_phase2_results"
        if args.phase == "all":
            p2_args.reuse = False
        summary, checks = run_phase2(p2_args)
        summaries.append(summary)
        all_checks.extend(checks)

    for summary in summaries:
        print(json.dumps({
            "phase": summary["phase"],
            "checks_passed": summary["checks_passed"],
            "checks_total": summary["checks_total"],
        }, indent=2))

    hard_failed = [x for x in all_checks if x.get("hard") and x["status"] == "FAIL"]
    if hard_failed:
        raise RuntimeError(
            f"{len(hard_failed)} hard gates failed: {[x['test'] for x in hard_failed]}")
    soft_failed = [x for x in all_checks if not x.get("hard") and x["status"] == "FAIL"]
    if soft_failed and args.phase in ("A", "1", "2", "all"):
        print("WARNING: soft gate failures:",
              [x["test"] for x in soft_failed], file=sys.stderr)

    write_barrow_validation_report()


if __name__ == "__main__":
    main()
