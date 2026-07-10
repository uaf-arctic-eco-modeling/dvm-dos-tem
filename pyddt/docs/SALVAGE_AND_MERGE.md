# Salvaging and Merging Failed Batch Runs

This document describes how to use the `pyddt-salvage` and `pyddt-merge` utilities to recover from partial batch run failures in dvmdostem.

## Problem

When running dvmdostem on a batch of grid cells (e.g., 10 cells), some cells may fail while others complete successfully. Without these tools, you would need to either:
- Restart the entire batch from scratch (wasting the successful runs), or
- Manually extract and merge outputs (complex and error-prone)

## Solution

The `pyddt-salvage` and `pyddt-merge` tools provide an automated workflow to:
1. Backup successful run outputs
2. Identify and create a mask for failed cells
3. Re-run only the failed cells
4. Merge the original successful outputs with the rerun outputs

## Workflow

### Step 1: Initial Run

Run dvmdostem with your run-mask as normal:

```bash
dvmdostem -p 10 -e 10 -s 10 -t 10 -n 5 -l monitor
```

Suppose some cells fail. The `output/run_status.nc` file will show which cells succeeded (value = 100) and which failed (value < 0).

### Step 2: Salvage the Run

Use `pyddt-salvage` to backup the outputs and create a new run-mask with only the failed cells:

```bash
pyddt-salvage output/ backup/ \
  --original-mask run-mask.nc \
  --new-mask run-mask-failed.nc \
  --verbose
```

This will:
- Create a backup of `output/` → `backup/`
- Analyze `output/run_status.nc` to identify failed cells
- Create `run-mask-failed.nc` with only failed cells enabled

Example output:
```
Salvaging run from: output/
Creating backup at: backup/
✓ Backup created at: backup/
✓ New run-mask created at: run-mask-failed.nc
  Number of failed cells to re-run: 2
```

### Step 3: Re-run Failed Cells

Now run dvmdostem again with the failed-cells mask:

```bash
# Replace the run-mask with the failed-cells mask
cp run-mask-failed.nc run-mask.nc

# Clear the output directory (or use a new one)
rm -rf output/
mkdir output/

# Re-run with the same parameters
dvmdostem -p 10 -e 10 -s 10 -t 10 -n 5 -l monitor
```

### Step 4: Merge Outputs

Use `pyddt-merge` to combine the salvaged outputs with the rerun outputs:

```bash
pyddt-merge backup/ output/ merged/ --verbose
```

This will:
- Read `backup/run_status.nc` and `output/run_status.nc`
- For each output file (e.g., `CMTNUM_yearly_tr.nc`):
  - Use rerun data for cells that were re-run
  - Use salvaged data for cells that succeeded originally
- Write merged results to `merged/`

Example output:
```
Salvaged run - successful cells: 8
Rerun - successful cells: 2
Found 15 files to merge
  Merging: CMTNUM_yearly_tr.nc
  Merging: GPP_monthly_tr.nc
  ...
✓ Merge complete
  Merged: 15 files
  Total successful cells: 10
```

### Step 5: Use Merged Outputs

The `merged/` directory now contains complete outputs for all cells as if the entire batch had succeeded on the first try.

## Command Reference

### pyddt-salvage

```
usage: pyddt-salvage [-h] --original-mask ORIGINAL_MASK --new-mask NEW_MASK 
                     [--run-status RUN_STATUS] [--verbose]
                     output_dir backup_dir

Salvage a failed batch run by creating a backup and preparing for re-run.

positional arguments:
  output_dir            Path to the output directory containing run_status.nc
  backup_dir            Path where the backup should be created (must not exist)

options:
  --original-mask ORIGINAL_MASK
                        Path to the original run-mask.nc used for this run
  --new-mask NEW_MASK   Path where the new run-mask (failed cells only) should be written
  --run-status RUN_STATUS
                        Path to run_status.nc (default: OUTPUT_DIR/run_status.nc)
  --verbose, -v         Print detailed progress information
```

### pyddt-merge

```
usage: pyddt-merge [-h] [--verbose] salvaged_dir rerun_dir output_dir

Merge outputs from a salvaged run and a rerun of failed cells.

positional arguments:
  salvaged_dir   Path to the salvaged output directory (backup from original run)
  rerun_dir      Path to the rerun output directory (results from re-running failed cells)
  output_dir     Path where merged outputs should be written

options:
  --verbose, -v  Print detailed progress information
```

## How It Works

### Run Status Tracking

The `run_status.nc` file contains a 2D array (Y, X) with values:
- `100`: Cell completed successfully
- `0` or negative: Cell failed or was not run

### Salvage Operation

1. **Backup**: Copies the entire output directory to preserve successful runs
2. **Analysis**: Reads `run_status.nc` to identify which cells failed
3. **Mask Creation**: Creates a new run-mask enabling only cells that:
   - Were enabled in the original mask, AND
   - Failed in the run (run_status < 0)

### Merge Operation

1. **Load Status**: Reads both `salvaged/run_status.nc` and `rerun/run_status.nc`
2. **Merge Files**: For each output file:
   - Uses `xarray.where()` to select data based on run_status
   - Where rerun status > 0: use rerun data
   - Otherwise: use salvaged data
3. **Broadcast**: Automatically handles broadcasting the 2D run_status to match any variable dimensionality (e.g., time, layer, pft dimensions)

## Limitations and Considerations

- **Restart Files**: The current implementation focuses on output files. Restart files are not automatically merged. For continuing runs, you may need to manually manage restart files.
  
- **Output Spec**: Both runs should use the same output specification to ensure files match.

- **Coordinates**: The merge assumes both runs have identical spatial dimensions and coordinates.

- **Disk Space**: The salvage operation creates a full copy of the output directory, so ensure you have sufficient disk space.

## Troubleshooting

### "Backup directory already exists"

The salvage operation will not overwrite an existing backup. Either:
- Use a different backup directory name
- Remove the existing backup (if you're sure you don't need it)

### "File not found in rerun"

If some output files exist in the salvaged run but not the rerun, they will be skipped with a warning. This can happen if:
- The output specification changed between runs
- Some outputs are only produced for successful cells

### "Dimensions don't match"

If the salvaged and rerun outputs have different dimensions, the merge will fail. Ensure:
- Both runs use the same input data (same grid size)
- Both runs use the same configuration and parameters

## Example: Full Workflow

```bash
# 1. Initial run
dvmdostem -p 10 -e 10 -s 10 -t 10 -n 5 -l monitor

# 2. Check for failures
ncdump output/run_status.nc | grep "run_status ="

# 3. Salvage the run
pyddt-salvage output/ backup/ \
  --original-mask run-mask.nc \
  --new-mask run-mask-failed.nc \
  --verbose

# 4. Prepare for rerun
cp run-mask-failed.nc run-mask.nc
rm -rf output/
mkdir output/

# 5. Rerun failed cells
dvmdostem -p 10 -e 10 -s 10 -t 10 -n 5 -l monitor

# 6. Merge results
pyddt-merge backup/ output/ merged/ --verbose

# 7. Verify merged results
ncdump merged/run_status.nc | grep "run_status ="

# 8. Use merged outputs
# The merged/ directory now has complete results
```

## See Also

- `pyddt-runmask`: Tool for creating and modifying run-masks
- GitHub Issue: Discussion on continuing failed runs
