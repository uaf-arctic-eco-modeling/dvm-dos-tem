#!/usr/bin/env python
"""
Headless Step 1 post-hoc analysis for cmax -> GPPAllIgnoringNitrogen SA runs.

Mirrors the analysis cells in notebooks/calibration_process.ipynb:
  equilibrium_check -> filter -> n_top_runs -> calc_metrics -> recommended_cmax

Typical usage inside dvmdostem-autocal:

  python mads_calibration/agent_calibration/step1_analyze.py \\
    --work-dir /data/workflows/CMT04-IMN-sa-N100/ \\
    --rmse-threshold 10 \\
    --config-yaml mads_calibration/logs/sa-IMN-step1.yaml \\
    --json-out /data/workflows/CMT04-IMN-sa-N100/step1-result.yaml
"""

from __future__ import print_function

import argparse
import json
import os
import sys

import pandas as pd
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MADS_CALIB_DIR = os.path.dirname(SCRIPT_DIR)
if MADS_CALIB_DIR not in sys.path:
    sys.path.insert(0, MADS_CALIB_DIR)

import SA_post_hoc_analysis as sa  # noqa: E402


def normalize_work_dir(path):
    path = os.path.abspath(path)
    if not path.endswith(os.sep):
        path = path + os.sep
    return path


def required_csv(path, name):
    full = os.path.join(path, name)
    if not os.path.isfile(full):
        raise RuntimeError('Missing required file: {}'.format(full))
    return full


def analyze(work_dir, rmse_threshold=10.0, n_top=10,
            slope_lim=1e-3, eps_lim=1e-5, cv_lim=1,
            run_id=None, config_yaml=None):
    work_dir = normalize_work_dir(work_dir)

    required_csv(work_dir, 'param_props.csv')
    required_csv(work_dir, 'sample_matrix.csv')
    required_csv(work_dir, 'targets.csv')
    required_csv(work_dir, 'results.csv')

    sample_matrix = pd.read_csv(os.path.join(work_dir, 'sample_matrix.csv'))
    targets = pd.read_csv(os.path.join(work_dir, 'targets.csv'), skiprows=1)
    results = pd.read_csv(os.path.join(work_dir, 'results.csv'))

    n_total = len(results)

    _, _, _, _, eq_data, _, _ = sa.equilibrium_check(
        path=work_dir, slope_lim=slope_lim, eps_lim=eps_lim, cv_lim=cv_lim)

    eq_mask = eq_data.all(axis=1)
    true_samples = eq_data[eq_mask].index.tolist()
    n_eq_passing = len(true_samples)

    if n_eq_passing == 0:
        return {
            'run_id': run_id or os.path.basename(work_dir.rstrip(os.sep)),
            'status': 'failed',
            'best_rmse': None,
            'best_r2': None,
            'best_sample_index': None,
            'work_dir': work_dir,
            'config_yaml': config_yaml,
            'n_eq_passing': 0,
            'n_total_samples': n_total,
            'recommended_cmax': {},
            'notes': 'No samples passed equilibrium check.',
        }

    results2 = results.loc[true_samples]
    sample_matrix2 = sample_matrix.loc[true_samples]

    best_params, best_model = sa.n_top_runs(
        results2, targets, sample_matrix2, r2lim=None, N=len(results2))

    n_take = min(n_top, len(best_params))
    best_params = best_params.iloc[-n_take:]
    best_model = best_model.iloc[-n_take:]

    r2, rmse, mape, re = sa.calc_metrics(best_model, targets)

    best_sample_index = int(best_params.index[-1])
    best_rmse = float(rmse[-1])
    best_r2 = float(r2[-1])
    recommended = best_params.iloc[-1]

    recommended_cmax = {
        col: float(recommended[col])
        for col in best_params.columns
        if col.startswith('cmax')
    }

    status = 'pass' if best_rmse < rmse_threshold else 'best_effort'

    return {
        'run_id': run_id or os.path.basename(work_dir.rstrip(os.sep)),
        'status': status,
        'best_rmse': best_rmse,
        'best_r2': best_r2,
        'best_sample_index': best_sample_index,
        'work_dir': work_dir,
        'config_yaml': config_yaml,
        'n_eq_passing': n_eq_passing,
        'n_total_samples': n_total,
        'recommended_cmax': recommended_cmax,
        'perturbation_runs': [],
        'notes': '',
    }


def write_output(result, path):
    ext = os.path.splitext(path)[1].lower()
    with open(path, 'w') as f:
        if ext == '.json':
            json.dump(result, f, indent=2)
        else:
            yaml.safe_dump(result, f, default_flow_style=False, sort_keys=False)


def get_parser():
    parser = argparse.ArgumentParser(
        description='Step 1 SA post-hoc analysis (cmax vs GPPAllIgnoringNitrogen).'
    )
    parser.add_argument(
        '--work-dir', required=True,
        help='SA work_dir from yaml (trailing slash optional)',
    )
    parser.add_argument(
        '--rmse-threshold', type=float, default=10.0,
        help='RMSE acceptance threshold (default: 10)',
    )
    parser.add_argument(
        '--n-top', type=int, default=10,
        help='Number of top R² runs to summarize (default: 10)',
    )
    parser.add_argument(
        '--run-id', default=None,
        help='Identifier for output artifact (default: work_dir basename)',
    )
    parser.add_argument(
        '--config-yaml', default=None,
        help='Path to SA config yaml used for this run',
    )
    parser.add_argument(
        '--json-out', default=None,
        help='Write result artifact to this path (.json or .yaml)',
    )
    parser.add_argument('--slope-lim', type=float, default=1e-3)
    parser.add_argument('--eps-lim', type=float, default=1e-5)
    parser.add_argument('--cv-lim', type=float, default=1.0)
    return parser


def main():
    args = get_parser().parse_args()
    result = analyze(
        work_dir=args.work_dir,
        rmse_threshold=args.rmse_threshold,
        n_top=args.n_top,
        slope_lim=args.slope_lim,
        eps_lim=args.eps_lim,
        cv_lim=args.cv_lim,
        run_id=args.run_id,
        config_yaml=args.config_yaml,
    )

    print('run_id:          {}'.format(result['run_id']))
    print('status:          {}'.format(result['status']))
    print('best_rmse:       {}'.format(result['best_rmse']))
    print('best_r2:         {}'.format(result['best_r2']))
    print('best_sample:     {}'.format(result['best_sample_index']))
    print('eq_passing:      {}/{}'.format(
        result['n_eq_passing'], result['n_total_samples']))
    print('recommended_cmax:')
    for key, val in sorted(result['recommended_cmax'].items()):
        print('  {}: {:.6f}'.format(key, val))

    if args.json_out:
        write_output(result, args.json_out)
        print('\nWrote {}'.format(args.json_out))

    if result['status'] == 'failed':
        sys.exit(1)
    if result['status'] == 'best_effort':
        sys.exit(2)
    sys.exit(0)


if __name__ == '__main__':
    main()
