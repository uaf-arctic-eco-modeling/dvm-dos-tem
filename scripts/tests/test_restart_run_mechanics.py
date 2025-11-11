#
# Make sure to run this first: 
#   export PYTHONPATH="/work/scripts/:/work/scripts/util:$PYTHONPATH"
#

# Test the mechanics of using the "restart from" functionality that now
# exists in the config file. User uses combination of the setting in the 
# config file and the command line flag.


import os
import json
import pytest
import pathlib
import subprocess

import netCDF4 as nc

import util.setup_working_directory as swd
import util.runmask


@pytest.fixture(scope="session")
def restart_run_directory(tmp_path_factory):
    '''
    Returns
    -------

    A path to a temporary directory which contains the setup for doing restart
    runs. 
    '''

    # Use the package default demo data
    DEMO_DATA = '/work/demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/'

    # Make a place to hold the run
    restart_run_dir = tmp_path_factory.mktemp("test-restart-mechanics")

    # Shouldn't need this - if the tmp_path_factory is working correctly
    # if(os.path.isdir(restart_run_dir)):
    #     shutil.rmtree(restart_run_dir)

    # Scaffold the run
    CMD = f"--force --input-data-path {DEMO_DATA} {restart_run_dir}"
    swd.cmdline_run(swd.cmdline_parse(CMD.split(" ")))

    # Adjust run mask
    util.runmask.cmdline_run(util.runmask.cmdline_parse(f'--reset --yx 1 1 {restart_run_dir}/run-mask.nc'.split(' ')))

    return restart_run_dir

@pytest.fixture(scope="session")
def restart_pr_eq_base_run(restart_run_directory):

  base_run_output_dir = pathlib.Path(restart_run_directory, 'output_pr_eq')

  CONFIG_FILE = f"{restart_run_directory}/config/config.js"
  with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)
  config["general"]["output_global_attributes"]["run_name"] = "Running PR, EQ base run."
  config["general"]["output_global_attributes"]["description"] = "junk run for testing restart"
  config["IO"]["output_dir"] = str(base_run_output_dir)
  with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)

  os.chdir(restart_run_directory)
  completed_process = subprocess.run(f"dvmdostem -f {CONFIG_FILE} -p5 -e5 -s0 -t0 -n0 -l monitor".split(' '))
  if completed_process.returncode != 0:
      raise RuntimeError("Model run failed")  

  return base_run_output_dir

@pytest.fixture(scope="session")
def restart_sp_from_eq(restart_run_directory, restart_pr_eq_base_run):

  sp_from_eq_output_dir = pathlib.Path(restart_run_directory, 'output_sp_from_eq')

  CONFIG_FILE = f"{restart_run_directory}/config/config.js"
  with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)
  config["general"]["output_global_attributes"]["run_name"] = "Running SP, restarting from EQ."
  config["general"]["output_global_attributes"]["description"] = "junk run for testing restart"
  
  config["IO"]["restart_from"] = str(pathlib.Path(restart_pr_eq_base_run, 'restart-eq.nc'))
  config["IO"]["output_dir"] = str(sp_from_eq_output_dir)
  
  with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)

  os.chdir(restart_run_directory)
  completed_process = subprocess.run(f"dvmdostem -f {CONFIG_FILE} -p0 -e0 -s5 -t0 -n0 -l monitor".split(' '))
  if completed_process.returncode != 0:
      raise RuntimeError("Model run failed")  

  return sp_from_eq_output_dir

@pytest.fixture(scope="session")
def restart_tr_from_sp(restart_run_directory, restart_sp_from_eq):

  tr_from_sp_output_dir = pathlib.Path(restart_run_directory, 'output_tr_from_sp')

  CONFIG_FILE = f"{restart_run_directory}/config/config.js"
  with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)
  config["general"]["output_global_attributes"]["run_name"] = "Running TR, restarting from SP."
  config["general"]["output_global_attributes"]["description"] = "junk run for testing restart"

  config["IO"]["restart_from"] = str(pathlib.Path(restart_sp_from_eq, 'restart-sp.nc'))
  config["IO"]["output_dir"] = str(tr_from_sp_output_dir)

  with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)

  os.chdir(restart_run_directory)
  completed_process = subprocess.run(f"dvmdostem -f {CONFIG_FILE} -p0 -e0 -s0 -t5 -n0 -l debug".split(' '))
  if completed_process.returncode != 0:
      raise RuntimeError("Model run failed")

  return tr_from_sp_output_dir

@pytest.fixture(scope="session")
def restart_sc_from_tr(restart_run_directory, restart_tr_from_sp):

  sc_from_tr_output_dir = pathlib.Path(restart_run_directory, 'output_sc_from_tr')

  CONFIG_FILE = f"{restart_run_directory}/config/config.js"
  with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)
  config["general"]["output_global_attributes"]["run_name"] = "Running SC, restarting from TR."
  config["general"]["output_global_attributes"]["description"] = "junk run for testing restart"

  config["IO"]["restart_from"] = str(pathlib.Path(restart_tr_from_sp, 'restart-tr.nc'))
  config["IO"]["output_dir"] = str(sc_from_tr_output_dir)

  with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)

  os.chdir(restart_run_directory)
  completed_process = subprocess.run(f"dvmdostem -f {CONFIG_FILE} -p0 -e0 -s0 -t0 -n5 -l debug".split(' '))
  if completed_process.returncode != 0:
      raise RuntimeError("Model run failed")

  return sc_from_tr_output_dir

@pytest.fixture(autouse=True)
def bad_restart_from_path(restart_run_directory):

  # arrange
  CONFIG_FILE = f"{restart_run_directory}/config/config.js"
  with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
      config = json.load(f)
      config_backup = config

  config["IO"]["restart_from"] = "/bad/path/to/restart.nc"
  config["IO"]["output_dir"] = str(pathlib.Path(restart_run_directory, 'output_bad_restart'))

  with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
      json.dump(config, f, indent=2)

  os.chdir(restart_run_directory)
  completed_process = subprocess.run(f"dvmdostem -f {CONFIG_FILE} -p0 -e0 -s5 -t0 -n0 -l debug".split(' '))

  if completed_process.returncode == 0:
     raise RuntimeError("Model run succeeded but it should have failed due to bad restart path")

  yield 

  # Put the config back the way it was so that other tests using this directory
  # don't fail...
  with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
      json.dump(config_backup, f, indent=2)


def test_try_restart_pr_eq(restart_run_directory, restart_pr_eq_base_run):
  '''
  Make sure that user can't specify restart run for pr or eq stage. This should
  fail because there should be no way to do a valid restart for the pr or eq
  stage. In order to test it, we use the restart_pr_eq_base_run fixture to get a
  valid restart file from the pr/eq run, and then try to use that to restart a
  pr run. This should fail. If you run the test with -s you will see a
  successful run first, followed by the failed run.
  '''

  CONFIG_FILE = f"{restart_run_directory}/config/config.js"
  with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
      config = json.load(f)

  config["IO"]["restart_from"] = str(pathlib.Path(restart_pr_eq_base_run, 'restart-eq.nc'))
  config["IO"]["output_dir"] = str(pathlib.Path(restart_run_directory, 'output_bad_pr_restart'))

  with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
      json.dump(config, f, indent=2)
  
  os.chdir(restart_run_directory)
  completed_process = subprocess.run(f"dvmdostem -f {CONFIG_FILE} -p5 -e5 -s0 -t0 -n0 -l debug".split(' '))
  assert completed_process.returncode != 0

  completed_process = subprocess.run(f"dvmdostem -f {CONFIG_FILE} -p0 -e5 -s0 -t0 -n0 -l debug".split(' '))
  assert completed_process.returncode != 0



def test_restart_pr_eq_base_run(restart_run_directory, restart_pr_eq_base_run):
    assert pathlib.Path(restart_run_directory, 'output_pr_eq', 'restart-eq.nc').exists()
    assert nc.Dataset(f'{restart_run_directory}/output_pr_eq/run_status.nc').variables['run_status'][1,1] == 100

def test_restart_sp_from_eq(restart_run_directory, restart_sp_from_eq):
    assert pathlib.Path(restart_run_directory, 'output_sp_from_eq', 'restart-sp.nc').exists()
    assert nc.Dataset(f'{restart_run_directory}/output_sp_from_eq/run_status.nc').variables['run_status'][1,1] == 100

def test_restart_tr_from_sp(restart_run_directory, restart_tr_from_sp):
    assert pathlib.Path(restart_run_directory, 'output_tr_from_sp', 'restart-tr.nc').exists()
    assert nc.Dataset(f'{restart_run_directory}/output_tr_from_sp/run_status.nc').variables['run_status'][1,1] == 100

def test_restart_sc_from_tr(restart_sc_from_tr):
    assert pathlib.Path(restart_sc_from_tr, 'restart-sc.nc').exists()
    assert nc.Dataset(f'{restart_sc_from_tr}/run_status.nc').variables['run_status'][1,1] == 100

def test_bad_restart_from_path(restart_run_directory, bad_restart_from_path):
  '''This is funky - most of the test is being done in the fixture...basically
  with a bad restart path, the model should fail to run before nearly anything
  happens. So thats what happens in the fixture and we just yield it to here.
  There isn't much to check here...'''

  CONFIG_FILE = f"{restart_run_directory}/config/config.js"
  with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
      config = json.load(f)

  bad_restart_from_path = config["IO"]["restart_from"]
  assert pathlib.Path(bad_restart_from_path).exists() == False

  

# Further tests:
#   --restart-run restart_from="" --> exception
#   restart_from <path> , no cmd line flag --> success
#
#   restart_from <bad path> --> exception
#
#
