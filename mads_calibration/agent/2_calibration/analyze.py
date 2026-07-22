#!/usr/bin/env python
"""
Headless Step 2 post-hoc analysis (target-first workflow).

Rank by target R²/RMSE (prefer nitrogen-passing samples), then gate the
selected sample on N-pass, tiered per-target fit, and equilibrium (hard
except chronic whitelist) before status pass.

Typical usage inside dvmdostem-autocal:

  # Two-phase workflow (see calibration_instructions.md):
  python .../analyze.py --phase veg_exploration --work-dir .../sa-step2-veg-exploration/ ...
  python .../analyze.py --phase soil_exploration --work-dir .../sa-step2-soil-exploration/ ...
  # Targeted SA within a phase:
  python .../analyze.py --phase krb --work-dir .../sa-step2-krb/ ...
  python .../analyze.py --phase cfall --work-dir .../sa-step2-cfall/ ...
  # Optional: phase6 (rhmoist/MINEC), phase7 (soil retune alias)
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
from eq_workdir import (  # noqa: E402
    build_step2_lim_dict,
    equilibrium_check_from_workdir,
)
from stage_ledger import (  # noqa: E402
    infer_param_dir_from_work_dir,
    ledger_path_for_param_dir,
    load_ledger,
    require_prerequisites,
)

RANKING_EXCLUDE_PREFIXES = ('RECO',)
DIAGNOSTIC_VARS = ('DEEPC', 'VEGC_pft4_Root', 'MINEC', 'AVLN')
CHRONIC_EQ_WHITELIST = frozenset(DIAGNOSTIC_VARS)
CHRONIC_EQ_PASS_RATE = 0.20
EXTINCT_MOD_THRESHOLD = 1e-6
EXTINCT_OBS_THRESHOLD = 1e-3
OBS_NEAR_ZERO = 1e-12
UNREACHABLE_REVIEW_MIN = 3

# Targeted per-param phases (krb/nfall/etc.) have far fewer gated columns
# than veg_exploration or main; requiring 3 unreachable columns before
# flagging a structural ceiling would almost never trigger. Any unreachable
# column on these dedicated phases, after the parameter built specifically
# to move it has already been swept, is itself the structural signal.
UNREACHABLE_REVIEW_MIN_BY_PHASE = {
    'main': UNREACHABLE_REVIEW_MIN,
    'veg_exploration': 2,
    'soil_exploration': 1,
    'nlevel': 1,
    'krb': 1,
    'cfall': 1,
    'nfall': 1,
    'soil': 1,
    'phase6': 1,
    'phase7': 1,  # alias of soil (post-rhmoist retune)
}

KDC_ORDER = ('kdcrawc', 'kdcsoma', 'kdcsompr', 'kdcsomcr')
SOIL_KDC_PHASES = frozenset(('soil', 'soil_exploration', 'phase7'))

POOL_NCNAMES = frozenset(('SHLWC', 'DEEPC', 'MINEC', 'ORGN', 'AVLN'))

PHASE_PASS_STATUS = {
    'main': 'pass',  # optional post-hoc on old integrated work_dirs only
    'veg_exploration': 'veg_pass',
    'soil_exploration': 'soil_pass',
    'nlevel': 'nlevel_pass',
    'krb': 'krb_pass',
    'cfall': 'cfall_pass',
    'nfall': 'nfall_pass',
    'soil': 'soil_pass',
    'phase6': 'phase6_pass',
    'phase7': 'phase7_pass',  # soil retune after rhmoist; same gates as soil
}

PASSING_STATUSES = frozenset(PHASE_PASS_STATUS.values())

# Gate prefixes (results.csv). Two-phase: veg_exploration then soil_exploration.
# Legacy per-param phases remain for targeted SA within each phase.
PHASE_GATE_POOLS = {
    'main': None,
    'veg_exploration': ('NPP', 'VEGC', 'VEGNSTR', 'AVLN'),
    'soil_exploration': ('SHLWC', 'DEEPC', 'MINEC'),
    'nlevel': ('AVLN',),
    'krb': ('NPP',),
    'cfall': ('VEGC',),
    'nfall': ('VEGNSTR',),
    'soil': ('SHLWC', 'DEEPC', 'MINEC'),
    'phase6': ('MINEC',),
    'phase7': ('SHLWC', 'DEEPC', 'MINEC'),
}

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


def validate_kdc_ordering(recommended_params):
    """Check kdcrawc > kdcsoma > kdcsompr > kdcsomcr and kdcrawc < 1.0."""
    present = [k for k in KDC_ORDER if k in recommended_params]
    if len(present) < 2:
        return True, []
    violations = []
    kdcrawc = recommended_params.get('kdcrawc')
    if kdcrawc is not None and kdcrawc >= 1.0:
        violations.append('kdcrawc must be < 1.0 (got {:.6g})'.format(kdcrawc))
    for i in range(len(KDC_ORDER) - 1):
        left, right = KDC_ORDER[i], KDC_ORDER[i + 1]
        if left in recommended_params and right in recommended_params:
            lv = recommended_params[left]
            rv = recommended_params[right]
            if lv <= rv:
                violations.append(
                    '{} must be > {} (got {:.6g} vs {:.6g})'.format(
                        left, right, lv, rv))
    return len(violations) == 0, violations


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
        'target_fit_pass': False,
        'failing_targets': [],
        'selected_eq_pass': False,
        'failing_eq_vars': [],
        'notes': notes,
    }


def filter_ranking_columns(targets, results):
    """Drop zero-weight targets (e.g. RECO) from ranking metrics."""
    keep = [
        c for c in targets.columns
        if not any(c.startswith(p) for p in RANKING_EXCLUDE_PREFIXES)
    ]
    return targets[keep], results[keep]


def column_matches_pool(column, pool_name):
    """True if results.csv column belongs to a soil pool gate (e.g. MINEC)."""
    if column == pool_name:
        return True
    return column.split('_')[0] == pool_name


def filter_phase_gate_columns(targets_rank, results_rank, phase):
    """Restrict ranking/gates to phase-specific pool columns (phase6/phase7)."""
    pools = PHASE_GATE_POOLS.get(phase)
    if pools is None:
        return targets_rank, results_rank
    keep = [
        c for c in targets_rank.columns
        if any(column_matches_pool(c, p) for p in pools)
    ]
    if not keep:
        return targets_rank.iloc[:, 0:0], results_rank.iloc[:, 0:0]
    return targets_rank[keep], results_rank[keep]


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


def tier_failure_score(results_rank, targets_rank, sample_idx,
                       flux_rel_err_pct, pool_rel_err_pct):
    """
    Count tier failures and worst excess |rel_err| for one sample.

    Lower (n_fail, excess) is better. Selection uses this instead of bulk RMSE.
    """
    n_fail = 0
    worst_excess = 0.0
    for col in targets_rank.columns:
        obs = float(targets_rank[col].iloc[0])
        if abs(obs) <= OBS_NEAR_ZERO:
            continue
        mod = float(results_rank.loc[sample_idx, col])
        rel_err = 100.0 * (mod - obs) / obs
        limit = target_tolerance_pct(col, flux_rel_err_pct, pool_rel_err_pct)
        if abs(rel_err) > limit:
            n_fail += 1
            worst_excess = max(worst_excess, abs(rel_err) - limit)
    return n_fail, worst_excess


def select_best_sample(results, targets, sample_matrix, n_check,
                       flux_rel_err_pct=10.0, pool_rel_err_pct=20.0,
                       gate_targets=None, gate_results=None):
    """
    Prefer nitrogen-passing samples; rank by fewest per-target tier failures,
    then lowest worst excess beyond tier (not bulk RMSE alone).

    When gate_targets/gate_results are set (phase6/phase7), ranking uses only
    those columns; recommended_params still come from the full sample_matrix.

    Returns (best_index, ranked_from_n_passing, rmse, r2, recommended_params, top_n).
    """
    targets_rank, results_rank = filter_ranking_columns(targets, results)
    rank_targets = gate_targets if gate_targets is not None else targets_rank
    rank_results = gate_results if gate_results is not None else results_rank

    if n_check is not None and n_check['result'].any():
        n_pass_ids = n_check.index[n_check['result'].astype(bool)].tolist()
        n_pass_ids = [i for i in n_pass_ids if i in results_rank.index]
        if n_pass_ids:
            candidate_ids = n_pass_ids
            ranked_from_n = True
        else:
            candidate_ids = list(results_rank.index)
            ranked_from_n = False
    else:
        candidate_ids = list(results_rank.index)
        ranked_from_n = False

    scored = []
    for idx in candidate_ids:
        n_fail, excess = tier_failure_score(
            rank_results, rank_targets, idx,
            flux_rel_err_pct, pool_rel_err_pct)
        scored.append((n_fail, excess, int(idx)))
    scored.sort()

    best_idx = scored[0][2]
    recommended = sample_matrix.loc[best_idx]
    recommended_params = {
        col: float(recommended[col]) for col in sample_matrix.columns
    }

    r2_all, rmse_all, mape_all = sa.calc_metrics(rank_results, rank_targets)
    rmse_by_idx = dict(zip(results_rank.index, rmse_all))
    r2_by_idx = dict(zip(results_rank.index, r2_all))
    mape_by_idx = dict(zip(results_rank.index, mape_all))

    top_n_summary = []
    for n_fail, excess, idx in scored[:10]:
        top_n_summary.append({
            'sample_index': idx,
            'tier_failures': n_fail,
            'worst_tier_excess_pct': float(excess),
            'R2': float(r2_by_idx[idx]),
            'RMSE': float(rmse_by_idx[idx]),
            'MAPE': float(mape_by_idx[idx]),
        })

    return best_idx, ranked_from_n, float(rmse_by_idx[best_idx]), float(r2_by_idx[best_idx]), \
        recommended_params, top_n_summary


def target_tolerance_pct(column, flux_rel_err_pct, pool_rel_err_pct):
    """Return max |rel_err_pct| for a results.csv column name."""
    if (column.startswith('NPP') or column.startswith('VEGC')
            or column.startswith('VEGNSTR')):
        return flux_rel_err_pct
    base = column.split('_')[0]
    if base in POOL_NCNAMES or column in POOL_NCNAMES:
        return pool_rel_err_pct
    return pool_rel_err_pct


def evaluate_target_fit(target_residuals, flux_rel_err_pct, pool_rel_err_pct):
    """
    Check tiered per-target tolerance on every ranked column.

    Returns (pass, failing_targets) where failing_targets is a list of dicts.
    """
    failing = []
    for col, row in target_residuals.items():
        obs = row['obs']
        rel_err = row['rel_err_pct']
        if abs(obs) <= OBS_NEAR_ZERO or rel_err is None:
            continue
        limit = target_tolerance_pct(col, flux_rel_err_pct, pool_rel_err_pct)
        if abs(rel_err) > limit:
            failing.append({
                'column': col,
                'obs': obs,
                'mod': row['mod'],
                'rel_err_pct': rel_err,
                'limit_pct': limit,
            })
    return len(failing) == 0, failing


def evaluate_selected_eq(eq_var_check, sample_idx, require_eq_pass):
    """
    Eq pass on selected sample for non-chronic variables.

    Returns (pass, failing_eq_vars).
    """
    if not require_eq_pass:
        return True, []
    if sample_idx not in eq_var_check.index:
        return False, ['sample_index_not_in_eq_check']
    failing = []
    for var in eq_var_check.columns:
        if var in CHRONIC_EQ_WHITELIST:
            continue
        if not bool(eq_var_check.loc[sample_idx, var]):
            failing.append(var)
    return len(failing) == 0, failing


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
            flux_rel_err_pct=10.0, pool_rel_err_pct=20.0,
            require_eq_pass=True,
            phase='main',
            run_id=None, config_yaml=None, step1_result=None,
            save_plots=False):
    work_dir = normalize_work_dir(work_dir)
    if phase not in PHASE_PASS_STATUS:
        return failed_result(
            work_dir,
            'Invalid phase {!r}; use one of {}'.format(
                phase, list(PHASE_PASS_STATUS)),
            run_id=run_id,
            config_yaml=config_yaml,
            step1_result=step1_result,
        )
    if phase != 'main':
        require_eq_pass = False

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

    _, _, _, eq_var_check, eq_data, _, lim_used = equilibrium_check_from_workdir(
        work_dir, targets, cv_lim=cv_lim, p_lim=eps_lim, slope_lim=slope_lim,
        lim_dict=eq_lim_dict if eq_lim_dict else None)

    fails_per_sample = (~eq_data).sum(axis=1)
    n_eq_passing = int(eq_data.all(axis=1).sum())

    eq_diag = compute_eq_diagnostics(eq_data, eq_var_check, fails_per_sample)

    targets_rank, results_rank = filter_ranking_columns(targets, results)
    gate_targets, gate_results = filter_phase_gate_columns(
        targets_rank, results_rank, phase)
    if phase != 'main' and len(gate_targets.columns) == 0:
        return failed_result(
            work_dir,
            'Phase {!r}: no gate columns found in targets/results '
            '(expected pools: {}).'.format(phase, PHASE_GATE_POOLS[phase]),
            run_id=run_id,
            config_yaml=config_yaml,
            step1_result=step1_result,
        )

    best_idx, ranked_from_n, best_rmse, best_r2, recommended_params, top_n = \
        select_best_sample(
            results, targets, sample_matrix, n_check,
            flux_rel_err_pct=flux_rel_err_pct,
            pool_rel_err_pct=pool_rel_err_pct,
            gate_targets=gate_targets if phase != 'main' else None,
            gate_results=gate_results if phase != 'main' else None)

    eval_targets = gate_targets if phase != 'main' else targets_rank
    eval_results = gate_results if phase != 'main' else results_rank
    target_residuals = compute_target_residuals(
        eval_targets, eval_results, best_idx)
    misfit_classification = classify_misfits(
        eval_targets, eval_results, best_idx)

    selected_n_pass = False
    selected_n_ratio = None
    if n_check is not None and best_idx in n_check.index:
        selected_n_pass = bool(n_check.loc[best_idx, 'result'])
        selected_n_ratio = float(n_check.loc[best_idx, 'ratio'])

    selected_eq_fails = int(fails_per_sample[best_idx])

    notes_parts = []
    if not ranked_from_n:
        notes_parts.append(
            'No nitrogen-passing samples; selected fewest tier failures from full pool.')
    if misfit_classification['extinct_pool']:
        notes_parts.append(
            'Extinct pools: {}'.format(
                ', '.join(misfit_classification['extinct_pool'][:5])))
    if misfit_classification['unreachable']:
        notes_parts.append(
            'Unreachable in SA envelope: {}'.format(
                ', '.join(misfit_classification['unreachable'][:5])))

    target_fit_pass, failing_targets = evaluate_target_fit(
        target_residuals, flux_rel_err_pct, pool_rel_err_pct)
    selected_eq_pass, failing_eq_vars = evaluate_selected_eq(
        eq_var_check, best_idx, require_eq_pass)

    kdc_ordering_valid = True
    kdc_ordering_violations = []
    if phase in SOIL_KDC_PHASES:
        kdc_ordering_valid, kdc_ordering_violations = validate_kdc_ordering(
            recommended_params)
        if not kdc_ordering_valid:
            notes_parts.append(
                'Kdc ordering violation: {}'.format(
                    '; '.join(kdc_ordering_violations)))

    if not target_fit_pass:
        cols = [f['column'] for f in failing_targets[:8]]
        notes_parts.append(
            'Per-target fit fail (>{:.0f}%/{:.0f}% tier): {}'.format(
                flux_rel_err_pct, pool_rel_err_pct, ', '.join(cols)))
    if require_eq_pass and not selected_eq_pass:
        notes_parts.append(
            'Eq fail on selected sample: {}'.format(
                ', '.join(failing_eq_vars[:8])))

    unreachable_min = UNREACHABLE_REVIEW_MIN_BY_PHASE.get(
        phase, UNREACHABLE_REVIEW_MIN)
    if (selected_n_pass and target_fit_pass and selected_eq_pass
            and kdc_ordering_valid
            and not misfit_classification['extinct_pool']):
        status = PHASE_PASS_STATUS[phase]
    elif (not target_fit_pass
          and len(misfit_classification.get('unreachable') or [])
          >= unreachable_min):
        status = 'unreachable_review'
        if phase == 'main':
            notes_parts.append(
                'HALT for human review: {} target(s) outside the SA envelope; '
                'document as structural/model limitation or revisit target '
                'value. Do not iterate bounds alone; do not reopen Step 1 '
                'automatically.'.format(len(misfit_classification['unreachable'])))
        else:
            notes_parts.append(
                'HALT for human review: {} target(s) gated by --phase {} '
                'outside the SA envelope even with the dedicated parameter set '
                '({}); document as structural/model limitation or revisit the '
                'target value. Do not widen bounds further on this phase; do '
                'not reopen Step 1 automatically.'.format(
                    len(misfit_classification['unreachable']), phase,
                    ', '.join(misfit_classification['unreachable'][:8])))
    else:
        status = 'target_fit_review'

    if status not in PASSING_STATUSES and not selected_n_pass:
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
        'phase': phase,
        'status': status,
        'best_rmse': best_rmse,
        'best_r2': best_r2,
        'best_sample_index': best_idx,
        'recommended_params': recommended_params,
        'top_n_summary': top_n[-n_take:],
        'target_residuals': target_residuals,
        'target_fit_pass': target_fit_pass,
        'failing_targets': failing_targets,
        'target_tolerance': {
            'flux_rel_err_pct': flux_rel_err_pct,
            'pool_rel_err_pct': pool_rel_err_pct,
        },
        'selected_eq_pass': selected_eq_pass,
        'failing_eq_vars': failing_eq_vars,
        'require_eq_pass': require_eq_pass,
        'misfit_classification': misfit_classification,
        'kdc_ordering_valid': kdc_ordering_valid,
        'kdc_ordering_violations': kdc_ordering_violations,
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
        description='Step 2 SA post-hoc analysis (strict per-target + N + eq gates).',
        epilog=(
            'Exit 0: *_pass. Exit 2: target_fit_review. '
            'Exit 3: unreachable_review. Exit 1: failed.'
        ),
    )
    parser.add_argument('--work-dir', required=True)
    parser.add_argument(
        '--param-dir', default=None,
        help='parameters-step2 dir for stage-ledger preflight (recommended)',
    )
    parser.add_argument(
        '--skip-preflight', action='store_true',
        help='Skip stage-order check (documented human approval only)',
    )
    parser.add_argument(
        '--phase', default='veg_exploration',
        choices=[
            'veg_exploration', 'soil_exploration',
            'nlevel', 'krb', 'cfall', 'nfall', 'soil',
            'phase6', 'phase7', 'main',
        ],
        help=('Gate: veg_exploration(NPP+VEGC+VEGNSTR+AVLN)|'
              'soil_exploration(SHLWC+DEEPC+MINEC)|'
              'krb(NPP)|cfall(VEGC)|nfall(VEGNSTR)|'
              'soil(SHLWC+DEEPC+MINEC)|phase6(MINEC)|phase7(soil alias)|'
              'main(all+eq)'),
    )
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
    parser.add_argument(
        '--flux-rel-err-pct', type=float, default=10.0,
        help='Max |rel_err_pct| for NPP* and VEGC* columns (default: 10)',
    )
    parser.add_argument(
        '--pool-rel-err-pct', type=float, default=20.0,
        help='Max |rel_err_pct| for SHLWC/DEEPC/MINEC/ORGN/AVLN (default: 20)',
    )
    parser.add_argument(
        '--require-eq-pass', action='store_true', default=True,
        help='Require eq pass on selected sample for non-chronic vars (default: on)',
    )
    parser.add_argument(
        '--no-require-eq-pass', action='store_false', dest='require_eq_pass',
        help='Disable equilibrium gate on selected sample',
    )
    return parser


def main():
    args = get_parser().parse_args()
    param_dir = args.param_dir or infer_param_dir_from_work_dir(args.work_dir)
    if param_dir and not args.skip_preflight:
        ledger_path = ledger_path_for_param_dir(param_dir)
        ledger = load_ledger(ledger_path)
        try:
            require_prerequisites(
                ledger, args.phase, param_dir=param_dir,
                force=args.skip_preflight)
        except RuntimeError as exc:
            print('PREFLIGHT FAILED: {}'.format(exc), file=sys.stderr)
            sys.exit(1)
    result = analyze(
        work_dir=args.work_dir,
        biome=args.biome,
        n_top=args.n_top,
        slope_lim=args.slope_lim,
        eps_lim=args.eps_lim,
        cv_lim=args.cv_lim,
        pft4_root_cv_lim=args.pft4_root_cv_lim,
        deepc_slope_lim=args.deepc_slope_lim,
        flux_rel_err_pct=args.flux_rel_err_pct,
        pool_rel_err_pct=args.pool_rel_err_pct,
        require_eq_pass=args.require_eq_pass,
        phase=args.phase,
        run_id=args.run_id,
        config_yaml=args.config_yaml,
        step1_result=args.step1_result,
        save_plots=args.save_plots,
    )

    print('run_id:              {}'.format(result['run_id']))
    print('phase:               {}'.format(result.get('phase', 'main')))
    print('status:              {}'.format(result['status']))
    if result['status'] == 'failed':
        print('notes:               {}'.format(result.get('notes', '')))
    else:
        print('best_rmse:           {}'.format(result['best_rmse']))
        print('best_r2:             {}'.format(result['best_r2']))
        print('best_sample:         {}'.format(result['best_sample_index']))
        print('selected N-pass:     {}'.format(result['selected_n_pass']))
        print('target_fit_pass:     {}'.format(result.get('target_fit_pass')))
        print('selected_eq_pass:    {}'.format(result.get('selected_eq_pass')))
        print('selected INGPP:GPP:  {}'.format(result['selected_n_ratio']))
        failing = result.get('failing_targets') or []
        if failing:
            print('failing_targets:     {} column(s)'.format(len(failing)))
            for ft in failing[:5]:
                print('  {} rel_err={:.1f}% limit={:.0f}%'.format(
                    ft['column'], ft['rel_err_pct'], ft['limit_pct']))
        eq_fail = result.get('failing_eq_vars') or []
        if eq_fail:
            print('failing_eq_vars:     {}'.format(', '.join(eq_fail[:8])))
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
    if result['status'] == 'unreachable_review':
        sys.exit(3)
    if result['status'] == 'target_fit_review':
        sys.exit(2)
    sys.exit(0)


if __name__ == '__main__':
    main()
