#!/usr/bin/env python
"""
Phase 0 calibration setup: sync GCS inputs/parameters, build site config.js,
verify site/input/parameter mapping, and write a setup manifest for Step 1.

Typical usage inside dvmdostem-autocal:

  python mads_calibration/agent/agent_calibration_setup/calibration_setup.py --discover

  python mads_calibration/agent/agent_calibration_setup/calibration_setup.py \\
    --site-name Imnavait --cmtnum 4 --site-label IMN \\
    --json-out mads_calibration/logs/IMN-setup-manifest.yaml
"""

from __future__ import print_function

import argparse
import os
import re
import shutil
import subprocess
import sys

import commentjson
import netCDF4 as nc
import numpy as np
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MADS_CALIB_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT = os.path.dirname(MADS_CALIB_DIR)
SCRIPTS_DIR = os.path.join(REPO_ROOT, 'scripts')
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import util.setup_working_directory  # noqa: E402
import util.runmask  # noqa: E402

DEFAULT_INPUT_BUCKET = 'gs://dvmdostem_calibration_input'
DEFAULT_PARAM_BUCKET = 'gs://vb-tem/Calibration/calibration_files/calibrated'
DEFAULT_INPUT_CATALOG = os.environ.get('DDT_INPUT_CATALOG', '/data/input-catalog')
DEFAULT_WORKFLOWS = os.environ.get('DDT_WORKFLOWS', '/data/workflows')
REPO_PARAMETERS = os.path.join(REPO_ROOT, 'parameters')
ALIASES_FILE = os.path.join(SCRIPT_DIR, 'site_aliases.yaml')

# Eq-only calibration sites may lack projected driver or optional fire files.
EQ_CALIBRATION_CORE = {
    'co2.nc', 'drainage.nc', 'run-mask.nc', 'soil-texture.nc',
    'topo.nc', 'vegetation.nc', 'historic-climate.nc',
}
EQ_CALIBRATION_OPTIONAL = {
    'fri-fire.nc', 'historic-explicit-fire.nc',
    'projected-climate.nc', 'projected-explicit-fire.nc',
}
EQ_CALIBRATION_REQUIRED = EQ_CALIBRATION_CORE | EQ_CALIBRATION_OPTIONAL

FULL_INPUT_REQUIRED = EQ_CALIBRATION_REQUIRED


def storage_tool():
    if shutil.which('gsutil'):
        return 'gsutil'
    if shutil.which('gcloud'):
        return 'gcloud'
    raise RuntimeError(
        'Neither gsutil nor gcloud found on PATH. '
        'Install Google Cloud SDK or run from a host with gcloud auth.')


def gsutil_ls(prefix, directories_only=False):
    tool = storage_tool()
    if tool == 'gsutil':
        cmd = ['gsutil', 'ls']
        if directories_only:
            cmd.append(prefix if prefix.endswith('/') else prefix + '/')
        else:
            cmd.append(prefix)
    else:
        cmd = ['gcloud', 'storage', 'ls']
        if directories_only:
            cmd.append(prefix if prefix.endswith('/') else prefix + '/')
        else:
            cmd.append(prefix)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            'storage ls failed for {}: {}'.format(prefix, proc.stderr.strip()))
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    return lines


def gsutil_rsync(src, dst, dry_run=False):
    tool = storage_tool()
    if tool == 'gsutil':
        cmd = ['gsutil', '-m', 'rsync', '-r']
        if dry_run:
            cmd.append('-n')
        cmd.extend([src, dst])
    else:
        cmd = ['gcloud', 'storage', 'rsync', '-r']
        if dry_run:
            cmd.append('--dry-run')
        cmd.extend([src, dst])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            'storage rsync failed {} -> {}: {}'.format(
                src, dst, proc.stderr.strip() or proc.stdout.strip()))
    return proc.stdout


def list_input_sites(input_bucket):
    entries = gsutil_ls(input_bucket, directories_only=True)
    sites = []
    for entry in entries:
        name = entry.rstrip('/').split('/')[-1]
        if name.endswith('.nc'):
            continue
        sites.append(name)
    return sorted(sites)


def list_param_folders(param_bucket):
    entries = gsutil_ls(param_bucket, directories_only=True)
    folders = []
    for entry in entries:
        name = entry.rstrip('/').split('/')[-1]
        folders.append(name)
    return sorted(folders)


def parse_cmt_from_folder_name(folder_name):
    match = re.search(r'CMT(\d+)', folder_name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r'parameters(\d+)', folder_name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def parse_cmt_from_calpar(path):
    if not os.path.isfile(path):
        return None
    with open(path, 'r') as f:
        for line in f:
            if not line.strip().startswith('//'):
                continue
            match = re.search(r'CMT(\d+)', line, re.IGNORECASE)
            if match:
                return int(match.group(1))
    return None


def load_aliases():
    if not os.path.isfile(ALIASES_FILE):
        return {}
    with open(ALIASES_FILE, 'r') as f:
        data = yaml.safe_load(f) or {}
    return {str(k): list(v) for k, v in data.items()}


def heuristic_param_matches(site_name, param_folders):
    site_lower = site_name.lower().replace('_', '')
    matches = []
    for folder in param_folders:
        folder_lower = folder.lower().replace('_', '')
        if site_lower in folder_lower or folder_lower[:3] in site_lower:
            matches.append(folder)
    return matches


def resolve_param_folder(site_name, cmtnum, param_folders, aliases):
    candidates = list(aliases.get(site_name, []))
    candidates.extend(heuristic_param_matches(site_name, param_folders))
    seen = set()
    ordered = []
    for folder in candidates:
        if folder in param_folders and folder not in seen:
            ordered.append(folder)
            seen.add(folder)

    cmt_matches = [f for f in ordered if parse_cmt_from_folder_name(f) == cmtnum]
    if cmtnum is None:
        return (ordered[0] if ordered else None), ordered

    cmt_matches = [f for f in ordered if parse_cmt_from_folder_name(f) == cmtnum]
    if cmt_matches:
        return cmt_matches[0], ordered

    return None, ordered


def check_input_files(input_dir, full=False):
    required = FULL_INPUT_REQUIRED if full else EQ_CALIBRATION_REQUIRED
    if not os.path.isdir(input_dir):
        raise RuntimeError('Input directory does not exist: {}'.format(input_dir))
    files = {
        f for f in os.listdir(input_dir)
        if os.path.isfile(os.path.join(input_dir, f))
    }
    missing = required.difference(files)
    missing_core = EQ_CALIBRATION_CORE.difference(files)
    missing_optional = EQ_CALIBRATION_OPTIONAL.difference(files)
    extra = files.difference(required)
    return {
        'missing': sorted(missing),
        'missing_core': sorted(missing_core),
        'missing_optional': sorted(missing_optional),
        'extra': sorted(extra),
        'ok': len(missing_core) == 0,
    }


def find_active_pixel(runmask_path):
    with nc.Dataset(runmask_path, 'r') as ds:
        if 'mask' not in ds.variables:
            return 0, 0
        mask = np.array(ds.variables['mask'][:, :])
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return 0, 0
    return int(xs[0]), int(ys[0])


def verify_calibration_targets(cmtnum):
    cal_dir = os.path.join(REPO_ROOT, 'calibration')
    if cal_dir not in sys.path:
        sys.path.insert(0, cal_dir)
    try:
        import calibration_targets as ct  # noqa: WPS433
    except ImportError as exc:
        return False, 'Cannot import calibration_targets: {}'.format(exc)

    found = [
        k for k, v in ct.calibration_targets.items()
        if isinstance(v, dict) and v.get('cmtnumber') == cmtnum
    ]
    if not found:
        return False, 'CMT {} not in calibration_targets.py'.format(cmtnum)
    entry = found[0]
    if 'GPPAllIgnoringNitrogen' not in ct.calibration_targets[entry]:
        return False, 'CMT {} missing GPPAllIgnoringNitrogen target'.format(cmtnum)
    return True, entry


def verify_veg_cmt(veg_path, pxx, pxy, cmtnum):
    with nc.Dataset(veg_path, 'r') as ds:
        veg = int(ds.variables['veg_class'][pxy, pxx])
    if veg != cmtnum:
        return False, 'vegetation.nc at ({}, {}) is CMT{}, expected CMT{}'.format(
            pxx, pxy, veg, cmtnum)
    return True, veg


def verify_config_js(config_path, expected_input_dir):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = commentjson.load(f)
    io = config.get('IO', {})
    hist = io.get('hist_climate_file', '')
    expected = os.path.abspath(expected_input_dir)
    if not hist.startswith(expected):
        return False, 'hist_climate_file does not point under {}: {}'.format(
            expected, hist)
    return True, hist


def build_crosswalk(input_sites, param_folders, aliases):
    rows = []
    for site in input_sites:
        _, candidates = resolve_param_folder(
            site, cmtnum=None, param_folders=param_folders, aliases=aliases)
        rows.append({
            'site_name': site,
            'param_candidates': candidates,
            'alias_listed': aliases.get(site, []),
        })
    return rows


def print_discover_table(rows):
    print('Site input folder          Param folder candidates')
    print('-' * 70)
    for row in rows:
        cands = ', '.join(row['param_candidates']) if row['param_candidates'] else '(none)'
        print('{:<26} {}'.format(row['site_name'], cands))


def discover(input_bucket, param_bucket):
    input_sites = list_input_sites(input_bucket)
    param_folders = list_param_folders(param_bucket)
    aliases = load_aliases()
    rows = build_crosswalk(input_sites, param_folders, aliases)
    print('Input bucket:  {}'.format(input_bucket))
    print('Param bucket:  {}'.format(param_bucket))
    print('Input sites:   {}'.format(len(input_sites)))
    print('Param folders: {}'.format(len(param_folders)))
    print()
    print_discover_table(rows)
    return rows


def setup_site(args):
    warnings = []
    workflow_dir = args.dest_workflow or os.path.join(
        DEFAULT_WORKFLOWS,
        'CMT{:02d}-{}'.format(args.cmtnum, args.site_label),
    )
    dest_input = args.dest_input or os.path.join(
        DEFAULT_INPUT_CATALOG, args.site_name)
    seed_dir = os.path.join(workflow_dir, 'parameters-seed')
    setup_dir = os.path.join(workflow_dir, 'setup')
    config_js = os.path.join(setup_dir, 'config', 'config.js')

    input_bucket_uri = '{}/{}'.format(
        args.input_bucket.rstrip('/'), args.site_name)
    aliases = load_aliases()
    if args.skip_sync:
        param_folders = sorted({
            folder for folders in aliases.values() for folder in folders
        })
    else:
        param_folders = list_param_folders(args.param_bucket)
    param_folder, all_candidates = resolve_param_folder(
        args.site_name, args.cmtnum, param_folders, aliases)

    param_bucket_uri = None
    param_cmt_in_file = None
    use_repo_seed = False

    if param_folder:
        param_bucket_uri = '{}/{}'.format(
            args.param_bucket.rstrip('/'), param_folder)
        folder_cmt = parse_cmt_from_folder_name(param_folder)
        param_cmt_in_file = folder_cmt
        if folder_cmt is not None and folder_cmt != args.cmtnum:
            warnings.append(
                'Param folder {} is CMT{} but user requested CMT{}; '
                'using /work/parameters as seed_path instead.'.format(
                    param_folder, folder_cmt, args.cmtnum))
            use_repo_seed = True
    else:
        warnings.append(
            'No calibrated parameter folder found for site {}; '
            'using /work/parameters as seed_path.'.format(args.site_name))
        use_repo_seed = True

    if all_candidates and not param_folder:
        warnings.append(
            'Candidates seen but none match CMT{}: {}'.format(
                args.cmtnum, ', '.join(all_candidates)))

    # Phase 2 — sync inputs
    if args.skip_sync:
        if not os.path.isdir(dest_input):
            raise RuntimeError(
                '--skip-sync set but dest input missing: {}'.format(dest_input))
        warnings.append('GCS input sync skipped (--skip-sync)')
    elif not args.dry_run:
        os.makedirs(os.path.dirname(dest_input), exist_ok=True)
        gsutil_rsync(input_bucket_uri, dest_input, dry_run=False)
    else:
        print('[dry-run] would rsync {} -> {}'.format(input_bucket_uri, dest_input))

    # Phase 3 — sync parameters
    if use_repo_seed:
        seed_path = REPO_PARAMETERS
        if not args.skip_sync:
            warnings.append('Using repo parameters at {}'.format(seed_path))
    else:
        seed_path = seed_dir
        if args.skip_sync:
            if not os.path.isdir(seed_dir):
                warnings.append(
                    'parameters-seed missing under {}; falling back to {}'.format(
                        seed_dir, REPO_PARAMETERS))
                seed_path = REPO_PARAMETERS
                use_repo_seed = True
            else:
                warnings.append('GCS parameter sync skipped (--skip-sync)')
        elif not args.dry_run:
            if args.force and os.path.isdir(seed_dir):
                import shutil
                shutil.rmtree(seed_dir)
            os.makedirs(os.path.dirname(seed_dir), exist_ok=True)
            gsutil_rsync(param_bucket_uri, seed_dir, dry_run=False)
            param_cmt_in_file = parse_cmt_from_calpar(
                os.path.join(seed_dir, 'cmt_calparbgc.txt'))
            if param_cmt_in_file is not None and param_cmt_in_file != args.cmtnum:
                warnings.append(
                    'cmt_calparbgc.txt in bucket is CMT{} but user cmtnum is CMT{}'.format(
                        param_cmt_in_file, args.cmtnum))
        else:
            print('[dry-run] would rsync {} -> {}'.format(param_bucket_uri, seed_dir))

    # Phase 4 — build site config
    if not args.dry_run:
        if args.force and os.path.isdir(setup_dir):
            import shutil
            shutil.rmtree(setup_dir)
        util.setup_working_directory.cmdline_entry([
            '--input-data-path', dest_input,
            '--seed-parameters', seed_path,
            '--no-cal-targets',
            setup_dir,
        ])
    else:
        print('[dry-run] would setup_working_directory {} '
              '--input-data-path {} --seed-parameters {}'.format(
                  setup_dir, dest_input, seed_path))

    pxx = args.pxx
    pxy = args.pxy
    runmask_path = os.path.join(dest_input, 'run-mask.nc')
    if pxx is None or pxy is None:
        if os.path.isfile(runmask_path):
            pxx, pxy = find_active_pixel(runmask_path)
        else:
            pxx, pxy = 0, 0
            if not args.dry_run:
                warnings.append('run-mask.nc missing; defaulting PXx=0, PXy=0')

    if not args.dry_run and os.path.isfile(runmask_path):
        util.runmask.cmdline_entry([
            '--reset', '--yx', str(pxy), str(pxx),
            os.path.join(setup_dir, 'run-mask.nc'),
        ])

    # Phase 5 — verify
    status = 'pass'
    if not args.dry_run:
        input_check = check_input_files(dest_input)
        if not input_check['ok']:
            status = 'failed'
            warnings.append(
                'Missing required core input files: {}'.format(
                    ', '.join(input_check['missing_core'])))
        elif input_check['missing_optional']:
            warnings.append(
                'Missing optional driver files: {}'.format(
                    ', '.join(input_check['missing_optional'])))

        ok, msg = verify_calibration_targets(args.cmtnum)
        if not ok:
            status = 'failed'
            warnings.append(msg)

        veg_path = os.path.join(dest_input, 'vegetation.nc')
        if os.path.isfile(veg_path):
            ok, msg = verify_veg_cmt(veg_path, pxx, pxy, args.cmtnum)
            if not ok:
                warnings.append(msg)

        if os.path.isfile(config_js):
            ok, msg = verify_config_js(config_js, dest_input)
            if not ok:
                status = 'failed'
                warnings.append(msg)
    else:
        warnings.append('dry-run: verification skipped')

    if warnings and status == 'pass':
        status = 'warn'

    manifest = {
        'site_name': args.site_name,
        'site_label': args.site_label,
        'cmtnum': args.cmtnum,
        'site': dest_input,
        'PXx': pxx,
        'PXy': pxy,
        'seed_path': seed_path,
        'setup_dir': setup_dir,
        'config_js': config_js,
        'input_bucket': input_bucket_uri,
        'param_bucket': param_bucket_uri,
        'param_folder': param_folder if not use_repo_seed else None,
        'param_cmt_in_file': param_cmt_in_file,
        'workflow_dir': workflow_dir,
        'status': status,
        'warnings': warnings,
    }
    return manifest


def write_manifest(manifest, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w') as f:
        yaml.safe_dump(manifest, f, default_flow_style=False, sort_keys=False)


def get_parser():
    parser = argparse.ArgumentParser(
        description='Phase 0 calibration setup from GCS buckets.',
    )
    parser.add_argument(
        '--discover', action='store_true',
        help='List input sites and parameter folder crosswalk; then exit.',
    )
    parser.add_argument('--site-name', help='GCS input folder name, e.g. Imnavait')
    parser.add_argument('--cmtnum', type=int, help='Calibration CMT number')
    parser.add_argument('--site-label', help='Short site token, e.g. IMN')
    parser.add_argument('--pxx', type=int, default=None)
    parser.add_argument('--pxy', type=int, default=None)
    parser.add_argument(
        '--input-bucket', default=DEFAULT_INPUT_BUCKET,
        help='GCS bucket for driving inputs (default: %(default)s)',
    )
    parser.add_argument(
        '--param-bucket', default=DEFAULT_PARAM_BUCKET,
        help='GCS prefix for calibrated parameters (default: %(default)s)',
    )
    parser.add_argument(
        '--dest-input', default=None,
        help='Local input path (default: $DDT_INPUT_CATALOG/{site_name})',
    )
    parser.add_argument(
        '--dest-workflow', default=None,
        help='Workflow base dir (default: /data/workflows/CMT{NN}-{label})',
    )
    parser.add_argument(
        '--skip-sync', action='store_true',
        help='Skip GCS rsync; use existing local input and seed paths.',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Print actions without syncing or writing files.',
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Overwrite existing seed and setup directories.',
    )
    parser.add_argument(
        '--json-out', default=None,
        help='Write setup manifest yaml to this path.',
    )
    return parser


def main():
    args = get_parser().parse_args()

    if args.discover:
        discover(args.input_bucket, args.param_bucket)
        sys.exit(0)

    missing = []
    if not args.site_name:
        missing.append('--site-name')
    if args.cmtnum is None:
        missing.append('--cmtnum')
    if not args.site_label:
        missing.append('--site-label')
    if missing:
        print('error: required for setup: {}'.format(', '.join(missing)),
              file=sys.stderr)
        sys.exit(1)

    manifest = setup_site(args)

    print('site_name:         {}'.format(manifest['site_name']))
    print('site_label:      {}'.format(manifest['site_label']))
    print('cmtnum:            {}'.format(manifest['cmtnum']))
    print('site:              {}'.format(manifest['site']))
    print('PXx, PXy:          {}, {}'.format(manifest['PXx'], manifest['PXy']))
    print('seed_path:         {}'.format(manifest['seed_path']))
    print('setup_dir:         {}'.format(manifest['setup_dir']))
    print('config_js:         {}'.format(manifest['config_js']))
    print('input_bucket:      {}'.format(manifest['input_bucket']))
    print('param_bucket:      {}'.format(manifest['param_bucket']))
    print('param_folder:      {}'.format(manifest['param_folder']))
    print('param_cmt_in_file: {}'.format(manifest['param_cmt_in_file']))
    print('status:            {}'.format(manifest['status']))
    if manifest['warnings']:
        print('warnings:')
        for w in manifest['warnings']:
            print('  - {}'.format(w))

    if args.json_out:
        write_manifest(manifest, args.json_out)
        print('\nWrote {}'.format(args.json_out))

    if manifest['status'] == 'failed':
        sys.exit(1)
    if manifest['status'] == 'warn':
        sys.exit(2)
    sys.exit(0)


if __name__ == '__main__':
    main()
