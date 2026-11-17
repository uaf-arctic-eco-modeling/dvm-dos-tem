#!/usr/bin/env python

import sys
import os
import argparse
import textwrap
import json
import re
from pathlib import Path

import commentjson


# Map config.js IO keys to standard default input filenames. Configured
# paths may use other filenames; these defaults are used when preparing
# a new run.
DEFAULT_INPUT_FILE_NAMES = {
  'hist_climate_file': 'historic-climate.nc',
  'proj_climate_file': 'projected-climate.nc',
  'veg_class_file': 'vegetation.nc',
  'drainage_file': 'drainage.nc',
  'soil_texture_file': 'soil-texture.nc',
  'co2_file': 'co2.nc',
  'proj_co2_file': 'projected-co2.nc',
  'runmask_file': 'run-mask.nc',
  'topo_file': 'topo.nc',
  'fri_fire_file': 'fri-fire.nc',
  'hist_exp_fire_file': 'historic-explicit-fire.nc',
  'proj_exp_fire_file': 'projected-explicit-fire.nc',
}


def load_config(config_file="config/config.js"):
  '''
  Read a model configuration file, allowing JSON comments.

  Parameters
  ----------
  config_file : str or pathlib.Path, optional
    Path to the configuration file. Relative paths are interpreted from the
    current working directory.

  Returns
  -------
  config : dict
    Parsed configuration contents.

  Raises
  ------
  OSError
    If the file cannot be opened or read.
  ValueError
    If the contents cannot be parsed as configuration data.
  '''
  with open(config_file, encoding='utf-8') as config_fh:
    return commentjson.load(config_fh)


def load_config_from_dir(run_dir):
  '''
  Read a run directory's configuration, if present.

  Parameters
  ----------
  run_dir : str or pathlib.Path
    Run directory containing ``config/config.js``.

  Returns
  -------
  config : dict or None
    Parsed configuration, or None if the configuration file is missing.
    Read and parse errors propagate to the caller.
  '''
  config_path = Path(run_dir) / 'config' / 'config.js'
  if not config_path.is_file():
    return None
  return load_config(config_path)


def get_input_paths(config_file="config/config.js", verbose=True):
  '''
  '''
  config = load_config(config_file)

  #Should this also handle parameter_dir and output_spec file location?
  #At least for now, no. The matching 'set_input_paths' method should likely
  # only apply to this set of files.
  if verbose:
    print("Fetching input paths for filenames:", *DEFAULT_INPUT_FILE_NAMES, sep=', ')

  paths = []
  for filename in DEFAULT_INPUT_FILE_NAMES:
#    path = os.path.dirname(config['IO'][filename])
    path = config['IO'][filename]
    if path not in paths:
      paths.append(path)

  return paths


def _parse_config_value(raw_value):
  '''
  Parse a value passed via CLI for writing into config data.
  '''
  try:
    return commentjson.loads(raw_value)
  except ValueError:
    # If it is not valid JSON-like syntax, keep it as a string.
    return raw_value


def set_config_value(config_file, key_path, value, verbose=True):
  '''
  Set a nested configuration value using dot-separated key paths,
  preserving comments, formatting, and key order in the original file.

  Works by validating the key path via commentjson, then performing a
  targeted regex replacement in the raw file text so that comments and
  formatting are never disturbed. Supports scalar values (strings,
  numbers, booleans, null) only — not inline objects or arrays.

  Example key paths:
    IO.output_dir
    stage_settings.eq.env
  '''
  
  with open(config_file, encoding='utf-8') as config_fh:
    raw_text = config_fh.read()

  # Validate key path and confirm the key exists.
  config = commentjson.loads(raw_text)

  keys = key_path.split('.')
  if not keys or any(not k for k in keys):
    raise ValueError("Invalid key path: '{}'".format(key_path))

  node = config
  for key in keys[:-1]:
    if key not in node:
      raise KeyError("Missing key in path '{}': '{}'".format(key_path, key))
    if not isinstance(node[key], dict):
      raise TypeError(
          "Cannot descend into non-object key '{}' for path '{}'".format(key, key_path)
      )
    node = node[key]

  if keys[-1] not in node:
    raise KeyError("Target key does not exist: '{}'".format(key_path))

  # Serialize the new value as compact JSON (handles str/int/float/bool/None).
  new_value_json = json.dumps(value)

  # Build a pattern that matches:  "last_key"  :  <scalar_value>
  # Scalar value covers JSON strings, numbers, booleans, and null.
  last_key = keys[-1]
  _json_string  = r'"(?:[^"\\]|\\.)*"'
  _json_number  = r'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?'
  _json_keyword = r'true|false|null'
  _scalar       = r'(?:{0}|{1}|{2})'.format(_json_string, _json_number, _json_keyword)
  pattern = r'("' + re.escape(last_key) + r'"\s*:\s*)(' + _scalar + r')'

  new_text, count = re.subn(pattern, r'\g<1>' + new_value_json, raw_text)

  if count == 0:
    raise ValueError(
        "Could not locate key '{}' in raw text of '{}'".format(last_key, config_file)
    )
  if count > 1:
    raise ValueError(
        "Ambiguous replacement: key '{}' matched {} times in '{}'. "
        "Use a more specific key path.".format(last_key, count, config_file)
    )

  with open(config_file, 'w', encoding='utf-8') as config_fh:
    config_fh.write(new_text)

  if verbose:
    print("Updated '{}' in {}".format(key_path, config_file))


def list_config_keys(config_file, root_key_path=None):
  '''
  Return available key paths in dot notation.
  If root_key_path is provided, list only that key and its subkeys.
  '''
  config = load_config(config_file)

  start_node = config
  start_prefix = ''
  if root_key_path:
    keys = root_key_path.split('.')
    if not keys or any(not k for k in keys):
      raise ValueError("Invalid key path: '{}'".format(root_key_path))
    for key in keys:
      if not isinstance(start_node, dict) or key not in start_node:
        raise KeyError("Target key does not exist: '{}'".format(root_key_path))
      start_node = start_node[key]
    start_prefix = root_key_path

  key_paths = []

  def _walk(node, prefix=''):
    if not isinstance(node, dict):
      return
    for key, value in node.items():
      path = key if not prefix else '{}.{}'.format(prefix, key)
      key_paths.append(path)
      _walk(value, path)

  if root_key_path:
    key_paths.append(start_prefix)
    _walk(start_node, start_prefix)
  else:
    _walk(config)

  return key_paths


def cmdline_define():
  '''Define the command line interface and return the parser object.'''

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      Helper script for a dvm-dos-tem config file.
    ''')
  )
  parser.add_argument('file', nargs='?', metavar=('FILE'),
      help=textwrap.dedent('''The config file to operate on.'''))

  parser.add_argument('--verbose', action='store_true',
      help=textwrap.dedent('''Print info to stdout when script runs.'''))

  parser.add_argument('--get-input-paths', action='store_true',
      help=textwrap.dedent('''Returns all input file paths'''))

  parser.add_argument('--set', nargs=2, action='append', metavar=('KEY_PATH', 'VALUE'),
      help=textwrap.dedent('''Set a config key path to a value. Use dot notation
      for nested keys (e.g. IO.output_dir output/new). VALUE is parsed as JSON if
      possible, otherwise stored as a string.'''))

  parser.add_argument('--list-keys', nargs='?', const='',
      metavar='KEY_PATH',
      help=textwrap.dedent('''List available config keys using dot notation. Use
                           an empty string to list all keys (e.g. --list-keys ""
                           <PATH_TO_CONFIG_FILE>). For nested keys, use dot
                           notation, e.g. --list-keys IO to list all keys under
                           the IO section.'''))

  return parser

def cmdline_parse(argv=None):
  '''
  The command line interface specification and parser for util config.py.

  If parse_args(...) is called with argv=None, then parse_args(...) will
  use sys.argv[1:]. Otherwise argv is parsed according to the specification.

  Parameters
  ----------
  argv : None or list of strings
    arguments that argparse library will parse; if None, then sys.argv[1:] are
    parsed.

  Returns
  -------
  args : Namespace generated by argparse

  '''
  parser = cmdline_define()

  args = parser.parse_args(argv)

  # print(argv)
  # print(args)

  # Force vebosity on if user requests showing data
  #if args.show:
    #args.verbose = True # ?? Not sure about this...
  
  if (args.file is None) or (not os.path.isfile(args.file)):
    parser.error("'{}' is an invalid path to a config file!".format(args.file))

  return args


def cmdline_run(args):
  '''
  Executes based on the command line arguments.

  Parameters
  ----------
  args : Namespace
    Should be a Namespace with all the appropriate arguments.

  Returns
  -------
  exit_code : int 
    Non-zero if the program cannot complete successfully.

  '''
  if args.get_input_paths:
    paths = get_input_paths(args.file, args.verbose)
    for i in paths:
      print(i)

  if args.set:
    for key_path, raw_value in args.set:
      value = _parse_config_value(raw_value)
      set_config_value(args.file, key_path, value, verbose=args.verbose)

  if args.list_keys is not None:
    root_key_path = args.list_keys if args.list_keys else None
    for key_path in list_config_keys(args.file, root_key_path):
      print(key_path)

  return 0


def cmdline_entry(argv=None):
  '''
  Wrapper allowing for easier testing of the cmdline run and parse functions.
  '''
  args = cmdline_parse(argv)
  return cmdline_run(args)

# adding this allows the script to be run standalone when installed with pip...
def main(argv=None):
  return cmdline_entry(argv=argv)

if __name__ == '__main__':
  sys.exit(cmdline_entry()) # this makes sure appropriate exit code is passed on.

