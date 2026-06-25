#!/usr/bin/env python
"""
Step 2 seed setup: copy parameters and fix cmax from Step 1 recommended_cmax.

Typical usage inside dvmdostem-autocal:

  python mads_calibration/agent_calibration_step2/seed_setup.py \\
    --step1-result /data/workflows/CMT04-IMN-sa-recovery-C/step1-result.yaml \\
    --cmtnum 4 \\
    --dest /data/workflows/CMT04-IMN/parameters-step2
"""

from __future__ import print_function

import argparse
import datetime
import os
import shutil
import sys

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MADS_CALIB_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT = os.path.dirname(MADS_CALIB_DIR)
SCRIPTS_DIR = os.path.join(REPO_ROOT, 'scripts')
if os.path.isdir(SCRIPTS_DIR) and SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import util.param as param  # noqa: E402

DEFAULT_SOURCE = '/work/parameters'
FALLBACK_SOURCE = os.path.join(REPO_ROOT, 'parameters')


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def recommended_cmax_from_step1(path):
    data = load_yaml(path)
    if 'recommended_cmax' not in data:
        raise ValueError('Expected recommended_cmax in {}'.format(path))
    return data['recommended_cmax'], data


def cmax_by_pft(recommended_cmax):
    values = {}
    for key, val in recommended_cmax.items():
        if not key.startswith('cmax_pft'):
            continue
        pft = int(key.replace('cmax_pft', ''))
        values[pft] = float(val)
    if not values:
        raise ValueError('No cmax_pft* keys in recommended_cmax')
    return values


def resolve_source(path):
    if path and os.path.isdir(path):
        return path
    if os.path.isdir(DEFAULT_SOURCE):
        return DEFAULT_SOURCE
    if os.path.isdir(FALLBACK_SOURCE):
        return FALLBACK_SOURCE
    raise RuntimeError(
        'No parameter source found. Tried: {!r}, {!r}, {!r}'.format(
            path, DEFAULT_SOURCE, FALLBACK_SOURCE
        )
    )


def copy_parameters(source, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(source, dest)


def apply_cmax_values(param_dir, cmax_values, cmtnum):
    for pft, value in sorted(cmax_values.items()):
        param.update_inplace(value, param_dir, 'cmax', cmtnum, pftnum=pft)


def write_manifest(manifest_path, step1_path, step1_data, dest, cmax_values, cmtnum, source):
    manifest = {
        'created': datetime.datetime.utcnow().isoformat() + 'Z',
        'cmtnum': cmtnum,
        'source_parameters': source,
        'dest_parameters': dest,
        'step1_result': os.path.abspath(step1_path),
        'step1_run_id': step1_data.get('run_id'),
        'step1_work_dir': step1_data.get('work_dir'),
        'applied_cmax': {
            'cmax_pft{}'.format(pft): val
            for pft, val in sorted(cmax_values.items())
        },
    }
    parent = os.path.dirname(os.path.abspath(manifest_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(manifest_path, 'w') as f:
        yaml.safe_dump(manifest, f, default_flow_style=False, sort_keys=False)
    return manifest_path


def get_parser():
    parser = argparse.ArgumentParser(
        description='Setup Step 2 seed parameters with fixed Step 1 cmax.'
    )
    parser.add_argument(
        '--step1-result', required=True,
        help='Path to step1-result.yaml/json (typically under /data/workflows/, not logs/)',
    )
    parser.add_argument('--cmtnum', type=int, required=True)
    parser.add_argument(
        '--dest', required=True,
        help='Destination parameters dir (e.g. .../parameters-step2)',
    )
    parser.add_argument(
        '--source', default=None,
        help='Source parameters dir (default: /work/parameters)',
    )
    parser.add_argument(
        '--manifest',
        default=None,
        help='Manifest yaml path (default: <parent-of-dest>/step2-seed-manifest.yaml)',
    )
    parser.add_argument('--dry-run', action='store_true')
    return parser


def main():
    args = get_parser().parse_args()
    recommended, step1_data = recommended_cmax_from_step1(args.step1_result)
    cmax_values = cmax_by_pft(recommended)
    source = resolve_source(args.source)

    manifest_path = args.manifest
    if manifest_path is None:
        manifest_path = os.path.join(
            os.path.dirname(os.path.abspath(args.dest)),
            'step2-seed-manifest.yaml',
        )

    print('Step 1 result: {}'.format(args.step1_result))
    print('Parameter source: {}'.format(source))
    print('Destination: {}'.format(args.dest))
    print('CMT: {}'.format(args.cmtnum))
    for pft in sorted(cmax_values):
        print('  cmax_pft{}: {:.6f}'.format(pft, cmax_values[pft]))

    if args.dry_run:
        print('Dry run — no files written.')
        return

    copy_parameters(source, args.dest)
    apply_cmax_values(args.dest, cmax_values, args.cmtnum)
    mpath = write_manifest(
        manifest_path, args.step1_result, step1_data,
        args.dest, cmax_values, args.cmtnum, source,
    )
    print('Wrote parameters to {}'.format(args.dest))
    print('Wrote manifest to {}'.format(mpath))


if __name__ == '__main__':
    main()
