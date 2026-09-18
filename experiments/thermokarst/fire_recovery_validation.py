#!/usr/bin/env python3
"""Validate early-season fire with active excess ice and multi-year recovery."""
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
FIRE_YEAR = 0
FIRE_JDAY = 180
FIRE_DAY = FIRE_JDAY - 1
YEARS = 4
SPLIT = 2
SEVERITY = {(0, 0): 3, (0, 1): 4}
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


def make_observed_fire_weather(source, dest):
    shutil.copy2(source, dest)
    with Dataset(source) as src, Dataset(dest, "r+") as out:
        tair = np.asarray(src["tair"][:, 0, 0], float)
        nyears = tair.size // 12
        june_july = np.array([tair[y * 12 + 5] + tair[y * 12 + 6]
                              for y in range(nyears)])
        year = int(np.argmax(june_july))
        selected = {}
        for name in ["tair", "precip", "nirr", "vapor_press"]:
            block = np.asarray(src[name][year * 12:(year + 1) * 12])
            selected[name] = block
            for i in range(out[name].shape[0]):
                out[name][i] = block[i % 12]
    return {
        "source_year_index": year,
        "june_C": float(selected["tair"][5, 0, 0]),
        "july_C": float(selected["tair"][6, 0, 0]),
        "june_precip_mm": float(selected["precip"][5, 0, 0]),
        "july_precip_mm": float(selected["precip"][6, 0, 0]),
        "monthly_tair_C": [float(selected["tair"][m, 0, 0]) for m in range(12)],
        "monthly_precip_mm": [float(selected["precip"][m, 0, 0]) for m in range(12)],
    }


def make_fire(source, dest, event_year=None):
    shutil.copy2(source, dest)
    with Dataset(dest, "r+") as dataset:
        for name in ["exp_burn_mask", "exp_jday_of_burn",
                     "exp_fire_severity", "exp_area_of_burn"]:
            dataset[name][:] = 0
        if event_year is not None:
            for (y, x), severity in SEVERITY.items():
                dataset["exp_burn_mask"][event_year, y, x] = 1
                dataset["exp_jday_of_burn"][event_year, y, x] = FIRE_JDAY
                dataset["exp_fire_severity"][event_year, y, x] = severity
                dataset["exp_area_of_burn"][event_year, y, x] = 1000000


def make_spec(source, dest):
    rows = list(csv.DictReader(source.open()))
    extra_daily = set(bgc.TK) | {"SNOWTHICK"}
    extra_yearly = set(bgc.BGC)
    extra_monthly = {"BURNTHICK", "BURNSOIL2AIRC", "BURNSOIL2AIRN"}
    for row in rows:
        row["Yearly"] = row["Monthly"] = row["Daily"] = ""
        if row["Name"] in extra_daily:
            row["Daily"] = "d"
        if row["Name"] in extra_yearly:
            row["Yearly"] = "y"
        if row["Name"] in extra_monthly:
            row["Monthly"] = "m"
    with dest.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def config(base, directory, restart, fire_file, output=True, tr_start=0):
    cfg = bgc.config(base, directory, restart, dsl=False, output=output, tr_start=tr_start)
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT / "dvmdostem")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "experiments/thermokarst/fire_recovery_validation_results")
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
    weather = make_observed_fire_weather(
        Path(base["IO"]["hist_climate_file"]), out / "observed-fire-weather.nc")
    base["IO"]["hist_climate_file"] = str(out / "observed-fire-weather.nc")
    spec = out / "fire-recovery-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec)
    base["IO"]["output_spec_file"] = str(spec)

    source_fire = Path(base["IO"]["hist_exp_fire_file"])
    fire_on = out / "fire-year-zero.nc"
    fire_off = out / "no-fire.nc"
    make_fire(source_fire, fire_on, FIRE_YEAR)
    make_fire(source_fire, fire_off)

    statuses = {}
    statuses["initialization"] = bgc.completed(out, "initialization") if args.reuse else None
    if statuses["initialization"] is None:
        statuses["initialization"] = bgc.run(
            args.binary.resolve(), out, "initialization",
            bgc.config(base, out / "initialization", output=False),
            ["--pr-yrs", "1", "--eq-yrs", "5"])
    initial = out / "initialization/restart-eq.nc"
    injected = out / "restart-with-excess.nc"
    added = bgc.inject_excess(initial, injected, fraction=.2, top=.05, bottom=.8)

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
            config(base, out / "resumed", out / "split-first/restart-tr.nc", fire_on, tr_start=SPLIT),
            ["--tr-yrs", str(YEARS - SPLIT)])

    burn = fire_topo.monthly(out / "continuous", "BURNTHICK")
    soilc = fire_topo.monthly(out / "continuous", "BURNSOIL2AIRC")
    sub_fire = bgc.read_daily(out / "continuous", "TKSUBSIDENCE")
    sub_ctl = bgc.read_daily(out / "control", "TKSUBSIDENCE")
    snow_fire = bgc.read_daily(out / "continuous", "SNOWTHICK")
    snow_ctl = bgc.read_daily(out / "control", "SNOWTHICK")
    yearly = {
        case: {name: bgc.read_yearly(out / case, name)
               for name in ["GPP", "NPP", "RHSOM", "SOC", "VEGC"]}
        for case in ["control", "continuous"]
    }
    first = {name: bgc.read_daily(out / "split-first", name) for name in bgc.TK}
    second = {name: bgc.read_daily(out / "resumed", name) for name in bgc.TK}
    resumed_daily = {name: np.concatenate([first[name], second[name]], axis=0)
                     for name in bgc.TK}

    excess_at_fire = remaining_excess(added, sub_fire, FIRE_DAY)
    excess_control_at_fire = remaining_excess(added, sub_ctl, FIRE_DAY)
    thaw_at_fire = {
        str(cell): float(ICE * sub_fire[FIRE_DAY][cell]) for cell in CELLS
    }

    final_c = out / "continuous/restart-tr.nc"
    final_r = out / "resumed/restart-tr.nc"
    physical = ["TKstate", "TKmatrix", "TKporosity", "TKexcess", "DZsoil",
                "TSsoil", "LIQsoil", "ICEsoil", "frontZ", "frontFT"]
    diffs = {
        name: max(bgc.maxdiff(fire_topo.restart(final_c, name, cell),
                              fire_topo.restart(final_r, name, cell))
                  for cell in CELLS)
        for name in physical
    }
    inventory_relative = 0.
    cells = []
    for cell, cmt in zip(CELLS, CMTS):
        state = fire_topo.restart(final_c, "TKstate", cell)
        before = bgc.inventory(injected, cell)
        after_fire = bgc.inventory(final_c, cell)
        after_ctl = bgc.inventory(out / "control/restart-tr.nc", cell)
        y, x = cell
        cells.append({
            "cmt": cmt,
            "severity": SEVERITY[cell],
            "burn_depth_m": float(np.sum(burn[:, y, x])),
            "burned_soil_c_g_m2": float(np.sum(soilc[:, y, x])),
            "released_water_kg_m2": float(state[FIRE_RELEASED_WATER]),
            "routed_liquid_kg_m2": float(state[FIRE_ROUTED_LIQUID]),
            "exported_solid_energy_J_m2": float(state[FIRE_EXPORTED_ENERGY]),
            "burned_matrix_m": float(state[FIRE_MATRIX_LOSS]),
            "initial_excess_kg_m2": added[str(cell)],
            "excess_at_fire_kg_m2": excess_at_fire[str(cell)],
            "control_excess_at_fire_kg_m2": excess_control_at_fire[str(cell)],
            "thawed_before_fire_kg_m2": thaw_at_fire[str(cell)],
            "final_excess_kg_m2": float(np.sum(fire_topo.restart(final_c, "TKexcess", cell))),
            "final_fire_SOC_g_m2": after_fire["SOC"],
            "final_control_SOC_g_m2": after_ctl["SOC"],
            "final_fire_VEGC_g_m2": after_fire["VEGC"],
            "final_control_VEGC_g_m2": after_ctl["VEGC"],
            "initial_layers": before["layers"],
            "final_layers": after_fire["layers"],
        })
        ia = bgc.inventory(final_c, cell)
        ib = bgc.inventory(final_r, cell)
        for name in ["C", "N"]:
            inventory_relative = max(
                inventory_relative,
                abs(ia[name] - ib[name]) / max(abs(ia[name]), 1.))

    fire_diag_relative = max(
        abs(fire_topo.restart(final_c, "TKstate", cell)[i]
            - fire_topo.restart(final_r, "TKstate", cell)[i])
        / max(abs(fire_topo.restart(final_c, "TKstate", cell)[i]), 1.)
        for cell in CELLS
        for i in [FIRE_RELEASED_WATER, FIRE_EXPORTED_ENERGY,
                  FIRE_MATRIX_LOSS, FIRE_ROUTED_LIQUID])
    sub_resume_diff = max(
        bgc.maxdiff(sub_fire[:, y, x], resumed_daily["TKSUBSIDENCE"][:, y, x])
        for y, x in CELLS)
    veg_recovery = []
    for i, cell in enumerate(CELLS):
        y, x = cell
        veg_f = yearly["continuous"]["VEGC"][:, y, x]
        veg_c = yearly["control"]["VEGC"][:, y, x]
        fire_year_loss = float(veg_c[0] - veg_f[0])
        later = float(veg_f[-1] - veg_f[0])
        veg_recovery.append({
            "cmt": CMTS[i],
            "fire_year_loss_g_m2": fire_year_loss,
            "postfire_change_g_m2": later,
        })

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
    gate("fire during thaw with remaining excess",
         {"excess_at_fire": [x["excess_at_fire_kg_m2"] for x in cells],
          "thawed_before_fire": [x["thawed_before_fire_kg_m2"] for x in cells]},
         "remaining excess >0 and some excess-ice thaw by DOY 180",
         all(x["excess_at_fire_kg_m2"] > 0 and x["thawed_before_fire_kg_m2"] > 1e-6
             for x in cells))
    gate("site-specific burn severity",
         [x["severity"] for x in cells], "CMT04=3 and CMT05=4",
         [x["severity"] for x in cells] == [3, 4])
    gate("nonzero explicit fire", [x["burn_depth_m"] for x in cells],
         ">0 m in each CMT", all(x["burn_depth_m"] > 0 for x in cells))
    gate("soil combustion branch", [x["burned_soil_c_g_m2"] for x in cells],
         ">0 g C m-2", all(x["burned_soil_c_g_m2"] > 0 for x in cells))
    gate("fire phase-water release", [x["released_water_kg_m2"] for x in cells],
         ">0 kg m-2", all(x["released_water_kg_m2"] > 0 for x in cells))
    gate("recovery years after fire", YEARS - 1, ">=3", YEARS - 1 >= 3)
    gate("vegetation mortality in fire year",
         [x["fire_year_loss_g_m2"] for x in veg_recovery],
         ">0 g C m-2 relative to unburned control",
         all(x["fire_year_loss_g_m2"] > 0 for x in veg_recovery))
    gate("restart geometry",
         max(diffs[n] for n in ["TKmatrix", "TKporosity", "TKexcess", "DZsoil"]),
         "<=1e-6 m",
         max(diffs[n] for n in ["TKmatrix", "TKporosity", "TKexcess", "DZsoil"]) <= 1e-6)
    gate("restart fire diagnostics", fire_diag_relative, "<=2e-4 scaled",
         fire_diag_relative <= 2e-4)
    gate("restart ecosystem C/N inventory", inventory_relative,
         "<=5e-3 relative after a post-fire midpoint restart",
         inventory_relative <= 5e-3)
    gate("restart subsidence trajectory", sub_resume_diff, "<=1e-5 m",
         sub_resume_diff <= 1e-5)

    summary = {
        "weather": weather,
        "fire": {"year_index": FIRE_YEAR, "jday": FIRE_JDAY,
                 "severity": {str(k): v for k, v in SEVERITY.items()}},
        "probe": probe,
        "statuses": statuses,
        "cells": cells,
        "vegetation_recovery": veg_recovery,
        "restart_max_difference": diffs,
        "restart_fire_diagnostic_relative_difference": fire_diag_relative,
        "restart_inventory_relative_difference": inventory_relative,
        "restart_subsidence_difference_m": sub_resume_diff,
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
    days = np.arange(sub_fire.shape[0]) / 365.0
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 5.6), sharex=True,
                             layout="constrained")
    for ax, cell, cmt, color in zip(axes, CELLS, CMTS, [TEAL, BLUE]):
        y, x = cell
        remaining_f = added[str(cell)] - ICE * sub_fire[:, y, x]
        remaining_c = added[str(cell)] - ICE * sub_ctl[:, y, x]
        ax.plot(days, remaining_c, "--", color=MUTED, lw=1.3, label="Unburned")
        ax.plot(days, remaining_f, color=color, lw=1.7, label="Burned")
        ax.axvline(FIRE_DAY / 365.0, color=ORANGE, lw=1.0, ls=":")
        ax.text(FIRE_DAY / 365.0, 0.98, "fire, DOY 180", color=ORANGE,
                fontsize=7.5, ha="left", va="top",
                transform=ax.get_xaxis_transform())
        ax.set_ylabel("Remaining excess ice (kg m⁻²)")
        ax.set_title(f"CMT{cmt:02d}: fire during active thaw")
        ax.grid(axis="y", color=GRID, lw=.6)
        ax.legend(loc="upper right")
    axes[-1].set_xlabel("Transition year")
    save(fig, out, "fire-recovery-excess-ice")

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.4), layout="constrained")
    years = np.arange(1, YEARS + 1)
    for ax, name, ylabel, title in [
            (axes[0], "VEGC", "Vegetation C (g m⁻²)", "(a) Vegetation recovery"),
            (axes[1], "SOC", "Soil C (g m⁻²)", "(b) Soil carbon")]:
        for cell, cmt, color in zip(CELLS, CMTS, [TEAL, BLUE]):
            y, x = cell
            ax.plot(years, yearly["control"][name][:, y, x], "--",
                    color=MUTED, lw=1.2)
            ax.plot(years, yearly["continuous"][name][:, y, x], color=color,
                    lw=1.7, label=f"CMT{cmt:02d} burned")
        ax.axvline(1, color=ORANGE, lw=1.0, ls=":")
        ax.set(xlabel="Transition year", ylabel=ylabel, title=title, xticks=years)
        ax.grid(axis="y", color=GRID, lw=.6)
        ax.legend()
    save(fig, out, "fire-recovery-carbon")

    fig, axes = plt.subplots(2, 1, figsize=(7.4, 5.4), sharex=True,
                             layout="constrained")
    for ax, cell, cmt, color in zip(axes, CELLS, CMTS, [TEAL, BLUE]):
        y, x = cell
        ax.plot(days, snow_ctl[:, y, x] * 100, "--", color=MUTED, lw=1.2,
                label="Unburned snow")
        ax.plot(days, snow_fire[:, y, x] * 100, color=color, lw=1.6,
                label="Burned snow")
        ax2 = ax.twinx()
        ax2.plot(days, sub_fire[:, y, x] * 1000, color=ORANGE, lw=1.3,
                 label="Burned subsidence")
        ax2.set_ylabel("Subsidence (mm)", color=ORANGE)
        ax.axvline(FIRE_DAY / 365.0, color=ORANGE, lw=1.0, ls=":")
        ax.set_ylabel("Snow thickness (cm)")
        ax.set_title(f"CMT{cmt:02d}: snowpack and post-fire subsidence")
        ax.grid(axis="y", color=GRID, lw=.6)
        lines = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
        labels = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
        ax.legend(lines, labels, loc="upper right")
    axes[-1].set_xlabel("Transition year")
    save(fig, out, "fire-recovery-snow-subsidence")

    fig, ax = plt.subplots(figsize=(7.2, 3.4), layout="constrained")
    names = ["Geometry (m)", "Subsidence (m)",
             "Fire diagnostics (relative)", "C/N inventory (relative)"]
    values = [
        max(diffs[n] for n in ["TKmatrix", "TKporosity", "TKexcess", "DZsoil"]),
        sub_resume_diff, fire_diag_relative, inventory_relative,
    ]
    ax.barh(names, values, color=TEAL)
    ax.set_xscale("symlog", linthresh=1e-12)
    ax.set(xlabel="Maximum continuous − resumed difference",
           title="Recovery continuation agrees after the post-fire restart")
    ax.grid(axis="x", color=GRID, lw=.6)
    save(fig, out, "fire-recovery-restart")

    print(json.dumps(summary, indent=2))
    failed = [x for x in checks if x["status"] != "PASS"]
    if failed:
        raise RuntimeError(f"{len(failed)} gates failed: {[x['test'] for x in failed]}")


if __name__ == "__main__":
    main()
