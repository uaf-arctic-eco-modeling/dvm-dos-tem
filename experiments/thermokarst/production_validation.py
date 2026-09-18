#!/usr/bin/env python3
"""Run production TEM thermokarst parity and restart validations."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import warnings

from netCDF4 import Dataset
import numpy as np


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

warnings.filterwarnings(
    "ignore", message="Setting the shape on a NumPy array has been deprecated",
    category=DeprecationWarning)


def parse_json_with_comments(path):
    lines = []
    for line in path.read_text().splitlines():
        quote = escape = False
        out = []
        i = 0
        while i < len(line):
            char = line[i]
            if escape:
                out.append(char)
                escape = False
            elif char == "\\" and quote:
                out.append(char)
                escape = True
            elif char == '"':
                out.append(char)
                quote = not quote
            elif not quote and char == "/" and i + 1 < len(line) and line[i + 1] == "/":
                break
            else:
                out.append(char)
            i += 1
        lines.append("".join(out))
    return json.loads("\n".join(lines))


def clone_config(base, output, runmask, enabled, fraction, climate=None,
                 restart=None):
    config = json.loads(json.dumps(base))
    io = config["IO"]
    io["runmask_file"] = str(runmask)
    io["output_dir"] = str(output) + "/"
    io["restart_from"] = str(restart) if restart else ""
    io["output_monthly"] = 0
    for key in ["output_nc_eq", "output_nc_sp", "output_nc_tr", "output_nc_sc"]:
        io[key] = 0
    if climate:
        io["hist_climate_file"] = str(climate)
    config["model_settings"]["thermokarst"] = {
        "enabled": enabled,
        "excess_fraction": fraction,
        "top_depth": 0.2,
        "bottom_depth": 1.0,
    }
    for stage in ["pr", "eq", "sp", "tr", "sc"]:
        config["stage_settings"][stage].update({
            "env": True, "bgc": False, "nfeed": False, "avlnflg": False,
            "baseline": False, "dsb": False, "dsl": False, "dyn_lai": False,
        })
    return config


def run_case(binary, result_root, name, config, years):
    config_path = result_root / f"{name}.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    command = [str(binary), "-f", str(config_path), "--log-level", "warn",
               "--max-output-volume=-1"] + years
    with (result_root / f"{name}.log").open("w") as log:
        completed = subprocess.run(command, cwd=ROOT, stdout=log,
                                   stderr=subprocess.STDOUT, check=False)
    if completed.returncode:
        raise RuntimeError(f"{name} exited {completed.returncode}")
    with Dataset(result_root / name / "run_status.nc") as dataset:
        status = int(dataset["run_status"][0, 0])
    if status != 100:
        failure = result_root / name / "fail_log.txt"
        detail = failure.read_text() if failure.exists() else "no fail_log.txt"
        raise RuntimeError(f"{name} cell status {status}: {detail}")


def restart_state(path):
    result = {}
    with Dataset(path) as dataset:
        n = int(dataset["numsl"][0, 0])
        result["numsl"] = n
        for name in ["DZsoil", "TSsoil", "LIQsoil", "ICEsoil",
                     "FROZENsoil", "FROZENFRACsoil"]:
            result[name] = np.asarray(dataset[name][0, 0, :n])
        for name in ["frontZ", "frontFT", "TKstate", "TKmatrix",
                     "TKporosity", "TKexcess"]:
            result[name] = np.asarray(dataset[name][0, 0])
        result["watertab"] = float(dataset["watertab"][0, 0])
    return result


def active_pixel_variables(path):
    values = {}
    with Dataset(path) as dataset:
        for name, variable in dataset.variables.items():
            if variable.dimensions[:2] != ("Y", "X"):
                continue
            value = variable[0, 0]
            values[name] = np.ma.filled(value, variable.getncattr("_FillValue")
                                        if "_FillValue" in variable.ncattrs() else 0)
    return values


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT / "dvmdostem")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/thermokarst/production_validation_results")
    args = parser.parse_args()
    binary = args.binary.resolve()
    output = args.output.resolve()
    if not binary.exists():
        raise FileNotFoundError(f"production binary not found: {binary}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    base = parse_json_with_comments(ROOT / "config/config.js")
    for section in ["IO"]:
        for key, value in list(base[section].items()):
            if key.endswith("_file") or key == "parameter_dir":
                base[section][key] = str((ROOT / value).resolve())

    # One active Toolik grid cell.
    runmask = output / "run-mask-one-cell.nc"
    shutil.copy2(base["IO"]["runmask_file"], runmask)
    with Dataset(runmask, "r+") as dataset:
        values = np.zeros(dataset["run"].shape, dtype=dataset["run"].dtype)
        values[0, 0] = 1
        dataset["run"][:] = values

    # A constant cold atmosphere makes climate year zero and year one exactly
    # interchangeable when TEM resets its stage-relative climate index on resume.
    cold_climate = output / "cold-historic-climate.nc"
    shutil.copy2(base["IO"]["hist_climate_file"], cold_climate)
    with Dataset(cold_climate, "r+") as dataset:
        shape = dataset["tair"].shape
        dataset["tair"][:] = np.full(shape, -20.0, dtype="f4")
        dataset["precip"][:] = np.zeros(shape, dtype="f4")
        dataset["nirr"][:] = np.zeros(shape, dtype="f4")
        dataset["vapor_press"][:] = np.ones(shape, dtype="f4")

    legacy = clone_config(base, output / "zero-legacy", runmask, False, 0.0)
    zero_tk = clone_config(base, output / "zero-thermokarst", runmask, True, 0.0)
    cold_seed = clone_config(base, output / "cold-seed", runmask, True, 0.2,
                             cold_climate)
    run_case(binary, output, "zero-legacy", legacy, ["--pr-yrs", "1"])
    run_case(binary, output, "zero-thermokarst", zero_tk, ["--pr-yrs", "1"])
    run_case(binary, output, "cold-seed", cold_seed, ["--pr-yrs", "1"])

    seed_restart = output / "cold-seed/restart-pr.nc"
    continuous = clone_config(base, output / "cold-continuous", runmask, True,
                              0.2, cold_climate, seed_restart)
    split_first = clone_config(base, output / "cold-split-first", runmask, True,
                               0.2, cold_climate, seed_restart)
    run_case(binary, output, "cold-continuous", continuous, ["--tr-yrs", "2"])
    run_case(binary, output, "cold-split-first", split_first, ["--tr-yrs", "1"])
    midpoint = output / "cold-split-first/restart-tr.nc"
    resumed = clone_config(base, output / "cold-resumed", runmask, True, 0.2,
                           cold_climate, midpoint)
    resumed["stage_settings"]["tr_start_yr"] = 1
    run_case(binary, output, "cold-resumed", resumed, ["--tr-yrs", "1"])

    old = restart_state(output / "zero-legacy/restart-pr.nc")
    new = restart_state(output / "zero-thermokarst/restart-pr.nc")
    temperature_difference = new["TSsoil"] - old["TSsoil"]
    water_old = np.sum(old["LIQsoil"] + old["ICEsoil"])
    water_new = np.sum(new["LIQsoil"] + new["ICEsoil"])
    zero_metrics = {
        "temperature_rmse_C": float(np.sqrt(np.mean(temperature_difference ** 2))),
        "temperature_max_abs_C": float(np.max(np.abs(temperature_difference))),
        "total_soil_water_relative_difference": float(abs(water_new - water_old) / water_old),
        "layer_thickness_max_abs_m": float(np.max(np.abs(new["DZsoil"] - old["DZsoil"]))),
        "subsidence_m": float(new["TKstate"][1]),
        "remaining_excess_ice_kg_m2": float(np.sum(new["TKexcess"])),
        "frozen_state_exact": bool(np.array_equal(old["FROZENsoil"], new["FROZENsoil"])),
    }

    seed = restart_state(seed_restart)
    middle = restart_state(midpoint)
    final_continuous_path = output / "cold-continuous/restart-tr.nc"
    final_resumed_path = output / "cold-resumed/restart-tr.nc"
    final = restart_state(final_continuous_path)
    resumed_state = restart_state(final_resumed_path)
    left = active_pixel_variables(final_continuous_path)
    right = active_pixel_variables(final_resumed_path)
    exact_variables = all(np.array_equal(left[name], right[name], equal_nan=True)
                          for name in left.keys() & right.keys())
    geometry_error = float(np.max(np.abs(
        final["DZsoil"] - final["TKmatrix"][:final["numsl"]]
        - final["TKexcess"][:final["numsl"]] / 917.0)))
    restart_metrics = {
        "bytewise_identical": final_continuous_path.read_bytes() == final_resumed_path.read_bytes(),
        "active_pixel_variables_exact": bool(exact_variables),
        "continuous_sha256": sha256(final_continuous_path),
        "resumed_sha256": sha256(final_resumed_path),
        "initial_excess_ice_kg_m2": float(np.sum(seed["TKexcess"])),
        "final_excess_ice_kg_m2": float(np.sum(final["TKexcess"])),
        "final_subsidence_m": float(final["TKstate"][1]),
        "maximum_geometry_identity_error_m": geometry_error,
        "final_water_residual_kg_m2": float(final["TKstate"][7]),
        "final_energy_residual_J_m2": float(final["TKstate"][8]),
        "maximum_final_soil_temperature_C": float(np.max(final["TSsoil"])),
        "final_frozen_state_all_one": bool(np.all(final["FROZENsoil"] == 1)),
    }

    checks = []
    def gate(group, name, observed, criterion, passed):
        checks.append({"group": group, "test": name, "observed": observed,
                       "criterion": criterion, "status": "PASS" if passed else "FAIL"})

    gate("zero-excess", "production runs complete", "100/100", "both status=100", True)
    gate("zero-excess", "layer geometry unchanged", zero_metrics["layer_thickness_max_abs_m"],
         "<=1e-12 m", zero_metrics["layer_thickness_max_abs_m"] <= 1e-12)
    gate("zero-excess", "no subsidence", zero_metrics["subsidence_m"],
         "<=1e-12 m", abs(zero_metrics["subsidence_m"]) <= 1e-12)
    gate("zero-excess", "no excess ice", zero_metrics["remaining_excess_ice_kg_m2"],
         "<=1e-12 kg m-2", zero_metrics["remaining_excess_ice_kg_m2"] <= 1e-12)
    gate("zero-excess", "frozen classifications agree", zero_metrics["frozen_state_exact"],
         "exact", zero_metrics["frozen_state_exact"])
    gate("zero-excess", "temperature profile RMSE", zero_metrics["temperature_rmse_C"],
         "<=2 C", zero_metrics["temperature_rmse_C"] <= 2.0)
    gate("zero-excess", "maximum temperature difference", zero_metrics["temperature_max_abs_C"],
         "<=2.5 C", zero_metrics["temperature_max_abs_C"] <= 2.5)
    gate("zero-excess", "total soil water difference", zero_metrics["total_soil_water_relative_difference"],
         "<=2%", zero_metrics["total_soil_water_relative_difference"] <= 0.02)
    gate("restart", "all production runs complete", "100/100/100/100", "all status=100", True)
    gate("restart", "NetCDF files bytewise identical", restart_metrics["bytewise_identical"],
         "exact", restart_metrics["bytewise_identical"])
    gate("restart", "active-pixel restart fields identical", restart_metrics["active_pixel_variables_exact"],
         "exact", restart_metrics["active_pixel_variables_exact"])
    gate("restart", "excess-ice inventory preserved",
         abs(restart_metrics["final_excess_ice_kg_m2"] - restart_metrics["initial_excess_ice_kg_m2"]),
         "<=1e-12 kg m-2", abs(restart_metrics["final_excess_ice_kg_m2"] - restart_metrics["initial_excess_ice_kg_m2"]) <= 1e-12)
    gate("restart", "no cold-column subsidence", restart_metrics["final_subsidence_m"],
         "<=1e-12 m", abs(restart_metrics["final_subsidence_m"]) <= 1e-12)
    gate("restart", "geometry identity", geometry_error, "<=1e-12 m", geometry_error <= 1e-12)
    gate("restart", "water budget residual", abs(restart_metrics["final_water_residual_kg_m2"]),
         "<=1e-7 kg m-2", abs(restart_metrics["final_water_residual_kg_m2"]) <= 1e-7)
    gate("restart", "energy budget residual", abs(restart_metrics["final_energy_residual_J_m2"]),
         "<=1e-3 J m-2", abs(restart_metrics["final_energy_residual_J_m2"]) <= 1e-3)
    gate("restart", "column remains frozen", restart_metrics["maximum_final_soil_temperature_C"],
         "<0 C and all frozen flags=1", restart_metrics["maximum_final_soil_temperature_C"] < 0 and restart_metrics["final_frozen_state_all_one"])

    with (output / "checks.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=checks[0].keys())
        writer.writeheader()
        writer.writerows(checks)
    summary = {"zero_excess": zero_metrics, "restart_equivalence": restart_metrics,
               "checks_passed": sum(x["status"] == "PASS" for x in checks),
               "checks_total": len(checks)}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none"})
    green, gray, black = "#1F6F5F", "#777777", "#111111"
    depth = np.cumsum(old["DZsoil"]) - old["DZsoil"] / 2
    fig, axes = plt.subplots(1, 3, figsize=(8.2, 3.4), layout="constrained")
    axes[0].plot(old["TSsoil"], depth, color=black, linestyle="--", label="Legacy")
    axes[0].plot(new["TSsoil"], depth, color=green, label="Thermokarst, X=0")
    axes[0].invert_yaxis(); axes[0].set(xlabel="Temperature (°C)", ylabel="Depth (m)", title="(a) Final soil temperature")
    axes[0].legend(frameon=False)
    axes[1].plot(temperature_difference, depth, color=green)
    axes[1].axvline(0, color=gray, linewidth=.8)
    axes[1].invert_yaxis(); axes[1].set(xlabel="Thermokarst − legacy (°C)", ylabel="Depth (m)", title="(b) Solver difference")
    axes[2].plot(old["ICEsoil"], depth, color=black, linestyle="--", label="Legacy")
    axes[2].plot(new["ICEsoil"], depth, color=green, label="Thermokarst, X=0")
    axes[2].invert_yaxis(); axes[2].set(xlabel="Layer ice (kg m⁻²)", ylabel="Depth (m)", title="(c) Final pore ice")
    axes[2].legend(frameon=False)
    fig.suptitle("One-year production TEM zero-excess comparison", fontsize=12)
    fig.savefig(output / "zero_excess_comparison.png", dpi=220)
    fig.savefig(output / "zero_excess_comparison.svg")
    plt.close(fig)

    states = [seed, middle, final]
    years = [0, 1, 2]
    fig, axes = plt.subplots(1, 3, figsize=(8.2, 3.4), layout="constrained")
    axes[0].plot(years, [np.sum(x["TKexcess"]) for x in states], "o-", color=green)
    axes[0].set(xlabel="Controlled years after seed", ylabel="Excess ice (kg m⁻²)", title="(a) Frozen inventory")
    axes[1].plot(years, [x["TKstate"][1] for x in states], "o-", color=green)
    axes[1].set(xlabel="Controlled years after seed", ylabel="Subsidence (m)", title="(b) Surface stability")
    for state, label, style in zip(states, ["Seed", "Midpoint", "Final"], [":", "--", "-"]):
        d = np.cumsum(state["DZsoil"]) - state["DZsoil"] / 2
        axes[2].plot(state["TSsoil"], d, color=green if label == "Final" else gray,
                     linestyle=style, label=label)
    axes[2].invert_yaxis(); axes[2].set(xlabel="Temperature (°C)", ylabel="Depth (m)", title="(c) Cold-column profile")
    axes[2].legend(frameon=False)
    fig.suptitle("Production restart path preserves the controlled frozen column", fontsize=12)
    fig.savefig(output / "restart_equivalence.png", dpi=220)
    fig.savefig(output / "restart_equivalence.svg")
    plt.close(fig)

    print(json.dumps(summary, indent=2))
    failed = [item for item in checks if item["status"] != "PASS"]
    if failed:
        raise RuntimeError(f"{len(failed)} production validation checks failed")


if __name__ == "__main__":
    main()
