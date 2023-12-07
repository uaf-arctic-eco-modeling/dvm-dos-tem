#!/usr/bin/env python

# import os
# import yaml

# import drivers.Sensitivity

# # THis is how you can setup and work with a driver for runs that are already
# # done...i.e. there should be output data in the ssrfs...
# #
# # Note that if you try to use this with a config file that has more stuff
# # enabled than the run was originally done with it should fail...

# WORK_PATH = '/data/workflows/CMT06_IMNAVIAT_GPPAINcmax_TBC'
# WORK_PATH = '/Users/tobeycarman/Documents/SEL/dvmdostem-workflows/CMT06_IMNAVIAT_GPPAINcmax_TBC'

# driver = drivers.Sensitivity.SensitivityDriver()

# driver.set_work_dir(WORK_PATH)

# driver.load_experiment(os.path.join(WORK_PATH, 'SA', 'param_props.csv'),
#                        os.path.join(WORK_PATH, 'SA', 'sample_matrix.csv'),
#                        os.path.join(WORK_PATH, 'SA', 'info.txt'), )

# # Should these be part of the save/load functionality?
# driver.set_seed_path('/work/parameters/')
# driver.load_target_data('/work/calibration/')

# with open('CMT06_IMNAVIAT_GPPAINcmax_TBC.yaml', 'r') as config_data:
#     config = yaml.safe_load(config_data)

# driver.setup_outputs(config['target_names'])


import numpy as np
import pandas as pd
import sklearn.metrics as sklm
import scipy.stats
import matplotlib.pyplot as plt


# This stuff is diamond box in SA (orange half)
def plot_boxplot(results, targets):
  '''
  Plots a box and whiskers for each column in ``results``. Plots a dot for
  each target value.

  Useful for seeing if the range of model outputs produced by running each row
  in the sample matrix contains the target values.

  .. image:: /images/SA_post_hoc_analysis/results_boxplot.png
     :width: 80%

  Parameters
  ----------
  results : pandas.DataFrame
    One column for each model ouput variable, one row for each run (sample)

  targets : pandas.DataFrame
    One column for each target (truth, or observation) value. One row.
  '''
  plt.close('all')
  fig, ax = plt.subplots(nrows=1, ncols=1,figsize=(6,6))
  results.boxplot(ax=ax, rot=45)
  ax.scatter(range(1,len(targets.columns)+1), targets, color='red', zorder=1000)
  plt.savefig("plots/results_boxplot.png")

def plot_spaghetti(results, targets):
  '''
  Plots one line for each sample (row) in ``results``. Plots targets as dots.
  X axis of plot are for different columns in ``results``. Makes 2 plots, the 
  right one uses a log scale for the y axis.

  Useful for seeing if the range of model outputs produced by running each row
  in the sample matrix contains the target values.

  .. image:: /images/SA_post_hoc_analysis/spaghetti_plot.png

  Parameters
  ----------
  results : pandas.DataFrame
    One row for each run (sample), one column for each model output variable.
  
  targets : pandas.DataFrame
    Single row, one column for each target (truth, or observation) value.
  '''
  plt.close('all')
  fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2,figsize=(24,6))

  for i, sample in results.iterrows():
    ax1.plot(sample, color='gray', alpha=0.1)

  # ax1.plot(results.mean(), color='blue')
  # ax1.fill_between(range(len(results.T)),
  #                 results.mean() - results.std(), 
  #                 results.mean() + results.std(),
  #                 color='gray', alpha=.5, linewidth=0)
  # ax1.fill_between(range(len(results.T)),
  #                 results.min(), 
  #                 results.max(),
  #                 color='gray', alpha=.25, linewidth=0)

  ax2.plot(results.mean(), color='blue')
  for i, sample in results.iterrows():
    ax2.plot(sample, color='gray', alpha=0.1)

  # Targets
  for ax in [ax1, ax2]:
    ax.scatter(range(len(targets.T)), targets, 
               marker='o', color='red', zorder=1000)

  ax2.set_yscale('log')

  plt.savefig("plots/spaghetti_plot.png")

def plot_match(results, targets):
  '''
  Plot targets vs model outputs (results). Dashed diagonal is line of perfect 
  agreement between the model output and the targets. Plot dot or marker for
  each model output. Targets are on the y axis, model outputs on the x axis.

  The result a horizontal collection of markers for each column in results.
  If the collection of markers crosses the dashed 1:1 line, then the model
  is capable of producing target values somewhere in the sample set. If the
  collection of markers for a given column (model output) is all to the left
  of the 1:1 line, then the modeled values are all too low. If the collection of
  markers is all to the right of the 1:1 line then the modeled values are too
  high.

  .. image:: /images/SA_post_hoc_analysis/one2one_match.png
  
  '''
  # "One to one match plot"
  plt.close('all')
  fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(12,12))

  x = np.linspace(targets.min(axis=1), targets.max(axis=1), 10)
  ax.plot(x,x, 'b--')
  ax.scatter(results, [targets for i in range(len(results))], alpha=.1)

  plt.savefig("plots/one2one_match.png")




# ut.get_param_r2_rmse()

# This stuff is all about revising (tightening parameter ranges) leads into blue box
def calc_metrics(results, targets):
  '''Calculate a bunch of sklearn regression metrics.'''
  r2 = [sklm.r2_score(targets.T, sample) for i,sample in results.iterrows()]
  mse = [sklm.mean_squared_error(targets.T, sample) for i,sample in results.iterrows()]
  mape = [sklm.mean_absolute_percentage_error(targets.T, sample) for i, sample in results.iterrows()]

  return r2, mse, mape

def calc_correlation(model_results, sample_matrix):
  '''
  sample_matrix: pandas DataFrame with one row per sample, one column per parameter
  model_results: pandas DataFrame with one row per sample, one column per output
  '''
  corr_mp = pd.DataFrame(columns=sample_matrix.columns, index=model_results.columns)

  for model_col in model_results.columns:
    for param_col in sample_matrix.columns:
        corr = model_results[model_col].corr(sample_matrix[param_col])
        corr_mp.loc[model_col, param_col] = corr

  corr_mp = corr_mp.astype(float)

  return corr_mp

def plot_corr_heatmap(df_corr):
  '''
  ??? Write something...

  .. image:: /images/SA_post_hoc_analysis/correlation_heatmap.png

  '''
  import seaborn

  plt.figure(figsize=(15,10))
  seaborn.heatmap(df_corr, cmap="YlGnBu", annot=True, fmt=".2f")
  plt.title("Correlation Matrix [Results vs Parameters]", fontsize=16)
  plt.ylabel("Model Results", fontsize=14)
  plt.xlabel("Parameters", fontsize=14)
  plt.savefig("plots/correlation_heatmap.png")




def plot_r2_mse(results, targets):
  '''
  Plot ???

  .. image:: /images/SA_post_hoc_analysis/r2_mse_mape.png

  '''

  r2, mse, mape = calc_metrics(results, targets)

  plt.close('all')
  fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12,12))

  axes[0].plot(r2,mse, 'o', alpha=.5)
  axes[0].set_xlabel('r2')
  axes[0].set_ylabel('mse')
  #axes[0].set_yscale('log')

  axes[1].plot(r2, mape, 'o', alpha=0.25)
  axes[1].set_xlabel('r2')
  axes[1].set_ylabel('mape')

  plt.legend()

  plt.savefig("plots/r2_mse_mape.png")

def calc_combined_score(results, targets):
  '''Calculate a combination score using r^2, and normalized mse and mape.'''

  r2, mse, mape = calc_metrics(results, targets)

  # normalize mse and mape to be between 0 and 1
  norm_mse = (mse - np.nanmin(mse)) / (np.nanmax(mse) - np.nanmin(mse))
  norm_mape = (mape - np.nanmin(mape)) / (np.nanmax(mape) - np.nanmin(mape))

  # combined accuracy by substracting average of mse and mape from r2
  combined_score = r2 - np.mean([norm_mse, norm_mape])

  return combined_score

def prep_mads_initial_guess(params):
  '''
  Generate MADS initial guess string based on parameter ranges. The idea is that
  the intial guess should be the mean of the parameter range. Gives you
  a string like this:

    .. code:: 

      mads_initialguess:
        - 16.252  # cmax_pft0
        - 79.738  # cmax_pft1
        - 44.687  # cmax_pft2

  that is intended to be copied into your ``.yaml`` config file.

  Parameters
  ----------
  params : pandas.DataFrame
    A DataFrame containing parameter values.

  Returns
  -------
  str
    MADS initial guess string.
  '''
  # First get the min and max for each column
  ranges = [(params[x].min(), params[x].max(), x) for x in params]

  s2 = 'mads_initialguess:\n'
  for MIN, MAX, comment in ranges:
    s2 += f"  - {scipy.stats.uniform(loc=MIN, scale=MAX-MIN).mean():8.3f}  # {comment}\n"

  return s2



def prep_mads_distributions(params):
  '''
  Gives you something like this:

  .. code::

    mads_paramdist:
      - Uniform(  5.9117,  26.5927)    # cmax_pft0
      - Uniform( 46.0129, 113.4639)    # cmax_pft1
      - Uniform( 11.7916,  77.5827)    # cmax_pft2

  From B. Maglio's notebook.

  Parameters
  ----------
  params : pandas.DataFrame
    One row for each of the selected runs, one column for each parameter.
    Column names are

  Returns
  -------
  dists : string
    A nicely formatted string with the distributions for each parameter that can be
    pasted into the .yaml file for the next step.
  '''

  # First get the min and max for each column
  ranges = [(params[x].min(), params[x].max(), x) for x in params]

  # Then make a nice string out of it...
  s = 'mads_paramdist:\n'
  for MIN, MAX, comment in ranges:
    s += f"  - Uniform({MIN:8.3f}, {MAX:8.3f})    # {comment}\n"


  return s


def n_top_runs(results, targets, params, N):
  '''
  Get the best runs measured using the combined scores.

  Parameters
  ----------
  results : pandas.DataFrame
    One row per sample (run), one column per output variable
  targets : pandas.DataFrame
    Single row, one column per target values (generally there is one output
    variable for each target)
  params : pandas.DataFrame
    One row per sample (run), one column per parameter. In other places in the
    process this is referred to as the "sample matrix".

  Returns
  -------
  top_runs : tuple of numpy.ndarrays
    First item is the 2D array of the top results (output variables), second
    item is the array of parameters used to generate the outputs.

  '''
  combined_score = calc_combined_score(results, targets)

  best_indices = np.argsort(combined_score)

  sorted_results = results.iloc[best_indices]
  sorted_params = params.iloc[best_indices]

  return sorted_results[:N], sorted_params[:N]

def get_parser():
  pass

def cmdline_parse():
  pass

def cmdline_run():
  pass

def cmdline_entry():
  pass

if __name__ == '__main__':

  # Load data
  param_props = pd.read_csv('SA/param_props.csv')
  sample_matrix = pd.read_csv("SA/sample_matrix.csv")
  targets = pd.read_csv('SA/targets.csv', skiprows=1)
  results = pd.read_csv('SA/results.csv')


  # # Trying to print out the bounds so we can get updated improved bounds after
  # # SA and getting n_top_runs...
  # lower, upper = row.strip().lstrip('[').rstrip(']').split(',')

  # #driver.collect_all_outputs()
  # from IPython import embed; embed()
    
