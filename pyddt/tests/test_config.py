#!/usr/bin/env python
'''
Pytest based tests for ``pyddt.util.config``.

Run (from the ``pyddt/`` directory, with the pyddt package importable,
e.g. after `pip install -e .` or with `src` on PYTHONPATH):

    pytest tests/test_config.py -v

Two different "sources" of config data are used here, deliberately:

  * Read-only checks (listing keys, reading input paths) exercise the real
    ``config/config.js`` that ships with the repo, since that is the file
    users will actually run this tool against and we want to know if it
    ever stops being readable/listable.

  * Tests that *modify* a config file (or that need a config file with a
    specific defect) use a small fixture defined inline in this module and
    written to ``tmp_path``. This keeps the tracked ``config/config.js``
    file from ever being mutated by a test run, and keeps the fixture
    content right next to the tests that depend on its exact shape.
'''

import os
import textwrap

import commentjson
import lark
import pytest

import pyddt.util.config as config


# Repo-shipped config file, used only for non-mutating checks.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SHIPPED_CONFIG = os.path.join(REPO_ROOT, 'config', 'config.js')


SAMPLE_CONFIG = textwrap.dedent('''\
    {
      // top level comment
      "IO": {
        "output_dir": "output/",     // inline comment
        "output_interval": 1
      },
      "model_settings": {
        "cell_timelimit": 0,
        "dynamic_lai": 1
      }
    }
    ''')

# Missing comma between the two "IO" members - a realistic typo.
MALFORMED_CONFIG = textwrap.dedent('''\
    {
      "IO": {
        "output_dir": "output/"
        "output_interval": 1
      }
    }
    ''')


@pytest.fixture
def sample_config_file(tmp_path):
  cfg = tmp_path / "sample_config.js"
  cfg.write_text(SAMPLE_CONFIG)
  return str(cfg)


@pytest.fixture
def malformed_config_file(tmp_path):
  cfg = tmp_path / "malformed_config.js"
  cfg.write_text(MALFORMED_CONFIG)
  return str(cfg)


# ---------------------------------------------------------------------------
# Reading the shipped config.js
# ---------------------------------------------------------------------------

def test_get_input_paths_reads_shipped_config():
  paths = config.get_input_paths(SHIPPED_CONFIG, verbose=False)
  assert len(paths) > 0
  assert all(isinstance(p, str) for p in paths)


def test_list_config_keys_shipped_config_all():
  keys = config.list_config_keys(SHIPPED_CONFIG)
  assert 'IO' in keys
  assert 'IO.output_dir' in keys
  assert 'stage_settings.eq.env' in keys


def test_list_config_keys_shipped_config_subset():
  keys = config.list_config_keys(SHIPPED_CONFIG, root_key_path='IO')
  assert keys[0] == 'IO'
  assert 'IO.output_dir' in keys
  assert not any(k.startswith('model_settings') for k in keys)


def test_list_config_keys_invalid_root_key_raises():
  with pytest.raises(KeyError):
    config.list_config_keys(SHIPPED_CONFIG, root_key_path='does.not.exist')


# ---------------------------------------------------------------------------
# Listing keys on a small, self-contained config
# ---------------------------------------------------------------------------

def test_list_config_keys_sample(sample_config_file):
  keys = config.list_config_keys(sample_config_file)
  assert keys == [
      'IO', 'IO.output_dir', 'IO.output_interval',
      'model_settings', 'model_settings.cell_timelimit',
      'model_settings.dynamic_lai',
  ]


# ---------------------------------------------------------------------------
# Modifying a value while preserving comments/formatting
# ---------------------------------------------------------------------------

def test_set_config_value_preserves_comments(sample_config_file):
  config.set_config_value(sample_config_file, 'IO.output_dir', 'new_output/', verbose=False)

  with open(sample_config_file) as f:
    new_raw = f.read()

  assert '"output_dir": "new_output/"' in new_raw
  assert '// top level comment' in new_raw
  assert '// inline comment' in new_raw
  assert '"output_interval": 1' in new_raw  # untouched sibling value

  reloaded = commentjson.loads(new_raw)
  assert reloaded['IO']['output_dir'] == 'new_output/'
  assert reloaded['IO']['output_interval'] == 1


def test_set_config_value_numeric_and_bool(sample_config_file):
  config.set_config_value(sample_config_file, 'model_settings.cell_timelimit', 42, verbose=False)
  config.set_config_value(sample_config_file, 'model_settings.dynamic_lai', False, verbose=False)

  with open(sample_config_file) as f:
    reloaded = commentjson.loads(f.read())
  assert reloaded['model_settings']['cell_timelimit'] == 42
  assert reloaded['model_settings']['dynamic_lai'] is False


# ---------------------------------------------------------------------------
# set_config_value error handling
# ---------------------------------------------------------------------------

def test_set_config_value_missing_key_raises(sample_config_file):
  with pytest.raises(KeyError):
    config.set_config_value(sample_config_file, 'IO.does_not_exist', 'x', verbose=False)


def test_set_config_value_missing_parent_raises(sample_config_file):
  with pytest.raises(KeyError):
    config.set_config_value(sample_config_file, 'does.not.exist', 'x', verbose=False)


def test_set_config_value_non_object_parent_raises(sample_config_file):
  with pytest.raises(TypeError):
    config.set_config_value(sample_config_file, 'IO.output_dir.nested', 'x', verbose=False)


def test_set_config_value_invalid_key_path_raises(sample_config_file):
  with pytest.raises(ValueError):
    config.set_config_value(sample_config_file, '', 'x', verbose=False)
  with pytest.raises(ValueError):
    config.set_config_value(sample_config_file, 'IO..output_dir', 'x', verbose=False)


def test_set_config_value_ambiguous_key_raises(tmp_path):
  '''
  Known limitation: the target key is located purely by its *last* path
  segment via regex, not by the full dot path, so a repeated key name
  anywhere else in the file is rejected as ambiguous -- even though the
  dot-path lookup used for validation is unambiguous. The shipped
  config.js hits this for "env", which repeats across each
  stage_settings sub-section (pr/eq/sp/tr/sc).
  '''
  copy = tmp_path / "config.js"
  with open(SHIPPED_CONFIG) as f:
    copy.write_text(f.read())

  with pytest.raises(ValueError, match='Ambiguous replacement'):
    config.set_config_value(str(copy), 'stage_settings.eq.env', False, verbose=False)


def test_set_config_value_file_not_found():
  with pytest.raises(FileNotFoundError):
    config.set_config_value('/path/does/not/exist/config.js', 'IO.output_dir', 'x', verbose=False)


# ---------------------------------------------------------------------------
# Malformed config file surfaces a reasonable error
# ---------------------------------------------------------------------------

def test_get_input_paths_malformed_config_raises(malformed_config_file):
  # get_input_paths uses commentjson.load(), which wraps any underlying
  # parser error in a commentjson.JSONLibraryException.
  with pytest.raises(commentjson.JSONLibraryException):
    config.get_input_paths(malformed_config_file, verbose=False)


def test_list_config_keys_malformed_config_raises(malformed_config_file):
  with pytest.raises(commentjson.JSONLibraryException):
    config.list_config_keys(malformed_config_file)


def test_set_config_value_malformed_config_raises(malformed_config_file):
  # set_config_value uses commentjson.loads() directly (not load()), so the
  # raw parser exception propagates instead of being wrapped in
  # commentjson.JSONLibraryException.
  with pytest.raises((ValueError, lark.exceptions.LarkError)):
    config.set_config_value(malformed_config_file, 'IO.output_dir', 'x', verbose=False)


def test_get_input_paths_missing_file_raises():
  with pytest.raises(FileNotFoundError):
    config.get_input_paths('/path/does/not/exist/config.js', verbose=False)
