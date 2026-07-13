# agent_calibration_step2

Prerequisite: Step 1 complete — handoff via [step1-transition.md](step1-transition.md).

Load [`agent-instructions-step2.md`](agent-instructions-step2.md) with site inputs from Step 1 result (see [agent README](../README.md#using-this-harness)).

Next: [agent_final_evaluation](../agent_final_evaluation/) when Nfall is applied and the final `analyze.py --phase main` exit `0`.

Calibrates the full Nmax → Krb → Cfall → Nfall → Kdc\* sequence from
[`docs_src/sphinx/source/calibration.rst`](../../../docs_src/sphinx/source/calibration.rst),
not just soil decomposition + Cfall. See **Parameter coverage** in
[`agent-instructions-step2.md`](agent-instructions-step2.md) and the
**Control flow** staged order (N-level → Krb → main → Nfall).

## Scripts (this folder)

| Script | Role |
|--------|------|
| [`seed_setup.py`](seed_setup.py) | Build immutable `parameters-step2` from Step 1 `cmax` |
| [`burial_params_setup.py`](burial_params_setup.py) | Upgrade `cmt_calparbgc.txt` to 20-row schema (`s2dfraction`, `d2mfraction`); called by `seed_setup.py` |
| [`analyze.py`](analyze.py) | Post-SA gates (`--phase main\|nlevel\|krb\|nfall\|phase6\|phase7`) |
| [`propose_bounds.py`](propose_bounds.py) | Tighten bounds after analyze exit `2` (`--family main\|nlevel\|krb\|nfall`) |
| [`param_update.py`](param_update.py) | Apply passing sample to `parameters-step2` (`--phase` matching analyze) |

## Templates (this folder)

| Template | Phase | Params → target |
|----------|-------|------------------|
| [`sa-step2-nlevel-template.yaml`](sa-step2-nlevel-template.yaml) | `nlevel` | `micbnup` + `nmax` → AVLN, N-ratio |
| [`sa-step2-krb-template.yaml`](sa-step2-krb-template.yaml) | `krb` | `krb(0/1/2)` → NPP |
| [`sa-step2-template.yaml`](sa-step2-template.yaml) | `main` | `kdc*`/`micbnup` + `cfall(0/1/2)` → soil C, VEGC |
| [`sa-step2-rhmoistfrozen-template.yaml`](sa-step2-rhmoistfrozen-template.yaml) | `phase6` | `rhmoistfrozen` → MINEC |
| [`sa-step2-soil-retune-template.yaml`](sa-step2-soil-retune-template.yaml) | `phase7` | `kdc*`/`micbnup` → SHLWC/DEEPC/MINEC |
| [`sa-step2-nfall-template.yaml`](sa-step2-nfall-template.yaml) | `nfall` | `nfall(0/1/2)` → VEGN |

Workflow and templates: [`agent-instructions-step2.md`](agent-instructions-step2.md).

**Concurrency:** run one `SA_setup_and_run.py` at a time per VM; stages are sequential (N-level → Krb → main → …). See [agent README](../README.md#sa-concurrency-per-vm).
