# Agent calibration harness

Instruction-driven workflow for MADS calibration (Phase 0 → Step 1 `cmax` → Step 2 staged → final evaluation). Works with any **coding agent** that can read markdown instructions and run shell commands on the calibration host (Cursor, Claude Code, Antigravity, etc.).

## Execution environment

Run the agent on a host that can execute commands inside the `dvmdostem-autocal` Docker container with `/work`, `/data/input-catalog`, and `/data/workflows` mounted. Typical setup: GCP calibration VM with the repo checked out and Docker Compose running.

The agent needs **shell access on that host**. If the agent UI runs elsewhere (IDE cloud session, separate agent runtime), connect it to the calibration VM as its execution worker — do not rely on a local SSH session that the agent cannot reach. Examples: Cursor **My Machines** on the VM; Claude Code or Antigravity opened in / attached to the VM workspace.

## Using this harness

Load **one phase instruction file at a time**, in order (paths relative to `mads_calibration/agent/`):

1. [agent_calibration_setup](agent_calibration_setup/) — `calibration_setup.md` (Phase 0)
2. [agent_calibration_step1](agent_calibration_step1/) — `step1-cmax-agent.md` (Step 1 `cmax`)
3. [agent_calibration_step2](agent_calibration_step2/) — `agent-instructions-step2.md` (Step 2 staged)
4. [agent_final_evaluation](agent_final_evaluation/) — `final-model-evaluation.md` (transient validation)

How to load the instruction file depends on your agent:

| Agent | Typical pattern |
|-------|-----------------|
| **Cursor** | `@mads_calibration/agent/.../instruction.md` in chat |
| **Claude Code** | Ask the agent to read the file path, or reference it in `CLAUDE.md` / project instructions |
| **Antigravity** | Include the file path in the workspace prompt or agent configuration |
| **Other** | Paste the repo-relative path and ask the agent to read it before proceeding |

Each phase doc lists **minimum user inputs** (YAML). Provide those in your first message when starting that phase.

### SA concurrency (per VM)

Run **one** `SA_setup_and_run.py` job at a time on a calibration VM. Do not launch Step 2 phases (N-level, Krb, Cfall, Nfall, Soil, phase6/7) or Step 1 runs in parallel — even from the same `parameters-step2` seed. Each SA spawns a multiprocessing pool of `dvmdostem` workers (N=100 × 2000 eq-yrs is typical). Overlapping jobs oversubscribe CPU, leave workers hung on slow samples, and block `results.csv` aggregation. Wait for exit `0` (or a clean failure), run `analyze.py`, then start the next phase.

Before a new SA: confirm no stray `dvmdostem` or `SA_setup_and_run.py` processes (`docker compose exec dvmdostem-autocal bash -c 'pgrep -a dvmdostem | head'`). If a run was canceled mid-pool, kill stuck workers and rebuild with `driver.post_hoc_build_all()` only when every `sample_*` has complete `output/` (see Step 2 Failure modes).

## Hard gates (scripts enforce; do not override in prose)

| Phase | Script | Proceed when |
|-------|--------|--------------|
| 0 | `calibration_setup.py` | exit `0` or `2`; exit `1` blocks Step 1 (no cross-CMT param fallback) |
| 1 | `step1_analyze.py` | `status: pass` (RMSE < 10); `best_effort` = keep iterating |
| 1→2 | `seed_setup.py` (+ `burial_params_setup.py`) | Step 1 `status: pass` (or `--force`); creates `step2-stage-ledger.yaml` |
| 2 preflight | `analyze.py` + `stage_ledger.py` | `--param-dir` set: prior `*_pass` stages applied (or `--skip-preflight` with approval) |
| 2 | `analyze.py` | exit `0` = phase pass; `2` = iterate bounds; `3` = **HALT for human** (do **not** auto-reopen Step 1; do not start the next stage) |
| 2 apply | `param_update.py` | matching `--phase` + pass status only; updates stage ledger (`--force` = documented approval) |

Step 2 order: **nlevel → krb → cfall → nfall → soil**. See [`agent_calibration_step2/agent-instructions-step2.md`](agent_calibration_step2/agent-instructions-step2.md).

Immutable `parameters-step2`: fixed `seed_path` for all SA iterations; bounds from `propose_bounds.py` / `sample_matrix.csv` only.

Shared helpers (this folder, imported by Step 1/2 analyze scripts): [`eq_workdir.py`](eq_workdir.py) — equilibrium gates from collated `eq_*_quality.csv` in SA `work_dir`.

Runtime configs and manifests: `mads_calibration/logs/` (gitignored).
