#!/usr/bin/env python3
"""Run a BGC thermokarst diagnostic to evaluate carbon cycle feedback."""

import argparse
import json
import os
import shutil
import sys
import warnings
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

ROOT = Path(__file__).resolve().parents[2]
MATPLOTLIB_CACHE = ROOT / "build/matplotlib-cache"
MATPLOTLIB_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MATPLOTLIB_CACHE))

original_path = os.environ.get("PATH", "")
if sys.platform == "darwin":
    os.environ["PATH"] = os.pathsep.join(
        item for item in original_path.split(os.pathsep)
        if item not in ("/usr/sbin", "/sbin"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
os.environ["PATH"] = original_path

import production_validation as production

def make_warm_climate(source, destination):
    shutil.copy2(source, destination)
    with Dataset(destination, "r+") as dataset:
        shape = dataset["tair"].shape
        # Warm the climate by +5 C
        dataset["tair"][:] = dataset["tair"][:] + 5.0
        # Increase precip slightly to prevent drought? 
        # Leave precip as is for now.

def read_yearly_output(result_root, variable, stage="tr"):
    path = result_root / f"{variable}_yearly_{stage}.nc"
    if not path.exists():
        return np.zeros(0)
    with Dataset(path) as dataset:
        val = dataset.variables[variable][:, 0, 0]
        if np.ma.isMaskedArray(val):
            val = val.filled(np.nan)
        return val

def setup_style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
        "legend.frameon": False,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    })

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=ROOT / "dvmdostem")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/thermokarst/bgc_diagnostic_results")
    args = parser.parse_args()
    
    binary = args.binary.resolve()
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    base = production.parse_json_with_comments(ROOT / "config/config.js")
    for key, value in list(base["IO"].items()):
        if key.endswith("_file") or key == "parameter_dir":
            base["IO"][key] = str((ROOT / value).resolve())
            
    runmask = output / "run-mask-one-cell.nc"
    shutil.copy2(base["IO"]["runmask_file"], runmask)
    with Dataset(runmask, "r+") as dataset:
        dataset["run"][...] = 0
        dataset["run"][0, 0] = 1

    historic_climate = Path(base["IO"]["hist_climate_file"])
    warm_climate = output / "warm-climate.nc"
    make_warm_climate(historic_climate, warm_climate)

    def make_bgc_config(name, climate, restart_from, eq=False):
        cfg = production.clone_config(base, output / name, runmask, True, 0.20, climate, restart_from)
        cfg["model_settings"]["thermokarst"].update({"top_depth": 0.5, "bottom_depth": 1.5})
        
        # Enable BGC for EQ and TR
        for stage in ["pr", "eq", "tr"]:
            cfg["stage_settings"][stage].update({
                "env": True, "bgc": True, "nfeed": True, "avlnflg": True,
                "baseline": False, "dsb": False, "dsl": False, "dyn_lai": True,
            })
            
        cfg["IO"]["output_nc_tr"] = 1
        if eq:
            cfg["IO"]["output_nc_eq"] = 1
        return cfg

    # 1. Spin up (pr + eq)
    spinup_cfg = make_bgc_config("spinup", historic_climate, None, eq=True)
    production.run_case(binary, output, "spinup", spinup_cfg, ["--pr-yrs", "1", "--eq-yrs", "10"])
    
    eq_restart = output / "spinup/restart-eq.nc"

    # 2. Control TR
    control_cfg = make_bgc_config("control", historic_climate, eq_restart)
    production.run_case(binary, output, "control", control_cfg, ["--tr-yrs", "5"])
    
    # 3. Thaw TR
    thaw_cfg = make_bgc_config("thaw", warm_climate, eq_restart)
    production.run_case(binary, output, "thaw", thaw_cfg, ["--tr-yrs", "5"])

    # Load Outputs
    vars_to_load = ["GPP", "NPP", "RHSOM", "SOC", "VEGC", "TKSUBSIDENCE"]
    
    control_data = {}
    thaw_data = {}
    for var in vars_to_load:
        if var == "TKSUBSIDENCE":
            # It's daily! We just get max per year or load daily. Let's load daily.
            c_path = output / f"control/TKSUBSIDENCE_daily_tr.nc"
            t_path = output / f"thaw/TKSUBSIDENCE_daily_tr.nc"
            with Dataset(c_path) as cd:
                control_data[var] = cd["TKSUBSIDENCE"][:,0,0].reshape(-1, 365).max(axis=1)
            with Dataset(t_path) as td:
                thaw_data[var] = td["TKSUBSIDENCE"][:,0,0].reshape(-1, 365).max(axis=1)
        else:
            control_data[var] = read_yearly_output(output / "control", var)
            thaw_data[var] = read_yearly_output(output / "thaw", var)

    setup_style()
    years = np.arange(1, len(control_data["GPP"]) + 1)
    
    fig, axes = plt.subplots(2, 2, figsize=(8.5, 6.0), layout="constrained")
    
    # GPP
    axes[0, 0].plot(years, control_data["GPP"], label="Control", color="#8D8D88", linestyle="--")
    axes[0, 0].plot(years, thaw_data["GPP"], label="Abrupt Thaw (+5°C)", color="#1F6F5F")
    axes[0, 0].set_ylabel("GPP (gC m⁻² yr⁻¹)")
    axes[0, 0].set_title("(a) Gross Primary Production")
    axes[0, 0].legend()
    
    # RHSOM
    axes[0, 1].plot(years, control_data["RHSOM"], label="Control", color="#8D8D88", linestyle="--")
    axes[0, 1].plot(years, thaw_data["RHSOM"], label="Abrupt Thaw (+5°C)", color="#D55E00")
    axes[0, 1].set_ylabel("Heterotrophic Resp (gC m⁻² yr⁻¹)")
    axes[0, 1].set_title("(b) Soil Respiration (RHSOM)")
    
    # SOC
    axes[1, 0].plot(years, control_data["SOC"], label="Control", color="#8D8D88", linestyle="--")
    axes[1, 0].plot(years, thaw_data["SOC"], label="Abrupt Thaw (+5°C)", color="#0072B2")
    axes[1, 0].set_ylabel("Total SOC (gC m⁻²)")
    axes[1, 0].set_xlabel("Transition Year")
    axes[1, 0].set_title("(c) Soil Organic Carbon")
    
    # Subsidence
    axes[1, 1].plot(years, control_data["TKSUBSIDENCE"] * 1000, label="Control", color="#8D8D88", linestyle="--")
    axes[1, 1].plot(years, thaw_data["TKSUBSIDENCE"] * 1000, label="Abrupt Thaw (+5°C)", color="#CC79A7")
    axes[1, 1].set_ylabel("Subsidence (mm)")
    axes[1, 1].set_xlabel("Transition Year")
    axes[1, 1].set_title("(d) Thermokarst Subsidence")
    
    fig.savefig(output / "bgc_feedback.png", dpi=240)
    fig.savefig(output / "bgc_feedback.svg")
    plt.close(fig)

if __name__ == "__main__":
    main()
