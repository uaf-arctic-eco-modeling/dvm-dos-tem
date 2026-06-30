# agent_calibration_step2

Prerequisite: Step 1 complete — handoff via [step1-transition.md](step1-transition.md).

Attach `@agent-instructions-step2.md` with site inputs from Step 1 result.

Next: [agent_final_evaluation](../agent_final_evaluation/) when last `analyze.py --phase main` exit `0`.

## Scripts (this folder)

| Script | Role |
|--------|------|
| [`seed_setup.py`](seed_setup.py) | Build immutable `parameters-step2` from Step 1 `cmax` |
| [`burial_params_setup.py`](burial_params_setup.py) | Upgrade `cmt_calparbgc.txt` to 20-row schema (`s2dfraction`, `d2mfraction`); called by `seed_setup.py` |
| [`analyze.py`](analyze.py) | Post-SA gates (`--phase main\|phase6\|phase7`) |
| [`propose_bounds.py`](propose_bounds.py) | Tighten bounds after analyze exit `2` |
| [`param_update.py`](param_update.py) | Apply passing sample to `parameters-step2` |

Workflow and templates: [`agent-instructions-step2.md`](agent-instructions-step2.md).
