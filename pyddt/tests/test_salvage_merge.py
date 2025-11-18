#!/usr/bin/env python

"""
Tests for salvage_run and merge_runs utilities.
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


def create_test_run_status(filepath, shape=(10, 10), failed_cells=None):
    """
    Create a test run_status.nc file.
    
    Parameters
    ----------
    filepath : str
        Where to write the file
    shape : tuple
        Shape of the grid (Y, X)
    failed_cells : list of tuples
        List of (y, x) coordinates for failed cells
        
    Returns
    -------
    run_status : numpy.ndarray
        The created run status array
    """
    sizey, sizex = shape
    
    # Initialize with all successful (100)
    run_status = np.ones((sizey, sizex), dtype=np.int32) * 100
    
    # Mark failed cells
    if failed_cells:
        for y, x in failed_cells:
            run_status[y, x] = -1  # Negative for failed
    
    # Write to file
    with nc.Dataset(filepath, 'w') as ds:
        ds.createDimension('Y', sizey)
        ds.createDimension('X', sizex)
        var = ds.createVariable('run_status', np.int32, ('Y', 'X',))
        var[:] = run_status
    
    return run_status


def create_test_run_mask(filepath, shape=(10, 10), enabled_cells=None):
    """
    Create a test run-mask.nc file.
    
    Parameters
    ----------
    filepath : str
        Where to write the file
    shape : tuple
        Shape of the grid (Y, X)
    enabled_cells : list of tuples or None
        List of (y, x) coordinates for enabled cells.
        If None, all cells are enabled.
        
    Returns
    -------
    run_mask : numpy.ndarray
        The created run mask array
    """
    sizey, sizex = shape
    
    if enabled_cells is None:
        # All cells enabled
        run_mask = np.ones((sizey, sizex), dtype=np.int32)
    else:
        # Only specified cells enabled
        run_mask = np.zeros((sizey, sizex), dtype=np.int32)
        for y, x in enabled_cells:
            run_mask[y, x] = 1
    
    # Write to file
    with nc.Dataset(filepath, 'w') as ds:
        ds.createDimension('Y', sizey)
        ds.createDimension('X', sizex)
        var = ds.createVariable('run', np.int32, ('Y', 'X',))
        var[:] = run_mask
    
    return run_mask


def create_test_output_file(filepath, varname='CMTNUM', shape=(10, 10), 
                            time_steps=12, value=5):
    """
    Create a test output NetCDF file.
    
    Parameters
    ----------
    filepath : str
        Where to write the file
    varname : str
        Name of the variable
    shape : tuple
        Spatial shape (Y, X)
    time_steps : int
        Number of time steps
    value : int or callable
        Value to fill, or function(t, y, x) to generate values
        
    Returns
    -------
    data : numpy.ndarray
        The created data array
    """
    sizey, sizex = shape
    
    # Create data
    if callable(value):
        data = np.array([[[value(t, y, x) for x in range(sizex)] 
                         for y in range(sizey)] 
                        for t in range(time_steps)])
    else:
        data = np.ones((time_steps, sizey, sizex)) * value
    
    # Write to file
    ds = xr.Dataset(
        {varname: (['time', 'Y', 'X'], data)},
        coords={
            'time': np.arange(time_steps),
            'Y': np.arange(sizey),
            'X': np.arange(sizex),
        }
    )
    ds.to_netcdf(filepath)
    
    return data


def test_identify_failed_cells():
    """Test identifying failed cells from run_status.nc"""
    print("Testing identify_failed_cells...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test run_status with some failed cells
        status_file = os.path.join(tmpdir, 'run_status.nc')
        failed_cells = [(0, 0), (1, 1), (5, 5)]
        create_test_run_status(status_file, failed_cells=failed_cells)
        
        # Test the function
        failed_mask, success_mask = salvage_run.identify_failed_cells(status_file)
        
        # Verify
        assert failed_mask[0, 0] == True, "Cell (0,0) should be marked as failed"
        assert failed_mask[1, 1] == True, "Cell (1,1) should be marked as failed"
        assert failed_mask[5, 5] == True, "Cell (5,5) should be marked as failed"
        assert success_mask[2, 2] == True, "Cell (2,2) should be marked as success"
        
        num_failed = np.sum(failed_mask)
        assert num_failed == 3, f"Expected 3 failed cells, got {num_failed}"
        
    print("✓ identify_failed_cells test passed")


def test_create_failed_cells_mask():
    """Test creating a new run-mask with only failed cells"""
    print("Testing create_failed_cells_mask...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create original mask with all cells enabled
        original_mask_file = os.path.join(tmpdir, 'original_mask.nc')
        create_test_run_mask(original_mask_file)
        
        # Create run_status with some failed cells
        status_file = os.path.join(tmpdir, 'run_status.nc')
        failed_cells = [(0, 0), (1, 1), (9, 9)]
        create_test_run_status(status_file, failed_cells=failed_cells)
        
        # Create new mask
        new_mask_file = os.path.join(tmpdir, 'new_mask.nc')
        num_failed = salvage_run.create_failed_cells_mask(
            original_mask_file, status_file, new_mask_file
        )
        
        # Verify
        assert num_failed == 3, f"Expected 3 failed cells, got {num_failed}"
        
        # Check the new mask
        with nc.Dataset(new_mask_file, 'r') as ds:
            new_mask = ds.variables['run'][:]
            assert new_mask[0, 0] == 1, "Failed cell (0,0) should be enabled"
            assert new_mask[1, 1] == 1, "Failed cell (1,1) should be enabled"
            assert new_mask[9, 9] == 1, "Failed cell (9,9) should be enabled"
            assert new_mask[2, 2] == 0, "Successful cell (2,2) should be disabled"
            
    print("✓ create_failed_cells_mask test passed")


def test_salvage_run():
    """Test the complete salvage operation"""
    print("Testing salvage_run...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup test data
        output_dir = os.path.join(tmpdir, 'output')
        backup_dir = os.path.join(tmpdir, 'backup')
        os.makedirs(output_dir)
        
        # Create run_status with failed cells
        status_file = os.path.join(output_dir, 'run_status.nc')
        failed_cells = [(0, 0), (5, 5)]
        create_test_run_status(status_file, failed_cells=failed_cells)
        
        # Create some output files
        create_test_output_file(os.path.join(output_dir, 'CMTNUM_yearly_tr.nc'))
        
        # Create original mask
        original_mask_file = os.path.join(tmpdir, 'original_mask.nc')
        create_test_run_mask(original_mask_file)
        
        # Create new mask path
        new_mask_file = os.path.join(tmpdir, 'new_mask.nc')
        
        # Run salvage
        info = salvage_run.salvage_run(
            output_dir, backup_dir, original_mask_file, new_mask_file,
            verbose=False
        )
        
        # Verify backup was created
        assert os.path.exists(backup_dir), "Backup directory should exist"
        assert os.path.exists(os.path.join(backup_dir, 'run_status.nc')), \
            "Backup should contain run_status.nc"
        
        # Verify new mask was created
        assert os.path.exists(new_mask_file), "New mask file should exist"
        assert info['num_failed'] == 2, f"Expected 2 failed cells, got {info['num_failed']}"
        
    print("✓ salvage_run test passed")


def test_merge_output_file():
    """Test merging a single output file"""
    print("Testing merge_output_file...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create salvaged file with value 5 everywhere
        salvaged_file = os.path.join(tmpdir, 'salvaged.nc')
        create_test_output_file(salvaged_file, value=5)
        
        # Create rerun file with value 10 everywhere
        rerun_file = os.path.join(tmpdir, 'rerun.nc')
        create_test_output_file(rerun_file, value=10)
        
        # Create run status files
        # Salvaged: all cells successful except (0,0) and (1,1)
        salvaged_status_file = os.path.join(tmpdir, 'salvaged_status.nc')
        salvaged_status = create_test_run_status(
            salvaged_status_file, failed_cells=[(0, 0), (1, 1)]
        )
        
        # Rerun: only (0,0) and (1,1) successful
        rerun_status_file = os.path.join(tmpdir, 'rerun_status.nc')
        rerun_status = np.zeros((10, 10), dtype=np.int32)
        rerun_status[0, 0] = 100
        rerun_status[1, 1] = 100
        with nc.Dataset(rerun_status_file, 'w') as ds:
            ds.createDimension('Y', 10)
            ds.createDimension('X', 10)
            var = ds.createVariable('run_status', np.int32, ('Y', 'X',))
            var[:] = rerun_status
        
        # Load as xarray
        ds_salvaged_status = xr.load_dataset(salvaged_status_file)
        ds_rerun_status = xr.load_dataset(rerun_status_file)
        
        # Merge
        output_file = os.path.join(tmpdir, 'merged.nc')
        merge_runs.merge_output_file(
            salvaged_file, rerun_file, output_file,
            ds_salvaged_status['run_status'],
            ds_rerun_status['run_status']
        )
        
        # Verify merged file
        ds_merged = xr.load_dataset(output_file)
        
        # At (0,0) and (1,1), should have rerun values (10)
        assert ds_merged['CMTNUM'][0, 0, 0].values == 10, \
            "Cell (0,0) should have rerun value"
        assert ds_merged['CMTNUM'][0, 1, 1].values == 10, \
            "Cell (1,1) should have rerun value"
        
        # At other cells, should have salvaged values (5)
        assert ds_merged['CMTNUM'][0, 2, 2].values == 5, \
            "Cell (2,2) should have salvaged value"
        
        ds_merged.close()
        ds_salvaged_status.close()
        ds_rerun_status.close()
        
    print("✓ merge_output_file test passed")


def test_merge_runs():
    """Test the complete merge operation"""
    print("Testing merge_runs...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create salvaged directory
        salvaged_dir = os.path.join(tmpdir, 'salvaged')
        os.makedirs(salvaged_dir)
        
        # Create salvaged outputs
        create_test_output_file(
            os.path.join(salvaged_dir, 'CMTNUM_yearly_tr.nc'),
            value=5
        )
        salvaged_status = create_test_run_status(
            os.path.join(salvaged_dir, 'run_status.nc'),
            failed_cells=[(0, 0), (1, 1)]
        )
        
        # Create rerun directory
        rerun_dir = os.path.join(tmpdir, 'rerun')
        os.makedirs(rerun_dir)
        
        # Create rerun outputs (only for failed cells)
        create_test_output_file(
            os.path.join(rerun_dir, 'CMTNUM_yearly_tr.nc'),
            value=10
        )
        rerun_status = np.zeros((10, 10), dtype=np.int32)
        rerun_status[0, 0] = 100
        rerun_status[1, 1] = 100
        with nc.Dataset(os.path.join(rerun_dir, 'run_status.nc'), 'w') as ds:
            ds.createDimension('Y', 10)
            ds.createDimension('X', 10)
            var = ds.createVariable('run_status', np.int32, ('Y', 'X',))
            var[:] = rerun_status
        
        # Merge
        output_dir = os.path.join(tmpdir, 'merged')
        info = merge_runs.merge_runs(
            salvaged_dir, rerun_dir, output_dir,
            verbose=False
        )
        
        # Verify merged outputs
        assert os.path.exists(output_dir), "Output directory should exist"
        assert os.path.exists(os.path.join(output_dir, 'run_status.nc')), \
            "Merged run_status.nc should exist"
        assert os.path.exists(os.path.join(output_dir, 'CMTNUM_yearly_tr.nc')), \
            "Merged CMTNUM file should exist"
        
        # Check merged run_status
        ds_status = xr.load_dataset(os.path.join(output_dir, 'run_status.nc'))
        assert ds_status['run_status'][0, 0].values == 100, \
            "Cell (0,0) should be successful in merged status"
        assert ds_status['run_status'][1, 1].values == 100, \
            "Cell (1,1) should be successful in merged status"
        assert ds_status['run_status'][2, 2].values == 100, \
            "Cell (2,2) should be successful in merged status"
        
        # Check that total successful cells is correct
        assert info['total_successful_cells'] == 100, \
            f"Expected 100 successful cells, got {info['total_successful_cells']}"
        
        ds_status.close()
        
    print("✓ merge_runs test passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("Running tests for salvage_run and merge_runs utilities")
    print("="*60 + "\n")
    
    tests = [
        test_identify_failed_cells,
        test_create_failed_cells_mask,
        test_salvage_run,
        test_merge_output_file,
        test_merge_runs,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
