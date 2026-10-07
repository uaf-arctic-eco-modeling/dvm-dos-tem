#!/usr/bin/env python3
"""Write CiPEHR synthetic snow precipitation schedule to CSV for documentation."""
from __future__ import annotations

import csv
from pathlib import Path

from healy_climate import (
    CIPEHR_SNOW_ACCUM_MONTHS,
    CIPEHR_SNOW_ACCUM_WEIGHTS,
    CIPEHR_SNOW_VALIDATION_END,
    CIPEHR_SNOW_VALIDATION_START,
    CIPEHR_SOIL_SNOW_DEPTH_MULTIPLIER,
    apply_cipehr_snow_precip,
    load_monthly_csv,
)


def write_cipehr_snow_precip_csv(
    monthly_csv: Path,
    output: Path,
    *,
    annual_swe_mm: float = 110.0,
    validation_start: int = CIPEHR_SNOW_VALIDATION_START,
    validation_end: int = CIPEHR_SNOW_VALIDATION_END,
):
    """Export monthly precip (mm) for control vs soil-warming snow treatments."""
    records = load_monthly_csv(monthly_csv)
    by_year = {}
    for year, month, tair, precip in records:
        by_year.setdefault(year, {})[month] = (tair, precip)

    rows = []
    for year in range(validation_start, validation_end + 1):
        if year not in by_year:
            continue
        for month in range(1, 13):
            tair, obs_p = by_year[year].get(month, (float("nan"), 0.0))
            ctrl_p = obs_p
            soil_p = obs_p
            if month in CIPEHR_SNOW_ACCUM_MONTHS:
                wsum = sum(CIPEHR_SNOW_ACCUM_WEIGHTS[m] for m in CIPEHR_SNOW_ACCUM_MONTHS)
                frac = CIPEHR_SNOW_ACCUM_WEIGHTS[month] / wsum
                ctrl_p = annual_swe_mm * frac
                soil_p = annual_swe_mm * CIPEHR_SOIL_SNOW_DEPTH_MULTIPLIER * frac
            elif month not in (5, 6, 7, 8, 9):
                ctrl_p = soil_p = 0.0
            rows.append({
                "year": year,
                "month": month,
                "tair_obs_C": f"{tair:.3f}",
                "precip_obs_mm": f"{obs_p:.3f}",
                "precip_control_snow_mm": f"{ctrl_p:.3f}",
                "precip_soil_warming_snow_mm": f"{soil_p:.3f}",
                "accum_month": month in CIPEHR_SNOW_ACCUM_MONTHS,
            })

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return output


if __name__ == "__main__":
    pkg = Path(__file__).resolve().parent
    monthly = pkg / "obs/eml_healy_monthly_2004-2018.csv"
    out = pkg / "obs/eml_cipehr_snow_precip_2009-2018.csv"
    write_cipehr_snow_precip_csv(monthly, out)
    print(f"wrote {out}")
