# agent_calibration_step2

Prerequisite: Step 1 complete — [`step1-transition.md`](step1-transition.md).

Load [`agent-instructions-step2.md`](agent-instructions-step2.md) (authoritative).

Next: [agent_final_evaluation](../agent_final_evaluation/) after soil (+ nfall) passes are applied.

## Sequence

**N-level → Krb → Cfall → Nfall → Soil** (`kdc*` only; `micbnup` frozen after N-level)

| Template | Phase | Params → target |
|----------|-------|------------------|
| `sa-step2-nlevel-template.yaml` | `nlevel` | `micbnup`+`nmax` → AVLN |
| `sa-step2-krb-template.yaml` | `krb` | `krb` → NPP |
| `sa-step2-cfall-template.yaml` | `cfall` | `cfall` → VEGC |
| `sa-step2-nfall-template.yaml` | `nfall` | `nfall` → VEGN |
| `sa-step2-soil-template.yaml` | `soil` | `kdc*` → soil C |
| `sa-step2-rhmoistfrozen-template.yaml` | `phase6` | `rhmoistfrozen` → MINEC |

GPP field fit is not gated here (needs `calibration_targets.py` outside this folder).

## Scripts

| Script | Role |
|--------|------|
| `seed_setup.py` | Build `parameters-step2` from Step 1 `cmax`; init stage ledger |
| `stage_ledger.py` | Stage order preflight + ledger I/O |
| `analyze.py` | Gates (`--phase nlevel\|krb\|cfall\|nfall\|soil\|…`); preflight from ledger |
| `propose_bounds.py` | Bounds after exit `2` (`--family` matching phase) |
| `param_update.py` | Apply `*_pass` to `parameters-step2`; update ledger |

**Hard gates:** ledger enforces stage order; no stage skip; exit `3` = HALT; one SA per VM. See [agent README](../README.md#sa-concurrency-per-vm).
