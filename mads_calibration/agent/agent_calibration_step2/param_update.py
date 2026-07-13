#!/usr/bin/env python
"""
Apply recommended_params from step2-result.yaml to workflow parameter files.

Uses util.param.update_inplace (routes to cmt_calparbgc.txt or cmt_bgcsoil.txt).

  # Main apply (all params, requires status: pass):
  python mads_calibration/agent/agent_calibration_step2/param_update.py \\
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-iter3/step2-result.yaml \\
    --param-dir /data/workflows/CMT04-IMN/parameters-step2 \\
    --cmtnum 4

  # N-level (micbnup+nmax only, requires status: nlevel_pass):
  python .../param_update.py --phase nlevel --step2-result .../sa-step2-nlevel/step2-result.yaml ...

  # Krb (krb(0/1/2) only, requires status: krb_pass):
  python .../param_update.py --phase krb --step2-result .../sa-step2-krb/step2-result.yaml ...

  # Nfall (nfall(0/1/2) only, requires status: nfall_pass):
  python .../param_update.py --phase nfall --step2-result .../sa-step2-nfall/step2-result.yaml ...

  # Phase 6 (rhmoistfrozen only, requires status: phase6_pass):
  python .../param_update.py --phase phase6 --step2-result .../sa-step2-rhmoistfrozen/step2-result.yaml ...

  # Phase 7 (soil kdc*/micbnup only, requires status: phase7_pass):
  python .../param_update.py --phase phase7 --step2-result .../sa-step2-soil-retune/step2-result.yaml ...

  --force applies even when status does not match (documented approval only).
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

PFT_COL_RE = re.compile(r'^(.+)_pft(\d+)$')

PASSING_STATUSES = frozenset((
    'pass', 'nlevel_pass', 'krb_pass', 'nfall_pass',
    'phase6_pass', 'phase7_pass',
))

PHASE_REQUIRED_STATUS = {
    'main': 'pass',
    'nlevel': 'nlevel_pass',
    'krb': 'krb_pass',
    'nfall': 'nfall_pass',
    'phase6': 'phase6_pass',
    'phase7': 'phase7_pass',
}

# Base param names (pre-`_pftN` split) allowed for each non-main apply phase.
# nlevel/krb/nfall mirror propose_bounds.py's PARAM_FAMILIES; phase7 mirrors
# the original soil-only apply scope.
PHASE7_PARAM_NAMES = frozenset((
    'micbnup', 'kdcrawc', 'kdcsoma', 'kdcsompr', 'kdcsomcr',
))

PHASE_PARAM_NAMES = {
    'nlevel': frozenset(('micbnup', 'nmax')),
    'krb': frozenset(('krb(0)', 'krb(1)', 'krb(2)')),
    'nfall': frozenset(('nfall(0)', 'nfall(1)', 'nfall(2)')),
    'phase7': PHASE7_PARAM_NAMES,
}


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def parse_param_key(key):
    m = PFT_COL_RE.match(key)
    if m:
        return m.group(1), int(m.group(2))
    return key, None


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


def require_pass_status(data, phase='main'):
    """Refuse apply unless analyze.py reported the expected status for phase."""
    status = data.get('status')
    result_phase = data.get('phase', 'main')
    required = PHASE_REQUIRED_STATUS[phase]
    if status != required:
        raise RuntimeError(
            'Refusing to apply parameters: step2-result status is {!r}, not {!r}. '
            'Do not write mid-loop SA samples into parameters-step2 — keep seed_path '
            'fixed and take bounds from sample_matrix.csv / propose_bounds.py. '
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
        '--phase', default='main',
        choices=['main', 'nlevel', 'krb', 'nfall', 'phase6', 'phase7'],
        help='Apply scope: main (all params, status pass), '
             'nlevel (micbnup+nmax), krb (Krb), nfall (Nfall), '
             'phase6 (rhmoistfrozen), phase7 (soil kdc*/micbnup)',
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

    print('Applying {} parameters ({}) to {}'.format(
        len(recommended), args.phase, args.param_dir))
    apply_recommended(args.param_dir, recommended, args.cmtnum, dry_run=args.dry_run)
    if not args.dry_run:
        print('Done.')


if __name__ == '__main__':
    main()
