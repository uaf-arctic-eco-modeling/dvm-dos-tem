# Step 1 Cmax Calibration — Cursor Agent Instruction Set

Attach this file in Cursor (`@step1-cmax-agent.md`) when running the calibration agent.

**Prerequisite:** Complete Phase 0 setup via [`calibration_setup.md`](../agent_calibration_setup/calibration_setup.md) and obtain `logs/{site_label}-setup-manifest.yaml`.

Automate **Step 1** of the MADS calibration workflow: calibrate **`cmax` per active PFT** against **`GPPAllIgnoringNitrogen`** field targets (modeled as NetCDF **`INGPP`**). Run entirely inside the `dvmdostem-autocal` Docker container. Do **not** proceed to Step 2 from this instruction set.

**Step 2** continues in [`agent/agent_calibration_step2/`](../agent_calibration_step2/) — see [`step1-transition.md`](../agent_calibration_step2/step1-transition.md). Folder overview: [`README.md`](README.md).

Reference notebook (interactive post-hoc analysis): [`notebooks/calibration_process.ipynb`](../notebooks/calibration_process.ipynb) — uses [`sa-step1-example-imn.yaml`](sa-step1-example-imn.yaml), not agent `logs/` paths.

## Directory layout

| Location | Tracked | Agent use |
|----------|---------|-----------|
| `agent/agent_calibration_step1/` (this folder) | Yes | Templates and scripts |
| `logs/` | **No** (gitignored) | Created SA yamls (`sa-{site_label}-step1.yaml`, recovery A–D) and optional `{run_id}-step1-result.yaml` archive |
| `/data/workflows/` | Runtime volume | SA outputs; canonical `step1-result.yaml` from `--json-out` |

Copy [`sa-step1-template.yaml`](sa-step1-template.yaml) into `logs/` for each run. Do not commit `logs/`.

## Minimum user action

Provide these inputs (typically from the Phase 0 setup manifest), then run the agent against this instruction set:

```yaml
cmtnum: 4
site: /data/input-catalog/Imnavait
PXx: 0
PXy: 0
site_label: IMN
seed_path: /work/parameters              # from setup manifest
setup_manifest: mads_calibration/logs/IMN-setup-manifest.yaml
```

## Quick checklist

- [ ] Phase 0 complete: `logs/{site_label}-setup-manifest.yaml` exists with `status: pass` or `warn`
- [ ] `dvmdostem-autocal` running; `/data/input-catalog` and `/data/workflows` mounted
- [ ] Driving inputs exist at `site` (synced by Phase 0)
- [ ] CMT has `GPPAllIgnoringNitrogen` in `calibration/calibration_targets.py`
- [ ] Plausible `cmax` seeds at `seed_path` (from setup manifest)

---

## Role and Goal

You are a calibration agent. Given a CMT number, site path, and grid cell, you will:

1. Build and run a Step 1 sensitivity analysis (SA).
2. Perform post-hoc analysis (equilibrium filter, rank by R², compute RMSE).
3. If RMSE ≥ threshold, launch recovery-style perturbation runs (A–D).
4. Report the best `recommended_cmax` values and metrics in the output contract format below.

**Success criterion:** equilibrium-filtered best sample has **RMSE < 10** (aggregate across all INGPP PFT columns). If no run meets the threshold, report `status: best_effort` with the global best found.

---

## Prerequisites

Before starting, confirm:

- **Phase 0 setup complete** — see [`calibration_setup.md`](../agent_calibration_setup/calibration_setup.md); `seed_path` and `site` come from `logs/{site_label}-setup-manifest.yaml`.
- Docker Compose is running and `dvmdostem-autocal` container is up.
- Image built: `dvmdostem-autocal:${V_TAG}` (see root [`docker-compose.yml`](../../docker-compose.yml)).
- `/work` is mounted to the repo; `/data/workflows` is mounted for SA outputs.
- Driving inputs exist at the requested `site` path under `/data/input-catalog/`.
- Python dependencies are pre-installed in the container — **do not** `pip install`.

---

## Inputs Schema

The human or orchestrator provides a YAML block at invocation:

```yaml
goal: "Calibrate cmax to match GPPAllIgnoringNitrogen with RMSE < 10"
cmtnum: 4
site: /data/input-catalog/Imnavait
PXx: 0
PXy: 0
site_label: IMN              # short token for work_dir / config naming
N_samples: 100               # use 5 with sa-demo-config for smoke tests
rmse_threshold: 10
max_perturbation_rounds: 1   # rounds of A-D recovery runs after baseline
percent_diffs: 0.25          # baseline SA perturbation fraction
recovery_percent_diffs: 0.40 # wider search for perturbation runs
```

---

## File Reference

| Role | Path | Purpose |
|------|------|---------|
| Field observation targets | `/work/calibration/calibration_targets.py` | GPP targets per CMT/PFT (`GPPAllIgnoringNitrogen`). Matched by `cmtnum`. |
| Initial cmax seeds | `/work/parameters/cmt_calparbgc.txt` | Starting center for Latin hypercube sampling via yaml `seed_path`. |
| Active PFT check | `/work/parameters/cmt_bgcvegetation.txt` | Which PFT slots are populated for the CMT. |
| SA entry point | `/work/mads_calibration/SA_setup_and_run.py` | Setup and run sensitivity analysis. |
| Post-hoc analysis | `/work/mads_calibration/SA_post_hoc_analysis.py` | Equilibrium check, metrics, ranking. |
| Headless analysis CLI | `/work/mads_calibration/agent/agent_calibration_step1/step1_analyze.py` | Preferred over inline Python for analysis phase. |
| Recovery seed setup | `/work/mads_calibration/agent/agent_calibration_step1/step1_recovery_setup.py` | Perturbed seed dirs for runs A–D. |
| Yaml template | `/work/mads_calibration/agent/agent_calibration_step1/sa-step1-template.yaml` | Parameterized Step 1 config template. |
| Recovery manifest template | `/work/mads_calibration/agent/agent_calibration_step1/recovery_cmax_optima.yaml` | Bias tiers and run definitions for perturbation loop. |
| Agent SA configs (per run) | `/work/mads_calibration/logs/sa-{site_label}-*.yaml` | Gitignored; created from template each calibration |
| Archived reference params | `/work/mads_calibration/calibration_files/originals/CMT{NN}-*/` | Historical per-site parameter snapshots. |

### Observations vs initial parameters

- **Observations (targets):** `calibration/calibration_targets.py` — find the entry whose `'cmtnumber'` equals `cmtnum` (e.g. CMT04 → `"shrub tundra"`).
- **Initial cmax guesses:** `parameters/cmt_calparbgc.txt` via `seed_path` — **not** derived from observations.

---

## Parameter Bounds: `(0, LIM]`

Default bounds are `initial ± (initial × percent_diffs)` and can go negative. Enforce positivity when needed:

- Use `p_bounds` in yaml (**mutually exclusive** with `percent_diffs`).
- Lower bound: ε > 0 (e.g. `0.1`) per PFT.
- Upper bound (LIM): cross-CMT max from `SA_post_hoc_analysis.get_max_parameter_ranges('cmax')`, or `min(seed × (1 + percent_diff), cross_cmt_max)`.
- Before writing perturbed seeds, verify all values stay in `(0, LIM]` (see `step1_recovery_setup.py`).

---

## Phase 1 — Baseline SA

### 1.1 Validate CMT and discover active PFTs

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python -c "
import sys; sys.path.insert(0, \"/work/calibration\")
import calibration_targets as ct
cmtnum = 4  # replace with input
found = [k for k,v in ct.calibration_targets.items()
         if isinstance(v,dict) and v.get(\"cmtnumber\")==cmtnum]
assert found, f\"CMT {cmtnum} not in calibration_targets.py\"
assert \"GPPAllIgnoringNitrogen\" in ct.calibration_targets[found[0]]
print(\"CMT entry:\", found[0])
"'
```

Inspect `parameters/cmt_bgcvegetation.txt` for the CMT block. Include PFTs 0–8 with non-zero vegetation; skip placeholder PFT9. Build equal-length `params`, `pftnums`, and `percent_diffs` lists.

### 1.2 Create Step 1 yaml

Copy [`sa-step1-template.yaml`](sa-step1-template.yaml) to `mads_calibration/logs/sa-{site_label}-step1.yaml` and fill placeholders:

| Key | Value |
|-----|-------|
| `cmtnum` | input cmtnum |
| `site`, `PXx`, `PXy` | input paths/coords |
| `seed_path` | from setup manifest (`parameters-seed/` or `/work/parameters`) |
| `observations` | `/work/calibration` |
| `work_dir` | `/data/workflows/CMT{cmtnum:02d}-{site_label}-sa-N{N_samples}` |
| `N_samples` | input |
| `params` / `pftnums` / `percent_diffs` | one `cmax` per active PFT |
| `calib_mode` | `GPPAllIgnoringNitrogen` (**required**) |
| `target_names` | `[GPPAllIgnoringNitrogen]` (**required**) |
| `opt_run_setup` | `--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0` |

### 1.3 Run SA

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'cd /work && python mads_calibration/SA_setup_and_run.py -f mads_calibration/logs/sa-{site_label}-step1.yaml'
```

- `-f` / `--force` clears existing `work_dir` before re-run.
- Long runs (N=100) may take hours; monitor for `work_dir/results.csv`.
- Demo smoke test: use [`sa-demo-config.yaml`](../sa-demo-config.yaml) (CMT06, N=5).

---

## Phase 2 — Post-hoc Analysis

Prefer the headless CLI (mirrors [`calibration_process.ipynb`](../notebooks/calibration_process.ipynb)):

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step1/step1_analyze.py \
    --work-dir /data/workflows/CMT04-IMN-sa-N100/ \
    --rmse-threshold 10 \
    --config-yaml mads_calibration/logs/sa-IMN-step1.yaml \
    --json-out /data/workflows/CMT04-IMN-sa-N100/step1-result.yaml'
```

Use the `work_dir` from your Step 1 yaml. Match `--config-yaml` to the `logs/` SA config you created.

**Important:** `n_top_runs` sorts ascending by R² — the **last** row is the best fit.

Equilibrium defaults (match notebook): `slope_lim=1e-3`, `eps_lim=1e-5`, `cv_lim=1`.

### Exit codes (`step1_analyze.py`)

The CLI sets both `status` in the output artifact **and** a process exit code. Treat them together when deciding the next phase:

| Exit code | `status` in artifact | Meaning | Agent action |
|-----------|----------------------|---------|--------------|
| `0` | `pass` | Best eq-filtered sample has RMSE < threshold | Step 1 complete — report `recommended_cmax`; **do not** run perturbation |
| `2` | `best_effort` | Eq-filtered samples exist but RMSE ≥ threshold | **Not a failure** — proceed to Phase 4 perturbation loop |
| `1` | `failed` | No samples passed equilibrium check | Stop or relax eq limits; do **not** proceed to perturbation |

Do **not** treat exit code `2` as a hard error. It is the normal signal to launch recovery runs A–D.

---

## Phase 3 — Acceptance Check

- **Pass (`status: pass`, exit `0`):** best equilibrium-filtered sample has `RMSE < rmse_threshold`.
- **Best effort (`status: best_effort`, exit `2`):** report global best even if threshold not met; proceed to Phase 4.
- **Failed (`status: failed`, exit `1`):** no equilibrium-passing samples; stop and report.

Extract `recommended_cmax` from the best sample's `cmax_*` columns in `sample_matrix.csv` (or from the artifact written by `--json-out`).

---

## Phase 4 — Perturbation Loop (when RMSE ≥ threshold)

Follow the recovery pattern in [`recovery_cmax_optima.yaml`](recovery_cmax_optima.yaml). Use that file for **`bias_tiers`** and **`runs`** only — its bundled `reference_optima` are CMT04 Imnavait **examples** and must **not** be used as seeds for a new calibration.

**Required:** pass `--reference-cmax-yaml` pointing to the baseline Step 1 artifact (`step1-result.yaml` from `--json-out` under the baseline `work_dir`). That file's `recommended_cmax` becomes `reference_optima` for runs A–D. Without this flag, recovery seeds would be wrong.

Steps:

1. Run recovery setup with `--reference-cmax-yaml` (command below). This merges baseline `recommended_cmax` into the manifest and writes seed dirs A–D under `dest-base`.
2. For non-CMT04 sites, scale `bias_tiers` per-PFT before running setup (template magnitudes are CMT04-specific).
3. Perturbation runs: **A** (+mild), **B** (−mild), **C** (+strong), **D** (−strong).

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step1/step1_recovery_setup.py \
    --manifest /work/mads_calibration/agent/agent_calibration_step1/recovery_cmax_optima.yaml \
    --reference-cmax-yaml /data/workflows/CMT04-IMN-sa-N100/step1-result.yaml \
    --write-manifest /data/workflows/CMT04-IMN/recovery-manifest.yaml \
    --cmtnum 4 \
    --dest-base /data/workflows/CMT04-IMN \
    --runs A B C D'
```

`dest-base` is `/data/workflows/CMT{cmtnum:02d}-{site_label}` (e.g. `CMT04-IMN`).

`--write-manifest` saves the merged yaml (template tiers + your `recommended_cmax`) for audit; seed dirs are written under `dest-base`.

For each run A–D:

1. Point `seed_path` to `parameters-recovery-{A|B|C|D}` under `dest-base`.
2. Create `logs/sa-{site_label}-recovery-{A|B|C|D}.yaml` with `percent_diffs: 0.40`, unique `work_dir`.
3. Run SA and analyze with `step1_analyze.py`.
4. Track global best RMSE across baseline + all perturbation runs.

After all runs, select the global best. Report even if none meet RMSE < 10.

---

## Output Contract

Write a YAML/JSON artifact via `step1_analyze.py --json-out` to `{work_dir}/step1-result.yaml` (canonical runtime path under `/data/workflows/`). After the full baseline + recovery loop, copy the consolidated result to `mads_calibration/logs/{run_id}-step1-result.yaml` (gitignored local archive).

```yaml
run_id: CMT04-IMN-step1
status: pass          # pass | best_effort
best_rmse: 7.42
best_r2: 0.91
best_sample_index: 42
work_dir: /data/workflows/CMT04-IMN-sa-recovery-C/
config_yaml: mads_calibration/logs/sa-IMN-recovery-C.yaml
n_eq_passing: 87
n_total_samples: 100
recommended_cmax:
  cmax_pft0: 243.20
  cmax_pft1: 423.38
  cmax_pft2: 52.93
  # ... one key per active PFT
perturbation_runs: []   # list of {run_id, work_dir, best_rmse, status} if triggered
notes: ""
```

---

## Decision Rules

1. **Always** apply equilibrium filter before ranking samples.
2. Rank by R² descending (take last rows from `n_top_runs`).
3. RMSE is aggregate across all INGPP PFT target columns (`calc_metrics`).
4. Trigger perturbation loop when `step1_analyze.py` returns exit `2` (`best_effort`, RMSE ≥ `rmse_threshold`).
5. Enforce `(0, LIM]` on all written cmax values.
6. Do not modify `calibration_targets.py` or `parameters/cmt_calparbgc.txt` in the repo — write copies under `/data/workflows/`.

---

## Failure Modes

| Symptom | Action |
|---------|--------|
| CMT not in `calibration_targets.py` | Stop; report missing CMT. |
| No equilibrium-passing samples | Report count; optionally relax eq limits and note in output. |
| Negative cmax after perturbation | Reduce negative bias for affected PFT; re-run setup. |
| SA sample folder errors | Inspect `sample_NNNNNNNNN/` logs; report failing sample indices. |
| `results.csv` missing | SA did not complete; check container logs. |

---

## Do Not

- Run Step 2 (vegetation/soil targets).
- Run `pip install` inside the container.
- Modify `calibration/calibration_targets.py`.
- Commit secrets or `.env` credentials.
- Commit `logs/` (gitignored local run artifacts).
- Use `sa-config-demo.yaml` — correct name is `sa-demo-config.yaml`.

---

## Filename Reference

| Draft / incorrect name | Correct path |
|------------------------|--------------|
| `calibration-process.ipynb` | `mads_calibration/notebooks/calibration_process.ipynb` |
| `sa-config-demo.yaml` | `mads_calibration/sa-demo-config.yaml` |
| Notebook Step 1 example (CMT04 Imnavait) | `mads_calibration/agent/agent_calibration_step1/sa-step1-example-imn.yaml` |
| Agent Step 1 / recovery SA configs | `mads_calibration/logs/sa-{SITE}-step1.yaml`, `logs/sa-{SITE}-recovery-{A,B,C,D}.yaml` |
| Agent Step 1 result artifacts | `{work_dir}/step1-result.yaml`; archive copy in `logs/{run_id}-step1-result.yaml` |
