# Final model evaluation

Post-calibration validation after Step 2 completion criteria are satisfied ([`calibration_instructions.md`](../2_calibration/calibration_instructions.md)). Load this file into your coding agent session for the evaluation stage. Path: `mads_calibration/agent/3_evaluation/evaluation_instructions.md`.

Calibration SA runs use equilibrium-only spinup (`--sp-yrs 0 --tr-yrs 0`). A **full site simulation** exercises spinup and transient years so fluxes, soil thermal state, and active layer depth can be compared against observations.

Run inside `dvmdostem-autocal` (or `dvmdostem-dev`) with calibrated parameters in workflow `parameters-step2`.

Path conventions: [Multisite conventions](../0_setup/setup_instructions.md#multisite-conventions).

## Minimum user inputs

```yaml
cmtnum: {cmtnum}
site: {site}
site_label: {site_label}
workflow: /data/workflows/CMT{cmtnum:02d}-{site_label}
tr_yrs: {TR_YRS}   # transient years — must not exceed historic driver length
```

## Prerequisites

- Step 2 complete per [`calibration_instructions.md`](../2_calibration/calibration_instructions.md)
- Step 1 `cmax` and Step 2 params in `{workflow}/parameters-step2`
- `{TR_YRS}` determined from site driver (see below)

## Procedure

### 1. Create evaluation config

Copy [`sa-final-eval-template.yaml`](sa-final-eval-template.yaml) to `logs/sa-{site_label}-final-eval.yaml` and fill placeholders:

| Key | Value |
|-----|-------|
| `param_dir` | `/data/workflows/CMT{NN}-{site_label}/parameters-step2` |
| `work_dir` | `/data/workflows/CMT{NN}-{site_label}/final-eval` (unique) |
| `site`, `PXx`, `PXy`, `cmtnum` | Same as calibration |
| `opt_run_setup` | `--pr-yrs 100 --eq-yrs 2000 --sp-yrs 250 --tr-yrs {TR_YRS} --sc-yrs 0` |

### Determine `{TR_YRS}` (required for every site)

`--tr-yrs` must not exceed the historic climate record at `{site}`. Inspect the driver inside the container:

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python -c "import netCDF4 as nc; f=nc.Dataset(\"{site}/historic-climate.nc\"); \
print(\"years:\", len(f.dimensions[\"time\"]))"'
```

Use that count as `{TR_YRS}`. Exceeding driver length causes a vector bounds crash at end of transient.

Example: Imnavait historic climate spans 1901–2022 → `{TR_YRS}=122`.

### 2. Setup working directory

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/scripts/util/setup_working_directory.py \
    /data/workflows/CMT{cmtnum:02d}-{site_label}/final-eval \
    --force --input-data-path {site} \
    --seed-parameters /data/workflows/CMT{cmtnum:02d}-{site_label}/parameters-step2 \
    --no-cal-targets'
```

### 3. Enable outputs

Edit `$work_dir/config/output_spec.csv` and enable at minimum:

- `GPP` (yearly transient)
- `INGPP` (yearly transient)
- `NPP` (yearly transient)
- `RECO` or ecosystem respiration outputs
- `ALD` if comparing active layer depth
- Soil temperature layers if comparing thermal profile

Without enabling outputs, transient comparison is limited.

### 4. Run full site simulation

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'cd /data/workflows/CMT{cmtnum:02d}-{site_label}/final-eval && \
   /work/dvmdostem --pr-yrs 100 --eq-yrs 2000 --sp-yrs 250 --tr-yrs {TR_YRS} --sc-yrs 0 \
   -l info --force-cmt {cmtnum} --ctrl-file config/config.js \
   2>&1 | tee /data/workflows/CMT{cmtnum:02d}-{site_label}/logs/final-eval-run.log'
```

Verify:

- No `output/fail_log.txt`
- Transient stage completes all `{TR_YRS}` years

Calibration SA used:

```text
--pr-yrs 100 --eq-yrs 2000 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0
```

The evaluation run **adds** `--sp-yrs 250 --tr-yrs {TR_YRS}`.

### 5. Compare model vs observations

Compare full-run outputs to site observations. Use plots and summary statistics (annual means, seasonal cycles) rather than a single global tolerance.

| Variable | Typical outputs | Notes |
|----------|-----------------|-------|
| GPP | `GPP` (daily/monthly/yearly, transient) | Gross primary productivity |
| RECO | `RECO`, ecosystem respiration | Include **winter** RECO when diagnosing soil respiration |
| NPP | `NPP` | Net primary productivity |
| Soil temperature | Soil layer temperatures | Profile and/or depth-integrated vs measurements |
| Active layer depth (ALD) | `ALD` | Seasonal maximum and interannual variability |

Useful tooling:

- [`calibration/calibration_targets.py`](../../calibration/calibration_targets.py) — equilibrium stock/flux targets used in SA
- [`calibration/calibration-viewer.py`](../../calibration/calibration-viewer.py) — interactive comparison with target lines
- [`scripts/simulation_comparison_report.py`](../../scripts/simulation_comparison_report.py) — batch comparison reports including ALD

Interactive exploration: [`notebooks/calibration_process.ipynb`](../notebooks/calibration_process.ipynb).

### 6. Write closure summary

Copy [`step2-closure-summary-template.yaml`](step2-closure-summary-template.yaml) to `logs/{site_label}-step2-closure-summary.yaml`. Fill transient flux means, stock comparisons, accepted limitations, and set `closure_criteria` booleans.

Archive final parameters:

```bash
cp -a /data/workflows/CMT{cmtnum:02d}-{site_label}/parameters-step2 \
      /data/workflows/CMT{cmtnum:02d}-{site_label}/parameters-step2-final
```

## Validated acceptance (reference — soft closure, any site)

Use only when both calibration phases (vegetation exploration → soil exploration)
were run to `*_pass` or documented exit `3` — not as a shortcut around missing
phases. Record `accepted_limitations` (target + phase that hit exit `3`):

- Final eval completes all TR years without crash
- AVLN within 20% tier on final parameters, or documented as unreachable via vegetation exploration exit `3`
- N ratio (INGPP:GPP) within `--biome` band on final parameters, or documented as unreachable — **diagnostic of N-limitation intensity**, not proof of GPP field-target fit (see Step 2 design intent)
- Transient NPP within ~10% of equilibrium target sums (indicative), or documented as unreachable via vegetation exploration exit `3`
- Transient GPP compared to available observations when present; do not equate N-ratio pass with GPP calibration
- VEGN (VegStructuralNitrogen) within 10% tier on final parameters, or documented as unreachable via vegetation exploration exit `3`
- Eq-stage soil pools (SHLWC, DEEPC, MINEC) within 20% tier on final parameters
- Phase 6 and Phase 7 completed when MINEC was sensitive to `rhmoistfrozen`

Set `status: complete` in closure summary when all `closure_criteria` are true. Loop back to Phase 7 (not skip) if soil pools regress after transient run. Soft closure is a fallback after the full two-phase calibration has been tried — not a shortcut around missing vegetation or soil exploration phases or around exit `3` HALTs.

## Interpreting mismatches

| Symptom | Likely parameter focus | File | Notes |
|---------|------------------------|------|-------|
| GPP greatly underestimated | `cmax` (Step 1) and/or `nmax`/`micbnup` | `cmt_calparbgc.txt`, `cmt_bgcsoil.txt` | Step 1 reopen is **human-only**. Check AVLN + ratio first |
| AVLN off tier, or N ratio (INGPP:GPP) outside `--biome` band | `nmax` (veg), `micbnup` (soil) | `cmt_calparbgc.txt`, `cmt_bgcsoil.txt` | Veg exploration for `nmax`; soil exploration for `micbnup`. Ratio ≠ GPP fit |
| NPP off tier while N-ratio is on band | `krb(0/1/2)` | `cmt_calparbgc.txt` | Targeted krb SA within veg exploration — ratio can pass while NPP* is unreachable |
| VEGC off tier | `cfall(0/1/2)` | `cmt_calparbgc.txt` | Targeted cfall SA within veg exploration |
| VEGN (VegStructuralNitrogen) off tier | `nfall(0/1/2)` | `cmt_calparbgc.txt` | Targeted nfall SA within veg exploration |
| RECO off, especially **winter RECO** | `rhmoistfrozen` | `cmt_bgcsoil.txt` | phase6 (last resort in soil phase) |
| Mineral / layer soil C off tier | soil `kdc*` (± `rhmoistfrozen`) | `cmt_bgcsoil.txt` | Soil exploration or targeted kdc* SA; phase6 then phase7 if needed |
| Soil temperature bias | `nfactor(s)`, `nfactor(w)` | `cmt_envground.txt` | Separate thermal SA |
| ALD too shallow/deep | `nfactor(s)`, `nfactor(w)`, snow/ground params | `cmt_envground.txt` | Thermal SA before BGC retune |

### Thermal parameter sensitivity (`nfactor`)

If soil temperature or ALD are off-target, run dedicated SA on `nfactor(s)` and `nfactor(w)` in **`cmt_envground.txt`**. Independent of main Step 2 soil/veg params unless deliberately coupled.

### When to loop back into calibration

| Severity | Action |
|----------|--------|
| Minor seasonal bias | Document; may be acceptable |
| Moderate flux offset | Targeted SA on parameter row above |
| Large GPP/RECO mismatch | Re-open Step 1 (`cmax`) or Step 2 Phases 6–7 |
| SHLWC/DEEPC drift after Phase 6 | Phase 7 soil retune (required, not optional) |
| Thermal / ALD failure | `nfactor` SA first |

After re-calibration, repeat SA checks, apply updated parameters, and **re-run this evaluation**.

## Checklist

- [ ] Step 2 completion criteria satisfied (see [`calibration_instructions.md`](../2_calibration/calibration_instructions.md)): applied `veg_pass` → `soil_pass` (and phase6/7 if used) — or exit `3` documented in closure summary for any structurally unreachable phase
- [ ] `sa-{site_label}-final-eval.yaml` in `logs/` from template
- [ ] `setup_working_directory.py` run; outputs enabled in `output_spec.csv`
- [ ] Full run: `--pr-yrs 100 --eq-yrs 2000 --sp-yrs 250 --tr-yrs {TR_YRS}` matching site climate length
- [ ] No `fail_log.txt`; all TR years complete
- [ ] GPP, RECO (incl. winter), NPP compared to observations
- [ ] Soil temperature and ALD compared if data available
- [ ] Closure summary written to `logs/{site_label}-step2-closure-summary.yaml`
- [ ] Parameters archived to `parameters-step2-final`

## Related docs

| Doc | Purpose |
|-----|---------|
| [`../1_cmax/cmax_instructions.md`](../1_cmax/cmax_instructions.md) | Step 1 `cmax` calibration |
| [`../2_calibration/calibration_instructions.md`](../2_calibration/calibration_instructions.md) | Step 2 staged calibration |
| [`../0_setup/setup_instructions.md`](../0_setup/setup_instructions.md) | Harness entry point (Phase 0) |
