"""EML CiPEHR soil thermal contour plots (depth × time) for validation reports."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from netCDF4 import Dataset

ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = ROOT / "docs_src/thermokarst"
PROFILE_VARS = ("TLAYER", "LAYERDEPTH", "LAYERDZ")
DAILY_OVERLAY = ("TKSUBSIDENCE", "SNOWTHICK", "TKPOND", "TKSURFICE")
ICE_DENSITY = 917.0


def read_monthly(directory: Path, name: str) -> np.ndarray:
    path = directory / f"{name}_monthly_tr.nc"
    with Dataset(path) as dataset:
        return np.asarray(np.ma.asarray(dataset[name][:]).filled(np.nan), float)


def read_daily(directory: Path, name: str) -> np.ndarray:
    path = directory / f"{name}_daily_tr.nc"
    with Dataset(path) as dataset:
        return np.asarray(np.ma.asarray(dataset[name][:]).filled(np.nan), float)


def cell_series(array: np.ndarray, cell: tuple[int, int]) -> np.ndarray:
    return array[(slice(None),) + cell]


def has_profile_outputs(run_dir: Path) -> bool:
    return all((run_dir / f"{name}_monthly_tr.nc").exists() for name in PROFILE_VARS)


def load_initial_ice_bands(restart: Path, cell: tuple[int, int], min_kg_m2: float = 1.0):
    """Return [(top_m, bottom_m, kg_m2), ...] for layers with excess ice at t=0."""
    y, x = cell
    bands = []
    with Dataset(restart) as dataset:
        n = int(dataset["numsl"][y, x])
        z = 0.0
        for j in range(n):
            matrix = float(dataset["TKmatrix"][y, x, j])
            if matrix <= 0.0:
                matrix = float(dataset["DZsoil"][y, x, j])
            excess = float(dataset["TKexcess"][y, x, j])
            if excess >= min_kg_m2:
                bands.append((z, z + matrix, excess))
            z += float(dataset["DZsoil"][y, x, j])
    return bands


def monthly_mean_daily(daily: np.ndarray, tr_years: int) -> np.ndarray:
    nmonths = tr_years * 12
    out = np.full(nmonths, np.nan)
    for month in range(nmonths):
        start = month * 30
        end = min((month + 1) * 30, daily.shape[0])
        chunk = daily[start:end]
        if np.any(np.isfinite(chunk)):
            out[month] = float(np.nanmean(chunk))
    return out


def depth_of_zero_isotherm(z_m: np.ndarray, temps_c: np.ndarray) -> float:
    """Return deepest depth (m) of the 0 °C isotherm; 0 if frozen at the surface."""
    z = np.asarray(z_m, float)
    t = np.asarray(temps_c, float)
    good = np.isfinite(t)
    if not np.any(good):
        return float("nan")
    z, t = z[good], t[good]
    if t[0] < 0.0:
        return 0.0
    deepest = 0.0
    for i in range(len(z) - 1):
        if t[i] >= 0.0:
            deepest = max(deepest, z[i])
            if t[i + 1] < 0.0 and t[i + 1] != t[i]:
                frac = t[i] / (t[i] - t[i + 1])
                deepest = max(deepest, z[i] + frac * (z[i + 1] - z[i]))
        else:
            break
    if t[-1] >= 0.0:
        deepest = max(deepest, z[-1])
    return float(deepest)


def monthly_alt_from_temperature(z_m: np.ndarray, temp_c: np.ndarray) -> np.ndarray:
    """Monthly active-layer depth (m) = max depth of the 0 °C isotherm."""
    nmonths = temp_c.shape[0]
    alt_m = np.full(nmonths, np.nan)
    for month in range(nmonths):
        alt_m[month] = depth_of_zero_isotherm(z_m, temp_c[month])
    return alt_m


def yearly_alt_from_temperature(z_m: np.ndarray, temp_c: np.ndarray, tr_years: int) -> np.ndarray:
    """Annual ALT (m) = max 0 °C isotherm depth over all months in each transient year."""
    values = []
    for year_idx in range(tr_years):
        start = year_idx * 12
        end = min(start + 12, temp_c.shape[0])
        if start >= temp_c.shape[0]:
            values.append(float("nan"))
            continue
        month_alts = [
            depth_of_zero_isotherm(z_m, temp_c[month])
            for month in range(start, end)
        ]
        values.append(float(np.nanmax(month_alts)))
    return np.asarray(values, float)


def build_temperature_field(run_dir: Path, cell: tuple[int, int], max_depth_m: float = 2.5):
    """Interpolate TLAYER onto a regular depth grid for each month."""
    tlayer = read_monthly(run_dir, "TLAYER")
    depth = read_monthly(run_dir, "LAYERDEPTH")
    dz = read_monthly(run_dir, "LAYERDZ")
    y, x = cell
    nmonths = tlayer.shape[0]
    z_grid = np.linspace(0.0, max_depth_m, 121)
    field = np.full((nmonths, z_grid.size), np.nan)
    for t in range(nmonths):
        tops = np.asarray(depth[t, :, y, x], float)
        thickness = np.asarray(dz[t, :, y, x], float)
        temps = np.asarray(tlayer[t, :, y, x], float)
        good = np.isfinite(temps) & np.isfinite(thickness) & (thickness > 0)
        if not np.any(good):
            continue
        tops, thickness, temps = tops[good], thickness[good], temps[good]
        mids = tops + 0.5 * thickness
        order = np.argsort(mids)
        mids, temps = mids[order], temps[order]
        field[t] = np.interp(z_grid, mids, temps, left=temps[0], right=temps[-1])
    return z_grid, field


def plot_soil_thermal_panel(
    run_dir: Path,
    restart: Path,
    cell: tuple[int, int],
    *,
    treatment: str,
    tr_years: int,
    start_year: int = 2009,
    out_dir: Path,
    max_depth_m: float = 2.5,
):
    """Depth–time soil temperature contour with ALT, subsidence, ice, and ponding."""
    z_m, temp_c = build_temperature_field(run_dir, cell, max_depth_m=max_depth_m)
    nmonths = temp_c.shape[0]
    years = start_year + np.arange(nmonths) / 12.0
    z_cm = z_m * 100.0

    sub_cm = cell_series(read_daily(run_dir, "TKSUBSIDENCE"), cell) * 100.0
    sub_month_cm = monthly_mean_daily(sub_cm, tr_years)
    snow_cm = cell_series(read_daily(run_dir, "SNOWTHICK"), cell) * 100.0
    snow_month_cm = monthly_mean_daily(snow_cm, tr_years)
    alt_temp_m = monthly_alt_from_temperature(z_m, temp_c)
    alt_temp_cm = alt_temp_m * 100.0
    yearly_alt_temp_cm = yearly_alt_from_temperature(z_m, temp_c, tr_years) * 100.0
    pond_mm = monthly_mean_daily(cell_series(read_daily(run_dir, "TKPOND"), cell), tr_years)
    surf_ice = monthly_mean_daily(
        cell_series(read_daily(run_dir, "TKSURFICE"), cell), tr_years)
    ice_bands = load_initial_ice_bands(restart, cell)

    finite = temp_c[np.isfinite(temp_c)]
    tlim = float(max(5.0, np.nanpercentile(np.abs(finite), 98))) if finite.size else 10.0
    norm = TwoSlopeNorm(vcenter=0.0, vmin=-tlim, vmax=tlim)

    fig = plt.figure(figsize=(9.2, 8.2), layout="constrained")
    gs = fig.add_gridspec(4, 1, height_ratios=[0.9, 0.9, 4.5, 1.2], hspace=0.08)
    ax_snow = fig.add_subplot(gs[0])
    ax_sub = fig.add_subplot(gs[1], sharex=ax_snow)
    ax = fig.add_subplot(gs[2], sharex=ax_snow)
    ax_hyd = fig.add_subplot(gs[3], sharex=ax_snow)

    ax_snow.fill_between(years, 0.0, snow_month_cm, color="#4C78A8", alpha=0.35, lw=0)
    ax_snow.plot(years, snow_month_cm, color="#4C78A8", lw=1.4, label="Snow depth")
    ax_snow.set_ylabel("Snow depth\n(cm)")
    ax_snow.grid(color="#E4E7E5", lw=0.6)
    ax_snow.set_xlim(years[0], years[-1])
    ax_snow.set_title(f"{treatment.replace('_', ' ').title()} — soil thermal state (2009–2018)")
    plt.setp(ax_snow.get_xticklabels(), visible=False)

    # Subsidence (cumulative surface collapse).
    ax_sub.plot(years, sub_month_cm, color="#D55E00", lw=1.4)
    ax_sub.set_ylabel("Subsidence\n(cm)")
    ax_sub.grid(color="#E4E7E5", lw=0.6)
    plt.setp(ax_sub.get_xticklabels(), visible=False)

    # Temperature contour: blue (cold) → white (0 °C) → red (warm).
    xx, zz = np.meshgrid(years, z_cm)
    mesh = ax.pcolormesh(
        xx, zz, temp_c.T, shading="auto", cmap="bwr", norm=norm, rasterized=True)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.01, fraction=0.025)
    cbar.set_label("Soil temperature (°C)")

    # Initial excess-ice bands (kg m⁻² annotated at left).
    for top_m, bot_m, mass in ice_bands:
        ax.axhspan(top_m * 100.0, bot_m * 100.0, color="#4C78A8", alpha=0.12, lw=0)
        ax.text(
            years[0] + 0.05, 0.5 * (top_m + bot_m) * 100.0,
            f"{mass:.0f} kg m$^{{-2}}$",
            fontsize=6.5, color="#1F6F5F", va="center",
        )

    # ALT from soil temperature: max depth of the 0 °C isotherm (monthly).
    valid_temp = np.isfinite(alt_temp_cm)
    if np.any(valid_temp):
        ax.plot(years[valid_temp], alt_temp_cm[valid_temp], color="#D55E00", lw=1.8,
                ls="-", label="ALT (0 °C isotherm from TLAYER)")

    # Annual max ALT from temperature (markers at year midpoints).
    year_centers = start_year + np.arange(tr_years) + 0.5
    year_valid = np.isfinite(yearly_alt_temp_cm)
    if np.any(year_valid):
        ax.plot(year_centers[year_valid], yearly_alt_temp_cm[year_valid], marker="o",
                color="#1F6F5F", ms=4.5, lw=0, mew=0.8,
                label="Annual max ALT (0 °C isotherm)")

    # 0 °C isotherm contour from the gridded temperature field.
    try:
        ax.contour(xx, zz, temp_c.T, levels=[0.0], colors="#777772", linewidths=0.6,
                   linestyles=":", alpha=0.7)
    except (ValueError, RuntimeError):
        pass

    ax.set_ylabel("Depth below surface (cm)")
    ax.invert_yaxis()
    ax.set_ylim(max_depth_m * 100.0, 0.0)
    ax.grid(color="#E4E7E5", lw=0.4, alpha=0.5)
    ax.legend(loc="lower right", fontsize=7, frameon=False)

    # Surface hydrology: ponded water and thermokarst surface ice.
    ax_hyd.plot(years, pond_mm, color="#1F6F5F", lw=1.3, label="Surface pond (TKPOND)")
    ax_hyd2 = ax_hyd.twinx()
    ax_hyd2.plot(years, surf_ice, color="#4C78A8", lw=1.1, ls="--",
                 label="Surface ice (TKSURFICE)")
    ax_hyd.set_ylabel("Pond depth (mm)", color="#1F6F5F")
    ax_hyd2.set_ylabel("Surface ice (kg m$^{-2}$)", color="#4C78A8")
    ax_hyd.set_xlabel("Calendar year")
    ax_hyd.grid(color="#E4E7E5", lw=0.6)
    lines = ax_hyd.get_lines() + ax_hyd2.get_lines()
    ax_hyd.legend(lines, [ln.get_label() for ln in lines], loc="upper left", fontsize=7,
                  frameon=False)

    stem = f"eml-soil-thermal-{treatment}"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def copy_report_figures(result_dir: Path, stems: list[str]):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for stem in stems:
        for ext in ("png", "svg"):
            src = result_dir / f"{stem}.{ext}"
            if src.exists():
                dst = REPORT_DIR / src.name
                shutil.copy2(src, dst)
                copied.append(dst.name)
    return copied


def generate_thermal_figures(
    result_dir: Path,
    *,
    treatments: tuple[str, ...] = ("control", "soil_warming"),
    tr_years: int = 9,
    start_year: int = 2009,
    cell: tuple[int, int] = (0, 0),
    copy_to_report: bool = True,
) -> list[str]:
    summary_path = result_dir / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"missing summary: {summary_path}")
    summary = json.loads(summary_path.read_text())
    restarts = summary.get("treatment_restarts", {})
    stems = []
    for treatment in treatments:
        run_dir = result_dir / f"treatment-{treatment}"
        if not has_profile_outputs(run_dir):
            raise FileNotFoundError(
                f"{run_dir} lacks TLAYER monthly output; re-run with profile spec "
                f"(make thermokarst-eml-thermal-plots)")
        restart = Path(restarts[treatment]["path"])
        stem = plot_soil_thermal_panel(
            run_dir, restart, cell,
            treatment=treatment, tr_years=tr_years, start_year=start_year,
            out_dir=result_dir)
        stems.append(stem)
    if copy_to_report:
        copy_report_figures(result_dir, stems)
    return stems
