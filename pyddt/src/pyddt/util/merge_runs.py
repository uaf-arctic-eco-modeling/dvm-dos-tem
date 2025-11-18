#!/usr/bin/env python

"""
Utility for merging outputs from salvaged runs.

This module provides functions to merge dvmdostem outputs from two runs:
- A "salvaged" run containing successful pixels from the original run
- A "rerun" containing outputs for pixels that failed in the original run

The merge creates a new set of outputs combining data from both runs,
with rerun data taking precedence where cells were re-executed.

Based on the workflow described in issue discussing continuing failed runs.
"""

import os
import sys
import glob
import argparse
import textwrap
import xarray as xr
import netCDF4 as nc
import numpy as np
from pathlib import Path


def merge_output_file(salvaged_file, rerun_file, output_file, 
                     salvaged_status, rerun_status, verbose=False):
    """
    Merge a single output file from salvaged and rerun directories.
    
    Uses xarray to merge data, taking rerun data where rerun cells were
    executed, otherwise using salvaged data.
    
    Parameters
    ----------
    salvaged_file : str
        Path to the output file from the salvaged (original) run
    rerun_file : str
        Path to the output file from the rerun
    output_file : str
        Path where the merged file should be written
    salvaged_status : xarray.DataArray
        Run status from the salvaged run
    rerun_status : xarray.DataArray
        Run status from the rerun
    verbose : bool, optional
        If True, print progress information
        
    Returns
    -------
    success : bool
        True if merge was successful
    """
    if verbose:
        print(f"  Merging: {os.path.basename(salvaged_file)}")
    
    # Load datasets
    ds_salvaged = xr.load_dataset(salvaged_file)
    ds_rerun = xr.load_dataset(rerun_file)
    
    # Get list of data variables (exclude coordinates)
    data_vars = [v for v in ds_salvaged.data_vars]
    
    # Create merged dataset starting with salvaged
    ds_merged = ds_salvaged.copy()
    
    # For each variable, merge using run_status as the condition
    for var in data_vars:
        if var in ds_rerun.data_vars:
            # Use rerun data where rerun_status is truthy (> 0), otherwise salvaged
            # We need to broadcast the run_status to match the variable's dimensions
            
            # Get the dimensions of the variable
            var_dims = ds_salvaged[var].dims
            
            # Build the condition by broadcasting run_status
            # run_status has dims (Y, X), we need to match variable dims
            if 'Y' in var_dims and 'X' in var_dims:
                # The variable has spatial dimensions
                # Create a condition that has the same dimensions as the variable
                # by broadcasting the run_status to all dimensions
                condition = rerun_status > 0
                
                # Broadcast condition to match variable dimensions
                # This ensures dimension order is preserved
                condition_broadcasted = condition.broadcast_like(ds_salvaged[var])
                
                # Use xr.where to merge: where condition is True, use rerun, else salvaged
                merged_var = xr.where(condition_broadcasted, ds_rerun[var], ds_salvaged[var])
                ds_merged[var] = merged_var
    
    # Write merged dataset
    ds_merged.to_netcdf(output_file)
    
    ds_salvaged.close()
    ds_rerun.close()
    ds_merged.close()
    
    return True


def find_output_files(output_dir, pattern='*.nc'):
    """
    Find all output NetCDF files in a directory.
    
    Parameters
    ----------
    output_dir : str
        Path to the output directory
    pattern : str, optional
        Glob pattern for files to find
        
    Returns
    -------
    files : list
        List of file paths found
    """
    search_path = os.path.join(output_dir, pattern)
    files = glob.glob(search_path)
    return sorted(files)


def merge_runs(salvaged_dir, rerun_dir, output_dir, verbose=False):
    """
    Merge all output files from salvaged and rerun directories.
    
    Parameters
    ----------
    salvaged_dir : str
        Path to the salvaged output directory (backup of original run)
    rerun_dir : str
        Path to the rerun output directory (results from re-running failed cells)
    output_dir : str
        Path where merged outputs should be written
    verbose : bool, optional
        If True, print detailed progress information
        
    Returns
    -------
    info : dict
        Dictionary with information about the merge operation
    """
    # Validate inputs
    if not os.path.exists(salvaged_dir):
        raise RuntimeError(f"Salvaged directory does not exist: {salvaged_dir}")
    
    if not os.path.exists(rerun_dir):
        raise RuntimeError(f"Rerun directory does not exist: {rerun_dir}")
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    # Load run_status files
    salvaged_status_file = os.path.join(salvaged_dir, 'run_status.nc')
    rerun_status_file = os.path.join(rerun_dir, 'run_status.nc')
    
    if not os.path.exists(salvaged_status_file):
        raise RuntimeError(f"run_status.nc not found in salvaged dir: {salvaged_status_file}")
    
    if not os.path.exists(rerun_status_file):
        raise RuntimeError(f"run_status.nc not found in rerun dir: {rerun_status_file}")
    
    # Load run status as xarray DataArrays
    ds_salvaged_status = xr.load_dataset(salvaged_status_file)
    ds_rerun_status = xr.load_dataset(rerun_status_file)
    
    salvaged_status = ds_salvaged_status['run_status']
    rerun_status = ds_rerun_status['run_status']
    
    if verbose:
        print(f"Salvaged run - successful cells: {(salvaged_status > 0).sum().values}")
        print(f"Rerun - successful cells: {(rerun_status > 0).sum().values}")
    
    # Find all NetCDF files in salvaged directory
    salvaged_files = find_output_files(salvaged_dir)
    
    if not salvaged_files:
        raise RuntimeError(f"No NetCDF files found in salvaged directory: {salvaged_dir}")
    
    if verbose:
        print(f"\nFound {len(salvaged_files)} files to merge")
    
    merged_count = 0
    skipped_count = 0
    
    # Merge each file
    for salvaged_file in salvaged_files:
        filename = os.path.basename(salvaged_file)
        rerun_file = os.path.join(rerun_dir, filename)
        output_file = os.path.join(output_dir, filename)
        
        # Skip if rerun file doesn't exist
        if not os.path.exists(rerun_file):
            if verbose:
                print(f"  Skipping {filename} (not in rerun)")
            skipped_count += 1
            continue
        
        # Skip run_status.nc - we'll merge it specially at the end
        if filename == 'run_status.nc':
            continue
        
        try:
            merge_output_file(salvaged_file, rerun_file, output_file,
                            salvaged_status, rerun_status, verbose)
            merged_count += 1
        except Exception as e:
            print(f"Warning: Failed to merge {filename}: {e}", file=sys.stderr)
            skipped_count += 1
    
    # Merge run_status.nc specially
    output_status_file = os.path.join(output_dir, 'run_status.nc')
    if verbose:
        print(f"  Merging: run_status.nc")
    
    # For run_status, we want to combine: take rerun where it ran, otherwise salvaged
    merged_status = xr.where(rerun_status > 0, rerun_status, salvaged_status)
    
    # Create a new dataset with the merged run_status
    ds_merged_status = xr.Dataset({'run_status': merged_status})
    
    # Copy attributes from salvaged status
    ds_merged_status['run_status'].attrs = ds_salvaged_status['run_status'].attrs
    ds_merged_status.attrs = ds_salvaged_status.attrs
    
    ds_merged_status.to_netcdf(output_status_file)
    
    # Close datasets
    ds_salvaged_status.close()
    ds_rerun_status.close()
    ds_merged_status.close()
    
    if verbose:
        print(f"\n✓ Merge complete")
        print(f"  Merged: {merged_count} files")
        print(f"  Skipped: {skipped_count} files")
        print(f"  Total successful cells: {(merged_status > 0).sum().values}")
    
    info = {
        'salvaged_dir': salvaged_dir,
        'rerun_dir': rerun_dir,
        'output_dir': output_dir,
        'merged_count': merged_count,
        'skipped_count': skipped_count,
        'total_successful_cells': int((merged_status > 0).sum().values),
    }
    
    return info


def cmdline_define():
    """Define the command line interface and return the parser object."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''
            Merge outputs from a salvaged run and a rerun of failed cells.
            
            This tool combines outputs from:
            1. A salvaged run (backup of original run with successful cells)
            2. A rerun of the failed cells from the original run
            
            The merge creates a complete set of outputs with data from both runs.
            Where a cell was re-run, the rerun data is used; otherwise the 
            salvaged data is used.
            
            Typical workflow:
            1. Run dvmdostem with initial run-mask
            2. Run pyddt-salvage to backup outputs and create failed-cells mask
            3. Re-run dvmdostem with the failed-cells mask
            4. Run pyddt-merge to combine salvaged and rerun outputs
        ''')
    )
    
    parser.add_argument('salvaged_dir',
        help='Path to the salvaged output directory (backup from original run)')
    
    parser.add_argument('rerun_dir',
        help='Path to the rerun output directory (results from re-running failed cells)')
    
    parser.add_argument('output_dir',
        help='Path where merged outputs should be written')
    
    parser.add_argument('--verbose', '-v', action='store_true',
        help='Print detailed progress information')
    
    return parser


def cmdline_parse(argv=None):
    """Parse command line arguments."""
    parser = cmdline_define()
    args = parser.parse_args(argv)
    
    # Validate paths
    if not os.path.exists(args.salvaged_dir):
        parser.error(f"Salvaged directory does not exist: {args.salvaged_dir}")
    
    if not os.path.exists(args.rerun_dir):
        parser.error(f"Rerun directory does not exist: {args.rerun_dir}")
    
    return args


def cmdline_run(args):
    """Execute based on command line arguments."""
    try:
        info = merge_runs(
            salvaged_dir=args.salvaged_dir,
            rerun_dir=args.rerun_dir,
            output_dir=args.output_dir,
            verbose=args.verbose
        )
        
        if not args.verbose:
            print(f"Merge complete:")
            print(f"  Output directory: {info['output_dir']}")
            print(f"  Merged files: {info['merged_count']}")
            print(f"  Total successful cells: {info['total_successful_cells']}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmdline_entry(argv=None):
    """Wrapper for easier testing of command line functions."""
    args = cmdline_parse(argv)
    return cmdline_run(args)


def main(argv=None):
    """Main entry point for the command line tool."""
    return cmdline_entry(argv=argv)


if __name__ == '__main__':
    sys.exit(cmdline_entry())
