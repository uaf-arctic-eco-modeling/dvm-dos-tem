# Step 2 Integrated Calibration — Cursor Agent Instruction Set

Attach this file in Cursor (`@agent-instructions-step2.md`) when running Step 2 calibration.

Automate **Step 2** after Step 1: jointly calibrate soil and vegetation parameters with **N limitation ON** (`calib_mode: VEGC`) inside `dvmdostem-autocal`.

**Prerequisite:** Step 1 `recommended_cmax` — see [`step1-transition.md`](step1-transition.md). Interactive reference: [`notebooks/calibration_process.ipynb`](../notebooks/calibration_process.ipynb) (uses `sa-step2-example-imn.yaml`, not agent `logs/` paths).

**Parameter coverage:** this workflow calibrates the full Nmax → Krb → Cfall →
Nfall → Kdc\* sequence from
[`docs_src/sphinx/source/calibration.rst`](../../../docs_src/sphinx/source/calibration.rst)
("Calibrate vegetation parameters with N limitation"), not just soil decomposition
+ Cfall. If AVLN, the N-ratio, or NPP show up in `misfit_classification.unreachable`
on the main-phase analyze, that is the signal to run the dedicated N-level / Krb
phase below — **do not** try to fix them by widening main-phase soil/Cfall bounds
alone; Nmax, Krb, and Nfall are not sampled by the main phase.

## Minimum user action

```yaml
cmtnum: 4
site: /data/input-catalog/Imnavait
PXx: 0
PXy: 0
site_label: IMN
step1_result: /data/workflows/CMT04-IMN-sa-recovery-C/step1-result.yaml
nitrogen_biome: tundra   # analyze.py --biome (boreal | tundra)
```

## Checklist

- [ ] `parameters-step2` via `seed_setup.py` (adds burial rows if missing); smoke SA (N=5) on new sites
- [ ] **N-level SA** (nlevel family) + `analyze.py --phase nlevel` until exit `0` (`nlevel_pass`) — fixes Nmax and pre-conditions micbnup before Cfall is swept (main re-tunes micbnup; see Stage: N-level)
- [ ] **Krb SA** (krb family) + `analyze.py --phase krb` until exit `0` (`krb_pass`) — locks Krb before Cfall (see Stage: Krb)
- [ ] Main iteration SA + `analyze.py --phase main` until exit `0` or branch (see Control flow)
- [ ] Rhmoist / soil branches when MINEC off-tier; snapshot before phase applies
- [ ] `param_update.py --phase main` **only** when main analyze exits `0` (`status: pass`) — apply before Nfall
- [ ] **Nfall SA** (nfall family) + `analyze.py --phase nfall` until exit `0` (`nfall_pass`) — **after** main `pass` is applied (see Stage: Nfall)
- [ ] Final `analyze.py --phase main` exit `0` → [`final-model-evaluation.md`](../agent_final_evaluation/final-model-evaluation.md)

All commands: `docker compose exec -T dvmdostem-autocal bash -c 'cd /work && ...'`

### VM concurrency

**One SA at a time per calibration VM.** Run stages sequentially (N-level → Krb → main → branches → Nfall): finish each `SA_setup_and_run.py`, run the matching `analyze.py`, then start the next yaml. Do **not** launch two SAs in parallel (e.g. Krb + main) to save wall time — observed on CH2 CMT73: ~11 workers hung 55–82 min, CPU stuck ~35% (11/32 cores), parent blocked before `results.csv`.

---

## Glossary

| Term | Meaning |
|------|---------|
| **Stage** | Section in this doc (Seed, N-level, Krb, Main SA, Rhmoist branch, Nfall, …) |
| **`analyze.py --phase`** | CLI gate scope: `main` (all targets+N+eq), `nlevel` (AVLN), `krb` (NPP), `nfall` (VEGNSTR), `phase6` (MINEC), `phase7` (SHLWC+DEEPC+MINEC) |
| **`propose_bounds.py --family`** | Param set for the target phase: `main` (soil+Cfall), `nlevel` (micbnup+Nmax), `krb` (Krb), `nfall` (Nfall). Every call also requires `--work-dir <prior SA dir>` (reads its `sample_matrix.csv`) and `--step2-result` (or `--veg-sample`) |
| **`param_update.py --phase`** | Must match analyze phase and `status` in `step2-result.yaml` |

---

## Control flow

### Calibration loop

The staged order below (N-level → Krb → main Cfall/soil → Nfall) follows
`docs_src/sphinx/source/calibration.rst`'s Nmax → Krb → Cfall → Nfall
sequence: each phase fixes one dimension of the N cycle before the next
phase's SA sweeps a different parameter set, so earlier-phase targets don't
drift once later phases start.

```
STAGE 0 — N-level (once per site, or whenever AVLN/N-ratio show up in
          main/krb/nfall misfit_classification.unreachable):
  LOOP: SA (nlevel family: micbnup + Nmax per PFT) → analyze --phase nlevel --biome {nitrogen_biome}
    on exit 0 (nlevel_pass): param_update --phase nlevel; break
    on exit 2: propose_bounds.py --family nlevel → repeat
    on exit 3: HALT for human review — AVLN outside envelope even with
               Nmax/micbnup swept wide; record unreachable target(s), document
               as structural/model limitation or revisit target value; do NOT
               reopen Step 1 automatically (see exit-3 note)

STAGE 1 — Krb (once per site, after nlevel_pass; re-run only if main-loop
          Cfall later regresses NPP):
  LOOP: SA (krb family: Krb(0/1/2) per PFT) → analyze --phase krb --biome {nitrogen_biome}
    on exit 0 (krb_pass): param_update --phase krb; break
    on exit 2: propose_bounds.py --family krb → repeat
    on exit 3: HALT for human review — NPP outside envelope even with Krb swept wide; document as structural/model limitation, do NOT reopen Step 1 automatically (see exit-3 note)

STAGE 2 — main iteration (Nmax/micbnup/Krb already fixed in parameters-step2):
LOOP main iteration:
  run main SA (soil Kdc*/micbnup + Cfall per PFT) → analyze.py --phase main --biome {nitrogen_biome}
  if any ft['column'].startswith('MINEC') for ft in failing_targets:
    cp -a parameters-step2 → parameters-step2-pre-phase6-{tag}
    LOOP rhmoist: SA → analyze --phase phase6
      on exit 0: param_update --phase phase6; break
    cp -a parameters-step2 → parameters-step2-pre-phase7-{tag}
    LOOP soil: SA → analyze --phase phase7
      on exit 0: param_update --phase phase7
      if MINEC regresses on next main analyze:
        restore pre-phase7 snapshot; re-apply phase6 from last phase6_pass; repeat soil loop
  if main exit 0: param_update.py --phase main   # required on pass; skip on exit 2/3
  elif main exit 2:
    if AVLN/N-ratio in misfit_classification.unreachable: go to STAGE 0 (Nmax/micbnup already
      set is not holding — re-widen there, not here); else if NPP in unreachable: go to STAGE 1
    else: propose_bounds.py --family main → repeat main SA
  elif main exit 3: HALT for human review — document unreachable target(s) as structural/model limitation; do NOT reopen Step 1 automatically (see exit-3 note)

STAGE 3 — Nfall (once per site, after main `pass` is applied):
  LOOP: SA (nfall family: Nfall(0/1/2) per PFT) → analyze --phase nfall --biome {nitrogen_biome}
    on exit 0 (nfall_pass): param_update --phase nfall; break
    on exit 2: propose_bounds.py --family nfall → repeat
    on exit 3: HALT for human review — VEGN outside envelope even with Nfall swept wide; document as structural/model limitation, do NOT reopen Step 1 automatically (see exit-3 note)

DONE when STAGE 3 nfall_pass is applied and a final analyze.py --phase main
(re-run after the Nfall apply, to confirm Nfall didn't regress anything main
gates on) exits 0
```

### Exit codes and apply (`analyze.py` + `param_update.py`)

| `analyze --phase` | Gated column(s) | exit `0` status | exit `2` | exit `3` (unreachable_min) | `param_update --phase` when exit `0` |
|-------------------|------------------|-----------------|----------|------------------------------|--------------------------------------|
| `nlevel` | `AVLN` (+ N-ratio, always checked) | `nlevel_pass` | `target_fit_review` | `unreachable_review` (≥1) | `nlevel` — `micbnup`, `nmax` only |
| `krb` | `NPP*` | `krb_pass` | `target_fit_review` | `unreachable_review` (≥1) | `krb` — `krb(0/1/2)` only |
| `main` | all targets | `pass` | `target_fit_review` | `unreachable_review` (≥3) | `main` — all `recommended_params` |
| `phase6` | `MINEC` | `phase6_pass` | `target_fit_review` | — | `phase6` — `rhmoistfrozen` only |
| `phase7` | `SHLWC`, `DEEPC`, `MINEC` | `phase7_pass` | `target_fit_review` | — | `phase7` — `micbnup`, `kdc*` only |
| `nfall` | `VEGNSTR*` | `nfall_pass` | `target_fit_review` | `unreachable_review` (≥1) | `nfall` — `nfall(0/1/2)` only |

Exit `1` = `failed` (missing CSVs). Phase modes skip eq gate; eq checked on final `--phase main`. `--force` on param_update overrides status (documented approval only).

On `nlevel`/`krb`/`nfall` exit `3`, the same rule as main exit `3` applies:
the dedicated parameter for that target has already been swept wide, so
widening bounds further is unlikely to help. **Exit 3 is a terminal HALT for
human review — not an agent branch, and not a trigger to reopen Step 1.**
Record the unreachable target(s) in the result and stop the phase: do not
loop, and do not reach back into Step 1 automatically. Step 2 is
self-contained — "unreachable" here means the observation fell outside the
model-output envelope this SA produced even after the controlling parameter
was swept wide, which points to either (a) a target value that needs
revisiting, or (b) a structural/model ceiling for that column at this site.
Reopening Step 1 (`cmax`) is a *human* decision reserved for one narrow
signature — VegCarbon or NPP unreachable **high** even after Krb is swept
wide, where `cmax` may be capping GPP — and is never performed by the agent
as part of this workflow (see **Do not**: "Re-sample `cmax`").

**Do not** `param_update --phase main` on `target_fit_review`. Phase applies require matching `phase` + status in the result yaml.

### Snapshot before phase apply

```bash
cp -a /data/workflows/CMT{NN}-{label}/parameters-step2 \
      /data/workflows/CMT{NN}-{label}/parameters-step2-pre-phase7-iter{N}
```

Restore on Phase 7 MINEC regression:

```bash
rm -rf .../parameters-step2
cp -a .../parameters-step2-pre-phase7-iter{N} .../parameters-step2
# then param_update --phase phase6 from last phase6_pass result if needed
```

### Immutable `parameters-step2`

- Created once by `seed_setup.py`; every SA uses the same `seed_path`
- Bounds from `sample_matrix.csv` / `propose_bounds.py` only — never main-apply mid-loop samples
- Phase 6/7 patch soil incrementally; main apply writes full `recommended_params` on pass
- `util.param.update_inplace` preserves all CMT blocks in multi-CMT files

### Acceptance (main `--phase main` only)

| Priority | Criterion | Gate |
|----------|-----------|------|
| 1 | N ratio | Hard — tundra 1.4–1.6, boreal 1.15–1.35 (`--biome`) |
| 2 | Per-target fit | Hard — NPP*/VEGC*/VEGNSTR* ≤10%, soil pools ≤20% (`failing_targets` if not) |
| 3 | Equilibrium | Hard except chronic whitelist: DEEPC, MINEC, VEGC_pft4_Root, AVLN |
| 4 | Bounds | Iterate — `propose_bounds.py`, plots; bulk RMSE alone ≠ pass |

Sample selection: fewest per-target tier failures among N-passing samples, then worst excess — not RMSE alone.

### Acceptance (`nlevel`/`krb`/`nfall` phases)

Same N-ratio + per-target-fit gates as main, restricted to that phase's
gated column(s) (Exit codes table above). Equilibrium is **not** required on
these phases (`require_eq_pass=False`) — it is only enforced on the final
`--phase main` pass. A phase status of `nlevel_pass`/`krb_pass`/`nfall_pass`
means: N-ratio in band AND the gated column(s) within tier, on the
best-scoring sample. It does **not** by itself mean the site is calibrated —
`main` still gates the full target set.

### `step2-result.yaml` (key fields)

`phase`, `status`, `recommended_params`, `best_sample_index`, `selected_n_pass`, `selected_n_ratio`, `failing_targets`, `failing_eq_vars`, `misfit_classification` (`unreachable`, `extinct_pool`), `target_residuals`.

Per iteration: `logs/sa-{SITE}-step2-iter{N}.yaml`, unique `work_dir`, `step2-result.yaml` from `--json-out`.

---

## File reference

| Role | Path |
|------|------|
| Targets | `/work/calibration/calibration_targets.py` |
| Seed dir | `/data/workflows/CMT{NN}-{site_label}/parameters-step2` |
| SA | `/work/mads_calibration/SA_setup_and_run.py` |
| Scripts | `seed_setup.py`, `burial_params_setup.py`, `analyze.py`, `propose_bounds.py`, `param_update.py` (this folder) |
| Plots / checks | `/work/mads_calibration/SA_post_hoc_analysis.py` |
| Templates | `sa-step2-template.yaml` (main), `sa-step2-nlevel-template.yaml`, `sa-step2-krb-template.yaml`, `sa-step2-nfall-template.yaml`, `sa-step2-rhmoistfrozen-template.yaml`, `sa-step2-soil-retune-template.yaml` |
| Agent yamls | `mads_calibration/logs/sa-{site_label}-*.yaml` (gitignored) |

---

## Stage: Seed setup

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/seed_setup.py \
    --step1-result /data/workflows/CMT04-IMN-sa-recovery-C/step1-result.yaml \
    --cmtnum 4 --dest /data/workflows/CMT04-IMN/parameters-step2'
```

## Stage: N-level (`--phase nlevel`)

Run once per site, right after seed setup and before the first main-loop SA
— this sets Nmax + micbnup jointly so actual GPP and AVLN land near target
before Cfall is ever swept (`docs_src/sphinx/source/calibration.rst` step 2).
Template: [`sa-step2-nlevel-template.yaml`](sa-step2-nlevel-template.yaml).
Params: `micbnup` (soil, `pftnum: null`) + `nmax` per active PFT from Step 1
`cmax_pft*` — use `propose_bounds.py --family nlevel`.

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'cd /work && python mads_calibration/SA_setup_and_run.py --force \
    mads_calibration/logs/sa-IMN-step2-nlevel-iter1.yaml'

docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/analyze.py \
    --phase nlevel --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-nlevel-iter1/ \
    --biome tundra \
    --json-out /data/workflows/CMT04-IMN/logs/sa-step2-nlevel-iter1/step2-result.yaml'

# on exit 0 (nlevel_pass):
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/param_update.py \
    --phase nlevel \
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-nlevel-iter1/step2-result.yaml \
    --param-dir /data/workflows/CMT04-IMN/parameters-step2 --cmtnum 4'
```

On exit `2`: `propose_bounds.py --work-dir <this SA's work_dir> --family nlevel --step2-result <that work_dir>/step2-result.yaml --yaml-out mads_calibration/logs/sa-IMN-step2-nlevel-iter{N+1}-bounds.yaml`, then paste `p_bounds` into a fresh iter yaml with a new `work_dir` and repeat. (`--work-dir` is **required** — it reads the prior SA's `sample_matrix.csv` to center the new bounds; `--step2-result` supplies `best_sample_index`.) On exit `3`: stop, do not keep widening — see Control flow.

## Stage: Krb (`--phase krb`)

Run once per site, after `nlevel_pass` is applied and before (or alongside)
the first main-loop Cfall SA — Krb sets the GPP:NPP ratio via maintenance
respiration and should be fixed before Cfall (`calibration.rst` step 3).
Template: [`sa-step2-krb-template.yaml`](sa-step2-krb-template.yaml). Params:
`krb(0)/krb(1)/krb(2)` per active PFT — use `propose_bounds.py --family krb`.
Krb values in `cmt_calparbgc.txt` are negative; keep bounds negative.

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'cd /work && python mads_calibration/SA_setup_and_run.py --force \
    mads_calibration/logs/sa-IMN-step2-krb-iter1.yaml'

docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/analyze.py \
    --phase krb --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-krb-iter1/ \
    --biome tundra \
    --json-out /data/workflows/CMT04-IMN/logs/sa-step2-krb-iter1/step2-result.yaml'

# on exit 0 (krb_pass):
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/param_update.py \
    --phase krb \
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-krb-iter1/step2-result.yaml \
    --param-dir /data/workflows/CMT04-IMN/parameters-step2 --cmtnum 4'
```

On exit `2`: `propose_bounds.py --work-dir <this SA's work_dir> --family krb --step2-result <that work_dir>/step2-result.yaml --yaml-out mads_calibration/logs/sa-IMN-step2-krb-iter{N+1}-bounds.yaml`, then paste `p_bounds` into a fresh iter yaml with a new `work_dir` and repeat. (`--work-dir` is **required**.) On exit `3`: stop — see Control flow.

## Stage: Main SA

Validate CMT in `calibration_targets.py`. `target_names` covers the calibratable Step 2 set — `CarbonShallow`, `CarbonDeep`, `CarbonMineralSum`, `AvailableNitrogenSum`, `OrganicNitrogenSum`, `VegCarbon`, `NPPAll`. RECO (`EcosystemRespiration`) is **not** a defined target in `calibration_targets.py`, so keep it as a diagnostic aux_output (`RECO y`, as in the base template) — do **not** add it to `target_names` unless you first define an `EcosystemRespiration` target on the CMT block (else the SA fails; see Failure modes). Params: 5 soil (`micbnup`, `kdc*`) + 3 `cfall` per active PFT from Step 1 `cmax_pft*`. Run **after** `nlevel_pass`/`krb_pass` are applied — Nmax and Krb are fixed in `parameters-step2` by this point; micbnup starts from its nlevel value and is re-tuned by this phase.

Copy [`sa-step2-template.yaml`](sa-step2-template.yaml) → `logs/sa-{site_label}-step2.yaml`. Required: `seed_path`, `calib_mode: VEGC`, `aux_outputs: [INGPP y, GPP y]`, `--eq-yrs 2000`, soil + `cfall`. First pass: `percent_diffs: 0.95`; later: `p_bounds` only.

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'cd /work && python mads_calibration/SA_setup_and_run.py --force \
    mads_calibration/logs/sa-IMN-step2-iter3.yaml'
```

## Stage: Analyze (main)

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/analyze.py \
    --phase main --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-iter3/ \
    --biome tundra --save-plots \
    --json-out /data/workflows/CMT04-IMN/logs/sa-step2-iter3/step2-result.yaml'
```

## Stage: Next iteration

1. Copy prior yaml → `iter{N}`; new `work_dir`
2. `propose_bounds.py --work-dir <prior main SA work_dir> --family main --step2-result <that work_dir>/step2-result.yaml --step1-result <step1-result.yaml> --yaml-out mads_calibration/logs/sa-IMN-step2-iter{N}-bounds.yaml` → `p_bounds` fragment. `--work-dir` and `--step2-result` are **required** (`--step1-result` only supplies the active-PFT count for `cfall`/PFT params)
3. Remove `percent_diffs`; add `p_bounds`; `--dry-run` then `--force` SA

## Stage: Main apply

On `analyze.py --phase main` exit `0` only — **always** apply:

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/param_update.py \
    --phase main \
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-iter3/step2-result.yaml \
    --param-dir /data/workflows/CMT04-IMN/parameters-step2 --cmtnum 4'
```

## Stage: Rhmoist branch (`--phase phase6`)

When `failing_targets` has a column starting with `MINEC`. Template: [`sa-step2-rhmoistfrozen-template.yaml`](sa-step2-rhmoistfrozen-template.yaml). `plot_relationships(..., variables=["rhmoistfrozen"])` — if insensitive, document and skip apply.

```bash
# after SA + snapshot:
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/analyze.py \
    --phase phase6 --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-rhmoistfrozen/ \
    --biome tundra \
    --json-out /data/workflows/CMT04-IMN/logs/sa-step2-rhmoistfrozen/step2-result.yaml'

docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/param_update.py \
    --phase phase6 \
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-rhmoistfrozen/step2-result.yaml \
    --param-dir /data/workflows/CMT04-IMN/parameters-step2 --cmtnum 4'
```

## Stage: Soil retune (`--phase phase7`)

Required after Phase 6 apply. Template: [`sa-step2-soil-retune-template.yaml`](sa-step2-soil-retune-template.yaml) (5 soil params only: `micbnup` + `kdc*`). Bounds: `propose_bounds.py --work-dir <last main-loop SA work_dir> --family main --step2-result <that work_dir>/step2-result.yaml --soil-span 0.20 --yaml-out ...`. `--family main` emits soil **then** `cfall` bounds in `PARAM_FAMILIES` order (`micbnup, kdcrawc, kdcsoma, kdcsompr, kdcsomcr, cfall...`) — copy only the **first 5** (soil) `p_bounds` entries into the soil-retune yaml so `p_bounds` length matches its 5 params. Snapshot before apply (Control flow).

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/analyze.py \
    --phase phase7 --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-soil-retune/ \
    --biome tundra \
    --json-out /data/workflows/CMT04-IMN/logs/sa-step2-soil-retune/step2-result.yaml'

docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/param_update.py \
    --phase phase7 \
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-soil-retune/step2-result.yaml \
    --param-dir /data/workflows/CMT04-IMN/parameters-step2 --cmtnum 4'
```

## Stage: Nfall (`--phase nfall`)

Run once per site, after main `status: pass` has been applied — Nfall is
the N-side counterpart of Cfall and targets VEGN
(`calibration.rst` step 5); running it before Cfall/VEGC has settled means
sweeping against a moving target. Template:
[`sa-step2-nfall-template.yaml`](sa-step2-nfall-template.yaml). Params:
`nfall(0)/nfall(1)/nfall(2)` per active PFT — use `propose_bounds.py --family nfall`.

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'cd /work && python mads_calibration/SA_setup_and_run.py --force \
    mads_calibration/logs/sa-IMN-step2-nfall-iter1.yaml'

docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/analyze.py \
    --phase nfall --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-nfall-iter1/ \
    --biome tundra \
    --json-out /data/workflows/CMT04-IMN/logs/sa-step2-nfall-iter1/step2-result.yaml'

# on exit 0 (nfall_pass):
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/agent_calibration_step2/param_update.py \
    --phase nfall \
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-nfall-iter1/step2-result.yaml \
    --param-dir /data/workflows/CMT04-IMN/parameters-step2 --cmtnum 4'
```

On exit `2`: `propose_bounds.py --work-dir <this SA's work_dir> --family nfall --step2-result <that work_dir>/step2-result.yaml --yaml-out mads_calibration/logs/sa-IMN-step2-nfall-iter{N+1}-bounds.yaml`, then paste `p_bounds` into a fresh iter yaml with a new `work_dir` and repeat. (`--work-dir` is **required**.) On exit `3`: stop — see Control flow.

After applying `nfall_pass`, re-run `analyze.py --phase main` once more
(no new SA needed — reuse the last main `work_dir`/results if Nfall cannot
change main-gated columns, or re-run main SA if in doubt) to confirm N-ratio
and per-target fit still hold before final evaluation.

---

## Sensitivity diagnostics

After each SA, from [`SA_post_hoc_analysis.py`](../SA_post_hoc_analysis.py): `nitrogen_check`, `plot_relationships`, `plot_pft_matrix`, `plot_equilibrium_relationships` on `failing_targets` columns.

---

## Diagnosis (`step2-result.yaml` → action)

| Signal | Action |
|--------|--------|
| exit `2`, `failing_targets` | Iterate bounds (`propose_bounds.py`); branch rhmoist/soil if MINEC off-tier |
| `AVLN`/N-ratio in `misfit_classification.unreachable` on `main` | Nmax/micbnup already fixed isn't holding — go to Stage: N-level, not more main-loop bounds iteration |
| `NPP*` in `misfit_classification.unreachable` on `main` | Go to Stage: Krb, not more main-loop bounds iteration |
| `VEGNSTR*` in `misfit_classification.unreachable` | Go to Stage: Nfall (only reachable after main `pass`) |
| `misfit_classification.unreachable` on `nlevel`/`krb`/`nfall` phase | The dedicated param for that target is already being swept — widening bounds rarely helps; treat as exit `3` (see below) |
| ≥3 unreachable on main analyze | exit `3` — HALT for human review; document as structural/model limitation; do not iterate bounds alone and do not reopen Step 1 automatically (see exit-3 note) |
| ≥1 unreachable on `nlevel`/`krb`/`nfall` analyze | exit `3` — HALT for human review; document / revisit target; do not iterate that phase's bounds alone (`cmax` reopen is a narrow human decision — see exit-3 note) |
| `misfit_classification.extinct_pool` | Mod ≈ 0, obs large — document limitation; rarely fixable |
| Chronic eq fail on whitelist vars | Allowed on main pass (see Acceptance table) |

---

## Failure modes

| Symptom | Action |
|---------|--------|
| CPU ~30–40% flat, SA hours with no `results.csv` | Hung `dvmdostem` workers — only one SA should run per VM; kill stuck PIDs, verify all `sample_*/output/` complete, then `post_hoc_build_all()` or re-run SA with `--force` |
| Parallel SAs launched (Krb + main, etc.) | Stop extras; run one phase to completion before the next |
| `analyze.py` exit `1` | Fix SA / missing CSVs |
| No N-passing samples | Rank full pool; note in result; iterate bounds |
| Phase 7 regresses MINEC | Restore snapshot; re-apply phase6; repeat phase7 |
| `p_bounds` length mismatch | Regenerate with `propose_bounds.py --work-dir ... --step2-result ...` + matching `--family` (`--step1-result` sets PFT count); for phase7 slice only the 5 soil entries |
| Main-loop AVLN/N-ratio/NPP unreachable, N-level/Krb never run | Structural gap — run Stage: N-level / Stage: Krb before iterating main bounds further |
| VEGN never assessed at all | Structural gap — run Stage: Nfall after main `pass`; `VegStructuralNitrogen` must be a `target_names` entry somewhere in the sequence |
| TR crash in final eval | `--tr-yrs` ≤ historic climate length |
| `EcosystemRespiration` missing in CMT | Remove from `target_names` or add to `calibration_targets.py` |

---

## Do not

- Run more than one `SA_setup_and_run.py` concurrently on the same VM
- Re-sample `cmax` or edit `/work/parameters` in the repo
- `param_update --phase main` unless main analyze exit `0` (`pass`)
- `param_update --phase phase6|phase7` without snapshot + matching phase pass
- `param_update --phase nlevel|krb|nfall` unless that phase's analyze exit `0` (`nlevel_pass`/`krb_pass`/`nfall_pass`)
- Try to fix AVLN/N-ratio, NPP, or VEGN misfits by widening `main`-phase soil/Cfall bounds alone — Nmax, Krb, and Nfall are not sampled by `main`; use the dedicated phase
- Run Stage: Nfall before a main `pass` has been applied (Cfall/VEGC should settle first)
- Skip `aux_outputs` for INGPP/GPP; skip Phase 7 after Phase 6 apply without documented MINEC insensitivity
- Commit `logs/`

---

## Filename reference

| Incorrect | Correct |
|-----------|---------|
| `step2-integrated-agent.md` | `agent-instructions-step2.md` |
| `step1-to-step2-transition.md` | `step1-transition.md` |
| `step2_seed_setup.py` | `seed_setup.py`, `burial_params_setup.py`, `analyze.py`, `propose_bounds.py`, `param_update.py` |

Closure summary: [`step2-closure-summary-template.yaml`](../agent_final_evaluation/step2-closure-summary-template.yaml) → `logs/{site_label}-step2-closure-summary.yaml`.