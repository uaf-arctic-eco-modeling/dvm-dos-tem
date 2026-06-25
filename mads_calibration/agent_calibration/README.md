# Step 1 agent calibration

Automated **Step 1** (`cmax` vs `GPPAllIgnoringNitrogen`) for the MADS workflow. Step 2 continues in [`../agent_calibration_step2/`](../agent_calibration_step2/).

## Directory layout

| Location | Tracked in git | Contents |
|----------|----------------|----------|
| This folder | Yes | Templates (`sa-step1-template.yaml`), example (`sa-step1-example-imn.yaml`), scripts, [`step1-cmax-agent.md`](step1-cmax-agent.md) |
| [`../logs/`](../logs/) | **No** (gitignored) | Agent-created SA yamls and optional result archives |
| `/data/workflows/` | No (runtime volume) | SA outputs; canonical `step1-result.yaml` via `--json-out` |

Do not commit files under `logs/`. On a fresh clone, `logs/` is empty until an agent run creates configs there.

## Run the agent

Attach [`step1-cmax-agent.md`](step1-cmax-agent.md) in Cursor (`@step1-cmax-agent.md`) with site inputs (`cmtnum`, `site`, `PXx`, `PXy`, `site_label`).

## Scripts

| Script | Purpose |
|--------|---------|
| [`step1_analyze.py`](step1_analyze.py) | Headless post-hoc analysis; writes `{work_dir}/step1-result.yaml` |
| [`step1_recovery_setup.py`](step1_recovery_setup.py) | Perturbed seed dirs for recovery runs A–D |
