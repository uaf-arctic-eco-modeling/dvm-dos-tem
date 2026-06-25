# Step 2 agent calibration

Automated **Step 2** (joint above/belowground C/N) after Step 1 `cmax` is fixed. Step 1 lives in [`../agent_calibration/`](../agent_calibration/).

## Directory layout

| Location | Tracked in git | Contents |
|----------|----------------|----------|
| This folder | Yes | Templates, example yaml, scripts, agent instruction markdown |
| [`../logs/`](../logs/) | **No** (gitignored) | Agent-created Step 2 SA yamls; optional result archives |
| `/data/workflows/` | No (runtime volume) | SA outputs; canonical `step2-result.yaml` via `--json-out` |

Step 1 hands off `recommended_cmax` from `{work_dir}/step1-result.yaml` (runtime). Do not commit `logs/`.

## Run the agent

Attach [`agent-instructions-step2.md`](agent-instructions-step2.md) in Cursor (`@agent-instructions-step2.md`) with site inputs. Handoff from Step 1: [`step1-transition.md`](step1-transition.md).

## Scripts

| Script | Purpose |
|--------|---------|
| [`seed_setup.py`](seed_setup.py) | Write `parameters-step2` with fixed Step 1 `cmax` |
| [`analyze.py`](analyze.py) | Headless post-hoc analysis; writes `step2-result.yaml` |
| [`propose_bounds.py`](propose_bounds.py) | Propose `p_bounds` for the next iteration |
| [`param_update.py`](param_update.py) | Apply `recommended_params` to workflow parameter files |

## Templates and examples

| File | Purpose |
|------|---------|
| [`sa-step2-template.yaml`](sa-step2-template.yaml) | Parameterized main Step 2 SA (copy into `logs/`) |
| [`sa-step2-example-imn.yaml`](sa-step2-example-imn.yaml) | Filled CMT04 Imnavait smoke example (notebook reference) |
| [`sa-step2-rhmoistfrozen-template.yaml`](sa-step2-rhmoistfrozen-template.yaml) | Phase 6 MINEC / `rhmoistfrozen` SA |
| [`sa-step2-soil-retune-template.yaml`](sa-step2-soil-retune-template.yaml) | Phase 7 focused soil retune (optional) |
| [`sa-final-eval-template.yaml`](sa-final-eval-template.yaml) | Full site transient evaluation run |
| [`step2-closure-summary-template.yaml`](step2-closure-summary-template.yaml) | Post-calibration closure artifact |

## Docs

| File | Purpose |
|------|---------|
| [`agent-instructions-step2.md`](agent-instructions-step2.md) | Step 2 agent workflow |
| [`step1-transition.md`](step1-transition.md) | Step 1 → Step 2 handoff |
| [`final-model-evaluation.md`](final-model-evaluation.md) | Post-calibration full site run and validation |
