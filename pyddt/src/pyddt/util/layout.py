"""Default relative paths and entry types for a dvmdostem run directory.

These paths describe the conventional layout. Configuration files can point
at other locations. Callers decide whether missing entries are acceptable
and how to create or populate them.
"""

DEFAULT_RUN_LAYOUT = {
    'calibration': 'directory',
    'config': 'directory',
    'config/config.js': 'file',
    'config/output_spec.csv': 'file',
    'parameters': 'directory',
    'output': 'directory',
    'run-mask.nc': 'file',
}
