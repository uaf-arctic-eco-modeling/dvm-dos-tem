# Step 1 agent calibration

Automated **Step 1** (`cmax` vs `GPPAllIgnoringNitrogen`) for the MADS workflow. Step 2 continues in [`../agent_calibration_step2/`](../agent_calibration_step2/).

## Directory layout

| Location | Tracked in git | Contents |
|----------|----------------|----------|
| This folder | Yes | Templates (`sa-step1-template.yaml`), example (`sa-step1-example-imn.yaml`), scripts, [`calibration_setup.md`](calibration_setup.md), [`step1-cmax-agent.md`](step1-cmax-agent.md) |
| [`../logs/`](../logs/) | **No** (gitignored) | Setup manifests, agent-created SA yamls and optional result archives |
| `/data/workflows/` | No (runtime volume) | SA outputs; canonical `step1-result.yaml` via `--json-out` |

Do not commit files under `logs/`. On a fresh clone, `logs/` is empty until an agent run creates configs there.

## Run the agent

**Phase 0 (setup):** Attach [`calibration_setup.md`](calibration_setup.md) (`@calibration_setup.md`) with `site_name`, `cmtnum`, `site_label`. Provisions GCS inputs/parameters and writes `logs/{site_label}-setup-manifest.yaml`.

**Phase 1 (calibration):** Attach [`step1-cmax-agent.md`](step1-cmax-agent.md) (`@step1-cmax-agent.md`) using fields from the setup manifest (`site`, `PXx`, `PXy`, `cmtnum`, `site_label`, `seed_path`).

## Scripts

| Script | Purpose |
|--------|---------|
| [`calibration_setup.py`](calibration_setup.py) | Phase 0: GCS sync, config.js, verify mapping, write setup manifest |
| [`step1_analyze.py`](step1_analyze.py) | Headless post-hoc analysis; writes `{work_dir}/step1-result.yaml` |
| [`step1_recovery_setup.py`](step1_recovery_setup.py) | Perturbed seed dirs for recovery runs A–D |
