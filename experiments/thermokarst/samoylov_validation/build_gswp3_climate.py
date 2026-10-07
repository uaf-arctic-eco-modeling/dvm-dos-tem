#!/usr/bin/env python3
"""CLI for Samoylov GSWP3 + Boike bias-corrected TEM climate."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
sys.path.insert(0, str(PKG))
DEFAULT_TEMPLATE = ROOT / "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/historic-climate.nc"
DEFAULT_BOIKE = PKG / "obs/boike_samoylov_monthly_2002-2014.csv"
DEFAULT_OUTPUT = PKG / "samoylov-gswp3-climate.nc"

from gswp3_climate import (  # noqa: E402
    TR_START,
    TR_YEARS,
    build_samoylov_climate,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE,
                        help="TEM climate template NetCDF (grid metadata)")
    parser.add_argument("--gswp3", type=Path, default=None,
                        help="GSWP3 monthly NetCDF (lat/lon or Y/X). Omit to use CRU proxy.")
    parser.add_argument("--cru-proxy", type=Path, default=None,
                        help="CRU/proxy reanalysis when --gswp3 absent (default: --template)")
    parser.add_argument("--boike", type=Path, default=DEFAULT_BOIKE,
                        help="Boike monthly calibration CSV (2002–2014)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--start-year", type=int, default=TR_START)
    parser.add_argument("--nyears", type=int, default=TR_YEARS)
    parser.add_argument("--cal-start", type=int, default=2002)
    parser.add_argument("--cal-end", type=int, default=2014)
    parser.add_argument("--fetch", action="store_true",
                        help="Download GSWP3 global files and extract Samoylov point first")
    args = parser.parse_args()

    if not args.template.exists():
        raise SystemExit(f"template not found: {args.template}")

    gswp3_path = args.gswp3
    if args.fetch and gswp3_path is None:
        from fetch_gswp3_samoylov import (
            ALIASES, CACHE_NAMES, GSWP3_BASE, REMOTE,
            build_point_climate, download, extract_point_series,
        )
        cache = PKG / "data/cache"
        tas_global = cache / CACHE_NAMES["tas"]
        pr_global = cache / CACHE_NAMES["pr"]
        download(f"{GSWP3_BASE}/{REMOTE['tas']}", tas_global)
        download(f"{GSWP3_BASE}/{REMOTE['pr']}", pr_global)
        tas, _, _, _ = extract_point_series(tas_global, ALIASES["tas"], 72.3667, 126.4667)
        pr, _, _, _ = extract_point_series(pr_global, ALIASES["pr"], 72.3667, 126.4667)
        fetch_out = PKG / "data/gswp3_samoylov_point.nc"
        build_point_climate(tas, pr, args.template, fetch_out)
        gswp3_path = fetch_out

    report = build_samoylov_climate(
        args.template,
        args.output,
        gswp3_path=gswp3_path,
        boike_path=args.boike,
        cru_proxy_path=args.cru_proxy or args.template,
        start_year=args.start_year,
        nyears=args.nyears,
        cal_start=args.cal_start,
        cal_end=args.cal_end,
    )
    print(json.dumps(report.to_dict(), indent=2))
    print(f"Wrote {args.output}", file=sys.stderr)
    print(f"Build report {args.output.with_suffix('.build-report.json')}", file=sys.stderr)


if __name__ == "__main__":
    main()
