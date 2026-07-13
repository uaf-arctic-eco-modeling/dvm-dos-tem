# Final model evaluation

Post-calibration validation after Step 2 completion criteria are satisfied ([`agent-instructions-step2.md`](../agent_calibration_step2/agent-instructions-step2.md)). Load this file into your coding agent session for the evaluation stage (see [agent README](../README.md#using-this-harness)). Path: `mads_calibration/agent/agent_final_evaluation/final-model-evaluation.md`.

Calibration SA runs use equilibrium-only spinup (`--sp-yrs 0 --tr-yrs 0`). A **full site simulation** exercises spinup and transient years so fluxes, soil thermal state, and active layer depth can be compared against observations.

Run inside `dvmdostem-autocal` (or `dvmdostem-dev`) with calibrated parameters in workflow `parameters-step2`.

## Prerequisites

- Step 2 complete per [`agent-instructions-step2.md`](../agent_calibration_step2/agent-instructions-step2.md) **Control flow**: N-level (`nlevel_pass`) and Krb (`krb_pass`) applied, last `analyze.py --phase main` exit `0`, and Nfall (`nfall_pass`) applied — or documented soft closure below
- Step 1 `cmax` and Step 2 params in `parameters-step2`; N-level/Krb/Nfall and Phase 6/7 documented in closure summary if run
- Site driver data; `--tr-yrs` ≤ historic climate length at site

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

## Validated acceptance (reference — soft closure, any site)

Use only when strict `analyze.py --phase main` exit `0` was documented
unreachable **and** the N-level, Krb, and Nfall phases (Control flow Stages
0/1/3) were each run to their own `*_pass` or documented exit `3`
(structural ceiling) — do not invoke soft closure as a substitute for
running those phases; it is a fallback for genuine residual misfits after
the full parameter set has been tried, not a shortcut around missing
phases. `accepted_limitations` must be recorded in the closure summary,
naming which target(s) remain off-tier and which phase (if any) hit exit
`3` for them:

- Final eval completes all TR years without crash
- N ratio (INGPP:GPP) within `--biome` band on final parameters, or documented as unreachable via Stage 0 (N-level) exit `3`
- AVLN within 20% tier on final parameters, or documented as unreachable via Stage 0 (N-level) exit `3`
- Transient NPP/GPP within ~10% of equilibrium target sums (indicative), or documented as unreachable via Stage 1 (Krb) exit `3`
- VEGN (VegStructuralNitrogen) within 10% tier on final parameters, or documented as unreachable via Stage 3 (Nfall) exit `3`
- Eq-stage soil pools (SHLWC, DEEPC, MINEC) within 20% tier on final parameters
- Phase 6 and Phase 7 completed when MINEC was sensitive to `rhmoistfrozen`

Set `status: complete` in closure summary when all `closure_criteria` are true. Loop back to Phase 7 (not skip) if soil pools regress after transient run. This section was originally IMN-specific reference language; it now applies to any site, since AVLN/N-ratio/NPP/VEGN misfits are addressed structurally (N-level/Krb/Nfall phases) before soft closure is considered, rather than being accepted as unreachable by default.

## Interpreting mismatches

| Symptom | Likely parameter focus | File | Notes |
|---------|------------------------|------|-------|
| GPP greatly underestimated | `cmax` | `cmt_calparbgc.txt` | Revisit **Step 1**; re-seed Step 2 if needed |
| AVLN off tier, or N ratio (INGPP:GPP) outside `--biome` band | `nmax`, `micbnup` | `cmt_calparbgc.txt`, `cmt_bgcsoil.txt` | Step 2 Stage 0 (N-level) — do not treat as an unfixable Step 1 issue before trying this |
| NPP off tier while GPP/N-ratio are on target | `krb(0/1/2)` | `cmt_calparbgc.txt` | Step 2 Stage 1 (Krb) |
| VEGN (VegStructuralNitrogen) off tier | `nfall(0/1/2)` | `cmt_calparbgc.txt` | Step 2 Stage 3 (Nfall) |
| RECO off, especially **winter RECO** | `rhmoistfrozen` | `cmt_bgcsoil.txt` | See Phase 6 |
| Mineral soil C (MINEC) off tier | `rhmoistfrozen`, soil `kdc*`, `micbnup` | `cmt_bgcsoil.txt`, `cmt_calparbgc.txt` | Phase 6 then Phase 7 |
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

- [ ] Step 2 completion criteria satisfied (see [`agent-instructions-step2.md`](agent-instructions-step2.md)): N-level (`nlevel_pass`), Krb (`krb_pass`), main (`pass`), and Nfall (`nfall_pass`) each applied — or exit `3` documented in closure summary for any that were structurally unreachable
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
| [`../agent_calibration_step1/README.md`](../agent_calibration_step1/README.md) | Step 1 `cmax` calibration |
| [`../agent_calibration_step2/README.md`](../agent_calibration_step2/README.md) | Step 2 integrated calibration |
| [`../agent_calibration_step2/agent-instructions-step2.md`](../agent_calibration_step2/agent-instructions-step2.md) | Step 2 agent workflow |
