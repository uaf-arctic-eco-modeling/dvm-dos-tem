#!/usr/bin/env python3
"""Full historic+projected Toolik series with a burn-severity raster and ice lenses."""
import argparse, csv, json, os, shutil, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
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
ICE_MASSES = (25.0, 50.0, 100.0)
ICE_DEPTH = 0.20
# Spatial raster values, not a CMT lookup (lookup would be CMT04=3, CMT05=4).
RASTER_SEVERITY = {(0, 0): 4, (0, 1): 3}
CMT_LOOKUP = {4: 3, 5: 4}
INK = "#171717"
TEAL = "#1F6F5F"
BLUE = "#4C78A8"
ORANGE = "#D55E00"
MUTED = "#777772"
GRID = "#E4E7E5"
MASSES_COLOR = {25.0: "#8FB9A8", 50.0: TEAL, 100.0: "#0B3D36"}


def climate_years(path):
    with Dataset(path) as src:
        return int(src["tair"].shape[0] // 12)


def warmest_fire_year(path):
    with Dataset(path) as src:
        tair = np.asarray(src["tair"][:, 0, 0], float)
        n = tair.size // 12
        score = np.array([tair[y * 12 + 5] + tair[y * 12 + 6] for y in range(n)])
        return int(np.argmax(score)), n


def write_severity_raster(veg, dest, values):
    shutil.copy2(veg, dest)
    with Dataset(dest, "r+") as dst:
        if "burn_severity" not in dst.variables:
            dst.createVariable("burn_severity", "i4", ("Y", "X"))
        sev = np.zeros(tuple(dst.dimensions[d].size for d in ("Y", "X")),
                       dtype=np.int32)
        for cell, value in values.items():
            y, x = cell
            sev[y, x] = int(value)
        dst["burn_severity"][:] = sev
        dst["burn_severity"].long_name = "input burn severity raster"
    return dest


def read_severity_raster(path):
    with Dataset(path) as src:
        name = "burn_severity" if "burn_severity" in src.variables else "veg_class"
        data = np.asarray(src[name][:], int)
    return {cell: int(data[cell]) for cell in CELLS}, data


def make_fire(source, dest, field, event_year=None):
    shutil.copy2(source, dest)
    with Dataset(dest, "r+") as dataset:
        for name in ["exp_burn_mask", "exp_jday_of_burn",
                     "exp_fire_severity", "exp_area_of_burn"]:
            dataset[name][:] = 0
        if event_year is not None:
            dataset["exp_fire_severity"][event_year] = field
            ny, nx = field.shape
            for y in range(ny):
                for x in range(nx):
                    if field[y, x] > 0:
                        dataset["exp_burn_mask"][event_year, y, x] = 1
                        dataset["exp_jday_of_burn"][event_year, y, x] = FIRE_JDAY
                        dataset["exp_area_of_burn"][event_year, y, x] = 1000000
    return dest


def make_spec(source, dest, daily=False, scenario=False):
    rows = list(csv.DictReader(source.open()))
    yearly = set(bgc.BGC) | {"TKSUBSIDENCE"}
    monthly = {"BURNTHICK", "BURNSOIL2AIRC"}
    daily_names = set(bgc.TK) | {"SNOWTHICK", "TKPOND", "TKSURFICE"} if daily else set()
    for row in rows:
        row["Yearly"] = row["Monthly"] = row["Daily"] = ""
        if row["Name"] in yearly:
            row["Yearly"] = "y"
        if row["Name"] in monthly:
            row["Monthly"] = "m"
        if row["Name"] in daily_names:
            row["Daily"] = "d"
    with dest.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def config(base, directory, restart, fire_hist, fire_proj, output=True,
           tr_start=0, scenario=False, dsl=True):
    cfg = bgc.config(base, directory, restart, dsl=dsl, output=output,
                     tr_start=tr_start)
    cfg["IO"]["hist_exp_fire_file"] = str(fire_hist)
    cfg["IO"]["proj_exp_fire_file"] = str(fire_proj)
    cfg["IO"]["output_nc_sc"] = int(bool(scenario and output))
    for stage in ["tr", "sc"]:
        cfg["stage_settings"][stage]["dsb"] = True
        cfg["stage_settings"][stage]["dsl"] = bool(dsl)
    return cfg


def yearly(directory, name, stage):
    path = directory / f"{name}_yearly_{stage}.nc"
    if not path.exists():
        return None
    with Dataset(path) as dataset:
        array = np.asarray(np.ma.asarray(dataset[name][:]).filled(np.nan), float)
    while array.ndim > 3:
        array = np.nansum(array, axis=1)
    return array


def join_stages(directory, name):
    tr = yearly(directory, name, "tr")
    sc = yearly(directory, name, "sc")
    if tr is None:
        return sc
    if sc is None:
        return tr
    return np.concatenate([tr, sc], axis=0)


def remaining_excess(initial, subsidence, day):
    melted = ICE * np.asarray(subsidence[day], float)
    return {str(cell): float(initial[str(cell)] - melted[cell])
            for cell in CELLS}


def save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=240, bbox_inches="tight")
    fig.savefig(out / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def lens_depth(path, cell, mass):
    with Dataset(path) as dataset:
        y, x = cell
        n = int(dataset["numsl"][y, x])
        z = 0.0
        for j in range(n):
            matrix = float(dataset["TKmatrix"][y, x, j])
            excess = float(dataset["TKexcess"][y, x, j])
            if abs(excess - mass) < 1e-6:
                return z, z + matrix
            z += matrix
    return float("nan"), float("nan")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=ROOT / "dvmdostem")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "experiments/thermokarst/historic_projection_validation_results")
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"
    out = args.output.resolve()
    if out.exists() and not args.reuse:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    probe = fire_topo.compile_probe(out)
    base = production.parse_json_with_comments(ROOT / "config/config.js")
    bgc.absolute_io(base)
    bgc.copy_spatial(base, out)
    hist_climate = Path(base["IO"]["hist_climate_file"])
    proj_climate = Path(base["IO"]["proj_climate_file"])
    hist_yrs = climate_years(hist_climate)
    proj_yrs = climate_years(proj_climate)
    fire_year, n_hist = warmest_fire_year(hist_climate)
    if n_hist != hist_yrs:
        raise RuntimeError("historic climate year count mismatch")
    spec = out / "century-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", spec, daily=False)
    daily_spec = out / "restart-output-spec.csv"
    make_spec(ROOT / "config/output_spec.csv", daily_spec, daily=True)
    base["IO"]["output_spec_file"] = str(spec)

    raster = out / "burn-severity.nc"
    write_severity_raster(Path(base["IO"]["veg_class_file"]), raster, RASTER_SEVERITY)
    raster_cells, raster_field = read_severity_raster(raster)
    lookup = {cell: CMT_LOOKUP[cmt] for cell, cmt in zip(CELLS, CMTS)}
    lookup_field = np.zeros_like(raster_field)
    for cell, value in lookup.items():
        lookup_field[cell] = value
    base["IO"]["burn_severity_file"] = str(raster)
    hist_fire = out / "historic-raster-fire.nc"
    proj_fire = out / "projected-no-fire.nc"
    no_hist_fire = out / "historic-no-fire.nc"
    # Fire timeseries keeps the CMT lookup so the raster override is testable.
    make_fire(Path(base["IO"]["hist_exp_fire_file"]), hist_fire, lookup_field, fire_year)
    make_fire(Path(base["IO"]["proj_exp_fire_file"]), proj_fire, lookup_field)
    make_fire(Path(base["IO"]["hist_exp_fire_file"]), no_hist_fire, lookup_field)

    statuses = {}
    statuses["initialization"] = bgc.completed(out, "initialization") if args.reuse else None
    if statuses["initialization"] is None:
        statuses["initialization"] = bgc.run(
            args.binary.resolve(), out, "initialization",
            bgc.config(base, out / "initialization", output=False),
            ["--pr-yrs", "1", "--eq-yrs", "5"])
    initial = out / "initialization/restart-eq.nc"
    injected = {}
    added = {}
    for mass in ICE_MASSES:
        path = out / f"restart-ice-{int(mass)}.nc"
        added[mass] = bgc.inject_excess_mass(initial, path, mass, ICE_DEPTH)
        injected[mass] = path

    jobs = []
    for mass in ICE_MASSES:
        for kind, fireh, firep in [
                ("control", no_hist_fire, proj_fire),
                ("burned", hist_fire, proj_fire)]:
            name = f"{kind}-{int(mass)}"
            jobs.append((name, mass, fireh, firep, injected[mass]))

    def launch(name, mass, fireh, firep, restart):
        if args.reuse:
            done = bgc.completed(out, name)
            if done is not None:
                return name, done
        cfg = config(base, out / name, restart, fireh, firep, scenario=True)
        return name, bgc.run(
            args.binary.resolve(), out, name, cfg,
            ["--tr-yrs", str(hist_yrs), "--sc-yrs", str(proj_yrs)])

    workers = max(1, int(args.workers))
    if workers == 1:
        for name, mass, fireh, firep, restart in jobs:
            statuses[name] = launch(name, mass, fireh, firep, restart)[1]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(launch, *job) for job in jobs]
            for future in as_completed(futures):
                name, status = future.result()
                statuses[name] = status

    restart_start = int(np.clip(fire_year - 3, 0, hist_yrs - 8))
    restart_nyears = 8
    restart_split = min(max(fire_year - restart_start + 2, 3), restart_nyears - 2)
    mass_r = 100.0
    restart_base = json.loads(json.dumps(base))
    restart_base["IO"]["output_spec_file"] = str(daily_spec)
    statuses["split-first"] = bgc.completed(out, "split-first") if args.reuse else None
    if statuses["split-first"] is None:
        statuses["split-first"] = bgc.run(
            args.binary.resolve(), out, "split-first",
            config(restart_base, out / "split-first", injected[mass_r],
                   hist_fire, proj_fire, tr_start=restart_start),
            ["--tr-yrs", str(restart_split)])
    statuses["restart-continuous"] = bgc.completed(out, "restart-continuous") if args.reuse else None
    if statuses["restart-continuous"] is None:
        statuses["restart-continuous"] = bgc.run(
            args.binary.resolve(), out, "restart-continuous",
            config(restart_base, out / "restart-continuous", injected[mass_r],
                   hist_fire, proj_fire, tr_start=restart_start),
            ["--tr-yrs", str(restart_nyears)])
    statuses["resumed"] = bgc.completed(out, "resumed") if args.reuse else None
    if statuses["resumed"] is None:
        statuses["resumed"] = bgc.run(
            args.binary.resolve(), out, "resumed",
            config(restart_base, out / "resumed",
                   out / "split-first/restart-tr.nc", hist_fire, proj_fire,
                   tr_start=restart_start + restart_split),
            ["--tr-yrs", str(restart_nyears - restart_split)])

    sub_c = bgc.read_daily(out / "restart-continuous", "TKSUBSIDENCE")
    first = bgc.read_daily(out / "split-first", "TKSUBSIDENCE")
    second = bgc.read_daily(out / "resumed", "TKSUBSIDENCE")
    resumed = np.concatenate([first, second], axis=0)
    daily_lag = max(bgc.maxdiff(sub_c[:, y, x], resumed[:, y, x]) for y, x in CELLS)
    endpoint = max(abs(float(sub_c[-1, y, x] - resumed[-1, y, x])) for y, x in CELLS)
    geometry = max(
        bgc.maxdiff(
            fire_topo.restart(out / "restart-continuous/restart-tr.nc", n, c),
            fire_topo.restart(out / "resumed/restart-tr.nc", n, c))
        for n in ["TKmatrix", "TKporosity", "TKexcess", "DZsoil"]
        for c in CELLS)

    cases = {}
    for mass in ICE_MASSES:
        burned = out / f"burned-{int(mass)}"
        control = out / f"control-{int(mass)}"
        burn = fire_topo.monthly(burned, "BURNTHICK")
        sub_b = join_stages(burned, "TKSUBSIDENCE")
        sub_k = join_stages(control, "TKSUBSIDENCE")
        rhs_b = join_stages(burned, "RHSOM")
        rhs_k = join_stages(control, "RHSOM")
        veg_b = join_stages(burned, "VEGC")
        veg_k = join_stages(control, "VEGC")
        gpp_b = join_stages(burned, "GPP")
        cases[mass] = {
            "added": added[mass],
            "lens": {str(c): lens_depth(injected[mass], c, mass) for c in CELLS},
            "burn_depth_m": {str(c): float(np.sum(burn[:, c[0], c[1]])) for c in CELLS},
            "severity": {str(c): raster_cells[c] for c in CELLS},
            "subsidence_burned": sub_b,
            "subsidence_control": sub_k,
            "rhsom_burned": rhs_b,
            "rhsom_control": rhs_k,
            "vegc_burned": veg_b,
            "vegc_control": veg_k,
            "gpp_burned": gpp_b,
            "final_subsidence_m": {str(c): float(sub_b[-1, c[0], c[1]]) for c in CELLS},
            "control_subsidence_m": {str(c): float(sub_k[-1, c[0], c[1]]) for c in CELLS},
        }

    fire_day = (fire_year - restart_start) * 365 + FIRE_JDAY - 1
    excess_at_fire = remaining_excess(added[mass_r], sub_c, fire_day)

    checks = []
    def gate(test, observed, criterion, ok):
        checks.append({"test": test,
                       "observed": json.dumps(observed) if isinstance(observed, (dict, list)) else observed,
                       "criterion": criterion,
                       "status": "PASS" if ok else "FAIL"})

    gate("synthetic fire water closure", abs(probe["water_residual_kg_m2"]),
         "<=1e-12 kg m-2", abs(probe["water_residual_kg_m2"]) <= 1e-12)
    gate("synthetic fire energy closure", abs(probe["energy_residual_J_m2"]),
         "<=1e-6 J m-2", abs(probe["energy_residual_J_m2"]) <= 1e-6)
    long_names = ["initialization"] + [f"{k}-{int(m)}" for m in ICE_MASSES
                                       for k in ("control", "burned")]
    gate("production completion", {n: statuses[n] for n in long_names},
         "all cells status 100",
         all(statuses[n] == [100, 100] for n in long_names))
    gate("full historic Toolik series", hist_yrs, "115 years", hist_yrs == 115)
    gate("projected climate series", proj_yrs, "85 years", proj_yrs == 85)
    raster_str = {str(k): v for k, v in raster_cells.items()}
    lookup_str = {str(k): v for k, v in lookup.items()}
    gate("severity comes from the raster", raster_str,
         "raster != CMT lookup and fire uses raster values",
         raster_cells != lookup and raster_cells == RASTER_SEVERITY)
    gate("raster overrides CMT lookup",
         {"raster": raster_str, "cmt_lookup": lookup_str,
          "burn_depth_m": cases[100.0]["burn_depth_m"]},
         "CMT04 (raster 4) burns more soil than CMT05 (raster 3)",
         cases[100.0]["burn_depth_m"][str(CELLS[0])] >
         cases[100.0]["burn_depth_m"][str(CELLS[1])])
    gate("ice lens masses", {m: added[m] for m in ICE_MASSES},
         "25, 50, and 100 kg m-2 in every cell",
         all(abs(added[m][str(c)] - m) < 1e-6 for m in ICE_MASSES for c in CELLS))
    lens_ok = True
    for mass in ICE_MASSES:
        for cell in CELLS:
            top, bottom = cases[mass]["lens"][str(cell)]
            if not (np.isfinite(top) and top - 1e-6 <= ICE_DEPTH < bottom + 1e-6):
                lens_ok = False
    gate("ice lens depth", {m: cases[m]["lens"] for m in ICE_MASSES},
         "20 cm below the ground surface", lens_ok)
    gate("historic raster fire", fire_year, "warmest June+July year burns",
         fire_year >= 0 and all(cases[100.0]["burn_depth_m"][str(c)] > 0 for c in CELLS))
    gate("remaining excess at fire", excess_at_fire,
         "CMT05 retains injected ice at the restart fire with dsl active",
         excess_at_fire[str(CELLS[1])] > 1.0)
    gate("restart geometry with dsl and remaining ice", geometry,
         "<=1e-3 m", geometry <= 1e-3)
    gate("CMT05 thaw-season restart lag",
         {"daily_max_m": daily_lag, "endpoint_m": endpoint},
         "endpoint <=1e-12 m and daily <=1e-4 m",
         endpoint <= 1e-12 and daily_lag <= 1e-4)
    gate("three ice amounts through hist+proj",
         [cases[m]["final_subsidence_m"] for m in ICE_MASSES],
         "finite subsidence for 25, 50, and 100 kg m-2",
         all(np.all(np.isfinite(list(cases[m]["final_subsidence_m"].values())))
             for m in ICE_MASSES))

    summary = {
        "hist_years": hist_yrs, "proj_years": proj_yrs, "fire_year": fire_year,
        "fire_jday": FIRE_JDAY, "ice_depth_m": ICE_DEPTH,
        "raster_severity": {str(k): v for k, v in raster_cells.items()},
        "cmt_lookup_severity": {str(k): v for k, v in lookup.items()},
        "added_excess_kg_m2": {str(m): added[m] for m in ICE_MASSES},
        "restart": {"start": restart_start, "years": restart_nyears,
                    "split": restart_split, "daily_lag_m": daily_lag,
                    "endpoint_m": endpoint, "geometry_m": geometry,
                    "excess_at_fire": excess_at_fire},
        "statuses": statuses,
        "cells": {str(m): {k: v for k, v in cases[m].items()
                           if k not in ("subsidence_burned", "subsidence_control",
                                        "rhsom_burned", "rhsom_control",
                                        "vegc_burned", "vegc_control", "gpp_burned")}
                  for m in ICE_MASSES},
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
    years = np.arange(hist_yrs + proj_yrs)
    fire_line = fire_year + (FIRE_JDAY - 1) / 365.0
    hist_end = hist_yrs - 0.5
    hist_years = years[:hist_yrs]
    proj_years = np.arange(proj_yrs)

    def plot_subsidence(name, xvals, sl, fire=False, xlabel="Year"):
        fig, axes = plt.subplots(2, 1, figsize=(8.2, 6.0), sharex=True,
                                 layout="constrained")
        for ax, cell, cmt in zip(axes, CELLS, CMTS):
            y, x = cell
            for mass in ICE_MASSES:
                color = MASSES_COLOR[mass]
                ax.plot(xvals, cases[mass]["subsidence_control"][sl, y, x] * 100,
                        "--", color=color, lw=1.0)
                ax.plot(xvals, cases[mass]["subsidence_burned"][sl, y, x] * 100,
                        color=color, lw=1.7, label=f"{int(mass)} kg m⁻²")
            if fire:
                ax.axvline(fire_line, color=ORANGE, lw=1.0, ls=":")
            ax.set_ylabel("Subsidence (cm)")
            ax.set_title(f"CMT{cmt:02d}")
            ax.grid(axis="y", color=GRID, lw=.6)
            ax.legend(ncol=3, loc="upper left")
        axes[-1].set_xlabel(xlabel)
        save(fig, out, name)

    def remaining_ice(mass, cell, sl):
        y, x = cell
        return np.maximum(
            0.0, added[mass][str(cell)] - ICE * cases[mass]["subsidence_burned"][sl, y, x])

    def plot_ice(name, xvals, sl, fire=False, xlabel="Year"):
        fig, axes = plt.subplots(2, 1, figsize=(8.2, 6.0), sharex=True,
                                 layout="constrained")
        for ax, cell, cmt in zip(axes, CELLS, CMTS):
            for mass in ICE_MASSES:
                ax.plot(xvals, remaining_ice(mass, cell, sl),
                        color=MASSES_COLOR[mass], lw=1.6, label=f"{int(mass)} kg m⁻²")
            if fire:
                ax.axvline(fire_line, color=ORANGE, lw=1.0, ls=":")
            ax.set_ylabel("Remaining excess ice (kg m⁻²)")
            ax.set_title(f"CMT{cmt:02d}: 20 cm lens")
            ax.grid(axis="y", color=GRID, lw=.6)
            ax.legend()
        axes[-1].set_xlabel(xlabel)
        save(fig, out, name)

    def plot_carbon(name, xvals, sl, fire=False, xlabel="Year"):
        fig, axes = plt.subplots(2, 1, figsize=(8.2, 6.0), sharex=True,
                                 layout="constrained")
        mass = 50.0
        for ax, cell, cmt in zip(axes, CELLS, CMTS):
            y, x = cell
            ax.plot(xvals, cases[mass]["vegc_control"][sl, y, x], "--", color=MUTED,
                    lw=1.2, label="Unburned VEGC")
            ax.plot(xvals, cases[mass]["vegc_burned"][sl, y, x],
                    color=TEAL if cmt == 4 else BLUE, lw=1.6, label="Burned VEGC")
            ax2 = ax.twinx()
            ax2.plot(xvals, cases[mass]["rhsom_burned"][sl, y, x], color=ORANGE, lw=1.1)
            ax2.set_ylabel("RHSOM (g C m⁻² y⁻¹)", color=ORANGE)
            if fire:
                ax.axvline(fire_line, color=ORANGE, lw=1.0, ls=":")
            ax.set_ylabel("Vegetation C (g C m⁻²)")
            ax.set_title(f"CMT{cmt:02d}: 50 kg m⁻² ice")
            ax.grid(axis="y", color=GRID, lw=.6)
            ax.legend(loc="upper left")
        axes[-1].set_xlabel(xlabel)
        save(fig, out, name)

    plot_subsidence("historic-subsidence", hist_years, slice(0, hist_yrs),
                    fire=True, xlabel="Historic year")
    plot_subsidence("projected-subsidence", proj_years, slice(hist_yrs, None),
                    xlabel="Projected year")
    plot_ice("historic-excess-ice", hist_years, slice(0, hist_yrs), fire=True,
             xlabel="Historic year")
    plot_ice("projected-excess-ice", proj_years, slice(hist_yrs, None),
             xlabel="Projected year")
    plot_carbon("historic-carbon", hist_years, slice(0, hist_yrs), fire=True,
                xlabel="Historic year")
    plot_carbon("projected-carbon", proj_years, slice(hist_yrs, None),
                xlabel="Projected year")

    fig, axes = plt.subplots(2, 1, figsize=(8.2, 6.0), sharex=True, layout="constrained")
    for ax, cell, cmt in zip(axes, CELLS, CMTS):
        y, x = cell
        for mass in ICE_MASSES:
            color = MASSES_COLOR[mass]
            ax.plot(years, cases[mass]["subsidence_control"][:, y, x] * 100,
                    "--", color=color, lw=1.0)
            ax.plot(years, cases[mass]["subsidence_burned"][:, y, x] * 100,
                    color=color, lw=1.7, label=f"{int(mass)} kg m⁻²")
        ax.axvline(fire_line, color=ORANGE, lw=1.0, ls=":")
        ax.axvline(hist_end, color=MUTED, lw=0.8, ls="--")
        ax.set_ylabel("Subsidence (cm)")
        ax.set_title(f"CMT{cmt:02d}: full historic and projected series")
        ax.grid(axis="y", color=GRID, lw=.6)
        ax.legend(ncol=3, loc="upper left")
    axes[-1].set_xlabel("Year (0 = historic start; dashed line = scenario start)")
    save(fig, out, "historic-projection-subsidence")

    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.4), layout="constrained")
    labels = [f"CMT{cmt:02d}" for cmt in CMTS]
    x = np.arange(len(labels))
    width = 0.24
    for i, mass in enumerate(ICE_MASSES):
        axes[0].bar(x + (i - 1) * width,
                    [cases[mass]["burn_depth_m"][str(c)] * 100 for c in CELLS],
                    width, color=MASSES_COLOR[mass], label=f"{int(mass)} kg")
        axes[1].bar(x + (i - 1) * width,
                    [cases[mass]["final_subsidence_m"][str(c)] * 100 for c in CELLS],
                    width, color=MASSES_COLOR[mass], label=f"{int(mass)} kg")
    axes[0].set(ylabel="Burn depth (cm)", title="Raster-severity combustion")
    axes[1].set(ylabel="Final subsidence (cm)", title="Subsidence after hist+proj")
    for ax in axes:
        ax.set_xticks(x, labels)
        ax.grid(axis="y", color=GRID, lw=.6)
        ax.legend()
    save(fig, out, "historic-projection-ice-amount")

    fig, ax = plt.subplots(figsize=(7.4, 3.6), layout="constrained")
    days = np.arange(sub_c.shape[0]) / 365.0 + restart_start
    y, x = CELLS[1]
    ax.plot(days, sub_c[:, y, x] * 1000, color=INK, lw=1.6, label="Continuous")
    ax.plot(days, resumed[:, y, x] * 1000, "--", color=TEAL, lw=1.4, label="Resumed")
    ax.axvline(fire_year + (FIRE_JDAY - 1) / 365.0, color=ORANGE, lw=1.0, ls=":")
    ax.set(xlabel="Historic year", ylabel="Subsidence (mm)",
           title="CMT05 restart lag with dsl and the 100 kg m⁻² lens")
    ax.grid(axis="y", color=GRID, lw=.6)
    ax.legend()
    save(fig, out, "historic-projection-restart-lag")

    fig, ax = plt.subplots(figsize=(4.6, 3.8), layout="constrained")
    show = np.ma.masked_where(raster_field == 0, raster_field)
    image = ax.imshow(show, origin="upper", cmap="YlOrRd", vmin=0, vmax=5)
    ax.set_xticks([0, 1])
    ax.set_yticks([0])
    ax.set_title("Input burn-severity raster")
    fig.colorbar(image, ax=ax, label="Severity code")
    save(fig, out, "historic-projection-severity-raster")

    print(json.dumps({k: summary[k] for k in
                      ["hist_years", "proj_years", "fire_year", "raster_severity",
                       "restart", "checks_passed", "checks_total"]}, indent=2))
    failed = [x for x in checks if x["status"] == "FAIL"]
    if failed:
        raise RuntimeError(f"{len(failed)} gates failed: {[x['test'] for x in failed]}")


if __name__ == "__main__":
    main()
