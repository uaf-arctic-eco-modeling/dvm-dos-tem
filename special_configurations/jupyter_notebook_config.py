# Special config so that jupyter notebooks are automatically
# saves in .py format for easy diffing and merging on github...

# This file will be copied into the docker image so that
# when a user is running a notebook server, this feature is
# enabled...

import os
import subprocess

def post_save(model, os_path, contents_manager):
    '''post-save hook for converting notebooks to .py scripts'''
    if model['type'] != 'notebook':
        return # only do this for notebooks
    d, fname = os.path.split(os_path)
    cp = subprocess.run(['jupyter', 'nbconvert', '--no-prompt', '--to', 'script', fname], capture_output=True, check=True, cwd=d)

c.FileContentsManager.post_save_hook = post_save
