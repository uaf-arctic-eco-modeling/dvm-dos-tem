# Samoylov thermokarst experiment spec (DVM-DOS-TEM)

**Date:** 2026-09-18

**Repository:** `/Users/EJafarov/projects/TEM_abrupt_thaw_dev`

**Scientific reference:** Bender et al. (2026), https://doi.org/10.5194/egusphere-2026-1039

**Status:** Phases 0–2 scaffolded (`samoylov_validation.py --phase 0|1|2`; Phase 2 default is scaffold-only)

## Purpose

Set up a **Samoylov Island** polygon-tundra experiment in DVM-DOS-TEM that compares
**Rim** and **Center** columns under shared forcing, with thermokarst subsidence and
ground temperatures as primary outputs.

This is a **Bender-inspired scoping study**, not a CLM reproduction. TEM runs two
**independent columns** on the same climate file. It does **not** implement CLM's
inter-tile snow redistribution, lateral heat flux, or lateral perched-water exchange.

Success criteria are staged:

1. **Phase 0 (pipeline):** two cells complete; ice runs subside; REF/control does not.
2. **Phase 1 (validation window):** seasonal soil temperature and snow depth at Rim vs
   Center are qualitatively consistent with Bender Fig. 2 (2002–2014).
3. **Phase 2 (full transient):** century-scale subsidence and ALT trajectories are
   physically plausible and bracket paper ranges.

## Site metadata

| Field | Value |
|---|---|
| Name | Samoylov Island |
| Location | 72°22′N, 126°28′E |
| Permafrost zone | Cold continuous |
| Mean annual ground temperature (obs.) | ≈ −9 °C (Boike et al., 2019) |
| Landscape | Ice-wedge polygon tundra (LCP → HCP gradient) |
| Paper tiles | **Rim** (elevated, ice-rich) and **Center** (lower, saturated) |

## Experiment matrix

Run three transient cases on a **two-cell grid** (same forcing, different soil/ice):

| Case | Cell (0,0) | Cell (0,1) | Thermokarst | Role |
|---|---|---|---|---|
| `ref` | Rim profile | Center profile | disabled | No-excess-ice reference |
| `rim-ice` | Rim profile | Rim profile | enabled | Isolated Rim response |
| `center-ice` | Center profile | Center profile | enabled | Isolated Center response |
| `paired` | Rim profile | Center profile | enabled | **Primary** landscape contrast |

The **`paired`** case is the main scientific target. The single-profile cases help
separate soil-structure effects from column-to-column forcing identity.

### Known TEM approximations vs CLM

| Bender process | TEM Phase 1–2 |
|---|---|
| Snow redistribution Rim → Center | ❌ manual snow tuning per column only |
| Lateral subsurface heat flux | ❌ |
| Lateral perched-water flux | ❌ (Richards drainage only) |
| Dynamic height difference ΔH(t) | ❌ (independent surface elevations) |
| Excess-ice melt → subsidence | ✅ `TKSUBSIDENCE` |
| Soil temperature profile | ✅ `TLAYER` + original-depth correction |
| Snow thermal mass | ✅ `SNOWTHICK` |

## Forcing

### Source protocol (from paper §2.3)

1. Extract **GSWP3** 3-hourly data at the Samoylov grid point (external download).
2. Compute **daily mean T anomaly** between Samoylov station observations and GSWP3
   for **2002–2014** (Boike et al., 2022).
3. Add that **day-of-year anomaly** to all GSWP3 years in the transient file.
4. Adjust precipitation:
   - reduce **summer liquid** precipitation by the mean percentile bias vs obs;
   - reduce **winter** precipitation by **25 %**;
   - target mean annual total ≈ **236 mm yr⁻¹** (liquid ≈ **117 mm yr⁻¹**; obs liquid
     ≈ 146 mm yr⁻¹).

### TEM driver format

Follow the existing harness pattern (`experiments/thermokarst/bgc_coupling_validation.py`):

- NetCDF monthly fields on dimension `time`: `tair`, `precip`, `nirr`, `vapor_press`
- One grid cell (or two-cell mask with identical climate in both cells)
- CO₂ file: pre-industrial **284 ppm** for spin-up; transient 1901–2014 record for TR

### Recommended staging

| Stage | Years | Climate source | Notes |
|---|---:|---|---|
| **Phase 0** | 1 PR + 10 EQ + 13 TR | synthetic Arctic monthly template | prove pipeline before GSWP3 |
| **Phase 1** | 1 PR + 30 EQ + 13 TR | bias-corrected 2002–2014 loop | validation vs Fig. 2 |
| **Phase 2** | 1 PR + 150 EQ + 114 TR | 1930–1950 loop (EQ), 1901–2014 (TR) | paper-equivalent spin-up + transient |

Phase 0 synthetic template (initial guess, °C / mm month⁻¹ / W m⁻²):

```python
# Samoylov-like monthly mean air temperature (°C) and precipitation (mm)
tair   = [-32, -30, -24, -12,  -2,   6,   8,   6,   1,  -8, -20, -28]
precip = [  8,   7,   6,   7,  10,  18,  22,  20,  14,  10,   9,   8]  # dry; sum ≈ 139 mm
nirr   = [  0,   2,   8,  18,  22,  24,  20,  14,   6,   2,   0,   0]
```

Replace with GSWP3 + Boike bias correction before claiming validation.

## Spatial setup

### Grid

- `run-mask-two-cells.nc`: activate `(0,0)` and `(0,1)`
- `topo.nc`: **slope = 6°** at both cells (paper value; not the 30° Toolik default)
- `drainage_file`: start with class **0** (well drained) for Rim; test class **1**
  (poorly drained / wetland analog) for Center in `paired` if Center stays too dry
- `veg_class_file`:
  - Rim → **CMT05** (tussock tundra, drier polygon rim analog)
  - Center → **CMT04** (shrub tundra) or the wettest available Arctic CMT in your
    parameter set; confirm against `parameter/cmt#*.nc` before locking

Document final CMT choices in the validation summary JSON when implemented.

## Soil and initial conditions (Table A1, Samoylov)

Initial state for both columns (paper):

- soil temperature: **−2 °C** throughout
- liquid saturation: **95 %** of pore capacity
- vegetation: predefined Arctic grass analog via fixed CMT (BGC off)

### Rim column (tile 1) — mineral-forward, shallow peat

| Depth (m) | Sand (%) | Clay (%) | Organic (kg m⁻³) |
|---:|---:|---:|---:|
| 0.00–0.09 | 36 | 15 | 130 |
| 0.10–0.25 | 60 | 20 | 130 |
| 0.25–0.50 | 60 | 20 | 40 |
| 0.50–1.25 | 60 | 20 | 40 |
| > 1.25 | 60 | 20 | 0 |

### Center column (tile 2) — peat-rich, clay-rich mineral soil

| Depth (m) | Sand (%) | Clay (%) | Organic (kg m⁻³) |
|---:|---:|---:|---:|
| 0.00–0.09 | 36 | 15 | 130 |
| 0.10–0.25 | 36 | 15 | 130 |
| 0.25–0.50 | 40 | 40 | 130 |
| 0.50–1.25 | 40 | 40 | 90 |
| > 1.25 | 40 | 40 | 0 |

**TEM implementation note:** the production column uses TEM layer types and CMT
parameters, not explicit sand/clay fractions. Phase 0 should map these profiles to
the closest available organic/mineral layer sequence in the equilibrium restart
(`PR` + `EQ`). Phase 1 may require a custom restart builder or manual layer editing
in `restart-eq.nc` if default CMT spin-up does not bracket the paper's peat/mineral
structure.

## Excess ice

### Paper geometry (Table 1 — for documentation only; not coupled in TEM)

| Parameter | Samoylov value | TEM use |
|---|---:|---|
| A1 (Rim area) | 70 m² | not used (no tiling) |
| A2 (Center area) | 58 m² | not used |
| dx | 2.1 m | not used |
| dl | 26.7 m | not used |
| ΔH_init | 0.38 m | target elevation offset Rim vs Center (qualitative) |
| fsplit | 0.7 | Rim receives 70 % of excess ice in paired conceptual budget |

### TEM thermokarst configuration

Inject excess ice **after equilibrium**, before transient, using the restart patch
pattern from `bgc_coupling_validation.inject_excess()`:

```json
"thermokarst": {
  "enabled": true,
  "excess_fraction": 0.25,
  "top_depth": 0.25,
  "bottom_depth": 3.00
}
```

Phase 0 harness uses a **shallow ice band** (0–0.5 m) so subsidence occurs under
the synthetic 13-year forcing. Paper-depth ice (0.25–3 m) is deferred to Phase 1+.

| Case | `excess_fraction` | `top_depth` (m) | `bottom_depth` (m) | Notes |
|---|---:|---:|---:|---|
| Rim (Phase 0) | 0.35 | 0.0 | 0.50 | higher fraction → more subsidence |
| Center (Phase 0) | 0.25 | 0.0 | 0.50 | lower fraction |
| Rim (Phase 1+) | 0.30 | 0.25 | 2.50 | paper target |
| Center (Phase 1+) | 0.20 | 0.25 | 3.00 | paper target |
| REF | 0.00 | — | — | no injected excess ice |

Alternative: inject a fixed mass (kg m⁻²) with `inject_excess_mass(restart, mass,
depth=0.40)` if fraction-based expansion does not match expected subsidence.

**Spin-up context from paper:** after REF spin-up, Samoylov sensitivity runs start
with **0.38 m** initial Rim elevation offset and **no prior subsidence**. Use this
as an order-of-magnitude subsidence ceiling for century-scale paired runs, not a hard
gate in Phase 0.

## Model stages and switches

Match paper physics scope: **soil physics only, no BGC**.

```json
"stage_settings": {
  "pr": { "env": true,  "bgc": false, "nfeed": false, "avlnflg": false,
          "baseline": false, "dsb": false, "dsl": false, "dyn_lai": false },
  "eq": { "env": true,  "bgc": false, "nfeed": false, "avlnflg": false,
          "baseline": true,  "dsb": false, "dsl": false, "dyn_lai": false },
  "tr": { "env": true,  "bgc": false, "nfeed": false, "avlnflg": false,
          "baseline": false, "dsb": false, "dsl": false, "dyn_lai": false }
}
```

Recommended CLI for Phase 1:

```sh
./dvmdostem -f experiments/thermokarst/samoylov_validation/paired.json \
  --log-level warn --max-output-volume=-1 \
  --pr-yrs 1 --eq-yrs 30 --tr-yrs 13
```

Phase 2 full run:

```sh
./dvmdostem -f experiments/thermokarst/samoylov_validation/paired-full.json \
  --log-level warn --max-output-volume=-1 \
  --pr-yrs 1 --eq-yrs 150 --tr-yrs 114
```

Use `baseline_start: 1930`, `baseline_end: 1950` in `model_settings` for the EQ
stage when the EQ climate file contains the 1930–1950 loop.

## Output specification

Extend `config/output_spec.csv` (same pattern as `observed_fire_validation.py`):

| Variable | Interval | Layers | Purpose |
|---|---|---|---|
| `TLAYER` | monthly | forced | soil temperature profile |
| `LAYERDEPTH` | monthly | forced | layer top depths (settled surface) |
| `LAYERDZ` | monthly | forced | layer thicknesses |
| `TSOIL_30cm`, `TSOIL_100cm` | monthly | — | quick depth probes |
| `SNOWTHICK` | daily | — | compare to paper snow height |
| `SNOWEND` | yearly | — | end-of-season snow depth |
| `TKSUBSIDENCE` | daily | — | cumulative subsidence |
| `TKFRONT`, `TKFRONTTYPE` | daily | — | active layer / frost table |
| `TKPOND`, `TKSURFICE` | daily | — | surface hydrology state |
| `TKLIQGEN`, `TKLIQDRAINAGE`, `TKLIQRUNOFF` | daily | — | water routing diagnostics |

## Observation targets (external data required)

`Bender_data/` does **not** contain these. Download from cited sources before Phase 1
gates.

| Variable | Depth / period | Observed (paper) | Primary figure |
|---|---|---|---|
| Soil temperature | 0.10 m, daily mean 2002–2014 | Rim amplitude > Center | Fig. 2b |
| Soil temperature | 0.65 m, daily mean 2002–2014 | Center ≈ obs; Rim too warm in winter | Fig. 2c |
| Active layer thickness | September max 2002–2014 | Rim 0.47 m, Center 0.49 m | Fig. 2d |
| Snow depth | daily mean 2002–2014 | Rim 0.09–0.71 m; shared obs Rim/Center | Fig. 2a |
| End-of-season snow | 2002–2014 range | Rim 0.30–0.81 m; Center 0.68–1.17 m | §3.1 |
| Winter soil T minimum | ≈ 0.65 m | ≈ −25 °C (model ≈ −15 °C with snow bias) | §3.2 |

Store observations as CSV:

```text
experiments/thermokarst/samoylov_validation/obs/
  samoylov_soilT_rim_10cm.csv      # columns: doy, mean_C, std_C (optional)
  samoylov_soilT_center_10cm.csv
  samoylov_soilT_rim_65cm.csv
  samoylov_soilT_center_65cm.csv
  samoylov_snow_depth.csv          # paper digitized or Boike archive
  samoylov_alt_sept.csv            # Rim, Center max ALT by year
```

## Derived model diagnostics

Compute in the validation script (mirror `observed_fire_validation.py`):

1. **Original-depth temperature:** subtract end-of-month cumulative `TKSUBSIDENCE`
   from fixed depths (0.10 m, 0.65 m) before comparing to obs.
2. **Daily mean climatology:** average each DOY over 2002–2014 (or TR window).
3. **September ALT:** max thaw depth from `TKFRONT` when `TKFRONTTYPE` indicates
   thawed active layer; compare yearly max in September.
4. **End-of-season snow:** `SNOWTHICK` on melt-out day (first day snow = 0 in spring).
5. **Rim − Center contrasts:** ΔT at 0.65 m in winter (DJF) and summer (JJA).

## Validation gates

### Phase 0 — pipeline (hard)

| Gate | Criterion |
|---|---|
| Run completion | both cells `run_status == 100` |
| REF subsidence | max `TKSUBSIDENCE` < 1 mm over TR |
| Ice subsidence | monotonic increasing `TKSUBSIDENCE`; final > 1 cm |
| Energy/mass sanity | no NaNs in `TLAYER` or `TKSUBSIDENCE` |
| Restart (optional) | split/resume at TR year 6: subsidence diff < 0.1 mm |

### Phase 1 — Samoylov window (soft, qualitative first)

| Gate | Target | Priority |
|---|---|---|
| Winter Rim colder than Center | ΔT(0.65 m, DJF) > 2 °C | high |
| Center Sept ALT | 0.35–0.60 m | high |
| Rim Sept ALT | 0.35–0.85 m (paper model 0.7 m) | medium |
| Center end-season snow > Rim | Δ snow > 0.10 m | high |
| Obs RMSE soil T at 0.65 m | < 5 °C seasonal cycle (Center) | medium |

Do **not** fail Phase 1 on winter absolute temperature until snow forcing is
bias-corrected; the paper itself reports ≈ 10 °C warm bias at Samoylov.

### Phase 2 — century transient (soft)

| Gate | Target |
|---|---|
| Cumulative subsidence | 0.05–0.50 m over 1901–2014 for ice cases |
| Center ALT deepening since 1901 | ≈ 0.10 m (paper) |
| Rim vs Center hydrology | Center `TKPOND` > Rim in summer |

## Proposed file layout

```text
experiments/thermokarst/samoylov_validation/
  samoylov_validation.py          # harness (to be implemented)
  samoylov-output-spec.csv
  paired.json                     # generated at run time
  obs/                            # external observations (user supplied)
  results/
    summary.json
    checks.csv
    paired/
    ref/
    figures/
      samoylov-soilT-10cm.png
      samoylov-soilT-65cm.png
      samoylov-snow.png
      samoylov-subsidence.png
      samoylov-alt.png
```

Run Phase 0:

```sh
make thermokarst-samoylov-validation
```

Build GSWP3+Boike climate (CRU proxy until `--gswp3` supplied):

```sh
make thermokarst-samoylov-gswp3-climate
```

Phase 2 scaffold (drivers + run script; no dvmdostem execution):

```sh
make thermokarst-samoylov-phase2-validation
```

Full Phase 2 century run:

```sh
make thermokarst-samoylov-phase2-validation RUN=1
```

## Example run configuration skeleton

```json
{
  "IO": {
    "parameter_dir": "DATA/Toolik_10x10_30yrs/parameters/",
    "hist_climate_file": "experiments/thermokarst/samoylov_validation/samoylov-climate.nc",
    "co2_file": "DATA/Toolik_10x10_30yrs/co2.nc",
    "runmask_file": "experiments/thermokarst/samoylov_validation/run-mask-two-cells.nc",
    "veg_class_file": "experiments/thermokarst/samoylov_validation/vegetation.nc",
    "drainage_file": "experiments/thermokarst/samoylov_validation/drainage.nc",
    "topo_file": "experiments/thermokarst/samoylov_validation/topo.nc",
    "output_dir": "experiments/thermokarst/samoylov_validation/results/paired/",
    "output_spec_file": "experiments/thermokarst/samoylov_validation/samoylov-output-spec.csv",
    "output_nc_pr": 0,
    "output_nc_eq": 0,
    "output_nc_sp": 0,
    "output_nc_tr": 1,
    "output_nc_sc": 0,
    "output_interval": 1,
    "restart_from": "experiments/thermokarst/samoylov_validation/results/initialization/restart-eq.nc"
  },
  "model_settings": {
    "cell_timelimit": 0,
    "dynamic_lai": 0,
    "baseline_start": 1930,
    "baseline_end": 1950,
    "thermokarst": {
      "enabled": true,
      "excess_fraction": 0.25,
      "top_depth": 0.25,
      "bottom_depth": 3.00
    }
  },
  "stage_settings": {
    "pr": { "env": true, "bgc": false, "nfeed": false, "avlnflg": false,
            "baseline": false, "dsb": false, "dsl": false, "dyn_lai": false },
    "eq": { "env": true, "bgc": false, "nfeed": false, "avlnflg": false,
            "baseline": true, "dsb": false, "dsl": false, "dyn_lai": false },
    "tr": { "env": true, "bgc": false, "nfeed": false, "avlnflg": false,
            "baseline": false, "dsb": false, "dsl": false, "dyn_lai": false },
    "tr_start_yr": 0
  }
}
```

Per-cell thermokarst fractions require **separate restart patches** after EQ (Rim
cell vs Center cell) because `thermokarst` settings in JSON are global; the harness
should fork `restart-eq.nc` into `restart-eq-rim.nc` and `restart-eq-center.nc`
with different `TKexcess` fields before the paired transient.

## Implementation checklist

- [x] Create `samoylov_validation.py` from `bgc_coupling_validation.py` template
- [x] Build Phase 0 synthetic climate NetCDF
- [x] Set slope = 6° and two-cell mask
- [x] Run PR + EQ without thermokarst; patch `TKexcess` per column profile
- [x] Run `ref`, `rim-ice`, `center-ice`, `paired` transients
- [x] Add original-depth TLAYER extraction at 0.10 m and 0.65 m
- [x] Seed paper-derived reference obs CSVs into `obs/` (replace with Boike archive when available)
- [x] Phase 1 harness: 30 EQ + 13 TR, paper-depth ice, soft validation gates
- [x] GSWP3+Boike climate builder (`samoylov_validation/gswp3_climate.py`, CRU proxy fallback)
- [x] Phase 2 scaffold: 150 EQ + 114 TR drivers, CO₂ slice, `phase2-scaffold.json`, `--run` flag
- [x] Download GSWP3-W5E5 monthly tas/pr (ISIMIP3a) and extract Samoylov grid point
- [x] Boike station CSV from PANGAEA.905230 (2002–2014 calibration window)
- [ ] Re-run Phase 1 with extended Boike calibration
- [ ] Adopt best hydrology variant from `make thermokarst-samoylov-hydrology-tune`
- [x] Execute full Phase 2 century run (`make thermokarst-samoylov-phase2-validation RUN=1`) — hard 2/2, soft 0/3
- [x] Write `samoylov-validation-report.md` with figures and gate table (Phase 1 run)

## Limitations (explicit)

1. **No inter-tile coupling** — the largest expected bias vs Bender Fig. 2.
2. **Soil texture mapping** — TEM CMT layers ≠ CLM sand/clay/organic tables.
3. **Snow scheme differences** — expect winter warm bias until forcing and snow
   parameters are tuned.
4. **Observations not bundled** — validation requires external Boike archive work.
5. **Excess-ice inventory uncertain** — `excess_fraction` must be calibrated; paper
   uses circum-Arctic ice map × fsplit, not point measurements.

## Next step

1. Download GSWP3 monthly forcing at 72.37°N, 126.47°E and pass `--gswp3` to the builder.
2. Replace `obs/boike_samoylov_monthly_2002-2014.csv` with primary Boike station data.
3. Re-run Phase 1 with `--gswp3` / `--boike` and review soft gates.
4. Execute Phase 2 century run: `make thermokarst-samoylov-phase2-validation RUN=1`.
