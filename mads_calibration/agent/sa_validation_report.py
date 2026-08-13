#!/usr/bin/env python
"""
SA Validation Report — multi-page PDF of post-hoc analysis figures.

Generates a PDF that bundles SA post-hoc visualizations and summary metrics
so the user can validate the headless calibration process at each step.

Typical usage inside dvmdostem-autocal:

  python mads_calibration/agent/sa_validation_report.py \
    --work-dir /data/workflows/CMT04-IMN/sa-step2-veg-exploration/ \
    --result-yaml /data/workflows/CMT04-IMN/sa-step2-veg-exploration/step2-result.yaml \
    --phase veg_exploration \
    --biome tundra \
    --output /data/workflows/CMT04-IMN/sa-step2-veg-exploration/sa-validation-report.pdf
"""

from __future__ import print_function

import argparse
import datetime
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MADS_CALIB_DIR = os.path.dirname(SCRIPT_DIR)
if MADS_CALIB_DIR not in sys.path:
    sys.path.insert(0, MADS_CALIB_DIR)

import SA_post_hoc_analysis as sa  # noqa: E402


def _text_page(lines, title=None, fontsize=9):
    """Render a list of text lines as a matplotlib figure page."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis('off')
    text = '\n'.join(lines)
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', loc='left', pad=20)
    ax.text(0.02, 0.95, text, transform=ax.transAxes,
            fontsize=fontsize, verticalalignment='top',
            fontfamily='monospace')
    return fig


def _summary_page(result, work_dir, phase, biome):
    """Page 1: run summary with key metrics."""
    lines = []
    lines.append('SA Validation Report')
    lines.append('=' * 60)
    lines.append('')
    lines.append('Generated:    {}'.format(
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    lines.append('Work dir:     {}'.format(work_dir))
    lines.append('Phase:        {}'.format(phase or 'n/a'))
    lines.append('Biome:        {}'.format(biome or 'n/a'))
    lines.append('')

    if result:
        lines.append('Run ID:       {}'.format(result.get('run_id', 'n/a')))
        lines.append('Status:       {}'.format(result.get('status', 'n/a')))
        lines.append('')
        lines.append('--- Key Metrics ---')
        lines.append('Best R2:            {}'.format(
            _fmt(result.get('best_r2'))))
        lines.append('Best RMSE:          {}'.format(
            _fmt(result.get('best_rmse'))))
        lines.append('Best sample index:  {}'.format(
            result.get('best_sample_index', 'n/a')))
        lines.append('N total samples:    {}'.format(
            result.get('n_total_samples', 'n/a')))
        lines.append('N eq passing:       {}'.format(
            result.get('n_eq_passing', 'n/a')))
        lines.append('N nitrogen passing: {}'.format(
            result.get('n_nitrogen_passing', 'n/a')))
        n_rate = result.get('nitrogen_pass_rate')
        lines.append('Nitrogen pass rate: {}'.format(
            '{:.1%}'.format(n_rate) if n_rate is not None else 'n/a'))
        lines.append('')

        # Target fit details
        failing = result.get('failing_targets') or []
        if failing:
            lines.append('--- Failing Targets ---')
            lines.append('{:<25s} {:>8s} {:>8s} {:>10s} {:>8s}'.format(
                'Column', 'Obs', 'Mod', 'RelErr%', 'Limit%'))
            for ft in failing:
                lines.append('{:<25s} {:>8s} {:>8s} {:>10.1f} {:>8.0f}'.format(
                    ft.get('column', '?'),
                    _fmt(ft.get('obs')),
                    _fmt(ft.get('mod')),
                    ft.get('rel_err_pct', 0),
                    ft.get('limit_pct', 0)))
            lines.append('')

        # Recommended params (brief)
        rec = result.get('recommended_params') or result.get('recommended_cmax')
        if rec:
            lines.append('--- Recommended Parameters ---')
            for k, v in (rec.items() if isinstance(rec, dict) else []):
                lines.append('  {}: {}'.format(k, _fmt(v)))
    else:
        lines.append('(No result YAML provided)')

    return _text_page(lines, title='SA Validation Report — Summary')


def _gate_summary_page(result, phase):
    """Final page: decision gate summary."""
    lines = []
    lines.append('Gate Decision Summary')
    lines.append('=' * 60)
    lines.append('')

    if not result:
        lines.append('(No result YAML available)')
        return _text_page(lines, title='Gate Decision Summary')

    status = result.get('status', 'unknown')
    lines.append('Status:              {}'.format(status))
    lines.append('Phase:               {}'.format(phase or 'n/a'))
    lines.append('')

    # Target fit
    lines.append('Target fit pass:     {}'.format(
        result.get('target_fit_pass', 'n/a')))
    lines.append('Selected eq pass:    {}'.format(
        result.get('selected_eq_pass', 'n/a')))
    lines.append('Selected N pass:     {}'.format(
        result.get('selected_n_pass', 'n/a')))
    lines.append('Selected N ratio:    {}'.format(
        _fmt(result.get('selected_n_ratio'))))
    lines.append('')

    # Kdc ordering
    kdc_valid = result.get('kdc_ordering_valid')
    if kdc_valid is not None:
        lines.append('Kdc ordering valid:  {}'.format(kdc_valid))
        violations = result.get('kdc_ordering_violations') or []
        if violations:
            for v in violations:
                lines.append('  violation: {}'.format(v))
        lines.append('')

    # Failing eq vars
    eq_fail = result.get('failing_eq_vars') or []
    if eq_fail:
        lines.append('Failing eq vars:     {}'.format(', '.join(eq_fail[:10])))
        lines.append('')

    # Misfit classification
    misfit = result.get('misfit_classification') or {}
    unreachable = misfit.get('unreachable') or []
    extinct = misfit.get('extinct_pool') or []
    if unreachable:
        lines.append('Unreachable targets: {}'.format(
            ', '.join(str(u) for u in unreachable[:5])))
    if extinct:
        lines.append('Extinct pools:       {}'.format(
            ', '.join(str(e) for e in extinct[:5])))
    lines.append('')

    # Next action
    action_map = {
        'pass': 'PROCEED — run param_update.py',
        'veg_pass': 'PROCEED — run param_update.py --phase veg',
        'soil_pass': 'PROCEED — run param_update.py --phase soil',
        'best_effort': 'PROCEED with recovery runs A-D',
        'target_fit_review': 'RE-RUN — run propose_bounds.py, adjust SA bounds',
        'unreachable_review': 'HALT — human review required',
        'failed': 'FIX — check missing data or SA configuration',
    }
    lines.append('Agent next action:   {}'.format(
        action_map.get(status, 'Unknown status: {}'.format(status))))

    return _text_page(lines, title='Gate Decision Summary')


def _fmt(val, precision=4):
    """Format a numeric value or return 'n/a'."""
    if val is None:
        return 'n/a'
    try:
        return '{:.{}f}'.format(float(val), precision)
    except (ValueError, TypeError):
        return str(val)


def _find_eq_csvs(work_dir):
    """Find equilibrium quality CSV files in work_dir."""
    eq_files = {}
    for f in os.listdir(work_dir):
        if f.startswith('eq_') and f.endswith('_quality.csv'):
            var = f.replace('eq_', '').replace('_quality.csv', '')
            eq_files[var] = os.path.join(work_dir, f)
    return eq_files


def generate(work_dir, result_yaml=None, phase=None, biome='tundra',
             output=None):
    """Generate the multi-page SA validation PDF.

    Parameters
    ----------
    work_dir : str
        Path to SA work directory containing CSVs.
    result_yaml : str, optional
        Path to step1-result.yaml or step2-result.yaml.
    phase : str, optional
        Calibration phase name.
    biome : str, optional
        Biome for nitrogen check ('tundra' or 'boreal').
    output : str, optional
        Output PDF path. Defaults to work_dir/sa-validation-report.pdf.

    Returns
    -------
    str
        Path to the generated PDF.
    """
    work_dir = os.path.abspath(work_dir)
    if not work_dir.endswith(os.sep):
        work_dir += os.sep

    if output is None:
        output = os.path.join(work_dir, 'sa-validation-report.pdf')

    # Load result YAML if provided
    result = None
    if result_yaml and os.path.isfile(result_yaml):
        with open(result_yaml, 'r') as f:
            result = yaml.safe_load(f)

    # Load SA data
    required_files = ['sample_matrix.csv', 'targets.csv', 'results.csv']
    for rf in required_files:
        if not os.path.isfile(os.path.join(work_dir, rf)):
            raise RuntimeError('Missing required file: {}'.format(
                os.path.join(work_dir, rf)))

    sample_matrix = pd.read_csv(os.path.join(work_dir, 'sample_matrix.csv'))
    targets = pd.read_csv(os.path.join(work_dir, 'targets.csv'), skiprows=1)
    results = pd.read_csv(os.path.join(work_dir, 'results.csv'))

    if len(results) == 0:
        raise RuntimeError('No samples in results.csv')

    eq_csvs = _find_eq_csvs(work_dir)

    with PdfPages(output) as pdf:
        # Page 1: Summary
        fig = _summary_page(result, work_dir, phase, biome)
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

        # Page 2: Spaghetti plot
        fig = sa.plot_spaghetti(results, targets)
        if fig is not None:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

        # Page 3: Box plot
        fig = sa.plot_boxplot(results, targets)
        if fig is not None:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

        # Page 4: 1:1 Match plot
        fig = sa.plot_match(results, targets)
        if fig is not None:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

        # Page 5+: PFT matrix (one figure per target variable)
        figs = sa.plot_pft_matrix(results, sample_matrix, targets)
        if figs is not None:
            if not isinstance(figs, list):
                figs = [figs]
            for fig in figs:
                if fig is not None:
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)

        # Correlation heatmap
        try:
            corr = sa.calc_correlation(results, sample_matrix)
            fig = sa.plot_corr_heatmap(corr)
            if fig is not None:
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
        except Exception:
            pass

        # R2 vs RMSE/MAPE
        fig = sa.plot_r2_rmse(results, targets)
        if fig is not None:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

        # Equilibrium diagnostics
        for var, eq_path in sorted(eq_csvs.items()):
            try:
                eq_params = pd.read_csv(eq_path)
                targets_eq = targets.filter(regex=var)
                if targets_eq.empty:
                    continue
                counts, eq_check, eq_data, eq_fig = sa.equilibrium_check(
                    eq_params, targets)
                if eq_fig is not None:
                    pdf.savefig(eq_fig, bbox_inches='tight')
                    plt.close(eq_fig)

                eq_scatter_figs = sa.plot_equilibrium_metrics_scatter(
                    eq_params, targets)
                if eq_scatter_figs is not None:
                    if not isinstance(eq_scatter_figs, list):
                        eq_scatter_figs = [eq_scatter_figs]
                    for sf in eq_scatter_figs:
                        if sf is not None:
                            pdf.savefig(sf, bbox_inches='tight')
                            plt.close(sf)
            except Exception:
                plt.close('all')

        # Nitrogen check (Step 2 with calib_mode VEGC)
        try:
            figs_before = set(plt.get_fignums())
            n_result = sa.nitrogen_check(
                path=work_dir, biome=biome, save=False)
            if n_result is not None:
                figs_after = set(plt.get_fignums())
                new_figs = sorted(figs_after - figs_before)
                for fnum in new_figs:
                    fig = plt.figure(fnum)
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)
        except Exception:
            plt.close('all')

        # Final page: Gate decision summary
        fig = _gate_summary_page(result, phase)
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    print('SA validation report written: {}'.format(output))
    return output


def get_parser():
    parser = argparse.ArgumentParser(
        description='Generate SA validation report PDF')
    parser.add_argument(
        '--work-dir', required=True,
        help='Path to SA work directory with CSVs')
    parser.add_argument(
        '--result-yaml', default=None,
        help='Path to step1-result.yaml or step2-result.yaml')
    parser.add_argument(
        '--phase', default=None,
        help='Calibration phase (veg_exploration, soil, etc.)')
    parser.add_argument(
        '--biome', default='tundra', choices=['boreal', 'tundra'],
        help='Biome for nitrogen check')
    parser.add_argument(
        '--output', default=None,
        help='Output PDF path (default: work_dir/sa-validation-report.pdf)')
    return parser


def main():
    args = get_parser().parse_args()
    generate(
        work_dir=args.work_dir,
        result_yaml=args.result_yaml,
        phase=args.phase,
        biome=args.biome,
        output=args.output,
    )


if __name__ == '__main__':
    main()
