#!/usr/bin/env python3
"""Build EML treatment climate NetCDF files from Healy monthly observations."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
sys.path.insert(0, str(PKG))

from healy_climate import (  # noqa: E402
    TREATMENT_BIAS,
    build_eml_climate,
    prepare_monthly_csv,
)

DEFAULT_TEMPLATE = (
    ROOT / "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/historic-climate.nc"
)
DEFAULT_OBS = PKG / "obs/eml_healy_monthly_2004-2018.csv"
DEFAULT_OUT = PKG / "data"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--monthly", type=Path, default=DEFAULT_OBS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--fetch", action="store_true",
                        help="Download NOAA Healy daily and aggregate monthly CSV first")
    parser.add_argument("--nyears", type=int, default=40)
    parser.add_argument("--treatment", choices=list(TREATMENT_BIAS) + ["all"], default="all")
    args = parser.parse_args()
    if not args.template.exists():
        raise SystemExit(f"template not found: {args.template}")
    if args.fetch or not args.monthly.exists():
        args.monthly, _ = prepare_monthly_csv(PKG / "data/cache", PKG / "obs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    treatments = list(TREATMENT_BIAS) if args.treatment == "all" else [args.treatment]
    reports = {}
    for treatment in treatments:
        out = args.output_dir / f"eml-climate-{treatment}.nc"
        report = build_eml_climate(
            args.template, out, args.monthly,
            treatment=treatment, nyears=args.nyears)
        reports[treatment] = report.to_dict()
        print(f"Wrote {out}", file=sys.stderr)
    summary = args.output_dir / "eml-climate-build-summary.json"
    summary.write_text(json.dumps(reports, indent=2) + "\n")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
