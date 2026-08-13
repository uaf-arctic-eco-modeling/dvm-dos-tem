#!/usr/bin/env python
"""
Headless Step 1 post-hoc analysis for cmax -> GPPAllIgnoringNitrogen SA runs.

Mirrors the analysis cells in notebooks/calibration_process.ipynb:
  equilibrium_check -> filter -> n_top_runs -> calc_metrics -> recommended_cmax

Typical usage inside dvmdostem-autocal:

  python mads_calibration/agent/1_cmax/step1_analyze.py \\
    --work-dir /data/workflows/CMT{cmtnum:02d}-{site_label}-sa-N100/ \\
    --config-yaml mads_calibration/logs/sa-{site_label}-step1.yaml \\
    --json-out /data/workflows/CMT{cmtnum:02d}-{site_label}-sa-N100/step1-result.yaml
"""

from __future__ import print_function

import argparse
import json
import os
import sys

import pandas as pd
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.dirname(SCRIPT_DIR)
CALIBRATION_DIR = os.path.join(AGENT_DIR, '2_calibration')
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)
if CALIBRATION_DIR not in sys.path:
    sys.path.insert(0, CALIBRATION_DIR)

import SA_post_hoc_analysis as sa  # noqa: E402
from eq_workdir import equilibrium_check_from_workdir  # noqa: E402


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


OBS_NEAR_ZERO = 1e-12
STEP1_FLUX_REL_ERR_PCT = 10.0


def tier_failure_score_step1(results, targets, sample_idx, rel_err_pct):
    """Per-target tier failures for Step 1 (all columns at flux tier)."""
    n_fail = 0
    worst_excess = 0.0
    for col in targets.columns:
        obs = float(targets[col].iloc[0])
        if abs(obs) <= OBS_NEAR_ZERO:
            continue
        mod = float(results.loc[sample_idx, col])
        rel_err = 100.0 * (mod - obs) / obs
        if abs(rel_err) > rel_err_pct:
            n_fail += 1
            worst_excess = max(worst_excess, abs(rel_err) - rel_err_pct)
    return n_fail, worst_excess


def select_best_sample_step1(results, targets, sample_matrix, rel_err_pct):
    """Rank eq-filtered samples by fewest per-PFT tier failures, then excess."""
    scored = []
    for idx in results.index:
        n_fail, excess = tier_failure_score_step1(
            results, targets, idx, rel_err_pct)
        scored.append((n_fail, excess, int(idx)))
    scored.sort()

    best_idx = scored[0][2]
    r2_all, rmse_all, mape_all = sa.calc_metrics(results, targets)
    rmse_by_idx = dict(zip(results.index, rmse_all))
    r2_by_idx = dict(zip(results.index, r2_all))

    return best_idx, float(rmse_by_idx[best_idx]), float(r2_by_idx[best_idx]), scored


def analyze(work_dir, n_top=10,
            slope_lim=1e-3, eps_lim=1e-5, cv_lim=1,
            flux_rel_err_pct=STEP1_FLUX_REL_ERR_PCT,
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

    _, _, _, _, eq_data, _, _ = equilibrium_check_from_workdir(
        work_dir, targets, cv_lim=cv_lim, p_lim=eps_lim, slope_lim=slope_lim)

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

    best_sample_index, best_rmse, best_r2, scored = select_best_sample_step1(
        results2, targets, sample_matrix2, flux_rel_err_pct)

    recommended = sample_matrix2.loc[best_sample_index]
    recommended_cmax = {
        col: float(recommended[col])
        for col in sample_matrix2.columns
        if col.startswith('cmax')
    }

    n_tier_fail, worst_excess = scored[0][0], scored[0][1]

    status = 'pass' if n_tier_fail == 0 else 'best_effort'

    top_n_summary = []
    for n_fail, excess, idx in scored[:min(n_top, len(scored))]:
        r2, rmse, _ = sa.calc_metrics(
            results2.loc[[idx]], targets)
        top_n_summary.append({
            'sample_index': idx,
            'tier_failures': n_fail,
            'worst_tier_excess_pct': float(excess),
            'RMSE': float(rmse[0]),
            'R2': float(r2[0]),
        })

    return {
        'run_id': run_id or os.path.basename(work_dir.rstrip(os.sep)),
        'status': status,
        'best_rmse': best_rmse,
        'best_r2': best_r2,
        'best_sample_index': best_sample_index,
        'selected_tier_failures': n_tier_fail,
        'selected_worst_tier_excess_pct': float(worst_excess),
        'flux_rel_err_pct': flux_rel_err_pct,
        'work_dir': work_dir,
        'config_yaml': config_yaml,
        'n_eq_passing': n_eq_passing,
        'n_total_samples': n_total,
        'recommended_cmax': recommended_cmax,
        'top_n_summary': top_n_summary,
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
    parser.add_argument(
        '--flux-rel-err-pct', type=float, default=STEP1_FLUX_REL_ERR_PCT,
        help='Per-PFT INGPP tier (%%) for selection and pass/fail (default: 10)',
    )
    parser.add_argument(
        '--generate-report', action='store_true',
        help='Generate sa-validation-report.pdf in work_dir after analysis',
    )
    return parser


def main():
    args = get_parser().parse_args()
    result = analyze(
        work_dir=args.work_dir,
        n_top=args.n_top,
        slope_lim=args.slope_lim,
        eps_lim=args.eps_lim,
        cv_lim=args.cv_lim,
        flux_rel_err_pct=args.flux_rel_err_pct,
        run_id=args.run_id,
        config_yaml=args.config_yaml,
    )

    print('run_id:          {}'.format(result['run_id']))
    print('status:          {}'.format(result['status']))
    print('best_rmse:       {}'.format(result['best_rmse']))
    print('best_r2:         {}'.format(result['best_r2']))
    print('best_sample:     {}'.format(result['best_sample_index']))
    print('tier_failures:   {}'.format(result.get('selected_tier_failures')))
    print('eq_passing:      {}/{}'.format(
        result['n_eq_passing'], result['n_total_samples']))
    print('recommended_cmax:')
    for key, val in sorted(result['recommended_cmax'].items()):
        print('  {}: {:.6f}'.format(key, val))

    if args.json_out:
        write_output(result, args.json_out)
        print('\nWrote {}'.format(args.json_out))

    if args.generate_report:
        from sa_validation_report import generate as generate_report
        try:
            generate_report(
                work_dir=args.work_dir,
                result_yaml=args.json_out,
                phase='cmax',
            )
        except Exception as exc:
            print('Warning: report generation failed: {}'.format(exc),
                  file=sys.stderr)

    if result['status'] == 'failed':
        sys.exit(1)
    if result['status'] == 'best_effort':
        sys.exit(2)
    sys.exit(0)


if __name__ == '__main__':
    main()
