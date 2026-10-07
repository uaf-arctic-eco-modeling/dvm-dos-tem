"""Build EML / Healy TEM monthly climate from BNZ:453 or NOAA Healy fallback."""
from __future__ import annotations

import csv
import json
import shutil
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

from lter_download import download_file

TR_START = 2004
TR_END = 2018
TR_YEARS = TR_END - TR_START + 1
DINM = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

# Rodenhizer CiPEHR treatment air-temperature biases (°C) applied to monthly tair.
TREATMENT_BIAS = {
    "control": {"winter": 0.0, "summer": 0.0},
    "air_warming": {"winter": 0.0, "summer": 0.3},
    "soil_warming": {"winter": 2.5, "summer": 1.5},
    "air_soil_warming": {"winter": 2.8, "summer": 1.8},
}
# Snow-fence insulation proxy: extra nonsummer warming on soil-warming treatments
# (Rodenhizer: +1.49 °C surface nonsummer after 7 yr; deep soil +0.78 °C summer).
SNOW_FENCE_WINTER_EXTRA_C = 1.5
SOIL_WARMING_TREATMENTS = ("soil_warming", "air_soil_warming")
SUMMER_MONTHS = {5, 6, 7, 8, 9}
WINTER_MONTHS = {10, 11, 12, 1, 2, 3, 4}

# CiPEHR snow-pack precipitation proxy (Phase 5+): target peak snow depth and seasonality.
# SWE is distributed Oct–Apr when monthly tair ≤ 0 °C; peak before May melt.
# ~110 mm SWE ≈ 40 cm depth at settled snow density (~275 kg m⁻³) after compaction.
CIPEHR_SNOW_ACCUM_MONTHS = (10, 11, 12, 1, 2, 3, 4)
# Late-heavy weights: peak snow depth in April–May, ablation June (control).
CIPEHR_SNOW_ACCUM_WEIGHTS = {
    10: 0.04, 11: 0.06, 12: 0.09, 1: 0.12, 2: 0.16, 3: 0.20, 4: 0.33,
}
CIPEHR_SNOW_TARGET_PEAK_CM = 40.0
CIPEHR_SOIL_SNOW_DEPTH_MULTIPLIER = 2.0
CIPEHR_SNOW_VALIDATION_START = 2009
CIPEHR_SNOW_VALIDATION_END = 2018
CIPEHR_DEFAULT_ANNUAL_SWE_MM = 100.0
# Extra May warming on soil-warming treatments to complete melt by end of May (fence removal).
CIPEHR_SOIL_MAY_MELT_EXTRA_C = 4.0

NCEI_HEALY_URL = (
    "https://www.ncei.noaa.gov/access/services/data/v1"
    "?dataset=daily-summaries"
    "&stations=USC00503585"
    "&startDate=2004-01-01"
    "&endDate=2018-12-31"
    "&dataTypes=TMAX,TMIN,PRCP"
    "&units=metric"
    "&format=csv"
)


@dataclass
class BuildReport:
    source: str
    monthly_csv: str
    template_path: str
    output_path: str
    treatment: str
    start_year: int
    nyears: int
    mean_annual_tair_C: float
    mean_annual_precip_mm: float
    notes: list[str]

    def to_dict(self):
        return asdict(self)


def fetch_ncei_healy_daily(cache_path: Path) -> Path:
    """Download NOAA daily summaries for Healy, AK (USC00503585)."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and cache_path.stat().st_size > 500:
        return cache_path
    with urllib.request.urlopen(NCEI_HEALY_URL, timeout=120) as response:
        cache_path.write_bytes(response.read())
    return cache_path


BNZ453_FILES = (
    "453_EML_AK_weather_data_2004-2009.csv",
    "453_EML_AK_weather_data_2009-2011.csv",
    "453_EML_AK_weather_data_2011-2012.csv",
    "453_EML_AK_weather_data_2012-2013.csv",
    "453_EML_AK_weather_data_2013-2014.csv",
    "453_EML_AK_weather_data_2014-2015.csv",
    "453_EML_AK_weather_data_2015-2016.csv",
    "453_EML_AK_Weather_data_2016-2017.csv",
    "453_EML_AK_Weather_data_2017-2018.csv",
)


def fetch_bnz453_hourly(cache_dir: Path, *, force: bool = False) -> list[Path]:
    """Download BNZ:453 EML site hourly met CSVs (2004–2018)."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in BNZ453_FILES:
        paths.append(download_file(name, cache_dir / name, force=force))
    return paths


def _month_from_doy(year: int, doy: int) -> int:
    dt = datetime(year, 1, 1) + timedelta(days=int(doy) - 1)
    return dt.month


def aggregate_bnz453_hourly(paths: list[Path]) -> list[tuple[int, int, float, float]]:
    """Aggregate BNZ:453 hourly Tair/Precip to monthly means and totals."""
    monthly_t: dict[tuple[int, int], list[float]] = {}
    monthly_p: dict[tuple[int, int], float] = {}
    for path in sorted(paths):
        with path.open(newline="") as stream:
            reader = csv.DictReader(stream)
            for row in reader:
                try:
                    year = int(float(row["Year"]))
                    doy = int(float(row["DOY"]))
                    tair = float(row["Tair"])
                    precip = float(row["Precip"]) if row["Precip"] not in ("", "NA") else 0.0
                except (KeyError, ValueError, TypeError):
                    continue
                if not np.isfinite(tair):
                    continue
                month = _month_from_doy(year, doy)
                key = (year, month)
                monthly_t.setdefault(key, []).append(tair)
                monthly_p[key] = monthly_p.get(key, 0.0) + precip
    records = []
    for key in sorted(monthly_t):
        year, month = key
        records.append((
            year,
            month,
            float(np.mean(monthly_t[key])),
            float(monthly_p.get(key, 0.0)),
        ))
    return records


def aggregate_daily_csv(path: Path) -> list[tuple[int, int, float, float]]:
    """Return (year, month, tair_C, precip_mm) monthly records."""
    monthly_t = {}
    monthly_p = {}
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            date = row["DATE"]
            year = int(date[:4])
            month = int(date[5:7])
            try:
                tmax = float(row["TMAX"]) if row["TMAX"] not in ("", "9999") else np.nan
                tmin = float(row["TMIN"]) if row["TMIN"] not in ("", "9999") else np.nan
                prcp = float(row["PRCP"]) if row["PRCP"] not in ("", "9999") else 0.0
            except (KeyError, ValueError):
                continue
            parts = [v for v in (tmax, tmin) if np.isfinite(v)]
            if not parts:
                continue
            tmean = float(np.mean(parts))
            key = (year, month)
            monthly_t.setdefault(key, []).append(tmean)
            monthly_p[key] = monthly_p.get(key, 0.0) + prcp
    records = []
    for key in sorted(monthly_t):
        year, month = key
        records.append((
            year,
            month,
            float(np.mean(monthly_t[key])),
            float(monthly_p.get(key, 0.0)),
        ))
    return records


def write_monthly_csv(path: Path, records: list[tuple[int, int, float, float]], source: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["year", "month", "tair_C", "precip_mm", "source"])
        for year, month, tair, precip in records:
            writer.writerow([year, month, f"{tair:.3f}", f"{precip:.3f}", source])


def load_monthly_csv(path: Path) -> list[tuple[int, int, float, float]]:
    rows = list(csv.DictReader(path.open()))
    return [
        (int(r["year"]), int(r["month"]), float(r["tair_C"]), float(r["precip_mm"]))
        for r in rows
    ]


def monthly_climatology(records: list[tuple[int, int, float, float]]):
    """12-month mean tair/precip from observed monthly records."""
    by_month = {m: {"t": [], "p": []} for m in range(1, 13)}
    for _year, month, tair, precip in records:
        by_month[month]["t"].append(tair)
        by_month[month]["p"].append(precip)
    tair = np.array([float(np.mean(by_month[m]["t"])) for m in range(1, 13)])
    precip = np.array([float(np.mean(by_month[m]["p"])) for m in range(1, 13)])
    return tair, precip


def expand_records(records: list[tuple[int, int, float, float]], nyears: int):
    """Tile 2004–2018 observations to ``nyears`` calendar years."""
    by_year = {}
    for year, month, tair, precip in records:
        by_year.setdefault(year, {})[month] = (tair, precip)
    obs_years = sorted(by_year)
    if not obs_years:
        raise ValueError("no monthly records to expand")
    tair = np.zeros(nyears * 12)
    precip = np.zeros(nyears * 12)
    for i in range(nyears):
        src_year = obs_years[i % len(obs_years)]
        for month in range(1, 13):
            if month in by_year[src_year]:
                t, p = by_year[src_year][month]
            else:
                t, p = np.nan, 0.0
            idx = i * 12 + (month - 1)
            tair[idx] = t
            precip[idx] = p
    good = np.isfinite(tair)
    if not np.all(good):
        fill = monthly_climatology(records)[0]
        for i in range(nyears):
            for month in range(12):
                idx = i * 12 + month
                if not np.isfinite(tair[idx]):
                    tair[idx] = fill[month]
    return tair, precip


def estimate_nirr(tair: np.ndarray, template: Path, y=0, x=0):
    """Use template monthly nirr shape scaled to Healy summer warmth."""
    with Dataset(template) as src:
        if "nirr" in src.variables and src["nirr"].shape[0] >= 12:
            base = np.asarray(src["nirr"][:12, y, x], float)
        else:
            base = np.array([0, 2, 6, 14, 20, 22, 18, 12, 6, 2, 0, 0], float)
    nyears = len(tair) // 12
    nirr = np.tile(base, nyears)
    warm = float(np.mean(tair[tair > 0])) if np.any(tair > 0) else 10.0
    scale = np.clip(warm / 12.0, 0.8, 1.4)
    return nirr * scale


def treatment_bias_table(
    profile: str = "default",
    *,
    winter_extra_c: float | None = None,
    summer_extra_c: float = 0.0,
) -> dict[str, dict[str, float]]:
    """Return treatment bias dict; ``snow_fence`` adds winter insulation proxy."""
    import copy
    bias = copy.deepcopy(TREATMENT_BIAS)
    if profile == "snow_fence":
        extra_winter = (
            SNOW_FENCE_WINTER_EXTRA_C if winter_extra_c is None else winter_extra_c)
        for treatment in SOIL_WARMING_TREATMENTS:
            bias[treatment]["winter"] += extra_winter
            bias[treatment]["summer"] += summer_extra_c
    return bias


def apply_treatment_bias(
    tair: np.ndarray,
    treatment: str,
    scale: float = 1.0,
    *,
    bias_table: dict[str, dict[str, float]] | None = None,
    may_melt_extra_c: float = 0.0,
    snow_profile: str | None = None,
):
    """Add CiPEHR warming bias to monthly air temperature.

    With ``snow_profile='cipehr'``, winter (Oct–Apr) bias is not scaled so
    synthetic snow precipitation still passes the rain/snow split; scaled
    warming applies May–September only. Soil-warming May gets ``may_melt_extra_c``
    to complete melt by end of May (fence removal).
    """
    bias_table = bias_table or TREATMENT_BIAS
    if treatment not in bias_table:
        raise KeyError(f"unknown treatment {treatment}")
    bias = bias_table[treatment]
    out = tair.copy()
    nyears = len(out) // 12
    winter_scale = 1.0 if snow_profile == "cipehr" else scale
    summer_scale = scale
    for year in range(nyears):
        for month in range(12):
            cal_month = month + 1
            idx = year * 12 + month
            if cal_month in SUMMER_MONTHS:
                out[idx] += bias["summer"] * summer_scale
                if cal_month == 5 and may_melt_extra_c != 0.0:
                    out[idx] += may_melt_extra_c
            elif cal_month in WINTER_MONTHS:
                out[idx] += bias["winter"] * winter_scale
    return out


def apply_cipehr_snow_precip(
    precip: np.ndarray,
    *,
    treatment: str,
    start_year: int,
    annual_swe_mm: float = CIPEHR_DEFAULT_ANNUAL_SWE_MM,
    target_peak_cm: float = CIPEHR_SNOW_TARGET_PEAK_CM,
    soil_multiplier: float = CIPEHR_SOIL_SNOW_DEPTH_MULTIPLIER,
    validation_start: int = CIPEHR_SNOW_VALIDATION_START,
    validation_end: int = CIPEHR_SNOW_VALIDATION_END,
    summer_months: tuple[int, ...] = (5, 6, 7, 8, 9),
    summer_climatology: np.ndarray | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Replace cold-season precip with synthetic snow SWE for the validation window.

    Control and air-warming: ``annual_swe_mm`` scaled to ``target_peak_cm``.
    Soil-warming treatments: multiply by ``soil_multiplier`` (default 2× → ~80 cm peak).
    May–September keep observed (mostly rain) totals unchanged.
    """
    out = precip.copy()
    notes: list[str] = []
    if treatment in SOIL_WARMING_TREATMENTS:
        swe_budget = annual_swe_mm * soil_multiplier
        notes.append(
            f"snow SWE {swe_budget:.1f} mm yr⁻¹ ({soil_multiplier:.1f}×, "
            f"target ~{target_peak_cm * soil_multiplier:.0f} cm peak)")
    else:
        swe_budget = annual_swe_mm
        notes.append(f"snow SWE {swe_budget:.1f} mm yr⁻¹ (target ~{target_peak_cm:.0f} cm peak)")

    weight_sum = sum(CIPEHR_SNOW_ACCUM_WEIGHTS[m] for m in CIPEHR_SNOW_ACCUM_MONTHS)
    nyears = len(out) // 12
    for yi in range(nyears):
        cal_year = start_year + yi
        if cal_year < validation_start or cal_year > validation_end:
            continue
        for month in range(1, 13):
            idx = yi * 12 + (month - 1)
            if month in CIPEHR_SNOW_ACCUM_MONTHS:
                frac = CIPEHR_SNOW_ACCUM_WEIGHTS[month] / weight_sum
                out[idx] = swe_budget * frac
            elif month in summer_months and summer_climatology is not None:
                out[idx] = float(summer_climatology[month - 1])
            elif month not in summer_months:
                out[idx] = 0.0
    if summer_climatology is not None:
        notes.append("May–Sep rain: monthly climatology (uniform validation years)")
    return out, notes


def write_tem_climate(template, dest, tair, precip, nirr, vapor=100.0, y=0, x=0):
    shutil.copy2(template, dest)
    nmonths = len(tair)
    with Dataset(dest, "r+") as dst:
        for name in ("tair", "precip", "nirr", "vapor_press"):
            if name not in dst.variables:
                continue
            shape = list(dst[name].shape)
            shape[0] = nmonths
            data = np.zeros(shape, dtype=np.float64)
            if name == "tair":
                values = tair
            elif name == "precip":
                values = precip
            elif name == "nirr":
                values = nirr
            else:
                values = np.full(nmonths, vapor)
            for t in range(nmonths):
                data[t, y, x] = values[t]
            dst[name][:] = data
    return dest


def prepare_monthly_csv(cache_dir: Path, obs_dir: Path, *, force: bool = False) -> tuple[Path, str]:
    """Fetch EML site met and write monthly CSV; return path and source label."""
    monthly = obs_dir / "eml_healy_monthly_2004-2018.csv"
    notes: list[str] = []
    source = "ncei_usc00503585_healy_fallback"
    records: list[tuple[int, int, float, float]] = []
    try:
        bnz_dir = cache_dir / "bnz453"
        hourly = fetch_bnz453_hourly(bnz_dir, force=force)
        records = aggregate_bnz453_hourly(hourly)
        if len(records) >= 120:
            source = "bnz453_eml_hourly_lter"
            notes.append(f"BNZ:453 EML site hourly met ({len(hourly)} files)")
        else:
            notes.append(f"BNZ:453 parse yielded only {len(records)} months; falling back")
            records = []
    except Exception as exc:
        notes.append(f"BNZ:453 fetch failed ({exc}); falling back to NOAA Healy")
        records = []
    if not records:
        daily = fetch_ncei_healy_daily(cache_dir / "ncei_healy_daily_2004-2018.csv")
        records = aggregate_daily_csv(daily)
        notes.append("NOAA Healy daily (USC00503585) town station fallback")
    write_monthly_csv(monthly, records, source)
    provenance = {
        "source": source,
        "ncei_url": NCEI_HEALY_URL,
        "notes": notes,
        "n_months": len(records),
    }
    monthly.with_suffix(".provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n")
    return monthly, source


def build_eml_climate(
    template: Path,
    output: Path,
    monthly_csv: Path,
    *,
    treatment: str = "control",
    nyears: int = 40,
    start_year: int = TR_START,
    bias_scale: float = 1.0,
    bias_profile: str = "default",
    bias_table: dict[str, dict[str, float]] | None = None,
    winter_extra_c: float | None = None,
    summer_extra_c: float = 0.0,
    snow_profile: str | None = None,
    annual_snow_swe_mm: float = CIPEHR_DEFAULT_ANNUAL_SWE_MM,
    snow_target_peak_cm: float = CIPEHR_SNOW_TARGET_PEAK_CM,
    soil_snow_multiplier: float = CIPEHR_SOIL_SNOW_DEPTH_MULTIPLIER,
    soil_may_melt_extra_c: float = CIPEHR_SOIL_MAY_MELT_EXTRA_C,
):
    """Write treatment-biased TEM climate NetCDF."""
    table = bias_table or treatment_bias_table(
        bias_profile,
        winter_extra_c=winter_extra_c,
        summer_extra_c=summer_extra_c,
    )
    records = load_monthly_csv(monthly_csv)
    tair, precip = expand_records(records, nyears)
    _clim_tair, clim_precip = monthly_climatology(records)
    report_notes: list[str] = []
    if snow_profile == "cipehr":
        precip, snow_notes = apply_cipehr_snow_precip(
            precip,
            treatment=treatment,
            start_year=start_year,
            annual_swe_mm=annual_snow_swe_mm,
            target_peak_cm=snow_target_peak_cm,
            soil_multiplier=soil_snow_multiplier,
            summer_climatology=clim_precip,
        )
        report_notes.extend(snow_notes)
        may_extra = (
            soil_may_melt_extra_c if treatment in SOIL_WARMING_TREATMENTS else 0.0)
        tair = apply_treatment_bias(
            tair, treatment, scale=bias_scale, bias_table=table,
            may_melt_extra_c=may_extra, snow_profile=snow_profile)
    else:
        tair = apply_treatment_bias(tair, treatment, scale=bias_scale, bias_table=table)
    nirr = estimate_nirr(tair, template)
    write_tem_climate(template, output, tair, precip, nirr)
    note = f"treatment bias: {table[treatment]} (profile={bias_profile})"
    if bias_scale != 1.0:
        note += f" (scale={bias_scale:.2f})"
    if snow_profile:
        note += f"; snow_profile={snow_profile}"
    report_notes.insert(0, note)
    report = BuildReport(
        source="healy_monthly_csv",
        monthly_csv=str(monthly_csv),
        template_path=str(template),
        output_path=str(output),
        treatment=treatment,
        start_year=start_year,
        nyears=nyears,
        mean_annual_tair_C=float(tair.reshape(nyears, 12).mean(axis=1).mean()),
        mean_annual_precip_mm=float(precip.reshape(nyears, 12).sum(axis=1).mean()),
        notes=report_notes,
    )
    report_path = output.with_suffix(".build-report.json")
    report_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n")
    return report
