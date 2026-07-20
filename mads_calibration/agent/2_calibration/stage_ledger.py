"""
Step 2 stage ledger — tracks applied phase passes and enforces stage order.

Written beside parameters-step2 as step2-stage-ledger.yaml (workflow root).
Initialized by seed_setup.py; updated by param_update.py; checked by analyze.py.
"""

from __future__ import print_function

import datetime
import os

import yaml

# Canonical order: nlevel -> krb -> cfall -> nfall -> soil (+ optional phase6/7).
PHASE_PASS_STATUS = {
    'nlevel': 'nlevel_pass',
    'krb': 'krb_pass',
    'cfall': 'cfall_pass',
    'nfall': 'nfall_pass',
    'soil': 'soil_pass',
    'phase6': 'phase6_pass',
    'phase7': 'phase7_pass',
    'main': 'pass',
}

PHASE_PREREQUISITES = {
    'nlevel': (),
    'krb': ('nlevel',),
    'cfall': ('krb',),
    'nfall': ('cfall',),
    'soil': ('nfall',),
    'phase6': ('nfall',),   # rhmoist branch during soil; veg chain must be applied
    'phase7': ('phase6',),
    'main': ('soil',),  # post-hoc on old integrated work_dirs only
}

LEDGER_FILENAME = 'step2-stage-ledger.yaml'


def ledger_path_for_param_dir(param_dir):
    """Default ledger path: sibling of parameters-step2 in workflow root."""
    param_dir = os.path.abspath(param_dir)
    return os.path.join(os.path.dirname(param_dir), LEDGER_FILENAME)


def infer_param_dir_from_work_dir(work_dir):
    """
    Infer parameters-step2 when work_dir is under .../logs/sa-step2-*/.

    Returns None if layout does not match.
    """
    work_dir = os.path.abspath(work_dir)
    parts = work_dir.split(os.sep)
    if 'logs' not in parts:
        return None
    idx = parts.index('logs')
    workflow_root = os.sep.join(parts[:idx])
    candidate = os.path.join(workflow_root, 'parameters-step2')
    if os.path.isdir(candidate):
        return candidate
    return None


def load_ledger(path):
    if not os.path.isfile(path):
        return None
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}


def save_ledger(path, data):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def init_ledger(param_dir, seed_manifest=None, step1_result=None):
    """Create an empty stage ledger after seed_setup."""
    param_dir = os.path.abspath(param_dir)
    path = ledger_path_for_param_dir(param_dir)
    data = {
        'param_dir': param_dir,
        'created': datetime.datetime.utcnow().isoformat() + 'Z',
        'seed_manifest': os.path.abspath(seed_manifest) if seed_manifest else None,
        'step1_result': os.path.abspath(step1_result) if step1_result else None,
        'stages': {},
    }
    save_ledger(path, data)
    return path, data


def stage_is_applied(ledger, stage):
    """True when stage was applied with the expected *_pass status."""
    if not ledger:
        return False
    rec = (ledger.get('stages') or {}).get(stage)
    if not rec:
        return False
    return rec.get('status') == PHASE_PASS_STATUS[stage]


def missing_prerequisites(ledger, phase):
    """Return list of prerequisite stage keys not yet applied."""
    missing = []
    for prereq in PHASE_PREREQUISITES.get(phase, ()):
        if not stage_is_applied(ledger, prereq):
            missing.append(prereq)
    return missing


def require_prerequisites(ledger, phase, param_dir=None, force=False):
    """
    Refuse analyze/SA when prior stages were not applied.

    nlevel requires a ledger file (from seed_setup); later phases require
    each prerequisite stage to show the matching *_pass status.
    """
    if force:
        return
    path = ledger_path_for_param_dir(param_dir) if param_dir else None
    if ledger is None:
        if phase == 'nlevel':
            raise RuntimeError(
                'Stage ledger missing at {!r}. Run seed_setup.py first '
                '(creates step2-stage-ledger.yaml beside parameters-step2).'.format(
                    path))
        raise RuntimeError(
            'Stage ledger missing at {!r}. Cannot start --phase {} without '
            'documented prior applies.'.format(path, phase))

    missing = missing_prerequisites(ledger, phase)
    if not missing:
        return

    stages = ledger.get('stages') or {}
    detail = []
    for stage in missing:
        rec = stages.get(stage)
        if rec is None:
            detail.append('{} (not applied)'.format(stage))
        else:
            detail.append(
                '{} (status={!r}, need {!r})'.format(
                    stage, rec.get('status'), PHASE_PASS_STATUS[stage]))
    raise RuntimeError(
        'Refusing --phase {}: prerequisites not applied: {}. '
        'Complete prior stages (param_update after analyze exit 0) or use '
        '--skip-preflight only with documented human approval.'.format(
            phase, '; '.join(detail)))


def record_stage_apply(ledger, phase, step2_result_path, status,
                       work_dir=None, run_id=None):
    """Update ledger after a successful param_update apply."""
    if ledger is None:
        ledger = {'stages': {}}
    if 'stages' not in ledger:
        ledger['stages'] = {}
    ledger['stages'][phase] = {
        'status': status,
        'applied_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'step2_result': os.path.abspath(step2_result_path),
        'work_dir': os.path.abspath(work_dir) if work_dir else None,
        'run_id': run_id,
    }
    ledger['last_applied'] = phase
    return ledger
