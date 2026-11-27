#!/usr/bin/env python

"""
Utility for salvaging failed batch runs by identifying failed cells and 
preparing for re-runs.

This module provides functions to:
1. Identify which pixels failed in a batch run
2. Create backups of outputs for successful runs
3. Generate a new run-mask containing only the failed pixels

Based on the workflow described in issue discussing continuing failed runs.
"""

import os
import sys
import shutil
import argparse
import textwrap
import netCDF4 as nc
import numpy as np
from pathlib import Path


def identify_failed_cells(run_status_file):
    """
    Identify pixels that failed during a run based on run_status.nc.
    
    Parameters
    ----------
    run_status_file : str
        Path to the run_status.nc file
        
    Returns
    -------
    failed_mask : numpy.ndarray
        2D boolean array where True indicates a failed pixel
    success_mask : numpy.ndarray
        2D boolean array where True indicates a successful pixel
    """
    with nc.Dataset(run_status_file, 'r') as ds:
        if 'run_status' not in ds.variables:
            raise RuntimeError(f"run_status variable not found in {run_status_file}")
        
        run_status = ds.variables['run_status'][:]
        
    # Positive values (typically 100) indicate success
    # Zero or negative values indicate failure or not run
    success_mask = run_status > 0
    failed_mask = ~success_mask
    
    return failed_mask, success_mask


def create_backup(output_dir, backup_dir):
    """
    Create a backup copy of the output directory.
    
    Parameters
    ----------
    output_dir : str
        Path to the output directory to backup
    backup_dir : str
        Path where the backup should be created
        
    Returns
    -------
    backup_path : str
        Path to the created backup directory
    """
    output_path = Path(output_dir)
    backup_path = Path(backup_dir)
    
    if not output_path.exists():
        raise RuntimeError(f"Output directory does not exist: {output_dir}")
    
    if backup_path.exists():
        raise RuntimeError(f"Backup directory already exists: {backup_dir}")
    
    # Copy the entire directory tree
    shutil.copytree(output_dir, backup_dir)
    
    return str(backup_path)


def create_failed_cells_mask(original_mask_file, run_status_file, output_mask_file):
    """
    Create a new run-mask with only the failed cells enabled.
    
    Parameters
    ----------
    original_mask_file : str
        Path to the original run-mask.nc file
    run_status_file : str
        Path to the run_status.nc file from the failed run
    output_mask_file : str
        Path where the new run-mask should be written
        
    Returns
    -------
    num_failed : int
        Number of failed cells that will be re-run
    """
    failed_mask, success_mask = identify_failed_cells(run_status_file)
    
    # Load the original mask to get the structure
    with nc.Dataset(original_mask_file, 'r') as orig_ds:
        if 'run' not in orig_ds.variables:
            raise RuntimeError(f"run variable not found in {original_mask_file}")
        
        original_run = orig_ds.variables['run'][:]
        
        # Get dimensions
        if 'Y' in orig_ds.dimensions and 'X' in orig_ds.dimensions:
            sizey = len(orig_ds.dimensions['Y'])
            sizex = len(orig_ds.dimensions['X'])
        else:
            sizey, sizex = original_run.shape
    
    # Create new mask: 1 for failed cells that were originally enabled, 0 otherwise
    # This ensures we only re-run cells that were supposed to run but failed
    new_mask = np.where((failed_mask) & (original_run == 1), 1, 0)
    
    num_failed = np.sum(new_mask)
    
    # Write the new mask file
    with nc.Dataset(output_mask_file, 'w') as new_ds:
        # Create dimensions
        new_ds.createDimension('Y', sizey)
        new_ds.createDimension('X', sizex)
        
        # Create variable
        run_var = new_ds.createVariable('run', np.int32, ('Y', 'X',))
        run_var[:] = new_mask
        
        # Copy global attributes if any
        with nc.Dataset(original_mask_file, 'r') as orig_ds:
            new_ds.setncatts(orig_ds.__dict__)
    
    return num_failed


def salvage_run(output_dir, backup_dir, original_mask_file, new_mask_file, 
                run_status_file=None, verbose=False):
    """
    Perform the complete salvage operation.
    
    This function:
    1. Creates a backup of the outputs
    2. Identifies failed cells from run_status.nc
    3. Creates a new run-mask with only failed cells enabled
    
    Parameters
    ----------
    output_dir : str
        Path to the output directory containing the failed run results
    backup_dir : str
        Path where the backup should be created
    original_mask_file : str
        Path to the original run-mask.nc file used for the run
    new_mask_file : str
        Path where the new run-mask (with only failed cells) should be written
    run_status_file : str, optional
        Path to run_status.nc. If None, looks for it in output_dir
    verbose : bool, optional
        If True, print detailed progress information
        
    Returns
    -------
    info : dict
        Dictionary with information about the salvage operation
    """
    if run_status_file is None:
        run_status_file = os.path.join(output_dir, 'run_status.nc')
    
    if not os.path.exists(run_status_file):
        raise RuntimeError(f"run_status.nc not found at {run_status_file}")
    
    if verbose:
        print(f"Salvaging run from: {output_dir}")
        print(f"Creating backup at: {backup_dir}")
    
    # Step 1: Create backup
    backup_path = create_backup(output_dir, backup_dir)
    if verbose:
        print(f"✓ Backup created at: {backup_path}")
    
    # Step 2: Identify failed cells and create new mask
    num_failed = create_failed_cells_mask(original_mask_file, run_status_file, new_mask_file)
    
    if verbose:
        print(f"✓ New run-mask created at: {new_mask_file}")
        print(f"  Number of failed cells to re-run: {num_failed}")
    
    # Get some additional stats
    failed_mask, success_mask = identify_failed_cells(run_status_file)
    num_success = np.sum(success_mask)
    total_cells = failed_mask.size
    
    info = {
        'output_dir': output_dir,
        'backup_dir': backup_path,
        'original_mask_file': original_mask_file,
        'new_mask_file': new_mask_file,
        'run_status_file': run_status_file,
        'num_failed': int(num_failed),
        'num_success': int(num_success),
        'total_cells': int(total_cells),
    }
    
    return info


def cmdline_define():
    """Define the command line interface and return the parser object."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''
            Salvage a failed batch run by creating a backup and preparing for re-run.
            
            This tool helps recover from partial batch failures by:
            1. Backing up the existing outputs (successful runs)
            2. Analyzing run_status.nc to identify failed pixels
            3. Creating a new run-mask with only the failed pixels enabled
            
            After running this tool, you can re-run dvmdostem with the new mask,
            then use pyddt-merge to combine the results.
        ''')
    )
    
    parser.add_argument('output_dir',
        help='Path to the output directory containing run_status.nc')
    
    parser.add_argument('backup_dir',
        help='Path where the backup should be created (must not exist)')
    
    parser.add_argument('--original-mask', required=True,
        help='Path to the original run-mask.nc used for this run')
    
    parser.add_argument('--new-mask', required=True,
        help='Path where the new run-mask (failed cells only) should be written')
    
    parser.add_argument('--run-status',
        help='Path to run_status.nc (default: OUTPUT_DIR/run_status.nc)')
    
    parser.add_argument('--verbose', '-v', action='store_true',
        help='Print detailed progress information')
    
    return parser


def cmdline_parse(argv=None):
    """Parse command line arguments."""
    parser = cmdline_define()
    args = parser.parse_args(argv)
    
    # Validate paths
    if not os.path.exists(args.output_dir):
        parser.error(f"Output directory does not exist: {args.output_dir}")
    
    if os.path.exists(args.backup_dir):
        parser.error(f"Backup directory already exists: {args.backup_dir}")
    
    if not os.path.exists(args.original_mask):
        parser.error(f"Original mask file does not exist: {args.original_mask}")
    
    return args


def cmdline_run(args):
    """Execute based on command line arguments."""
    try:
        info = salvage_run(
            output_dir=args.output_dir,
            backup_dir=args.backup_dir,
            original_mask_file=args.original_mask,
            new_mask_file=args.new_mask,
            run_status_file=args.run_status,
            verbose=args.verbose
        )
        
        if not args.verbose:
            print(f"Salvage complete:")
            print(f"  Backup: {info['backup_dir']}")
            print(f"  New mask: {info['new_mask_file']}")
            print(f"  Failed cells: {info['num_failed']}")
            print(f"  Successful cells: {info['num_success']}")
        
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
