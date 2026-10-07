# Anaktuvuk River fire validation report

**Reference:** Jones et al. (2024), *Scientific Reports* — 2007 Anaktuvuk River fire Yedoma subsidence

**Harness:** `experiments/thermokarst/anaktuvuk_validation.py`

## Phase 0 — pipeline (hard gates)

**Output:** `experiments/thermokarst/anaktuvuk_validation_results/`

| Item | Value |
|---|---|
| Spin-up | 1 PR + 5 EQ |
| Transient | 15 TR (2007–2021) |
| Climate | Synthetic North Slope thaw-capable (MAT ≈ −8.1 °C) |
| Ice | Excess ice on **burned cell only** (0.15–0.90 m, 32 % fraction) |
| Fire | 2007, DOY 180, severity 4 |

**Gates:** 15/15 PASS

| Metric | Burned | Control |
|---|---:|---:|
| Fire-year subsidence | 4.2 cm | 0 |
| Cumulative at 2014 | 8.2 cm | 0 |
| Final (2021) | 12.8 cm | 0 |
| 1 m MAGT offset (last year) | +0.77 °C | — |

Phase 0 confirms the burned-vs-control harness, restart continuity, and thermokarst response under thaw-capable forcing. Ice was placed only on the burned column so the unburned control stays at zero subsidence (paired-column shortcut documented in the experiment spec).

## Phase 1 — Jones 2009–2014 window (soft gates)

**Output:** `experiments/thermokarst/anaktuvuk_phase1_validation_results/`

### Hybrid staging (production workflow)

Stage A and Stage B are split so BGC can equilibrate on the fast legacy thermal path while thermokarst runs only for the fire/subsidence experiment.

| Stage | Thermokarst | dvmdostem flags | Climate | Restart |
|---|---|---|---|---|
| **A — spin-up** (once) | **off** | `--pr-yrs 100 --eq-yrs 1000 --sp-yrs 100` | `north-slope-climate-full-7p5.nc` | `restart-sp.nc` |
| **Bridge** (offline) | prep only | — | — | `restart-sp-tk-ready.nc` |
| **B — transient** (each run) | **on** + ice inject | `--sp-yrs 20 --tr-yrs 24` | 20-yr seasonal climatology + 2000–2023 TR | `restart-yedoma-ice.nc` |

Stage A wall time on this machine: **211 s** (~3.5 min) for PR 100 + EQ 1000 + SP 100 (both cells status 100).

![Seasonal mean forcing (24-yr TR climatology; winter precip scaled for ~40 cm snow)](anaktuvuk-seasonal-forcing.png)

### Latest run (+7.5 °C, severity 4, hybrid, ~40 cm snow)

| Item | Value |
|---|---|
| Spin-up | **Hybrid Stage A:** PR 100 + EQ 1000 + SP 100 (thermokarst **off**) |
| Bridge | `restart-sp-tk-ready.nc` → offline Yedoma ice injection |
| Transient | **SP 20** + **TR 24** (calendar **2000–2023**); `--paired-only` |
| Climate | North Slope monthly obs + **+7.5 °C inland bias** |
| Winter precip | Snow-month scale **×2.06** (target **40 cm** peak snow depth) |
| Fire | 2007, DOY 240, severity **4**; explicit fire at climate index **27** (`tr_start_yr 20 + TR year 7`) |
| Ice | **Identical Yedoma inventory on both cells** (0.30–1.00 m, 28 % fraction, ~250 kg m⁻²) |

**Gates:** **9/16 PASS** on the latest `--reuse` report pass. **Paired control+burned runs complete (status 100).** Restart continuity gates **FAIL** because `split-first/` and `resumed/` outputs are **stale** (from an earlier climate/fire configuration before snow scaling and fire-index fix); re-run transient **without** `--paired-only` to refresh those gates.

| Metric | Burned | Control | Gate |
|---|---:|---:|---|
| Seasonal snow peak (mean) | **~41 cm** | **~41 cm** | — |
| Post-fire snow ratio | — | — | **1.000** (hard PASS) |
| Fire organic burn depth | **5.3 cm** max | 0 | fire active |
| Organic depth (Sep) | **8.6 cm** (2007) | 12.6 cm | ↓ from 12.6 cm pre-fire |
| Max ALT (0 °C isotherm) | 125 cm | 128 cm | hard PASS (≥ 30 cm) |
| Subsidence increment 2009–2014 | 0 cm | 0 cm | soft FAIL |
| TDD ratio 2010–2014 mean | — | — | 1.04 (soft FAIL; obs ≈ 2.8×) |
| TDD ratio 2019–2021 mean | — | — | 0.85 (soft FAIL) |
| MAGT offset 1 m (2023) | — | — | −0.42 °C (soft FAIL) |
| Thaw penetration 2021 | 138 cm | — | soft FAIL (expect 45–75 cm) |

Fire and organic-layer response are now active (2007 step visible on burned organic panel). **No thermokarst subsidence** yet in 2009–2014 — thaw has not mobilized the 0.30 m Yedoma ice band.

Run:

```sh
make thermokarst-anaktuvuk-spinup              # Stage A once (~3–5 min)
make thermokarst-anaktuvuk-transient           # Stage B SP(20)+TR(24), paired-only
make thermokarst-anaktuvuk-climate-calibration # ALT ≥ 30 cm precondition
make thermokarst-anaktuvuk-fire-calibration    # optional severity sweep
make thermokarst-anaktuvuk-phase1-validation   # gates + all figures (--reuse)
make thermokarst-anaktuvuk-plot-diagnostics    # figures only
```

### Snow depth pairing (burned vs unburned)

Winter precipitation in snow months (tair ≤ 0 °C) is scaled to target **~40 cm** seasonal peak snow depth (`WINTER_PRECIP_SCALE ≈ 2.06`, calibrated from the pre-scale ~7 cm baseline). Post-fire **seasonal snow peak** ratio is **~1.000** at severity 4.

Snow figures use **calendar-month maximum** depth (not month-end point samples). The burned soil-thermal panel overlays unburned control snow as a dashed line.

A **hard gate** enforces post-fire seasonal-peak ratio ∈ **[0.85, 1.15]**.

Fire severity calibration: `anaktuvuk-fire-calibration.json` (selected severity **4**).

### Active layer depth (ALT) definition

**ALT is computed from monthly `TLAYER` profiles**, not from `TKFRONT` alone:

1. Interpolate layer-centre temperatures onto a regular depth grid (0–2 m).
2. Each month, find the **maximum depth of the 0 °C isotherm**.
3. **Annual ALT** = max of monthly isotherm depths within each calendar year.

This matches the EML/BNZ soil-thermal diagnostic pattern and is shown as an orange overlay on the depth–time contour plots.

### Staged calibration (required order)

1. **Climate / ALT precondition** — unburned control max ALT (0 °C isotherm) must reach **≥ 30 cm** before ALT, soil-temperature, or subsidence calibration.
2. **Snow / fire severity** — scale winter precip for target snow depth; keep burned snow within 0.85–1.15× control.
3. **ALT + soil temperature** — compare isotherm ALT, TDD, and MAGT to Jones ground-temperature CSVs.
4. **Subsidence / ice band** — tune `--ice-top`, `--ice-fraction` once thaw accesses the Yedoma band on the burned cell (see ice calibration below).

Phase 1 includes hard gates: ALT precondition (≥ 30 cm) and post-fire snow ratio.

### Excess ground-ice mass degradation

The restart file stores `TKexcess` (kg m⁻² per layer); daily output does not include a time series of remaining ice mass. The harness plots **inferred remaining inventory**:

\[
\text{remaining}(t) = \max\bigl(0,\; \text{TKexcess}_\text{initial} - \text{TKSUBSIDENCE}(t) \times 917\ \text{kg m}^{-3}\bigr)
\]

Both panels show burned vs control from the **identical paired Yedoma injection** (~250 kg m⁻² at 0.30–1.00 m, 28 % fraction). Symmetric melt on both columns is expected when thaw reaches the ice band equally; differential degradation requires a shallower ice band plus stronger burned-column warming.

![Excess ground-ice mass degradation (standard Phase 1)](anaktuvuk-phase1-excess-ice-degradation.png)

Regenerate:

```sh
make thermokarst-anaktuvuk-plot-diagnostics
```

### Thaw-depth bracket mode (`--ice-bracket`)

Production strategy (see [anaktuvuk-experiment-spec.md](anaktuvuk-experiment-spec.md)): identical ice on both cells with **pre-fire ALT below ice top** and **post-fire burned ALT above ice top** while control stays below. Default band **0.50–0.68 m**, fraction **36 %**, auto-enables `--max-organic-burn`.

```sh
make thermokarst-anaktuvuk-bracket-climate-calibration  # control ALT 30–75 cm
make thermokarst-anaktuvuk-bracket-ice-calibration      # sweep ice_top 0.40–0.60 m
make thermokarst-anaktuvuk-ice-bracket-validation
```

Phase 1 adds four soft **bracket gates** (pre/post-fire ALT vs `ice_top`, control ALT in Jones range).

#### First ice-bracket run (2026-09-20, max-organic-burn)

**Output:** `experiments/thermokarst/anaktuvuk_ice_bracket_results/`

| Item | Value |
|---|---|
| Bracket climate bias | **+4.5 °C** (control max ALT **47 cm**, closest to 55 cm target in Jones range) |
| Ice band | **0.50–0.68 m**, 36 % (~**93 kg m⁻²**) on both cells |
| Organic burn | **12.6 cm** (full column, max-organic-burn) |
| **Gates** | **16/19 PASS** — all **four bracket gates PASS** |
| Post-fire ALT | burned **91 cm**, control **31 cm** (ice top 50 cm) |
| Subsidence 2009–2014 | **0 cm** both (soft FAIL — geometry bracket met, no excess-ice melt yet) |
| MAGT offset 1 m | **+0.63 °C** (PASS) |
| Thaw penetration 2021 | **93 cm** (soft FAIL, slightly above 75 cm ceiling) |

The thaw-depth **geometry** is now correct (control stays below ice top; burned penetrates it), but thermokarst subsidence has not started — likely needs `make thermokarst-anaktuvuk-bracket-ice-calibration` (ice_top sweep) or higher ice fraction.

![Ice-bracket excess ice degradation](anaktuvuk-ice-bracket-excess-ice-degradation.png)

#### Soil temperature, liquid water, and ice content (depth–time contours)

Standalone contour panels for burned and control (2000–2023). Blue band = initial excess-ice injection; orange line = 0 °C isotherm ALT on temperature plots; dashed vertical = 2007 fire; shaded = 2009–2014 LiDAR window.

**Burned**

![Burned soil temperature](anaktuvuk-ice-bracket-soil-temperature-burned.png)

![Burned liquid water](anaktuvuk-ice-bracket-liquid-water-burned.png)

![Burned ice content](anaktuvuk-ice-bracket-ice-content-burned.png)

**Control**

![Control soil temperature](anaktuvuk-ice-bracket-soil-temperature-control.png)

![Control liquid water](anaktuvuk-ice-bracket-liquid-water-control.png)

![Control ice content](anaktuvuk-ice-bracket-ice-content-control.png)

#### Organic horizon thickness (September, burned and control)

Stacked **September** moss, fibric (shallow), and humic (deep) organic layers from `LAYERTYPE` + `LAYERDZ`. Total organic depth is overlaid as a black line; the 2007 fire is marked at DOY 240. With max-organic-burn, the burned column loses the **full ~12.6 cm** organic column in 2007; control is unchanged.

![Burned organic horizon](anaktuvuk-ice-bracket-organic-layers-burned.png)

![Control organic horizon](anaktuvuk-ice-bracket-organic-layers-control.png)

#### Subsidence and BGC (paired burned vs control)

![Paired subsidence](anaktuvuk-ice-bracket-subsidence-burned-vs-control.png)

![Paired BGC — VEGC, SOC, GPP, NPP](anaktuvuk-ice-bracket-bgc-burned-vs-control.png)

Regenerate:

```sh
make thermokarst-anaktuvuk-ice-bracket-plot-diagnostics
```

### Legacy ice-band calibration (deep band)

Default Phase 1 ice (0.30–1.00 m, 28 %) sits below a deeply thawed active layer (~128 cm), so both columns melt excess ice symmetrically before the 2009–2014 LiDAR window → **zero subsidence increment**. Phase 0 worked because ice was **burned-only** at a shallow band (0.15–0.90 m).

```sh
make thermokarst-anaktuvuk-ice-calibration   # shallow top sweep 0.15–0.30 m
```

### Climate calibration result

| Bias (°C) | Control max ALT (cm) | TR MAT (°C) |
|---:|---:|---:|
| 2.5 | 4.0 | −8.2 |
| 3.5 | 14.0 | −7.2 |
| 4.5 | 18.1 | −6.2 |
| 5.5 | 21.1 | −5.2 |
| 6.5 | 25.4 | −4.2 |
| **7.5** | **31.4** | **−3.2** |

**Selected inland bias: +7.5 °C** (`anaktuvuk-climate-calibration.json`). Probe used 10 EQ + 15 TR control runs without excess ice. Full hybrid spin-up with scaled winter snow reaches **~128 cm** ALT on the control column.

### Climate forcing inputs

Historic climate files written by the harness:

- `north-slope-climate-full-7p5.nc` — bias-corrected series used during Stage A EQ spin-up
- `anaktuvuk-transient-climate-7p5.nc` — combined SP(20) climatology + 2000–2023 TR slice (winter precip scaled)
- `north-slope-climate-tr-7p5.nc` — 2000–2023 transient slice

Climate figure window: **2000–2023** (fire at 2007; LiDAR epochs through 2021).

![North Slope climate inputs — air temperature, precipitation, NIRR](anaktuvuk-phase1-climate-inputs.png)

### Soil thermal, snow, and carbon–moisture diagnostics (2000–2023)

Depth–time panels use the **main paired transient** (SP 20 + TR 24 from 2000, hybrid spin-up restart, +7.5 °C bias, ~40 cm snow). Snow, soil temperature, combusted C, total SOC, and volumetric liquid/ice content all share this window.

![Paired snow depth burned vs control](anaktuvuk-phase1-snow-burned-vs-control.png)

![Burned soil thermal contour](anaktuvuk-phase1-soil-thermal-burned.png)

![Control soil thermal contour](anaktuvuk-phase1-soil-thermal-control.png)

![Burned soil carbon and moisture](anaktuvuk-phase1-soil-carbon-water-burned.png)

![Control soil carbon and moisture](anaktuvuk-phase1-soil-carbon-water-control.png)

### Organic horizon thickness (2000–2023)

Stacked **September** moss, fibric (shallow), and humic (deep) organic layers from the same main transient run. Total organic depth is overlaid as a black line; the 2007 fire is marked at DOY 240. Burned column shows a **~4 cm step down** in September 2007 (12.6 → 8.6 cm); control is unchanged.

![Burned organic layer depths](anaktuvuk-phase1-organic-layers-burned.png)

![Control organic layer depths](anaktuvuk-phase1-organic-layers-control.png)

Regenerate after any run:

```sh
make thermokarst-anaktuvuk-phase1-validation   # add --reuse if transient output exists
make thermokarst-anaktuvuk-plot-diagnostics
```

### dvmdostem stage years (Phase 1 harness)

| Stage | CLI flag | Stage A (spin-up) | Stage B (transient) | Notes |
|---|---|---:|---:|---|
| PR (pre-run) | `--pr-yrs` | **100** | 0 | BGC initialization |
| EQ (equilibrium) | `--eq-yrs` | **1000** | 0 | Soil C equilibration (~1000 yr) |
| SP (spin-up) | `--sp-yrs` | **100** | **20** | Stage B repeats 24-yr seasonal climatology |
| TR (transient) | `--tr-yrs` | 0 | **24** | Calendar 2000–2023; fire at climate index 27 |
| SC (scenario) | `--sc-yrs` | 0 | 0 | Not invoked |

Stage A uses **thermokarst off** (legacy thermal). Stage B enables thermokarst after bridge + ice injection.

### Subsidence and temperature contrast figures

- `anaktuvuk-phase1-subsidence-burned-vs-control.png` — cumulative subsidence time series
- `anaktuvuk-phase1-subsidence-by-window.png` — LiDAR-window bars
- `anaktuvuk-phase1-tdd-ratio.png` — thawing degree-day contrast (0.15 m proxy)
- `anaktuvuk-phase1-magt-1m.png` — 1 m mean annual ground temperature

![Burned vs control subsidence](anaktuvuk-phase1-subsidence-burned-vs-control.png)

![LiDAR-window subsidence bars](anaktuvuk-phase1-subsidence-by-window.png)

![TDD ratio burned / control](anaktuvuk-phase1-tdd-ratio.png)

![1 m mean annual ground temperature](anaktuvuk-phase1-magt-1m.png)

## Max-organic-burn experiment (thermal contrast probe)

**Output:** `experiments/thermokarst/anaktuvuk_max_organic_burn_results/`

CMT05 fire parameters patched for **full organic-column combustion** (`foslburn=1.0`, `vsmburn=1.0`, `r_retain_c=0.0`); snow pairing gate relaxed (informational). Same hybrid staging, climate (+7.5 °C), snow scale (~41 cm), and ice band as standard Phase 1.

**Gates:** **12/15 PASS** (restart continuity gates skipped under `--paired-only`)

| Metric | Burned | Control | vs standard Phase 1 |
|---|---:|---:|---|
| Organic burn depth | **~12.6 cm** (full column) | 0 | was ~5.3 cm |
| TDD ratio 2010–2014 | **1.49** | — | was 1.04 |
| TDD ratio 2019–2021 | **1.25** (PASS) | — | was 0.85 |
| MAGT offset 1 m (2023) | **+0.69 °C** (PASS) | — | was −0.42 °C |
| Max ALT | **147 cm** | 128 cm | +19 cm burned |
| Subsidence 2009–2014 | 0 cm | 0 cm | unchanged (ice band still too deep) |

Run:

```sh
make thermokarst-anaktuvuk-max-organic-burn-transient
make thermokarst-anaktuvuk-max-organic-burn-validation
make thermokarst-anaktuvuk-max-organic-burn-plot-diagnostics
```

![Max-organic-burn excess ice degradation](anaktuvuk-max-organic-burn-excess-ice-degradation.png)

### Observation provenance

Bundled under `experiments/thermokarst/anaktuvuk_validation/obs/`:

- `jones2024-lidar-subsidence-by-terrain.csv`
- `jones2024-ground-temperature-annual.csv`
- `jones2024-cryostratigraphy-coring.csv`
- `jones2024-ground-ice-content.csv`
- `jones2024-north-slope-climate-monthly.csv`

## Phase 2 — terrain units and stabilization

**Output:** `experiments/thermokarst/anaktuvuk_phase2_validation_results/`

| Cell | Role | Slope | Drainage | Fire | Ice band |
|---|---|---:|---:|---|---|
| (0, 0) | Yedoma upland burned | 0° | 0 | 2007 | 0.30–1.00 m, 28 % |
| (0, 1) | Yedoma upland control | 0° | 0 | none | same |
| (1, 0) | Yedoma slope burned | 3° | 0 | 2007 | 0.30–1.00 m, 30 % |
| (1, 1) | DLB / lowland burned | 0° | 1 | 2007 | 0.25–0.80 m, 24 % |

Phase 2 should resume from the hybrid Stage A restart (`restart-sp-tk-ready.nc` or bridged Phase 1 state), inject terrain-specific excess ice, and run one **15 TR** four-cell simulation. **Not yet re-run** under the hybrid workflow.

```sh
make thermokarst-anaktuvuk-phase2-validation
```

**Previous run (30 EQ legacy):** 7/8 gates PASS (all hard gates PASS). `VEGC` recovery on upland burned is upward (73.6 → 77.1 g m⁻²); subsidence soft gates await ice-band calibration.

**Soft gates:**

- Stabilization ratio (upland burned): 2014–2021 / 2009–2014 **< 0.25**
- Slope subsidence 2009–2014 **≥** upland burned
- Upland burned `VEGC` trend upward post-2010 (sign only) — **PASS**

![Phase 2 four-cell subsidence](anaktuvuk-phase2-subsidence-four-cells.png)
