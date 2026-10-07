# EML CiPEHR subsidence experiment spec (DVM-DOS-TEM)

**Date:** 2026-09-19

**Repository:** `/Users/EJafarov/projects/TEM_abrupt_thaw_dev`

**Scientific reference:** Rodenhizer et al. (2020),
*Carbon thaw rate doubles when accounting for subsidence in a permafrost warming experiment*,
Journal of Geophysical Research: Biogeosciences, DOI
[10.1029/2019JG005528](https://doi.org/10.1029/2019JG005528)

**Status:** Phase 0 **PASS**; Phase 1 **PARTIAL** (control brackets obs; soil-warming rate
underestimated). See [eml-validation-report.md](eml-validation-report.md).

## Purpose

Set up an **Eight Mile Lake (EML) Carbon in Permafrost Experimental Heating Research
(CiPEHR)** experiment in DVM-DOS-TEM that compares four warming treatments under shared
discontinuous-permafrost tundra conditions, with **thermokarst subsidence** and
**thaw penetration** (ALT + subsidence) as primary validation metrics.

This is an **isotropic subsidence + thaw-penetration validation study**, not a reproduction
of CiPEHR snow-fence geometry, open-top chambers, or dGPS kriging. TEM runs four
**independent columns** on the same climate file (Phase 0) or treatment-perturbed climate
files (Phase 1+). It does **not** implement:

- snow-fence snow trapping and April snow removal;
- open-top chamber radiative warming;
- high-accuracy GPS elevation grids and anisotropic kriging;
- organic-matter volume loss from lateral C export (9–15 % of observed subsidence);
- localized thermokarst pond bathymetry.

Success criteria are staged:

1. **Phase 0 (pipeline):** four treatment cells complete; ice runs subside; reference runs do not.
2. **Phase 1 (validation window):** cumulative subsidence and treatment ordering over
   **2009–2018** bracket Rodenhizer et al. within calibrated bounds.
3. **Phase 2 (process validation):** simulated thaw penetration and water-table response
   qualitatively match control vs soil-warming contrasts.

## Feasibility assessment (subsidence validation)

**Verdict: Phase 1 subsidence validation is feasible as a soft, treatment-bracketing study,
but not as a plot-level reproduction of kriged GPS surfaces.**

### Why validation is possible

| Rodenhizer observable | TEM counterpart | Match quality |
|---|---|---|
| Cumulative subsidence (GPS Δ elevation) | `TKSUBSIDENCE` | **Good** — same physical process (excess-ice loss) for 85–91 % of observed subsidence |
| Thaw penetration = ALT + subsidence | `TKFRONT` max thaw + `TKSUBSIDENCE` | **Good** — direct diagnostic |
| Treatment ordering (soil ≫ control) | Perturbed climate or ice per treatment | **Moderate** — requires calibration |
| Control ~1.2 cm yr⁻¹ (~11 cm / 9 yr) | Calibrated excess-ice lens + Healy climate | **Moderate** — Barrow-scale precedent |
| Soil warming ~5–6 cm yr⁻¹ | Stronger forcing + deeper ice band | **Moderate** — needs +1–2 °C warming proxy |
| EML vegetation / soils | **CMT21** (EML Tussock Tundra) already in repo | **Good** |
| Published LTER time series | BNZ:729, BNZ:480, BNZ:554 | **Good** — obs CSVs bundled under `obs/` |

The paper's central finding — subsidence shifts the ALT reference frame and thaw
penetration exceeds ALT by **19 % (control)** and **49 % (soil warming)** by 2018 — maps
cleanly onto TEM outputs without reimplementing GPS postprocessing.

### Major limitations (explicit)

1. **Experimental warming is not native TEM physics.** Snow-fence insulation and OTC
   chambers must be approximated by **monthly air-temperature bias** (and optionally
   deeper snow depth in winter for soil-warming runs). TEM uses one global climate file per
   run; Phase 1 should use **four separate transient configs**, not a single 4-cell grid
   with different forcings.

2. **Soil-loss subsidence (9–15 %) is not modeled.** `TKSUBSIDENCE` tracks excess-ice
   collapse only. Expect simulated subsidence to sit **below** GPS totals unless ice
   inventory is tuned high enough to compensate.

3. **Spatial heterogeneity is large.** Kriged max subsidence reached **89 cm** while
   control plot means were **~11 cm** over 9 years. Validation should target **treatment
   mean rates** (Table S1 / Fig. 4 slopes), not cell-maximum maps.

4. **Early GPS point relocation adds noise.** Pre-2017 grid points were tape-measured,
   not navigated; microtopography can differ by **5–7 cm** at 1 m offset. Year-to-year
   GPS wiggles (including apparent elevation *increases*) should not be hard gates.

5. **Thermokarst pond inundation** (soil-warming blocks B/C from 2016) is only partially
   represented through Richards drainage and pond thermal mass — not explicit depression
   geometry.

6. **Warmer discontinuous permafrost** (MAT ≈ −1 °C) makes the site sensitive to spin-up
   equilibrium. Longer EQ (30+ yr) and near-0 °C permafrost initialization are recommended
   before transient comparison.

### Recommended validation strategy

Treat Rodenhizer as a **two-tier target**:

- **Tier A (subsidence rates):** OLS slope of cumulative `TKSUBSIDENCE` vs calendar year,
  compared to treatment slopes in `obs/rodenhizer-subsidence-rates.csv`.
- **Tier B (thaw penetration):** End-of-season thaw depth + cumulative subsidence vs 2018
  values in `obs/rodenhizer-thaw-penetration-2018.csv`.

Do **not** fail on absolute ALT alone without adding subsidence — that would repeat the
paper's documented bias.

## Site metadata

| Field | Value |
|---|---|
| Name | Eight Mile Lake CiPEHR |
| Location | 63°52′59″N, 149°13′32″W (near Healy, AK; west of Denali NP) |
| Permafrost zone | Discontinuous; permafrost temperatures near 0 °C |
| Elevation | 670 m (Geoid 12B) |
| Mean annual air temperature | **−0.94 °C** (nonsummer −10.09 °C; summer 11.91 °C) |
| Ecosystem | Moist acidic tussock tundra (*Eriophorum vaginatum*, *Vaccinium uliginosum*) |
| Soils | Gelisols; ~**0.35 m** organic layer over cryoturbated glacial till + loess |
| Site slope | ~**5 %** |
| Experiment start | 2008 (subsidence/GPS from **2009** baseline) |
| Study period | 2009–2018 (9 yr subsidence; ALT/water table through 2018) |

### CiPEHR experimental design

Three replicate blocks (A, B, C), each with two snow fences. On each fence side, four
0.36 m² plots; two plots per side receive open-top chamber **air warming** in summer.
Snow is trapped leeward (soil-warming side), then removed each April.

| Treatment | Manipulation | Approx. warming effect |
|---|---|---|
| **Control** | Ambient | — |
| **Air warming** | OTC chambers (summer) | +0.3 °C air (1st season); minimal soil effect |
| **Soil warming** | Snow-fence insulation | +0.78 °C deep soil (20–40 cm, summer); +1.49 °C surface nonsummer after 7 yr |
| **Air + soil warming** | Both | Highest subsidence; +1.05 °C deep nonsummer |

## Observation targets (from Rodenhizer et al. 2020)

Bundled CSV under `experiments/thermokarst/eml_validation/obs/`.

### Subsidence rates (2009–2018, plot-level mixed model)

| Treatment | Rate (cm yr⁻¹) | 95 % CI | ~Total (cm / 9 yr) |
|---|---:|---|---:|
| Control | **1.2** | 0.7 – 1.7 | 10.8 |
| Air warming | 1.4 | 0.9 – 2.0 | — |
| Soil warming | **5.4** | 4.8 – 5.9 | — |
| Air + soil warming | **6.1** | 5.6 – 6.7 | — |
| Site maximum (kriged) | — | — | 89.2 ± 3.5 |

Air vs control slopes are **not significantly different**. Soil-warming and air+soil slopes
exceed control by **~4–5×**.

### Thaw penetration vs ALT (2018)

| Treatment | ALT (cm) | Thaw penetration (cm) | TP increase vs ALT |
|---|---:|---:|---:|
| Control | 74.5 ± 1.2 | 88.6 ± 2.3 | **+19 %** |
| Soil warming | 92.4 ± 2.7 | 137.4 ± 4.3 | **+49 %** |

Newly thawed bulk C (2009→2018): control **17.5 → 24.0 kg m⁻²** (+37 % with TP);
soil warming **26.8 → 57.1 kg m⁻²** (+113 %).

### Water table depth (summer mean)

| Treatment | 2009 (cm) | 2018 (cm) | Change |
|---|---:|---:|---|
| Control | 27.6 ± 0.4 | 18.4 ± 0.3 | 33 % closer to surface |
| Soil warming | 25.4 ± 0.5 | 6.6 ± 0.3 | 74 % closer to surface |

### Ice inventory (2009 cores, thawed permafrost layer)

Total ice content **248–778 g kg⁻¹** (gravimetric, wet-soil basis). Ice loss explains
**85–91 %** of subsidence after adjusting for estimated soil-loss contribution.

## Experiment matrix

### Phase 0 — four-cell pipeline (shared climate)

| Cell | Treatment | CMT | Drainage | Role |
|---|---|---:|---:|---|
| (0, 0) | Control | **CMT21** | 1 (poor) | EML tussock tundra |
| (0, 1) | Air warming | **CMT21** | 1 | Same profile; Phase 1 gets +0.3 °C bias |
| (1, 0) | Soil warming | **CMT21** | 1 | Phase 1 gets +1.5 °C bias |
| (1, 1) | Air + soil warming | **CMT21** | 1 | Phase 1 gets +1.8 °C bias |

Phase 0 uses **identical forcing and uniform excess ice** on all cells to prove the
4-cell harness (mirrors Barrow Phase 0).

### Phase 1 — treatment validation (separate runs recommended)

Because TEM applies one `hist_climate_file` globally, run **four single-cell transients**
with bias-corrected Healy/EML climate:

| Run | ΔT_air (monthly tair) | Δ snow (optional) | Primary gate |
|---|---:|---|---|
| `control` | 0 | 0 | 0.7–1.7 cm yr⁻¹ |
| `air` | +0.3 °C summer only | 0 | ≈ control (within CI) |
| `soil` | +1.5 °C Oct–Apr; +0.8 °C May–Sep | +30 cm winter snow cap | 4.8–5.9 cm yr⁻¹ |
| `air_soil` | +1.8 °C annual mean split | +30 cm winter | 5.6–6.7 cm yr⁻¹ |

Calibrate excess-ice mass and depth band against **control** subsidence first, then verify
**soil-warming/control ratio** ∈ [3, 6].

## Forcing

### Do not use raw Toolik climate uncorrected

The bundled Toolik demo file is **too cold in winter and wrong in summer phase** for Healy
foothills (MAT ≈ −1 °C vs Toolik ≈ −8 °C). Use only as a NetCDF template in Phase 0.

### Source protocol (Phase 1+)

1. Download **Eight Mile Lake hourly meteorology** (BNZ:453; Celis et al. 2018) or Healy
   station records from WRCC/NOAA.
2. Aggregate to monthly `tair`, `precip`, `nirr`, `vapor_press` on TEM's `time` dimension.
3. Apply treatment-specific temperature biases (table above) in separate climate files.
4. CO₂: historic file sliced to 2009–2018 transient window.

Target file: `experiments/thermokarst/eml_validation/eml-climate.nc`

Phase 0 synthetic Healy-like template:

```python
# EML / Healy foothills monthly mean air temperature (°C) and precipitation (mm)
tair   = [-12, -10,  -6,   0,   8,  14,  16,  12,   6,  -2,  -8, -11]
precip = [ 18,  16,  14,  16,  22,  35,  45,  40,  28,  22,  20,  18]  # wetter foothills
nirr   = [  0,   2,   6,  14,  20,  22,  18,  12,   6,   2,   0,   0]
```

### Recommended staging

| Stage | Spin-up | Transient | Climate | Notes |
|---|---:|---:|---|---|
| **Phase 0** | 1 PR + 5 EQ | 9 TR | synthetic Healy template; **100 kg m⁻² lens at 0.10 m** | pipeline proof |
| **Phase 1** | 1 PR + 30 EQ | 9 TR (2009–18) | BNZ/Healy monthly + treatment bias | primary validation |
| **Phase 2** | resume Phase 1 | + water-table / ALT gates | same | add hydrology diagnostics |

External LTER data (for obs refresh, not required for Phase 0):

| Dataset | DOI / ID | Variable |
|---|---|---|
| GPS elevation | BNZ:729 | subsidence |
| Plot locations | BNZ:730 | spatial extraction |
| Weekly thaw depth | BNZ:480 | ALT |
| Water table | BNZ:554 | hydrology |
| Soil properties | BNZ:655 | ice/C calibration |

## Spatial setup

- `run-mask-four-cells.nc`: activate all four treatment cells.
- `topo.nc`: **slope = 5 %** (site mean; use 0° if spin-up fails on sloped drainage).
- **CMT21** (EML Tussock Tundra) on all cells — matches dominant *E. vaginatum* cover.
- Drainage class **1** (poorly drained) — moist acidic tussock tundra.

## Excess ice

### Paper context

- Organic layer **~0.35 m**; ice-rich cryoturbated mineral below.
- Core ice content **248–778 g kg⁻¹** in newly thawed permafrost.
- **85–91 %** of subsidence from ice loss; remainder from organic soil volume loss
  (not modeled in TEM).

### TEM thermokarst configuration

Inject excess ice **after equilibrium**, before transient:

```json
"thermokarst": {
  "enabled": true,
  "excess_fraction": 0.0,
  "top_depth": 0.35,
  "bottom_depth": 1.20
}
```

Starting calibration (adjust in Phase 1):

| Treatment | Initial mass (kg m⁻²) | Band (m) | Notes |
|---|---:|---|---|
| Control | 80–120 | 0.35–0.90 | target ~11 cm / 9 yr |
| Air warming | 80–120 | 0.35–0.90 | same ice; climate distinguishes |
| Soil warming | 120–180 | 0.35–1.20 | deeper thaw reaches more ice |
| Air + soil warming | 120–180 | 0.35–1.20 | highest subsidence |
| REF | 0 | — | thermokarst disabled |

**Calibration procedure:**

1. Tune control run to **8–14 cm** cumulative subsidence over 9 TR years.
2. Apply soil-warming climate bias; verify subsidence rate **≥ 3× control**.
3. Compare thaw penetration (ALT + subsidence) to 2018 obs (+19 % / +49 % boosts).
4. If soil warming is too slow, increase ice mass or winter warming bias before deepening
   the injection band.

## Model stages and switches

Undisturbed tundra, **no fire, no BGC** for Phase 1 (match Rodenhizer soil-physics focus).

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

Recommended CLI for Phase 1 control run:

```sh
./dvmdostem -f experiments/thermokarst/eml_validation/control.json \
  --log-level warn --max-output-volume=-1 \
  --pr-yrs 1 --eq-yrs 30 --tr-yrs 9
```

## Output specification

| Variable | Interval | Purpose |
|---|---|---|
| `TKSUBSIDENCE` | daily + yearly | primary validation metric |
| `TKFRONT`, `TKFRONTTYPE` | daily | ALT / thaw-front depth |
| `WTABLE` or water-table diagnostic | daily | wetter soils after subsidence |
| `SNOWTHICK` | daily | snow-fence proxy tuning |
| `TLAYER` | monthly | soil temperature profile |
| `LAYERDEPTH`, `LAYERDZ` | monthly | settled geometry |

## Derived model diagnostics

1. **Year-end cumulative subsidence (cm):** `TKSUBSIDENCE` on 31 December each year.
2. **Subsidence rate (cm yr⁻¹):** OLS slope over 2009–2018.
3. **Thaw penetration (cm):** max seasonal `TKFRONT` depth + cumulative subsidence
   (Rodenhizer Eq. 1).
4. **Treatment ratio:** subsidence_soil / subsidence_control (target 3–6).
5. **TP vs ALT boost (%):** (TP − ALT) / ALT at 2018 (target 19 % / 49 %).
6. **Water-table drawdown toward surface:** compare 2009 vs 2018 simulated depth.

## Validation gates

### Phase 0 — pipeline (hard)

| Gate | Criterion |
|---|---|
| Run completion | all four cells `run_status == 100` |
| REF subsidence | max `TKSUBSIDENCE` < 1 mm over TR |
| Ice subsidence | monotonic increasing; final > 5 mm per cell |
| Energy/mass sanity | no NaNs in `TKSUBSIDENCE` or `TLAYER` |

### Phase 1 — Rodenhizer window 2009–2018 (soft)

| Gate | Target | Priority |
|---|---|---|
| Control subsidence rate | 0.7–1.7 cm yr⁻¹ | high |
| Soil-warming rate | 4.8–5.9 cm yr⁻¹ | high |
| Air+soil rate | 5.6–6.7 cm yr⁻¹ | high |
| Soil / control ratio | 3–6× | high |
| Air ≈ control | \|slope_air − slope_ctrl\| < 0.5 cm yr⁻¹ | medium |
| Control TP boost 2018 | 15–25 % | medium |
| Soil TP boost 2018 | 40–55 % | medium |
| Water table rises (soil) | 2018 depth < 2009 depth | medium |
| REF control | < 1 mm subsidence | hard |

Do **not** fail Phase 1 on:

- kriged maximum subsidence (89 cm) — spatial outlier;
- year-to-year GPS noise or apparent heave in individual years;
- absolute newly thawed C stocks (BGC disabled).

## Proposed file layout

```text
experiments/thermokarst/eml_validation/
  eml_validation.py               # Phase 0 harness
  eml-climate.nc                  # Healy-derived (Phase 1+)
  run-mask-four-cells.nc
  obs/
    rodenhizer-subsidence-rates.csv
    rodenhizer-thaw-penetration-2018.csv
    rodenhizer-water-table.csv
    rodenhizer-climate.csv
  results/
    summary.json
    checks.csv
    ref/
    uniform-ice/
    figures/
docs_src/thermokarst/
  eml-experiment-spec.md
  eml-validation-report.md        # after Phase 1
```

Makefile target:

```makefile
thermokarst-eml-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation.py --binary ./dvmdostem
```

## Limitations (explicit)

1. **Warming manipulations are climate proxies**, not snow-fence or OTC physics.
2. **Soil-loss subsidence** (9–15 %) is omitted — expect low bias vs GPS unless ice is tuned high.
3. **One climate file per run** — treatment differences require separate configs in Phase 1.
4. **No spatial kriging** — compare treatment means, not block-scale maps.
5. **Thermokarst ponds** from 2016 are not explicitly simulated.
6. **CMT21** is EML-calibrated but spin-up may not reproduce 0.35 m organic layer exactly.

## Next step

Run Phase 0 (`make thermokarst-eml-validation`), then build Healy monthly climate from
BNZ:453, implement four treatment-biased climate files, and calibrate excess-ice inventory
until control and soil-warming subsidence rates bracket Rodenhizer et al. (2020).
