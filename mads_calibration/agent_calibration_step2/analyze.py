#!/usr/bin/env python
"""
Headless Step 2 post-hoc analysis (target-first workflow).

Single path: equilibrium diagnostics (soft gate) -> rank by target R²/RMSE
(prefer nitrogen-passing samples) -> recommended_params + residuals.

Typical usage inside dvmdostem-autocal:

  python mads_calibration/agent_calibration_step2/analyze.py \\
    --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-iter3/ \\
    --biome tundra \\
    --save-plots \\
    --json-out /data/workflows/CMT04-IMN/logs/sa-step2-iter3/step2-result.yaml
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

RANKING_EXCLUDE_PREFIXES = ('RECO',)
DIAGNOSTIC_VARS = ('DEEPC', 'VEGC_pft4_Root', 'MINEC', 'AVLN')
CHRONIC_EQ_PASS_RATE = 0.20
EXTINCT_MOD_THRESHOLD = 1e-6
EXTINCT_OBS_THRESHOLD = 1e-3

# Bands match nitrogen_check() in SA_post_hoc_analysis.py.
NITROGEN_CHECK_BANDS = {
    'boreal': (1.15, 1.35),
    'tundra': (1.4, 1.6),
}


def nitrogen_check_ratio_bounds(biome):
    """Return (lo, hi) for the INGPP:GPP pass band."""
    if biome not in NITROGEN_CHECK_BANDS:
        raise ValueError(
            'biome must be one of {}; got {!r}'.format(
                list(NITROGEN_CHECK_BANDS), biome))
    return NITROGEN_CHECK_BANDS[biome]


def build_step2_lim_dict(targets, cv_lim, eps_lim, slope_lim,
                         pft4_root_cv_lim=None, deepc_slope_lim=None):
    """Per-variable eq thresholds; relax sparse-pool and slow-soil gates when requested."""
    lim = sa.generate_eq_lim_dict(
        targets,
        cv_lim=[cv_lim] * len(targets.columns),
        eps_lim=[eps_lim] * len(targets.columns),
        slope_lim=[slope_lim] * len(targets.columns),
    )
    if pft4_root_cv_lim is not None and 'VEGC_pft4_Root_cv_lim' in lim:
        lim['VEGC_pft4_Root_cv_lim'] = pft4_root_cv_lim
    if deepc_slope_lim is not None and 'DEEPC_slope_lim' in lim:
        lim['DEEPC_slope_lim'] = deepc_slope_lim
    return lim


def normalize_work_dir(path):
    path = os.path.abspath(path)
    if not path.endswith(os.sep):
        path = path + os.sep
    return path


def required_csv(path, name):
    full = os.path.join(path, name)
    if not os.path.isfile(full):
        return None
    return full


REQUIRED_CSV_NAMES = (
    'param_props.csv',
    'sample_matrix.csv',
    'targets.csv',
    'results.csv',
)


def missing_required_csvs(work_dir):
    return [
        name for name in REQUIRED_CSV_NAMES
        if required_csv(work_dir, name) is None
    ]


def failed_result(work_dir, notes, run_id=None, config_yaml=None, step1_result=None):
    """Minimal artifact when analysis cannot run."""
    return {
        'run_id': run_id or os.path.basename(work_dir.rstrip(os.sep)),
        'work_dir': work_dir,
        'config_yaml': config_yaml,
        'step1_result': step1_result,
        'n_total_samples': 0,
        'n_eq_passing': 0,
        'n_nitrogen_passing': 0,
        'nitrogen_pass_rate': 0.0,
        'status': 'failed',
        'best_rmse': None,
        'best_r2': None,
        'best_sample_index': None,
        'recommended_params': {},
        'selected_n_pass': False,
        'selected_n_ratio': None,
        'notes': notes,
    }


def filter_ranking_columns(targets, results):
    """Drop zero-weight targets (e.g. RECO) from ranking metrics."""
    keep = [
        c for c in targets.columns
        if not any(c.startswith(p) for p in RANKING_EXCLUDE_PREFIXES)
    ]
    return targets[keep], results[keep]


def load_nitrogen_check(work_dir, biome):
    """Return (n_pass_count, pass_rate, n_check DataFrame aligned to results index)."""
    n_check, _ = sa.nitrogen_check(path=work_dir, biome=biome)
    if n_check is None or len(n_check) == 0:
        return 0, 0.0, None
    n_pass = int(n_check['result'].sum())
    rate = float(n_pass) / float(len(n_check))
    return n_pass, rate, n_check


def compute_eq_diagnostics(eq_data, eq_var_check, fails_per_sample):
    fail_rates = (1 - eq_data.sum() / len(eq_data)).sort_values(ascending=False)
    top_failure_vars = fail_rates.head(8).index.tolist()

    per_variable_pass_rates = {}
    for var in DIAGNOSTIC_VARS:
        if var in eq_var_check.columns:
            per_variable_pass_rates[var] = float(eq_var_check[var].mean())

    var_pass = eq_var_check.mean()
    chronic_eq_failures = var_pass[var_pass < CHRONIC_EQ_PASS_RATE].index.tolist()

    return {
        'near_eq_count_le1': int((fails_per_sample <= 1).sum()),
        'near_eq_count_le3': int((fails_per_sample <= 3).sum()),
        'top_failure_vars': top_failure_vars,
        'per_variable_eq_pass_rates': {
            k: float(v) for k, v in var_pass.to_dict().items()
        },
        'chronic_eq_failures': chronic_eq_failures,
        'per_variable_pass_rates': per_variable_pass_rates,
    }


def select_best_sample(results, targets, sample_matrix, n_check):
    """
    Rank by target R²/RMSE; prefer samples passing nitrogen_check.
    Returns (best_index, ranked_from_n_passing, top_n_summary, recommended_params).
    """
    targets_rank, results_rank = filter_ranking_columns(targets, results)

    if n_check is not None and n_check['result'].any():
        n_pass_ids = n_check.index[n_check['result'].astype(bool)].tolist()
        n_pass_ids = [i for i in n_pass_ids if i in results_rank.index]
        if n_pass_ids:
            pool_r = results_rank.loc[n_pass_ids]
            pool_sm = sample_matrix.loc[n_pass_ids]
            ranked_from_n = True
        else:
            pool_r = results_rank
            pool_sm = sample_matrix
            ranked_from_n = False
    else:
        pool_r = results_rank
        pool_sm = sample_matrix
        ranked_from_n = False

    best_params, best_model = sa.n_top_runs(
        pool_r, targets_rank, pool_sm, r2lim=None, N=len(pool_r))

    best_idx = int(best_params.index[-1])
    recommended = best_params.iloc[-1]
    recommended_params = {
        col: float(recommended[col]) for col in best_params.columns
    }

    r2, rmse, mape, _ = sa.calc_metrics(best_model, targets_rank)
    top_n_summary = []
    for i, idx in enumerate(best_params.index):
        top_n_summary.append({
            'sample_index': int(idx),
            'R2': float(r2[i]),
            'RMSE': float(rmse[i]),
            'MAPE': float(mape[i]),
        })

    return best_idx, ranked_from_n, float(rmse[-1]), float(r2[-1]), \
        recommended_params, top_n_summary


def compute_target_residuals(targets_rank, results_rank, sample_idx):
    """Per-column obs/mod/rel_err_pct for the selected sample."""
    residuals = {}
    for col in targets_rank.columns:
        obs = float(targets_rank[col].iloc[0])
        mod = float(results_rank.loc[sample_idx, col])
        if abs(obs) > 1e-12:
            rel_err = 100.0 * (mod - obs) / obs
        else:
            rel_err = None
        residuals[col] = {
            'obs': obs,
            'mod': mod,
            'rel_err_pct': rel_err,
        }
    return residuals


def classify_misfits(targets_rank, results_rank, sample_idx):
    """Label columns as unreachable or extinct_pool for the selected sample."""
    unreachable = []
    extinct_pool = []
    for col in targets_rank.columns:
        obs = float(targets_rank[col].iloc[0])
        mod = float(results_rank.loc[sample_idx, col])
        rmin = float(results_rank[col].min())
        rmax = float(results_rank[col].max())
        if mod < EXTINCT_MOD_THRESHOLD and obs > EXTINCT_OBS_THRESHOLD:
            extinct_pool.append(col)
        elif obs < rmin or obs > rmax:
            unreachable.append(col)
    return {
        'unreachable': unreachable,
        'extinct_pool': extinct_pool,
    }


def save_diagnostic_plots(work_dir, results, targets):
    import matplotlib
    matplotlib.use('Agg')
    targets_rank, results_rank = filter_ranking_columns(targets, results)
    prefix = work_dir
    sa.plot_spaghetti(results_rank, targets_rank, save=True, saveprefix=prefix)
    sa.plot_boxplot(results_rank, targets_rank, save=True, saveprefix=prefix)


def analyze(work_dir, biome='tundra', n_top=10,
            slope_lim=1e-3, eps_lim=1e-5, cv_lim=1,
            pft4_root_cv_lim=None, deepc_slope_lim=None,
            run_id=None, config_yaml=None, step1_result=None,
            save_plots=False):
    work_dir = normalize_work_dir(work_dir)

    missing = missing_required_csvs(work_dir)
    if missing:
        return failed_result(
            work_dir,
            'Missing required files: {}'.format(', '.join(missing)),
            run_id=run_id,
            config_yaml=config_yaml,
            step1_result=step1_result,
        )

    sample_matrix = pd.read_csv(os.path.join(work_dir, 'sample_matrix.csv'))
    targets = pd.read_csv(os.path.join(work_dir, 'targets.csv'), skiprows=1)
    results = pd.read_csv(os.path.join(work_dir, 'results.csv'))

    n_total = len(results)
    if n_total == 0:
        return failed_result(
            work_dir,
            'No samples in results.csv.',
            run_id=run_id,
            config_yaml=config_yaml,
            step1_result=step1_result,
        )
    n_nitrogen_passing, nitrogen_pass_rate, n_check = load_nitrogen_check(
        work_dir, biome)

    eq_lim_dict = None
    if pft4_root_cv_lim is not None or deepc_slope_lim is not None:
        eq_lim_dict = build_step2_lim_dict(
            targets, cv_lim, eps_lim, slope_lim,
            pft4_root_cv_lim=pft4_root_cv_lim,
            deepc_slope_lim=deepc_slope_lim,
        )

    _, _, _, eq_var_check, eq_data, _, lim_used = sa.equilibrium_check(
        path=work_dir, slope_lim=slope_lim, eps_lim=eps_lim, cv_lim=cv_lim,
        lim_dict=eq_lim_dict if eq_lim_dict else False)

    fails_per_sample = (~eq_data).sum(axis=1)
    n_eq_passing = int(eq_data.all(axis=1).sum())

    eq_diag = compute_eq_diagnostics(eq_data, eq_var_check, fails_per_sample)

    best_idx, ranked_from_n, best_rmse, best_r2, recommended_params, top_n = \
        select_best_sample(results, targets, sample_matrix, n_check)

    targets_rank, results_rank = filter_ranking_columns(targets, results)
    target_residuals = compute_target_residuals(
        targets_rank, results_rank, best_idx)
    misfit_classification = classify_misfits(
        targets_rank, results_rank, best_idx)

    selected_n_pass = False
    selected_n_ratio = None
    if n_check is not None and best_idx in n_check.index:
        selected_n_pass = bool(n_check.loc[best_idx, 'result'])
        selected_n_ratio = float(n_check.loc[best_idx, 'ratio'])

    selected_eq_fails = int(fails_per_sample[best_idx])

    notes_parts = []
    if not ranked_from_n:
        notes_parts.append(
            'No nitrogen-passing samples; selected best RMSE from full pool.')
    if misfit_classification['extinct_pool']:
        notes_parts.append(
            'Extinct pools: {}'.format(
                ', '.join(misfit_classification['extinct_pool'][:5])))
    if misfit_classification['unreachable']:
        notes_parts.append(
            'Unreachable in SA envelope: {}'.format(
                ', '.join(misfit_classification['unreachable'][:5])))

    if selected_n_pass and not misfit_classification['extinct_pool']:
        status = 'pass'
    else:
        status = 'target_fit_review'
        if not selected_n_pass:
            n_lo, n_hi = nitrogen_check_ratio_bounds(biome)
            notes_parts.append(
                'Selected sample INGPP:GPP={:.3f} outside {} band [{:.3f}, {:.3f}].'.format(
                    selected_n_ratio or float('nan'), biome, n_lo, n_hi))

    if save_plots:
        save_diagnostic_plots(work_dir, results, targets)

    n_take = min(n_top, len(top_n))
    return {
        'run_id': run_id or os.path.basename(work_dir.rstrip(os.sep)),
        'work_dir': work_dir,
        'config_yaml': config_yaml,
        'step1_result': step1_result,
        'n_total_samples': n_total,
        'n_eq_passing': n_eq_passing,
        'n_nitrogen_passing': n_nitrogen_passing,
        'nitrogen_pass_rate': nitrogen_pass_rate,
        'nitrogen_biome': biome,
        'selected_n_pass': selected_n_pass,
        'selected_n_ratio': selected_n_ratio,
        'selected_eq_fails': selected_eq_fails,
        'ranked_from_n_passing': ranked_from_n,
        'eq_lim_dict': lim_used if isinstance(lim_used, dict) else None,
        'perturbation_runs': [],
        'status': status,
        'best_rmse': best_rmse,
        'best_r2': best_r2,
        'best_sample_index': best_idx,
        'recommended_params': recommended_params,
        'top_n_summary': top_n[-n_take:],
        'target_residuals': target_residuals,
        'misfit_classification': misfit_classification,
        'notes': ' '.join(notes_parts),
        **eq_diag,
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
        description='Step 2 SA post-hoc analysis (target-first, N on selected sample).'
    )
    parser.add_argument('--work-dir', required=True)
    parser.add_argument(
        '--biome', default='tundra',
        choices=['boreal', 'tundra'],
        help='Biome for nitrogen_check (boreal ~1.15-1.35, tundra ~1.4-1.6)',
    )
    parser.add_argument('--n-top', type=int, default=10)
    parser.add_argument('--run-id', default=None)
    parser.add_argument('--config-yaml', default=None)
    parser.add_argument('--step1-result', default=None)
    parser.add_argument('--json-out', default=None)
    parser.add_argument('--slope-lim', type=float, default=1e-3)
    parser.add_argument('--eps-lim', type=float, default=1e-5)
    parser.add_argument('--cv-lim', type=float, default=1.0)
    parser.add_argument(
        '--pft4-root-cv-lim', type=float, default=None,
        help='Relax VEGC_pft4_Root cv gate (%%) in eq report only',
    )
    parser.add_argument(
        '--deepc-slope-lim', type=float, default=None,
        help='Relax DEEPC slope gate in eq report only',
    )
    parser.add_argument(
        '--save-plots', action='store_true',
        help='Write spaghetti_plot.png and results_boxplot.png to work_dir',
    )
    return parser


def main():
    args = get_parser().parse_args()
    result = analyze(
        work_dir=args.work_dir,
        biome=args.biome,
        n_top=args.n_top,
        slope_lim=args.slope_lim,
        eps_lim=args.eps_lim,
        cv_lim=args.cv_lim,
        pft4_root_cv_lim=args.pft4_root_cv_lim,
        deepc_slope_lim=args.deepc_slope_lim,
        run_id=args.run_id,
        config_yaml=args.config_yaml,
        step1_result=args.step1_result,
        save_plots=args.save_plots,
    )

    print('run_id:              {}'.format(result['run_id']))
    print('status:              {}'.format(result['status']))
    if result['status'] == 'failed':
        print('notes:               {}'.format(result.get('notes', '')))
    else:
        print('best_rmse:           {}'.format(result['best_rmse']))
        print('best_r2:             {}'.format(result['best_r2']))
        print('best_sample:         {}'.format(result['best_sample_index']))
        print('selected N-pass:     {}'.format(result['selected_n_pass']))
        print('selected INGPP:GPP:  {}'.format(result['selected_n_ratio']))
        print('eq_passing:          {}/{}'.format(
            result['n_eq_passing'], result['n_total_samples']))
        print('nitrogen_passing:    {}/{} ({:.1%})'.format(
            result['n_nitrogen_passing'],
            result['n_total_samples'],
            result.get('nitrogen_pass_rate') or 0.0,
        ))
        print('near_eq (<=1 fail):  {}'.format(
            result.get('near_eq_count_le1', 'n/a')))
        print('recommended_params: {} keys'.format(
            len(result.get('recommended_params') or {})))

    if args.json_out:
        write_output(result, args.json_out)
        print('\nWrote {}'.format(args.json_out))

    if result['status'] == 'failed':
        sys.exit(1)
    if result['status'] == 'target_fit_review':
        sys.exit(2)
    sys.exit(0)


if __name__ == '__main__':
    main()
