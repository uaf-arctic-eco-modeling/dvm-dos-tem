# Step 2 Calibration — Agent Instructions

Load this file for Step 2. Path: `mads_calibration/agent/2_calibration/calibration_instructions.md`.

Canonical process: [`docs_src/sphinx/source/calibration.rst`](../../../docs_src/sphinx/source/calibration.rst) (N limitation ON, then soil).

`calib_mode: VEGC` turns NFEED on. Run **one SA at a time** per VM.

Path conventions: [Multisite conventions](../0_setup/setup_instructions.md#multisite-conventions). Workflow root: `/data/workflows/CMT{cmtnum:02d}-{site_label}/`.

---

## Step 1 handoff

Handoff from [`1_cmax/`](../1_cmax/) to Step 2.

### Prerequisites

| Field | Use |
|-------|-----|
| `recommended_cmax` | Fixed in Step 2 `seed_path`; **not** re-sampled |
| `status` | Must be `pass` for `seed_setup.py` (default); `best_effort` needs `--force` |

### What changes

| Setting | Step 1 | Step 2 |
|---------|--------|--------|
| `params` | `cmax` | Staged: nlevel → krb → cfall → nfall → soil |
| `calib_mode` | `GPPAllIgnoringNitrogen` | **`VEGC`** |
| `opt_run_setup` | `--eq-yrs 200` | **`--eq-yrs 2000`** |
| `seed_path` | repo/recovery params | **`parameters-step2`** |

Do **not** reopen Step 1 from Step 2 on N-level failure (exit `3` = human HALT).

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
- [ ] First SA is **N-level** (`sa-step2-nlevel-template.yaml`)
- [ ] `calib_mode: VEGC`; `aux_outputs: [INGPP y, GPP y]`

---

## Stages (required order)

| # | Phase | Params | Gate (`analyze --phase`) | Template |
|---|-------|--------|--------------------------|----------|
| 0 | N-level | `micbnup`, `nmax` | `nlevel` → AVLN (+ N-ratio diagnostic) | `sa-step2-nlevel-template.yaml` |
| 1 | Krb | `krb(0/1/2)` | `krb` → NPP* | `sa-step2-krb-template.yaml` |
| 2 | Cfall | `cfall(0/1/2)` | `cfall` → VEGC* | `sa-step2-cfall-template.yaml` |
| 3 | Nfall | `nfall(0/1/2)` | `nfall` → VEGNSTR* | `sa-step2-nfall-template.yaml` |
| 4 | Soil | `kdc*` only | `soil` → SHLWC/DEEPC/MINEC | `sa-step2-soil-template.yaml` |

Optional: `phase6` (`rhmoistfrozen` → MINEC) then re-run soil with analyze/apply `--phase phase7`.

**micbnup** is set only in N-level and must stay frozen afterward (not in cfall/soil SA).

### GPP note

`calibration.rst` targets **actual GPP** with Nmax/micbnup. This harness gates **AVLN** and the INGPP:GPP **ratio** only — N-limited GPP targets live outside the agent folder (`calibration_targets.py`). Do not report GPP as calibrated on `nlevel_pass`.

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
- [ ] N-level → exit `0` → `param_update --phase nlevel`
- [ ] Krb → exit `0` → `param_update --phase krb`
- [ ] Cfall → exit `0` → `param_update --phase cfall`
- [ ] Nfall → exit `0` → `param_update --phase nfall`
- [ ] Soil → exit `0` → `param_update --phase soil` (phase6/7 if MINEC needs rhmoist)
- [ ] [`evaluation_instructions.md`](../3_evaluation/evaluation_instructions.md)

---

## Control flow

```
SEED → N-level → Krb → Cfall → Nfall → Soil → DONE
         │         │       │       │       │
         └─exit 3──┴─HALT──┴───────┴───────┘  (no next stage; no Step 1 reopen)

Soil loop only: if MINEC failing → phase6 (rhmoist) → phase7 (soil alias) with snapshots
```

Each stage loop: SA → `analyze.py --phase {p} --biome {biome}` →

| Exit | Status | Action |
|------|--------|--------|
| 0 | `*_pass` | `param_update.py --phase {p}`; next stage |
| 2 | `target_fit_review` | `propose_bounds.py --family {p}` → new iter |
| 3 | `unreachable_review` | **HALT** — document; human only |
| 1 | `failed` | Fix missing CSVs / SA |

### Hard gates

1. No Krb without applied `nlevel_pass` (ledger + `analyze.py` preflight)
2. No Cfall without applied `krb_pass`
3. No Nfall without applied `cfall_pass`
4. No Soil without applied `nfall_pass`
5. Exit `3` = stop (never auto-reopen Step 1; never skip ahead)
6. One `SA_setup_and_run.py` at a time per VM

Preflight: `analyze.py` reads `step2-stage-ledger.yaml` (auto from `work_dir` under `.../logs/`). Use `--skip-preflight` only with documented approval.

---

## Commands (pattern)

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/2_calibration/seed_setup.py \
    --step1-result /data/workflows/CMT{cmtnum:02d}-{site_label}/.../step1-result.yaml \
    --cmtnum {cmtnum} --dest /data/workflows/CMT{cmtnum:02d}-{site_label}/parameters-step2'

# After filling logs/sa-{site_label}-step2-{phase}-iterN.yaml from the template:
docker compose exec -T dvmdostem-autocal bash -c \
  'cd /work && python mads_calibration/SA_setup_and_run.py --force \
    mads_calibration/logs/sa-{site_label}-step2-nlevel-iter1.yaml'

docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/2_calibration/analyze.py \
    --phase nlevel --work-dir /data/workflows/CMT{cmtnum:02d}-{site_label}/logs/sa-step2-nlevel-iter1/ \
    --param-dir /data/workflows/CMT{cmtnum:02d}-{site_label}/parameters-step2 \
    --biome {nitrogen_biome} \
    --json-out /data/workflows/CMT{cmtnum:02d}-{site_label}/logs/sa-step2-nlevel-iter1/step2-result.yaml'

# exit 0:
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/2_calibration/param_update.py \
    --phase nlevel \
    --step2-result /data/workflows/CMT{cmtnum:02d}-{site_label}/logs/sa-step2-nlevel-iter1/step2-result.yaml \
    --param-dir /data/workflows/CMT{cmtnum:02d}-{site_label}/parameters-step2 --cmtnum {cmtnum}'

# exit 2:
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/2_calibration/propose_bounds.py \
    --work-dir /data/workflows/CMT{cmtnum:02d}-{site_label}/logs/sa-step2-nlevel-iter1/ \
    --step2-result /data/workflows/CMT{cmtnum:02d}-{site_label}/logs/sa-step2-nlevel-iter1/step2-result.yaml \
    --family nlevel --yaml-out mads_calibration/logs/sa-{site_label}-step2-nlevel-iter2-bounds.yaml'
```

Repeat the same pattern for `krb`, `cfall`, `nfall`, `soil` (change `--phase` / `--family` / template).

### Rhmoist branch (during soil)

When soil `failing_targets` includes `MINEC*`: snapshot `parameters-step2`, run `sa-step2-rhmoistfrozen-template.yaml` → analyze/apply `--phase phase6`, then soil template again with analyze/apply `--phase phase7`. Restore snapshot if MINEC regresses.

---

## Acceptance

| Phase | Pass means |
|-------|------------|
| `nlevel_pass` | AVLN in tier + selected sample N-ratio in biome band |
| `krb_pass` | NPP* ≤10% + N-ratio in band |
| `cfall_pass` | VEGC* ≤10% + N-ratio in band |
| `nfall_pass` | VEGNSTR* ≤10% + N-ratio in band |
| `soil_pass` / `phase7_pass` | SHLWC/DEEPC/MINEC ≤20% + N-ratio in band |

N-ratio bands: tundra 1.4–1.6, boreal 1.15–1.35. Every phase requires the **selected sample** to pass N-ratio (stability guard).

---

## Diagnosis

| Signal | Action |
|--------|--------|
| exit 2 | `propose_bounds.py --family {phase}` |
| AVLN unreachable | Stay on / return to nlevel — not cfall/soil bounds |
| NPP unreachable | Krb phase |
| VEGC fail | Cfall bounds |
| Soil C fail | Soil `kdc*` (raw→fibric, active→fibric/humic, pr→humic/mineral) |
| exit 3 | HALT; document; human decides (targets vs model ceiling) |
| preflight fail | Prior `*_pass` not in ledger — complete earlier stage or `--skip-preflight` (in-flight sites only) |

---

## Do not

- Parallel SAs on one VM
- Skip stages or continue after exit `3`
- Re-sample `cmax` / reopen Step 1 automatically
- Sample `micbnup` outside nlevel
- Treat N-ratio pass as GPP field fit
- `param_update` without matching `*_pass` status (unless documented `--force`)
- Commit `logs/`

---

## File reference

| Role | Path |
|------|------|
| Seed | `seed_setup.py` → `/data/workflows/CMT{NN}-{label}/parameters-step2` |
| Scripts | `seed_setup.py`, `stage_ledger.py`, `analyze.py`, `propose_bounds.py`, `param_update.py` |
| Templates | `sa-step2-{nlevel,krb,cfall,nfall,soil,rhmoistfrozen}-template.yaml` |
| Agent yamls | `mads_calibration/logs/` (gitignored) |
| Closure | [`step2-closure-summary-template.yaml`](../3_evaluation/step2-closure-summary-template.yaml) |
