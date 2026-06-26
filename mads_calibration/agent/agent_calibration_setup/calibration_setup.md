# Phase 0 — Calibration Setup (GCS → local)

Attach this file in Cursor (`@calibration_setup.md`) **before** `@step1-cmax-agent.md`.

Automate **Phase 0** of the MADS agent calibration workflow: provision driving inputs and parameter seeds from GCS, build a per-site `config/config.js`, verify site/input/parameter mapping, and write a setup manifest for Step 1. Run entirely inside the `dvmdostem-autocal` Docker container (or host with `gsutil` auth and mounted volumes). **Do not** run sensitivity analysis from this instruction set.

**Step 1** continues in [`step1-cmax-agent.md`](../agent_calibration_step1/step1-cmax-agent.md). Folder overview: [`README.md`](README.md).

## Directory layout

| Location | Tracked | Agent use |
|----------|---------|-----------|
| `agent/agent_calibration_setup/` (this folder) | Yes | Setup script, aliases, templates |
| `logs/` | **No** (gitignored) | `{site_label}-setup-manifest.yaml` |
| `/data/input-catalog/` | Runtime volume | Synced driving inputs from GCS |
| `/data/workflows/CMT{NN}-{label}/` | Runtime volume | `parameters-seed/`, `setup/config/config.js` |

Do not commit files under `logs/`.

## Minimum user action

Provide these three inputs, then run the setup agent against this instruction set:

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

**Naming is not 1:1.** Input folders use site names (`Imnavait`, `trail_valley`). Parameter folders encode site token + CMT (`IMN_CMT05`, `TVC_CMT50`, `Cherskii_CMT73`, legacy `parameters75`). Known pairs are listed in [`site_aliases.yaml`](site_aliases.yaml).

**Important:** Imnavait has calibrated params as `IMN_CMT05` (CMT05) while Step 1 often calibrates **CMT04** at that site. Always use **user-specified `cmtnum`**; when bucket CMT differs, `calibration_setup.py` falls back to `/work/parameters` and records a warning.

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
  'python /work/mads_calibration/agent/agent_calibration_setup/calibration_setup.py --discover'
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
  'python /work/mads_calibration/agent/agent_calibration_setup/calibration_setup.py \
    --site-name Imnavait \
    --cmtnum 4 \
    --site-label IMN \
    --force \
    --json-out mads_calibration/logs/IMN-setup-manifest.yaml'
```

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
| `warnings` | Review CMT mismatch, missing projected climate, param fallback |

### Exit codes (`calibration_setup.py`)

| Exit | `status` | Meaning | Agent action |
|------|----------|---------|--------------|
| `0` | `pass` | Setup complete | Proceed to Step 1 |
| `2` | `warn` | Usable with documented warnings (e.g. param fallback, eq-only inputs) | Proceed to Step 1; carry warnings forward |
| `1` | `failed` | Missing inputs, bad config, or CMT not in targets | Fix and re-run setup |

---

## Output contract

Write manifest via `--json-out` to `mads_calibration/logs/{site_label}-setup-manifest.yaml`:

```yaml
site_name: Imnavait
site_label: IMN
cmtnum: 4
site: /data/input-catalog/Imnavait
PXx: 0
PXy: 0
seed_path: /work/parameters
setup_dir: /data/workflows/CMT04-IMN/setup
config_js: /data/workflows/CMT04-IMN/setup/config/config.js
input_bucket: gs://dvmdostem_calibration_input/Imnavait
param_bucket: null
param_folder: null
param_cmt_in_file: 5
workflow_dir: /data/workflows/CMT04-IMN
status: warn
warnings:
  - Param folder IMN_CMT05 is CMT5 but user requested CMT4; using /work/parameters as seed_path instead.
```

See [`setup-manifest-template.yaml`](setup-manifest-template.yaml) for field descriptions.

---

## Handoff to Step 1

After setup completes, attach [`step1-cmax-agent.md`](../agent_calibration_step1/step1-cmax-agent.md) and pass manifest fields:

```yaml
cmtnum: 4                    # from manifest
site: /data/input-catalog/Imnavait
PXx: 0
PXy: 0
site_label: IMN
seed_path: /work/parameters  # from manifest seed_path
setup_manifest: mads_calibration/logs/IMN-setup-manifest.yaml
```

When filling [`sa-step1-template.yaml`](../agent_calibration_step1/sa-step1-template.yaml), use `seed_path` and `site` from the manifest. SA runs auto-generate per-sample `config/config.js`; the site-level `setup/config/config.js` is the verified reference.

---

## Failure modes

| Symptom | Action |
|---------|--------|
| `gsutil` / `gcloud` auth error | Run `gcloud auth application-default login`; ensure SDK on PATH in the execution environment |
| Site not in input bucket | Re-run `--discover`; confirm `site_name` spelling |
| No param folder for site | Expected for new sites; uses `/work/parameters` — note in manifest |
| Bucket param CMT ≠ user `cmtnum` | Expected (e.g. Imnavait CMT04 vs IMN_CMT05); repo fallback — note in manifest |
| CMT not in `calibration_targets.py` | Stop; add targets or choose valid `cmtnum` |
| Missing projected climate | Warn only for eq-only Step 1 SA |
| `vegetation.nc` CMT mismatch at pixel | Warn; confirm `PXx`/`PXy` or forcing CMT intent |
| `config.js` paths wrong | Re-run setup with `--force` |

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

| Draft / incorrect name | Correct path |
|------------------------|--------------|
| `setup.md` | `calibration_setup.md` |
| `phase0-setup.md` | `calibration_setup.md` |
| Setup manifest | `mads_calibration/logs/{site_label}-setup-manifest.yaml` |
| Step 1 after setup | `agent/agent_calibration_step1/step1-cmax-agent.md` |
