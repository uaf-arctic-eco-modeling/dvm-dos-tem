#!/usr/bin/env python
# coding: utf-8

import netCDF4 as nc
import numpy as np
from matplotlib import pyplot as plt
import os
import json
import pandas as pd
import seaborn as sns
import xarray as xr


from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"


os.environ['HDF5_USE_FILE_LOCKING']='FALSE'


get_ipython().system('ls /data/input-catalog/cpcrw_towers_downscaled/')


get_ipython().run_line_magic('cd', '/work')
get_ipython().system('rm -r /data/workflows/BONA-black-spruce-fire-1930/')

get_ipython().system("scripts/util/setup_working_directory.py  --input-data-path /data/input-catalog/cpcrw_towers_downscaled/  /data/workflows/BONA-black-spruce-fire-1930/ --fire_hist_file='historic-explicit-fire_1930.nc'")

get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --empty')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on CMTNUM yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on GPP monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on RG monthly compartment')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on RH monthly layer')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on RM monthly compartment')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on NPP monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on ALD yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on SHLWC yearly monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on DEEPC yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on MINEC yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on ORGN yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on AVLN yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on LTRFALC monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on LWCLAYER monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on TLAYER monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on LAYERDEPTH monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on LAYERDZ monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on EET monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on TRANSPIRATION monthly PFT')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on LAI monthly PFT')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on VEGC monthly PFT compartment')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce-fire-1930/config/output_spec.csv --on BURNVEG2AIRC monthly')

get_ipython().run_line_magic('cd', '/data/workflows/BONA-black-spruce-fire-1930')

get_ipython().system("dvmdostem --force-cmt=15 --log-level='err' --eq-yrs=1000 --sp-yrs=300 --tr-yrs=122 --sc-yrs=0")

get_ipython().system('ls /data/workflows/BONA-black-spruce-fire-1930/output/')




