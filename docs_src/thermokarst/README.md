# Experimental thermokarst mechanism

## Status and scope

This repository contains a **runnable, dependency-light C++ reference column and
an opt-in production integration in DVM-DOS-TEM**.
It uses TEM's physical constants and soil C/N pool convention. It implements
single-column heat conduction, phase change, excess-ice loss, irreversible
settlement, conservative layer remapping, overflow accounting, and a versioned
restart format. The executable is `build/thermokarst/thermokarst-column`.

When `model_settings.thermokarst.enabled` is true, `Soil_Env` uses the finite-volume
enthalpy solver for the complete snow-soil-rock column and bypasses the legacy
Stefan/TemperatureUpdator path for that day. The adapter stores matrix thickness,
matrix porosity, excess ice, and cumulative budgets on production layers; contracts
layers in place; rebuilds fronts and drainage; recalculates root distributions; and
routes released liquid through existing ponding, infiltration, Richards drainage,
and runoff. Annual dynamic-soil splits, merges, and resizes use a conservative
material-horizon map for physical, C/N, root, front, and accumulated layer state.
Fire-driven topology uses an open-system map that couples burned matrix, water,
and sensible enthalpy to combustion and post-fire hydrology while retaining
WildFire's authoritative C/N losses. Production NetCDF restarts persist the
versioned thermokarst state and geometry. With the setting absent or disabled, TEM
uses its legacy thermal pathway.

This is still an experimental one-column mechanism. SOM-driven dynamic soil (`dsl`)
and fire-driven topology (`dsb`) are supported while thermokarst is active.
The budgeted surface ice/pond reservoir now conducts with the snowpack and the
top soil layer. Lateral thermokarst drainage is still represented only through
TEM's existing Richards drainage pathway.

Base repository: https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem

Base commit: `419a4eb3fb1fb0ea91795a76d366396c850d5fd3`.

Scientific motivation: Bender et al. (2026),
https://doi.org/10.5194/egusphere-2026-1039. This is an original, simplified TEM
prototype, not a line-for-line implementation or reproduction of the CLM study.

## Run

From the repository root:

```sh
make thermokarst-test
build/thermokarst/thermokarst-column --help
```

C++11 and Make are sufficient for the numerical executables; Boost, NetCDF,
LAPACK, and jsoncpp are not required for these targets.

To reproduce every experiment, numerical check, and figure:

```sh
python3 -m venv .venv-thermokarst
.venv-thermokarst/bin/python -m pip install -r experiments/thermokarst/requirements.txt
.venv-thermokarst/bin/python experiments/thermokarst/run_suite.py
```

Results go to `experiments/thermokarst/results/` (ignored by Git). Override with
`--output /absolute/output/directory`. The pipeline exits nonzero if any unit test,
integration check, or programmatic figure-boundary check fails. It stores source
CSV data, test results, JSON metrics, PNG/SVG figures, and restart snapshots.

### Code-only clone: inputs and report figures

Git tracks **source, harnesses, small obs CSVs, and markdown reports** — not
LTER/PANGAEA/GSWP3 caches, prebuilt site climate NetCDF, or PNG figures under
`docs_src/thermokarst/`. After checkout, prepare site drivers once:

```sh
# Barrow: builds nws-barrow-climate-full.nc on first validation run if missing
make thermokarst-barrow-validation-phase0

# Samoylov
make thermokarst-samoylov-fetch-data
make thermokarst-samoylov-gswp3-climate

# EML (Healy / CiPEHR)
make thermokarst-eml-fetch-data thermokarst-eml-fetch-gps thermokarst-eml-fetch-wtd
make thermokarst-eml-climate
```

Anaktuvuk uses bundled obs CSVs only; North Slope climate is built at run time
(see [anaktuvuk-experiment-spec.md](anaktuvuk-experiment-spec.md)). Report PNGs
embedded in `*-report.md` files are regenerated when you run the corresponding
`make thermokarst-*-validation` (or plot) targets; SVG copies may remain in Git
where committed.

Production restart validations are available as separate targets:

```sh
make thermokarst-production-validation
make thermokarst-active-thaw-validation
make thermokarst-fire-validation
make thermokarst-fire-recovery-validation
make thermokarst-observed-fire-validation
make thermokarst-samoylov-validation
make thermokarst-samoylov-phase1-validation
make thermokarst-samoylov-gswp3-climate
make thermokarst-samoylov-fetch-data
make thermokarst-samoylov-hydrology-tune
make thermokarst-samoylov-phase2-validation
make thermokarst-eml-validation
make thermokarst-eml-phase1-validation
```

Refresh Boike (2002–2014) and GSWP3 point forcing:

```sh
make thermokarst-samoylov-fetch-data
```

Center hydrology tuning (drainage/CMT matrix, 10 EQ + 13 TR):

```sh
make thermokarst-samoylov-hydrology-tune
```

Build GSWP3+Boike climate only:

```sh
make thermokarst-samoylov-gswp3-climate
# with real GSWP3:
.venv-thermokarst/bin/python experiments/thermokarst/samoylov_validation/build_gswp3_climate.py \
  --gswp3 /path/to/gswp3_samoylov_monthly.nc
```

Phase 2 scaffolds drivers and run scripts by default (no century simulation).
Add `RUN=1` to execute the full 150 EQ + 114 TR run:

```sh
make thermokarst-samoylov-phase2-validation RUN=1
```

The Samoylov Phase 0 harness runs two-cell Rim/Center polygon columns under
synthetic Arctic forcing (1 PR + 10 EQ + 13 TR years), injects shallow excess
ice, and checks subsidence plus original-depth soil temperatures.

Phase 1 extends spin-up to 30 EQ years, uses paper-depth ice (0.25–3 m) and
paper-calibrated synthetic forcing (~236 mm yr⁻¹), compares soil temperature,
snow, and September ALT against reference curves in
`experiments/thermokarst/samoylov_validation/obs/`, and writes
[samoylov-validation-report.md](samoylov-validation-report.md).

See [samoylov-experiment-spec.md](samoylov-experiment-spec.md).

The active-thaw test places a restart inside ongoing excess-ice melt under an
explicitly one-year-periodic forcing. It compares subsidence, collapse water,
conservation residuals, fronts, root remapping, and settled geometry. See
[active-thaw-validation-report.md](active-thaw-validation-report.md) for the
full configuration, results, figures, and limitations.

The fire validation enables thermokarst, BGC, dynamic soil, and fire disturbance
for CMT04 and CMT05. It checks combustion-linked water and enthalpy loss,
post-fire hydrology, layer geometry, fronts, roots, C/N state, and restart
continuation. See
[fire-topology-validation-report.md](fire-topology-validation-report.md).

The fire-recovery validation places that fire on day-of-year 180 while excess
ice is still melting, uses a Toolik fire-weather year and site-specific
severity, and follows three recovery years against an unburned control. See
[fire-recovery-validation-report.md](fire-recovery-validation-report.md).

The observed-fire validation keeps that coupled snow/pond/fire column under a
multi-year Toolik climate series, a vegetation-mapped burn-severity field,
dynamic soil through recovery, and TEM ponding merged with the thermokarst
surface store as one overnight thermal mass. The resumed segment starts at
transient year 3 of the same climate, CO2, and fire files. Original-surface
temperatures use end-of-month subsidence. See
[observed-fire-validation-report.md](observed-fire-validation-report.md).

```sh
make thermokarst-observed-fire-validation
```

The historic-projection validation replaces the CMT severity lookup with an
input burn-severity raster, runs the full 115-year historic and 85-year
projected Toolik series, and injects 25, 50, and 100 kg m⁻² excess-ice lenses
at 20 cm. See
[historic-projection-validation-report.md](historic-projection-validation-report.md).

```sh
make thermokarst-historic-projection-validation
```

Draft experiment specifications for additional Arctic validation sites:

- [Samoylov experiment spec](samoylov-experiment-spec.md) — Bender-inspired Rim/Center
  polygon tundra (not yet implemented).
- [Barrow CRREL subsidence spec](barrow-experiment-spec.md) — Streletskiy et al. (2016)
  plots 34, 37, 40, 44; four-cell isotropic subsidence validation.
  Report: [barrow-validation-report.md](barrow-validation-report.md) (Phases 0–2).

```sh
make thermokarst-barrow-validation-phase0   # pipeline proof
make thermokarst-barrow-alt-calibration     # Phase A: ALT via n-factor (no ice)
make thermokarst-barrow-alt-calibrate       # Phase A: sweep nfactor_s grid
make thermokarst-barrow-diagnostic-plots    # climate, soil thermal, isotherm ALT figures
make thermokarst-barrow-validation-phase1   # Streletskiy 2003–2015 window
make thermokarst-barrow-validation-phase2   # full 1962–2015 record
make thermokarst-barrow-validation          # all phases
```

- [EML CiPEHR subsidence spec](eml-experiment-spec.md) — Rodenhizer et al. (2020)
  warming-treatment subsidence and thaw-penetration validation at Eight Mile Lake.
- [Anaktuvuk River fire subsidence spec](anaktuvuk-experiment-spec.md) — Jones et al. (2024)
  2007 burned vs unburned Yedoma tundra; LiDAR subsidence 2009–2014 and ground-temperature
  validation against Arctic Data Center observations.
- [Anaktuvuk validation report](anaktuvuk-validation-report.md) — Phase 0 (15/15) and Phase 1 harness results.

```sh
make thermokarst-anaktuvuk-validation
make thermokarst-anaktuvuk-climate-calibration
make thermokarst-anaktuvuk-phase1-validation
```

```sh
make thermokarst-eml-validation          # Phase 0 pipeline
make thermokarst-eml-phase1-validation   # Healy climate + calibrated treatment runs
make thermokarst-eml-phase2-validation   # BNZ:453 climate, thaw penetration, GPS obs
make thermokarst-eml-phase3-validation   # snow-fence bias, 15-yr deep thaw, WTD gates
make thermokarst-eml-phase4-validation   # WTD subsidence coupling + multi-objective calibration
make thermokarst-eml-phase5-validation   # CiPEHR snow SWE proxy (40/80 cm) + recalibration
make thermokarst-eml-thermal-plots       # soil T depth–time contours for validation report
make thermokarst-eml-climate-plots       # climate driver figure for validation report
```

Report: [eml-validation-report.md](eml-validation-report.md) (Phase 1 control brackets
Rodenhizer; Phases 2–3 add BNZ site met, thaw-penetration, GPS, and water-table gates).

Run a custom constant-temperature experiment:

```sh
mkdir -p experiments/thermokarst/results
build/thermokarst/thermokarst-column \
  --days 90 --top 5 --excess-depth 0.15 --max-step 300 \
  --output experiments/thermokarst/results/custom.csv \
  --profile experiments/thermokarst/results/custom-profile.csv \
  --save experiments/thermokarst/results/custom.restart
```

`--excess-depth` is the total **added excess-ice thickness**, not an ice fraction.
`--days` is additional elapsed time when continuing from a restart. The initial
matrix is 1.5 m deep. Five matrix layers between 0.3 and 0.8 m receive equal ice
inventories; adding ice expands their geometric thickness. Initial temperature is
-2 C and pore ice is 90% of matrix pore-volume capacity. The default ground-surface
boundary is +8 C, with zero basal heat flux, for 180 days. These are deliberately
idealized forcings, not an Alaska climate projection.

## State and equations

`include/Thermokarst.h` declares `Cell`, `Column`, and `Budget`.
`src/Thermokarst.cpp` implements the physics. Each cell stores:

- Matrix thickness `matrix` (m), including ordinary pore space.
- Matrix porosity, solid heat capacity, conductivity, and a material identifier.
- `water`, `ice`, and `excess` (kg/m2). `ice` means pore ice only.
- `enthalpy` (J/m2), referenced to ice at 0 C.
- Six passive extensive pools (g/m2): `rawc`, `soma`, `sompr`, `somcr`, `orgn`, `avln`.

For matrix thickness d_m and excess mass X:

    d = d_m + X / rho_ice
    C_A = d_m (1 - porosity) C_solid + W c_water + (I + X) c_ice
    H = C_A T + L_f W

Conduction is finite-volume, using harmonic interface conductance and an explicit
adaptive timestep limited to 0.2 times the smallest sensible-heat timescale. The
conductivity is a geometric mixture of solid, liquid, ice, and air volume fractions
in the expanded layer. This is a prototype closure, not a calibrated replacement
for TEM's soil conductivity scheme.

After adding energy, phase equilibrium is solved at 0 C:

    W_new = clamp(H / L_f, 0, W + I + X)
    frozen_new = total_mass - W_new
    X_new = min(X_old, frozen_new)
    I_new = frozen_new - X_new

This prescription melts **pore ice before excess ice within each cell**. It is an
explicit subgrid assumption, not a resolved ice-lens geometry or an unfrozen-water
curve. It can generate layer-scale steps in settlement. Spatial convergence and
alternative subgrid ice distributions are necessary before site calibration.

Excess-ice loss gives:

    settlement = (X_old - X_new) / rho_ice
    surface_new = surface_old - sum(settlement)

The same mass becomes liquid. Latent heat is charged once through enthalpy. Cold
energy first warms the cell to melting temperature; residual heat after complete
melting warms liquid and solids. Refreezing creates pore ice, never new excess ice.
The matrix does not compact and the surface does not rebound.

### Water and overflow

Matrix pore space is constrained by:

    W / rho_water + I / rho_ice <= porosity * d_m

Local surplus goes to an explicitly budgeted surface reservoir, without hydraulic
travel time. Surplus ice from pore-water refreezing is retained at the surface.
Only liquid above the configured surface-liquid capacity becomes runoff. Both
mass and advected enthalpy are transferred. This is a bounded storage/outflow
closure, **not Richards flow**. The reservoir conducts with adjacent snow and soil
when its mass is at least 4 kg m⁻² (TEM's hydrology puddle), so retained surface ice and ponded liquid
intercept atmospheric heat. The pond node's numerical thickness is the physical
water/ice depth, so a 4 mm hydrology puddle is not padded into an air-filled
insulator. Vanishing snow/organic films are omitted from the
explicit stencil. It does not infiltrate back into
soil as a separate Richards pond, move C/N, or replace TEM's hydrology puddle.

### Conservative regridding

Physical collapse precedes numerical regridding. `regrid()` accepts target layer
thicknesses that cover the already-collapsed column exactly. Donor overlap fractions
redistribute water, pore/excess ice, enthalpy, matrix/pore/solid volumes, solid heat
capacity, and each C/N pool. Temperature is recovered from the remapped enthalpy,
not averaged directly. The column base remains fixed in absolute elevation;
local depth is always measured below the changing surface.

Targets crossing different materials or frozen/melting/thawed regimes are rejected
to prevent artificial mixing across phase fronts. The original column is unchanged
if target validation fails. `split_thick()` provides automatic subdivision while
preserving donor boundaries. Arbitrary merging across fronts and material changes
is intentionally unsupported. The default conduction experiment splits its initial
expanded layers to at most 0.1 m; subsequent collapse changes their thicknesses.
The heat-pulse benchmark also exercises regridding midway through melting.

The reference column stores phase mass fractions rather than TEM's explicit front
deque. The production adapter reconstructs that deque after each settled state is
mapped back, without changing the conserved enthalpy or phase masses.

### Budgets

`Column::budget()` includes soil, retained surface storage, and cumulative runoff.
For no external water forcing:

    water_residual = final_total_water - initial_total_water
    energy_residual = final_total_enthalpy - initial_total_enthalpy - boundary_energy_added

C/N and matrix volume are extensive invariants. Output C/N are passive conservation
tests: no decomposition, mineralization, vegetation uptake, or gas production occurs.
`pond_kg_m2` is total retained surface water-equivalent mass, which can include ice.

### Restart

The reference executable's `write_restart()` / `read_restart()` use a strict text format headed
`TEM_THERMOKARST 1`, with 17-digit floating-point precision. All state and cumulative
fluxes are persisted. Unsupported versions, malformed/truncated data, invalid state,
and extra trailing content are rejected. The production NetCDF restart adds
`TKversion`, `TKactive`, `TKstate`, `TKpuddle`, `TKmatrix`, `TKporosity`, and
`TKexcess`. Files without `TKversion` are treated as legacy version-zero restarts
and initialize thermokarst from configuration. Version one preserves settled
geometry and cumulative water/energy accounting. Unsupported future versions are
rejected. Same-platform reference-column restart continuity is tested bitwise;
bitwise reproducibility across compilers/platforms is not promised.

## Verification experiments

1. **Heat pulse:** 0.5 m matrix, porosity 0.5, saturated pore ice, and 0.20 m added
   excess ice at 0 C. Known energy is added incrementally. Exact settlement is
   `min(0.20, max(0, (E/L_f - initial_pore_ice)/rho_ice))`. A mid-run regrid must
   preserve this result, water, and energy.
2. **Classical one-phase Stefan benchmark:** initial frozen column at 0 C, surface
   held at +5 C, no excess ice, 3 m matrix depth. Thaw depth is compared with
   `2 lambda sqrt(alpha t)`, where
   `lambda exp(lambda^2) erf(lambda) = Stefan_number/sqrt(pi)`. Fully thawed
   properties define alpha and the Stefan number. The numerical front uses
   melt-fraction-integrated depth. Meshes are 0.10, 0.05, and 0.025 m.
3. **Thermokarst warming:** the idealized 180-day column described above, with
   0.25 m total excess-ice thickness. Verify ice exhaustion, fixed base, and
   meltwater plus enthalpy accounting.
4. **Controls:** identical forcing with no excess ice; initial cold equilibrium
   with the same excess ice. Neither may subside.
5. **Restart:** 180 days continuously versus 90 days + saved state + 90 days.
6. **Timestep sensitivity:** compare settlement trajectories for maximum timesteps
   of 60 and 30 seconds over 90 days.

Acceptance gates: heat-pulse error <1e-10 m; water residual <1e-8 kg/m2;
energy residual <1e-3 J/m2; C/N residual <1e-8 g/m2; finest Stefan front error
<5 mm at day 15 and decreasing error under refinement; timestep trajectory
difference <1 mm; identical same-platform final restart serialization.

See `tests/thermokarst/test_thermokarst.cpp` for additional unit tests of partial
melting, sensible heat, finite storage, refreezing, all pools, invalid inputs,
material/phase boundaries, and conservative regridding.

## Production configuration and sequencing

Thermokarst is controlled in each run JSON under `model_settings.thermokarst`.
The stock [`config/config.js`](../../config/config.js) keeps it **disabled** for
legacy TEM runs; validation harnesses set `"enabled": true` when they exercise
subsidence, excess ice, or coupled pond/fire topology.

```json
"thermokarst": {
  "enabled": true,
  "excess_fraction": 0.20,
  "top_depth": 0.50,
  "bottom_depth": 2.00
}
```

| Field | Role |
|---|---|
| `enabled` | `true`: finite-volume snow–soil enthalpy path, matrix/excess geometry, subsidence, and TK restart fields. `false` or omitted: legacy Stefan/`TemperatureUpdator` thermal path (default). |
| `excess_fraction` | Volume fraction of **added** excess ice within `[top_depth, bottom_depth]` on a **fresh** run (no versioned TK restart yet). Ignored once settled TK geometry is loaded from restart. |
| `top_depth`, `bottom_depth` | Depth bounds (m below surface) for that initial excess-ice band. |

There is **no separate per-stage** (`pr`, `eq`, `sp`, `tr`, `sc`) thermokarst switch;
the same `enabled` value applies for the whole execution. To spin up BGC on legacy
physics and turn thermokarst on only for the experiment segment, use a **hybrid**
workflow: save a restart with `enabled: false`, then start the transient with
`enabled: true` and that restart (see
[anaktuvuk-experiment-spec.md](anaktuvuk-experiment-spec.md), Stage A / Stage B).

### Restart compatibility (`TKversion` ≥ 1)

NetCDF restarts record `TKactive` (1 = thermokarst was on when the file was written).

| Run config `enabled` | Restart `TKactive` | Outcome |
|---:|---:|---|
| `false` | 1 | **Rejected** — cannot load an active thermokarst state with the module disabled. |
| `true` | 0 | **Hybrid handoff** — BGC/soil state from a light spin-up; thermokarst is enabled on load and layers get matrix geometry (excess ice is added separately if needed). |
| `true` | 1 | Full TK state, geometry, and puddle restored. |
| `true` | (no `TKversion`) | Legacy restart: thermokarst initialized from `excess_fraction` and depth bounds above. |

You cannot toggle thermokarst mid-run by editing config; start a new stage from an
appropriate restart or change `enabled` only at process launch.

The daily order is: copy production C/N pools into the layer state; run one enthalpy
and phase-change solve; contract affected material layers; rebuild geometry, fronts,
roots, and drainage; run snow mass bookkeeping; route collapse water through soil
hydrology; then accumulate daily state into monthly arrays. This ordering makes the
monthly thickness weights use settled geometry without resetting accumulated fluxes.

Before scientific use, validate pond and drainage behavior against observations
and add pond thermal feedback. Use the current mechanism
for numerical and integration experiments rather than calibrated ecosystem
projections. The production dynamic-soil validation is documented in
[topology-map-validation-report.md](topology-map-validation-report.md).

## Additional build checks on this computer

The prototype compiles with `-Wall -Wextra -Wpedantic -Werror`.
UndefinedBehaviorSanitizer passed the numerical unit suite. Reproduce with:

```sh
sh tests/thermokarst/run_sanitizers.sh
```

AddressSanitizer could not be evaluated in this host environment: an independent
minimal sanitizer-runtime probe also exited with an illegal instruction before
printing its first message. On a supported host, enable it with
`SANITIZERS=address,undefined sh tests/thermokarst/run_sanitizers.sh`.

Production ecosystem execution is covered by the production, active-thaw,
seasonal-diagnostic, BGC/drainage, and active-topology validation suites. The
current consolidated results are in
[topology-map-validation-report.md](topology-map-validation-report.md).

The daily source-water tracer and seasonal restart validation are documented in
[seasonal-diagnostic-report.md](seasonal-diagnostic-report.md). Reproduce the
continuous, midpoint-restarted, and diagnostics-disabled control cases with:

```sh
make thermokarst-seasonal-diagnostics-validation
```
