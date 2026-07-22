#!/usr/bin/env python
"""
Apply recommended_params from step2-result.yaml to workflow parameter files.

Uses util.param.update_inplace (routes to cmt_calparbgc.txt or cmt_bgcsoil.txt).

  python .../param_update.py --phase cfall --step2-result .../step2-result.yaml \\
    --param-dir .../parameters-step2 --cmtnum 4

Phases: veg_exploration | soil_exploration | nlevel | krb | cfall | nfall |
        soil | phase6 | phase7 | main(legacy)
micbnup is applied via --phase soil_exploration (or legacy nlevel).
"""

from __future__ import print_function

import argparse
import os
import re
import sys

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MADS_CALIB_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT = os.path.dirname(MADS_CALIB_DIR)
SCRIPTS_DIR = os.path.join(REPO_ROOT, 'scripts')
if os.path.isdir(SCRIPTS_DIR) and SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import util.param as param  # noqa: E402

from stage_ledger import (  # noqa: E402
    ledger_path_for_param_dir,
    load_ledger,
    record_stage_apply,
    save_ledger,
)

PFT_COL_RE = re.compile(r'^(.+)_pft(\d+)$')

PHASE_REQUIRED_STATUS = {
    'veg_exploration': 'veg_pass',
    'soil_exploration': 'soil_pass',
    'nlevel': 'nlevel_pass',
    'krb': 'krb_pass',
    'cfall': 'cfall_pass',
    'nfall': 'nfall_pass',
    'soil': 'soil_pass',
    'phase6': 'phase6_pass',
    'phase7': 'phase7_pass',
    'main': 'pass',  # optional post-hoc on old integrated work_dirs only
}

# Base param names (pre-`_pftN`) allowed per phase.
KDC_PARAMS = frozenset(('kdcrawc', 'kdcsoma', 'kdcsompr', 'kdcsomcr'))
KDC_ORDER = ('kdcrawc', 'kdcsoma', 'kdcsompr', 'kdcsomcr')
SOIL_KDC_PHASES = frozenset(('soil', 'soil_exploration', 'phase7'))
VEG_COMPARTMENTS = frozenset((
    'krb(0)', 'krb(1)', 'krb(2)',
    'cfall(0)', 'cfall(1)', 'cfall(2)',
    'nfall(0)', 'nfall(1)', 'nfall(2)',
))
PHASE_PARAM_NAMES = {
    'veg_exploration': frozenset(('nmax',)) | VEG_COMPARTMENTS,
    'soil_exploration': frozenset(('micbnup',)) | KDC_PARAMS,
    'nlevel': frozenset(('micbnup', 'nmax')),
    'krb': frozenset(('krb(0)', 'krb(1)', 'krb(2)')),
    'cfall': frozenset(('cfall(0)', 'cfall(1)', 'cfall(2)')),
    'nfall': frozenset(('nfall(0)', 'nfall(1)', 'nfall(2)')),
    'soil': KDC_PARAMS,
    'phase7': KDC_PARAMS,
}


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def parse_param_key(key):
    m = PFT_COL_RE.match(key)
    if m:
        return m.group(1), int(m.group(2))
    return key, None


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


def require_kdc_ordering(recommended_params, phase, force=False):
    if phase not in SOIL_KDC_PHASES:
        return
    valid, violations = validate_kdc_ordering(recommended_params)
    if valid or force:
        return
    raise RuntimeError(
        'Refusing to apply parameters: kdc ordering violation(s): {}. '
        'Use --force only with documented human approval.'.format(
            '; '.join(violations)))


def apply_recommended(param_dir, recommended_params, cmtnum, dry_run=False):
    for key, value in sorted(recommended_params.items()):
        pname, pftnum = parse_param_key(key)
        print('  {} = {} (pft={})'.format(pname, value, pftnum))
        if dry_run:
            continue
        param.update_inplace(float(value), param_dir, pname, cmtnum, pftnum=pftnum)


def filter_params_for_phase(recommended_params, phase):
    """Return subset of recommended_params allowed for this apply phase."""
    if phase == 'main':
        return recommended_params
    filtered = {}
    allowed = PHASE_PARAM_NAMES.get(phase)
    for key, value in recommended_params.items():
        pname, _ = parse_param_key(key)
        if phase == 'phase6' and 'rhmoistfrozen' in pname:
            filtered[key] = value
        elif allowed is not None and pname in allowed:
            filtered[key] = value
    return filtered


def require_pass_status(data, phase='cfall'):
    """Refuse apply unless analyze.py reported the expected status for phase."""
    status = data.get('status')
    result_phase = data.get('phase', 'main')
    required = PHASE_REQUIRED_STATUS[phase]
    if status != required:
        raise RuntimeError(
            'Refusing to apply parameters: step2-result status is {!r}, not {!r}. '
            'Keep seed_path fixed; take bounds from sample_matrix / propose_bounds. '
            'Use --force only with documented human approval.'.format(
                status, required))
    if phase != 'main' and result_phase != phase:
        raise RuntimeError(
            'Refusing to apply: step2-result phase is {!r}, but --phase is {!r}. '
            'Re-run analyze.py with --phase {}.'.format(
                result_phase, phase, phase))


def get_parser():
    parser = argparse.ArgumentParser(
        description='Write Step 2 recommended_params into workflow parameter files.'
    )
    parser.add_argument('--step2-result', required=True)
    parser.add_argument('--param-dir', required=True)
    parser.add_argument('--cmtnum', type=int, required=True)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument(
        '--phase', default='veg_exploration',
        choices=sorted(PHASE_REQUIRED_STATUS),
        help='Apply scope matching analyze --phase (default: veg_exploration)',
    )
    parser.add_argument(
        '--ledger',
        default=None,
        help='Stage ledger yaml (default: <workflow>/step2-stage-ledger.yaml)',
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Apply even when status does not match phase (documented approval only)',
    )
    return parser


def main():
    args = get_parser().parse_args()
    data = load_yaml(args.step2_result)
    if not args.force:
        require_pass_status(data, phase=args.phase)
    recommended = filter_params_for_phase(
        data.get('recommended_params') or {}, args.phase)
    if not recommended:
        raise RuntimeError(
            'No parameters to apply for phase {!r} in {}'.format(
                args.phase, args.step2_result))

    require_kdc_ordering(recommended, args.phase, force=args.force)

    print('Applying {} parameters ({}) to {}'.format(
        len(recommended), args.phase, args.param_dir))
    apply_recommended(args.param_dir, recommended, args.cmtnum, dry_run=args.dry_run)
    if not args.dry_run:
        ledger_path = args.ledger or ledger_path_for_param_dir(args.param_dir)
        ledger = load_ledger(ledger_path) or {'param_dir': os.path.abspath(args.param_dir)}
        ledger = record_stage_apply(
            ledger,
            args.phase,
            args.step2_result,
            PHASE_REQUIRED_STATUS[args.phase],
            work_dir=data.get('work_dir'),
            run_id=data.get('run_id'),
        )
        save_ledger(ledger_path, ledger)
        print('Updated stage ledger: {}'.format(ledger_path))
        print('Done.')


if __name__ == '__main__':
    main()
