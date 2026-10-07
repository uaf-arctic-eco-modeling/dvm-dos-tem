#!/usr/bin/env python3
"""Samoylov Center hydrology tuning — drainage/CMT matrix under GSWP3+Boike forcing."""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "experiments/thermokarst"))
sys.path.insert(0, str(PKG))

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "build/matplotlib-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import production_validation as production
import bgc_coupling_validation as bgc
import samoylov_validation as sam

VARIANTS = {
    "baseline": {
        "description": "Paper-like: Rim drain 0 / Center drain 1, CMT 5/4",
        "drains": {sam.RIM: 0, sam.CENTER: 1},
        "cmts": {sam.RIM: 5, sam.CENTER: 4},
    },
    "center_dry": {
        "description": "Both well drained — test if Center retains snow",
        "drains": {sam.RIM: 0, sam.CENTER: 0},
        "cmts": {sam.RIM: 5, sam.CENTER: 4},
    },
    "both_wet": {
        "description": "Both poorly drained wetland analog",
        "drains": {sam.RIM: 1, sam.CENTER: 1},
        "cmts": {sam.RIM: 5, sam.CENTER: 4},
    },
    "rim_wet_center_dry": {
        "description": "Inverted drainage: Rim wet, Center dry",
        "drains": {sam.RIM: 1, sam.CENTER: 0},
        "cmts": {sam.RIM: 5, sam.CENTER: 4},
    },
    "swap_cmt": {
        "description": "Swap CMTs with baseline drainage",
        "drains": {sam.RIM: 0, sam.CENTER: 1},
        "cmts": {sam.RIM: 4, sam.CENTER: 5},
    },
}


def copy_spatial_variant(base, out, variant):
    cfg = VARIANTS[variant]
    mask = out / f"run-mask-{variant}.nc"
    shutil.copy2(base["IO"]["runmask_file"], mask)
    with Dataset(mask, "r+") as dataset:
        dataset["run"][:] = 0
        for cell in sam.CELLS:
            dataset["run"][cell] = 1

    paths = {"runmask_file": mask}
    for key, var in [("veg_class_file", "veg_class"),
                     ("drainage_file", "drainage_class"),
                     ("topo_file", "slope")]:
        src = Path(base["IO"][key])
        dst = out / f"{src.stem}-{variant}.nc"
        shutil.copy2(src, dst)
        with Dataset(dst, "r+") as dataset:
            for cell in sam.CELLS:
                if var == "veg_class":
                    dataset[var][cell] = cfg["cmts"][cell]
                elif var == "drainage_class":
                    dataset[var][cell] = cfg["drains"][cell]
                else:
                    dataset[var][cell] = sam.SLOPE_DEG
        paths[key] = dst
    return paths


def config_variant(base, out, variant, restart, eq_yrs):
    rim_ice = sam.PHASES[1]["rim_ice"]
    cfg = sam.config(
        base, out, out / variant, restart, True, rim_ice,
        layout="paired", output=True)
    spatial = copy_spatial_variant(base, out, variant)
    cfg["IO"].update({k: str(v) for k, v in spatial.items()})
    return cfg


def metrics(case_dir, tr_yrs):
    sub = bgc.read_daily(case_dir, "TKSUBSIDENCE")
    snow = bgc.read_daily(case_dir, "SNOWTHICK")
    pond = bgc.read_daily(case_dir, "TKPOND")
    _, orig = sam.temperature_series(case_dir, sub)
    rim_snow = float(np.nanmax(bgc.cell_series(snow, sam.RIM)))
    center_snow = float(np.nanmax(bgc.cell_series(snow, sam.CENTER)))
    rim_pond = sam.summer_mean_pond(case_dir, sam.RIM, tr_yrs)
    center_pond = sam.summer_mean_pond(case_dir, sam.CENTER, tr_yrs)
    rim_alt = sam.september_max_alt(case_dir, sam.RIM, tr_yrs)
    center_alt = sam.september_max_alt(case_dir, sam.CENTER, tr_yrs)
    rim_t65 = float(orig[0.65][:, sam.RIM[0], sam.RIM[1]].mean())
    center_t65 = float(orig[0.65][:, sam.CENTER[0], sam.CENTER[1]].mean())
    return {
        "peak_snow_rim_m": rim_snow,
        "peak_snow_center_m": center_snow,
        "snow_center_minus_rim_m": center_snow - rim_snow,
        "summer_pond_rim_m": rim_pond,
        "summer_pond_center_m": center_pond,
        "pond_center_minus_rim_m": center_pond - rim_pond,
        "sept_alt_rim_m": float(np.nanmean(rim_alt)),
        "sept_alt_center_m": float(np.nanmean(center_alt)),
        "mean_soilT_rim_65cm_C": rim_t65,
        "mean_soilT_center_65cm_C": center_t65,
        "subsidence_rim_m": float(bgc.cell_series(sub, sam.RIM)[-1]),
        "subsidence_center_m": float(bgc.cell_series(sub, sam.CENTER)[-1]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT / "dvmdostem")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/thermokarst/samoylov_hydrology_tune_results")
    parser.add_argument("--eq-yrs", type=int, default=10)
    parser.add_argument("--tr-yrs", type=int, default=13)
    parser.add_argument("--variants", nargs="*", default=list(VARIANTS))
    parser.add_argument("--reuse", action="store_true")
    args = parser.parse_args()

    out = args.output.resolve()
    if out.exists() and not args.reuse:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    base = production.parse_json_with_comments(ROOT / "config/config.js")
    bgc.absolute_io(base)
    climate_path = out / "samoylov-climate.nc"
    _, _, _, climate_meta = sam.prepare_climate(
        base, climate_path, 1, sam.PHASES[1], gswp3_path=sam.GSWP3_POINT)
    base["IO"]["hist_climate_file"] = str(climate_path)
    spec = out / "samoylov-output-spec.csv"
    sam.make_spec(ROOT / "config/output_spec.csv", spec, phase=2)
    base["IO"]["output_spec_file"] = str(spec)

    rim_ice = sam.PHASES[1]["rim_ice"]
    results = {}
    statuses = {}

    for variant in args.variants:
        init_dir = out / f"{variant}-init"
        case_dir = out / variant
        status_key = f"{variant}-init"
        statuses[status_key] = bgc.completed(out, f"{variant}-init") if args.reuse else None
        if statuses[status_key] is None:
            init_cfg = sam.config(
                base, out, init_dir, restart=None, thermokarst_enabled=True,
                ice_profile=rim_ice, layout="paired", output=False)
            spatial = copy_spatial_variant(base, out, variant)
            init_cfg["IO"].update({k: str(v) for k, v in spatial.items()})
            statuses[status_key] = bgc.run(
                args.binary.resolve(), out, f"{variant}-init", init_cfg,
                ["--pr-yrs", "1", "--eq-yrs", str(args.eq_yrs)])

        restart = init_dir / "restart-eq.nc"
        paired_restart = out / f"restart-{variant}.nc"
        sam.inject_excess_cells(restart, paired_restart, {
            sam.RIM: rim_ice, sam.CENTER: sam.PHASES[1]["center_ice"]})

        statuses[variant] = bgc.completed(out, variant) if args.reuse else None
        if statuses[variant] is None:
            cfg = config_variant(base, out, variant, paired_restart, args.eq_yrs)
            statuses[variant] = bgc.run(
                args.binary.resolve(), out, variant, cfg,
                ["--tr-yrs", str(args.tr_yrs)])

        m = metrics(case_dir, args.tr_yrs)
        m["description"] = VARIANTS[variant]["description"]
        m["drainage"] = {str(c): VARIANTS[variant]["drains"][c] for c in sam.CELLS}
        m["cmt"] = {str(c): VARIANTS[variant]["cmts"][c] for c in sam.CELLS}
        m["status"] = statuses[variant]
        results[variant] = m

    ranked = sorted(
        results.items(),
        key=lambda item: (
            item[1]["snow_center_minus_rim_m"],
            item[1]["pond_center_minus_rim_m"],
            -abs(item[1]["mean_soilT_center_65cm_C"]),
        ),
        reverse=True,
    )
    best = ranked[0][0] if ranked else None

    summary = {
        "eq_years": args.eq_yrs,
        "tr_years": args.tr_yrs,
        "forcing": climate_meta,
        "variants": results,
        "recommended_variant": best,
        "statuses": statuses,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    rows = []
    for name, m in results.items():
        rows.append({
            "variant": name,
            "drain_rim": m["drainage"][str(sam.RIM)],
            "drain_center": m["drainage"][str(sam.CENTER)],
            "cmt_rim": m["cmt"][str(sam.RIM)],
            "cmt_center": m["cmt"][str(sam.CENTER)],
            "peak_snow_rim_m": m["peak_snow_rim_m"],
            "peak_snow_center_m": m["peak_snow_center_m"],
            "snow_center_minus_rim_m": m["snow_center_minus_rim_m"],
            "pond_center_minus_rim_m": m["pond_center_minus_rim_m"],
            "sept_alt_rim_m": m["sept_alt_rim_m"],
            "sept_alt_center_m": m["sept_alt_center_m"],
            "soilT_center_65cm_C": m["mean_soilT_center_65cm_C"],
        })
    with (out / "variant_comparison.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    sam.style()
    fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
    names = [r["variant"] for r in rows]
    x = np.arange(len(names))
    w = 0.35
    ax.bar(x - w / 2, [r["peak_snow_rim_m"] for r in rows], w, label="Rim snow", color=sam.TEAL)
    ax.bar(x + w / 2, [r["peak_snow_center_m"] for r in rows], w, label="Center snow", color=sam.BLUE)
    ax.set_xticks(x, names, rotation=20, ha="right")
    ax.set(ylabel="Peak snow (m)", title="Samoylov hydrology tuning variants")
    ax.legend()
    ax.grid(axis="y", color=sam.GRID, lw=0.6)
    sam.save(fig, out, "hydrology-tune-snow")
    sam.write_samoylov_validation_report()

    print(json.dumps(summary, indent=2))
    print(f"Recommended variant: {best}", file=sys.stderr)


if __name__ == "__main__":
    main()
