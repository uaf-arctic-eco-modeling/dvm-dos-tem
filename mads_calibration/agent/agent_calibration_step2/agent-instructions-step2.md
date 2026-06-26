# Step 2 Integrated Calibration — Cursor Agent Instruction Set

Attach this file in Cursor (`@agent-instructions-step2.md`) when running Step 2 calibration.

Automate **Step 2** after Step 1 is complete: jointly calibrate soil and vegetation parameters against integrated C/N targets with **N limitation ON** (`calib_mode: VEGC`). Run entirely inside the `dvmdostem-autocal` Docker container.

**Prerequisite:** Step 1 result with `recommended_cmax` — see [`step1-transition.md`](step1-transition.md). Folder overview: [`README.md`](README.md).

Reference notebook (interactive): [`notebooks/calibration_process.ipynb`](../notebooks/calibration_process.ipynb) — uses [`sa-step2-example-imn.yaml`](sa-step2-example-imn.yaml), not agent `logs/` paths.

## Directory layout

| Location | Tracked | Agent use |
|----------|---------|-----------|
| `agent/agent_calibration_step2/` (this folder) | Yes | Templates, example yaml, scripts |
| `logs/` | **No** (gitignored) | SA yamls, closure notes, optional archives |
| `/data/workflows/` | Runtime volume | SA outputs; `step2-result.yaml` from `--json-out` |

Copy [`sa-step2-template.yaml`](sa-step2-template.yaml) or adapt [`sa-step2-example-imn.yaml`](sa-step2-example-imn.yaml) into `logs/` for each new site. Do not commit `logs/`.

## Minimum user action

```yaml
cmtnum: 4
site: /data/input-catalog/Imnavait
PXx: 0
PXy: 0
site_label: IMN
step1_result: /data/workflows/CMT04-IMN-sa-recovery-C/step1-result.yaml
nitrogen_biome: tundra   # maps to analyze.py --biome (boreal | tundra)
```

## Checklist

- [ ] Step 1 complete (`recommended_cmax` in result yaml)
- [ ] `parameters-step2` written via `seed_setup.py`
- [ ] Smoke SA (N=5) completes (new sites only)
- [ ] Production / iteration SA completes
- [ ] Sensitivity diagnostics reviewed (`plot_pft_matrix`, `plot_relationships`)
- [ ] `analyze.py --biome {nitrogen_biome}` with `--save-plots`
- [ ] Review spaghetti/boxplot; confirm selected sample N-pass before apply
- [ ] Iterative `p_bounds` refinement via `propose_bounds.py`
- [ ] `param_update.py` when apply policy satisfied (see below)
- [ ] `rhmoistfrozen` SA if MINEC off-target (Phase 6)
- [ ] Post-`rhmoistfrozen` soil retune only if justified (Phase 7 — optional)
- [ ] Final completion criteria met
- [ ] Attach [`final-model-evaluation.md`](../agent_final_evaluation/final-model-evaluation.md) for full site validation and closure summary

---

## Prerequisites

Before starting, confirm:

- Docker Compose is running and `dvmdostem-autocal` container is up.
- Image built: `dvmdostem-autocal:${V_TAG}` (see root [`docker-compose.yml`](../../docker-compose.yml)).
- `/work` is mounted to the repo; `/data/workflows` is mounted for SA outputs.
- Driving inputs exist at the requested `site` path under `/data/input-catalog/`.
- Step 1 `step1-result.yaml` available with `recommended_cmax`.
- Python dependencies are pre-installed in the container — **do not** `pip install`.

All commands below use:

```bash
docker compose exec -T dvmdostem-autocal bash -c 'cd /work && ...'
```

---

## File reference

| Role | Path | Purpose |
|------|------|---------|
| Field observation targets | `/work/calibration/calibration_targets.py` | C/N targets per CMT |
| Step 1 result | `{work_dir}/step1-result.yaml` | Fixed `recommended_cmax` |
| Step 2 seed directory | `/data/workflows/CMT{NN}-{site_label}/parameters-step2` | SA `seed_path`; repo params not modified |
| SA entry point | `/work/mads_calibration/SA_setup_and_run.py` | Setup and run sensitivity analysis |
| Post-hoc analysis module | `/work/mads_calibration/SA_post_hoc_analysis.py` | Equilibrium, nitrogen, plots, ranking |
| Seed setup | `/work/mads_calibration/agent/agent_calibration_step2/seed_setup.py` | Copy params + fix Step 1 `cmax` |
| Headless analysis CLI | `/work/mads_calibration/agent/agent_calibration_step2/analyze.py` | Target-first analysis; writes `step2-result.yaml` |
| Bound proposal | `/work/mads_calibration/agent/agent_calibration_step2/propose_bounds.py` | Hybrid `p_bounds` for next iteration |
| Parameter apply | `/work/mads_calibration/agent/agent_calibration_step2/param_update.py` | Apply `recommended_params` after review |
| Main SA template | [`sa-step2-template.yaml`](sa-step2-template.yaml) | Copy into `logs/sa-{site_label}-step2.yaml` |
| Filled example | [`sa-step2-example-imn.yaml`](sa-step2-example-imn.yaml) | CMT04 Imnavait 32-param layout reference |
| rhmoistfrozen template | [`sa-step2-rhmoistfrozen-template.yaml`](sa-step2-rhmoistfrozen-template.yaml) | Phase 6 |
| soil retune template | [`sa-step2-soil-retune-template.yaml`](sa-step2-soil-retune-template.yaml) | Phase 7 (optional) |
| Agent SA configs | `/work/mads_calibration/logs/sa-{site_label}-*.yaml` | Gitignored; created from templates |

---

## Acceptance hierarchy

| Priority | Criterion | Gate | Notes |
|----------|-----------|------|-------|
| 1 | **Selected sample N ratio** | **Hard** for `pass` / apply | `--biome boreal\|tundra`; boreal ~1.15–1.35, tundra ~1.4–1.6 |
| 2 | **Target fit (RMSE / plots)** | Primary rank | Rank by R²/RMSE; review spaghetti + residuals before apply |
| 3 | **Equilibrium on most vars** | Soft / diagnostic | Report pass rates; whitelist chronic failures; never require full pass |
| 4 | **Sensitivity** | Manual | `plot_relationships` / `plot_pft_matrix` when refining bounds |

Majority N-pass or majority eq-pass across all samples is **not** required.

## Iteration strategy

**Wide pass — Feasible region:** SA with `percent_diffs: 0.95` (N=100–200). Goal: acceptable bulk target fit; document chronic eq failures.

**Refinement pass — Target tuning:** re-anchor `p_bounds` on best low-RMSE sample (`propose_bounds.py`); widen only params correlated with plot outliers.

Per iteration artifacts:

- One yaml: `logs/sa-{SITE}-step2-iter{N}.yaml`
- Optional bounds fragment: `sa-{SITE}-step2-iter{N}-bounds.yaml`
- Runtime: `/data/workflows/.../sa-step2-iter{N}/` with `step2-result.yaml` from `--json-out`

## Misfit categories (from `step2-result.yaml`)

| Category | Fixable? | Action |
|----------|----------|--------|
| **A — Eq-only** | Accept | Whitelist chronic vars; optional `--pft4-root-cv-lim` / `--deepc-slope-lim` in reports |
| **B — Reachable** | Yes | Anchor `p_bounds` on best sample; widen correlated param |
| **C — Unreachable** | Partial | Widen bounds or add params (`krb`, `nmax`, `rhmoistfrozen` for MINEC) |
| **D — Extinct pool** | Often no | One target-anchored retry; else document limitation |

---

## Phase 1 — Seed setup

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/seed_setup.py \
    --step1-result /data/workflows/CMT04-IMN-sa-recovery-C/step1-result.yaml \
    --cmtnum 4 \
    --dest /data/workflows/CMT04-IMN/parameters-step2'
```

## Phase 2 — SA yaml and run

### 2.1 Validate CMT and discover active PFTs

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python -c "
import sys; sys.path.insert(0, \"/work/calibration\")
import calibration_targets as ct
cmtnum = 4  # replace with input
found = [k for k,v in ct.calibration_targets.items()
         if isinstance(v,dict) and v.get(\"cmtnumber\")==cmtnum]
assert found, f\"CMT {cmtnum} not in calibration_targets.py\"
print(\"CMT entry:\", found[0])
"'
```

Build Step 2 param lists:

- **5 soil params** with `pftnums: null`: `micbnup`, `kdcrawc`, `kdcsoma`, `kdcsompr`, `kdcsomcr`
- **3 `cfall` compartments per active PFT**: `cfall(0)`, `cfall(1)`, `cfall(2)`

**Authoritative active PFT list:** indices from Step 1 `recommended_cmax` keys (`cmax_pft0` … `cmax_pftN`). Cross-check `parameters/cmt_bgcvegetation.txt` for the CMT block.

Copy [`sa-step2-template.yaml`](sa-step2-template.yaml) or [`sa-step2-example-imn.yaml`](sa-step2-example-imn.yaml) to `logs/sa-{site_label}-step2.yaml` (smoke N=5 for new sites).

Required keys: `seed_path`, `calib_mode: VEGC`, `aux_outputs: [INGPP y, GPP y]`, `opt_run_setup: --pr-yrs 100 --eq-yrs 2000 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0`, soil + `cfall` params. First wide pass: `percent_diffs: 0.95`; later iterations: `p_bounds` only (mutually exclusive with `percent_diffs`).

When calling `propose_bounds.py`, pass `--step1-result` so `--pft-max` matches your yaml active PFT count.

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'cd /work && python mads_calibration/SA_setup_and_run.py --dry-run \
    -f mads_calibration/logs/sa-IMN-step2.yaml'

docker compose exec -T dvmdostem-autocal bash -c \
  'cd /work && python mads_calibration/SA_setup_and_run.py --force \
    -f mads_calibration/logs/sa-IMN-step2-iter3.yaml'
```

## Phase 3 — Analysis

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/analyze.py \
    --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-iter3/ \
    --biome tundra \
    --save-plots \
    --json-out /data/workflows/CMT04-IMN/logs/sa-step2-iter3/step2-result.yaml'
```

Use `--biome` matching input `nitrogen_biome`. Headless plots (`--save-plots`): spaghetti and boxplot.

### Analysis status contract

| `status` | Meaning | exit |
|----------|---------|------|
| `pass` | Selected sample N-pass + no extinct_pool misfits | 0 |
| `target_fit_review` | Params populated; N fail and/or plot outliers need review | 2 |
| `failed` | Missing CSVs / empty results | 1 |

`recommended_params` is populated from the selected sample when SA completed successfully.

## Sensitivity diagnostics

All diagnostic functions live in [`SA_post_hoc_analysis.py`](../SA_post_hoc_analysis.py). Run after each SA before proposing the next `p_bounds`.

| Function | Use |
|----------|-----|
| `plot_pft_matrix` | PFT / `cfall` sensitivity to veg and soil targets |
| `plot_relationships` | Soil param ↔ target slopes |
| `plot_equilibrium_relationships` | Time-series eq trends for key vars |
| `equilibrium_check` | Quantitative eq pass rates (soft gate) |
| `nitrogen_check` | INGPP:GPP ratio on selected sample (hard gate) |

**Bound refinement:** switch from `percent_diffs` to explicit `p_bounds` once a feasible region is found (`propose_bounds.py` or manual). Widen only params correlated with plot outliers.

## Phase 4 — Build next iteration yaml

1. Copy prior `logs/sa-{site_label}-step2-iter{N-1}.yaml` → `logs/sa-{site_label}-step2-iter{N}.yaml`
2. Set a **new unique** `work_dir`
3. Generate bounds:

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/propose_bounds.py \
    --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-iter2/ \
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-iter2/step2-result.yaml \
    --step1-result /data/workflows/CMT04-IMN-sa-recovery-C/step1-result.yaml \
    --soil-samples 6,16 --veg-span 0.30 \
    --yaml-out mads_calibration/logs/sa-IMN-step2-iter3-bounds.yaml'
```

4. **Remove** `percent_diffs` from the iteration yaml
5. **Add** `p_bounds:` list from the bounds fragment (same length as `params`)
6. Keep `params`, `pftnums`, `target_names`, `aux_outputs` unchanged
7. `--dry-run` then `--force` SA

## Phase 5 — Apply parameters

### Apply policy

| Condition | Action |
|-----------|--------|
| `analyze.py` exit `0` (`pass`) | Apply via `param_update.py` |
| exit `2` (`target_fit_review`) | **Do not apply** unless human approves; document `selected_n_ratio`, misfits, and limitations in `logs/{site_label}-step2-closure-notes.md` |
| exit `1` (`failed`) | Fix SA or inputs; do not apply |

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/param_update.py \
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-iter3/step2-result.yaml \
    --param-dir /data/workflows/CMT04-IMN/parameters-step2 \
    --cmtnum 4'
```

## Phase 6 — `rhmoistfrozen` tuning (MINEC)

Run after Phase 5. Parameter **`rhmoistfrozen`** lives in **`cmt_bgcsoil.txt`**.

Copy [`sa-step2-rhmoistfrozen-template.yaml`](sa-step2-rhmoistfrozen-template.yaml) to `logs/sa-{site_label}-step2-rhmoistfrozen.yaml`.

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'cd /work && python mads_calibration/SA_setup_and_run.py \
    -f mads_calibration/logs/sa-IMN-step2-rhmoistfrozen.yaml'
```

After the run, analyze before apply:

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/analyze.py \
    --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-rhmoistfrozen/ \
    --biome tundra \
    --json-out /data/workflows/CMT04-IMN/logs/sa-step2-rhmoistfrozen/step2-result.yaml'
```

1. `plot_relationships(..., variables=[\"rhmoistfrozen\"])` — if MINEC is insensitive, document and skip.
2. If sensitive and apply policy satisfied, apply via `param_update.py`.
3. Iterate Phase 6 until MINEC is acceptable or documented as insensitive.

## Phase 7 — Post-`rhmoistfrozen` soil retune (optional)

**Default: skip.** IMN Phase 7 caused DEEPC regression and was reverted.

If SHLWC/DEEPC drift after Phase 6, copy [`sa-step2-soil-retune-template.yaml`](sa-step2-soil-retune-template.yaml) to `logs/`, set tight `p_bounds` (±20% around current best soil params), run SA + `analyze.py`, apply only if plots improve without regressing other targets.

## Final completion criteria

| Criterion | Gate | Notes |
|-----------|------|-------|
| **Target fit** | Soft | Acceptable bulk fit via RMSE, spaghetti, `target_residuals` |
| **Equilibrium** | Soft | Review via `equilibrium_check`; whitelist chronic failures |
| **Nitrogen limitation** | **Hard** for `pass` | Selected sample must pass `nitrogen_check` band before unattended apply |

When calibration is complete, attach [`final-model-evaluation.md`](../agent_final_evaluation/final-model-evaluation.md) and write closure summary from [`step2-closure-summary-template.yaml`](../agent_final_evaluation/step2-closure-summary-template.yaml) to `logs/{site_label}-step2-closure-summary.yaml`.

---

## Output contract (`step2-result.yaml`)

`status`: `pass` | `target_fit_review` | `failed`

**Exit codes (`analyze.py`):** `0` pass, `2` target_fit_review, `1` failed.

Key fields: `recommended_params`, `best_sample_index`, `selected_n_pass`, `selected_n_ratio`, `target_residuals`, `misfit_classification`, `chronic_eq_failures`.

---

## Decision rules

1. Rank by target R²/RMSE; prefer samples passing `nitrogen_check` when any exist in the pool.
2. Equilibrium is diagnostic only — do not require full eq-pass before ranking.
3. Never re-sample `cmax` in Step 2; it is fixed in `parameters-step2`.
4. Use `propose_bounds.py --step1-result` so bound list length matches yaml PFT layout.
5. Do not modify `/work/parameters` in the repo — all writes go to `/data/workflows/`.
6. On `target_fit_review`, iterate bounds or seek human approval before apply.

---

## Failure modes

| Symptom | Action |
|---------|--------|
| CMT not in `calibration_targets.py` | Stop; report missing CMT. |
| `analyze.py` exit `1` / missing CSVs | SA did not complete; check container logs and `work_dir`. |
| Zero samples / empty `results.csv` | Re-run SA; verify yaml and `seed_path`. |
| No nitrogen-passing samples in pool | Continue ranking from full pool; note in `step2-result.yaml`; iterate bounds. |
| SA sample folder errors | Inspect `sample_NNNNNNNNN/` logs; report failing indices. |
| Phase 7 regressions DEEPC/MINEC | Revert to prior anchor (re-apply iter params + Phase 6); skip Phase 7. |
| Final eval TR crash (`vector::_M_range_check`) | Reduce `--tr-yrs` to historic climate length at site. |
| `p_bounds` length mismatch | Regenerate with `propose_bounds.py --step1-result` matching yaml PFT count. |

---

## Do not

- Re-sample `cmax` in Step 2
- Modify `/work/parameters` in the repo
- Use `GPPAllIgnoringNitrogen` for Step 2
- Skip `aux_outputs` for INGPP/GPP
- Call `nitrogen_check` without site-appropriate `--biome`
- Apply parameters on `target_fit_review` without human approval
- Commit `logs/` (gitignored)

---

## Filename reference

| Draft / incorrect name | Correct path |
|------------------------|--------------|
| `step2-integrated-agent.md` | `agent-instructions-step2.md` |
| `step1-to-step2-transition.md` | `step1-transition.md` |
| `step2_seed_setup.py` etc. | `seed_setup.py`, `analyze.py`, `propose_bounds.py`, `param_update.py` |
| Notebook Step 2 example | `sa-step2-example-imn.yaml` |
