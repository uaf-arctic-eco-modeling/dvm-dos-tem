# Agent calibration pipeline

Attach **one phase instruction file at a time** in Cursor, in order:

1. [agent_calibration_setup](agent_calibration_setup/) — `@calibration_setup.md` (Phase 0)
2. [agent_calibration_step1](agent_calibration_step1/) — `@step1-cmax-agent.md` (Step 1 `cmax`)
3. [agent_calibration_step2](agent_calibration_step2/) — `@agent-instructions-step2.md` (Step 2 integrated)
4. [agent_final_evaluation](agent_final_evaluation/) — `@final-model-evaluation.md` (transient validation)

## Hard gates (scripts enforce; do not override in prose)

| Phase | Script | Proceed when |
|-------|--------|--------------|
| 0 | `calibration_setup.py` | exit `0` or `2`; exit `1` blocks Step 1 (no cross-CMT param fallback) |
| 1 | `step1_analyze.py` | `status: pass` (RMSE < 10); `best_effort` = keep iterating |
| 1→2 | `seed_setup.py` (+ `burial_params_setup.py`) | Step 1 `status: pass` (or `--force`); upgrades calpar to 20-row burial schema |
| 2 | `analyze.py` | exit `0` = pass; `2` = iterate bounds; `3` = stop / reopen Step 1 |
| 2 apply | `param_update.py` | matching `--phase` + pass status only (`--force` = documented approval) |

Immutable `parameters-step2`: fixed `seed_path` for all SA iterations; bounds from `propose_bounds.py` / `sample_matrix.csv` only.

Runtime configs and manifests: `mads_calibration/logs/` (gitignored).
