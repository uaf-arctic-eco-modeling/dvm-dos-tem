#!/usr/bin/env python
"""
Propose Step 2 p_bounds from a prior SA sample_matrix.csv or step2-result.yaml.

Hybrid default: soil params averaged from --soil-samples, cfall from --veg-sample.
Use --step2-result to read best_sample_index from target-first analysis.

Usage (inside dvmdostem-autocal):

  python mads_calibration/agent/agent_calibration_step2/propose_bounds.py \\
    --work-dir /data/workflows/CMT04-IMN/logs/sa-step2-iter2/ \\
    --step2-result /data/workflows/CMT04-IMN/logs/sa-step2-iter2/step2-result.yaml \\
    --soil-samples 6,16 --veg-span 0.30 \\
    --yaml-out mads_calibration/logs/sa-IMN-step2-iter3-bounds.yaml
"""

from __future__ import print_function

import argparse
import os
import sys

import pandas as pd
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

SOIL_PARAMS = {'micbnup', 'kdcrawc', 'kdcsoma', 'kdcsompr', 'kdcsomcr'}
MIN_POSITIVE = 1e-6


def pft_indices_from_step1(path):
    """Active PFT indices from Step 1 recommended_cmax keys."""
    with open(path) as f:
        data = yaml.safe_load(f)
    recommended = data.get('recommended_cmax') or {}
    indices = []
    for key in recommended:
        if key.startswith('cmax_pft'):
            indices.append(int(key.replace('cmax_pft', '')))
    if not indices:
        raise ValueError('No cmax_pft* keys in {}'.format(path))
    return sorted(indices)


def step2_param_lists(pft_indices=None, pft_max=8):
    """Soil params + cfall(0/1/2) for each active PFT (Step 2 yaml layout)."""
    if pft_indices is None:
        pft_indices = list(range(pft_max + 1))
    soil = ['micbnup', 'kdcrawc', 'kdcsoma', 'kdcsompr', 'kdcsomcr']
    params = list(soil)
    pftnums = [None] * len(soil)
    for pft in pft_indices:
        for compartment in ('cfall(0)', 'cfall(1)', 'cfall(2)'):
            params.append(compartment)
            pftnums.append(pft)
    return params, pftnums


def parse_int_list(text):
    return [int(x.strip()) for x in text.split(',') if x.strip()]


def column_for_param(param, pftnum):
    if pftnum is None:
        return param
    return '{}_pft{}'.format(param, pftnum)


def span_bounds(center, span, floor=MIN_POSITIVE, cap=None):
    lo = center * (1.0 - span)
    hi = center * (1.0 + span)
    if center <= 0:
        lo, hi = floor, floor * 10.0
    lo = max(lo, floor)
    if cap is not None:
        hi = min(hi, cap)
    if lo >= hi:
        hi = lo * 1.5 + floor
    return [float(lo), float(hi)]


def load_step2_result(path):
    with open(path) as f:
        data = yaml.safe_load(f)
    return data


def propose_bounds(work_dir, soil_samples, veg_sample, soil_span, veg_span,
                   pft_indices=None):
    work_dir = os.path.abspath(work_dir)
    sm = pd.read_csv(os.path.join(work_dir, 'sample_matrix.csv'))
    params, pftnums = step2_param_lists(pft_indices=pft_indices)
    bounds = []

    for param, pftnum in zip(params, pftnums):
        col = column_for_param(param, pftnum)

        if param in SOIL_PARAMS:
            vals = [float(sm.loc[i, col]) for i in soil_samples]
            center = sum(vals) / float(len(vals))
            bounds.append(span_bounds(center, soil_span))
            continue

        center = float(sm.loc[veg_sample, col])
        cap = 5e-4 if center <= MIN_POSITIVE else None
        bounds.append(span_bounds(center, veg_span, cap=cap))

    return params, pftnums, bounds


def main():
    parser = argparse.ArgumentParser(description='Propose Step 2 p_bounds from prior SA.')
    parser.add_argument('--work-dir', required=True)
    parser.add_argument(
        '--step2-result', default=None,
        help='Use best_sample_index as --veg-sample when --veg-sample omitted',
    )
    parser.add_argument(
        '--soil-samples', default=None,
        help='Comma-separated sample indices for soil param centers (required unless only cfall from result)',
    )
    parser.add_argument('--veg-sample', type=int, default=None)
    parser.add_argument(
        '--step1-result', default=None,
        help='Derive active PFT list from recommended_cmax (matches Step 2 yaml)',
    )
    parser.add_argument(
        '--pft-max', type=int, default=None,
        help='Max PFT index inclusive (0..N); default 8 or from --step1-result',
    )
    parser.add_argument('--soil-span', type=float, default=0.25)
    parser.add_argument('--veg-span', type=float, default=0.30)
    parser.add_argument('--yaml-out', default=None,
                        help='Write [[lo,hi],...] list as yaml fragment')
    args = parser.parse_args()

    veg_sample = args.veg_sample
    if veg_sample is None and args.step2_result:
        result = load_step2_result(args.step2_result)
        veg_sample = int(result['best_sample_index'])
        print('# veg-sample from step2-result: {}'.format(veg_sample))

    if veg_sample is None:
        parser.error('Provide --veg-sample or --step2-result with best_sample_index')

    if args.soil_samples:
        soil_samples = parse_int_list(args.soil_samples)
    else:
        soil_samples = [veg_sample]

    if args.step1_result:
        pft_indices = pft_indices_from_step1(args.step1_result)
        print('# active PFTs from step1-result: {}'.format(pft_indices))
    elif args.pft_max is not None:
        pft_indices = list(range(args.pft_max + 1))
        print('# active PFTs 0..{}'.format(args.pft_max))
    else:
        pft_indices = list(range(9))
        print('# active PFTs default 0..8')

    params, pftnums, bounds = propose_bounds(
        args.work_dir,
        soil_samples=soil_samples,
        veg_sample=veg_sample,
        soil_span=args.soil_span,
        veg_span=args.veg_span,
        pft_indices=pft_indices,
    )

    print('# p_bounds for {} params (soil from {}, cfall from {})'.format(
        len(bounds), soil_samples, veg_sample))
    for (param, pftnum), b in zip(zip(params, pftnums), bounds):
        pft = '' if pftnum is None else '_pft{}'.format(pftnum)
        print('  # {}{}: [{:.6g}, {:.6g}]'.format(param, pft, b[0], b[1]))

    if args.yaml_out:
        out_dir = os.path.dirname(os.path.abspath(args.yaml_out))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.yaml_out, 'w') as f:
            yaml.safe_dump({'p_bounds': bounds}, f, default_flow_style=True)
        print('\nWrote {}'.format(args.yaml_out))


if __name__ == '__main__':
    main()
