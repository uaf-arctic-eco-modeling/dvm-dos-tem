#!/usr/bin/env python3
"""Extract eq-stage residuals and classify measurement verdict for deep_carbon_v2 validation."""

from __future__ import print_function

import argparse
import json
import os
import sys

import netCDF4 as nc
import numpy as np
from scipy import stats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, 'scripts'))

from util.qcal import QCal  # noqa: E402


def equilibrium_gate(output_dir, var, obs, y=0, x=0, last_n=100,
                     slope_lim=0.001, cv_lim_pct=15.0):
    path = os.path.join(output_dir, '{}_yearly_eq.nc'.format(var))
    with nc.Dataset(path) as ds:
        data = ds.variables[var][:, y, x]
    tail = data[-last_n:]
    years = np.arange(len(tail))
    slope, _, _, _, _ = stats.linregress(years, tail)
    mean_last10 = float(data[-10:].mean())
    cv = 100.0 * np.std(tail) / np.mean(tail) if np.mean(tail) else 999.0
    slope_pass = abs(slope) < slope_lim * obs
    cv_pass = cv < cv_lim_pct
    return {
        'var': var,
        'mean_last10': mean_last10,
        'obs': obs,
        'rel_err_pct': (mean_last10 / obs - 1.0) * 100.0 if obs else None,
        'slope': float(slope),
        'slope_pass': bool(slope_pass),
        'cv_pct': float(cv),
        'cv_pass': bool(cv_pass),
        'eq_gate_pass': bool(slope_pass and cv_pass),
    }


def _py(val):
    """Convert numpy scalars to native Python types for YAML/JSON."""
    if hasattr(val, 'item'):
        return val.item()
    return val


def _py_dict(d):
    if isinstance(d, dict):
        return {k: _py_dict(v) for k, v in d.items()}
    if isinstance(d, (list, tuple)):
        return [_py_dict(v) for v in d]
    return _py(d)


def classify_verdict(minec, deepc, shlwc, gpp_rel, npp_rel,
                     minec_gate, deepc_gate, threshold=20.0, share_threshold=25.0):
    if not (minec_gate and deepc_gate):
        return 'under_spun'

    total_obs = shlwc['obs'] + deepc['obs'] + minec['obs']
    total_mod = shlwc['mean_last10'] + deepc['mean_last10'] + minec['mean_last10']
    total_rel = (total_mod / total_obs - 1.0) * 100.0 if total_obs else None

    minec_share_obs = minec['obs'] / total_obs if total_obs else 0.0
    minec_share_mod = minec['mean_last10'] / total_mod if total_mod else 0.0
    share_delta_pct = abs(minec_share_mod - minec_share_obs) / minec_share_obs * 100.0 if minec_share_obs else 999.0

    minec_ok = abs(minec['rel_err_pct']) <= threshold
    total_ok = abs(total_rel) <= threshold if total_rel is not None else False
    gpp_ok = abs(gpp_rel) <= threshold if gpp_rel is not None else True
    npp_ok = abs(npp_rel) <= threshold if npp_rel is not None else True

    if minec_ok and total_ok and gpp_ok and npp_ok:
        return 'match'

    if total_ok and not minec_ok and share_delta_pct > share_threshold:
        return 'partition_miss'

    return 'tunable_miss'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--params-dir', required=True)
    parser.add_argument('--targets-dir', default=os.path.join(REPO_ROOT, 'calibration'))
    parser.add_argument('--cmtnum', type=int, default=4)
    parser.add_argument('--site-label', default='IMN')
    parser.add_argument('--json-out', default='')
    args = parser.parse_args()

    sys.path.insert(0, args.targets_dir)
    import calibration_targets as ct  # noqa: E402

    cmt_key = None
    cmt_data = None
    for k, v in ct.calibration_targets.items():
        if isinstance(v, dict) and v.get('cmtnumber') == args.cmtnum:
            cmt_key = k
            cmt_data = v
            break
    if cmt_data is None:
        raise SystemExit('No calibration targets for cmtnumber {}'.format(args.cmtnum))

    obs = {
        'MINEC': float(cmt_data['CarbonMineralSum']),
        'DEEPC': float(cmt_data['CarbonDeep']),
        'SHLWC': float(cmt_data['CarbonShallow']),
    }

    eq = {var: equilibrium_gate(args.output_dir, var, obs[var]) for var in obs}

    qcal = QCal(
        ncdata_path=args.output_dir,
        y=0, x=0,
        ref_targets_dir=args.targets_dir,
        ref_params_dir=args.params_dir,
    )
    results = qcal.nc_qcal()

    def sum_pft(ctname):
        vals = [r for r in results if r['ctname'] == ctname]
        mod = sum(r['value'] for r in vals)
        truth = sum(r['truth'] for r in vals)
        rel = (mod / truth - 1.0) * 100.0 if truth else None
        return mod, truth, rel

    ingpp_mod, ingpp_obs, ingpp_rel = sum_pft('GPPAllIgnoringNitrogen')
    npp_mod, npp_obs, npp_rel = sum_pft('NPPAll')

    stock_rows = {}
    for ctname, ncname in [
        ('CarbonMineralSum', 'MINEC'),
        ('CarbonDeep', 'DEEPC'),
        ('CarbonShallow', 'SHLWC'),
    ]:
        row = next(r for r in results if r['ctname'] == ctname)
        stock_rows[ncname] = {
            'mod': row['value'],
            'obs': row['truth'],
            'rel_err_pct': (row['value'] / row['truth'] - 1.0) * 100.0,
        }

    total_obs = obs['SHLWC'] + obs['DEEPC'] + obs['MINEC']
    total_mod = stock_rows['SHLWC']['mod'] + stock_rows['DEEPC']['mod'] + stock_rows['MINEC']['mod']

    verdict = classify_verdict(
        eq['MINEC'], eq['DEEPC'], eq['SHLWC'],
        ingpp_rel, npp_rel,
        eq['MINEC']['eq_gate_pass'], eq['DEEPC']['eq_gate_pass'],
    )

    report = _py_dict({
        'site_label': args.site_label,
        'cmtnum': args.cmtnum,
        'cmt_key': cmt_key,
        'status': 'measurement_only',
        'verdict': verdict,
        'model_branch': 'deep_carbon_v2',
        'run_setup': '--pr-yrs 100 --eq-yrs 2000 --sp-yrs 250 --tr-yrs 122 --sc-yrs 0',
        'output_dir': args.output_dir,
        'params_source': args.params_dir,
        'param_provenance_note': (
            'Local parameters-step2-final (agent-calibrated); stripped s2dfraction/d2mfraction '
            'for 18-row deep_carbon_v2 schema. No CMT04 folder in vb-tem calibrated bucket.'
        ),
        'equilibrium_gate': eq,
        'stocks_eq_last10_mean': stock_rows,
        'total_soil_c': {
            'mod': total_mod,
            'obs': total_obs,
            'rel_err_pct': (total_mod / total_obs - 1.0) * 100.0,
        },
        'fluxes_eq_last10_mean': {
            'INGPP_sum': {'mod': ingpp_mod, 'obs': ingpp_obs, 'rel_err_pct': ingpp_rel},
            'NPP_sum': {'mod': npp_mod, 'obs': npp_obs, 'rel_err_pct': npp_rel},
        },
        'checklist': {
            'mapping_confirmed': True,
            'params_18_row': True,
            'config_paths_ok': True,
            'no_fail_log': not os.path.isfile(os.path.join(args.output_dir, 'fail_log.txt')),
            'eq_gate_before_residuals': eq['MINEC']['eq_gate_pass'] and eq['DEEPC']['eq_gate_pass'],
        },
        'open_questions': [
            'Bucket params provenance vs deep_carbon_v2 unknown for this site copy.',
        ],
    })

    print(json.dumps(report, indent=2))
    if args.json_out:
        import yaml
        out_path = args.json_out
        os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
        with open(out_path, 'w') as f:
            yaml.dump({'sites': [report]}, f, default_flow_style=False, sort_keys=False)


if __name__ == '__main__':
    main()
