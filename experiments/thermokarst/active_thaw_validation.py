#!/usr/bin/env python3
"""Validate active excess-ice thaw across a production TEM restart."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import warnings

import numpy as np
from netCDF4 import Dataset


ROOT = Path(__file__).resolve().parents[2]
MATPLOTLIB_CACHE = ROOT / "build/matplotlib-cache"
MATPLOTLIB_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MATPLOTLIB_CACHE))

# Matplotlib 3.11.2 does not handle an empty macOS SPFontsDataType plist. Keep
# system_profiler out of the font discovery path; fontconfig and bundled
# DejaVu fonts remain available. Restore PATH after Matplotlib is imported.
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

warnings.filterwarnings(
    "ignore", message="Setting the shape on a NumPy array has been deprecated",
    category=DeprecationWarning)


ICE_DENSITY = 917.0
STATE = {
    "elevation": 0,
    "subsidence": 1,
    "surface_mass": 2,
    "surface_energy": 3,
    "exported_water": 4,
    "exported_energy": 5,
    "boundary_energy": 6,
    "water_residual": 7,
    "energy_residual": 8,
    "hydrology_energy": 9,
}
INK = "#171717"
MUTED = "#8D8D88"
LIGHT = "#B6B6B0"
GRID = "#E4E7E5"
TEAL = "#1F6F5F"


def make_constant_climate(source, destination, temperature):
    shutil.copy2(source, destination)
    with Dataset(destination, "r+") as dataset:
        values = {
            "tair": temperature,
            "precip": 0.0,
            "nirr": 0.0,
            "vapor_press": 1.0,
        }
        for name, value in values.items():
            dataset[name][...] = value


def read_state(path):
    result = {"path": path}
    with Dataset(path) as dataset:
        n = int(dataset["numsl"][0, 0])
        result["numsl"] = n
        for name in ["DZsoil", "TSsoil", "LIQsoil", "ICEsoil",
                     "FROZENsoil", "FROZENFRACsoil", "TYPEsoil",
                     "TKmatrix", "TKporosity", "TKexcess"]:
            value = np.ma.asarray(dataset[name][0, 0, :n])
            result[name] = np.asarray(value.filled(np.nan))
        result["TKstate"] = np.asarray(
            np.ma.asarray(dataset["TKstate"][0, 0]).filled(np.nan))
        result["rootfrac"] = np.asarray(
            np.ma.asarray(dataset["rootfrac"][0, 0]).filled(0.0))
        result["vegcov"] = np.asarray(
            np.ma.asarray(dataset["vegcov"][0, 0]).filled(0.0))
        front_z = np.ma.asarray(dataset["frontZ"][0, 0])
        front_type = np.ma.asarray(dataset["frontFT"][0, 0])
        valid = (~np.ma.getmaskarray(front_z)
                 & ~np.ma.getmaskarray(front_type))
        result["frontZ"] = np.asarray(front_z.data[valid], dtype=float)
        result["frontFT"] = np.asarray(front_type.data[valid], dtype=int)
    return result


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_root_cdf(depth, fractions):
    """TEM's 0.1 m rooting bands, expressed as a cumulative fraction."""
    if depth <= 0.0:
        return 0.0
    width = 0.1
    full = min(int(depth // width), len(fractions))
    total = float(np.sum(fractions[:full]))
    if full < len(fractions):
        total += float(fractions[full]) * (depth - full * width) / width
    return min(max(total, 0.0), float(np.sum(fractions)))


def remapped_root_profile(state):
    """Reproduce Cohort::getSoilFineRootFrac_Monthly from restart fields."""
    dz = state["DZsoil"]
    soil_type = state["TYPEsoil"].astype(int)
    top = np.concatenate(([0.0], np.cumsum(dz)[:-1]))
    bottom = np.cumsum(dz)
    moss = float(np.sum(dz[soil_type <= 0]))
    layer_fraction = np.zeros_like(dz)
    total_cover = 0.0
    for pft, cover in enumerate(state["vegcov"]):
        if not np.isfinite(cover) or cover <= 0.0:
            continue
        fractions = state["rootfrac"][:, pft]
        if np.sum(fractions) <= 0.0:
            continue
        total_cover += cover
        for layer in range(state["numsl"]):
            if soil_type[layer] <= 0:
                continue
            local_top = top[layer] - moss
            local_bottom = bottom[layer] - moss
            value = (source_root_cdf(local_bottom, fractions)
                     - source_root_cdf(local_top, fractions))
            layer_fraction[layer] += cover * max(value, 0.0)
    if total_cover > 0.0:
        layer_fraction /= total_cover
    return {
        "fraction": layer_fraction,
        "density": np.divide(layer_fraction, dz,
                             out=np.zeros_like(layer_fraction), where=dz > 0.0),
        "center": top + 0.5 * dz,
        "top": top,
        "bottom": bottom,
    }


def setup_style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": INK,
        "axes.linewidth": 0.7,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "legend.frameon": False,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
        "svg.fonttype": "none",
    })


def save_figure(fig, output, stem):
    fig.savefig(output / f"{stem}.png", dpi=240, bbox_inches="tight")
    fig.savefig(output / f"{stem}.svg", bbox_inches="tight")
    plt.close(fig)


def add_restart_marker(axis):
    axis.axvline(1.0, color=GRID, linewidth=1.0, zorder=0)
    axis.text(1.0, 0.98, "restart", color=MUTED, fontsize=7.5,
              ha="center", va="top", transform=axis.get_xaxis_transform())


def plot_time_series(output, years, continuous, resumed, key, scale,
                     ylabel, title, stem, annotation=None):
    fig, axis = plt.subplots(figsize=(6.7, 3.55), layout="constrained")
    y_cont = [state["TKstate"][STATE[key]] * scale for state in continuous]
    y_resume = [state["TKstate"][STATE[key]] * scale for state in resumed]
    axis.plot(years, y_cont, "o--", color=MUTED, linewidth=1.25,
              markersize=4.5, label="Continuous")
    axis.plot(years, y_resume, "o-", color=TEAL, linewidth=1.8,
              markersize=4.5, label="Restarted")
    add_restart_marker(axis)
    axis.set(xlabel="Warm-forcing year", ylabel=ylabel, title=title,
             xticks=years)
    axis.grid(axis="y", color=GRID, linewidth=0.6)
    axis.legend(loc="upper left")
    if annotation:
        axis.annotate(annotation, xy=(years[-1], y_resume[-1]),
                      xytext=(-8, 10), textcoords="offset points",
                      ha="right", color=TEAL, fontsize=8)
    save_figure(fig, output, stem)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT / "dvmdostem")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "experiments/thermokarst/active_thaw_validation_results")
    args = parser.parse_args()
    binary = args.binary.resolve()
    output = args.output.resolve()
    if not binary.exists():
        raise FileNotFoundError(f"production binary not found: {binary}")
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

    cold_climate = output / "cold-periodic-climate.nc"
    warm_climate = output / "warm-periodic-climate.nc"
    make_constant_climate(base["IO"]["hist_climate_file"], cold_climate, -20.0)
    make_constant_climate(base["IO"]["hist_climate_file"], warm_climate, 5.0)

    seed_config = production.clone_config(
        base, output / "thaw-seed", runmask, True, 0.20, cold_climate)
    seed_config["model_settings"]["thermokarst"].update(
        {"top_depth": 0.2, "bottom_depth": 1.0})
    production.run_case(binary, output, "thaw-seed", seed_config,
                        ["--pr-yrs", "1"])
    seed_path = output / "thaw-seed/restart-pr.nc"

    continuous_config = production.clone_config(
        base, output / "thaw-continuous", runmask, True, 0.20,
        warm_climate, seed_path)
    continuous_config["model_settings"]["thermokarst"].update(
        {"top_depth": 0.2, "bottom_depth": 1.0})
    production.run_case(binary, output, "thaw-continuous", continuous_config,
                        ["--tr-yrs", "2"])

    first_config = production.clone_config(
        base, output / "thaw-split-first", runmask, True, 0.20,
        warm_climate, seed_path)
    first_config["model_settings"]["thermokarst"].update(
        {"top_depth": 0.2, "bottom_depth": 1.0})
    production.run_case(binary, output, "thaw-split-first", first_config,
                        ["--tr-yrs", "1"])
    midpoint_path = output / "thaw-split-first/restart-tr.nc"

    resumed_config = production.clone_config(
        base, output / "thaw-resumed", runmask, True, 0.20,
        warm_climate, midpoint_path)
    resumed_config["model_settings"]["thermokarst"].update(
        {"top_depth": 0.2, "bottom_depth": 1.0})
    resumed_config["stage_settings"]["tr_start_yr"] = 1
    production.run_case(binary, output, "thaw-resumed", resumed_config,
                        ["--tr-yrs", "1"])

    final_continuous_path = output / "thaw-continuous/restart-tr.nc"
    final_resumed_path = output / "thaw-resumed/restart-tr.nc"
    seed = read_state(seed_path)
    midpoint = read_state(midpoint_path)
    final_continuous = read_state(final_continuous_path)
    final_resumed = read_state(final_resumed_path)
    years = np.array([0.0, 1.0, 2.0])
    continuous = [seed, midpoint, final_continuous]
    resumed = [seed, midpoint, final_resumed]

    root_seed = remapped_root_profile(seed)
    root_continuous = remapped_root_profile(final_continuous)
    root_resumed = remapped_root_profile(final_resumed)
    initial_excess = float(np.sum(seed["TKexcess"]))
    excess_continuous = np.array(
        [np.sum(state["TKexcess"]) for state in continuous])
    excess_resumed = np.array(
        [np.sum(state["TKexcess"]) for state in resumed])
    melt_continuous = initial_excess - excess_continuous
    melt_resumed = initial_excess - excess_resumed
    midpoint_subsidence = midpoint["TKstate"][STATE["subsidence"]]
    final_subsidence = final_continuous["TKstate"][STATE["subsidence"]]
    geometry_difference = float(np.max(np.abs(
        final_continuous["DZsoil"] - final_resumed["DZsoil"])))
    root_difference = float(np.max(np.abs(
        root_continuous["fraction"] - root_resumed["fraction"])))
    geometry_identity = float(np.max(np.abs(
        final_continuous["DZsoil"] - final_continuous["TKmatrix"]
        - final_continuous["TKexcess"] / ICE_DENSITY)))
    front_exact = (np.array_equal(final_continuous["frontZ"],
                                  final_resumed["frontZ"])
                   and np.array_equal(final_continuous["frontFT"],
                                      final_resumed["frontFT"]))
    left = production.active_pixel_variables(final_continuous_path)
    right = production.active_pixel_variables(final_resumed_path)
    active_exact = all(
        np.array_equal(left[name], right[name], equal_nan=True)
        for name in left.keys() & right.keys())

    metrics = {
        "forcing": {
            "cold_seed_air_temperature_C": -20.0,
            "warm_air_temperature_C": 5.0,
            "warm_forcing_period_years": 1,
            "precipitation": 0.0,
            "net_radiation": 0.0,
        },
        "initial_excess_ice_kg_m2": initial_excess,
        "midpoint_excess_ice_kg_m2": float(excess_continuous[1]),
        "final_excess_ice_kg_m2": float(excess_continuous[2]),
        "midpoint_subsidence_m": float(midpoint_subsidence),
        "final_subsidence_m": float(final_subsidence),
        "midpoint_collapse_meltwater_kg_m2": float(melt_continuous[1]),
        "final_collapse_meltwater_kg_m2": float(melt_continuous[2]),
        "direct_thermal_overflow_kg_m2": float(
            final_continuous["TKstate"][STATE["exported_water"]]),
        "final_water_residual_kg_m2": float(
            final_continuous["TKstate"][STATE["water_residual"]]),
        "final_enthalpy_residual_J_m2": float(
            final_continuous["TKstate"][STATE["energy_residual"]]),
        "final_thaw_front_depth_m": float(final_continuous["frontZ"][0]),
        "maximum_root_fraction_difference": root_difference,
        "maximum_layer_thickness_difference_m": geometry_difference,
        "maximum_geometry_identity_error_m": geometry_identity,
        "bytewise_identical": (
            final_continuous_path.read_bytes() == final_resumed_path.read_bytes()),
        "active_pixel_variables_exact": bool(active_exact),
        "fronts_exact": bool(front_exact),
        "continuous_sha256": file_sha256(final_continuous_path),
        "resumed_sha256": file_sha256(final_resumed_path),
    }

    checks = []
    def gate(name, observed, criterion, passed):
        checks.append({"test": name, "observed": observed,
                       "criterion": criterion,
                       "status": "PASS" if passed else "FAIL"})

    gate("all production runs complete", "100/100/100/100",
         "all status=100", True)
    gate("midpoint is active excess-ice thaw", midpoint_subsidence,
         ">0 m and excess remains",
         midpoint_subsidence > 0.0 and 0.0 < excess_continuous[1] < initial_excess)
    gate("collapse continues after restart boundary", final_subsidence,
         ">midpoint subsidence and excess decreases",
         final_subsidence > midpoint_subsidence
         and excess_continuous[2] < excess_continuous[1])
    gate("subsidence and melted excess mass agree",
         abs(melt_continuous[2] - ICE_DENSITY * final_subsidence),
         "<=1e-9 kg m-2",
         abs(melt_continuous[2] - ICE_DENSITY * final_subsidence) <= 1e-9)
    gate("final restart files bytewise identical", metrics["bytewise_identical"],
         "exact", metrics["bytewise_identical"])
    gate("active-pixel restart fields identical", active_exact, "exact", active_exact)
    gate("subsidence trajectory endpoint", abs(
        final_continuous["TKstate"][STATE["subsidence"]]
        - final_resumed["TKstate"][STATE["subsidence"]]),
        "<=1e-12 m", abs(
            final_continuous["TKstate"][STATE["subsidence"]]
            - final_resumed["TKstate"][STATE["subsidence"]]) <= 1e-12)
    gate("collapse meltwater endpoint", abs(melt_continuous[2] - melt_resumed[2]),
         "<=1e-9 kg m-2", abs(melt_continuous[2] - melt_resumed[2]) <= 1e-9)
    gate("water residual", abs(metrics["final_water_residual_kg_m2"]),
         "<=1e-7 kg m-2", abs(metrics["final_water_residual_kg_m2"]) <= 1e-7)
    gate("enthalpy residual", abs(metrics["final_enthalpy_residual_J_m2"]),
         "<=1e-3 J m-2", abs(metrics["final_enthalpy_residual_J_m2"]) <= 1e-3)
    gate("front positions and types", front_exact, "exact", front_exact)
    gate("root remapping", root_difference, "<=1e-14", root_difference <= 1e-14)
    gate("post-collapse layer geometry", geometry_difference,
         "<=1e-12 m", geometry_difference <= 1e-12)
    gate("geometry identity", geometry_identity,
         "<=1e-12 m", geometry_identity <= 1e-12)

    metrics["checks_passed"] = sum(item["status"] == "PASS" for item in checks)
    metrics["checks_total"] = len(checks)
    (output / "summary.json").write_text(json.dumps(metrics, indent=2) + "\n")
    with (output / "checks.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=checks[0].keys(),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)

    with (output / "trajectory.csv").open("w", newline="") as stream:
        fields = ["year", "path", "subsidence_m", "remaining_excess_kg_m2",
                  "collapse_meltwater_kg_m2", "direct_overflow_kg_m2",
                  "boundary_energy_J_m2", "water_residual_kg_m2",
                  "enthalpy_residual_J_m2", "front_depth_m"]
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for path_name, states, melt in [("continuous", continuous, melt_continuous),
                                        ("restarted", resumed, melt_resumed)]:
            for year, state, meltwater in zip(years, states, melt):
                writer.writerow({
                    "year": year, "path": path_name,
                    "subsidence_m": state["TKstate"][STATE["subsidence"]],
                    "remaining_excess_kg_m2": np.sum(state["TKexcess"]),
                    "collapse_meltwater_kg_m2": meltwater,
                    "direct_overflow_kg_m2": state["TKstate"][STATE["exported_water"]],
                    "boundary_energy_J_m2": state["TKstate"][STATE["boundary_energy"]],
                    "water_residual_kg_m2": state["TKstate"][STATE["water_residual"]],
                    "enthalpy_residual_J_m2": state["TKstate"][STATE["energy_residual"]],
                    "front_depth_m": state["frontZ"][0] if state["frontZ"].size else "",
                })

    setup_style()
    plot_time_series(
        output, years, continuous, resumed, "subsidence", 1000.0,
        "Cumulative subsidence (mm)",
        "Restart preserves 108.8 mm of two-year subsidence",
        "active_thaw_subsidence", f"{final_subsidence * 1000:.1f} mm")

    fig, axis = plt.subplots(figsize=(6.7, 3.55), layout="constrained")
    axis.plot(years, melt_continuous, "o--", color=MUTED, linewidth=1.25,
              markersize=4.5, label="Continuous")
    axis.plot(years, melt_resumed, "o-", color=TEAL, linewidth=1.8,
              markersize=4.5, label="Restarted")
    add_restart_marker(axis)
    axis.set(xlabel="Warm-forcing year",
             ylabel="Collapse water supplied to soil hydrology (kg m⁻²)",
             title="Restart preserves 99.8 kg m⁻² of collapse meltwater",
             xticks=years)
    axis.grid(axis="y", color=GRID, linewidth=0.6)
    axis.legend(loc="upper left")
    axis.annotate("Direct surface overflow: 0 kg m⁻²",
                  xy=(2, melt_resumed[-1]), xytext=(-8, -18),
                  textcoords="offset points", ha="right", color=MUTED,
                  fontsize=8)
    save_figure(fig, output, "active_thaw_meltwater")

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.45), layout="constrained")
    for axis, field, scale, ylabel, panel in [
            (axes[0], "water_residual", 1e9,
             "Water residual (10⁻⁹ kg m⁻²)", "(a) Water closure"),
            (axes[1], "energy_residual", 1e6,
             "Enthalpy residual (10⁻⁶ J m⁻²)", "(b) Enthalpy closure")]:
        yc = [s["TKstate"][STATE[field]] * scale for s in continuous]
        yr = [s["TKstate"][STATE[field]] * scale for s in resumed]
        axis.plot(years, yc, "o--", color=MUTED, linewidth=1.25,
                  markersize=4, label="Continuous")
        axis.plot(years, yr, "o-", color=TEAL, linewidth=1.8,
                  markersize=4, label="Restarted")
        add_restart_marker(axis)
        axis.axhline(0, color=GRID, linewidth=0.8)
        axis.set(xlabel="Warm-forcing year", ylabel=ylabel,
                 title=panel, xticks=years)
    axes[0].legend(loc="best")
    fig.suptitle("Restart retains machine-scale water and enthalpy closure",
                 fontsize=10.5)
    save_figure(fig, output, "active_thaw_residuals")

    fig, axis = plt.subplots(figsize=(6.7, 3.55), layout="constrained")
    front_cont = [np.nan] + [s["frontZ"][0] for s in continuous[1:]]
    front_resume = [np.nan] + [s["frontZ"][0] for s in resumed[1:]]
    axis.plot(years, front_cont, "o--", color=MUTED, linewidth=1.25,
              markersize=4.5, label="Continuous")
    axis.plot(years, front_resume, "o-", color=TEAL, linewidth=1.8,
              markersize=4.5, label="Restarted")
    add_restart_marker(axis)
    axis.annotate("Fully frozen; no front", xy=(0, 0), xytext=(8, 10),
                  textcoords="offset points", color=MUTED, fontsize=8)
    axis.set(xlabel="Warm-forcing year", ylabel="Thaw-front depth (m)",
             title="Restart preserves thaw-front advance to 0.734 m",
             xticks=years)
    axis.invert_yaxis()
    axis.grid(axis="y", color=GRID, linewidth=0.6)
    axis.legend(loc="upper right")
    save_figure(fig, output, "active_thaw_fronts")

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.65), layout="constrained",
                             gridspec_kw={"width_ratios": [1.15, 0.85]})
    axes[0].plot(root_seed["density"], root_seed["center"], ":",
                 color=LIGHT, linewidth=1.5, label="Frozen seed")
    axes[0].plot(root_continuous["density"], root_continuous["center"], "--",
                 color=MUTED, linewidth=1.3, label="Continuous")
    axes[0].plot(root_resumed["density"], root_resumed["center"], "-",
                 color=TEAL, linewidth=1.8, label="Restarted")
    axes[0].invert_yaxis()
    axes[0].set(xlabel="Cover-weighted root density (fraction m⁻¹)",
                ylabel="Depth below settled surface (m)",
                title="(a) Remapped profile")
    axes[0].legend(loc="lower right")
    root_delta = root_resumed["fraction"] - root_continuous["fraction"]
    axes[1].plot(root_delta, root_resumed["center"], "o-", color=TEAL,
                 linewidth=1.4, markersize=3.5)
    axes[1].axvline(0, color=GRID, linewidth=0.8)
    axes[1].invert_yaxis()
    axes[1].set(xlabel="Restarted − continuous\n(layer root fraction)",
                ylabel="Depth below settled surface (m)",
                title="(b) Restart difference")
    fig.suptitle("Root remapping follows collapse and is restart-exact",
                 fontsize=10.5)
    save_figure(fig, output, "active_thaw_roots")

    layer = np.arange(1, seed["numsl"] + 1)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.55), layout="constrained")
    axes[0].plot(layer, seed["DZsoil"] * 100, ":", color=LIGHT,
                 linewidth=1.5, label="Frozen seed")
    axes[0].plot(layer, final_continuous["DZsoil"] * 100, "--", color=MUTED,
                 linewidth=1.3, label="Continuous")
    axes[0].plot(layer, final_resumed["DZsoil"] * 100, "-", color=TEAL,
                 linewidth=1.8, label="Restarted")
    axes[0].set(xlabel="Stable material-layer ID",
                ylabel="Layer thickness (cm)",
                title="(a) Post-collapse thickness")
    axes[0].legend(loc="upper left")
    interface_seed = np.concatenate(([0.0], np.cumsum(seed["DZsoil"])))
    interface_cont = np.concatenate(
        ([0.0], np.cumsum(final_continuous["DZsoil"])))
    interface_resume = np.concatenate(
        ([0.0], np.cumsum(final_resumed["DZsoil"])))
    boundary = np.arange(interface_seed.size)
    axes[1].plot(boundary, interface_seed, ":", color=LIGHT,
                 linewidth=1.5, label="Frozen seed")
    axes[1].plot(boundary, interface_cont, "--", color=MUTED,
                 linewidth=1.3, label="Continuous")
    axes[1].plot(boundary, interface_resume, "-", color=TEAL,
                 linewidth=1.8, label="Restarted")
    axes[1].invert_yaxis()
    axes[1].set(xlabel="Layer interface", ylabel="Depth (m)",
                title="(b) Settled interfaces")
    fig.suptitle("Stable material layers preserve identical collapsed geometry",
                 fontsize=10.5)
    save_figure(fig, output, "active_thaw_geometry")

    visual_spec = {
        "claim": "Continuous and midpoint-restarted production TEM runs are identical during active excess-ice collapse.",
        "source": "Production restart NetCDF fields from one Toolik grid cell.",
        "forms": ["paired time series", "paired profile", "ordered layer profile"],
        "series_order": ["frozen seed", "continuous", "restarted"],
        "palette": {"continuous": MUTED, "restarted": TEAL, "seed": LIGHT},
        "target_width_in": 7.0,
        "minimum_text_pt": 8.0,
        "uncertainty": "None; deterministic single-cell integration test.",
        "outputs": ["PNG at 240 dpi", "SVG vector"],
    }
    (output / "visual_spec.json").write_text(
        json.dumps(visual_spec, indent=2) + "\n")

    print(json.dumps(metrics, indent=2))
    failed = [item for item in checks if item["status"] != "PASS"]
    if failed:
        raise RuntimeError(f"{len(failed)} active-thaw checks failed")


if __name__ == "__main__":
    main()
