#!/usr/bin/env python3
"""Download BNZ:729 GPS elevation zips and build treatment subsidence obs CSV."""
from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

PKG = Path(__file__).resolve().parent
sys.path.insert(0, str(PKG))

from lter_download import download_dataset_files  # noqa: E402

GPS_YEARS = (
    2009, 2011, 2015, 2016, 2017, 2018,
    2019, 2020, 2022, 2023, 2024,
)
TREATMENT_MAP = {
    "control": "control",
    "air warming": "air_warming",
    "soil warming": "soil_warming",
    "air + soil warming": "air_soil_warming",
    "air_+_soil_warming": "air_soil_warming",
}


def fetch_gps_zips(cache_dir: Path, *, force: bool = False) -> list[Path]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    years = "|".join(str(y) for y in GPS_YEARS)
    pattern = rf"729_EML_AK_CiPEHR_GPS_Elevation_({years})\.zip"
    return download_dataset_files(729, cache_dir, pattern=pattern, force=force)


def fetch_plot_locations(cache_dir: Path, *, force: bool = False) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    paths = download_dataset_files(
        730, cache_dir, pattern=r"730_EML_AK_CiPEHR_GPS_Plot_Locations\.zip", force=force)
    return paths[0]


def _extract_zip(zip_path: Path, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(dest)
    return next(dest.rglob("*.shp"))


def _shp_to_csv(shp: Path, csv_path: Path) -> None:
    cmd = ["ogr2ogr", "-f", "CSV", str(csv_path), str(shp), "-lco", "GEOMETRY=AS_XY"]
    subprocess.run(cmd, check=True, capture_output=True)


def _load_plot_treatments(shp: Path) -> list[dict]:
    csv_path = shp.with_suffix(".plots.csv")
    _shp_to_csv(shp, csv_path)
    plots = []
    for row in csv.DictReader(csv_path.open()):
        raw = row["treatment"].strip().lower().replace(" ", "_")
        treatment = TREATMENT_MAP.get(row["treatment"].strip().lower(), raw)
        if treatment == "air_+_soil_warming":
            treatment = "air_soil_warming"
        plots.append({
            "e": float(row["X"]),
            "n": float(row["Y"]),
            "treatment": treatment,
        })
    return plots


def _nearest_treatment(e: float, n: float, plots: list[dict]) -> str:
    best = min(plots, key=lambda p: (p["e"] - e) ** 2 + (p["n"] - n) ** 2)
    return best["treatment"]


def _col(row: dict, *names: str) -> str | None:
    lower = {k.lower(): v for k, v in row.items()}
    for name in names:
        if name.lower() in lower and lower[name.lower()] not in ("", None):
            return lower[name.lower()]
    return None


def _load_gps_year(shp: Path, plots: list[dict], file_year: int | None = None) -> dict[str, dict]:
    csv_path = shp.with_suffix(".gps.csv")
    _shp_to_csv(shp, csv_path)
    by_key: dict[str, dict] = {}
    for row in csv.DictReader(csv_path.open()):
        e_raw = _col(row, "Easting")
        n_raw = _col(row, "Northing", "Northng")
        elev_raw = _col(row, "Elevation", "Elevatn")
        id_raw = _col(row, "id", "Name", "nmrc_nm")
        if not all((e_raw, n_raw, elev_raw, id_raw)):
            continue
        e = float(e_raw)
        n = float(n_raw)
        point_id = id_raw.split(".")[0]
        by_key[point_id] = {
            "e": e,
            "n": n,
            "elev": float(elev_raw),
            "treatment": _nearest_treatment(e, n, plots),
            "file_year": file_year,
        }
    return by_key


def build_subsidence_obs(
    cache_dir: Path,
    obs_path: Path,
    *,
    baseline_year: int = 2009,
) -> dict:
    gps_cache = cache_dir / "bnz729"
    plot_cache = cache_dir / "bnz730"
    zips = fetch_gps_zips(gps_cache)
    plot_zip = fetch_plot_locations(plot_cache)
    plot_shp = _extract_zip(plot_zip, plot_cache / "extracted")
    plots = _load_plot_treatments(plot_shp)

    yearly: dict[int, dict[str, dict]] = {}
    for zip_path in sorted(zips):
        stem = zip_path.stem
        year_token = stem.split("_")[-1]
        if year_token == "may":
            year = int(stem.split("_")[-2])
        else:
            year = int(year_token)
        shp = _extract_zip(zip_path, gps_cache / f"extracted/{year}")
        yearly[year] = _load_gps_year(shp, plots, file_year=year)

    baseline = yearly[baseline_year]
    keys = set(baseline)
    for data in yearly.values():
        keys &= set(data)

    # Treatment-mean cumulative subsidence (cm) relative to baseline year.
    series: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for key in keys:
        base_elev = baseline[key]["elev"]
        treatment = baseline[key]["treatment"]
        for year, data in sorted(yearly.items()):
            subs_cm = (base_elev - data[key]["elev"]) * 100.0
            series[treatment][year].append(subs_cm)

    obs_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    summary = {}
    with obs_path.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow([
            "year", "treatment", "mean_subsidence_cm", "se_cm", "n_points", "baseline_year",
        ])
        for treatment in sorted(series):
            summary[treatment] = {}
            for year in sorted(series[treatment]):
                values = series[treatment][year]
                mean = float(np_mean(values))
                se = float(np_se(values))
                writer.writerow([
                    year, treatment, f"{mean:.3f}", f"{se:.3f}", len(values), baseline_year,
                ])
                summary[treatment][year] = {"mean_cm": mean, "se_cm": se, "n": len(values)}

    meta = {
        "source": "bnz729_gps_elevation",
        "baseline_year": baseline_year,
        "years": sorted(yearly),
        "n_common_points": len(keys),
        "treatments": summary,
        "obs_csv": str(obs_path),
    }
    obs_path.with_suffix(".provenance.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def np_mean(values: list[float]) -> float:
    import numpy as np
    return float(np.mean(values))


def np_se(values: list[float]) -> float:
    import numpy as np
    arr = np.asarray(values, float)
    if len(arr) < 2:
        return 0.0
    return float(np.std(arr, ddof=1) / math.sqrt(len(arr)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=PKG / "data/cache")
    parser.add_argument(
        "--obs", type=Path,
        default=PKG / "obs/bnz729-gps-subsidence-by-treatment.csv")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    meta = build_subsidence_obs(args.cache, args.obs)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
