"""Plot EML CiPEHR TEM climate driver inputs for validation reports."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset

ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = ROOT / "docs_src/thermokarst"

TREATMENTS = ("control", "air_warming", "soil_warming", "air_soil_warming")
TREAT_COLOR = {
    "control": "#1F6F5F",
    "air_warming": "#4C78A8",
    "soil_warming": "#D55E00",
    "air_soil_warming": "#777772",
}
TREAT_LABEL = {
    "control": "Control",
    "air_warming": "Air warming",
    "soil_warming": "Soil warming",
    "air_soil_warming": "Air + soil warming",
}
CLIMATE_START_YEAR = 2004


def read_climate_series(climate_path: Path, variable: str, cell: tuple[int, int] = (0, 0)):
    with Dataset(climate_path) as dataset:
        return np.asarray(dataset[variable][:, cell[0], cell[1]], float)


def month_index(year: int, month: int = 1) -> int:
    return (year - CLIMATE_START_YEAR) * 12 + (month - 1)


def plot_climate_inputs(
    result_dir: Path,
    *,
    start_year: int = 2009,
    end_year: int = 2018,
    cell: tuple[int, int] = (0, 0),
    treatments: tuple[str, ...] = TREATMENTS,
    out_dir: Path | None = None,
) -> str:
    """Four-panel monthly climate drivers for the Rodenhizer TR window."""
    out_dir = out_dir or result_dir
    i0 = month_index(start_year, 1)
    i1 = month_index(end_year, 12) + 1
    nmonths = i1 - i0
    years = start_year + (np.arange(nmonths) + 0.5) / 12.0

    panels = [
        ("tair", "Air temperature (°C)", "tair"),
        ("nirr", "Shortwave radiation (W m$^{-2}$)", "nirr"),
        ("vapor_press", "Vapor pressure (hPa)", "vapor_press"),
        ("precip", "Precipitation (mm month$^{-1}$)", "precip"),
    ]

    fig, axes = plt.subplots(4, 1, figsize=(9.2, 8.8), sharex=True, layout="constrained")
    for ax, (var, ylabel, _) in zip(axes, panels):
        for treatment in treatments:
            climate_path = result_dir / f"eml-climate-{treatment}.nc"
            if not climate_path.exists():
                continue
            series = read_climate_series(climate_path, var, cell)[i0:i1]
            ax.plot(
                years, series,
                color=TREAT_COLOR[treatment],
                lw=1.2,
                label=TREAT_LABEL[treatment],
            )
        ax.set_ylabel(ylabel)
        ax.grid(color="#E4E7E5", lw=0.6)

    axes[0].set_title(f"EML climate inputs ({start_year}–{end_year}, BNZ:453 + treatment bias)")
    axes[0].legend(loc="upper right", fontsize=7, ncol=2, frameon=False)
    axes[-1].set_xlabel("Calendar year")

    stem = "eml-climate-inputs"
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return stem


def copy_report_figure(result_dir: Path, stem: str) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        src = result_dir / f"{stem}.{ext}"
        if src.exists():
            shutil.copy2(src, REPORT_DIR / src.name)


def generate_climate_figures(
    result_dir: Path,
    *,
    start_year: int = 2009,
    end_year: int = 2018,
    cell: tuple[int, int] = (0, 0),
    copy_to_report: bool = True,
) -> str:
    stem = plot_climate_inputs(
        result_dir, start_year=start_year, end_year=end_year, cell=cell)
    if copy_to_report:
        copy_report_figure(result_dir, stem)
    return stem
