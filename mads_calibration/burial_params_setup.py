#!/usr/bin/env python3
"""Append s2dfraction/d2mfraction rows to a workflow CMT block (20-row calpar schema)."""

from __future__ import print_function

import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from util.param import (  # noqa: E402
    find_cmt_start_idx,
    get_CMT_datablock,
)


def add_burial_rows(fpath, cmtnum, s2df, d2mf):
    block = get_CMT_datablock(fpath, cmtnum)
    if any('s2dfraction' in line for line in block):
        print('s2dfraction already in CMT{:02d} block'.format(cmtnum))
        return False

    with open(fpath, 'r') as f:
        lines = f.readlines()

    start = find_cmt_start_idx(lines, 'CMT{:02d}'.format(cmtnum))
    # Insert after kdcsomcr line (last soil calpar before optional burial rows).
    insert_at = None
    for i in range(start, len(lines)):
        if 'kdcsomcr' in lines[i]:
            insert_at = i + 1
            break
    if insert_at is None:
        raise RuntimeError('kdcsomcr line not found for CMT{:02d}'.format(cmtnum))
    new_lines = [
        '{:<12}// s2dfraction:\n'.format(s2df),
        '{:<12}// d2mfraction:\n'.format(d2mf),
    ]
    lines[insert_at:insert_at] = new_lines
    with open(fpath, 'w') as f:
        f.writelines(lines)
    print('Inserted burial rows at line {} in {}'.format(insert_at + 1, fpath))
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--param-dir', required=True)
    parser.add_argument('--cmtnum', type=int, default=4)
    parser.add_argument('--s2df', type=float, default=0.5)
    parser.add_argument('--d2mf', type=float, default=0.5)
    args = parser.parse_args()

    fpath = os.path.join(args.param_dir, 'cmt_calparbgc.txt')
    add_burial_rows(fpath, args.cmtnum, args.s2df, args.d2mf)


if __name__ == '__main__':
    main()
