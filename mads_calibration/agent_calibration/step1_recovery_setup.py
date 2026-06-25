#!/usr/bin/env python
"""
Parameterized recovery seed setup for Step 1 cmax perturbation runs A–D.

Parameterized recovery seed setup: accepts custom cmtnum, manifest path,
and reference optima from a prior step1_analyze.py result or hand-written yaml.

Typical usage inside dvmdostem-autocal:

  python mads_calibration/agent_calibration/step1_recovery_setup.py \\
    --manifest /work/mads_calibration/agent_calibration/recovery_cmax_optima.yaml \\
    --reference-cmax-yaml /data/workflows/CMT04-IMN-sa-N100/step1-result.yaml \\
    --write-manifest /data/workflows/CMT04-IMN/recovery-manifest.yaml \\
    --cmtnum 4 \\
    --dest-base /data/workflows/CMT04-IMN \\
    --runs A B C D

Manifest format (same as recovery_cmax_optima.yaml):

  reference_optima:
    cmax_pft0: 243.20
    ...
  bias_tiers:
    mild: {pft0: 50, ...}
    strong: {pft0: 100, ...}
  runs:
    A: {label: recovery-plus-mild, direction: 1, tier: mild}
    ...
"""

from __future__ import print_function

import argparse
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
DEFAULT_MANIFEST = os.path.join(SCRIPT_DIR, 'recovery_cmax_optima.yaml')


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def reference_from_step1_result(path):
    """Build reference_optima dict from step1_analyze.py output artifact."""
    data = load_yaml(path)
    if 'recommended_cmax' in data:
        return data['recommended_cmax']
    if 'reference_optima' in data:
        return data['reference_optima']
    raise ValueError(
        'Expected recommended_cmax or reference_optima in {}'.format(path)
    )


def merge_reference_into_manifest(manifest, reference_optima, pft_keys=None):
    """Ensure manifest has reference_optima; optionally restrict to active PFTs."""
    manifest = dict(manifest)
    manifest['reference_optima'] = dict(reference_optima)
    if pft_keys:
        manifest['reference_optima'] = {
            k: v for k, v in reference_optima.items() if k in pft_keys
        }
    return manifest


def active_pft_indices(manifest):
    """Return sorted PFT indices present in reference_optima."""
    indices = []
    for key in manifest.get('reference_optima', {}):
        if key.startswith('cmax_pft'):
            indices.append(int(key.replace('cmax_pft', '')))
    return sorted(indices)


def compute_seed_cmax(manifest, run_key, cmtnum):
    run = manifest['runs'][run_key]
    tier = manifest['bias_tiers'][run['tier']]
    direction = run['direction']
    optima = manifest['reference_optima']

    values = {}
    for pft in active_pft_indices(manifest):
        key = 'cmax_pft{}'.format(pft)
        if key not in optima:
            raise KeyError('Missing {} in reference_optima'.format(key))
        pft_key = 'pft{}'.format(pft)
        bias = tier.get(pft_key, tier.get(str(pft), 0))
        values[pft] = optima[key] + direction * bias
        if values[pft] <= 0:
            raise ValueError(
                'Run {} PFT{} would be non-positive ({:.4f}). '
                'Reduce negative bias for this PFT.'.format(
                    run_key, pft, values[pft]
                )
            )
    return values


def copy_parameters(source, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(source, dest)


def apply_cmax_values(param_dir, cmax_by_pft, cmtnum):
    for pft, value in sorted(cmax_by_pft.items()):
        param.update_inplace(value, param_dir, 'cmax', cmtnum, pftnum=pft)


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


def setup_run(run_key, manifest, source, dest_base, cmtnum, dry_run=False):
    run = manifest['runs'][run_key]
    seed_dir = os.path.join(dest_base, 'parameters-recovery-{}'.format(run_key))
    cmax_values = compute_seed_cmax(manifest, run_key, cmtnum)

    print('\n=== Run {} ({}) ==='.format(run_key, run.get('label', '')))
    print('  seed_path: {}'.format(seed_dir))
    for pft in sorted(cmax_values):
        print('  cmax_pft{}: {:.6f}'.format(pft, cmax_values[pft]))

    if dry_run:
        return seed_dir, cmax_values

    copy_parameters(source, seed_dir)
    apply_cmax_values(seed_dir, cmax_values, cmtnum)
    print('  -> seed directory written')
    return seed_dir, cmax_values


def get_parser():
    parser = argparse.ArgumentParser(
        description='Setup perturbed cmax seed dirs for Step 1 recovery SA runs.'
    )
    parser.add_argument(
        '--manifest',
        default=DEFAULT_MANIFEST,
        help='Recovery manifest yaml (default: recovery_cmax_optima.yaml)',
    )
    parser.add_argument(
        '--reference-cmax-yaml',
        default=None,
        help='Override reference_optima from step1-result.yaml/json',
    )
    parser.add_argument(
        '--cmtnum', type=int, required=True,
        help='Community type number (e.g. 4)',
    )
    parser.add_argument(
        '--source',
        default=None,
        help='Source parameters dir (default: /work/parameters)',
    )
    parser.add_argument(
        '--dest-base', required=True,
        help='Base workflow dir for seed copies (e.g. /data/workflows/CMT04-IMN)',
    )
    parser.add_argument(
        '--runs',
        nargs='+',
        default=['A', 'B', 'C', 'D'],
        help='Which recovery runs to setup (default: A B C D)',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print values only; do not copy or modify files',
    )
    parser.add_argument(
        '--write-manifest',
        default=None,
        help='Write merged manifest (with reference optima) to this path',
    )
    return parser


def main():
    args = get_parser().parse_args()
    manifest = load_yaml(args.manifest)

    if args.reference_cmax_yaml:
        reference = reference_from_step1_result(args.reference_cmax_yaml)
        manifest = merge_reference_into_manifest(manifest, reference)

    if 'reference_optima' not in manifest:
        raise RuntimeError(
            'Manifest missing reference_optima. Pass --reference-cmax-yaml '
            'with output from step1_analyze.py.'
        )

    if args.write_manifest:
        parent = os.path.dirname(os.path.abspath(args.write_manifest))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(args.write_manifest, 'w') as f:
            yaml.safe_dump(manifest, f, default_flow_style=False, sort_keys=False)
        print('Wrote manifest to {}'.format(args.write_manifest))

    source = resolve_source(args.source)
    print('Parameter source: {}'.format(source))
    print('Destination base: {}'.format(args.dest_base))
    print('CMT number: {}'.format(args.cmtnum))

    for run_key in args.runs:
        if run_key not in manifest.get('runs', {}):
            raise KeyError('Run {} not defined in manifest'.format(run_key))
        setup_run(
            run_key, manifest, source, args.dest_base,
            args.cmtnum, dry_run=args.dry_run,
        )

    if not args.dry_run:
        print('\nSeed directories ready under {}'.format(args.dest_base))


if __name__ == '__main__':
    main()
