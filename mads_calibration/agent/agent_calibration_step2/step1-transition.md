# Step 1 → Step 2 transition

Handoff from [`../agent_calibration_step1/`](../agent_calibration_step1/) to Step 2. Authoritative workflow: [`agent-instructions-step2.md`](agent-instructions-step2.md).

## Prerequisites

| Field | Use |
|-------|-----|
| `recommended_cmax` | Fixed in Step 2 `seed_path`; **not** re-sampled |
| `status` | Must be `pass` for `seed_setup.py` (default); `best_effort` needs `--force` |

## What changes

| Setting | Step 1 | Step 2 |
|---------|--------|--------|
| `params` | `cmax` | Staged: nlevel → krb → cfall → nfall → soil |
| `calib_mode` | `GPPAllIgnoringNitrogen` | **`VEGC`** |
| `opt_run_setup` | `--eq-yrs 200` | **`--eq-yrs 2000`** |
| `seed_path` | repo/recovery params | **`parameters-step2`** |

Do **not** reopen Step 1 from Step 2 on N-level failure (exit `3` = human HALT).

## Seed

```bash
python mads_calibration/agent/agent_calibration_step2/seed_setup.py \
  --step1-result <path-to-step1-result.yaml> \
  --cmtnum 4 \
  --dest /data/workflows/CMT04-IMN/parameters-step2
```

## Start checklist

- [ ] Step 1 `status: pass` (or documented `--force`)
- [ ] `parameters-step2` exists; `step2-stage-ledger.yaml` initialized (empty `stages`)
- [ ] First SA is **N-level** (`sa-step2-nlevel-template.yaml`)
- [ ] `calib_mode: VEGC`; `aux_outputs: [INGPP y, GPP y]`
- [ ] Loaded [`agent-instructions-step2.md`](agent-instructions-step2.md)
