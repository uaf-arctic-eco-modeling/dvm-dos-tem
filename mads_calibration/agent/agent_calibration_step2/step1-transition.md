# Step 1 → Step 2 transition

Handoff from Step 1 agent calibration ([`../agent_calibration_step1/`](../agent_calibration_step1/)) to begin Step 2 integrated calibration. Full Step 2 workflow: [`agent-instructions-step2.md`](agent-instructions-step2.md).

## Prerequisites

Step 1 must be complete with `step1-result.yaml` from [`step1_analyze.py`](../agent_calibration_step1/step1_analyze.py) (`--json-out` under `/data/workflows/`).

| Field | Use when starting Step 2 |
|-------|--------------------------|
| `recommended_cmax` (`cmax_pft0` … `cmax_pftN`) | Fixed in Step 2 `seed_path`; **not** re-sampled |
| `work_dir` / `run_id` | Provenance in `step2-seed-manifest.yaml` |
| `status` | Should be `pass` or documented `best_effort` |

## What changes

| Setting | Step 1 | Step 2 |
|---------|--------|--------|
| `params` | `cmax` per PFT | `micbnup`, `kdc*`, `cfall(0/1/2)` per PFT |
| `percent_diffs` | 0.25 (0.40 recovery) | **0.95** initially, then `p_bounds` |
| `calib_mode` | `GPPAllIgnoringNitrogen` | **`VEGC`** |
| `target_names` | `GPPAllIgnoringNitrogen` | Soil + veg targets (see yaml template) |
| `opt_run_setup` | `--eq-yrs 200` | **`--eq-yrs 2000`** |
| `work_dir` | Step 1 path | New unique path (e.g. `/data/workflows/CMT04-IMN/logs/sa-step2`) |
| `seed_path` | `/work/parameters` or recovery dir | **`parameters-step2`** |

## What stays fixed

- `cmtnum`, `site`, `PXx`, `PXy`, driving data
- **`cmax`** for all active PFTs (from Step 1 `recommended_cmax`)
- Do **not** modify `/work/parameters` in the repo

## Setup — seed parameters

```bash
python mads_calibration/agent/agent_calibration_step2/seed_setup.py \
  --step1-result <path-to-step1-result.yaml> \
  --cmtnum 4 \
  --dest /data/workflows/CMT04-IMN/parameters-step2
```

Writes:

- `parameters-step2/` — full parameter tree with Step 1 `cmax` applied
- `step2-seed-manifest.yaml` — audit record (parent of `parameters-step2`)

## Setup — first Step 2 SA yaml

Copy [`sa-step2-template.yaml`](sa-step2-template.yaml) or adapt [`sa-step2-example-imn.yaml`](sa-step2-example-imn.yaml) to `logs/sa-{SITE}-step2.yaml` and set:

- `seed_path` → `parameters-step2`
- `calib_mode: VEGC`
- `aux_outputs: [INGPP y, GPP y]` (required for `nitrogen_check`)
- Site, grid cell, `cmtnum`, and a new `work_dir`

Validate with a dry-run before the first SA:

```bash
python mads_calibration/SA_setup_and_run.py --dry-run \
  -f mads_calibration/logs/sa-{SITE}-step2.yaml
```

## Checklist (start Step 2)

- [ ] Step 1 `recommended_cmax` available in `step1-result.yaml`
- [ ] `seed_setup.py` run; `parameters-step2` exists
- [ ] `seed_path` in Step 2 SA yaml points to `parameters-step2`
- [ ] Step 2 SA yaml in `logs/` (from `sa-step2-template.yaml` or `sa-step2-example-imn.yaml`)
- [ ] `aux_outputs` includes `INGPP y` and `GPP y`
- [ ] `--dry-run` passes
