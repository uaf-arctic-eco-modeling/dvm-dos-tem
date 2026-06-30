# Step 2 Integrated Calibration — Cursor Agent Instruction Set

Attach this file in Cursor (`@agent-instructions-step2.md`) when running Step 2 calibration.

Automate **Step 2** after Step 1: jointly calibrate soil and vegetation parameters with **N limitation ON** (`calib_mode: VEGC`) inside `dvmdostem-autocal`.

**Prerequisite:** Step 1 `recommended_cmax` — see [`step1-transition.md`](step1-transition.md). Interactive reference: [`notebooks/calibration_process.ipynb`](../notebooks/calibration_process.ipynb) (uses `sa-step2-example-imn.yaml`, not agent `logs/` paths).

## Minimum user action

```yaml
cmtnum: 4
site: /data/input-catalog/Imnavait
PXx: 0
PXy: 0
site_label: IMN
step1_result: /data/workflows/CMT04-IMN-sa-recovery-C/step1-result.yaml
nitrogen_biome: tundra   # analyze.py --biome (boreal | tundra)
```

## Checklist

- [ ] `parameters-step2` via `seed_setup.py` (adds burial rows if missing); smoke SA (N=5) on new sites
- [ ] Main iteration SA + `analyze.py --phase main` until exit `0` or branch (see Control flow)
- [ ] Rhmoist / soil branches when MINEC off-tier; snapshot before phase applies
- [ ] `param_update.py --phase main` **only** when main analyze exits `0` (`status: pass`)
- [ ] Final `analyze.py --phase main` exit `0` → [`final-model-evaluation.md`](../agent_final_evaluation/final-model-evaluation.md)

All commands: `docker compose exec -T dvmdostem-autocal bash -c 'cd /work && ...'`

---

## Glossary

| Term | Meaning |
|------|---------|
| **Stage** | Section in this doc (Seed, Main SA, Rhmoist branch, …) |
| **`analyze.py --phase`** | CLI gate scope: `main` (all targets+N+eq), `phase6` (MINEC), `phase7` (SHLWC+DEEPC+MINEC) |
| **`param_update.py --phase`** | Must match analyze phase and `status` in `step2-result.yaml` |

---

## Control flow

### Calibration loop

```
LOOP main iteration:
  run main SA → analyze.py --phase main --biome {nitrogen_biome}
  if any ft['column'].startswith('MINEC') for ft in failing_targets:
    cp -a parameters-step2 → parameters-step2-pre-phase6-{tag}
    LOOP rhmoist: SA → analyze --phase phase6
      on exit 0: param_update --phase phase6; break
    cp -a parameters-step2 → parameters-step2-pre-phase7-{tag}
    LOOP soil: SA → analyze --phase phase7
      on exit 0: param_update --phase phase7
      if MINEC regresses on next main analyze:
        restore pre-phase7 snapshot; re-apply phase6 from last phase6_pass; repeat soil loop
  if main exit 0: param_update.py --phase main   # required on pass; skip on exit 2/3
  elif main exit 2: propose_bounds.py → repeat main SA
  elif main exit 3: stop — reopen Step 1 or add parameters

DONE when last analyze.py --phase main exit 0
```

### Exit codes and apply (`analyze.py` + `param_update.py`)

| `analyze --phase` | exit `0` status | exit `2` | exit `3` | `param_update --phase` when exit `0` |
|-------------------|-----------------|----------|----------|--------------------------------------|
| `main` | `pass` | `target_fit_review` | `unreachable_review` (≥3 unreachable) | `main` — all `recommended_params` |
| `phase6` | `phase6_pass` | `target_fit_review` | — | `phase6` — `rhmoistfrozen` only |
| `phase7` | `phase7_pass` | `target_fit_review` | — | `phase7` — `micbnup`, `kdc*` only |

Exit `1` = `failed` (missing CSVs). Phase modes skip eq gate; eq checked on final `--phase main`. `--force` on param_update overrides status (documented approval only).

**Do not** `param_update --phase main` on `target_fit_review`. Phase applies require matching `phase` + status in the result yaml.

### Snapshot before phase apply

```bash
cp -a /data/workflows/CMT{NN}-{label}/parameters-step2 \
      /data/workflows/CMT{NN}-{label}/parameters-step2-pre-phase7-iter{N}
```

Restore on Phase 7 MINEC regression:

```bash
rm -rf .../parameters-step2
cp -a .../parameters-step2-pre-phase7-iter{N} .../parameters-step2
# then param_update --phase phase6 from last phase6_pass result if needed
```

### Immutable `parameters-step2`

- Created once by `seed_setup.py`; every SA uses the same `seed_path`
- Bounds from `sample_matrix.csv` / `propose_bounds.py` only — never main-apply mid-loop samples
- Phase 6/7 patch soil incrementally; main apply writes full `recommended_params` on pass
- `util.param.update_inplace` preserves all CMT blocks in multi-CMT files

### Acceptance (main `--phase main` only)

| Priority | Criterion | Gate |
|----------|-----------|------|
| 1 | N ratio | Hard — tundra 1.4–1.6, boreal 1.15–1.35 (`--biome`) |
| 2 | Per-target fit | Hard — NPP*/VEGC* ≤10%, soil pools ≤20% (`failing_targets` if not) |
| 3 | Equilibrium | Hard except chronic whitelist: DEEPC, MINEC, VEGC_pft4_Root, AVLN |
| 4 | Bounds | Iterate — `propose_bounds.py`, plots; bulk RMSE alone ≠ pass |

Sample selection: fewest per-target tier failures among N-passing samples, then worst excess — not RMSE alone.

### `step2-result.yaml` (key fields)

`phase`, `status`, `recommended_params`, `best_sample_index`, `selected_n_pass`, `selected_n_ratio`, `failing_targets`, `failing_eq_vars`, `misfit_classification` (`unreachable`, `extinct_pool`), `target_residuals`.

Per iteration: `logs/sa-{SITE}-step2-iter{N}.yaml`, unique `work_dir`, `step2-result.yaml` from `--json-out`.

---

## File reference

| Role | Path |
|------|------|
| Targets | `/work/calibration/calibration_targets.py` |
| Seed dir | `/data/workflows/CMT{NN}-{site_label}/parameters-step2` |
| SA | `/work/mads_calibration/SA_setup_and_run.py` |
| Scripts | `seed_setup.py`, `burial_params_setup.py`, `analyze.py`, `propose_bounds.py`, `param_update.py` (this folder) |
| Plots / checks | `/work/mads_calibration/SA_post_hoc_analysis.py` |
| Templates | `sa-step2-template.yaml`, `sa-step2-rhmoistfrozen-template.yaml`, `sa-step2-soil-retune-template.yaml` |
| Agent yamls | `mads_calibration/logs/sa-{site_label}-*.yaml` (gitignored) |

---

## Stage: Seed setup

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/seed_setup.py \
    --step1-result /data/workflows/CMT04-IMN-sa-recovery-C/step1-result.yaml \
    --cmtnum 4 --dest /data/workflows/CMT04-IMN/parameters-step2'
```

## Stage: Main SA

Validate CMT in `calibration_targets.py`. Params: 5 soil (`micbnup`, `kdc*`) + 3 `cfall` per active PFT from Step 1 `cmax_pft*`.

Copy [`sa-step2-template.yaml`](sa-step2-template.yaml) → `logs/sa-{site_label}-step2.yaml`. Required: `seed_path`, `calib_mode: VEGC`, `aux_outputs: [INGPP y, GPP y]`, `--eq-yrs 2000`, soil + `cfall`. First pass: `percent_diffs: 0.95`; later: `p_bounds` only.

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'cd /work && python mads_calibration/SA_setup_and_run.py --force \
    -f mads_calibration/logs/sa-IMN-step2-iter3.yaml'
```

## Stage: Analyze (main)

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/analyze.py \
    --phase main --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-iter3/ \
    --biome tundra --save-plots \
    --json-out /data/workflows/CMT04-IMN/logs/sa-step2-iter3/step2-result.yaml'
```

## Stage: Next iteration

1. Copy prior yaml → `iter{N}`; new `work_dir`
2. `propose_bounds.py --step1-result ...` → bounds fragment
3. Remove `percent_diffs`; add `p_bounds`; `--dry-run` then `--force` SA

## Stage: Main apply

On `analyze.py --phase main` exit `0` only — **always** apply:

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/param_update.py \
    --phase main \
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-iter3/step2-result.yaml \
    --param-dir /data/workflows/CMT04-IMN/parameters-step2 --cmtnum 4'
```

## Stage: Rhmoist branch (`--phase phase6`)

When `failing_targets` has a column starting with `MINEC`. Template: [`sa-step2-rhmoistfrozen-template.yaml`](sa-step2-rhmoistfrozen-template.yaml). `plot_relationships(..., variables=["rhmoistfrozen"])` — if insensitive, document and skip apply.

```bash
# after SA + snapshot:
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/analyze.py \
    --phase phase6 --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-rhmoistfrozen/ \
    --biome tundra \
    --json-out /data/workflows/CMT04-IMN/logs/sa-step2-rhmoistfrozen/step2-result.yaml'

docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/param_update.py \
    --phase phase6 \
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-rhmoistfrozen/step2-result.yaml \
    --param-dir /data/workflows/CMT04-IMN/parameters-step2 --cmtnum 4'
```

## Stage: Soil retune (`--phase phase7`)

Required after Phase 6 apply. Template: [`sa-step2-soil-retune-template.yaml`](sa-step2-soil-retune-template.yaml). Bounds: `propose_bounds.py --soil-span 0.20` from **last main-loop** `step2-result.yaml`. Snapshot before apply (Control flow).

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/analyze.py \
    --phase phase7 --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-soil-retune/ \
    --biome tundra \
    --json-out /data/workflows/CMT04-IMN/logs/sa-step2-soil-retune/step2-result.yaml'

docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/param_update.py \
    --phase phase7 \
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-soil-retune/step2-result.yaml \
    --param-dir /data/workflows/CMT04-IMN/parameters-step2 --cmtnum 4'
```

---

## Sensitivity diagnostics

After each SA, from [`SA_post_hoc_analysis.py`](../SA_post_hoc_analysis.py): `nitrogen_check`, `plot_relationships`, `plot_pft_matrix`, `plot_equilibrium_relationships` on `failing_targets` columns.

---

## Diagnosis (`step2-result.yaml` → action)

| Signal | Action |
|--------|--------|
| exit `2`, `failing_targets` | Iterate bounds (`propose_bounds.py`); branch rhmoist/soil if MINEC off-tier |
| `misfit_classification.unreachable` | Obs outside SA min–max — widen bounds or add params (`rhmoistfrozen`, `krb`, `nmax`) |
| ≥3 unreachable on main analyze | exit `3` — reopen Step 1; do not iterate bounds alone |
| `misfit_classification.extinct_pool` | Mod ≈ 0, obs large — document limitation; rarely fixable |
| Chronic eq fail on whitelist vars | Allowed on main pass (see Acceptance table) |

---

## Failure modes

| Symptom | Action |
|---------|--------|
| `analyze.py` exit `1` | Fix SA / missing CSVs |
| No N-passing samples | Rank full pool; note in result; iterate bounds |
| Phase 7 regresses MINEC | Restore snapshot; re-apply phase6; repeat phase7 |
| `p_bounds` length mismatch | `propose_bounds.py --step1-result` matching PFT count |
| TR crash in final eval | `--tr-yrs` ≤ historic climate length |
| `EcosystemRespiration` missing in CMT | Remove from `target_names` or add to `calibration_targets.py` |

---

## Do not

- Re-sample `cmax` or edit `/work/parameters` in the repo
- `param_update --phase main` unless main analyze exit `0` (`pass`)
- `param_update --phase phase6|phase7` without snapshot + matching phase pass
- Skip `aux_outputs` for INGPP/GPP; skip Phase 7 after Phase 6 apply without documented MINEC insensitivity
- Commit `logs/`

---

## Filename reference

| Incorrect | Correct |
|-----------|---------|
| `step2-integrated-agent.md` | `agent-instructions-step2.md` |
| `step1-to-step2-transition.md` | `step1-transition.md` |
| `step2_seed_setup.py` | `seed_setup.py`, `burial_params_setup.py`, `analyze.py`, `propose_bounds.py`, `param_update.py` |

Closure summary: [`step2-closure-summary-template.yaml`](../agent_final_evaluation/step2-closure-summary-template.yaml) → `logs/{site_label}-step2-closure-summary.yaml`.
