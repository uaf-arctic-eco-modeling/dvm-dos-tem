#!/usr/bin/env python3
"""Download BNZ:554 CiPEHR water-table depth and build treatment obs CSV."""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PKG = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(PKG))

from lter_download import download_dataset_files  # noqa: E402

# WW column: c = ambient (control-side), w = snow-fence warmed (soil-warming side).
WW_TREATMENT = {"c": "control", "w": "soil_warming"}


def fetch_wtd_files(cache_dir: Path, *, force: bool = False) -> list[Path]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    return download_dataset_files(554, cache_dir, pattern=r"554_CiPEHR_WTD_", force=force)


def _parse_date(raw: str) -> datetime | None:
    raw = raw.strip()
    for fmt in ("%Y/%m/%d", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _load_wtd_file(path: Path) -> list[dict]:
    rows = []
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            dt = _parse_date(row.get("Date", ""))
            if dt is None:
                continue
            ww = row.get("WW", "").strip().lower()
            if ww not in WW_TREATMENT:
                continue
            try:
                wtd = float(row["WTD"])
            except (KeyError, ValueError):
                continue
            rows.append({
                "year": dt.year,
                "month": dt.month,
                "treatment": WW_TREATMENT[ww],
                "wtd_cm": wtd,
                "block": row.get("Block", "").strip().upper(),
            })
    return rows


def build_water_table_obs(cache_dir: Path, obs_path: Path) -> dict:
    files = fetch_wtd_files(cache_dir / "bnz554")
    all_rows: list[dict] = []
    for path in sorted(files):
        all_rows.extend(_load_wtd_file(path))

    # Summer (Jun–Aug) mean depth by year and treatment.
    summer: dict[tuple[int, str], list[float]] = defaultdict(list)
    for row in all_rows:
        if row["month"] in (6, 7, 8):
            summer[(row["year"], row["treatment"])].append(row["wtd_cm"])

    obs_path.parent.mkdir(parents=True, exist_ok=True)
    summary: dict[str, dict[int, dict]] = defaultdict(dict)
    with obs_path.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["year", "treatment", "mean_wtd_cm", "se_cm", "n_measurements"])
        for (year, treatment) in sorted(summer):
            values = summer[(year, treatment)]
            mean = float(sum(values) / len(values))
            se = _se(values)
            writer.writerow([year, treatment, f"{mean:.3f}", f"{se:.3f}", len(values)])
            summary[treatment][year] = {"mean_cm": mean, "se_cm": se, "n": len(values)}

    meta = {
        "source": "bnz554_cipehr_wtd",
        "n_files": len(files),
        "years": sorted({y for y, _ in summer}),
        "treatments": {t: summary[t] for t in sorted(summary)},
        "obs_csv": str(obs_path),
    }
    obs_path.with_suffix(".provenance.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def _se(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(var / len(values))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=PKG / "data/cache")
    parser.add_argument(
        "--obs", type=Path, default=PKG / "obs/bnz554-water-table-by-treatment.csv")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    meta = build_water_table_obs(args.cache, args.obs)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
