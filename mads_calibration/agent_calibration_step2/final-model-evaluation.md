# Final model evaluation

Post-calibration validation after Step 2 completion criteria are satisfied ([`agent-instructions-step2.md`](agent-instructions-step2.md)). Attach this file in Cursor (`@final-model-evaluation.md`) for the evaluation stage.

Calibration SA runs use equilibrium-only spinup (`--sp-yrs 0 --tr-yrs 0`). A **full site simulation** exercises spinup and transient years so fluxes, soil thermal state, and active layer depth can be compared against observations.

Run inside `dvmdostem-autocal` (or `dvmdostem-dev`) with calibrated parameters in workflow `parameters-step2`.

## Prerequisites

- Step 1 `cmax` and Step 2 soil/veg params applied to workflow parameter files
- Optional Phase 6 `rhmoistfrozen` complete if used; Phase 7 only if kept (often skipped)
- Site driver data available for the evaluation period
- `--tr-yrs` set to **historic climate length at site** (must not exceed driver NetCDF span)

## Procedure

### 1. Create evaluation config

Copy [`sa-final-eval-template.yaml`](sa-final-eval-template.yaml) to `logs/sa-{site_label}-final-eval.yaml` and fill placeholders:

| Key | Value |
|-----|-------|
| `param_dir` | `/data/workflows/CMT{NN}-{site_label}/parameters-step2` |
| `work_dir` | `/data/workflows/CMT{NN}-{site_label}/final-eval` (unique) |
| `site`, `PXx`, `PXy`, `cmtnum` | Same as calibration |
| `opt_run_setup` | `--pr-yrs 100 --eq-yrs 2000 --sp-yrs 250 --tr-yrs {TR_YRS} --sc-yrs 0` |

**Site constraint (CMT04 Imnavait):** historic climate at `/data/input-catalog/Imnavait/historic-climate.nc` spans **1901–2022 (122 years)**. Use `--tr-yrs 122`. Exceeding driver length causes a vector bounds crash at end of transient.

Inspect your site driver or site documentation to set `{TR_YRS}` for other locations.

### 2. Setup working directory

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/scripts/util/setup_working_directory.py \
    /data/workflows/CMT04-IMN/final-eval \
    --force --input-data-path /data/input-catalog/Imnavait \
    --seed-parameters /data/workflows/CMT04-IMN/parameters-step2 \
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

Without enabling outputs, transient comparison is limited (IMN v1 only wrote `GPP_yearly_tr.nc`).

### 4. Run full site simulation

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'cd /data/workflows/CMT04-IMN/final-eval && \
   /work/dvmdostem --pr-yrs 100 --eq-yrs 2000 --sp-yrs 250 --tr-yrs 122 --sc-yrs 0 \
   -l info --force-cmt 4 --ctrl-file config/config.js \
   2>&1 | tee /data/workflows/CMT04-IMN/logs/final-eval-run.log'
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
cp -a /data/workflows/CMT04-IMN/parameters-step2 \
      /data/workflows/CMT04-IMN/parameters-step2-final
```

## IMN-validated acceptance (reference)

Acceptable to skip further calibration retune when:

- Final eval completes all TR years without crash
- Transient NPP/GPP within ~10% of equilibrium target sums (indicative)
- Soil stock gaps (SHLWC/DEEPC/MINEC) documented as tradeoffs
- Phase 7 reverted if it regresses DEEPC

Set `status: complete` in closure summary when all `closure_criteria` are true.

## Interpreting mismatches

| Symptom | Likely parameter focus | File | Notes |
|---------|------------------------|------|-------|
| GPP greatly underestimated | `cmax` | `cmt_calparbgc.txt` | Revisit **Step 1**; re-seed Step 2 if needed |
| RECO off, especially **winter RECO** | `rhmoistfrozen` | `cmt_bgcsoil.txt` | See Phase 6 |
| Mineral soil C (MINEC) tradeoff | `rhmoistfrozen`, soil `kdc*`, `micbnup` | `cmt_bgcsoil.txt`, `cmt_calparbgc.txt` | Document tradeoff |
| Soil temperature bias | `nfactor(s)`, `nfactor(w)` | `cmt_envground.txt` | Separate thermal SA |
| ALD too shallow/deep | `nfactor(s)`, `nfactor(w)`, snow/ground params | `cmt_envground.txt` | Thermal SA before BGC retune |

### Thermal parameter sensitivity (`nfactor`)

If soil temperature or ALD are off-target, run dedicated SA on `nfactor(s)` and `nfactor(w)` in **`cmt_envground.txt`**. Independent of main Step 2 soil/veg params unless deliberately coupled.

### When to loop back into calibration

| Severity | Action |
|----------|--------|
| Minor seasonal bias | Document; may be acceptable |
| Moderate flux offset | Targeted SA on parameter row above |
| Large GPP/RECO mismatch | Re-open Step 1 (`cmax`) or Step 2 (`rhmoistfrozen`, soil `kdc*`) |
| Thermal / ALD failure | `nfactor` SA first |

After re-calibration, repeat SA checks, apply updated parameters, and **re-run this evaluation**.

## Checklist

- [ ] Step 2 completion criteria satisfied (see [`agent-instructions-step2.md`](agent-instructions-step2.md))
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
| [`../agent_calibration/README.md`](../agent_calibration/README.md) | Step 1 `cmax` calibration |
| [`README.md`](README.md) | Step 2 integrated calibration |
| [`agent-instructions-step2.md`](agent-instructions-step2.md) | Step 2 agent workflow |
