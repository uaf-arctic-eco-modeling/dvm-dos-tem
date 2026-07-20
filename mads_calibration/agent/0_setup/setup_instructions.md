# Agent calibration harness — Phase 0 setup

Instruction-driven workflow for MADS calibration (Phase 0 → Step 1 `cmax` → Step 2 staged → final evaluation). Works with any **coding agent** that can read markdown instructions and run shell commands on the calibration host (Cursor, Claude Code, Antigravity, etc.).

Path: `mads_calibration/agent/0_setup/setup_instructions.md`

## Execution environment

Run the agent on a host that can execute commands inside the `dvmdostem-autocal` Docker container with `/work`, `/data/input-catalog`, and `/data/workflows` mounted. Typical setup: GCP calibration VM with the repo checked out and Docker Compose running.

The agent needs **shell access on that host**. If the agent UI runs elsewhere (IDE cloud session, separate agent runtime), connect it to the calibration VM as its execution worker — do not rely on a local SSH session that the agent cannot reach. Examples: Cursor **My Machines** on the VM; Claude Code or Antigravity opened in / attached to the VM workspace.

## Using this harness

Load **one phase instruction file at a time**, in order (paths relative to `mads_calibration/agent/`):

1. [`0_setup/setup_instructions.md`](setup_instructions.md) (Phase 0 — this file)
2. [`1_cmax/cmax_instructions.md`](../1_cmax/cmax_instructions.md) (Step 1 `cmax`)
3. [`2_calibration/calibration_instructions.md`](../2_calibration/calibration_instructions.md) (Step 2 staged)
4. [`3_evaluation/evaluation_instructions.md`](../3_evaluation/evaluation_instructions.md) (transient validation)

| Agent | Typical pattern |
|-------|-----------------|
| **Cursor** | `@mads_calibration/agent/0_setup/setup_instructions.md` in chat |
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

Step 2 order: **nlevel → krb → cfall → nfall → soil**. See [`2_calibration/calibration_instructions.md`](../2_calibration/calibration_instructions.md).

Immutable `parameters-step2`: fixed `seed_path` for all SA iterations; bounds from `propose_bounds.py` / `sample_matrix.csv` only.

Shared helper [`2_calibration/eq_workdir.py`](../2_calibration/eq_workdir.py) — equilibrium gates from collated `eq_*_quality.csv` in SA `work_dir` (imported by Step 1/2 analyze scripts).

Runtime configs and manifests: `mads_calibration/logs/` (gitignored).

---

# Phase 0 — Calibration Setup (GCS → local)

Automate **Phase 0** of the MADS agent calibration workflow: provision driving inputs and parameter seeds from GCS, build a per-site `config/config.js`, verify site/input/parameter mapping, and write a setup manifest for Step 1. Run entirely inside the `dvmdostem-autocal` Docker container (or host with `gsutil` auth and mounted volumes). **Do not** run sensitivity analysis from this instruction set.

**Step 1** continues in [`cmax_instructions.md`](../1_cmax/cmax_instructions.md).

## Directory layout

| Location | Tracked | Agent use |
|----------|---------|-----------|
| `agent/0_setup/` (this folder) | Yes | Setup script, aliases, templates |
| `logs/` | **No** (gitignored) | `{site_label}-setup-manifest.yaml` |
| `/data/input-catalog/` | Runtime volume | Synced driving inputs from GCS |
| `/data/workflows/CMT{NN}-{label}/` | Runtime volume | `parameters-seed/`, `setup/config/config.js` |

Do not commit files under `logs/`.

## Multisite conventions

Every site uses the same path pattern — substitute `{cmtnum}`, `{site_label}`, and `{site_name}` from user inputs or the setup manifest:

| Token | Meaning | Example |
|-------|---------|---------|
| `{site_name}` | GCS input folder name | `Imnavait`, `trail_valley`, `Cherskii` |
| `{site_label}` | Short unique workflow token | `IMN`, `TVC`, `EML`, `CHS` |
| `{cmtnum}` | Calibration CMT integer | `4`, `50`, `73` |
| `{workflow}` | `/data/workflows/CMT{cmtnum:02d}-{site_label}` | `/data/workflows/CMT04-IMN` |
| `{site}` | Local input path | `/data/input-catalog/{site_name}` |

Manifests and SA configs are keyed by `{site_label}` under `mads_calibration/logs/`. Run **one site’s SA at a time** per VM (see [SA concurrency](#sa-concurrency-per-vm)). To calibrate multiple sites, repeat the full harness (Phase 0 → evaluation) for each `{site_label}`.

## Minimum user action

Provide these three inputs (example shown; any valid site/CMT pair works), then run the setup agent against this instruction set:

```yaml
site_name: Imnavait      # GCS input folder name under dvmdostem_calibration_input
cmtnum: 4                # calibration CMT (must match calibration_targets.py)
site_label: IMN          # short token for workflow paths
```

Optional overrides: `PXx`, `PXy` (default: first active cell in `run-mask.nc`, else `0,0`).

## Quick checklist

- [ ] `dvmdostem-autocal` running; `/data/input-catalog` and `/data/workflows` mounted
- [ ] `gcloud` / `gsutil` authenticated (`gcloud auth application-default login` on host if needed)
- [ ] User specified `site_name`, `cmtnum`, `site_label`
- [ ] Setup manifest written to `logs/{site_label}-setup-manifest.yaml` with `status: pass` or documented `warn`
- [ ] Hand off manifest fields to Step 1 agent

---

## Role and goal

You are a **calibration setup agent**. Given a site name, CMT number, and site label, you will:

1. Discover or confirm site ↔ input ↔ parameter mapping across two GCS buckets.
2. Sync driving inputs and (when CMT-aligned) calibrated parameter files to local workflow paths.
3. Build a site-level `config/config.js` via `setup_working_directory.py`.
4. Verify inputs, targets, vegetation CMT at pixel, and config paths.
5. Write a setup manifest yaml for the Step 1 agent.

**Success criterion:** manifest `status` is `pass` or `warn` (exit `0` or `2` from `calibration_setup.py`); `failed` (exit `1`) blocks Step 1 until resolved.

**Do not** edit the repo-root [`config/config.js`](../../config/config.js) — it is a demo template. Per-site config lives under `{workflow_dir}/setup/config/config.js`.

---

## GCS bucket reference

Two buckets serve **different** purposes. Do not conflate them.

| Bucket | Console | Contents |
|--------|---------|----------|
| **Driving inputs** | [dvmdostem_calibration_input](https://console.cloud.google.com/storage/browser/dvmdostem_calibration_input) | NetCDF driver files per site folder (`historic-climate.nc`, `vegetation.nc`, etc.) — used for `config.js` IO paths |
| **Calibrated parameters** | [vb-tem/.../calibrated](https://console.cloud.google.com/storage/browser/vb-tem/Calibration/calibration_files/calibrated) | Per-site parameter trees (`cmt_calparbgc.txt`, `cmt_bgcsoil.txt`, …) — used for `seed_path` when CMT matches |
| **Observation targets** | [vb-tem/Calibration/calibration_targets.py](https://console.cloud.google.com/storage/browser/vb-tem/Calibration) | Field/ecosystem targets consumed by SA via `observations: /work/calibration` (see below) |

**Naming is not 1:1.** Input folders use site names (`Imnavait`, `trail_valley`). Parameter folders encode site token + CMT (`IMN_CMT05`, `TVC_CMT50`, `Cherskii_CMT73`, legacy `parameters75`). Known pairs are listed in [`site_aliases.yaml`](site_aliases.yaml).

### Observation targets (`calibration_targets.py`)

SA and setup read **`/work/calibration/calibration_targets.py`** (repo copy). Each CMT block must include at least `GPPAllIgnoringNitrogen` for Step 1.

| Source | Path | Scope |
|--------|------|-------|
| **Master (preferred sync)** | `gs://vb-tem/Calibration/calibration_targets.py` | 34 CMTs — includes Chersky (73), TVC (50–52), SCC (60–61), Chokurdakh (70), Yakutsk (71), Zotino (74), etc. |
| **AGU snapshots** | `gs://vb-tem/AGU/{EML,IMN,MD1,SCC,TVC}/calibration/calibration_targets.py` | 24 CMTs — superset of repo legacy entries; **does not** include CMT73 |
| **Repo** | `calibration/calibration_targets.py` | Must be kept in sync with master when calibrating CMTs absent from an older checkout |

Sync master targets into the repo (host or container with `gsutil`):

```bash
gsutil cp gs://vb-tem/Calibration/calibration_targets.py \
  /work/calibration/calibration_targets.py
```

Alternatively, point SA yaml `observations:` at any directory containing a site-specific copy (agent runs normally use `/work/calibration`).

**Important:** Imnavait has calibrated params as `IMN_CMT05` (CMT05) while Step 1 often calibrates **CMT04** at that site. Always use **user-specified `cmtnum`**. When bucket CMT differs from `cmtnum`, setup **fails** (exit `1`) — **no cross-CMT fallback** to `/work/parameters`.

---

## Prerequisites

Before starting, confirm:

- Docker Compose is running and `dvmdostem-autocal` container is up.
- Image built: `dvmdostem-autocal:${V_TAG}` (see root [`docker-compose.yml`](../../docker-compose.yml)).
- `/work` is mounted to the repo; `/data/input-catalog` and `/data/workflows` are mounted.
- `gsutil` or `gcloud` on PATH with access to both buckets (install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) in the container if missing; on some hosts only `gcloud storage` is available)
- Python dependencies are pre-installed — **do not** `pip install`.

All commands below use:

```bash
docker compose exec -T dvmdostem-autocal bash -c 'cd /work && ...'
```

---

## File reference

| Role | Path | Purpose |
|------|------|---------|
| Setup CLI | [`calibration_setup.py`](calibration_setup.py) | Discover, sync, verify, write manifest |
| Site aliases | [`site_aliases.yaml`](site_aliases.yaml) | Known input folder → param folder mappings |
| Manifest template | [`setup-manifest-template.yaml`](setup-manifest-template.yaml) | Output contract schema |
| Working dir bootstrap | `/work/scripts/util/setup_working_directory.py` | Creates `setup/` with `config/config.js` |
| Run mask util | `/work/scripts/util/runmask-util.py` | Reset mask to single pixel |
| Field targets | `/work/calibration/calibration_targets.py` | CMT must exist with `GPPAllIgnoringNitrogen` |
| Repo parameter fallback | `/work/parameters` | Used when bucket params missing or CMT mismatch |
| Setup manifest (per run) | `mads_calibration/logs/{site_label}-setup-manifest.yaml` | Gitignored handoff artifact |

---

## Phase 1 — Discovery

List available sites and parameter-folder crosswalk:

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/0_setup/calibration_setup.py --discover'
```

Review the table. For the user's `site_name`:

- Confirm the input folder exists in `dvmdostem_calibration_input`.
- Note param folder candidates from aliases and heuristics.
- Flag if no candidate matches user `cmtnum` (expect `/work/parameters` fallback).

Extend [`site_aliases.yaml`](site_aliases.yaml) when you validate a new mapping.

---

## Phase 2 — Run setup

Preferred: use the headless CLI (implements Phases 2–5 below):

```bash
docker compose exec -T dvmdostem-autocal bash -c \
  'python /work/mads_calibration/agent/0_setup/calibration_setup.py \
    --site-name {site_name} \
    --cmtnum {cmtnum} \
    --site-label {site_label} \
    --force \
    --json-out mads_calibration/logs/{site_label}-setup-manifest.yaml'
```

Example (CMT04 Imnavait): `--site-name Imnavait --cmtnum 4 --site-label IMN`.

| Flag | Purpose |
|------|---------|
| `--force` | Overwrite existing `parameters-seed/` and `setup/` |
| `--skip-sync` | Use existing local files; skip GCS rsync (aliases still used for param mapping) |
| `--dry-run` | Print actions without syncing or writing |
| `--pxx` / `--pxy` | Override grid cell (default: first active in run-mask) |
| `--dest-input` | Override local input path (default: `/data/input-catalog/{site_name}`) |
| `--dest-workflow` | Override workflow base (default: `/data/workflows/CMT{NN}-{label}`) |

### What the script does

1. **Sync inputs:** `gsutil -m rsync -r gs://dvmdostem_calibration_input/{site_name}/` → `/data/input-catalog/{site_name}/`
2. **Sync parameters:** If a calibrated folder matches site **and** CMT → `parameters-seed/`; else `seed_path` = `/work/parameters`
3. **Build config:** `setup_working_directory.py {workflow_dir}/setup --input-data-path {site} --seed-parameters {seed_path} --no-cal-targets`
4. **Run mask:** `runmask-util.py --reset --yx {PXy} {PXx}` on `setup/run-mask.nc`
5. **Verify:** input files, `calibration_targets.py`, `vegetation.nc` CMT at pixel, `config.js` paths

---

## Phase 3 — Verify manifest

Read `logs/{site_label}-setup-manifest.yaml` and confirm:

| Field | Expected |
|-------|----------|
| `site` | `/data/input-catalog/{site_name}` exists with eq-calibration NetCDFs |
| `seed_path` | `parameters-seed/` or `/work/parameters` |
| `config_js` | IO paths point under `site` |
| `PXx`, `PXy` | Active pixel; `vegetation.nc` CMT matches `cmtnum` (warn if not) |
| `status` | `pass` or `warn` — not `failed` |
| `warnings` | Review missing projected climate; **CMT mismatch is now `failed`, not warn** |
| `seed_path` | Must contain `cmt_calparbgc.txt` block for requested `cmtnum` |

### Exit codes (`calibration_setup.py`)

| Exit | `status` | Meaning | Agent action |
|------|----------|---------|--------------|
| `0` | `pass` | Setup complete | Proceed to Step 1 |
| `2` | `warn` | Usable with documented warnings (e.g. eq-only inputs, repo seed when no GCS folder) | Proceed to Step 1; carry warnings forward |
| `1` | `failed` | Missing inputs, bad config, CMT not in targets, **cross-CMT param mismatch**, or seed missing requested CMT block | Fix mapping or `cmtnum`; re-run setup |

---

## Output contract

Write manifest via `--json-out` to `mads_calibration/logs/{site_label}-setup-manifest.yaml`:

```yaml
# Example manifest (failed cross-CMT case). Replace values per site.
site_name: Imnavait
site_label: IMN
cmtnum: 4
site: /data/input-catalog/Imnavait
PXx: 0
PXy: 0
seed_path: /work/parameters
setup_dir: /data/workflows/CMT04-IMN/setup
config_js: /data/workflows/CMT04-IMN/setup/config/config.js
workflow_dir: /data/workflows/CMT04-IMN
status: failed
warnings:
  - Param folder IMN_CMT05 is CMT5 but user requested CMT4; cross-CMT parameter fallback is not allowed.
```

See [`setup-manifest-template.yaml`](setup-manifest-template.yaml) for field descriptions.

---

## Handoff to Step 1

After setup completes, load [`cmax_instructions.md`](../1_cmax/cmax_instructions.md) and pass manifest fields:

```yaml
# From manifest — substitute per site
cmtnum: {cmtnum}
site: {site}                 # e.g. /data/input-catalog/Imnavait
PXx: {PXx}
PXy: {PXy}
site_label: {site_label}
seed_path: {seed_path}       # from manifest
setup_manifest: mads_calibration/logs/{site_label}-setup-manifest.yaml
```

When filling [`sa-step1-template.yaml`](../1_cmax/sa-step1-template.yaml), use `seed_path` and `site` from the manifest. SA runs auto-generate per-sample `config/config.js`; the site-level `setup/config/config.js` is the verified reference.

---

## Failure modes

| Symptom | Action |
|---------|--------|
| `gsutil` / `gcloud` auth error | Run `gcloud auth application-default login`; ensure SDK on PATH in the execution environment |
| Site not in input bucket | Re-run `--discover`; confirm `site_name` spelling |
| No param folder for site | Uses `/work/parameters` only if it contains the requested CMT block; else **failed** |
| Bucket param CMT ≠ user `cmtnum` | **Setup fails** — add alias for correct folder or use matching `cmtnum` |
| CMT not in `calibration_targets.py` | Sync `gs://vb-tem/Calibration/calibration_targets.py` → `/work/calibration/` (see **Observation targets** above); re-run setup |
| Missing projected climate | Warn only for eq-only Step 1 SA |
| `vegetation.nc` CMT mismatch at pixel | Warn; confirm `PXx`/`PXy` or forcing CMT intent |
| `config.js` paths wrong | Re-run setup with `--force` |

---

## Script enforcement

| Rule | Enforcement |
|------|-------------|
| No cross-CMT parameter fallback | If GCS param folder or `cmt_calparbgc.txt` CMT ≠ user `cmtnum` → manifest `status: failed`, exit `1` |
| Seed must match site CMT | `verify_param_dir_has_cmt(seed_path, cmtnum)` before handoff |
| Step 1 blocked on setup failure | Do not start Step 1 when setup exit `1` |

---

## Do not

- Run Step 1 SA or `SA_setup_and_run.py` from this instruction set
- Edit repo-root `config/config.js`
- Infer `cmtnum` solely from bucket folder names
- Modify `calibration/calibration_targets.py` during setup
- Commit `logs/` (gitignored)
- Run `pip install` inside the container

---

## Filename reference

| Artifact | Path |
|----------|------|
| Setup manifest | `mads_calibration/logs/{site_label}-setup-manifest.yaml` |
| Step 1 after setup | `agent/1_cmax/cmax_instructions.md` |
