# Barrow CRREL subsidence experiment spec (DVM-DOS-TEM)

**Date:** 2026-09-18

**Repository:** `/Users/EJafarov/projects/TEM_abrupt_thaw_dev`

**Scientific reference:** Streletskiy et al. (2016),
*Thaw Subsidence in Undisturbed Tundra Landscapes, Barrow, Alaska, 1962–2015*,
Permafrost and Periglacial Processes, DOI [10.1002/ppp.1918](https://doi.org/10.1002/ppp.1918)

**Status:** Phases 0–2 implemented and reported ([barrow-validation-report.md](barrow-validation-report.md))

## Purpose

Set up a **Barrow Environmental Observatory (BEO) CRREL transect** experiment in
DVM-DOS-TEM that compares four undisturbed polygon-tundra plots (**34, 37, 40, 44**)
under shared Barrow climate forcing, with thermokarst subsidence and active-layer
depth as primary outputs.

This is an **isotropic thaw-subsidence validation study**, not a reproduction of
dGPS survey geometry or frost-heave mechanics. TEM runs four **independent columns**
on the same climate file. It does **not** implement:

- differential GPS survey sampling at five points per plot;
- frost heave or seasonal uplift from segregation-ice accretion;
- snow redistribution between plot elevations;
- lateral heat or water flux between adjacent polygons.

Success criteria are staged:

1. **Phase 0 (pipeline):** four cells complete; ice runs subside; reference runs do not.
2. **Phase 1 (validation window):** cumulative subsidence and plot ordering over
   **2003–2015** match Streletskiy et al. within calibrated bounds.
3. **Phase 2 (full record):** long-term stability over **1962–2003** and warming
   response over **2003–2015** are qualitatively consistent with the paper.

## Site metadata

| Field | Value |
|---|---|
| Name | Barrow CRREL transect (CALM U2) |
| Location | 71°19′N, 156°35′W (BEO, ~5 km E of Utqiaġvik) |
| Permafrost zone | Continuous, ice-rich coastal plain |
| Mean annual air temperature | −9.7 °C (July 4.5 °C; February −26.4 °C) |
| Organic layer thickness | ~13 cm (silty loam, graminoid–moss tundra) |
| Transient layer | top 20–55 cm (mean **34 cm**); thickness **23 cm** |
| Ice volume at permafrost table | **>70 %** |
| Climate station | NWS Barrow Airport (USW00027502), ~7 km from plots |
| Snow survey | CALM Barrow U2 grid (15 points near plots) |

### Plot characteristics (Streletskiy et al. 2016)

| Plot | Landscape | Relative elevation | Soil moisture | 2003 elevation (cm) |
|---:|---|---|---|---:|
| **34** | Low-centre polygon | lowest | wettest; frost boils | 368.2 |
| **37** | Low-centre polygon | low | wet; frost boils | 372.7 |
| **40** | Polygonised tundra | moderate | drier | 392.1 |
| **44** | Polygonised tundra | highest | driest | 423.9 |

## Observation targets (from Streletskiy et al. 2016, Table 1)

Store these as bundled CSV under `experiments/thermokarst/barrow_validation/obs/` so
the harness can gate without re-parsing the PDF.

### Long-term elevation change (1962 → 2003)

| Plot | Δ elevation (cm) | Notes |
|---:|---:|---|
| 34 | −3.4 | subsidence |
| 37 | −4.3 | subsidence |
| 40 | −3.9 | subsidence |
| 44 | +4.9 | heave (snow redistribution) |

Paper interpretation: 41-year net change is within 2003–2015 interannual variability
→ **net stability** over the historical period.

### Subsidence trends (2003–2015)

| Plot | Trend (cm yr⁻¹) | Significance | Approx. net subsidence (cm) |
|---:|---:|---|---:|
| 34 | **−1.0** | p < 0.10 | ~15 |
| 37 | −0.5 | p < 0.05 | ~8 |
| 40 | −0.4 | p < 0.05 | ~8 |
| 44 | −0.5 | p < 0.05 | ~9 |

All four plots show negative elevation trends. Warm summers **2004, 2007, 2012**
account for ~60 % of total subsidence.

### Cumulative elevation change relative to 2003 (cm)

| Year | Plot 34 | Plot 37 | Plot 40 | Plot 44 |
|---:|---:|---:|---:|---:|
| 2004 | −4.1 | −3.7 | −3.0 | −5.0 |
| 2005 | −2.0 | −0.4 | −1.8 | −1.2 |
| 2006 | −5.1 | −1.0 | −2.7 | −3.6 |
| 2007 | −6.2 | −8.8 | −4.8 | −5.7 |
| 2008 | −5.4 | −1.6 | −2.1 | −4.3 |
| 2009 | −8.9 | −5.4 | −7.6 | −7.3 |
| 2010 | −5.8 | −2.6 | −5.7 | −4.3 |
| 2011 | −4.7 | 0.0 | +2.1 | −1.5 |
| **2012** | **−17.4** | **−12.0** | **−10.1** | **−13.5** |
| 2013 | −11.6 | −6.1 | −4.5 | −6.2 |
| 2014 | −7.5 | −3.8 | −3.5 | −3.6 |
| 2015 | −14.9 | −8.0 | −8.1 | −8.7 |

### Active-layer thickness at survey date (cm, five probe points per plot)

| Year | Plot 34 | Plot 37 | Plot 40 | Plot 44 | Mean |
|---:|---:|---:|---:|---:|---:|
| 2003 | 27.2 | 31.2 | 29.6 | 25.4 | 28.4 |
| 2004 | 42.4 | 40.8 | 41.0 | 37.8 | 40.5 |
| 2007 | 37.6 | 35.6 | 32.4 | 33.2 | 34.7 |
| 2012 | 43.8 | 46.6 | 39.2 | 39.8 | 42.4 |
| 2015 | 39.6 | 39.8 | 39.0 | 33.4 | 37.9 |
| Mean 2003–15 | 37.7 | 39.2 | 36.5 | 34.1 | 36.9 |

ALT trend over 2003–15: +0.3 to +0.5 cm yr⁻¹ (not significant individually).

### Barrow climate summary (NWS, Table 1)

| Variable | 2003–15 mean | 2003–15 trend |
|---|---:|---:|
| Mean annual air T (°C) | −9.9 | +0.06 °C yr⁻¹ |
| Mean summer air T (°C) | 4.2 | +0.03 °C yr⁻¹ |
| Snow depth (cm, spring CALM) | 40.3 | +0.8 cm yr⁻¹ |
| Degree-days freezing (DDF) | 4086 | −22.2 d yr⁻¹ |
| Degree-days thawing (DDT) | 447 | +1.8 d yr⁻¹ |

## Experiment matrix

Run on a **four-cell grid** (one cell per CRREL plot):

| Case | Cells | Thermokarst | Role |
|---|---|---|---|
| `ref` | 34, 37, 40, 44 | disabled | No-excess-ice reference |
| `uniform-ice` | all four | enabled, same ice | Sensitivity to shared ice inventory |
| `paired-wet-dry` | 34/37 wet, 40/44 dry | enabled, per-cell ice | **Primary** landscape contrast |
| `calibrated` | all four | enabled, per-plot ice | Phase 1 validation target |

**Primary case:** `calibrated` — each cell receives plot-specific excess-ice mass
after equilibrium, then runs the Barrow 2003–2015 transient (Phase 1) or full
1962–2015 record (Phase 2).

### Known TEM approximations vs Streletskiy observations

| Streletskiy process | TEM Phase 1–2 |
|---|---|
| dGPS net elevation (heave + subsidence) | ❌ compare `TKSUBSIDENCE` only |
| Frost heave from segregation ice | ❌ |
| Snow redistribution by elevation | ❌ manual snow tuning per column only |
| Mechanical ALT probing | ✅ approximate via `TKFRONT` thaw depth |
| ALT corrected for subsidence | ✅ compare `TKFRONT` + `TKSUBSIDENCE` |
| Thaw into transient layer / ice wedges | ✅ excess-ice melt at calibrated depth |
| Isotropic thaw subsidence | ✅ `TKSUBSIDENCE` |
| Undisturbed tundra (no fire) | ✅ control runs only; no `dsb` |

## Forcing

### Do not use raw Toolik climate

The bundled Toolik demo file
(`demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/historic-climate.nc`)
is **~6 °C too warm in summer** relative to Barrow for 2003–2015. Use it only in
Phase 0 pipeline tests, never for scientific validation gates.

| Metric (2003–15) | Barrow (obs.) | Toolik (demo) | Bias |
|---|---:|---:|---:|
| Mean annual T | −9.9 °C | −8.2 °C | +1.8 °C |
| Mean summer T | 4.2 °C | 10.5 °C | **+6.3 °C** |

### Source protocol (Phase 1+)

1. Download daily NWS Barrow Airport (USW00027502) temperature and precipitation
   from NOAA/NCEI (paper used data back to 1960).
2. Aggregate to **monthly** `tair`, `precip`, `nirr`, `vapor_press` on TEM's `time`
   dimension (same layout as Toolik demo files).
3. Optionally bias-correct CRU/GSWP3 reanalysis to the NWS record for years before
   continuous station coverage; the paper used 1960+ directly from NWS.
4. Build a separate **snow-depth forcing** or tune snow parameters using CALM U2
   spring snow surveys (15 points, 2003–15 mean 40.3 cm, trend +0.8 cm yr⁻¹).
5. CO₂: use the existing historic CO₂ file sliced to the transient window.

Target file: `experiments/thermokarst/barrow_validation/barrow-climate.nc`

Phase 0 may copy the Toolik NetCDF structure and overwrite monthly `tair` with a
Barrow-like synthetic template:

```python
# Barrow-like monthly mean air temperature (°C) and precipitation (mm)
tair   = [-26, -25, -22, -14,  -3,   3,   5,   4,   0,  -8, -18, -24]
precip = [  6,   5,   5,   6,   8,  12,  15,  14,  10,   8,   7,   6]  # sum ≈ 101 mm
nirr   = [  0,   1,   4,  12,  18,  20,  16,  10,   4,   1,   0,   0]
```

Replace with NWS-derived monthly fields before Phase 1 gates.

### Recommended staging

| Stage | Spin-up | Transient | Climate source | Notes |
|---|---:|---:|---|---|
| **Phase 0** | 1 PR + 5 EQ | 13 TR (2003–15) | thaw-capable synthetic periodic template; **100 kg m⁻² lens at 0.08 m** | prove 4-cell pipeline |
| **Phase A** | 1 PR + 30 EQ | 13 TR (2003–15) | NWS Barrow monthly | ALT calibration via CMT n-factors; no ice |
| **Phase 1** | 1 PR + 30 EQ | 13 TR (2003–15) | NWS Barrow monthly | primary validation (after Phase A) |
| **Phase 2a** | 1 PR + 50 EQ | 54 TR (1962–2015) | NWS Barrow monthly | full paper record |
| **Phase 2b** | resume Phase 2a | +85 SC | AR5 projection (optional) | forward extension only |

Slice the transient from the master climate file using `bgc.slice_driver_years()`:

```python
# Phase 1: calendar years 2003–2015 inclusive → 13 years, source index 102
slice_driver_years(barrow_climate, dest, start=102, nyears=13)
```

### Phase A — ALT calibration (n-factor)

Calibrate **September max thaw depth** (`TKFRONT`) against Streletskiy mechanical
probing **before** any excess-ice / subsidence experiment:

- **Thermokarst on** for spin-up and transient (enables `TKFRONT` output); no ice injection.
- **Parameters:** fork `parameters/cmt_*.txt` into
  `experiments/thermokarst/barrow_validation/parameters/` and patch
  `nfactor(s)` / `nfactor(w)` in `cmt_envground.txt` for CMT05 (plots 40, 44) and
  CMT06 (plots 34, 37).
- **Gates (hard):** all four cells complete; subsidence &lt; 1 mm over TR.
- **Gates (soft):** mean ALT 33–42 cm; per-plot mean 20–50 cm; RMSE &lt; 12 cm;
  warm-year deepening.

Commands:

```sh
make thermokarst-barrow-alt-calibration     # baseline with default n-factors
make thermokarst-barrow-alt-calibrate       # 56-point nfactor_s sweep + 30-yr confirm
```

Calibration output: `experiments/thermokarst/barrow_validation/barrow-alt-calibration.json`.
Phases 1–2 automatically use this parameter directory when the file exists.

## Spatial setup

### Grid

| Cell | Plot | CMT (initial) | Drainage | Slope | Rationale |
|---|---|---:|---:|---:|---|
| (0, 0) | 34 | **CMT06** wet sedge | 1 (poor) | 0° | wettest, lowest |
| (0, 1) | 37 | **CMT06** wet sedge | 1 (poor) | 0° | wet, frost boils |
| (1, 0) | 40 | **CMT05** tussock | 0 (well) | 0° | drier, moderate elevation |
| (1, 1) | 44 | **CMT05** tussock | 0 (well) | 0° | driest, highest |

- `run-mask-four-cells.nc`: activate all four cells above.
- `topo.nc`: **slope = 0°** (flat coastal plain; not the 30° Toolik default).
- Confirm CMT choices against `parameters/cmt_*.txt` before locking; CMT06 is
  calibrated for Toolik-area wet sedge but is the closest wet-tundra analog.

Document final CMT and drainage choices in the validation summary JSON when
implemented.

## Excess ice

### Paper geometry (for calibration targets)

| Parameter | Barrow value | TEM use |
|---|---:|---|
| Transient layer top | 20–55 cm (mean **34 cm**) | `top_depth` or injection depth |
| Transient layer thickness | **23 cm** | conceptual subsidence ceiling |
| Ice volume at table | **>70 %** | convert to kg m⁻² inventory |
| Estimated transient-layer ice | **~148 kg m⁻²** | 0.23 m × 0.70 × 917 kg m⁻³ |

Observed 2003–15 net subsidence of **8–15 cm** implies **partial** melt of the
transient layer, not full removal.

### TEM thermokarst configuration

Inject excess ice **after equilibrium**, before transient, using per-cell restart
patches (`bgc.inject_excess_mass()` or `inject_excess()`):

```json
"thermokarst": {
  "enabled": true,
  "excess_fraction": 0.0,
  "top_depth": 0.20,
  "bottom_depth": 1.00
}
```

Starting calibration (adjust in Phase 1):

| Plot | Initial mass (kg m⁻²) | Injection depth (m) | Notes |
|---:|---:|---:|---|
| 34 | 120–160 | 0.34–0.45 | highest subsidence; may reach ice wedges |
| 37 | 100–140 | 0.34–0.40 | wet low-centre polygon |
| 40 | 80–120 | 0.30–0.38 | drier; slower subsidence |
| 44 | 80–120 | 0.25–0.35 | highest elevation; less ice-rich in paper |
| REF | 0 | — | thermokarst disabled |

Alternative: use `inject_excess(restart, fraction=0.25, top=0.25, bottom=0.55)` to
fill the transient-layer depth band rather than a point lens.

**Calibration procedure:**

1. Run Phase 1 with a shared mass (100 kg m⁻² at 0.34 m) on all four cells.
2. Adjust mass until mean simulated 2003–15 subsidence is **8–12 cm**.
3. Split mass by plot (34 > 37 ≥ 40 ≈ 44) to match ordering.
4. If rates are too slow even at 150 kg m⁻², enable `dsl` and verify thaw depth
   reaches the injection layer in warm years (2004, 2007, 2012).

## Model stages and switches

Match Streletskiy scope: **undisturbed tundra, no fire, no BGC** for Phase 1.

```json
"stage_settings": {
  "pr": { "env": true,  "bgc": false, "nfeed": false, "avlnflg": false,
          "baseline": false, "dsb": false, "dsl": true,  "dyn_lai": false },
  "eq": { "env": true,  "bgc": false, "nfeed": false, "avlnflg": false,
          "baseline": true,  "dsb": false, "dsl": true,  "dyn_lai": false },
  "tr": { "env": true,  "bgc": false, "nfeed": false, "avlnflg": false,
          "baseline": false, "dsb": false, "dsl": true,  "dyn_lai": false }
}
```

Enable `dsl` so layer geometry can adjust as ice melts; disable `dsb` (no fire).

Recommended CLI for Phase 1:

```sh
./dvmdostem -f experiments/thermokarst/barrow_validation/calibrated.json \
  --log-level warn --max-output-volume=-1 \
  --pr-yrs 1 --eq-yrs 30 --tr-yrs 13
```

## Output specification

Extend `config/output_spec.csv` (same pattern as `historic_projection_validation.py`):

| Variable | Interval | Purpose |
|---|---|---|
| `TKSUBSIDENCE` | daily + yearly | cumulative collapse; primary validation metric |
| `TKFRONT`, `TKFRONTTYPE` | daily | active-layer / thaw-front depth |
| `SNOWTHICK`, `SNOWEND` | daily / yearly | snow-depth comparison to CALM |
| `TLAYER` | monthly | soil temperature profile |
| `LAYERDEPTH`, `LAYERDZ` | monthly | settled geometry |
| `TKLIQGEN`, `TKLIQDRAINAGE`, `TKLIQRUNOFF` | daily | water-routing diagnostics |

## Derived model diagnostics

Compute in the validation script (mirror `historic_projection_validation.py`):

1. **Year-end cumulative subsidence (cm):** `TKSUBSIDENCE` on 31 December each year.
2. **Subsidence trend (cm yr⁻¹):** OLS slope over 2003–2015 per cell.
3. **Corrected ALT (cm):** max thaw depth from `TKFRONT` plus cumulative subsidence
   (Streletskiy Fig. 2c methodology).
4. **Warm-year response:** incremental subsidence in 2004, 2007, 2012 vs other years.
5. **Plot ordering:** rank subsidence 34 > 37 ≥ 40 ≈ 44 at 2015.
6. **Original-depth temperature:** subtract end-of-month `TKSUBSIDENCE` for fixed
   depth comparisons if soil-T validation is added later.

## Validation gates

### Phase 0 — pipeline (hard)

| Gate | Criterion |
|---|---|
| Run completion | all four cells `run_status == 100` |
| REF subsidence | max `TKSUBSIDENCE` < 1 mm over TR |
| Ice subsidence | monotonic increasing `TKSUBSIDENCE`; final > 5 mm per cell |
| Energy/mass sanity | no NaNs in `TKSUBSIDENCE` or `TLAYER` |
| Restart (optional) | split/resume at TR year 6: subsidence diff < 0.1 mm |

### Phase 1 — Streletskiy window 2003–2015 (soft)

| Gate | Target | Priority |
|---|---|---|
| All plots subside | Δ subsidence > 5 cm at 2015 | high |
| Mean subsidence bracket | 8–15 cm across four plots | high |
| Plot 34 fastest | sub₃₄ > sub₄₄ | high |
| Trend bracket | 0.3–1.2 cm yr⁻¹ per plot | high |
| Plot 34 trend highest | slope₃₄ ≥ slope₄₄ | medium |
| Warm-year concentration | >40 % of total subsidence in 2004, 2007, 2012 | medium |
| Corrected ALT mean | 33–42 cm (obs. 36.9 cm) | medium |
| REF control | < 1 mm subsidence | hard |

Do **not** fail Phase 1 on:

- year-to-year elevation oscillations (±5–13 cm in obs.; frost heave not modeled);
- 1962–2003 stability (deferred to Phase 2);
- absolute ALT in individual warm/cold years (high interannual variability in obs.).

### Phase 2 — full record 1962–2015 (soft)

| Gate | Target |
|---|---|
| 1962–2003 net subsidence | < 5 cm per plot (obs. stability) |
| 2003–2015 subsidence | 8–15 cm (repeat Phase 1) |
| 2012 event | largest single-year increment in TR window |
| Long-term ALT trend | +0.2 to +0.6 cm yr⁻¹ (obs. 0.3–0.5) |

Phase 2 1962–2003 stability is expected to be **difficult** without frost heave.
Treat as qualitative unless spin-up and ice replenishment are explicitly tuned.

## Proposed file layout

```text
experiments/thermokarst/barrow_validation/
  barrow_validation.py            # harness (to be implemented)
  barrow-output-spec.csv
  nws-barrow-climate-full.nc      # NWS-derived 1901–2015 (bundled; reused by all phases)
  run-mask-four-cells.nc
  vegetation.nc
  drainage.nc
  topo.nc
  obs/
    streletskiy-elevation-2003-2015.csv
    streletskiy-alt-2003-2015.csv
    streletskiy-climate-2003-2015.csv
  results/
    summary.json
    checks.csv
    ref/
    calibrated/
    figures/
      barrow-subsidence-timeseries.png
      barrow-subsidence-vs-obs.png
      barrow-subsidence-trends.png
      barrow-alt-corrected.png
      barrow-warm-year-response.png
```

Add Makefile target when implemented:

```makefile
thermokarst-barrow-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/barrow_validation.py
```

## Example run configuration skeleton

```json
{
  "IO": {
    "parameter_dir": "parameter/",
    "hist_climate_file": "experiments/thermokarst/barrow_validation/barrow-climate.nc",
    "co2_file": "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/co2.nc",
    "runmask_file": "experiments/thermokarst/barrow_validation/run-mask-four-cells.nc",
    "veg_class_file": "experiments/thermokarst/barrow_validation/vegetation.nc",
    "drainage_file": "experiments/thermokarst/barrow_validation/drainage.nc",
    "topo_file": "experiments/thermokarst/barrow_validation/topo.nc",
    "output_dir": "experiments/thermokarst/barrow_validation/results/calibrated/",
    "output_spec_file": "experiments/thermokarst/barrow_validation/barrow-output-spec.csv",
    "output_nc_pr": 0,
    "output_nc_eq": 0,
    "output_nc_sp": 0,
    "output_nc_tr": 1,
    "output_nc_sc": 0,
    "output_interval": 1,
    "restart_from": "experiments/thermokarst/barrow_validation/results/initialization/restart-calibrated.nc"
  },
  "model_settings": {
    "cell_timelimit": 0,
    "dynamic_lai": 0,
    "baseline_start": 1971,
    "baseline_end": 2000,
    "thermokarst": {
      "enabled": true,
      "excess_fraction": 0.0,
      "top_depth": 0.20,
      "bottom_depth": 1.00
    }
  },
  "stage_settings": {
    "pr": { "env": true, "bgc": false, "nfeed": false, "avlnflg": false,
            "baseline": false, "dsb": false, "dsl": true, "dyn_lai": false },
    "eq": { "env": true, "bgc": false, "nfeed": false, "avlnflg": false,
            "baseline": true, "dsb": false, "dsl": true, "dyn_lai": false },
    "tr": { "env": true, "bgc": false, "nfeed": false, "avlnflg": false,
            "baseline": false, "dsb": false, "dsl": true, "dyn_lai": false },
    "tr_start_yr": 0
  }
}
```

Per-cell excess-ice masses require **separate restart patches** after EQ because
`thermokarst` JSON settings are global; the harness should fork `restart-eq.nc` into
four plot-specific restarts (or one merged restart with distinct `TKexcess` fields per
cell) before the calibrated transient.

## Implementation checklist

- [x] Create `barrow_validation.py` from `historic_projection_validation.py` template
- [x] Extend `copy_spatial()` to four cells with plot-specific CMT/drainage
- [x] Bundle Streletskiy obs CSVs in `obs/`
- [x] Build Phase 0 synthetic Barrow climate NetCDF
- [x] Build Phase 1 NWS Barrow monthly climate NetCDF (1960–2015)
- [x] Set slope = 0° and four-cell run mask
- [x] Run PR + EQ without thermokarst; patch `TKexcess` per plot
- [x] Run `ref-p1`, `calibrated-p1` transients (Phase 1)
- [x] Add subsidence trend and warm-year diagnostic plots
- [x] Calibrate excess-ice mass per plot against 2003–15 obs
- [x] Extend to 1962–2015 transient (Phase 2)
- [x] Write Phase 2 report with full-record figures and gate table
- [x] Persist `nws-barrow-climate-full.nc` under `barrow_validation/`
- [x] `--reuse` skips completed stages and bundled climate rebuild (Phases 1–2)
- [x] Write [barrow-validation-report.md](barrow-validation-report.md) with figures and gate table
- [x] Phase A ALT calibration harness (`--phase A`, `--calibrate`)
- [ ] Phase B subsidence experiment using Phase A n-factors and deep ice band

## Limitations (explicit)

1. **No frost heave** — `TKSUBSIDENCE` is irreversible collapse only; cannot reproduce
   ±8–13 cm interannual elevation swings or 1962–2003 net stability without heave.
2. **Net elevation ≠ collapse** — compare cumulative subsidence trends, not raw dGPS
   elevation time series.
3. **Raw Toolik climate invalid** — ~6 °C summer warm bias vs Barrow; Phase 0 only.
4. **No snow redistribution** — plot 44 heave in 1962–2003 likely snow-related; not modeled.
5. **Excess-ice inventory uncertain** — transient-layer ice is inferred, not measured
   per plot; calibration against subsidence is required.
6. **CMT analogs** — CMT05/CMT06 are Toolik-calibrated wet/dry tundra, not Barrow-specific.
7. **Four independent columns** — no lateral coupling between polygon units.

## Next step

Run Phase A with 30 EQ years (or `--calibrate` if default n-factors miss ALT gates),
then implement **Phase B**: subsidence validation using calibrated n-factors and a
deeper excess-ice band (~0.25–0.55 m) with fresh spin-up.
