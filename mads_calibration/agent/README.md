# Agent calibration pipeline

## Runtime

Cloud Agent sessions must use **My Machines** on the GCP calibration VM (not Cursor-managed). Remote SSH into the VM does not route Cloud Agent tool calls; select the connected worker in the Cloud Agents dashboard.

### SA concurrency (per VM)

Run **one** `SA_setup_and_run.py` job at a time on a calibration VM. Do not launch Step 2 phases (N-level, Krb, main, Nfall, phase6/7) or Step 1 runs in parallel — even from the same `parameters-step2` seed. Each SA spawns a multiprocessing pool of `dvmdostem` workers (N=100 × 2000 eq-yrs is typical). Overlapping jobs oversubscribe CPU, leave workers hung on slow samples, and block `results.csv` aggregation. Wait for exit `0` (or a clean failure), run `analyze.py`, then start the next phase.

Before a new SA: confirm no stray `dvmdostem` or `SA_setup_and_run.py` processes (`docker compose exec dvmdostem-autocal bash -c 'pgrep -a dvmdostem | head'`). If a run was canceled mid-pool, kill stuck workers and rebuild with `driver.post_hoc_build_all()` only when every `sample_*` has complete `output/` (see Step 2 Failure modes).

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

Shared helpers (this folder, imported by Step 1/2 analyze scripts): [`eq_workdir.py`](eq_workdir.py) — equilibrium gates from collated `eq_*_quality.csv` in SA `work_dir`.

Runtime configs and manifests: `mads_calibration/logs/` (gitignored).
