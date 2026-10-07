"""Climate-input and soil-thermal diagnostic figures for Anaktuvuk validation."""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset

REPORT_DIR = Path(__file__).resolve().parents[3] / "docs_src" / "thermokarst"
GRID = "#E4E7E5"
TEAL = "#1F6F5F"
BLUE = "#4C78A8"
ORANGE = "#D55E00"
MUTED = "#777772"
DINM = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

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
    ann_tair = tair.mean(axis=1)
    ann_precip = precip.sum(axis=1)
    return {
        "tair_monthly": tair,
        "precip_monthly": precip,
        "nirr_monthly": nirr,
        "ann_tair": ann_tair,
        "ann_precip": ann_precip,
        "nyears": nyears,
    }


def _window_slice(data: dict, years: np.ndarray, win_start: int, win_end: int):
    """Slice monthly arrays to calendar years within [win_start, win_end]."""
    mask = (years >= win_start) & (years <= win_end)
    if not np.any(mask):
        return data, years
    idx = np.where(mask)[0]
    tair = data["tair_monthly"][idx]
    precip = data["precip_monthly"][idx]
    nirr = data["nirr_monthly"][idx]
    sliced = {
        "tair_monthly": tair,
        "precip_monthly": precip,
        "nirr_monthly": nirr,
        "ann_tair": tair.mean(axis=1),
        "ann_precip": precip.sum(axis=1),
        "nyears": tair.shape[0],
    }
    return sliced, years[mask]


def plot_climate_inputs(
    out_dir: Path,
    full_climate: Path,
    tr_climate: Path,
    *,
    eq_start_year: int = 1901,
    tr_start_year: int = 2007,
    tr_years: int = 15,
    tr_end_year: int | None = None,
    bias_c: float | None = None,
    prefix: str = "anaktuvuk-phase1",
    full_label: str | None = None,
    tr_label: str | None = None,
    sp_start_year: int | None = None,
) -> str:
    """Plot historic (EQ/SP) and transient climate forcing used by the harness."""
    full = read_climate_series(full_climate)
    tr = read_climate_series(tr_climate)
    tr_end_year = tr_end_year or (tr_start_year + tr_years - 1)
    win_end = tr_end_year

    sp_start_year = sp_start_year or (tr_start_year - full["nyears"])
    eq_years = np.arange(sp_start_year, sp_start_year + full["nyears"])
    tr_calendar = np.arange(tr_start_year, tr_start_year + tr["nyears"])
    full_win, eq_years_win = _window_slice(full, eq_years, tr_start_year, win_end)
    tr_win, tr_calendar_win = _window_slice(tr, tr_calendar, tr_start_year, win_end)

    fig, axes = plt.subplots(3, 2, figsize=(10.5, 8.0), layout="constrained")
    bias_note = f" (+{bias_c:.1f} °C inland bias)" if bias_c is not None else ""
    window_note = f"{tr_start_year}–{win_end}"
    fig.suptitle(f"North Slope climate inputs — {window_note}{bias_note}", fontsize=11)
    left_label = full_label or f"Seasonal SP block ({full['nyears']} yr climatology repeat)"
    right_label = tr_label or f"Historic TR ({window_note})"

    for ax, data, years, label in [
        (axes[0, 0], full_win, eq_years_win, left_label),
        (axes[0, 1], tr_win, tr_calendar_win, right_label),
    ]:
        tflat = data["tair_monthly"].ravel()
        xmonths = np.repeat(years, 12) + np.tile(np.arange(12) / 12.0, data["nyears"])
        ax.plot(xmonths, tflat, color=TEAL, lw=0.7)
        ax.plot(years, data["ann_tair"], color=ORANGE, lw=1.4, marker="o", ms=2.5,
                label="Mean annual tair")
        ax.axhline(0.0, color=MUTED, lw=0.6, ls=":")
        ax.set(title=label, ylabel="Air temperature (°C)",
               xlim=(tr_start_year - 0.1, win_end + 0.9))
        ax.grid(color=GRID, lw=0.5)
        ax.legend(fontsize=7, loc="lower right", frameon=False)

    for ax, data, years, label in [
        (axes[1, 0], full_win, eq_years_win, f"Monthly precipitation — full ({window_note})"),
        (axes[1, 1], tr_win, tr_calendar_win, f"Monthly precipitation — TR ({window_note})"),
    ]:
        pflat = data["precip_monthly"].ravel()
        xmonths = np.repeat(years, 12) + np.tile(np.arange(12) / 12.0, data["nyears"])
        ax.plot(xmonths, pflat, color=BLUE, lw=0.7)
        ax.plot(years, data["ann_precip"], color=TEAL, lw=1.2, label="Annual total")
        ax.set(title=label, ylabel="Precipitation (mm mo$^{-1}$)",
               xlim=(tr_start_year - 0.1, win_end + 0.9))
        ax.grid(color=GRID, lw=0.5)
        ax.legend(fontsize=7, frameon=False)

    for ax, data, years, label in [
        (axes[2, 0], full_win, eq_years_win, f"Monthly NIRR — full ({window_note})"),
        (axes[2, 1], tr_win, tr_calendar_win, f"Monthly NIRR — TR ({window_note})"),
    ]:
        nflat = data["nirr_monthly"].ravel()
        xmonths = np.repeat(years, 12) + np.tile(np.arange(12) / 12.0, data["nyears"])
        ax.plot(xmonths, nflat, color=MUTED, lw=0.7)
        ax.set(title=label, ylabel="NIRR (W m$^{-2}$)", xlabel="Calendar year",
               xlim=(tr_start_year - 0.1, win_end + 0.9))
        ax.grid(color=GRID, lw=0.5)

    stem = f"{prefix}-climate-inputs"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def isotherm_alt_metrics(run_dir: Path, cell: tuple[int, int], tr_years: int):
    """ALT (cm) from TLAYER: max depth of the 0 °C isotherm."""
    if not _etp.has_profile_outputs(run_dir):
        return None
    z_m, temp_c = _etp.build_temperature_field(run_dir, cell)
    monthly_m = _etp.monthly_alt_from_temperature(z_m, temp_c)
    yearly_m = _etp.yearly_alt_from_temperature(z_m, temp_c, tr_years)
    finite = monthly_m[np.isfinite(monthly_m)]
    return {
        "monthly_cm": (monthly_m * 100.0).tolist(),
        "yearly_cm": (yearly_m * 100.0).tolist(),
        "max_cm": float(np.nanmax(monthly_m) * 100.0) if finite.size else float("nan"),
        "mean_cm": float(np.nanmean(monthly_m) * 100.0) if finite.size else float("nan"),
        "september_cm": [
            float(monthly_m[y * 12 + 8] * 100.0) if y * 12 + 8 < monthly_m.size else float("nan")
            for y in range(tr_years)
        ],
    }


def monthly_max_snow(daily: np.ndarray, tr_years: int) -> np.ndarray:
    """Calendar-month maximum snow depth (avoids month-end sampling artifacts)."""
    nmonths = tr_years * 12
    out = np.full(nmonths, np.nan)
    for year in range(tr_years):
        for month in range(12):
            start = year * 365 + sum(DINM[:month])
            end = min(year * 365 + sum(DINM[: month + 1]), daily.shape[0])
            chunk = daily[start:end]
            if chunk.size:
                out[year * 12 + month] = float(np.nanmax(chunk))
    return out


def monthly_mean_daily(daily: np.ndarray, tr_years: int) -> np.ndarray:
    """Calendar-month mean for slowly varying series (e.g. subsidence)."""
    nmonths = tr_years * 12
    out = np.full(nmonths, np.nan)
    for year in range(tr_years):
        for month in range(12):
            start = year * 365 + sum(DINM[:month])
            end = min(year * 365 + sum(DINM[: month + 1]), daily.shape[0])
            chunk = daily[start:end]
            if chunk.size:
                out[year * 12 + month] = float(np.nanmean(chunk))
    return out


def annual_winter_max_cm(daily_cm: np.ndarray, tr_years: int) -> list[float]:
    """Seasonal snowpack peak (cm) for each transient year."""
    peaks = []
    for year in range(tr_years):
        chunk = daily_cm[year * 365:min((year + 1) * 365, daily_cm.shape[0])]
        peaks.append(float(np.nanmax(chunk)) if chunk.size else float("nan"))
    return peaks


ICE_DENSITY_KG_M3 = 917.0


def total_excess_ice_kg_m2(restart: Path, cell: tuple[int, int]) -> float:
    """Sum TKexcess (kg m⁻²) across soil layers in a restart file."""
    y, x = cell
    with Dataset(restart) as dataset:
        if "TKexcess" not in dataset.variables:
            return float("nan")
        n = int(np.ma.asarray(dataset["numsl"][y, x]).filled(0))
        if n <= 0:
            return 0.0
        values = np.asarray(np.ma.asarray(dataset["TKexcess"][y, x, :n]).filled(0.0), float)
        return float(np.sum(values))


def plot_excess_ice_degradation(
    out_dir: Path,
    restart: Path,
    *,
    tr_years: int,
    start_year: int,
    fire_jday: int = 240,
    fire_year: int = 2007,
    plot_start_year: int | None = None,
    prefix: str = "anaktuvuk-phase1",
) -> str | None:
    """Excess-ice inventory vs time (inferred from subsidence) for burned and control."""
    burned_dir = out_dir / "burned"
    control_dir = out_dir / "control"
    if not restart.exists() or not (burned_dir / "TKSUBSIDENCE_daily_tr.nc").exists():
        return None
    plot_start_year = plot_start_year if plot_start_year is not None else start_year
    initial_b = total_excess_ice_kg_m2(restart, (0, 0))
    initial_c = total_excess_ice_kg_m2(restart, (0, 1))
    if not np.isfinite(initial_b) or initial_b <= 0.0:
        return None

    sub_b = _etp.cell_series(_etp.read_daily(burned_dir, "TKSUBSIDENCE"), (0, 0))
    sub_c = _etp.cell_series(_etp.read_daily(control_dir, "TKSUBSIDENCE"), (0, 1))
    ndays = min(sub_b.shape[0], sub_c.shape[0], tr_years * 365)
    years = start_year + np.arange(ndays) / 365.0

    remaining_b = np.maximum(0.0, initial_b - sub_b[:ndays] * ICE_DENSITY_KG_M3)
    remaining_c = np.maximum(0.0, initial_c - sub_c[:ndays] * ICE_DENSITY_KG_M3)
    frac_b = remaining_b / initial_b
    frac_c = remaining_c / initial_c if initial_c > 0.0 else np.zeros_like(remaining_c)

    final_restart = burned_dir / "restart-tr.nc"
    final_b = (total_excess_ice_kg_m2(final_restart, (0, 0))
               if final_restart.exists() else float("nan"))

    fig, axes = plt.subplots(2, 1, figsize=(9.0, 6.2), layout="constrained", sharex=True)
    fig.suptitle("Excess ground-ice mass (paired Yedoma inventory)", fontsize=11)

    ax = axes[0]
    ax.plot(years, remaining_b, color=ORANGE, lw=1.5, label="Burned")
    ax.plot(years, remaining_c, "--", color=MUTED, lw=1.3, label="Control")
    ax.axhline(0.0, color=GRID, lw=0.6)
    ax.set_ylabel("Remaining excess ice (kg m⁻²)")
    ax.set_title(
        f"Inferred from initial TKexcess − subsidence × {ICE_DENSITY_KG_M3:.0f} kg m⁻³")
    ax.grid(color=GRID, lw=0.5)
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    if np.isfinite(final_b):
        ax.text(
            0.02, 0.05,
            f"End-of-run TKexcess (burned restart): {final_b:.0f} kg m⁻²",
            transform=ax.transAxes, fontsize=7.5, color=TEAL)

    ax = axes[1]
    ax.plot(years, frac_b * 100.0, color=ORANGE, lw=1.5, label="Burned")
    ax.plot(years, frac_c * 100.0, "--", color=MUTED, lw=1.3, label="Control")
    ax.axhline(0.0, color=GRID, lw=0.6)
    ax.set_ylim(-2.0, 105.0)
    ax.set_ylabel("Remaining fraction (%)")
    ax.set_xlabel("Calendar year")
    ax.grid(color=GRID, lw=0.5)
    ax.legend(loc="upper right", fontsize=8, frameon=False)

    fire_x = fire_year + (fire_jday - 1) / 365.0
    for axis in axes:
        axis.axvline(fire_x, color=ORANGE, ls=":", lw=0.9, alpha=0.75)
        axis.axvspan(2009, 2014, color=BLUE, alpha=0.08)
        axis.set_xlim(plot_start_year - 0.1, years[-1] + 0.3)

    note = (
        f"Initial inventory: burned {initial_b:.0f}, control {initial_c:.0f} kg m⁻² "
        f"({restart.name})"
    )
    fig.text(0.01, 0.01, note, fontsize=7, color=MUTED)

    stem = f"{prefix}-excess-ice-degradation"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def plot_snow_paired(
    out_dir: Path,
    *,
    tr_years: int = 15,
    start_year: int = 2007,
    plot_start_year: int | None = None,
    fire_jday: int = 240,
    fire_year: int = 2007,
    prefix: str = "anaktuvuk-phase1",
    run_root: Path | None = None,
) -> str:
    """Burned vs control snow depth on shared axes (same paired run)."""
    root = run_root or out_dir
    burned_dir = root / "burned"
    control_dir = root / "control"
    plot_start_year = plot_start_year if plot_start_year is not None else start_year
    snow_b = _etp.cell_series(_etp.read_daily(burned_dir, "SNOWTHICK"), (0, 0)) * 100.0
    snow_c = _etp.cell_series(_etp.read_daily(control_dir, "SNOWTHICK"), (0, 1)) * 100.0
    nmonths = tr_years * 12
    month_centers = start_year + (np.arange(nmonths) + 0.5) / 12.0
    sb = monthly_max_snow(snow_b, tr_years)
    sc = monthly_max_snow(snow_c, tr_years)
    peaks_b = annual_winter_max_cm(snow_b, tr_years)
    peaks_c = annual_winter_max_cm(snow_c, tr_years)
    post_ratios = [b / c for b, c in zip(peaks_b[1:], peaks_c[1:])
                   if np.isfinite(b) and np.isfinite(c) and c > 1e-6]
    ratio = float(np.mean(post_ratios)) if post_ratios else float("nan")

    fig, ax = plt.subplots(figsize=(8.8, 3.4), layout="constrained")
    ax.fill_between(month_centers, 0.0, sc, color=MUTED, alpha=0.20, lw=0)
    ax.plot(month_centers, sc, "--", color=MUTED, lw=1.4, label="Unburned control")
    ax.plot(month_centers, sb, color=TEAL, lw=1.6, label="Burned CMT05")
    ax.axvline(fire_year + (fire_jday - 1) / 365.0, color=ORANGE, ls=":", lw=0.9,
               label=f"{fire_year} fire")
    ax.set(xlim=(plot_start_year - 0.1, month_centers[-1] + 0.4),
           xlabel="Calendar year", ylabel="Snow depth (cm, monthly max)",
           title=f"Paired snow depth ({plot_start_year}–{start_year + tr_years - 1}; "
                   f"post-fire peak ratio = {ratio:.2f})")
    ax.grid(color=GRID, lw=0.6)
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    stem = f"{prefix}-snow-burned-vs-control"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def build_layer_profile_field(
    run_dir: Path,
    var_name: str,
    cell: tuple[int, int],
    *,
    tr_years: int,
    max_depth_m: float = 2.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Interpolate a layer-resolved monthly variable onto a regular depth grid."""
    values = _etp.read_monthly(run_dir, var_name)
    depth = _etp.read_monthly(run_dir, "LAYERDEPTH")
    dz = _etp.read_monthly(run_dir, "LAYERDZ")
    y, x = cell
    nmonths = min(tr_years * 12, values.shape[0])
    z_grid = np.linspace(0.0, max_depth_m, 121)
    field = np.full((nmonths, z_grid.size), np.nan)
    for t in range(nmonths):
        tops = np.asarray(depth[t, :, y, x], float)
        thickness = np.asarray(dz[t, :, y, x], float)
        vals = np.asarray(values[t, :, y, x], float)
        good = np.isfinite(vals) & np.isfinite(thickness) & (thickness > 0)
        if not np.any(good):
            continue
        tops, thickness, vals = tops[good], thickness[good], vals[good]
        mids = tops + 0.5 * thickness
        order = np.argsort(mids)
        mids, vals = mids[order], vals[order]
        field[t] = np.interp(z_grid, mids, vals, left=vals[0], right=vals[-1])
    return z_grid, field


def monthly_layer_total(run_dir: Path, var_name: str, cell: tuple[int, int], tr_years: int):
    """Sum a layer-resolved monthly variable over all layers (e.g. total SOC, g m⁻²)."""
    values = _etp.read_monthly(run_dir, var_name)
    y, x = cell
    nmonths = min(tr_years * 12, values.shape[0])
    totals = np.zeros(nmonths)
    for t in range(nmonths):
        layer_vals = np.asarray(values[t, :, y, x], float)
        good = np.isfinite(layer_vals) & (layer_vals > 0)
        totals[t] = float(np.nansum(layer_vals[good]))
    return totals


def _decorate_soil_depth_contour(
    ax,
    years: np.ndarray,
    *,
    restart: Path | None,
    cell: tuple[int, int],
    fire_year: int,
    fire_jday: int,
    plot_start_year: int,
    max_depth_m: float,
    lidar_window: bool = True,
):
    """Shared overlays: fire, LiDAR window, initial excess-ice band."""
    fire_x = fire_year + (fire_jday - 1) / 365.0
    ax.axvline(fire_x, color=ORANGE, ls=":", lw=0.9, alpha=0.8)
    if lidar_window:
        ax.axvspan(2009, 2014, color=BLUE, alpha=0.08)
    if restart is not None and restart.exists():
        for top_m, bot_m, mass in _etp.load_initial_ice_bands(restart, cell):
            ax.axhspan(top_m * 100.0, bot_m * 100.0, color=BLUE, alpha=0.12, lw=0)
            ax.text(
                years[0] + 0.05, 0.5 * (top_m + bot_m) * 100.0,
                f"{mass:.0f} kg m$^{{-2}}$",
                fontsize=6.5, color=TEAL, va="center",
            )
    ax.set_xlim(plot_start_year - 0.1, years[-1] + 0.4)
    ax.invert_yaxis()
    ax.set_ylim(max_depth_m * 100.0, 0.0)
    ax.set_ylabel("Depth below surface (cm)")
    ax.grid(color=GRID, lw=0.4, alpha=0.5)


def plot_soil_temperature_contour(
    run_dir: Path,
    restart: Path,
    cell: tuple[int, int],
    *,
    role: str,
    tr_years: int,
    start_year: int,
    plot_start_year: int | None = None,
    fire_jday: int = 240,
    fire_year: int = 2007,
    out_dir: Path,
    max_depth_m: float = 2.0,
    prefix: str = "anaktuvuk-phase1",
) -> str:
    """Standalone soil temperature depth–time contour (°C)."""
    from matplotlib.colors import TwoSlopeNorm

    plot_start_year = plot_start_year if plot_start_year is not None else start_year
    z_m, temp_c = _etp.build_temperature_field(run_dir, cell, max_depth_m=max_depth_m)
    nmonths = temp_c.shape[0]
    years = start_year + (np.arange(nmonths) + 0.5) / 12.0
    z_cm = z_m * 100.0
    alt_temp_cm = _etp.monthly_alt_from_temperature(z_m, temp_c) * 100.0

    finite = temp_c[np.isfinite(temp_c)]
    tlim = float(max(5.0, np.nanpercentile(np.abs(finite), 98))) if finite.size else 10.0
    norm = TwoSlopeNorm(vcenter=0.0, vmin=-tlim, vmax=tlim)

    fig, ax = plt.subplots(figsize=(9.0, 4.8), layout="constrained")
    xx, zz = np.meshgrid(years, z_cm)
    mesh = ax.pcolormesh(
        xx, zz, temp_c.T, shading="auto", cmap="bwr", norm=norm, rasterized=True)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.01, fraction=0.025)
    cbar.set_label("Soil temperature (°C)")

    valid = np.isfinite(alt_temp_cm)
    if np.any(valid):
        ax.plot(years[valid], alt_temp_cm[valid], color=ORANGE, lw=1.6,
                label="ALT (0 °C isotherm)")
    try:
        ax.contour(xx, zz, temp_c.T, levels=[0.0], colors=MUTED, linewidths=0.7,
                   linestyles=":", alpha=0.75)
    except (ValueError, RuntimeError):
        pass

    _decorate_soil_depth_contour(
        ax, years, restart=restart, cell=cell,
        fire_year=fire_year, fire_jday=fire_jday,
        plot_start_year=plot_start_year, max_depth_m=max_depth_m)
    ax.set_xlabel("Calendar year")
    ax.legend(loc="lower right", fontsize=7, frameon=False)
    ax.set_title(
        f"{role.title()} — soil temperature ({plot_start_year}–{start_year + tr_years - 1})")

    stem = f"{prefix}-soil-temperature-{role}"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def plot_liquid_water_contour(
    run_dir: Path,
    restart: Path,
    cell: tuple[int, int],
    *,
    role: str,
    tr_years: int,
    start_year: int,
    plot_start_year: int | None = None,
    fire_jday: int = 240,
    fire_year: int = 2007,
    out_dir: Path,
    max_depth_m: float = 2.0,
    prefix: str = "anaktuvuk-phase1",
) -> str:
    """Standalone volumetric liquid water depth–time contour."""
    from matplotlib.colors import Normalize

    plot_start_year = plot_start_year if plot_start_year is not None else start_year
    nmonths = tr_years * 12
    years = start_year + (np.arange(nmonths) + 0.5) / 12.0
    z_m, lwc = build_layer_profile_field(
        run_dir, "LWCLAYER", cell, tr_years=tr_years, max_depth_m=max_depth_m)
    z_cm = z_m * 100.0

    finite = lwc[np.isfinite(lwc)]
    vmax = float(np.nanpercentile(finite, 98)) if finite.size else 0.5
    vmax = max(vmax, 0.05)

    fig, ax = plt.subplots(figsize=(9.0, 4.8), layout="constrained")
    xx, zz = np.meshgrid(years, z_cm)
    mesh = ax.pcolormesh(
        xx, zz, lwc.T, shading="auto", cmap="Blues",
        norm=Normalize(vmin=0.0, vmax=vmax), rasterized=True)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.01, fraction=0.025)
    cbar.set_label("Volumetric liquid water (m$^3$ m$^{-3}$)")

    _decorate_soil_depth_contour(
        ax, years, restart=restart, cell=cell,
        fire_year=fire_year, fire_jday=fire_jday,
        plot_start_year=plot_start_year, max_depth_m=max_depth_m)
    ax.set_xlabel("Calendar year")
    ax.set_title(
        f"{role.title()} — liquid water content ({plot_start_year}–"
        f"{start_year + tr_years - 1})")

    stem = f"{prefix}-liquid-water-{role}"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def plot_ice_content_contour(
    run_dir: Path,
    restart: Path,
    cell: tuple[int, int],
    *,
    role: str,
    tr_years: int,
    start_year: int,
    plot_start_year: int | None = None,
    fire_jday: int = 240,
    fire_year: int = 2007,
    out_dir: Path,
    max_depth_m: float = 2.0,
    prefix: str = "anaktuvuk-phase1",
) -> str:
    """Standalone volumetric ice content depth–time contour."""
    from matplotlib.colors import Normalize

    plot_start_year = plot_start_year if plot_start_year is not None else start_year
    nmonths = tr_years * 12
    years = start_year + (np.arange(nmonths) + 0.5) / 12.0
    z_m, iwc = build_layer_profile_field(
        run_dir, "IWCLAYER", cell, tr_years=tr_years, max_depth_m=max_depth_m)
    z_cm = z_m * 100.0

    finite = iwc[np.isfinite(iwc)]
    vmax = float(np.nanpercentile(finite, 98)) if finite.size else 0.5
    vmax = max(vmax, 0.05)

    fig, ax = plt.subplots(figsize=(9.0, 4.8), layout="constrained")
    xx, zz = np.meshgrid(years, z_cm)
    mesh = ax.pcolormesh(
        xx, zz, iwc.T, shading="auto", cmap="PuBu",
        norm=Normalize(vmin=0.0, vmax=vmax), rasterized=True)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.01, fraction=0.025)
    cbar.set_label("Volumetric ice content (m$^3$ m$^{-3}$)")

    _decorate_soil_depth_contour(
        ax, years, restart=restart, cell=cell,
        fire_year=fire_year, fire_jday=fire_jday,
        plot_start_year=plot_start_year, max_depth_m=max_depth_m)
    ax.set_xlabel("Calendar year")
    ax.set_title(
        f"{role.title()} — ice content ({plot_start_year}–{start_year + tr_years - 1})")

    stem = f"{prefix}-ice-content-{role}"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def read_yearly_cell(run_dir: Path, name: str, cell: tuple[int, int]) -> np.ndarray:
    path = run_dir / f"{name}_yearly_tr.nc"
    if not path.exists():
        return np.array([])
    y, x = cell
    with Dataset(path) as dataset:
        return np.asarray(np.ma.asarray(dataset[name][:, y, x]).filled(np.nan), float)


def annual_means_from_monthly(monthly: np.ndarray, tr_years: int) -> np.ndarray:
    values = []
    for year in range(tr_years):
        chunk = monthly[year * 12:min((year + 1) * 12, monthly.shape[0])]
        values.append(float(np.nanmean(chunk)) if chunk.size else float("nan"))
    return np.asarray(values, float)


def plot_subsidence_paired(
    out_dir: Path,
    *,
    tr_years: int,
    start_year: int,
    plot_start_year: int | None = None,
    fire_jday: int = 240,
    fire_year: int = 2007,
    prefix: str = "anaktuvuk-ice-bracket",
) -> str | None:
    """Cumulative subsidence time series — burned vs unburned control."""
    burned_dir = out_dir / "burned"
    control_dir = out_dir / "control"
    if not (burned_dir / "TKSUBSIDENCE_daily_tr.nc").exists():
        return None
    plot_start_year = plot_start_year if plot_start_year is not None else start_year
    sub_b = _etp.cell_series(_etp.read_daily(burned_dir, "TKSUBSIDENCE"), (0, 0)) * 100.0
    sub_c = _etp.cell_series(_etp.read_daily(control_dir, "TKSUBSIDENCE"), (0, 1)) * 100.0
    ndays = min(sub_b.shape[0], sub_c.shape[0], tr_years * 365)
    years = start_year + np.arange(ndays) / 365.0
    fire_x = fire_year + (fire_jday - 1) / 365.0

    fig, ax = plt.subplots(figsize=(8.8, 3.6), layout="constrained")
    ax.plot(years, sub_c[:ndays], "--", color=MUTED, lw=1.4, label="Unburned control")
    ax.plot(years, sub_b[:ndays], color=ORANGE, lw=1.8, label="Burned CMT05")
    ax.axvline(fire_x, color=ORANGE, ls=":", lw=0.9, alpha=0.75)
    ax.axvspan(2009, 2014, color=BLUE, alpha=0.08, label="2009–2014 LiDAR window")
    ax.set(xlim=(plot_start_year - 0.1, years[-1] + 0.3),
           xlabel="Calendar year", ylabel="Cumulative subsidence (cm)",
           title=f"Paired subsidence ({plot_start_year}–{start_year + tr_years - 1})")
    ax.grid(color=GRID, lw=0.6)
    ax.legend(loc="upper left", fontsize=8, frameon=False)

    stem = f"{prefix}-subsidence-burned-vs-control"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def plot_bgc_paired(
    out_dir: Path,
    *,
    tr_years: int,
    start_year: int,
    plot_start_year: int | None = None,
    fire_jday: int = 240,
    fire_year: int = 2007,
    prefix: str = "anaktuvuk-ice-bracket",
) -> str | None:
    """VEGC, SOC, GPP, and NPP — burned vs control time series."""
    burned_dir = out_dir / "burned"
    control_dir = out_dir / "control"
    if not (burned_dir / "VEGC_yearly_tr.nc").exists():
        return None
    plot_start_year = plot_start_year if plot_start_year is not None else start_year
    years = start_year + np.arange(tr_years) + 0.5
    fire_x = fire_year + (fire_jday - 1) / 365.0

    veg_b = read_yearly_cell(burned_dir, "VEGC", (0, 0))[:tr_years]
    veg_c = read_yearly_cell(control_dir, "VEGC", (0, 1))[:tr_years]
    gpp_b = read_yearly_cell(burned_dir, "GPP", (0, 0))[:tr_years]
    gpp_c = read_yearly_cell(control_dir, "GPP", (0, 1))[:tr_years]
    npp_b = read_yearly_cell(burned_dir, "NPP", (0, 0))[:tr_years]
    npp_c = read_yearly_cell(control_dir, "NPP", (0, 1))[:tr_years]
    soc_b = annual_means_from_monthly(
        monthly_layer_total(burned_dir, "SOC", (0, 0), tr_years), tr_years)
    soc_c = annual_means_from_monthly(
        monthly_layer_total(control_dir, "SOC", (0, 1), tr_years), tr_years)

    fig, axes = plt.subplots(2, 2, figsize=(9.4, 6.8), layout="constrained", sharex=True)
    fig.suptitle(
        f"Paired BGC ({plot_start_year}–{start_year + tr_years - 1})", fontsize=11)

    panels = [
        (axes[0, 0], veg_b, veg_c, "VEGC (g m$^{-2}$)", "Vegetation C"),
        (axes[0, 1], soc_b, soc_c, "Total SOC (g m$^{-2}$)", "Soil organic C (layer sum)"),
        (axes[1, 0], gpp_b, gpp_c, "GPP (g m$^{-2}$ yr$^{-1}$)", "Gross primary production"),
        (axes[1, 1], npp_b, npp_c, "NPP (g m$^{-2}$ yr$^{-1}$)", "Net primary production"),
    ]
    for ax, series_b, series_c, ylabel, title in panels:
        ax.plot(years, series_c, "--", color=MUTED, lw=1.4, label="Control")
        ax.plot(years, series_b, color=ORANGE, lw=1.6, label="Burned")
        ax.axvline(fire_x, color=ORANGE, ls=":", lw=0.9, alpha=0.75)
        ax.axvspan(2009, 2014, color=BLUE, alpha=0.06)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=9)
        ax.grid(color=GRID, lw=0.6)
        ax.set_xlim(plot_start_year - 0.1, years[-1] + 0.4)
        ax.legend(loc="best", fontsize=7, frameon=False)

    for ax in axes[1, :]:
        ax.set_xlabel("Calendar year")

    stem = f"{prefix}-bgc-burned-vs-control"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def plot_organic_horizon_suite(
    out_dir: Path,
    *,
    tr_years: int,
    start_year: int,
    plot_start_year: int | None = None,
    fire_jday: int = 240,
    fire_year: int = 2007,
    prefix: str = "anaktuvuk-ice-bracket",
) -> list[str]:
    """September organic horizon thickness for burned and control."""
    stems = []
    kwargs = dict(
        tr_years=tr_years, start_year=start_year,
        plot_start_year=plot_start_year or start_year,
        fire_jday=fire_jday, fire_year=fire_year,
        out_dir=out_dir, prefix=prefix,
    )
    for role, cell, subdir in [
        ("burned", (0, 0), "burned"),
        ("control", (0, 1), "control"),
    ]:
        run_dir = out_dir / subdir
        if (run_dir / "LAYERTYPE_monthly_tr.nc").exists():
            stems.append(plot_organic_layer_depths(run_dir, cell, role=role, **kwargs))
    return stems


def plot_ice_bracket_paired_diagnostics(
    out_dir: Path,
    *,
    tr_years: int,
    start_year: int,
    plot_start_year: int | None = None,
    fire_jday: int = 240,
    fire_year: int = 2007,
    prefix: str = "anaktuvuk-ice-bracket",
) -> list[str]:
    """Organic horizons, subsidence, and BGC paired panels for ice-bracket mode."""
    kwargs = dict(
        tr_years=tr_years, start_year=start_year, plot_start_year=plot_start_year,
        fire_jday=fire_jday, fire_year=fire_year, prefix=prefix,
    )
    stems = plot_organic_horizon_suite(out_dir, **kwargs)
    sub_stem = plot_subsidence_paired(out_dir, **kwargs)
    if sub_stem:
        stems.append(sub_stem)
    bgc_stem = plot_bgc_paired(out_dir, **kwargs)
    if bgc_stem:
        stems.append(bgc_stem)
    return stems


def plot_ice_bracket_contour_suite(
    run_dir: Path,
    restart: Path,
    cell: tuple[int, int],
    *,
    role: str,
    tr_years: int,
    start_year: int,
    plot_start_year: int | None = None,
    fire_jday: int = 240,
    fire_year: int = 2007,
    out_dir: Path,
    prefix: str = "anaktuvuk-ice-bracket",
) -> list[str]:
    """Soil temperature, liquid water, and ice content contours for one column."""
    kwargs = dict(
        role=role, tr_years=tr_years, start_year=start_year,
        plot_start_year=plot_start_year, fire_jday=fire_jday, fire_year=fire_year,
        out_dir=out_dir, prefix=prefix,
    )
    return [
        plot_soil_temperature_contour(run_dir, restart, cell, **kwargs),
        plot_liquid_water_contour(run_dir, restart, cell, **kwargs),
        plot_ice_content_contour(run_dir, restart, cell, **kwargs),
    ]


def plot_soil_thermal_panel(
    run_dir: Path,
    restart: Path,
    cell: tuple[int, int],
    *,
    role: str,
    tr_years: int,
    start_year: int = 2007,
    plot_start_year: int | None = None,
    fire_jday: int = 240,
    fire_year: int = 2007,
    out_dir: Path,
    max_depth_m: float = 2.0,
    prefix: str = "anaktuvuk-phase1",
    control_run_dir: Path | None = None,
) -> str:
    """Soil temperature depth–time contour (bwr), snow, subsidence, 0 °C ALT."""
    plot_start_year = plot_start_year if plot_start_year is not None else start_year
    z_m, temp_c = _etp.build_temperature_field(run_dir, cell, max_depth_m=max_depth_m)
    nmonths = temp_c.shape[0]
    years = start_year + (np.arange(nmonths) + 0.5) / 12.0
    z_cm = z_m * 100.0

    sub_cm = _etp.cell_series(_etp.read_daily(run_dir, "TKSUBSIDENCE"), cell) * 100.0
    sub_month_cm = monthly_mean_daily(sub_cm, tr_years)
    snow_cm = _etp.cell_series(_etp.read_daily(run_dir, "SNOWTHICK"), cell) * 100.0
    snow_month_cm = monthly_max_snow(snow_cm, tr_years)
    control_snow_month_cm = None
    if control_run_dir is not None and control_run_dir.exists():
        snow_ctl = (_etp.cell_series(_etp.read_daily(control_run_dir, "SNOWTHICK"), (0, 1))
                    * 100.0)
        control_snow_month_cm = monthly_max_snow(snow_ctl, tr_years)
    alt_temp_m = _etp.monthly_alt_from_temperature(z_m, temp_c)
    alt_temp_cm = alt_temp_m * 100.0
    yearly_alt_temp_cm = _etp.yearly_alt_from_temperature(z_m, temp_c, tr_years) * 100.0
    ice_bands = _etp.load_initial_ice_bands(restart, cell)

    finite = temp_c[np.isfinite(temp_c)]
    tlim = float(max(5.0, np.nanpercentile(np.abs(finite), 98))) if finite.size else 10.0
    from matplotlib.colors import TwoSlopeNorm
    norm = TwoSlopeNorm(vcenter=0.0, vmin=-tlim, vmax=tlim)

    fig = plt.figure(figsize=(9.2, 8.0), layout="constrained")
    gs = fig.add_gridspec(3, 1, height_ratios=[0.9, 0.9, 4.8], hspace=0.08)
    ax_snow = fig.add_subplot(gs[0])
    ax_sub = fig.add_subplot(gs[1], sharex=ax_snow)
    ax = fig.add_subplot(gs[2], sharex=ax_snow)

    ax_snow.fill_between(years, 0.0, snow_month_cm, color=BLUE, alpha=0.35, lw=0)
    ax_snow.plot(years, snow_month_cm, color=BLUE, lw=1.4,
                 label=role.title() if control_snow_month_cm is None else "Burned")
    if control_snow_month_cm is not None:
        ax_snow.plot(years, control_snow_month_cm, "--", color=MUTED, lw=1.3,
                     label="Unburned control")
        ax_snow.legend(loc="upper right", fontsize=7, frameon=False)
    ax_snow.set_ylabel("Snow depth\n(cm, mo. max)")
    ax_snow.grid(color=GRID, lw=0.6)
    ax_snow.set_xlim(plot_start_year - 0.1, years[-1] + 0.4)
    ax_snow.set_title(
        f"{role.title()} — soil thermal state ({plot_start_year}–{start_year + tr_years - 1})")
    plt.setp(ax_snow.get_xticklabels(), visible=False)

    ax_sub.plot(years, sub_month_cm, color=ORANGE, lw=1.4)
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

    fire_x = fire_year + (fire_jday - 1) / 365.0
    for axis in (ax_snow, ax_sub, ax):
        axis.axvline(fire_x, color=ORANGE, ls=":", lw=0.9, alpha=0.8)

    ax.set_ylabel("Depth below surface (cm)")
    ax.set_xlabel("Calendar year")
    ax.invert_yaxis()
    ax.set_ylim(max_depth_m * 100.0, 0.0)
    ax.grid(color=GRID, lw=0.4, alpha=0.5)
    ax.legend(loc="lower right", fontsize=7, frameon=False)

    stem = f"{prefix}-soil-thermal-{role}"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def plot_soil_carbon_water_panel(
    run_dir: Path,
    cell: tuple[int, int],
    *,
    role: str,
    tr_years: int,
    start_year: int = 2000,
    plot_start_year: int | None = None,
    fire_jday: int = 240,
    fire_year: int = 2007,
    out_dir: Path,
    max_depth_m: float = 2.0,
    prefix: str = "anaktuvuk-phase1",
) -> str:
    """Combusted C, total SOC, and volumetric liquid/ice content depth–time panels."""
    from matplotlib.colors import Normalize

    plot_start_year = plot_start_year if plot_start_year is not None else start_year
    nmonths = tr_years * 12
    years = start_year + (np.arange(nmonths) + 0.5) / 12.0

    burn_flux = _etp.cell_series(_etp.read_monthly(run_dir, "BURNSOIL2AIRC"), cell)
    burn_flux = burn_flux[:nmonths]
    burn_cum = np.cumsum(np.nan_to_num(burn_flux, nan=0.0))
    soc_total = monthly_layer_total(run_dir, "SOC", cell, tr_years)

    z_m, lwc = build_layer_profile_field(
        run_dir, "LWCLAYER", cell, tr_years=tr_years, max_depth_m=max_depth_m)
    _, iwc = build_layer_profile_field(
        run_dir, "IWCLAYER", cell, tr_years=tr_years, max_depth_m=max_depth_m)
    z_cm = z_m * 100.0

    fig = plt.figure(figsize=(9.2, 10.0), layout="constrained")
    gs = fig.add_gridspec(4, 1, height_ratios=[0.9, 0.9, 4.0, 4.0], hspace=0.08)
    ax_burn = fig.add_subplot(gs[0])
    ax_soc = fig.add_subplot(gs[1], sharex=ax_burn)
    ax_lwc = fig.add_subplot(gs[2], sharex=ax_burn)
    ax_iwc = fig.add_subplot(gs[3], sharex=ax_burn)

    ax_burn.fill_between(years, 0.0, burn_cum, color=ORANGE, alpha=0.25, lw=0)
    ax_burn.plot(years, burn_cum, color=ORANGE, lw=1.5, label="Cumulative combusted soil C")
    ax_burn.set_ylabel("Combusted C\n(g m$^{-2}$)")
    ax_burn.grid(color=GRID, lw=0.6)
    ax_burn.legend(loc="upper left", fontsize=7, frameon=False)
    ax_burn.set_title(
        f"{role.title()} — soil carbon and moisture ({plot_start_year}–"
        f"{start_year + tr_years - 1})")
    plt.setp(ax_burn.get_xticklabels(), visible=False)

    ax_soc.plot(years, soc_total, color=TEAL, lw=1.5, label="Total soil organic C")
    ax_soc.set_ylabel("Total SOC\n(g m$^{-2}$)")
    ax_soc.grid(color=GRID, lw=0.6)
    ax_soc.legend(loc="upper right", fontsize=7, frameon=False)
    plt.setp(ax_soc.get_xticklabels(), visible=False)

    xx, zz = np.meshgrid(years, z_cm)
    lwc_finite = lwc[np.isfinite(lwc)]
    lwc_vmax = float(np.nanpercentile(lwc_finite, 98)) if lwc_finite.size else 0.5
    lwc_vmax = max(lwc_vmax, 0.05)
    mesh_lwc = ax_lwc.pcolormesh(
        xx, zz, lwc.T, shading="auto", cmap="Blues",
        norm=Normalize(vmin=0.0, vmax=lwc_vmax), rasterized=True)
    cbar_lwc = fig.colorbar(mesh_lwc, ax=ax_lwc, pad=0.01, fraction=0.025)
    cbar_lwc.set_label("Liquid water (m$^3$ m$^{-3}$)")
    ax_lwc.set_ylabel("Depth (cm)")
    ax_lwc.invert_yaxis()
    ax_lwc.set_ylim(max_depth_m * 100.0, 0.0)
    ax_lwc.grid(color=GRID, lw=0.4, alpha=0.5)

    iwc_finite = iwc[np.isfinite(iwc)]
    iwc_vmax = float(np.nanpercentile(iwc_finite, 98)) if iwc_finite.size else 0.5
    iwc_vmax = max(iwc_vmax, 0.05)
    mesh_iwc = ax_iwc.pcolormesh(
        xx, zz, iwc.T, shading="auto", cmap="PuBu",
        norm=Normalize(vmin=0.0, vmax=iwc_vmax), rasterized=True)
    cbar_iwc = fig.colorbar(mesh_iwc, ax=ax_iwc, pad=0.01, fraction=0.025)
    cbar_iwc.set_label("Ice content (m$^3$ m$^{-3}$)")
    ax_iwc.set_ylabel("Depth (cm)")
    ax_iwc.set_xlabel("Calendar year")
    ax_iwc.invert_yaxis()
    ax_iwc.set_ylim(max_depth_m * 100.0, 0.0)
    ax_iwc.grid(color=GRID, lw=0.4, alpha=0.5)

    fire_x = fire_year + (fire_jday - 1) / 365.0
    for axis in (ax_burn, ax_soc, ax_lwc, ax_iwc):
        axis.set_xlim(plot_start_year - 0.1, years[-1] + 0.4)
        axis.axvline(fire_x, color=ORANGE, ls=":", lw=0.9, alpha=0.8)

    stem = f"{prefix}-soil-carbon-water-{role}"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


ORGANIC_MOSS = "#4DAF4A"
ORGANIC_FIBRIC = "#C4A574"
ORGANIC_HUMIC = "#8B5A2B"
ORGANIC_TOTAL = "#171717"


def read_layer_monthly(run_dir: Path, name: str) -> np.ndarray:
    with Dataset(run_dir / f"{name}_monthly_tr.nc") as dataset:
        data = np.ma.asarray(dataset[name][:])
        if np.issubdtype(data.dtype, np.integer):
            return np.asarray(data.filled(-1), float)
        return np.asarray(data.filled(np.nan), float)


def organic_depth_cm_series(run_dir: Path, cell: tuple[int, int], tr_years: int):
    """Return monthly moss/fibric/humic/total organic thickness (cm) from layer outputs."""
    dz = read_layer_monthly(run_dir, "LAYERDZ")
    ltype_path = run_dir / "LAYERTYPE_monthly_tr.nc"
    if not ltype_path.exists():
        raise FileNotFoundError(f"Missing LAYERTYPE monthly output in {run_dir}")
    ltype = read_layer_monthly(run_dir, "LAYERTYPE")
    y, x = cell
    nmonths = min(tr_years * 12, dz.shape[0])
    moss = np.zeros(nmonths)
    fibric = np.zeros(nmonths)
    humic = np.zeros(nmonths)
    for t in range(nmonths):
        for j in range(dz.shape[1]):
            thickness_cm = float(dz[t, j, y, x]) * 100.0
            if thickness_cm <= 0.0:
                continue
            raw_type = ltype[t, j, y, x]
            layer_type = int(raw_type) if np.isfinite(raw_type) and raw_type >= 0 else 3
            if layer_type == 0:
                moss[t] += thickness_cm
            elif layer_type == 1:
                fibric[t] += thickness_cm
            elif layer_type == 2:
                humic[t] += thickness_cm
    total = moss + fibric + humic
    return {
        "moss_cm": moss,
        "fibric_cm": fibric,
        "humic_cm": humic,
        "total_cm": total,
    }


def september_annual(series: np.ndarray, tr_years: int, start_year: int) -> tuple[np.ndarray, np.ndarray]:
    """Sample each September and return calendar years + values."""
    years = []
    values = []
    for year in range(tr_years):
        month = year * 12 + 8
        if month >= series.size:
            break
        years.append(start_year + year + 8 / 12.0)
        values.append(float(series[month]))
    return np.asarray(years, float), np.asarray(values, float)


def plot_organic_layer_depths(
    run_dir: Path,
    cell: tuple[int, int],
    *,
    role: str,
    tr_years: int,
    start_year: int = 2000,
    plot_start_year: int = 2000,
    fire_jday: int = 240,
    fire_year: int = 2007,
    out_dir: Path,
    prefix: str = "anaktuvuk-phase1",
) -> str:
    """Stacked moss / fibric / humic organic horizons with total depth."""
    depths = organic_depth_cm_series(run_dir, cell, tr_years)
    moss_y, moss = september_annual(depths["moss_cm"], tr_years, start_year)
    _, fibric = september_annual(depths["fibric_cm"], tr_years, start_year)
    _, humic = september_annual(depths["humic_cm"], tr_years, start_year)
    _, total = september_annual(depths["total_cm"], tr_years, start_year)

    fig, ax = plt.subplots(figsize=(8.8, 3.8), layout="constrained")
    ax.fill_between(moss_y, 0.0, humic, color=ORGANIC_HUMIC, alpha=0.85, lw=0,
                    label="Humic (deep)")
    ax.fill_between(moss_y, humic, humic + fibric, color=ORGANIC_FIBRIC, alpha=0.85, lw=0,
                    label="Fibric (shallow)")
    ax.fill_between(moss_y, humic + fibric, total, color=ORGANIC_MOSS, alpha=0.85, lw=0,
                    label="Moss")
    ax.plot(moss_y, total, color=ORGANIC_TOTAL, lw=1.6, label="Total organic")
    ax.axvline(fire_year + (fire_jday - 1) / 365.0, color=ORANGE, ls=":", lw=0.9,
               label="2007 fire")
    ax.set(xlim=(plot_start_year - 0.1, moss_y[-1] + 0.4),
           xlabel="Calendar year", ylabel="Organic layer depth (cm, September)",
           title=f"{role.title()} — organic horizon thickness ({plot_start_year}–"
                   f"{start_year + tr_years - 1})")
    ax.grid(color=GRID, lw=0.6)
    ax.legend(loc="upper right", fontsize=7, ncol=2, frameon=False)
    slug = "burned" if "burn" in role.lower() else "control"
    stem = f"{prefix}-organic-layers-{slug}"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def resolve_climate_paths(out_dir: Path, bias_c: float | None) -> tuple[Path | None, Path | None]:
    """Locate bias-tagged or legacy North Slope climate NetCDF files."""
    if bias_c is not None:
        tag = f"{bias_c:.1f}".replace(".", "p")
        full = out_dir / f"north-slope-climate-full-{tag}.nc"
        tr = out_dir / f"north-slope-climate-tr-{tag}.nc"
        if full.exists() and tr.exists():
            return full, tr
    for full, tr in [
        (out_dir / "north-slope-climate-full.nc", out_dir / "north-slope-climate-tr.nc"),
        (out_dir / "north-slope-climate-full-7p5.nc", out_dir / "north-slope-climate-tr-7p5.nc"),
    ]:
        if full.exists() and tr.exists():
            return full, tr
    return None, None


def generate_diagnostic_figures(
    out_dir: Path,
    *,
    full_climate: Path | None = None,
    tr_climate: Path | None = None,
    restart: Path | None = None,
    tr_years: int = 15,
    start_year: int = 2007,
    tr_end_year: int | None = None,
    fire_jday: int = 240,
    fire_year: int = 2007,
    bias_c: float | None = None,
    prefix: str = "anaktuvuk-phase1",
    profile_probe_dir: Path | None = None,
    profile_start_year: int = 2000,
    profile_tr_years: int | None = None,
    plot_start_year: int = 2000,
    copy_to_report: bool = True,
) -> list[str]:
    out_dir = out_dir.resolve()
    stems: list[str] = []

    if full_climate is None or tr_climate is None:
        resolved_full, resolved_tr = resolve_climate_paths(out_dir, bias_c)
        full_climate = full_climate or resolved_full
        tr_climate = tr_climate or resolved_tr
    if full_climate and tr_climate and full_climate.exists() and tr_climate.exists():
        climate_tr_years = (tr_end_year - start_year + 1) if tr_end_year else tr_years
        sp_years = read_climate_series(full_climate)["nyears"]
        stems.append(plot_climate_inputs(
            out_dir, full_climate, tr_climate,
            tr_start_year=start_year, tr_years=climate_tr_years, tr_end_year=tr_end_year,
            bias_c=bias_c, prefix=prefix,
            sp_start_year=start_year - sp_years))

    restart = restart or out_dir / "restart-yedoma-ice.nc"
    profile_root = profile_probe_dir or (out_dir / "organic-layer-probe")
    if profile_tr_years is None:
        profile_tr_years = (
            (tr_end_year - profile_start_year + 1) if tr_end_year
            else tr_years
        )

    if profile_root.exists() and (profile_root / "burned").exists():
        stems.append(plot_snow_paired(
            out_dir, tr_years=profile_tr_years, start_year=profile_start_year,
            plot_start_year=plot_start_year, fire_jday=fire_jday, fire_year=fire_year,
            prefix=prefix, run_root=profile_root))
        for role, cell, subdir in [
            ("burned", (0, 0), "burned"),
            ("control", (0, 1), "control"),
        ]:
            run_dir = profile_root / subdir
            if not _etp.has_profile_outputs(run_dir):
                continue
            control_dir = profile_root / "control" if role == "burned" else None
            stems.append(plot_soil_thermal_panel(
                run_dir, restart, cell,
                role=role, tr_years=profile_tr_years, start_year=profile_start_year,
                plot_start_year=plot_start_year, fire_jday=fire_jday, fire_year=fire_year,
                out_dir=out_dir, prefix=prefix, control_run_dir=control_dir))
            if (run_dir / "IWCLAYER_monthly_tr.nc").exists():
                stems.append(plot_soil_carbon_water_panel(
                    run_dir, cell,
                    role=role, tr_years=profile_tr_years,
                    start_year=profile_start_year, plot_start_year=plot_start_year,
                    fire_jday=fire_jday, fire_year=fire_year,
                    out_dir=out_dir, prefix=prefix))
            ltype_path = run_dir / "LAYERTYPE_monthly_tr.nc"
            if (ltype_path.exists()
                    and not prefix.startswith("anaktuvuk-ice-bracket")):
                stems.append(plot_organic_layer_depths(
                    run_dir, cell,
                    role=role, tr_years=profile_tr_years,
                    start_year=profile_start_year, plot_start_year=plot_start_year,
                    fire_jday=fire_jday, fire_year=fire_year,
                    out_dir=out_dir, prefix=prefix))
            if (prefix.startswith("anaktuvuk-ice-bracket")
                    and (run_dir / "IWCLAYER_monthly_tr.nc").exists()):
                stems.extend(plot_ice_bracket_contour_suite(
                    run_dir, restart, cell,
                    role=role, tr_years=profile_tr_years,
                    start_year=profile_start_year, plot_start_year=plot_start_year,
                    fire_jday=fire_jday, fire_year=fire_year,
                    out_dir=out_dir, prefix=prefix))
    elif (out_dir / "burned").exists() and (out_dir / "control").exists():
        stems.append(plot_snow_paired(
            out_dir, tr_years=tr_years, start_year=start_year,
            plot_start_year=plot_start_year, fire_jday=fire_jday, fire_year=fire_year,
            prefix=prefix))
        for role, cell, subdir in [
            ("burned", (0, 0), "burned"),
            ("control", (0, 1), "control"),
        ]:
            run_dir = out_dir / subdir
            if not _etp.has_profile_outputs(run_dir):
                continue
            control_dir = out_dir / "control" if role == "burned" else None
            stems.append(plot_soil_thermal_panel(
                run_dir, restart, cell,
                role=role, tr_years=tr_years, start_year=start_year,
                plot_start_year=plot_start_year, fire_jday=fire_jday, fire_year=fire_year,
                out_dir=out_dir, prefix=prefix, control_run_dir=control_dir))
            if (run_dir / "IWCLAYER_monthly_tr.nc").exists():
                stems.append(plot_soil_carbon_water_panel(
                    run_dir, cell,
                    role=role, tr_years=tr_years, start_year=start_year,
                    plot_start_year=plot_start_year, fire_jday=fire_jday, fire_year=fire_year,
                    out_dir=out_dir, prefix=prefix))
            if (prefix.startswith("anaktuvuk-ice-bracket")
                    and (run_dir / "IWCLAYER_monthly_tr.nc").exists()):
                stems.extend(plot_ice_bracket_contour_suite(
                    run_dir, restart, cell,
                    role=role, tr_years=tr_years, start_year=start_year,
                    plot_start_year=plot_start_year, fire_jday=fire_jday, fire_year=fire_year,
                    out_dir=out_dir, prefix=prefix))

    if (out_dir / "burned").exists() and (out_dir / "control").exists():
        ice_stem = plot_excess_ice_degradation(
            out_dir, restart,
            tr_years=tr_years, start_year=start_year,
            fire_jday=fire_jday, fire_year=fire_year,
            plot_start_year=plot_start_year, prefix=prefix)
        if ice_stem:
            stems.append(ice_stem)
        if prefix.startswith("anaktuvuk-ice-bracket"):
            stems.extend(plot_ice_bracket_paired_diagnostics(
                out_dir, tr_years=tr_years, start_year=start_year,
                plot_start_year=plot_start_year, fire_jday=fire_jday, fire_year=fire_year,
                prefix=prefix))

    if copy_to_report and stems:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        for stem in stems:
            for ext in ("png", "svg"):
                src = out_dir / f"{stem}.{ext}"
                if src.exists():
                    shutil.copy2(src, REPORT_DIR / src.name)
        for seasonal_name in ("anaktuvuk-seasonal-forcing.png", "anaktuvuk-seasonal-forcing.svg"):
            src = out_dir / seasonal_name
            if src.exists():
                shutil.copy2(src, REPORT_DIR / seasonal_name)
    return stems
