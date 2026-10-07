#!/usr/bin/env python3
"""Fetch EML meteorology for climate builder (BNZ:453 LTER, else NOAA Healy)."""
import argparse
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent
sys.path.insert(0, str(PKG))
from healy_climate import NCEI_HEALY_URL, fetch_bnz453_hourly, prepare_monthly_csv  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=PKG / "data/cache")
    parser.add_argument("--obs", type=Path, default=PKG / "obs")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    hourly = fetch_bnz453_hourly(args.cache / "bnz453", force=args.force)
    monthly, source = prepare_monthly_csv(args.cache, args.obs, force=args.force)
    out = {
        "monthly_csv": str(monthly),
        "source": source,
        "bnz453_files": [str(p) for p in hourly],
        "ncei_url": NCEI_HEALY_URL,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
