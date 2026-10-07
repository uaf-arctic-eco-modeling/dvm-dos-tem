"""Climate and soil-thermal diagnostic figures for Barrow validation reports."""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from netCDF4 import Dataset

REPORT_DIR = Path(__file__).resolve().parents[3] / "docs_src" / "thermokarst"
GRID = "#E4E7E5"
TEAL = "#1F6F5F"
BLUE = "#4C78A8"
ORANGE = "#D55E00"
MUTED = "#777772"
PLOT_COLOR = {34: TEAL, 37: BLUE, 40: ORANGE, 44: MUTED}

_etp_spec = importlib.util.spec_from_file_location(
    "eml_thermal_plots",
    Path(__file__).resolve().parents[1] / "eml_validation" / "eml_thermal_plots.py",
)
_etp = importlib.util.module_from_spec(_etp_spec)
sys.modules[_etp_spec.name] = _etp
_etp_spec.loader.exec_module(_etp)


def read_climate_series(path: Path) -> dict[str, np.ndarray]:
    with Dataset(path) as dataset:
        n = dataset["tair"].shape[0]
        nyears = n // 12
        tair = np.asarray(dataset["tair"][:n, 0, 0], float).reshape(nyears, 12)
        precip = np.asarray(dataset["precip"][:n, 0, 0], float).reshape(nyears, 12)
        nirr = np.asarray(dataset["nirr"][:n, 0, 0], float).reshape(nyears, 12)
    return {
        "tair_monthly": tair,
        "precip_monthly": precip,
        "nirr_monthly": nirr,
        "ann_tair": tair.mean(axis=1),
        "ann_precip": precip.sum(axis=1),
        "nyears": nyears,
    }


def plot_climate_inputs(
    out_dir: Path,
    full_climate: Path,
    tr_climate: Path,
    *,
    eq_start_year: int = 1901,
    tr_start_year: int = 2003,
    tr_years: int = 13,
) -> str:
    """Historic (EQ) and transient NWS-bias-corrected climate forcing."""
    full = read_climate_series(full_climate)
    tr = read_climate_series(tr_climate)
    eq_years = np.arange(eq_start_year, eq_start_year + full["nyears"])
    tr_calendar = np.arange(tr_start_year, tr_start_year + tr["nyears"])

    fig, axes = plt.subplots(3, 2, figsize=(10.5, 8.0), layout="constrained")
    fig.suptitle("Barrow NWS-bias-corrected climate inputs", fontsize=11)

    for ax, data, years, label in [
        (axes[0, 0], full, eq_years, "Spin-up / EQ (full historic)"),
        (axes[0, 1], tr, tr_calendar, "Transient window (2003–2015)"),
    ]:
        tflat = data["tair_monthly"].ravel()
        xmonths = np.repeat(years, 12) + np.tile(np.arange(12) / 12.0, data["nyears"])
        ax.plot(xmonths, tflat, color=TEAL, lw=0.7)
        ax.plot(years, data["ann_tair"], color=ORANGE, lw=1.4, marker="o", ms=2.5,
                label="Mean annual tair")
        ax.axhline(0.0, color=MUTED, lw=0.6, ls=":")
        ax.set(title=label, ylabel="Air temperature (°C)")
        ax.grid(color=GRID, lw=0.5)
        ax.legend(fontsize=7, loc="lower right", frameon=False)

    for ax, data, years, label in [
        (axes[1, 0], full, eq_years, "Monthly precipitation — full"),
        (axes[1, 1], tr, tr_calendar, "Monthly precipitation — TR"),
    ]:
        pflat = data["precip_monthly"].ravel()
        xmonths = np.repeat(years, 12) + np.tile(np.arange(12) / 12.0, data["nyears"])
        ax.plot(xmonths, pflat, color=BLUE, lw=0.7)
        ax.plot(years, data["ann_precip"], color=TEAL, lw=1.2, label="Annual total")
        ax.set(title=label, ylabel="Precipitation (mm mo$^{-1}$)")
        ax.grid(color=GRID, lw=0.5)
        ax.legend(fontsize=7, frameon=False)

    for ax, data, years, label in [
        (axes[2, 0], full, eq_years, "Monthly NIRR — full"),
        (axes[2, 1], tr, tr_calendar, "Monthly NIRR — TR"),
    ]:
        nflat = data["nirr_monthly"].ravel()
        xmonths = np.repeat(years, 12) + np.tile(np.arange(12) / 12.0, data["nyears"])
        ax.plot(xmonths, nflat, color=MUTED, lw=0.7)
        ax.set(title=label, ylabel="NIRR (W m$^{-2}$)", xlabel="Calendar year")
        ax.grid(color=GRID, lw=0.5)

    stem = "barrow-climate-inputs"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def september_isotherm_alt_cm(z_m: np.ndarray, temp_c: np.ndarray, tr_years: int) -> list[float]:
    """September (month 8) 0 °C isotherm depth in cm for each transient year."""
    values = []
    for year_idx in range(tr_years):
        month = year_idx * 12 + 8
        if month >= temp_c.shape[0]:
            values.append(float("nan"))
        else:
            values.append(float(_etp.depth_of_zero_isotherm(z_m, temp_c[month]) * 100.0))
    return values


def isotherm_alt_metrics(run_dir: Path, cell: tuple[int, int], tr_years: int):
    if not _etp.has_profile_outputs(run_dir):
        return None
    z_m, temp_c = _etp.build_temperature_field(run_dir, cell)
    monthly_m = _etp.monthly_alt_from_temperature(z_m, temp_c)
    yearly_m = _etp.yearly_alt_from_temperature(z_m, temp_c, tr_years)
    finite = monthly_m[np.isfinite(monthly_m)]
    return {
        "monthly_cm": (monthly_m * 100.0).tolist(),
        "yearly_cm": (yearly_m * 100.0).tolist(),
        "september_cm": september_isotherm_alt_cm(z_m, temp_c, tr_years),
        "max_cm": float(np.nanmax(monthly_m) * 100.0) if finite.size else float("nan"),
        "mean_cm": float(np.nanmean(monthly_m) * 100.0) if finite.size else float("nan"),
    }


def plot_soil_thermal_panel(
    run_dir: Path,
    restart: Path,
    cell: tuple[int, int],
    plot: int,
    *,
    tr_years: int,
    start_year: int = 2003,
    out_dir: Path,
    max_depth_m: float = 1.5,
) -> str:
    """Depth–time soil temperature (bwr), snow, subsidence, 0 °C isotherm ALT."""
    z_m, temp_c = _etp.build_temperature_field(run_dir, cell, max_depth_m=max_depth_m)
    nmonths = temp_c.shape[0]
    years = start_year + np.arange(nmonths) / 12.0
    z_cm = z_m * 100.0

    sub_cm = _etp.cell_series(_etp.read_daily(run_dir, "TKSUBSIDENCE"), cell) * 100.0
    sub_month_cm = _etp.monthly_mean_daily(sub_cm, tr_years)
    snow_cm = _etp.cell_series(_etp.read_daily(run_dir, "SNOWTHICK"), cell) * 100.0
    snow_month_cm = _etp.monthly_mean_daily(snow_cm, tr_years)
    alt_temp_m = _etp.monthly_alt_from_temperature(z_m, temp_c)
    alt_temp_cm = alt_temp_m * 100.0
    yearly_alt_temp_cm = _etp.yearly_alt_from_temperature(z_m, temp_c, tr_years) * 100.0
    ice_bands = _etp.load_initial_ice_bands(restart, cell)

    finite = temp_c[np.isfinite(temp_c)]
    tlim = float(max(5.0, np.nanpercentile(np.abs(finite), 98))) if finite.size else 10.0
    norm = TwoSlopeNorm(vcenter=0.0, vmin=-tlim, vmax=tlim)

    fig = plt.figure(figsize=(9.2, 8.0), layout="constrained")
    gs = fig.add_gridspec(3, 1, height_ratios=[0.9, 0.9, 4.8], hspace=0.08)
    ax_snow = fig.add_subplot(gs[0])
    ax_sub = fig.add_subplot(gs[1], sharex=ax_snow)
    ax = fig.add_subplot(gs[2], sharex=ax_snow)

    ax_snow.fill_between(years, 0.0, snow_month_cm, color=BLUE, alpha=0.35, lw=0)
    ax_snow.plot(years, snow_month_cm, color=BLUE, lw=1.4, label="Snow depth")
    ax_snow.set_ylabel("Snow depth\n(cm)")
    ax_snow.grid(color=GRID, lw=0.6)
    ax_snow.set_xlim(years[0], years[-1])
    ax_snow.set_title(f"Plot {plot} — soil thermal state ({start_year}–{start_year + tr_years - 1})")
    plt.setp(ax_snow.get_xticklabels(), visible=False)

    ax_sub.plot(years, sub_month_cm, color=ORANGE, lw=1.4, label="Subsidence")
    ax_sub.set_ylabel("Subsidence\n(cm)")
    ax_sub.grid(color=GRID, lw=0.6)
    plt.setp(ax_sub.get_xticklabels(), visible=False)

    xx, zz = np.meshgrid(years, z_cm)
    mesh = ax.pcolormesh(
        xx, zz, temp_c.T, shading="auto", cmap="bwr", norm=norm, rasterized=True)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.01, fraction=0.025)
    cbar.set_label("Soil temperature (°C)")

    for top_m, bot_m, mass in ice_bands:
        ax.axhspan(top_m * 100.0, bot_m * 100.0, color=BLUE, alpha=0.12, lw=0)
        if mass >= 1.0:
            ax.text(
                years[0] + 0.05, 0.5 * (top_m + bot_m) * 100.0,
                f"{mass:.0f} kg m$^{{-2}}$",
                fontsize=6.5, color=TEAL, va="center",
            )

    valid = np.isfinite(alt_temp_cm)
    if np.any(valid):
        ax.plot(years[valid], alt_temp_cm[valid], color=ORANGE, lw=1.8,
                label="ALT (0 °C isotherm, TLAYER)")

    year_centers = start_year + np.arange(tr_years) + 0.5
    yvalid = np.isfinite(yearly_alt_temp_cm)
    if np.any(yvalid):
        ax.plot(year_centers[yvalid], yearly_alt_temp_cm[yvalid], marker="o",
                color=TEAL, ms=4.5, lw=0, label="Annual max ALT (0 °C)")

    try:
        ax.contour(xx, zz, temp_c.T, levels=[0.0], colors=MUTED, linewidths=0.6,
                   linestyles=":", alpha=0.7)
    except (ValueError, RuntimeError):
        pass

    ax.set_ylabel("Depth below surface (cm)")
    ax.set_xlabel("Calendar year")
    ax.invert_yaxis()
    ax.set_ylim(max_depth_m * 100.0, 0.0)
    ax.grid(color=GRID, lw=0.4, alpha=0.5)
    ax.legend(loc="lower right", fontsize=7, frameon=False)

    stem = f"barrow-soil-thermal-plot{plot}"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def plot_alt_isotherm_vs_obs(
    run_dir: Path,
    cells: list[tuple[int, int]],
    plots: list[int],
    obs_alt: dict[int, dict[int, float]],
    calendar_years: list[int],
    tr_years: int,
    out_dir: Path,
) -> str:
    """Four-panel September 0 °C isotherm ALT vs Streletskiy probing."""
    fig, axes = plt.subplots(2, 2, figsize=(8.8, 6.4), sharex=True, layout="constrained")
    for ax, cell, plot in zip(axes.flat, cells, plots):
        metrics = isotherm_alt_metrics(run_dir, cell, tr_years)
        if metrics is None:
            continue
        model = metrics["september_cm"]
        obs = [obs_alt[plot].get(y, np.nan) for y in calendar_years]
        ax.plot(calendar_years, obs, "s--", color=MUTED, lw=1.2, ms=4, label="Observed")
        ax.plot(calendar_years, model, "o-", color=PLOT_COLOR[plot], lw=1.6, ms=4,
                label="0 °C isotherm")
        ax.set_title(f"Plot {plot}")
        ax.set_ylabel("September ALT (cm)")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.legend(fontsize=7)
    axes[1, 0].set_xlabel("Calendar year")
    axes[1, 1].set_xlabel("Calendar year")
    fig.suptitle("Active-layer thickness: 0 °C isotherm (TLAYER) vs Streletskiy probing",
                 fontsize=10)
    stem = "barrow-alt-isotherm-vs-obs"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def copy_report_figures(out_dir: Path, stems: list[str]) -> list[str]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for stem in stems:
        for ext in ("png", "svg"):
            src = out_dir / f"{stem}.{ext}"
            if src.exists():
                dst = REPORT_DIR / src.name
                shutil.copy2(src, dst)
                if ext == "png":
                    copied.append(stem)
    return copied


def generate_diagnostic_figures(
    out_dir: Path,
    *,
    run_dir: Path,
    restart: Path,
    cells: list[tuple[int, int]],
    plots: list[int],
    obs_alt: dict[int, dict[int, float]],
    full_climate: Path | None = None,
    tr_climate: Path | None = None,
    tr_years: int = 13,
    start_year: int = 2003,
    calendar_years: list[int] | None = None,
    copy_to_report: bool = True,
) -> list[str]:
    out_dir = out_dir.resolve()
    run_dir = run_dir.resolve()
    calendar_years = calendar_years or list(range(start_year, start_year + tr_years))
    stems: list[str] = []

    full_climate = full_climate or out_dir / "nws-barrow-climate-full.nc"
    tr_climate = tr_climate or out_dir / "nws-barrow-climate-tr.nc"
    if full_climate.exists() and tr_climate.exists():
        stems.append(plot_climate_inputs(
            out_dir, full_climate, tr_climate,
            tr_start_year=start_year, tr_years=tr_years))

    if not _etp.has_profile_outputs(run_dir):
        raise FileNotFoundError(
            f"{run_dir} lacks TLAYER monthly output; re-run with profile spec "
            f"(--diagnostic-plots)")

    for cell, plot in zip(cells, plots):
        stems.append(plot_soil_thermal_panel(
            run_dir, restart, cell, plot,
            tr_years=tr_years, start_year=start_year, out_dir=out_dir))

    stems.append(plot_alt_isotherm_vs_obs(
        run_dir, cells, plots, obs_alt, calendar_years, tr_years, out_dir))

    if copy_to_report:
        copy_report_figures(out_dir, stems)
    return stems
