#!/usr/bin/env python3
"""Download and aggregate Boike Samoylov station data for climate bias correction."""
from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

PKG = Path(__file__).resolve().parent
CACHE = PKG / "data/cache"
OBS = PKG / "obs"

PANGAEA_806203 = "https://doi.pangaea.de/10.1594/PANGAEA.806203?format=textfile"
PANGAEA_905230_ZIP = "https://store.pangaea.de/Publications/Boike-etal_2019_V201908/met_lv1_V201908.zip"
DINM = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def download(path, url):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 1000:
        return path
    print(f"Downloading {url} -> {path}", file=sys.stderr)
    with urllib.request.urlopen(url, timeout=600) as response:
        path.write_bytes(response.read())
    return path


def parse_pangaea_tab(path):
    rows = []
    in_data = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Date/Time"):
            in_data = True
            continue
        if not in_data or not line.strip() or line.startswith('"'):
            continue
        parts = line.split("\t")
        if len(parts) < 6:
            continue
        dt, _height, t2, _rh, _net, precip = parts[:6]
        try:
            rows.append((int(dt[:4]), int(dt[5:7]), int(dt[8:10]), float(t2), float(precip)))
        except ValueError:
            continue
    return rows


def parse_met_lv1_zip(zip_path, year_min=2002, year_max=2014):
    """Parse AWI level-1 30-min meteorology (PANGAEA.905230 archive)."""
    rows = []
    with zipfile.ZipFile(zip_path) as archive:
        for name in sorted(archive.namelist()):
            if not name.endswith(".dat"):
                continue
            year = int(name.split("_")[-1].split(".")[0])
            if year < year_min or year > year_max:
                continue
            for i, line in enumerate(archive.read(name).decode("utf-8", errors="replace").splitlines()):
                if i == 0:
                    continue
                parts = line.split(",")
                if len(parts) < 24:
                    continue
                stamp = parts[0]
                t_raw, t_fl = parts[1], parts[2]
                prec_raw, prec_fl = parts[23], parts[24]
                if t_fl != "0" or t_raw in ("NA", ""):
                    continue
                try:
                    month = int(stamp[5:7])
                    day = int(stamp[8:10])
                    tair = float(t_raw)
                    precip = float(prec_raw) if prec_raw not in ("NA", "") and prec_fl == "0" else 0.0
                except ValueError:
                    continue
                rows.append((year, month, day, tair, precip))
    return rows


def aggregate(rows, year_min=2002, year_max=2014):
    daily_t = defaultdict(list)
    daily_p = defaultdict(float)
    monthly_t = defaultdict(list)
    monthly_p = defaultdict(float)
    for year, month, day, tair, precip in rows:
        if year < year_min or year > year_max:
            continue
        key_d = (year, month, day)
        key_m = (year, month)
        daily_t[key_d].append(tair)
        daily_p[key_d] += precip
        monthly_t[key_m].append(tair)
        monthly_p[key_m] += precip
    return daily_t, daily_p, monthly_t, monthly_p


def write_monthly_csv(path, monthly_t, monthly_p, source):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["year", "month", "tair_C", "precip_mm", "source"])
        for (year, month) in sorted(monthly_t):
            writer.writerow([
                year, month,
                f"{np.mean(monthly_t[(year, month)]):.3f}",
                f"{monthly_p[(year, month)]:.3f}",
                source,
            ])


def write_daily_csv(path, daily_t, daily_p, source):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["year", "month", "day", "doy", "tair_C", "precip_mm", "source"])
        for (year, month, day) in sorted(daily_t):
            doy = sum(DINM[:month - 1]) + day
            writer.writerow([
                year, month, day, doy,
                f"{np.mean(daily_t[(year, month, day)]):.3f}",
                f"{daily_p[(year, month, day)]:.3f}",
                source,
            ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, default=CACHE / "met_lv1_V201908.zip")
    parser.add_argument("--monthly-out", type=Path,
                        default=OBS / "boike_samoylov_monthly_2002-2014.csv")
    parser.add_argument("--daily-out", type=Path,
                        default=OBS / "boike_samoylov_daily_2002-2014.csv")
    parser.add_argument("--year-min", type=int, default=2002)
    parser.add_argument("--year-max", type=int, default=2014)
    parser.add_argument("--legacy-fallback", action="store_true",
                        help="Use PANGAEA.806203 if ZIP unavailable")
    args = parser.parse_args()

    source = "PANGAEA.905230"
    if args.zip.exists() or not args.legacy_fallback:
        download(args.zip, PANGAEA_905230_ZIP)
        rows = parse_met_lv1_zip(args.zip, args.year_min, args.year_max)
    else:
        source = "PANGAEA.806203"
        tab = download(CACHE / "boike_samoylov_2002-2011.tab", PANGAEA_806203)
        rows = parse_pangaea_tab(tab)

    daily_t, daily_p, monthly_t, monthly_p = aggregate(rows, args.year_min, args.year_max)
    write_monthly_csv(args.monthly_out, monthly_t, monthly_p, source)
    write_daily_csv(args.daily_out, daily_t, daily_p, source)

    ann_precip = [
        sum(v for (y, _), v in monthly_p.items() if y == year)
        for year in range(args.year_min, args.year_max + 1)
    ]
    report = {
        "source_doi": "10.1594/PANGAEA.905230" if source == "PANGAEA.905230" else "10.1594/PANGAEA.806203",
        "years": [args.year_min, args.year_max],
        "records": len(rows),
        "monthly_rows": len(monthly_t),
        "daily_rows": len(daily_t),
        "mean_annual_precip_mm": float(np.mean(ann_precip)) if ann_precip else None,
        "monthly_out": str(args.monthly_out),
        "daily_out": str(args.daily_out),
    }
    report_path = args.monthly_out.with_suffix(".provenance.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
