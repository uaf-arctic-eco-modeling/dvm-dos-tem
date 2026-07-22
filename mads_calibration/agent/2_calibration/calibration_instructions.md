# Step 2 Calibration — Agent Instructions

Load this file for Step 2. Path: `mads_calibration/agent/2_calibration/calibration_instructions.md`.

Canonical process: [`docs_src/sphinx/source/calibration.rst`](../../../docs_src/sphinx/source/calibration.rst) (N limitation ON, then soil).

`calib_mode: VEGC` turns NFEED on. Run **one SA at a time** per VM.

Path conventions: [Multisite conventions](../0_setup/setup_instructions.md#multisite-conventions). Workflow root: `/data/workflows/CMT{cmtnum:02d}-{site_label}/`.

---

## Overview

Step 2 is an **iterative exploration process**, not a fixed sequence of stages. After Step 1 fixes `cmax`, calibrate vegetation parameters to fit vegetation targets, then calibrate soil parameters to fit soil targets.

| Setting | Step 1 | Step 2 |
|---------|--------|--------|
| `params` | `cmax` | Vegetation then soil (see below) |
| `calib_mode` | `GPPAllIgnoringNitrogen` | **`VEGC`** |
| `opt_run_setup` | `--eq-yrs 200` | **`--eq-yrs 2000`** |
| `seed_path` | repo/recovery params | **`parameters-step2`** |
| `N_samples` | 100 (5 smoke) | **25** (exploration iterations) |

**Sample size:** Use **N=25** for all Step 2 SA runs. This supports fast iteration cycles to understand how parameters interact with targets, which are insensitive, and which correlate. Re-run entire SAs, review results, tweak troublesome PFTs or parameter families, and repeat.

**Two main gates:**
1. **Vegetation pass** (`veg_pass`) — required before starting soil phase
2. **Soil pass** (`soil_pass`) — required before evaluation

Within each phase, iteration order is flexible. Use combined exploration SAs first, then targeted SAs on troublesome parameters or PFTs.

---

## Step 1 handoff

Handoff from [`1_cmax/`](../1_cmax/) to Step 2.

### Prerequisites

| Field | Use |
|-------|-----|
| `recommended_cmax` | Fixed in Step 2 `seed_path`; **not** re-sampled |
| `status` | Must be `pass` for `seed_setup.py` (default); `best_effort` needs `--force` |

Do **not** reopen Step 1 from Step 2 on failure (exit `3` = human HALT).

### Seed

```bash
python mads_calibration/agent/2_calibration/seed_setup.py \
  --step1-result /data/workflows/CMT{cmtnum:02d}-{site_label}/{step1-work-dir}/step1-result.yaml \
  --cmtnum {cmtnum} \
  --dest /data/workflows/CMT{cmtnum:02d}-{site_label}/parameters-step2
```

### Start checklist

- [ ] Step 1 `status: pass` (or documented `--force`)
- [ ] `parameters-step2` exists; `step2-stage-ledger.yaml` initialized (empty `stages`)
- [ ] First SA is **vegetation exploration** (`sa-step2-veg-exploration-template.yaml`)
- [ ] `calib_mode: VEGC`; `N_samples: 25`; `aux_outputs: [INGPP y, GPP y]`

---

## Parameters by phase

### Vegetation parameters (Phase 1)

Fixed from Step 1: **`cmax`** (per PFT).

Calibrated in Step 2:

| Parameter | File | Targets | Notes |
|-----------|------|---------|-------|
| `nmax` | `cmt_calparbgc.txt` | AVLN, GPP/N-ratio | Max plant N uptake |
| `krb(0/1/2)` | `cmt_calparbgc.txt` | NPP* | Maintenance respiration; bounds stay **negative** |
| `cfall(0/1/2)` | `cmt_calparbgc.txt` | VEGC* | Carbon litterfall per compartment |
| `nfall(0/1/2)` | `cmt_calparbgc.txt` | VEGNSTR* | Nitrogen litterfall per compartment |

### Soil parameters (Phase 2 — after `veg_pass`)

| Parameter | File | Targets | Notes |
|-----------|------|---------|-------|
| `micbnup` | `cmt_bgcsoil.txt` | AVLN, GPP/N-ratio | Microbial N uptake |
| `kdcrawc` | `cmt_bgcsoil.txt` | SHLWC (fibric) | Raw/litter decomposition — **largest** kdc value |
| `kdcsoma` | `cmt_bgcsoil.txt` | SHLWC, DEEPC | Active organic matter |
| `kdcsompr` | `cmt_bgcsoil.txt` | DEEPC, MINEC | Physically resistant pool |
| `kdcsomcr` | `cmt_bgcsoil.txt` | MINEC | Chemically resistant pool — **smallest** kdc value |
| `rhmoistfrozen` | `cmt_bgcsoil.txt` | MINEC | **Last resort** when MINEC fails after kdc* tuning |

### Kdc ordering constraint

Soil decomposition rates must satisfy:

```
kdcrawc > kdcsoma > kdcsompr > kdcsomcr
```

Additionally, **`kdcrawc` must be < 1.0**.

This ordering reflects faster turnover in raw/active pools and slower turnover in resistant pools ([`calibration.rst`](../../../docs_src/sphinx/source/calibration.rst)). Enforced in `propose_bounds.py`, `analyze.py`, and `param_update.py`.

When setting `p_bounds`, ensure each subsequent kdc upper bound is below the previous parameter's lower bound. Example:

```yaml
p_bounds:
  - [0.05, 0.95]     # kdcrawc (< 1.0)
  - [0.01, 0.04]     # kdcsoma (< kdcrawc lo)
  - [0.005, 0.009]   # kdcsompr (< kdcsoma lo)
  - [0.001, 0.004]   # kdcsomcr (< kdcsompr lo)
```

---

## Phase 1 — Vegetation iteration

### Goal

Fit vegetation targets: **AVLN**, **NPP***, **VEGC***, **VEGNSTR***, with INGPP:GPP **N-ratio** in biome band.

N-ratio bands: **tundra 1.4–1.6**, **boreal 1.15–1.35**.

### Iteration workflow

```
SEED → Veg exploration SA (N=25) → Analyze → Review
         │                              │
         │                    targets met + N-ratio OK
         │                              ↓
         │                         veg_pass → Phase 2
         │
         └── troublesome PFTs/params → Targeted SA (N=25) → Analyze → repeat
```

1. **Combined exploration SA** — run all vegetation params together:
   - Template: `sa-step2-veg-exploration-template.yaml`
   - Params: `nmax`, `krb(0/1/2)`, `cfall(0/1/2)`, `nfall(0/1/2)` per active PFT
   - Targets: `VegCarbon`, `NPPAll`, `VegStructuralNitrogen`, `AvailableNitrogenSum`
   - Analyze: `--phase veg_exploration`

2. **Review SA results** — understand parameter behavior before changing bounds:
   - Inspect `sample_matrix.csv`, `results.csv`, `targets.csv`
   - Identify **insensitive** parameters (target response flat across sampled range)
   - Identify **correlated** parameters (moving one shifts multiple targets)
   - Note **troublesome PFTs** (specific PFT compartments failing tier while others pass)
   - Use diagnostic plots if helpful: `analyze.py --save-plots`

3. **Targeted SA** (when needed) — narrow focus on failing parameter families or PFTs:
   - Templates: `sa-step2-krb-template.yaml`, `sa-step2-cfall-template.yaml`, `sa-step2-nfall-template.yaml`
   - Analyze with matching `--phase krb|cfall|nfall`
   - Restrict `params`/`pftnums` to active PFTs and compartments that need adjustment
   - Use `propose_bounds.py --family {krb|cfall|nfall}` after exit `2`

4. **Iterate** — re-run exploration or targeted SA until:
   - All gated vegetation targets within tier
   - Selected sample N-ratio in biome band
   - `analyze.py --phase veg_exploration` exits `0` (`veg_pass`)
   - Apply: `param_update.py --phase veg_exploration`

### Reading SA results

| Signal | Meaning | Action |
|--------|---------|--------|
| Flat target response across param range | Parameter **insensitive** to that target | Fix at seed value or narrow bounds; focus on sensitive params |
| Strong correlation between two params and one target | Parameters **interact** | Adjust both together in combined SA; avoid tuning one in isolation |
| One PFT compartment fails while others pass | **Troublesome PFT** | Run targeted SA on that PFT's compartments only |
| Target outside SA envelope (min/max of results) | Target **unreachable** in current bounds | Widen bounds or HALT (exit `3`) |
| N-ratio outside band | N limitation mis-set | Adjust `nmax` (in veg exploration) before krb/cfall/nfall |

### GPP note

`calibration.rst` targets **actual GPP** with N limitation. This harness gates **AVLN** and the INGPP:GPP **ratio** as stability diagnostics — N-limited GPP field targets live in `calibration_targets.py`. Do not report GPP as calibrated on `veg_pass`.

---

## Phase 2 — Soil iteration

**Prerequisite:** applied `veg_pass` in stage ledger.

### Goal

Fit soil targets: **SHLWC**, **DEEPC**, **MINEC**, with N-ratio still in band.

### Iteration workflow

```
veg_pass → Soil exploration SA (N=25) → Analyze → Review
              │                              │
              │                    targets met + kdc ordering OK
              │                              ↓
              │                         soil_pass → Evaluation
              │
              ├── iterate bounds / targeted kdc* SA
              └── MINEC still failing → rhmoistfrozen (last) → retune kdc*
```

1. **Combined exploration SA** — run all soil params together:
   - Template: `sa-step2-soil-exploration-template.yaml`
   - Params: `micbnup`, `kdcrawc`, `kdcsoma`, `kdcsompr`, `kdcsomcr`
   - Targets: `CarbonShallow`, `CarbonDeep`, `CarbonMineralSum`, `AvailableNitrogenSum`
   - Analyze: `--phase soil_exploration`
   - Enforce kdc ordering in `p_bounds` (see above)

2. **Review SA results** — same analysis approach as vegetation:
   - `kdcrawc` primarily moves **SHLWC** (fibric layer)
   - `kdcsoma` moves **SHLWC** and **DEEPC** (active pool)
   - `kdcsompr` moves **DEEPC** and **MINEC** (physically resistant)
   - `kdcsomcr` primarily moves **MINEC** (chemically resistant)
   - `micbnup` affects **AVLN** and N-ratio

3. **Targeted SA** (when needed):
   - Template: `sa-step2-soil-template.yaml` (kdc* only)
   - Analyze: `--phase soil`
   - Use `propose_bounds.py --family soil` or `--family soil_exploration`

4. **Rhmoist branch** (last resort for MINEC):
   - When soil `failing_targets` includes `MINEC*` after kdc* iteration:
   - Snapshot `parameters-step2`
   - Run `sa-step2-rhmoistfrozen-template.yaml` → analyze/apply `--phase phase6`
   - Re-run soil template → analyze/apply `--phase phase7`
   - Restore snapshot if MINEC regresses

5. **Iterate** until `analyze.py --phase soil_exploration` exits `0` (`soil_pass`), then apply.

---

## Minimum user inputs

```yaml
cmtnum: {cmtnum}
site: {site}
PXx: {PXx}
PXy: {PXy}
site_label: {site_label}
step1_result: /data/workflows/CMT{cmtnum:02d}-{site_label}/.../step1-result.yaml
nitrogen_biome: tundra   # tundra (1.4–1.6) | boreal (1.15–1.35) — set from site/CMT
```

Set `nitrogen_biome` from site ecology (arctic tundra sites → `tundra`; boreal forest → `boreal`). Pass the same value to every `analyze.py --biome` call for this site.

## Checklist

- [ ] `seed_setup.py` → `parameters-step2` + `step2-stage-ledger.yaml`
- [ ] Vegetation exploration SA (N=25) → analyze `--phase veg_exploration`
- [ ] Iterate targeted veg SA as needed → exit `0` → `param_update --phase veg_exploration`
- [ ] Soil exploration SA (N=25) → analyze `--phase soil_exploration`
- [ ] Iterate targeted soil SA / rhmoist as needed → exit `0` → `param_update --phase soil_exploration`
- [ ] [`evaluation_instructions.md`](../3_evaluation/evaluation_instructions.md)

---

## Control flow

Each SA iteration loop: fill yaml from template → `SA_setup_and_run.py --force` → `analyze.py --phase {p} --biome {biome}` →

| Exit | Status | Action |
|------|--------|--------|
| 0 | `*_pass` | `param_update.py --phase {p}`; advance phase or proceed to evaluation |
| 2 | `target_fit_review` | Review SA results; `propose_bounds.py --family {p}` → new iteration |
| 3 | `unreachable_review` | **HALT** — document; human only |
| 1 | `failed` | Fix missing CSVs / SA failure |

### Hard gates

1. No soil phase without applied `veg_pass` (ledger + `analyze.py` preflight)
2. Exit `3` = stop (never auto-reopen Step 1; never skip ahead)
3. One `SA_setup_and_run.py` at a time per VM
4. Kdc ordering must be valid before soil apply

Preflight: `analyze.py` reads `step2-stage-ledger.yaml` (auto from `work_dir` under `.../logs/`). Use `--skip-preflight` only with documented approval.

---

## Commands (pattern)

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/2_calibration/seed_setup.py \
    --step1-result /data/workflows/CMT{cmtnum:02d}-{site_label}/.../step1-result.yaml \
    --cmtnum {cmtnum} --dest /data/workflows/CMT{cmtnum:02d}-{site_label}/parameters-step2'

# After filling logs/sa-{site_label}-step2-veg-exploration-iter1.yaml from template:
docker compose exec -T dvmdostem-autocal bash -c \
  'cd /work && python mads_calibration/SA_setup_and_run.py --force \
    mads_calibration/logs/sa-{site_label}-step2-veg-exploration-iter1.yaml'

docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/2_calibration/analyze.py \
    --phase veg_exploration \
    --work-dir /data/workflows/CMT{cmtnum:02d}-{site_label}/logs/sa-step2-veg-exploration-iter1/ \
    --param-dir /data/workflows/CMT{cmtnum:02d}-{site_label}/parameters-step2 \
    --biome {nitrogen_biome} \
    --json-out /data/workflows/CMT{cmtnum:02d}-{site_label}/logs/sa-step2-veg-exploration-iter1/step2-result.yaml'

# exit 0:
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/2_calibration/param_update.py \
    --phase veg_exploration \
    --step2-result /data/workflows/CMT{cmtnum:02d}-{site_label}/logs/sa-step2-veg-exploration-iter1/step2-result.yaml \
    --param-dir /data/workflows/CMT{cmtnum:02d}-{site_label}/parameters-step2 --cmtnum {cmtnum}'

# exit 2 (vegetation targeted iteration):
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/2_calibration/propose_bounds.py \
    --work-dir /data/workflows/CMT{cmtnum:02d}-{site_label}/logs/sa-step2-veg-exploration-iter1/ \
    --step2-result /data/workflows/CMT{cmtnum:02d}-{site_label}/logs/sa-step2-veg-exploration-iter1/step2-result.yaml \
    --family veg_exploration --yaml-out mads_calibration/logs/sa-{site_label}-step2-veg-exploration-iter2-bounds.yaml'
```

Repeat the same pattern for soil (`--phase soil_exploration`, template `sa-step2-soil-exploration-template.yaml`, `--family soil_exploration`).

For targeted SA within a phase, use the matching template and `--phase krb|cfall|nfall|soil`.

---

## Acceptance

| Phase | Pass means |
|-------|------------|
| `veg_pass` | NPP*/VEGC*/VEGNSTR* ≤10%, AVLN ≤20%, N-ratio in biome band |
| `soil_pass` | SHLWC/DEEPC/MINEC ≤20%, kdc ordering valid, N-ratio in band |
| `phase6_pass` | MINEC ≤20% after rhmoistfrozen adjustment |
| `phase7_pass` | SHLWC/DEEPC/MINEC ≤20% after kdc* retune |

Every phase requires the **selected sample** to pass N-ratio (stability guard).

Legacy per-param statuses (`krb_pass`, `cfall_pass`, etc.) remain supported for targeted SA runs within each phase.

---

## Diagnosis

| Signal | Action |
|--------|--------|
| exit 2 | Review SA; `propose_bounds.py --family {phase}` |
| AVLN unreachable | Adjust `nmax` (veg) or `micbnup` (soil) bounds |
| NPP unreachable | Targeted krb SA on failing PFTs |
| VEGC fail | Targeted cfall SA |
| VEGNSTR fail | Targeted nfall SA |
| Soil C fail | Soil exploration or targeted kdc* (raw→fibric, active→fibric/humic, pr→humic/mineral) |
| kdc ordering violation | Fix bounds in yaml; re-run SA |
| MINEC fail after kdc* | rhmoistfrozen branch (phase6 → phase7) |
| exit 3 | HALT; document; human decides (targets vs model ceiling) |
| preflight fail | `veg_pass` not in ledger before soil — complete vegetation phase first |

---

## Do not

- Parallel SAs on one VM
- Skip the vegetation gate before soil phase
- Continue after exit `3`
- Re-sample `cmax` / reopen Step 1 automatically
- Use N=100 for Step 2 exploration (use **N=25**)
- Violate kdc ordering (`kdcrawc > kdcsoma > kdcsompr > kdcsomcr`, `kdcrawc < 1.0`)
- Run rhmoistfrozen before exhausting kdc* iteration
- Treat N-ratio pass as GPP field fit
- `param_update` without matching `*_pass` status (unless documented `--force`)
- Commit `logs/`

---

## File reference

| Role | Path |
|------|------|
| Seed | `seed_setup.py` → `/data/workflows/CMT{NN}-{label}/parameters-step2` |
| Scripts | `seed_setup.py`, `stage_ledger.py`, `analyze.py`, `propose_bounds.py`, `param_update.py` |
| Exploration templates | `sa-step2-veg-exploration-template.yaml`, `sa-step2-soil-exploration-template.yaml` |
| Targeted templates | `sa-step2-{krb,cfall,nfall,soil,rhmoistfrozen}-template.yaml` |
| Legacy | `sa-step2-nlevel-template.yaml` (superseded; in-flight sites only) |
| Agent yamls | `mads_calibration/logs/` (gitignored) |
| Closure | [`step2-closure-summary-template.yaml`](../3_evaluation/step2-closure-summary-template.yaml) |
