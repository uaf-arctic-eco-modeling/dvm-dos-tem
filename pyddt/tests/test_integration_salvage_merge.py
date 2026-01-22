#!/usr/bin/env python

"""
Integration test for the complete salvage and merge workflow.

This test simulates the complete user workflow:
1. Initial run with some failures
2. Salvage operation
3. Rerun of failed cells
4. Merge operation
5. Verification of final results
"""

import os
import sys
import tempfile
import shutil
import numpy as np
import netCDF4 as nc
import xarray as xr
from pathlib import Path

# Add pyddt to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pyddt.util import salvage_run, merge_runs


def create_test_environment(tmpdir, shape=(10, 10)):
    """
    Create a test environment simulating a dvmdostem run.
    
    Returns paths dict with all necessary directories and files.
    """
    paths = {
        'root': tmpdir,
        'initial_output': os.path.join(tmpdir, 'output_initial'),
        'rerun_output': os.path.join(tmpdir, 'output_rerun'),
        'backup': os.path.join(tmpdir, 'backup'),
        'merged': os.path.join(tmpdir, 'merged'),
        'original_mask': os.path.join(tmpdir, 'run-mask.nc'),
        'failed_mask': os.path.join(tmpdir, 'run-mask-failed.nc'),
    }
    
    # Create directories
    os.makedirs(paths['initial_output'])
    
    # Create original run-mask (all cells enabled)
    sizey, sizex = shape
    run_mask = np.ones((sizey, sizex), dtype=np.int32)
    with nc.Dataset(paths['original_mask'], 'w') as ds:
        ds.createDimension('Y', sizey)
        ds.createDimension('X', sizex)
        var = ds.createVariable('run', np.int32, ('Y', 'X',))
        var[:] = run_mask
    
    return paths


def simulate_initial_run(output_dir, shape=(10, 10), failed_cells=None):
    """
    Simulate an initial dvmdostem run with some failures.
    
    Creates output files including run_status.nc with failed cells.
    """
    sizey, sizex = shape
    time_steps = 12
    
    # Create run_status.nc with some failures
    run_status = np.ones((sizey, sizex), dtype=np.int32) * 100
    if failed_cells:
        for y, x in failed_cells:
            run_status[y, x] = -1  # Failed
    
    with nc.Dataset(os.path.join(output_dir, 'run_status.nc'), 'w') as ds:
        ds.createDimension('Y', sizey)
        ds.createDimension('X', sizex)
        var = ds.createVariable('run_status', np.int32, ('Y', 'X',))
        var[:] = run_status
    
    # Create some output files
    # CMTNUM - use different values for each cell to track merging
    cmtnum_data = np.zeros((time_steps, sizey, sizex))
    for y in range(sizey):
        for x in range(sizex):
            # Use pixel coordinates + 1000 as value so we can track which data is merged
            # Adding 1000 ensures all values are positive and non-zero
            cmtnum_data[:, y, x] = 1000 + y * 10 + x
    
    ds = xr.Dataset(
        {'CMTNUM': (['time', 'Y', 'X'], cmtnum_data)},
        coords={
            'time': np.arange(time_steps),
            'Y': np.arange(sizey),
            'X': np.arange(sizex),
        }
    )
    ds.to_netcdf(os.path.join(output_dir, 'CMTNUM_yearly_tr.nc'))
    
    # GPP - monthly data
    gpp_data = np.ones((time_steps, sizey, sizex)) * 100
    ds = xr.Dataset(
        {'GPP': (['time', 'Y', 'X'], gpp_data)},
        coords={
            'time': np.arange(time_steps),
            'Y': np.arange(sizey),
            'X': np.arange(sizex),
        }
    )
    ds.to_netcdf(os.path.join(output_dir, 'GPP_monthly_tr.nc'))


def simulate_rerun(output_dir, shape=(10, 10), rerun_cells=None):
    """
    Simulate re-running only failed cells.
    
    Creates output files with data only for rerun cells.
    """
    sizey, sizex = shape
    time_steps = 12
    
    # Create run_status.nc with only rerun cells successful
    run_status = np.zeros((sizey, sizex), dtype=np.int32)
    if rerun_cells:
        for y, x in rerun_cells:
            run_status[y, x] = 100  # Success
    
    with nc.Dataset(os.path.join(output_dir, 'run_status.nc'), 'w') as ds:
        ds.createDimension('Y', sizey)
        ds.createDimension('X', sizex)
        var = ds.createVariable('run_status', np.int32, ('Y', 'X',))
        var[:] = run_status
    
    # Create output files
    # CMTNUM - use negative values to distinguish rerun data
    cmtnum_data = np.zeros((time_steps, sizey, sizex))
    for y in range(sizey):
        for x in range(sizex):
            # Use 2000 + value to distinguish from original (which uses 1000 + value)
            cmtnum_data[:, y, x] = 2000 + y * 10 + x
    
    ds = xr.Dataset(
        {'CMTNUM': (['time', 'Y', 'X'], cmtnum_data)},
        coords={
            'time': np.arange(time_steps),
            'Y': np.arange(sizey),
            'X': np.arange(sizex),
        }
    )
    ds.to_netcdf(os.path.join(output_dir, 'CMTNUM_yearly_tr.nc'))
    
    # GPP
    gpp_data = np.ones((time_steps, sizey, sizex)) * 200  # Different value
    ds = xr.Dataset(
        {'GPP': (['time', 'Y', 'X'], gpp_data)},
        coords={
            'time': np.arange(time_steps),
            'Y': np.arange(sizey),
            'X': np.arange(sizex),
        }
    )
    ds.to_netcdf(os.path.join(output_dir, 'GPP_monthly_tr.nc'))


def test_complete_workflow():
    """
    Test the complete salvage and merge workflow.
    """
    print("\n" + "="*70)
    print("Integration Test: Complete Salvage and Merge Workflow")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print("\n1. Setting up test environment...")
        paths = create_test_environment(tmpdir)
        
        # Define which cells will fail
        failed_cells = [(0, 0), (1, 1), (5, 5)]
        print(f"   Simulating failures at cells: {failed_cells}")
        
        print("\n2. Simulating initial run with failures...")
        simulate_initial_run(paths['initial_output'], failed_cells=failed_cells)
        
        # Verify initial run_status
        with nc.Dataset(os.path.join(paths['initial_output'], 'run_status.nc')) as ds:
            status = ds.variables['run_status'][:]
            num_success = np.sum(status > 0)
            num_failed = np.sum(status < 0)
            print(f"   Initial run: {num_success} successful, {num_failed} failed")
            assert num_failed == 3, f"Expected 3 failures, got {num_failed}"
        
        print("\n3. Running salvage operation...")
        info = salvage_run.salvage_run(
            output_dir=paths['initial_output'],
            backup_dir=paths['backup'],
            original_mask_file=paths['original_mask'],
            new_mask_file=paths['failed_mask'],
            verbose=True
        )
        
        # Verify salvage operation
        assert info['num_failed'] == 3, "Salvage should identify 3 failed cells"
        assert os.path.exists(paths['backup']), "Backup directory should exist"
        assert os.path.exists(paths['failed_mask']), "Failed cells mask should exist"
        
        # Check new mask
        with nc.Dataset(paths['failed_mask']) as ds:
            new_mask = ds.variables['run'][:]
            assert new_mask[0, 0] == 1, "Cell (0,0) should be enabled"
            assert new_mask[1, 1] == 1, "Cell (1,1) should be enabled"
            assert new_mask[5, 5] == 1, "Cell (5,5) should be enabled"
            assert new_mask[2, 2] == 0, "Cell (2,2) should be disabled"
        
        print("\n4. Simulating rerun of failed cells...")
        os.makedirs(paths['rerun_output'])
        simulate_rerun(paths['rerun_output'], rerun_cells=failed_cells)
        
        # Verify rerun
        with nc.Dataset(os.path.join(paths['rerun_output'], 'run_status.nc')) as ds:
            status = ds.variables['run_status'][:]
            num_success = np.sum(status > 0)
            print(f"   Rerun: {num_success} cells successful")
            assert num_success == 3, f"Expected 3 successful reruns, got {num_success}"
        
        print("\n5. Running merge operation...")
        merge_info = merge_runs.merge_runs(
            salvaged_dir=paths['backup'],
            rerun_dir=paths['rerun_output'],
            output_dir=paths['merged'],
            verbose=True
        )
        
        # Verify merge
        assert merge_info['total_successful_cells'] == 100, \
            "All cells should be successful after merge"
        
        print("\n6. Verifying merged results...")
        
        # Load merged run_status
        with nc.Dataset(os.path.join(paths['merged'], 'run_status.nc')) as ds:
            merged_status = ds.variables['run_status'][:]
            assert np.all(merged_status == 100), "All cells should be successful"
        
        # Load merged CMTNUM and verify data sources
        ds_merged = xr.load_dataset(os.path.join(paths['merged'], 'CMTNUM_yearly_tr.nc'))
        
        # For rerun cells, should have 2000+ values (rerun data)
        assert ds_merged['CMTNUM'][0, 0, 0].values >= 2000, \
            f"Cell (0,0) should have rerun data (2000+), got {ds_merged['CMTNUM'][0, 0, 0].values}"
        assert ds_merged['CMTNUM'][0, 1, 1].values >= 2000, \
            f"Cell (1,1) should have rerun data (2000+), got {ds_merged['CMTNUM'][0, 1, 1].values}"
        assert ds_merged['CMTNUM'][0, 5, 5].values >= 2000, \
            f"Cell (5,5) should have rerun data (2000+), got {ds_merged['CMTNUM'][0, 5, 5].values}"
        
        # For successful cells, should have 1000+ values (original data)
        assert 1000 <= ds_merged['CMTNUM'][0, 2, 2].values < 2000, \
            f"Cell (2,2) should have original data (1000-2000), got {ds_merged['CMTNUM'][0, 2, 2].values}"
        assert 1000 <= ds_merged['CMTNUM'][0, 3, 3].values < 2000, \
            f"Cell (3,3) should have original data (1000-2000), got {ds_merged['CMTNUM'][0, 3, 3].values}"
        
        # Verify specific values
        assert ds_merged['CMTNUM'][0, 0, 0].values == 2000, \
            f"Cell (0,0) should be 2000 (rerun), got {ds_merged['CMTNUM'][0, 0, 0].values}"
        assert ds_merged['CMTNUM'][0, 2, 2].values == 1022, \
            f"Cell (2,2) should be 1022 (original), got {ds_merged['CMTNUM'][0, 2, 2].values}"
        
        print("   ✓ Data correctly merged from rerun and original")
        
        # Check GPP
        ds_gpp = xr.load_dataset(os.path.join(paths['merged'], 'GPP_monthly_tr.nc'))
        
        # Rerun cells should have value 200
        assert ds_gpp['GPP'][0, 0, 0].values == 200, \
            "Cell (0,0) GPP should be from rerun (200)"
        
        # Original cells should have value 100
        assert ds_gpp['GPP'][0, 2, 2].values == 100, \
            "Cell (2,2) GPP should be from original (100)"
        
        print("   ✓ All variables correctly merged")
        
        print("\n" + "="*70)
        print("Integration Test PASSED")
        print("="*70)
        
        return True


if __name__ == '__main__':
    try:
        success = test_complete_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
