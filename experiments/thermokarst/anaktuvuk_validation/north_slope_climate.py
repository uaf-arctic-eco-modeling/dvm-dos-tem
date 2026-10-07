"""Build North Slope monthly TEM climate for Anaktuvuk Phase 1."""
from __future__ import annotations

import csv
import json
import shutil
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

# Barrow / Utqiaġvik monthly climatology (NWS USW00027502; Streletskiy et al. 2016).
BARROW_MONTHLY_TAIR = np.array([-26.4, -25.0, -22.0, -14.0, -3.0, 3.0, 4.5, 4.0,
                                0.0, -8.0, -18.0, -24.0])
# Inland North Slope (Anaktuvuk) is warmer than coastal Barrow (Jones et al. 2024 ~ -9 C).
INLAND_TAIR_BIAS_C = 7.5
BARROW_MONTHLY_PRECIP = np.array([5., 4.5, 4., 5., 7., 12., 14., 12., 8., 6., 5., 5.])
BARROW_MONTHLY_NIRR = np.array([0., 1., 4., 12., 18., 20., 16., 10., 4., 1., 0., 0.])

# Stage B snow target: ~7 cm peak at scale 1.0 with bundled North Slope precip (~82 mm yr⁻¹).
DEFAULT_WINTER_PRECIP_SCALE = 1.0


def scale_winter_precip(tair_c: np.ndarray, precip_mm: np.ndarray,
                        scale: float = DEFAULT_WINTER_PRECIP_SCALE) -> np.ndarray:
    """Scale precipitation in snow months (tair ≤ 0 °C) only."""
    if scale == 1.0:
        return np.asarray(precip_mm, float)
    tair_c = np.asarray(tair_c, float)
    precip_mm = np.asarray(precip_mm, float)
    scaled = precip_mm.copy()
    scaled[tair_c <= 0.0] *= scale
    return scaled

# Toolik demo historic file uses calendar year 1901 as index 0.
TR_CALENDAR_START = 2007
TR_YEARS = 15
TR_SLICE_START = TR_CALENDAR_START - 1901

NCEI_BARROW_URL = (
    "https://www.ncei.noaa.gov/access/services/data/v1"
    "?dataset=daily-summaries"
    "&stations=USW00027502"
    "&startDate=1990-01-01"
    "&endDate=2023-12-31"
    "&dataTypes=TMAX,TMIN,PRCP"
    "&units=metric"
    "&format=csv"
)


@dataclass
class BuildReport:
    source: str
    template_path: str
    full_climate_path: str
    tr_climate_path: str
    tr_slice_start: int
    tr_years: int
    mean_annual_tair_C: float
    notes: list[str]

    def to_dict(self):
        return asdict(self)


def load_obs_csv(path: Path) -> list[tuple[int, int, float, float]]:
    rows = []
    with path.open() as stream:
        for line in stream:
            if line.startswith("#") or not line.strip():
                continue
            rows.append(line)
    records = []
    for row in csv.DictReader(rows):
        records.append((
            int(row["year"]),
            int(row["month"]),
            float(row["tair_C"]),
            float(row["precip_mm"]),
        ))
    return records


def fetch_ncei_barrow(cache_path: Path) -> Path | None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and cache_path.stat().st_size > 500:
        return cache_path
    try:
        with urllib.request.urlopen(NCEI_BARROW_URL, timeout=120) as response:
            cache_path.write_bytes(response.read())
        return cache_path
    except Exception:
        return None


def aggregate_daily_csv(path: Path) -> list[tuple[int, int, float, float]]:
    monthly_t: dict[tuple[int, int], list[float]] = {}
    monthly_p: dict[tuple[int, int], float] = {}
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            try:
                year = int(row["DATE"][:4])
                month = int(row["DATE"][5:7])
                tmax = float(row["TMAX"]) if row["TMAX"] not in ("", "9999") else np.nan
                tmin = float(row["TMIN"]) if row["TMIN"] not in ("", "9999") else np.nan
                prcp = float(row["PRCP"]) if row["PRCP"] not in ("", "9999") else 0.0
            except (KeyError, ValueError):
                continue
            parts = [v for v in (tmax, tmin) if np.isfinite(v)]
            if not parts:
                continue
            key = (year, month)
            monthly_t.setdefault(key, []).append(float(np.mean(parts)))
            monthly_p[key] = monthly_p.get(key, 0.0) + prcp
    return [
        (year, month, float(np.mean(monthly_t[key])), float(monthly_p.get(key, 0.0)))
        for key in sorted(monthly_t)
    ]


def annual_anomalies(records: list[tuple[int, int, float, float]]):
    clim_ann = float(BARROW_MONTHLY_TAIR.mean())
    by_year: dict[int, list[float]] = {}
    for year, _month, tair, _precip in records:
        by_year.setdefault(year, []).append(tair)
    return {year: float(np.mean(vals)) - clim_ann for year, vals in by_year.items()}


def make_full_north_slope_climate(
    template: Path,
    dest: Path,
    obs_csv: Path,
    cache_dir: Path,
    inland_bias_c: float = INLAND_TAIR_BIAS_C,
) -> BuildReport:
    """Bias-correct Toolik monthly tair to Barrow/North Slope climatology."""
    notes: list[str] = []
    records = load_obs_csv(obs_csv)
    ncei = fetch_ncei_barrow(cache_dir / "ncei-barrow-daily.csv")
    if ncei is not None:
        ncei_records = aggregate_daily_csv(ncei)
        if ncei_records:
            records = ncei_records
            notes.append("NOAA NCEI USW00027502 daily aggregated to monthly")
        else:
            notes.append("NOAA fetch empty; using bundled obs CSV")
    else:
        notes.append("NOAA fetch unavailable; using bundled obs CSV")

    anomalies = annual_anomalies(records)
    clim_ann = float(BARROW_MONTHLY_TAIR.mean())
    shutil.copy2(template, dest)
    with Dataset(template) as src, Dataset(dest, "r+") as dst:
        toolik = np.asarray(src["tair"][:, 0, 0], float)
        nmonths = toolik.size
        nyears = nmonths // 12
        t2 = toolik.reshape(nyears, 12)
        toolik_ann = t2.mean(axis=1)
        toolik_clim_ann = float(t2.mean())
        new = np.zeros_like(toolik)
        for y in range(nyears):
            year = 1901 + y
            monthly = BARROW_MONTHLY_TAIR.copy() + inland_bias_c
            if year in anomalies:
                monthly += anomalies[year]
            elif year in {yr for yr, *_ in records}:
                obs_years = sorted({yr for yr, *_ in records})
                nearest = min(obs_years, key=lambda yr: abs(yr - year))
                monthly += anomalies.get(nearest, 0.0)
            else:
                monthly += (toolik_ann[y] - toolik_clim_ann) * 0.25
            new[y * 12:(y + 1) * 12] = monthly
        ny, nx = dst["tair"].shape[1], dst["tair"].shape[2]
        dst["tair"][:] = new[:, None, None]
        precip_scale = float(BARROW_MONTHLY_PRECIP.sum() / max(1.0, np.mean(src["precip"][:12, 0, 0]) * 12))
        precip_scale = np.clip(precip_scale, 0.35, 0.75)
        dst["precip"][:] = np.asarray(src["precip"][:], float) * precip_scale
        if "nirr" in dst.variables:
            for i in range(nmonths):
                dst["nirr"][i, :, :] = BARROW_MONTHLY_NIRR[i % 12]
        if "vapor_press" in dst.variables:
            dst["vapor_press"][:] = 100.0

    report = BuildReport(
        source="NOAA Barrow + bundled obs" if ncei else "bundled obs CSV",
        template_path=str(template),
        full_climate_path=str(dest),
        tr_climate_path="",
        tr_slice_start=TR_SLICE_START,
        tr_years=TR_YEARS,
        mean_annual_tair_C=float(BARROW_MONTHLY_TAIR.mean() + inland_bias_c),
        notes=notes + [f"inland tair bias +{inland_bias_c:.1f} C"],
    )
    return report


def make_tr_climate_from_obs(template: Path, dest: Path, obs_csv: Path,
                             start_year: int = TR_CALENDAR_START,
                             nyears: int = TR_YEARS,
                             inland_bias_c: float = INLAND_TAIR_BIAS_C,
                             winter_precip_scale: float = DEFAULT_WINTER_PRECIP_SCALE) -> BuildReport:
    """Build a standalone TR climate file (e.g. 2007–2021) from bundled monthly obs."""
    records = load_obs_csv(obs_csv)
    by_ym = {(year, month): (tair, precip) for year, month, tair, precip in records}
    shutil.copy2(template, dest)
    monthly_tair = []
    monthly_precip = []
    monthly_tair_raw = []
    with Dataset(dest, "r+") as dataset:
        ny, nx = dataset["tair"].shape[1], dataset["tair"].shape[2]
        nmonths = nyears * 12
        for year in range(start_year, start_year + nyears):
            for month in range(1, 13):
                if (year, month) in by_ym:
                    tair, precip = by_ym[(year, month)]
                    tair += inland_bias_c
                else:
                    tair = float(BARROW_MONTHLY_TAIR[month - 1] + inland_bias_c)
                    precip = float(BARROW_MONTHLY_PRECIP[month - 1])
                monthly_tair_raw.append(tair)
                monthly_precip.append(precip)
                monthly_tair.append(tair)
        monthly_precip = scale_winter_precip(
            np.asarray(monthly_tair_raw, float),
            np.asarray(monthly_precip, float),
            winter_precip_scale,
        )
        for idx in range(nmonths):
            tair = monthly_tair[idx]
            precip = float(monthly_precip[idx])
            month = idx % 12
            dataset["tair"][idx, :, :] = tair
            dataset["precip"][idx, :, :] = precip
            dataset["nirr"][idx, :, :] = BARROW_MONTHLY_NIRR[month]
            if "vapor_press" in dataset.variables:
                dataset["vapor_press"][idx, :, :] = 100.0
        for name in ["tair", "precip", "nirr", "vapor_press"]:
            if name in dataset.variables and dataset[name].shape[0] > nmonths:
                dataset[name][nmonths:] = 0.0
    ann = np.asarray(monthly_tair, float).reshape(nyears, 12).mean(axis=1)
    return BuildReport(
        source="bundled North Slope monthly obs CSV",
        template_path=str(template),
        full_climate_path="",
        tr_climate_path=str(dest),
        tr_slice_start=start_year - 1901,
        tr_years=nyears,
        mean_annual_tair_C=float(np.mean(ann)),
        notes=[
            f"standalone TR {start_year}–{start_year + nyears - 1}",
            f"inland tair bias +{inland_bias_c:.1f} C",
            f"winter precip scale ×{winter_precip_scale:.3f} (snow months only)",
        ],
    )


def write_build_report(path: Path, report: BuildReport):
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n")


def append_obs_years_from_ncei(
    obs_csv: Path,
    cache_dir: Path,
    *,
    start_year: int,
    end_year: int,
) -> int:
    """Append monthly rows for ``start_year``–``end_year`` from NOAA Barrow daily data."""
    ncei = fetch_ncei_barrow(cache_dir / "ncei-barrow-daily.csv")
    if ncei is None:
        return 0
    monthly = {
        (year, month): (tair, precip)
        for year, month, tair, precip in aggregate_daily_csv(ncei)
        if start_year <= year <= end_year
    }
    if not monthly:
        return 0
    existing = load_obs_csv(obs_csv)
    existing_keys = {(year, month) for year, month, *_ in existing}
    new_rows = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if (year, month) in existing_keys:
                continue
            if (year, month) in monthly:
                tair, precip = monthly[(year, month)]
                source = "ncei_barrow"
            else:
                tair = float(BARROW_MONTHLY_TAIR[month - 1])
                precip = float(BARROW_MONTHLY_PRECIP[month - 1])
                source = "barrow_climatology"
            new_rows.append((year, month, tair, precip, source))
    if not new_rows:
        return 0
    with obs_csv.open("a") as stream:
        for year, month, tair, precip, source in new_rows:
            stream.write(f"{year},{month},{tair},{precip},{source}\n")
    return len(new_rows)


def read_climate_monthly(path: Path) -> dict[str, np.ndarray]:
    """Return monthly tair/precip/nirr/vapor_press arrays (nmonths,)."""
    with Dataset(path) as dataset:
        n = dataset["tair"].shape[0]
        return {
            "tair": np.asarray(dataset["tair"][:n, 0, 0], float),
            "precip": np.asarray(dataset["precip"][:n, 0, 0], float),
            "nirr": np.asarray(dataset["nirr"][:n, 0, 0], float),
            "vapor_press": np.asarray(dataset["vapor_press"][:n, 0, 0], float),
            "nmonths": n,
        }


def monthly_climatology_from_tr(tr_path: Path, tr_years: int) -> dict[str, np.ndarray]:
    """Average each calendar month over ``tr_years`` in a standalone TR NetCDF."""
    data = read_climate_monthly(tr_path)
    nmonths = min(tr_years * 12, data["nmonths"])
    clim = {}
    for key in ("tair", "precip", "nirr", "vapor_press"):
        series = data[key][:nmonths].reshape(tr_years, 12)
        clim[key] = series.mean(axis=0)
    clim["notes"] = [f"monthly mean over {tr_years} TR years from {tr_path.name}"]
    return clim


def willmot_monthly_rain_snow(tair_c: np.ndarray, precip_mm: np.ndarray):
    """Monthly rain/snow water (mm mo⁻¹) using the model's Willmott split."""
    tair_c = np.asarray(tair_c, float)
    precip_mm = np.asarray(precip_mm, float)
    rain = np.where(tair_c > 0.0, precip_mm, 0.0)
    snow = np.where(tair_c <= 0.0, precip_mm, 0.0)
    return rain, snow


def write_monthly_climate(template: Path, dest: Path, blocks: list[dict[str, np.ndarray]]):
    """Write one or more 12-month blocks into a climate NetCDF."""
    shutil.copy2(template, dest)
    nmonths = 12 * len(blocks)
    with Dataset(dest, "r+") as dataset:
        ny, nx = dataset["tair"].shape[1], dataset["tair"].shape[2]
        for bi, block in enumerate(blocks):
            for month in range(12):
                idx = bi * 12 + month
                dataset["tair"][idx, :, :] = block["tair"][month]
                dataset["precip"][idx, :, :] = block["precip"][month]
                dataset["nirr"][idx, :, :] = block["nirr"][month]
                if "vapor_press" in dataset.variables:
                    dataset["vapor_press"][idx, :, :] = block["vapor_press"][month]
        for name in ("tair", "precip", "nirr", "vapor_press"):
            if name in dataset.variables and dataset[name].shape[0] > nmonths:
                dataset[name][nmonths:] = 0.0
    return dest


def make_repeated_seasonal_climate(
    template: Path,
    dest: Path,
    clim: dict[str, np.ndarray],
    repeat_years: int,
) -> Path:
    """Copy a 12-month climatology ``repeat_years`` times (SP spin-up forcing)."""
    block = {k: clim[k] for k in ("tair", "precip", "nirr", "vapor_press")}
    write_monthly_climate(template, dest, [block] * repeat_years)
    return dest


def make_combined_transient_climate(
    template: Path,
    dest: Path,
    tr_path: Path,
    *,
    seasonal_repeat_years: int = 20,
    tr_years: int = 24,
) -> tuple[Path, dict[str, np.ndarray], int]:
    """Build hist climate: ``seasonal_repeat_years`` of mean seasonal cycle + ``tr_years`` historic TR."""
    clim = monthly_climatology_from_tr(tr_path, tr_years)
    tr_data = read_climate_monthly(tr_path)
    n_tr = min(tr_years * 12, tr_data["nmonths"])
    tr_block = {
        "tair": tr_data["tair"][:n_tr].reshape(tr_years, 12),
        "precip": tr_data["precip"][:n_tr].reshape(tr_years, 12),
        "nirr": tr_data["nirr"][:n_tr].reshape(tr_years, 12),
        "vapor_press": tr_data["vapor_press"][:n_tr].reshape(tr_years, 12),
    }
    seasonal_block = {k: clim[k] for k in ("tair", "precip", "nirr", "vapor_press")}
    blocks = [seasonal_block] * seasonal_repeat_years + [
        {k: tr_block[k][y] for k in tr_block} for y in range(tr_years)
    ]
    write_monthly_climate(template, dest, blocks)
    tr_start_yr = seasonal_repeat_years
    return dest, clim, tr_start_yr


def plot_seasonal_forcing(
    clim: dict[str, np.ndarray],
    out_path: Path,
    *,
    title: str = "Anaktuvuk seasonal mean forcing (24-yr TR average)",
) -> Path:
    """Six-panel seasonal cycle: tair, precip, rain, snow, nirr, vapor pressure."""
    import matplotlib.pyplot as plt

    months = np.arange(1, 13)
    month_labels = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
    rain, snow = willmot_monthly_rain_snow(clim["tair"], clim["precip"])
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 5.8), layout="constrained")
    panels = [
        (axes[0, 0], clim["tair"], "Air temperature (°C)", "#D55E00"),
        (axes[0, 1], clim["precip"], "Precipitation (mm mo⁻¹)", "#4C78A8"),
        (axes[0, 2], rain, "Rain (mm mo⁻¹)", "#1F6F5F"),
        (axes[1, 0], snow, "Snowfall (mm mo⁻¹)", "#777772"),
        (axes[1, 1], clim["nirr"], "Shortwave (W m⁻²)", "#EECA3B"),
        (axes[1, 2], clim["vapor_press"], "Vapor pressure (hPa)", "#8C6DAB"),
    ]
    for ax, values, ylabel, color in panels:
        ax.plot(months, values, "o-", color=color, lw=1.6, ms=4)
        ax.set(xticks=months, xticklabels=month_labels, xlabel="Month",
               ylabel=ylabel, xlim=(0.8, 12.2))
        ax.grid(color="#E4E7E5", lw=0.6)
    fig.suptitle(title, fontsize=10)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(out_path.with_suffix(f".{ext}"), dpi=240, bbox_inches="tight")
    plt.close(fig)
    return out_path.with_suffix(".png")
