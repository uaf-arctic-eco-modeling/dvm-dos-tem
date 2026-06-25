"""Workdir-based equilibrium checks from collated eq_*_quality.csv files."""

from __future__ import print_function

import glob
import os

import pandas as pd


def _eq_col_base(col):
    """MINEC_eq_slope -> MINEC; VEGC_pft0_Leaf_eq_cv -> VEGC_pft0_Leaf."""
    return col.rsplit('_eq_', 1)[0]


def build_step2_lim_dict(targets, cv_lim, eps_lim, slope_lim,
                         pft4_root_cv_lim=None, deepc_slope_lim=None):
    """Per-variable eq thresholds; relax sparse-pool and slow-soil gates when requested."""
    lim = {
        'cv_lim': cv_lim,
        'p_lim': eps_lim,
        'slope_lim': slope_lim,
    }
    if pft4_root_cv_lim is not None:
        lim['VEGC_pft4_Root_cv_lim'] = pft4_root_cv_lim
    if deepc_slope_lim is not None:
        lim['DEEPC_slope_lim'] = deepc_slope_lim
    return lim


def equilibrium_check_from_workdir(work_dir, targets, cv_lim=1.0, p_lim=1e-5,
                                   slope_lim=1e-3, lim_dict=None):
    """
    Build eq pass/fail tables from collated eq_*_quality.csv files in work_dir.

    Returns (counts, eq_check, eq_var_check, eq_data, eq_metrics, lim_used)
    with leading None placeholders for legacy 7-tuple callers.
    """
    eq_files = sorted(glob.glob(os.path.join(work_dir, 'eq_*_quality.csv')))
    if not eq_files:
        raise RuntimeError('No eq_*_quality.csv files in {}'.format(work_dir))

    eq_metrics = pd.concat([pd.read_csv(f) for f in eq_files], axis=1)
    n_samples = len(eq_metrics)

    eq_data = pd.DataFrame(index=range(n_samples), columns=eq_metrics.columns,
                           data=False)
    bases = sorted(set(_eq_col_base(c) for c in eq_metrics.columns))
    eq_var_check = pd.DataFrame(index=range(n_samples), columns=bases, data=False)

    targ_row = targets.iloc[0]

    for base in bases:
        slope_col = base + '_eq_slope'
        p_col = base + '_eq_p'
        cv_col = base + '_eq_cv'
        if slope_col not in eq_metrics.columns:
            continue

        col_cv_lim = cv_lim
        col_slope_lim = slope_lim
        col_p_lim = p_lim
        if lim_dict:
            col_cv_lim = lim_dict.get(base + '_cv_lim', lim_dict.get('cv_lim', cv_lim))
            col_slope_lim = lim_dict.get(
                base + '_slope_lim', lim_dict.get('slope_lim', slope_lim))
            col_p_lim = lim_dict.get('p_lim', p_lim)

        if base not in targ_row.index:
            targ_val = float(targ_row[base]) if base in targ_row else 1.0
        else:
            targ_val = float(targ_row[base])

        for i in range(n_samples):
            cv_ok = abs(eq_metrics[cv_col].iloc[i]) * 100 < col_cv_lim
            p_ok = eq_metrics[p_col].iloc[i] < col_p_lim
            slope_ok = abs(eq_metrics[slope_col].iloc[i]) < col_slope_lim * targ_val
            eq_data[cv_col].iloc[i] = cv_ok
            eq_data[p_col].iloc[i] = p_ok
            eq_data[slope_col].iloc[i] = slope_ok
            eq_var_check[base].iloc[i] = cv_ok and p_ok and slope_ok

    counts = eq_var_check.apply(pd.value_counts)
    lim_used = lim_dict if lim_dict else {
        'cv_lim': cv_lim, 'p_lim': p_lim, 'slope_lim': slope_lim,
    }
    return None, None, None, eq_var_check, eq_data, eq_metrics, lim_used
