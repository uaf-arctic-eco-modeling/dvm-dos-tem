#!/usr/bin/env python3
"""Multi-year observed climate, mapped fire severity, dsl, and unified ponding."""
import argparse, csv, json, os, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from netCDF4 import Dataset

ROOT = Path(__file__).resolve().parents[2]
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

CELLS = bgc.CELLS
CMTS = bgc.CMTS
ICE = 917.0
FIRE_JDAY = 180
YEARS = 5
SPLIT = 3
SEVERITY_BY_CMT = {4: 3, 5: 4}
DEPTHS = (0.0, 0.5, 1.0)
DINM = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
INK = "#171717"
TEAL = "#1F6F5F"
BLUE = "#4C78A8"
ORANGE = "#D55E00"
MUTED = "#777772"
GRID = "#E4E7E5"
FIRE_RELEASED_WATER = 15
FIRE_EXPORTED_ENERGY = 16
FIRE_MATRIX_LOSS = 17
FIRE_ROUTED_LIQUID = 18


def climate_stats(path, years):
    with Dataset(path) as src:
        tair = np.asarray(src["tair"][:years * 12, 0, 0], float)
        precip = np.asarray(src["precip"][:years * 12, 0, 0], float)
    monthly = tair.reshape(years, 12)
    return {
        "years": years,
        "annual_mean_tair_C": [float(x) for x in monthly.mean(axis=1)],
        "june_C": [float(monthly[y, 5]) for y in range(years)],
        "july_C": [float(monthly[y, 6]) for y in range(years)],
        "annual_precip_mm": [float(precip[y * 12:(y + 1) * 12].sum())
                             for y in range(years)],
        "year_to_year_tair_range_C": float(np.ptp(monthly.mean(axis=1))),
    }


def select_observed_climate(source, dest, nyears):
    """Copy a consecutive observed window that contains the warmest June+July."""
    with Dataset(source) as src:
        n = int(src["tair"].shape[0] // 12)
        tair = np.asarray(src["tair"][:n * 12, 0, 0], float).reshape(n, 12)
        score = tair[:, 5] + tair[:, 6]
        warm = int(np.argmax(score))
        start = int(np.clip(warm - 1, 0, n - nyears))
        fire_year = warm - start
        if fire_year > nyears - 2:
            start = max(0, warm - (nyears - 2))
            fire_year = min(warm - start, nyears - 2)
        sl = slice(start * 12, (start + nyears) * 12)
        window = {name: np.asarray(src[name][sl]) for name in
                  ["tair", "precip", "nirr", "vapor_press", "time"]}
    shutil.copy2(source, dest)
    with Dataset(dest, "r+") as dst:
        for name, data in window.items():
            dst[name][:nyears * 12] = data
    return {"source_start_year": start, "fire_year_index": fire_year,
            "warmest_source_year": warm}


def mapped_severity(veg_file):
    with Dataset(veg_file) as dataset:
        veg = np.asarray(dataset["veg_class"][:], int)
    severity = np.zeros_like(veg)
    for cmt, value in SEVERITY_BY_CMT.items():
        severity[veg == cmt] = value
    return severity, veg


def make_fire(source, dest, veg_file, event_year=None):
    shutil.copy2(source, dest)
    severity_map, veg = mapped_severity(veg_file)
    with Dataset(dest, "r+") as dataset:
        for name in ["exp_burn_mask", "exp_jday_of_burn",
                     "exp_fire_severity", "exp_area_of_burn"]:
            dataset[name][:] = 0
        if event_year is not None:
            dataset["exp_fire_severity"][event_year] = severity_map
            ny, nx = severity_map.shape
            for y in range(ny):
                for x in range(nx):
                    if severity_map[y, x] > 0:
                        dataset["exp_burn_mask"][event_year, y, x] = 1
                        dataset["exp_jday_of_burn"][event_year, y, x] = FIRE_JDAY
                        dataset["exp_area_of_burn"][event_year, y, x] = 1000000
    return {
        "severity_map": {str((y, x)): int(severity_map[y, x]) for y, x in CELLS},
        "veg_class": {str((y, x)): int(veg[y, x]) for y, x in CELLS},
    }


def make_spec(source, dest):
    rows = list(csv.DictReader(source.open()))
    extra_daily = set(bgc.TK) | {"SNOWTHICK", "TKPOND", "TKSURFICE"}
    extra_yearly = set(bgc.BGC)
    extra_monthly = {"BURNTHICK", "BURNSOIL2AIRC", "BURNSOIL2AIRN",
                     "TLAYER", "LAYERDEPTH", "LAYERDZ",
                     "TSOIL_30cm", "TSOIL_100cm"}
    extra_layers = {"TLAYER", "LAYERDEPTH", "LAYERDZ"}
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
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def config(base, directory, restart, fire_file, output=True, tr_start=0):
    cfg = bgc.config(base, directory, restart, dsl=True, output=output, tr_start=tr_start)
    cfg["IO"]["hist_exp_fire_file"] = str(fire_file)
    for stage in ["tr", "sc"]:
        cfg["stage_settings"][stage]["dsb"] = True
    return cfg


def save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=240, bbox_inches="tight")
    fig.savefig(out / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def remaining_excess(initial, subsidence, day):
    melted = ICE * np.asarray(subsidence[day], float)
    return {str(cell): float(initial[str(cell)] - melted[cell]) for cell in CELLS}


def monthly(directory, name):
    return fire_topo.monthly(directory, name)


def carbon_yearly(directory, name):
    path = directory / f"{name}_yearly_tr.nc"
    if path.exists():
        return bgc.read_yearly(directory, name)
    m = monthly(directory, name)
    nyears = m.shape[0] // 12
    return m.reshape(nyears, 12, *m.shape[1:]).sum(axis=1)


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
    series = {z0: np.zeros((months,) + tlayer.shape[2:]) for z0 in DEPTHS}
    original = {z0: np.zeros((months,) + tlayer.shape[2:]) for z0 in DEPTHS}
    for t in range(months):
        for y, x in CELLS:
            current = interpolate_profile(
                tlayer[t, :, y, x], z[t, :, y, x], dz[t, :, y, x], DEPTHS)
            s = float(sub_month[t, y, x])
            orig_depths = tuple(max(0., d - s) for d in DEPTHS)
            shifted = interpolate_profile(
                tlayer[t, :, y, x], z[t, :, y, x], dz[t, :, y, x], orig_depths)
            for z0, zo in zip(DEPTHS, orig_depths):
                series[z0][t, y, x] = current[z0]
                original[z0][t, y, x] = shifted[zo]
    return series, original, sub_month


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT / "dvmdostem")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "experiments/thermokarst/observed_fire_validation_results")
    parser.add_argument("--reuse", action="store_true")
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() and not args.reuse:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    probe = fire_topo.compile_probe(out)
    base = production.parse_json_with_comments(ROOT / "config/config.js")
    bgc.absolute_io(base)
    bgc.copy_spatial(base, out)
    climate = Path(base["IO"]["hist_climate_file"])
    observed = out / "observed-multi-year-climate.nc"
    climate_window = select_observed_climate(climate, observed, YEARS)
    fire_year = climate_window["fire_year_index"]
    fire_day = fire_year * 365 + FIRE_JDAY - 1
    base["IO"]["hist_climate_file"] = str(observed)
    weather = climate_stats(observed, YEARS)
    weather.update(climate_window)
    spec = out / "observed-fire-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec)
    base["IO"]["output_spec_file"] = str(spec)

    veg = Path(base["IO"]["veg_class_file"])
    source_fire = Path(base["IO"]["hist_exp_fire_file"])
    fire_on = out / "mapped-fire.nc"
    fire_off = out / "no-fire.nc"
    fire_map = make_fire(source_fire, fire_on, veg, fire_year)
    make_fire(source_fire, fire_off, veg)

    statuses = {}
    statuses["initialization"] = bgc.completed(out, "initialization") if args.reuse else None
    if statuses["initialization"] is None:
        statuses["initialization"] = bgc.run(
            args.binary.resolve(), out, "initialization",
            bgc.config(base, out / "initialization", output=False),
            ["--pr-yrs", "1", "--eq-yrs", "5"])
    initial = out / "initialization/restart-eq.nc"
    injected = out / "restart-with-excess.nc"
    added = bgc.inject_excess(initial, injected, fraction=.2, top=.05, bottom=1.5)

    for name, restart, fire, years in [
            ("control", injected, fire_off, YEARS),
            ("continuous", injected, fire_on, YEARS),
            ("split-first", injected, fire_on, SPLIT)]:
        statuses[name] = bgc.completed(out, name) if args.reuse else None
        if statuses[name] is None:
            statuses[name] = bgc.run(
                args.binary.resolve(), out, name,
                config(base, out / name, restart, fire),
                ["--tr-yrs", str(years)])
    statuses["resumed"] = bgc.completed(out, "resumed") if args.reuse else None
    if statuses["resumed"] is None:
        statuses["resumed"] = bgc.run(
            args.binary.resolve(), out, "resumed",
            config(base, out / "resumed",
                   out / "split-first/restart-tr.nc", fire_on, tr_start=SPLIT),
            ["--tr-yrs", str(YEARS - SPLIT)])

    burn = monthly(out / "continuous", "BURNTHICK")
    soilc = monthly(out / "continuous", "BURNSOIL2AIRC")
    sub_fire = bgc.read_daily(out / "continuous", "TKSUBSIDENCE")
    sub_ctl = bgc.read_daily(out / "control", "TKSUBSIDENCE")
    pond_fire = bgc.read_daily(out / "continuous", "TKPOND")
    pond_ctl = bgc.read_daily(out / "control", "TKPOND")
    ice_fire = bgc.read_daily(out / "continuous", "TKSURFICE")
    yearly = {
        case: {name: carbon_yearly(out / case, name)
               for name in ["GPP", "NPP", "RHSOM", "RHDWD", "SOC", "VEGC"]}
        for case in ["control", "continuous"]
    }
    t_fire, t_fire_orig, _ = temperature_series(out / "continuous", sub_fire)
    t_ctl, t_ctl_orig, _ = temperature_series(out / "control", sub_ctl)

    first = {name: bgc.read_daily(out / "split-first", name) for name in bgc.TK}
    second = {name: bgc.read_daily(out / "resumed", name) for name in bgc.TK}
    resumed_daily = {name: np.concatenate([first[name], second[name]], axis=0)
                     for name in bgc.TK}

    fire_month = fire_year * 12 + 5
    after_month = -1
    cells = []
    inventory_relative = 0.
    final_c = out / "continuous/restart-tr.nc"
    final_r = out / "resumed/restart-tr.nc"
    physical = ["TKmatrix", "TKporosity", "TKexcess", "DZsoil"]
    diffs = {
        name: max(bgc.maxdiff(fire_topo.restart(final_c, name, cell),
                              fire_topo.restart(final_r, name, cell))
                  for cell in CELLS)
        for name in physical + ["TSsoil"]
    }
    for cell, cmt in zip(CELLS, CMTS):
        y, x = cell
        state = fire_topo.restart(final_c, "TKstate", cell)
        after_fire = bgc.inventory(final_c, cell)
        after_ctl = bgc.inventory(out / "control/restart-tr.nc", cell)
        t_before = {z: float(t_fire[z][fire_month, y, x]) for z in DEPTHS}
        t_after = {z: float(t_fire[z][after_month, y, x]) for z in DEPTHS}
        t_before_orig = {z: float(t_fire_orig[z][fire_month, y, x]) for z in DEPTHS}
        t_after_orig = {z: float(t_fire_orig[z][after_month, y, x]) for z in DEPTHS}
        cells.append({
            "cmt": cmt,
            "severity": fire_map["severity_map"][str(cell)],
            "burn_depth_m": float(np.sum(burn[:, y, x])),
            "burned_soil_c_g_m2": float(np.sum(soilc[:, y, x])),
            "released_water_kg_m2": float(state[FIRE_RELEASED_WATER]),
            "routed_liquid_kg_m2": float(state[FIRE_ROUTED_LIQUID]),
            "max_pond_mm": float(np.nanmax(pond_fire[:, y, x])),
            "max_control_pond_mm": float(np.nanmax(pond_ctl[:, y, x])),
            "max_surface_ice_kg_m2": float(np.nanmax(ice_fire[:, y, x])),
            "initial_excess_kg_m2": added[str(cell)],
            "excess_at_fire_kg_m2": remaining_excess(added, sub_fire, fire_day)[str(cell)],
            "thawed_before_fire_kg_m2": float(ICE * sub_fire[fire_day][cell]),
            "final_subsidence_m": float(sub_fire[-1, y, x]),
            "control_subsidence_m": float(sub_ctl[-1, y, x]),
            "final_layers": after_fire["layers"],
            "initial_layers": bgc.inventory(injected, cell)["layers"],
            "final_fire_SOC_g_m2": after_fire["SOC"],
            "final_control_SOC_g_m2": after_ctl["SOC"],
            "final_fire_VEGC_g_m2": after_fire["VEGC"],
            "final_control_VEGC_g_m2": after_ctl["VEGC"],
            "temperature_before_C": t_before,
            "temperature_after_C": t_after,
            "temperature_before_original_surface_C": t_before_orig,
            "temperature_after_original_surface_C": t_after_orig,
            "rhsom_fire_g_m2": float(np.sum(yearly["continuous"]["RHSOM"][:, y, x])),
            "rhsom_control_g_m2": float(np.sum(yearly["control"]["RHSOM"][:, y, x])),
        })
        ia = bgc.inventory(final_c, cell)
        ib = bgc.inventory(final_r, cell)
        for name in ["C", "N"]:
            inventory_relative = max(
                inventory_relative,
                abs(ia[name] - ib[name]) / max(abs(ia[name]), 1.))

    sub_resume_diff = max(
        bgc.maxdiff(sub_fire[:, y, x], resumed_daily["TKSUBSIDENCE"][:, y, x])
        for y, x in CELLS)
    sub_end_diff = max(
        abs(float(sub_fire[-1, y, x]) - float(resumed_daily["TKSUBSIDENCE"][-1, y, x]))
        for y, x in CELLS)
    veg_loss = [
        float(yearly["control"]["VEGC"][fire_year, y, x]
              - yearly["continuous"]["VEGC"][fire_year, y, x])
        for y, x in CELLS
    ]

    checks = []
    def gate(test, observed, criterion, ok):
        checks.append({"test": test, "observed": observed,
                       "criterion": criterion,
                       "status": "PASS" if ok else "FAIL"})

    gate("synthetic fire water closure", abs(probe["water_residual_kg_m2"]),
         "<=1e-12 kg m-2", abs(probe["water_residual_kg_m2"]) <= 1e-12)
    gate("synthetic fire energy closure", abs(probe["energy_residual_J_m2"]),
         "<=1e-6 J m-2", abs(probe["energy_residual_J_m2"]) <= 1e-6)
    gate("production completion", statuses, "all cells status 100",
         all(v == [100, 100] for v in statuses.values()))
    gate("multi-year observed climate", weather["year_to_year_tair_range_C"],
         "annual mean tair differs among years",
         weather["year_to_year_tair_range_C"] > 0.05)
    gate("mapped burn severity", [x["severity"] for x in cells],
         "CMT04=3 and CMT05=4 from the vegetation map",
         [x["severity"] for x in cells] == [3, 4])
    gate("dynamic soil through recovery",
         [x["final_layers"] for x in cells], "dsl enabled; finite layers",
         all(x["final_layers"] >= 1 for x in cells))
    gate("fire during thaw with remaining excess",
         [x["excess_at_fire_kg_m2"] for x in cells],
         "remaining excess >0 and some thaw by fire",
         all(x["excess_at_fire_kg_m2"] > 0 and x["thawed_before_fire_kg_m2"] > 1e-6
             for x in cells))
    gate("nonzero explicit fire", [x["burn_depth_m"] for x in cells],
         ">0 m in each CMT", all(x["burn_depth_m"] > 0 for x in cells))
    gate("overnight surface ponding", [x["max_pond_mm"] for x in cells],
         ">0 mm liquid pond in at least one cell",
         any(x["max_pond_mm"] > 0 for x in cells))
    gate("soil temperature at 0, 0.5, and 1 m",
         [x["temperature_before_C"] for x in cells],
         "finite before and after subsidence",
         all(np.all(np.isfinite(list(x["temperature_before_C"].values())
                                + list(x["temperature_after_C"].values())))
             for x in cells))
    gate("heterotrophic respiration",
         [x["rhsom_fire_g_m2"] for x in cells], "finite and >0",
         all(np.isfinite(x["rhsom_fire_g_m2"]) and x["rhsom_fire_g_m2"] > 0
             for x in cells))
    gate("vegetation mortality in fire year", veg_loss,
         ">0 g C m-2 relative to unburned control",
         all(v > 0 for v in veg_loss))
    gate("restart geometry",
         max(diffs[n] for n in physical), "<=1e-3 m with dsl",
         max(diffs[n] for n in physical) <= 1e-3)
    gate("restart ecosystem C/N inventory", inventory_relative,
         "<=5e-3 relative after a post-fire midpoint restart",
         inventory_relative <= 5e-3)
    gate("restart subsidence trajectory",
         {"daily_max_m": sub_resume_diff, "endpoint_m": sub_end_diff},
         "endpoint <=1e-12 m; daily <=5e-4 m with dsl and remaining excess",
         sub_end_diff <= 1e-12 and sub_resume_diff <= 5e-4)

    summary = {
        "weather": weather,
        "fire": {"year_index": fire_year, "jday": FIRE_JDAY,
                 "map": fire_map},
        "probe": probe,
        "statuses": statuses,
        "cells": cells,
        "vegetation_mortality_g_m2": veg_loss,
        "restart_max_difference": diffs,
        "restart_inventory_relative_difference": inventory_relative,
        "restart_subsidence_difference_m": sub_resume_diff,
        "restart_subsidence_endpoint_difference_m": sub_end_diff,
        "checks_passed": sum(x["status"] == "PASS" for x in checks),
        "checks_total": len(checks),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (out / "checks.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=checks[0].keys(),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 10,
        "axes.labelsize": 9, "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "svg.fonttype": "none",
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })
    months = np.arange(t_fire[0.0].shape[0]) / 12.0
    days = np.arange(sub_fire.shape[0]) / 365.0
    fire_line = fire_year + (FIRE_JDAY - 1) / 365.0

    fig, axes = plt.subplots(2, 1, figsize=(7.4, 5.8), sharex=True,
                             layout="constrained")
    styles = {0.0: ("-", "0 m"), 0.5: ("--", "0.5 m"), 1.0: (":", "1 m")}
    for ax, cell, cmt in zip(axes, CELLS, CMTS):
        y, x = cell
        for z0, (ls, label) in styles.items():
            ax.plot(months, t_ctl[z0][:, y, x], ls, color=MUTED, lw=1.1)
            ax.plot(months, t_fire[z0][:, y, x], ls, color=TEAL if cmt == 4 else BLUE,
                    lw=1.6, label=label)
        ax.axvline(fire_line, color=ORANGE, lw=1.0, ls=":")
        ax.set_ylabel("Soil temperature (°C)")
        ax.set_title(f"CMT{cmt:02d}: T at 0, 0.5, and 1 m below the current surface")
        ax.grid(axis="y", color=GRID, lw=.6)
        ax.legend(loc="lower left")
    axes[-1].set_xlabel("Transition year")
    save(fig, out, "observed-fire-soil-temperature")

    fig, axes = plt.subplots(2, 1, figsize=(7.4, 5.8), sharex=True,
                             layout="constrained")
    for ax, cell, cmt in zip(axes, CELLS, CMTS):
        y, x = cell
        for z0, (ls, label) in styles.items():
            ax.plot(months, t_fire_orig[z0][:, y, x], ls,
                    color=TEAL if cmt == 4 else BLUE, lw=1.6, label=label)
        ax.axvline(fire_line, color=ORANGE, lw=1.0, ls=":")
        ax.set_ylabel("Soil temperature (°C)")
        ax.set_title(f"CMT{cmt:02d}: T at original 0, 0.5, and 1 m after subsidence")
        ax.grid(axis="y", color=GRID, lw=.6)
        ax.legend(loc="lower left")
    axes[-1].set_xlabel("Transition year")
    save(fig, out, "observed-fire-temperature-original-depth")

    fig, axes = plt.subplots(2, 1, figsize=(7.4, 5.4), sharex=True,
                             layout="constrained")
    for ax, cell, cmt, color in zip(axes, CELLS, CMTS, [TEAL, BLUE]):
        y, x = cell
        ax.plot(days, pond_ctl[:, y, x], "--", color=MUTED, lw=1.2, label="Unburned pond")
        ax.plot(days, pond_fire[:, y, x], color=color, lw=1.5, label="Burned pond")
        ax2 = ax.twinx()
        ax2.plot(days, ice_fire[:, y, x], color=ORANGE, lw=1.1, label="Surface ice")
        ax2.set_ylabel("Surface ice (kg m⁻²)", color=ORANGE)
        ax.axvline(fire_line, color=ORANGE, lw=1.0, ls=":")
        ax.set_ylabel("Ponding depth (mm)")
        ax.set_title(f"CMT{cmt:02d}: overnight surface ponding")
        ax.grid(axis="y", color=GRID, lw=.6)
        lines = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
        labels = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
        ax.legend(lines, labels, loc="upper right")
    axes[-1].set_xlabel("Transition year")
    save(fig, out, "observed-fire-ponding")

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.4), layout="constrained")
    years = np.arange(1, YEARS + 1)
    for ax, name, ylabel, title in [
            (axes[0], "RHSOM", "Heterotrophic respiration (g C m⁻² yr⁻¹)",
             "(a) Soil heterotrophic respiration"),
            (axes[1], "RHDWD", "Dead-wood HR (g C m⁻² yr⁻¹)",
             "(b) Dead woody debris HR")]:
        for cell, cmt, color in zip(CELLS, CMTS, [TEAL, BLUE]):
            y, x = cell
            ax.plot(years, yearly["control"][name][:, y, x], "--",
                    color=MUTED, lw=1.2)
            ax.plot(years, yearly["continuous"][name][:, y, x], color=color,
                    lw=1.7, label=f"CMT{cmt:02d} burned")
        ax.axvline(fire_year + 1, color=ORANGE, lw=1.0, ls=":")
        ax.set(xlabel="Transition year", ylabel=ylabel, title=title, xticks=years)
        ax.grid(axis="y", color=GRID, lw=.6)
        ax.legend()
    save(fig, out, "observed-fire-respiration")

    fig, axes = plt.subplots(2, 1, figsize=(7.4, 5.4), sharex=True,
                             layout="constrained")
    for ax, cell, cmt, color in zip(axes, CELLS, CMTS, [TEAL, BLUE]):
        y, x = cell
        ax.plot(days, ICE * sub_ctl[:, y, x], "--", color=MUTED, lw=1.2,
                label="Unburned melt")
        ax.plot(days, ICE * sub_fire[:, y, x], color=color, lw=1.6,
                label="Burned melt")
        ax.axvline(fire_line, color=ORANGE, lw=1.0, ls=":")
        ax.set_ylabel("Cumulative excess-ice melt (kg m⁻²)")
        ax.set_title(f"CMT{cmt:02d}: observed-climate thaw with mapped fire")
        ax.grid(axis="y", color=GRID, lw=.6)
        ax.legend(loc="upper left")
    axes[-1].set_xlabel("Transition year")
    save(fig, out, "observed-fire-excess-ice")

    print(json.dumps(summary, indent=2))
    failed = [x for x in checks if x["status"] != "PASS"]
    if failed:
        raise RuntimeError(f"{len(failed)} gates failed: {[x['test'] for x in failed]}")


if __name__ == "__main__":
    main()
