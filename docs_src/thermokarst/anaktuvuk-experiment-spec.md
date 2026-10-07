# Anaktuvuk River fire subsidence experiment spec (DVM-DOS-TEM)

**Date:** 2026-09-19

**Repository:** `/Users/EJafarov/projects/TEM_abrupt_thaw_dev`

**Scientific reference:** Jones et al. (2024),
*Post-fire stabilization of thaw-affected permafrost terrain in northern Alaska*,
Scientific Reports, DOI [10.1038/s41598-024-58998-5](https://doi.org/10.1038/s41598-024-58998-5)

**Related references:**

- Jones et al. (2015), initial thermokarst after the fire, Sci. Rep. 5:15865
- Mack et al. (2011), fire carbon emissions, Nature 475:489–492
- Jandt et al. (2021), fire effects 10 years post-fire, BLM Technical Report #64
- Urban & Clow (2018), NPR-A / ANWR climate and active-layer data (GTN-P)

**Data archive:** Jones et al. (2024) field and LiDAR products —
[https://doi.org/10.18739/A2251FM9P](https://doi.org/10.18739/A2251FM9P)

**Status:** Phase 0 **PASS** (15/15 gates; `make thermokarst-anaktuvuk-validation`)

## Purpose

Set up a **2007 Anaktuvuk River tundra fire** experiment in DVM-DOS-TEM that compares
**burned vs unburned** ice-rich Yedoma tundra under North Slope climate forcing, with
thermokarst subsidence and near-surface ground temperature as primary validation metrics.

The fire burned >1000 km² in 2007; Jones et al. (2024) focus on a **50 km² repeat-LiDAR
mosaic** in the Yedoma “silt belt” where widespread ice-wedge thermokarst developed
between **2009 and 2014**, then largely stabilized by **2021**.

This is a **paired-column fire + subsidence validation study**, not a spatial reproduction
of LiDAR change detection, ice-wedge polygon geometry, or airborne survey sampling.
TEM runs independent columns on shared climate files. It does **not** implement:

- per-pixel LiDAR Geomorphic Change Detection (GCD) at 1 m resolution;
- ice-wedge trough vs polygon-center microtopography;
- differential snow trapping in burned micro-relief (noted as warming mechanism post-2015);
- explicit transient/intermediate layer cryostratigraphy after thaw unconformities;
- lateral heat or water flux between burned and unburned patches.

## Feasibility assessment (burned vs unburned subsidence validation)

**Verdict: validation is feasible as a staged, soft-bracketing study — strongest for
ground temperature and burned–control subsidence contrast; moderate for absolute
subsidence magnitude; weak for LiDAR areal fractions and post-2014 stabilization
without calibration.**

### Why validation is possible

| Jones et al. (2024) observable | TEM counterpart | Match quality |
|---|---|---|
| Burned vs unburned ground T at 0.15 m and 1.0 m (2010–2022) | `TLAYER` at fixed depths; original-depth correction via `TKSUBSIDENCE` | **Good** — direct paired-site metric at logger locations |
| Thawing degree days (TDD) ratio burn/control (~3× early, ~1.3× by 2022) | Summed positive daily soil T at 0.15 m | **Good** — process diagnostic |
| Post-fire thermokarst subsidence (2009–2014 active phase) | `TKSUBSIDENCE` on burned column vs unburned control | **Moderate** — column cumulative vs landscape areal detection |
| Max post-fire thaw depth ~50–67 cm (coring 2021–2023) | `TKFRONT` max thaw + `TKSUBSIDENCE` | **Moderate** — no wedge-resolved geometry |
| Yedoma intermediate-layer ice (~45 % volumetric excess ice) | Calibrated `TKexcess` injection band | **Moderate** — requires inventory tuning |
| Fire in 2007 with organic-layer combustion | `dsb` + mapped `exp_fire_severity` | **Good** — existing fire-topology path |
| Stabilization 2014–2021 (<1 % new LiDAR subsidence) | Slowing `TKSUBSIDENCE` + `dsl` organic recovery | **Weak** — needs vegetation/soil-surface feedback tuning |

The repository already validates the required physics stack:

- [fire-topology-validation-report.md](fire-topology-validation-report.md) — combustion water/enthalpy topology;
- [fire-recovery-validation-report.md](fire-recovery-validation-report.md) — mid-thaw-season fire with excess ice;
- [observed-fire-validation-report.md](observed-fire-validation-report.md) — multi-year climate, `dsl`, burned vs control subsidence contrast.

An Anaktuvuk harness should extend `observed_fire_validation.py` / `fire_recovery_validation.py`,
not invent new model physics.

### Major limitations (explicit)

1. **LiDAR subsidence is a landscape areal statistic, not a point time series.**
   Jones report **14.6 %** of the 50 km² area subsided (>0.24 m) between 2009 and 2014,
   with **0.08 m yr⁻¹** mean rate *where detected*. TEM outputs **one cumulative
   `TKSUBSIDENCE` per column**. Validation must compare:
   - burned minus control cumulative subsidence over 2009–2014 (primary); and
   - optional terrain-unit columns (upland / slope / DLB) with different ice and slope —
     not the LiDAR **percent area affected** without a spatial model.

2. **No logger-point subsidence record.** Ground-temperature loggers sit on Yedoma upland
   tussock tundra (Fig. 1c), but published subsidence is from repeat airborne LiDAR over
   the full mosaic. Point subsidence at the logger is unknown. Tier A subsidence gates
   should use **column integrals**, not attempt to match 14.6 % areal coverage.

3. **LiDAR baseline starts 2009 (two years post-fire).** Phase 0–2 (2007–2009) thermokarst
   may already have occurred before the first LiDAR epoch. The experiment should spin up
   to **pre-2007**, fire in **2007**, and treat **2009–2014** as the primary subsidence
   comparison window (matching the paper’s “phase 2” widespread ice-wedge degradation).

4. **Detection threshold is 0.24 m between epochs.** Mean detected rate 0.08 m yr⁻¹ over
   5 years implies ~**0.40 m** cumulative subsidence in subsiding pixels. A burned column
   that subsides **20–40 cm** over 2009–2014 while the unburned control subsides **<5 cm**
   would be qualitatively consistent; exact match requires ice-inventory calibration.

5. **Stabilization (2014–2021) depends on vegetation and organic-layer recovery.**
   Jandt et al. (2021) document ~5 cm moss/litter accumulation and vigorous *Eriophorum*
   regrowth in the burn. TEM can approximate this with `dsl` and BGC, but reproducing the
   **~30× decline** in new subsidence area is not guaranteed without site calibration.

6. **Climate forcing is not bundled.** North Slope MAT ≈ **−9 °C** (Urban & Clow; Jones cite).
   Raw Toolik demo climate is unsuitable (same issue as Barrow/EML specs). NPR-A or
   Utkiagvik-bias-corrected monthly fields are required for Phase 1+.

7. **CMT analog.** Logger sites are **tussock tundra** on Yedoma uplands → **CMT05**
   (tussock) is the best available community; it is Toolik-calibrated, not North Slope-specific.

8. **Yedoma ice inventory is uncertain at column scale.** Intermediate layer mean **44.6 %**
   volumetric excess ice over ~10–15 cm (Table 1 aggradation + coring) implies a deep,
   ice-rich band — likely **200–400 kg m⁻²** injected between ~0.3 and 1.0 m after
   equilibrium, with calibration against subsidence and thaw depth.

### Recommended validation strategy

Treat Jones et al. (2024) as **three tiers**:

| Tier | Metric | Source CSV | Gate type |
|---|---|---|---|
| **A** | Cumulative subsidence 2009–2014: burned − control | model vs inferred from LiDAR | soft bracket |
| **B** | Ground T and TDD at 0.15 m and 1.0 m | `jones2024-ground-temperature-annual.csv` | soft RMSE / ratio |
| **C** | Subsidence rate decline 2014–2021 | `jones2024-lidar-subsidence-by-terrain.csv` | qualitative |

**Tier A targets (soft, burned CMT05 upland column):**

- Control subsidence 2009–2014: **< 5 cm** (undisturbed Yedoma upland analog).
- Burned subsidence 2009–2014: **15–40 cm** (partial melt of upper ice-rich permafrost;
  bracket informed by 0.08 m yr⁻¹ × 5 yr in subsiding fraction and coring thaw depths).
- Burned − control increment: **> 10 cm** (fire must enhance thermokarst vs paired control).

**Tier B targets:**

- Early period (2010–2014): TDD ratio burned/control **> 2.0** (paper ~3×).
- Late period (2019–2022): TDD ratio **1.1–1.5** (paper ~1.3× by 2022).
- MAGT at 1 m in 2022: burned **0.4–1.0 °C** warmer than control.

**Tier C:** burned-column subsidence increment 2014–2021 should be **< 25 %** of the
2009–2014 increment (paper: <1 % areal extent vs 14.6 % — order-of-magnitude slowdown).

Do **not** hard-fail on LiDAR **percent area affected** or terrain-unit spatial partitioning.

## Site metadata

| Field | Value |
|---|---|
| Name | Anaktuvuk River tundra fire — Yedoma LiDAR mosaic |
| Location | North Slope, Alaska (~69.5°N, 150°W; NPR-A region) |
| Fire year | **2007** (largest recorded North Slope tundra fire) |
| Burn extent | >1000 km² total; ~50 % on ice-rich Yedoma |
| LiDAR study area | **50 km²** repeat coverage (2009, 2014, 2021) |
| Permafrost type | Syngenetic Yedoma; high ground-ice content; ice-wedge polygons |
| Ecosystem | Tussock tundra (*Eriophorum vaginatum*) on Yedoma uplands |
| Mean annual air temperature | **~−9 °C** (regional GTN-P / Urban & Clow) |
| Ground-temperature loggers | Burned + unburned Yedoma upland; installed **July 2009**; 0.15 m and 1.00 m |
| Primary subsidence window | **2009–2014** (widespread ice-wedge thermokarst) |
| Stabilization window | **2014–2021** (<1 % additional detected subsidence) |

### Landscape phases (Jones et al. 2024 discussion)

| Phase | Years post-fire | Dominant process | TEM emphasis |
|---|---|---|---|
| 1 | 0–3 (2007–2010) | Active-layer thickening; limited slides | Fire severity, organic-layer loss |
| 2 | 3–7 (2010–2014) | Widespread ice-wedge degradation | Excess-ice melt; `TKSUBSIDENCE` |
| 3 | 7–15 (2014–2022) | Stabilization; transient/intermediate layer aggradation | `dsl`, slowed subsidence |

## Observation targets (bundled under `experiments/thermokarst/anaktuvuk_validation/obs/`)

| File | Content |
|---|---|
| `jones2024-lidar-subsidence-by-terrain.csv` | Table 1 LiDAR areal subsidence by terrain unit and period |
| `jones2024-ground-temperature-annual.csv` | Table 2 annual TDD and MAGT, burned vs unburned |
| `jones2024-cryostratigraphy-coring.csv` | Coring thaw depths and post-fire aggradation |
| `jones2024-ground-ice-content.csv` | Supplement excess-ice content by layer |

Download LiDAR DTMs, logger time series, and borehole logs from
[Arctic Data Center 10.18739/A2251FM9P](https://doi.org/10.18739/A2251FM9P) before Phase 2
point-scale gates.

### LiDAR summary (primary validation period)

| Period | Area affected | Mean rate where detected | Interpretation for TEM |
|---|---:|---:|---|
| 2009–2014 | **14.6 %** of 4678 ha | **0.08 m yr⁻¹** | Active thermokarst phase — burned column should subside much faster than control |
| 2014–2021 | **0.8 %** | **0.05 m yr⁻¹** | Stabilization — burned subsidence should nearly cease relative to 2009–2014 |

### Ground temperature summary (logger pair)

| Metric | Early post-fire (~2010–2014) | Late (~2019–2022) |
|---|---|---|
| TDD ratio (burned / unburned, 0.15 m) | **~3×** | **~1.3×** |
| MAGT offset at 1 m (burned − unburned) | up to **~2.3 °C** (2014) | **~0.7 °C** (2022) |
| Permafrost trend at 1 m in burn | **+0.33 °C yr⁻¹** (warming phase) | **−0.15 °C yr⁻¹** (cooling phase) |

## Experiment matrix

### Phase 1 — minimum viable validation (two cells)

| Cell | Role | CMT | Fire | Slope | Drainage |
|---|---|---:|---|---:|---:|
| (0, 0) | **Burned** Yedoma upland tussock | **CMT05** | 2007, severity **4** | 0° | 0 (well) |
| (0, 1) | **Unburned control** (paired) | **CMT05** | none | 0° | 0 (well) |

Fire severity **4** is consistent with Mack et al. (2011) severe organic consumption on
tussock tundra and with CMT05 mapping in existing fire validations. Confirm against
Jandt et al. (2021) burn-depth measurements when ADC data are loaded.

### Phase 2 — terrain-unit extension (optional four cells)

| Cell | Terrain analog | Slope | Excess-ice notes |
|---|---|---:|---|
| (0, 0) | Yedoma upland burned | 0° | primary logger match |
| (0, 1) | Yedoma upland control | 0° | unburned paired site |
| (1, 0) | Yedoma slope burned | **3°** | 40.8 % LiDAR area affected 2009–2014 |
| (1, 1) | DLB / lowland burned | 0° | poor drainage (1); slower early subsidence |

All burned cells share the same **2007** fire file entry; control cells use zeroed fire.

## Forcing

### Do not use raw Toolik climate

Same constraint as [barrow-experiment-spec.md](barrow-experiment-spec.md) and
[eml-experiment-spec.md](eml-experiment-spec.md). North Slope tundra is **colder** with
a shorter, cooler summer than Toolik demo files.

### Source protocol (Phase 1+)

1. Use **Urban & Clow (2018)** GTN-P NPR-A / North Slope active-layer sites, or NWS
   Utqiaġvik (formerly Barrow) for monthly temperature bias, to build a North Slope
   monthly template (MAT ≈ −9 °C).
2. Extend to **1980–2021** transient window: spin-up → fire 2007 → validation 2009–2021.
3. Optionally merge Jones et al. ADC logger years for Tier B point comparison.
4. CO₂: slice existing historic `co2.nc` to the transient window.

Target file: `experiments/thermokarst/anaktuvuk_validation/anaktuvuk-climate.nc`

Phase 0 may use a **North Slope synthetic** monthly template ( colder than Barrow spec ):

```python
# North Slope–like monthly mean air temperature (°C) — Phase 0 placeholder only
tair   = [-28, -27, -24, -16,  -5,   2,   4,   3,  -1, -10, -20, -26]
precip = [  5,   4,   4,   5,   7,  10,  12,  11,   8,   6,   5,   5]  # sum ≈ 82 mm
```

Replace with GTN-P / station-derived fields before Phase 1 gates.

### Recommended staging (production workflow)

The experiment is split into a **one-time spin-up** and **repeatable transient** runs.
All validation phases below should migrate to this pattern; Phase 0–2 harness paths remain
for regression until replaced.

#### Stage A — Spin-up (run once, hybrid / light physics)

| Step | dvmdostem flags | Climate file | Restart saved |
|---|---|---|---|
| Pre-run | `--pr-yrs 100` | `north-slope-climate-full-*.nc` (historic EQ) | `restart-pr.nc` |
| Equilibrium | `--eq-yrs 1000` | same historic file | `restart-eq.nc` |
| Spin-up | `--sp-yrs 100` | same historic file | **`restart-sp.nc`** |

```sh
make thermokarst-anaktuvuk-spinup
# → experiments/thermokarst/anaktuvuk_spinup_results/restart-sp.nc
# → experiments/thermokarst/anaktuvuk_spinup_results/restart-sp-tk-ready.nc
```

Run **once**; archive both restarts. Stage A uses the **legacy thermal path**
(`thermokarst.enabled: false`) so BGC and soil C can equilibrate over 1000 EQ years
without the thermokarst/Richards cost. No excess ice during spin-up.

The harness then writes **`restart-sp-tk-ready.nc`**: sets `TKactive`, fills
`TKmatrix`/`TKporosity`, and clears thermokarst diagnostics so Stage B can load
thermokarst physics and accept offline Yedoma ice injection.

#### Stage B — Transient (every experiment / calibration run)

Before each transient, build forcing from the Anaktuvuk / North Slope meteo file:

1. Take the **24-year TR window** (`2000–2023` by default).
2. Compute the **monthly climatological mean** (12 months) over those 24 years.
3. Write a **20-year seasonal spin-up** climate file (20 identical 12-month blocks).
4. Append the **24-year historic TR** slice to the same `hist_climate` NetCDF
   (44 years total: indices **0–19** seasonal, **20–43** historic).
5. Bridge `restart-sp.nc` → `restart-sp-tk-ready.nc` (thermokarst-ready, no excess ice).
6. Inject **Yedoma excess ice** offline into the bridged restart (same band as today).
7. Run **transient only** with **thermokarst enabled**:

| Step | dvmdostem flags | Climate slice | Notes |
|---|---|---|---|
| Seasonal SP | `--sp-yrs 20` | years **0–19** (repeated climatology) | re-equilibrates snow/soil under mean season |
| Historic TR | `--tr-yrs 24` | years **20–43** (`tr_start_yr = 20`) | calendar **2000–2023**; fire at TR year **7** (= 2007) |

```sh
make thermokarst-anaktuvuk-transient
# → uses restart-sp.nc + SP(20) + TR(24); outputs to anaktuvuk_phase1_validation_results/
```

**Every new run** uses only `--sp-yrs 20 --tr-yrs 24` (no PR/EQ). Reuse the archived
`restart-sp.nc` unless cryostratigraphy or CMT changes require a new spin-up.

#### Seasonal mean forcing (24-yr TR average)

The 20-year SP block repeats this climatology. Rain and snow panels use the model's
Willmott split on monthly mean temperature and precipitation (snowfall water, mm mo⁻¹).
Snow **depth** is a model state (`SNOWTHICK`) after SP, not a climate input.

![Anaktuvuk seasonal mean forcing](anaktuvuk-seasonal-forcing.png)

#### Legacy Phase 0–2 harness (short regression runs)

| Stage | Spin-up | Transient | Fire | Notes |
|---|---:|---:|---|---|
| **Phase 0** | 1 PR + 5 EQ | 15 TR (2007–2021) | 2007 DOY 180 | pipeline proof; ice on burned cell only |
| **Phase 1** | 1 PR + 30 EQ | 15 TR | 2007 | North Slope climate; Tier A+B soft gates |
| **Phase 2** | resume Phase 1 | +7 TR | — | Tier C stabilization |

Calendar alignment (legacy Phase 1, TR year 0 = **2007**): **2009–2014** subsidence maps to
TR years **2–7** (inclusive). Production TR (2000–2023) maps fire to TR year **7** (= 2007).

## Excess ice

### Thaw-depth bracket (production Phase 1 strategy)

Jones-style subsidence requires **identical excess ice on both columns** with **differential
thaw depth**, not ice on the burned cell only (Phase 0 shortcut).

```text
Surface
  │  pre-fire ALT (both columns)     < ice_top
  ├──────── ice_top (e.g. 0.50 m) ─── start of Yedoma excess-ice band
  │  excess ice (both cells, frozen at t₀)
  ├──────── ice_bottom (e.g. 0.68 m)
  │
  │  post-fire burned ALT            > ice_top  → excess melt → TKSUBSIDENCE
  │  post-fire control ALT           < ice_top  → no / minimal subsidence
  ▼
```

**Bracket conditions** (0 °C isotherm ALT from monthly `TLAYER`):

| Check | Target |
|---|---|
| Pre-fire (TR years 0–6) control ALT | `< ice_top` |
| Post-fire (TR years 7+) burned ALT | `> ice_top` |
| Post-fire control ALT | `< ice_top` |
| Control max ALT (whole run) | **30–75 cm** (Jones coring thaw depths) |

**Default bracket band** (harness `--ice-bracket`):

| Parameter | Default | Notes |
|---|---:|---|
| `--ice-top` | **0.50 m** | below pre-fire thaw, above post-fire control |
| `--ice-bottom` | **0.68 m** | thin slab (~150–200 kg m⁻² at 36 % fraction) |
| `--ice-fraction` | **0.36** | Jones intermediate-layer range |
| Fire | **`--max-organic-burn`** (auto) | full organic removal, stronger TDD/MAGT contrast |

**Calibration order** (after hybrid Stage A spin-up):

1. `make thermokarst-anaktuvuk-bracket-climate-calibration` — hybrid control-only SP(20)+TR(24)
   probes; selects inland bias with control max isotherm ALT in **30–75 cm** (target **55 cm**).
   Writes `anaktuvuk-bracket-climate-calibration.json`.
2. `make thermokarst-anaktuvuk-bracket-ice-calibration` — sweeps `ice_top` ∈ {0.40, 0.45, 0.50,
   0.55, 0.60} m with max-organic-burn paired transients; scores bracket geometry + subsidence
   contrast. Writes `anaktuvuk-ice-calibration.json` (`mode: ice_bracket`).
3. `make thermokarst-anaktuvuk-ice-bracket-validation` — full Phase 1 gates including four
   soft **bracket** checks.

The legacy deep band (**0.30–1.00 m**, 28 %) fails this bracket when climate bias yields
**~128 cm** ALT — both columns melt ice symmetrically before the 2009–2014 LiDAR window.

Subsidence is inferred from `TKSUBSIDENCE`; remaining excess ice:
`initial TKexcess − subsidence × 917 kg m⁻³` (see validation report excess-ice figure).

**Diagnostic figures** (prefix `anaktuvuk-ice-bracket-*`):

| Figure | Variable | Source |
|---|---|---|
| `soil-temperature-{burned,control}` | Soil T (°C) depth–time | `TLAYER` → regular depth grid |
| `liquid-water-{burned,control}` | Volumetric liquid water | `LWCLAYER` |
| `ice-content-{burned,control}` | Volumetric ice content | `IWCLAYER` |
| `soil-thermal-{burned,control}` | T + snow + subsidence stack | combined panel |
| `excess-ice-degradation` | Remaining TKexcess inventory | restart + `TKSUBSIDENCE` |
| `organic-layers-{burned,control}` | Moss / fibric / humic thickness (September) | `LAYERTYPE`, `LAYERDZ` |
| `subsidence-burned-vs-control` | Cumulative subsidence (cm) | `TKSUBSIDENCE` daily |
| `bgc-burned-vs-control` | VEGC, SOC, GPP, NPP | yearly + layer-summed SOC |

All contour panels overlay the injected excess-ice band, 2007 fire, and 2009–2014 LiDAR window.
Regenerate: `make thermokarst-anaktuvuk-ice-bracket-plot-diagnostics`.

### Yedoma cryostratigraphy (calibration targets)

| Layer | Excess ice (vol. %) | TEM use |
|---|---:|---|
| Intermediate (upper permafrost) | **44.6** | primary injection band |
| Underlying syngenetic | 38.2 | deeper band optional |
| Transient | 9.4 | post-stabilization, not initial |

Convert volumetric excess ice to mass inventory:

\[
M \approx f_{\mathrm{excess}} \cdot \rho_{\mathrm{ice}} \cdot \Delta z
\]

Example: \(f = 0.45\), \(\Delta z = 0.5\) m → **~206 kg m⁻²**.

### Starting thermokarst configuration

```json
"thermokarst": {
  "enabled": true,
  "excess_fraction": 0.0,
  "top_depth": 0.30,
  "bottom_depth": 1.20
}
```

Inject **offline into `restart-sp.nc`** (after Stage A spin-up, before Stage B transient SP)
on **both** burned and control cells (same pre-fire ice); fire then accelerates thaw on
the burned column only. Ice is **not** present during PR/EQ/SP spin-up.

| Cell | Initial mass (kg m⁻²) | Band (m) | Notes |
|---|---:|---|---|
| Burned upland | 150–250 | **0.50–0.68** (bracket default) | thaw-depth bracket + Tier A |
| Control upland | same | same | identical pre-fire ice |
| Burned upland (legacy) | 200–350 | 0.30–1.00 | over-thaws with +7.5 °C bias |
| Slope (Ph. 2) | +10–20 % | bracket or legacy | higher LiDAR affected fraction |
| DLB (Ph. 2) | −10–20 % | 0.25–0.80 | wetter, shallower thaw in paper |

## Model stages and switches

Production runs use two dvmdostem invocations:

| Invocation | Flags | `stage_settings` emphasis |
|---|---|---|
| Spin-up (once) | `--pr-yrs 100 --eq-yrs 1000 --sp-yrs 100` | `dsb=false`, `dsl=true`, historic full climate |
| Transient (repeat) | `--sp-yrs 20 --tr-yrs 24` | `tr_start_yr=20`, `dsb=true` on burned run, combined climate file |

Legacy Phase 1 should mirror [observed-fire-validation-report.md](observed-fire-validation-report.md):

```json
"stage_settings": {
  "pr": { "env": true,  "bgc": true, "dsb": false, "dsl": true,  "dyn_lai": false },
  "eq": { "env": true,  "bgc": true, "baseline": true,  "dsb": false, "dsl": true },
  "tr": { "env": true,  "bgc": true, "dsb": true,  "dsl": true,  "dyn_lai": false }
}
```

- **`dsb`:** fire disturbance on burned run only (2007).
- **`dsl`:** dynamic soil for organic-layer recovery (needed for Tier C).
- **Thermokarst + pond unification:** reuse overnight pond merge from observed-fire path.

Fire file sketch:

```python
# Transient year 0 = 2007 → fire on DOY ~240 (late summer tundra fire season)
dataset["exp_fire_severity"][0, burned_y, burned_x] = 4
dataset["exp_jday_of_burn"][0, burned_y, burned_x] = 240
```

## Output specification

Extend `config/output_spec.csv` (same pattern as fire-recovery / observed-fire):

| Variable | Interval | Purpose |
|---|---|---|
| `TKSUBSIDENCE` | daily + yearly | primary subsidence validation |
| `TKFRONT`, `TKFRONTTYPE` | daily | thaw depth vs coring |
| `TLAYER` | monthly | ground temperature at 0.15 m and 1.0 m |
| `SNOWTHICK` | daily | snow–pond–soil coupling |
| `TKPOND`, `TKSURFICE` | daily | post-fire hydrology |
| `BURNTHICK`, `BURNSOIL2AIRC` | monthly | fire consumption |
| `VEGC`, `SOC`, `GPP`, `NPP` | yearly | recovery trajectory (Tier C) |

## Derived model diagnostics

1. **Window subsidence (cm):** Δ `TKSUBSIDENCE` over TR years 2–7 (2009–2014) and 8–14
   (2014–2021), burned minus control.
2. **Annual TDD at 0.15 m:** sum positive daily soil temperature; ratio burned/control.
3. **MAGT at 1.0 m:** mean annual `TLAYER` at 1 m original depth (month-end subsidence correction).
4. **Thaw penetration (cm):** max seasonal `TKFRONT` + cumulative subsidence vs coring
   (`jones2024-cryostratigraphy-coring.csv`).
5. **Stabilization ratio:** subsidence 2014–2021 divided by subsidence 2009–2014 (burned cell).

## Validation gates

### Phase 0 — pipeline (hard)

| Gate | Criterion |
|---|---|
| Run completion | both cells `run_status == 100` |
| Control subsidence | monotonic; fire cell only burns in 2007 |
| Burned subsidence | burned > control at 2014 by **> 5 mm** |
| Fire mapper | water/energy closure (existing fire-topology gates) |
| Restart | split at 2014; resume subsidence diff < 0.1 mm |

### Phase 1 — 2009–2014 subsidence + ground temperature (soft)

| Gate | Target | Priority |
|---|---|---|
| Burned − control subsidence 2009–2014 | **10–35 cm** | high |
| Control subsidence 2009–2014 | **< 5 cm** | high |
| TDD ratio 2010–2014 | **> 2.0** | high |
| TDD ratio 2019–2022 | **1.1–1.5** | medium |
| MAGT offset 1 m, 2022 | **0.4–1.0 °C** | medium |
| Thaw penetration 2021 | **45–75 cm** | medium |

### Phase 2 — stabilization 2014–2021 (qualitative)

| Gate | Target |
|---|---|
| Subsidence slowdown | 2014–2021 increment < 25 % of 2009–2014 (burned) |
| Slope vs upland (4-cell) | slope cell ≥ upland subsidence 2009–2014 |
| Vegetation recovery | burned `VEGC` trend upward post-2010 (sign only) |

Do **not** fail Phase 1 on LiDAR **14.6 % areal extent** or GCD **0.24 m detection threshold**
without a spatial model.

## Proposed file layout

```text
experiments/thermokarst/anaktuvuk_validation/
  anaktuvuk_validation.py         # harness (to be implemented)
  anaktuvuk-output-spec.csv
  anaktuvuk-climate.nc            # North Slope derived (Phase 1+)
  run-mask-two-cells.nc           # Phase 1
  run-mask-four-cells.nc          # Phase 2 optional
  vegetation.nc
  drainage.nc
  topo.nc
  obs/
    jones2024-lidar-subsidence-by-terrain.csv
    jones2024-ground-temperature-annual.csv
    jones2024-cryostratigraphy-coring.csv
    jones2024-ground-ice-content.csv
  results/
    summary.json
    checks.csv
    control/
    burned/
    figures/
      anaktuvuk-subsidence-burned-vs-control.png
      anaktuvuk-subsidence-by-window.png
      anaktuvuk-tdd-ratio.png
      anaktuvuk-magt-1m.png
```

Add Makefile target when implemented:

```makefile
thermokarst-anaktuvuk-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py
```

## Implementation checklist

- [x] Extract Jones et al. (2024) observation tables to `obs/*.csv`
- [x] Write experiment spec with feasibility assessment
- [x] Implement `anaktuvuk_validation.py` from `observed_fire_validation.py` template
- [x] Add Makefile target `thermokarst-anaktuvuk-validation`
- [ ] Build North Slope monthly climate NetCDF (GTN-P / Utqiaġvik bias)
- [ ] Configure 2007 fire on CMT05 burned cell; zero fire on control
- [ ] Inject Yedoma excess-ice inventory on both cells after EQ
- [ ] Add Tier A/B gates and figures
- [ ] Fetch ADC logger time series for Phase 2 hourly comparison
- [ ] Write `anaktuvuk-validation-report.md` after Phase 1 runs

## Limitations (explicit)

1. **Column vs landscape** — LiDAR reports areal fractions; TEM columns give point integrals.
2. **No ice-wedge geometry** — excess ice is a layer inventory, not trough/center microtopography.
3. **Logger subsidence unknown** — ground-T validation is stronger than subsidence magnitude.
4. **Stabilization physics** — transient/intermediate layer aggradation is not explicit state.
5. **North Slope climate gap** — must build forcing; Toolik demo is invalid.
6. **CMT05 analog** — not calibrated for Anaktuvuk Yedoma tussock.
7. **Fire severity** — severity 4 is inferred; should be checked against Jandt/Mack burn depth.

## Phase 0 results (2026-09-19)

Harness: `experiments/thermokarst/anaktuvuk_validation.py`

| Metric | Burned CMT05 | Control CMT05 |
|---|---:|---:|
| Excess ice injected | 324 kg m⁻² | none (paired unburned column) |
| Fire-year subsidence (2007) | 4.2 cm | 0 |
| Cumulative subsidence at 2014 | 8.2 cm | 0 |
| Increment 2009–2014 | 4.0 cm | 0 |
| Increment 2014–2021 | 4.6 cm | 0 |
| Final subsidence (2021) | 12.8 cm | 0 |
| 1 m MAGT offset 2022 (burn − control) | +0.77 °C | — |

Phase 0 uses a **thaw-capable North Slope synthetic** (MAT ≈ −8.1 °C), severity-4 fire on DOY 180,
and Yedoma excess ice (**32 %** fraction from **0.15–0.90 m**) on the **burned cell only** so the
unburned control stays at zero subsidence under the same climate. Phase 1 should inject matched
ice on both columns and calibrate against Jones logger temperatures and LiDAR epoch rates.

Figures: `experiments/thermokarst/anaktuvuk_validation_results/anaktuvuk-*.png`

## Next step

Phase 1 production path — **thaw-depth bracket** on hybrid staging:

```sh
make thermokarst-anaktuvuk-spinup                      # Stage A once
make thermokarst-anaktuvuk-bracket-climate-calibration  # Jones-scale ALT bias
make thermokarst-anaktuvuk-bracket-ice-calibration      # ice_top sweep
make thermokarst-anaktuvuk-ice-bracket-validation       # gates + figures
```

- two-cell burned/control on North Slope climate (+ bracket-calibrated bias);
- 2007 fire with **`--max-organic-burn`** (full organic column);
- identical excess ice **0.50–0.68 m**, ~36 % fraction on both cells;
- SP(20)+TR(24) transient (2000–2023);

Iterate until Tier A/B soft gates and bracket checks bracket Jones et al. (2024).
