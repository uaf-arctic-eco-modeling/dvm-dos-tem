#!/usr/bin/env python
"""
Apply recommended_params from step2-result.yaml to workflow parameter files.

Uses util.param.update_inplace (routes to cmt_calparbgc.txt or cmt_bgcsoil.txt).

  python mads_calibration/agent_calibration_step2/param_update.py \\
    --step2-result /data/workflows/CMT04-IMN-sa-step2/step2-result.yaml \\
    --param-dir /data/workflows/CMT04-IMN/parameters-step2 \\
    --cmtnum 4
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


def get_parser():
    parser = argparse.ArgumentParser(
        description='Write Step 2 recommended_params into workflow parameter files.'
    )
    parser.add_argument('--step2-result', required=True)
    parser.add_argument('--param-dir', required=True)
    parser.add_argument('--cmtnum', type=int, required=True)
    parser.add_argument('--dry-run', action='store_true')
    return parser


def main():
    args = get_parser().parse_args()
    data = load_yaml(args.step2_result)
    recommended = data.get('recommended_params') or {}
    if not recommended:
        raise RuntimeError('No recommended_params in {}'.format(args.step2_result))

    print('Applying {} parameters to {}'.format(len(recommended), args.param_dir))
    apply_recommended(args.param_dir, recommended, args.cmtnum, dry_run=args.dry_run)
    if not args.dry_run:
        print('Done.')


if __name__ == '__main__':
    main()
