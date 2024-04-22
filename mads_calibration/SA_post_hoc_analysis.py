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

import os
import numpy as np
import pandas as pd
import netCDF4 as nc
import sklearn.metrics as sklm
import scipy.stats
import matplotlib.pyplot as plt
# import Line2D to manually create legend handles
from matplotlib.lines import Line2D

# This stuff is diamond box in SA (orange half)
def plot_boxplot(results, targets, check_filter=None, save=False, saveprefix=''):
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

  check_filter : pandas.Series
    Series with boolean values for additional tests following
    SA run, e.g. equilibrium_check, eq_check['result']

  save : bool
    Assumes False so plot will not be saved. If set to true it will plot
    in current directory unless saveprefix is specified

  saveprefix : str
    A string that is prepended to the saved filename 'results_boxplot.png'

  Returns
  -------
  None
  '''
  plt.close('all')

  x = np.linspace(1, len(results.columns), len(results.columns))

  if check_filter is not None:
    c = 'grey'
    plt.boxplot(results, positions=x-0.15, widths=0.25,
          boxprops=dict(color=c), capprops=dict(color=c), whiskerprops=dict(color=c), 
          flierprops=dict(color=c, markeredgecolor=c), medianprops=dict(color=c)
          )
    c = 'green'
    plt.boxplot(results[check_filter==True], positions=x+0.15, widths=0.25,
          boxprops=dict(color=c), capprops=dict(color=c), whiskerprops=dict(color=c), 
          flierprops=dict(color=c, markeredgecolor=c), medianprops=dict(color=c)
          )
    plt.xticks(x, results.columns, rotation=90)
  else:
    c = 'grey'
    plt.boxplot(results, positions=x, widths=0.25,
          boxprops=dict(color=c), capprops=dict(color=c), whiskerprops=dict(color=c), 
          flierprops=dict(color=c, markeredgecolor=c), medianprops=dict(color=c)
          )
    plt.xticks(x, results.columns, rotation=90)
  
  plt.scatter(x, targets, color='red', zorder=1000)

  if save:
    plt.savefig(saveprefix + "results_boxplot.png", bbox_inches='tight')

def plot_spaghetti(results, targets, check_filter=None, save=False, saveprefix=''):
  '''
  Plots one line for each sample (row) in ``results``. Plots targets as dots.
  X axis of plot are for different columns in ``results``. Makes 2 plots, the 
  right one uses a log scale for the y axis. The right plot also has a mean line
  (blue).

  Useful for seeing if the range of model outputs produced by running each row
  in the sample matrix contains the target values.

  .. image:: /images/SA_post_hoc_analysis/spaghetti_plot.png

  Parameters
  ----------
  results : pandas.DataFrame
    One row for each run (sample), one column for each model output variable.
  
  targets : pandas.DataFrame
    Single row, one column for each target (truth, or observation) value.

  check_filter : pandas.Series
    Series with boolean values for additional tests following
    SA run, e.g. equilibrium_check, eq_check['result']

  save : bool
    Assumes False so plot will not be saved. If set to true it will plot
    in current directory unless saveprefix is specified

  saveprefix : str
    A string that is prepended to the saved filename 'spaghetti_plot.png'

  Returns
  -------
  None
  '''
  plt.close('all')
  fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2,figsize=(24,6))

  for i, sample in results.iterrows():
    ax1.plot(sample, color='gray', alpha=0.1)
    if check_filter is not None:
      if check_filter.loc[i].all() == True:
        ax1.plot(sample, color='green', alpha=0.1)

  ax1.plot(results.mean(), color='blue')

  for i, sample in results.iterrows():
    ax2.plot(sample, color='gray', alpha=0.1)
    if check_filter is not None:
      if check_filter.loc[i].all() == True:
        ax2.plot(sample, color='green', alpha=0.1)

  ax2.plot(results.mean(), color='blue')

  # Targets
  for ax in [ax1, ax2]:
    ax.scatter(range(len(targets.T)), targets, 
               marker='o', color='red', zorder=1000)

  ax2.set_yscale('log')
  if save:
    plt.savefig(saveprefix + "spaghetti_plot.png", bbox_inches='tight')

def plot_match(results, targets, check_filter=None, save=False, saveprefix=''):
  '''
  Plot targets vs model outputs (results). Dashed diagonal is line of perfect 
  agreement between the model output and the targets. Plot dot or marker for
  each model output. Targets are on the y axis, model outputs on the x axis.

  There is a horizontal collection of markers for each column in results.
  If the collection of markers crosses the dashed 1:1 line, then the model
  is capable of producing target values somewhere in the sample set. If the
  collection of markers for a given column (model output) is all to the left
  of the 1:1 line, then the modeled values are all too low. If the collection of
  markers is all to the right of the 1:1 line then the modeled values are too
  high.

  .. image:: /images/SA_post_hoc_analysis/one2one_match.png
  
  Parameters
  ----------
  results : pandas.DataFrame
    One row for each run (sample), one column for each model output variable.
  
  targets : pandas.DataFrame
    Single row, one column for each target (truth, or observation) value.

  check_filter : pandas.Series
    Series with boolean values for additional tests following
    SA run, e.g. equilibrium_check, eq_check['result']

  save : bool
    Assumes False so plot will not be saved. If set to true it will plot
    in current directory unless saveprefix is specified

  saveprefix : str
    A string that is prepended to the saved filename 'results_boxplot.png'

  Returns
  -------
  None
  '''
  # "One to one match plot"
  fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(12,12))

  x = np.linspace(targets.min(axis=1), targets.max(axis=1), 10)
  ax.plot(x,x, 'b--')
  ax.scatter(results, [targets for i in range(len(results))], alpha=.1)
  if check_filter is not None:
    ax.scatter(results.loc[check_filter==True], [targets for i in range(check_filter.value_counts()[True])], alpha=.1, color='green')
  if save:
    plt.savefig(saveprefix + "one2one_match.png", bbox_inches='tight')

# ut.get_param_r2_rmse()

# This stuff is all about revising (tightening parameter ranges) leads into blue box
def calc_metrics(results, targets):
  '''Calculate a bunch of sklearn regression metrics.'''
  # This is gonna need some help...not seeming to pick the right stuff.\
  # not sure if weights should be passed to metrics function, like this:
  #
  #    weights_by_targets = targets.values[0]/targets.sum(axis=1)[0]
  #    r2 = [sklm.r2_score(targets.T, sample, sample_weight=weights_by_targets) for i,sample in results.iterrows()]

  r2 = [sklm.r2_score(targets.T, sample) for i,sample in results.iterrows()] 
  rmse = [sklm.mean_squared_error(targets.T, sample, squared=False) for i,sample in results.iterrows()]
  mape = [sklm.mean_absolute_percentage_error(targets.T, sample) for i,sample in results.iterrows()]

  return r2, rmse, mape

def calc_correlation(model_results, sample_matrix):
  '''
  Generate a correlation matrix between parameters and model outputs.

  Parameters
  ----------
  sample_matrix: pandas.DataFrame
    with one row per sample, one column per parameter
  model_results: pandas.DataFrame
    with one row per sample, one column per output

  Returns
  -------
  corr_mp: pandas.DataFrame
    One column for each parameter, one row for each model output.
  '''
  # correlation between model outputs and parameters
  corr_mp = pd.DataFrame(columns=sample_matrix.columns, index=model_results.columns)

  for model_col in model_results.columns:
    for param_col in sample_matrix.columns:
        corr = model_results[model_col].corr(sample_matrix[param_col])
        corr_mp.loc[model_col, param_col] = corr

  corr_mp = corr_mp.astype(float)

  return corr_mp

def plot_relationships(results, sample_matrix, targets, check_filter=None, variables=None, 
                       parameters=None, corr_threshold=None, save=False, saveprefix=''):
  '''
  Look at the model outputs and the parameters, calculate the corrleation
  between the two, and then make one plot for each instance where the
  correlation exceeds the threshold.

  Parameters
  ----------
  results: pandas.DataFrame
    One row per sample, one column per output.

  sample_matrix: pandas.DataFrame
    One row per sample, one column per parameter.

  targets: pandas.DataFrame
    One row with one column per target value.

  check_filter : pandas.Series
    Series with boolean values for additional tests following
    SA run, e.g. equilibrium_check, eq_check['result']

  variables: list, optional
    Strings referencing variables of interest in results

  parameter: list, optional
    Strings referencing parameers of interest in sample_matrix

  corr_threshold: float, optional
    Lower threshold for correlation to plot

  save : bool
    Assumes False so plot will not be saved. If set to true it will plot
    in current directory unless saveprefix is specified
    Saves all subplots (can be a lot) if != None

  saveprefix : str
    A string that is prepended to the saved filename '{var}-{parameters}.png'

  Returns
  -------
  None

  .. image:: /images/INGPP_pft0-cmax_pft0-cmax_pft3.png

  '''
  # if variables/parameters are None plot all variables/parameters
  if variables == None:
    variables = list(results.columns.values)
  if parameters == None:
    parameters = list(sample_matrix.columns.values)
    
  # Calculate correlation
  corr = calc_correlation(results, sample_matrix)

  # loop through variables and create set of subplots for each
  for vars in variables:
    # Create a square of subplots from square root of number of parameters per variable
    fig_size = int(np.ceil(np.sqrt(len(parameters))))
    # Create indices for looping through subplot columns
    col_indices = np.linspace(0, fig_size - 1, fig_size).astype(int)
    # Create subplots
    if len(parameters) < 2:
      fig, ax = plt.subplots()
      row_indices = [None]
    elif len(parameters) < 3:
      fig, ax = plt.subplots(1, fig_size)
      # Create indices for looping through subplot rows
      row_indices = [1]
    else:
      fig, ax = plt.subplots(fig_size, fig_size)
      # Create indices for looping through subplot rows
      row_indices = np.linspace(0, fig_size - 1, fig_size).astype(int)
        
    # Counter for results column number during subplot looping
    count = 0

    # Looping through rows and columns in subplot square
    for row in row_indices:  
      for col in col_indices:
        # Catch if only looking at a single row of subplots
        if len(row_indices) <= 1:
          if row==None:
            axis = ax
            plt.setp(ax, ylabel=vars)
          else:
            axis = ax[col]
            plt.setp(ax[0], ylabel=vars)
        else:
          axis = ax[row, col]
          plt.setp(ax[:, 0], ylabel=vars)

        if corr_threshold != None:
          if corr.loc[vars, parameters[count]] < corr_threshold:
            # Setting title (corr) 
            axis.set_title(corr.loc[vars, parameters[count]])
            # Setting xlabel (parameter name) 
            axis.set_xlabel(parameters[count])
            #Do not plot as below correlation threshold
            break
          elif corr.loc[vars, parameters[count]] >= corr_threshold:
            # Plotting scatter of parameter, variable relationship
            axis.scatter(sample_matrix[parameters[count]], results[vars])
            if check_filter is not None:
              axis.scatter(sample_matrix[check_filter==True][parameters[count]], results[check_filter==True][vars], color='green')
            # Plotting target value line
            axis.plot(sample_matrix[parameters[count]], targets[vars].values*np.ones(len(sample_matrix[parameters[count]])), 'k--')
            # Setting xlabel (parameter name) 
            axis.set_xlabel(parameters[count])
            # Setting title (corr) 
            axis.set_title(corr.loc[vars, parameters[count]])
            # Go to next output variable
            count+=1
            # Break loop if we reach maximum number of columns before number of subplots
            if count > (len(parameters) - 1):
              break
        else:
          # Plotting scatter of parameter, variable relationship
          axis.scatter(sample_matrix[parameters[count]], results[vars])
          if check_filter is not None:
            axis.scatter(sample_matrix[check_filter==True][parameters[count]], results[check_filter==True][vars], color='green')
          # Plotting target value line
          axis.plot(sample_matrix[parameters[count]], targets[vars].values*np.ones(len(sample_matrix[parameters[count]])), 'k--')
          # Setting xlabel (parameter name) 
          axis.set_xlabel(parameters[count])
          # Go to next output variable
          count+=1
          # Break loop if we reach maximum number of columns before number of subplots
          if count >= (len(parameters) - 1):
            break
      # Create a single legend with all handles provided outside of subplots
      legend_info = [Line2D([0], [0], color='k', linewidth=3, linestyle='--'),
                     Line2D([0], [0], marker='o', markersize=5, markeredgecolor='C0', markerfacecolor='C0', linestyle='')]
      legend_labels = ["Observations", "Model"]
      plt.legend(legend_info, legend_labels, bbox_to_anchor=(1.05, 1.0), loc="upper left", fontsize=10)
      # Adjust spacing between subplots
      plt.subplots_adjust(left=None, bottom=None, right=1, top=1.2, wspace=None, hspace=None)
      # Save figure if enabled - may create a large number of figures
      plt.tight_layout()
      if save:
        name = saveprefix + f"{vars}-{'-'.join(parameters)}.png"
        plt.savefig(name, bbox_inches="tight")

def plot_pft_matrix(results, sample_matrix, targets, check_filter=None, save=False, saveprefix=''):
  '''
  Look at the model outputs and the parameters, and plot all parameters
  against each variable for 10 potential pfts

  Parameters
  ----------
  results: pandas.DataFrame
    One row per sample, one column per output.

  sample_matrix: pandas.DataFrame
    One row per sample, one column per parameter.

  targets: pandas.DataFrame
    One row with one column per target value.

  check_filter : pandas.Series
    Series with boolean values for additional tests following
    SA run, e.g. equilibrium_check, eq_check['result']

  save : bool
    Assumes False so plot will not be saved. If set to true it will plot
    in current directory unless saveprefix is specified

  saveprefix : str
    A string that is prepended to the saved filename '{var}_pft_plot.pdf'


  Returns
  -------
  None

  .. image:: 

  '''
  variables = list(results.columns.values)
  parameters = list(sample_matrix.columns.values)
  target_values = list(targets.columns.values)

  param_types = []; pft_nums = []
  for p in parameters:
    param_types.append(p.split("_")[0])
    pft_nums.append(p.split("_")[-1])
  param_set = list(set(param_types)); param_set.sort()
  pft_nums_set = list(set(pft_nums)); pft_nums_set.sort()

  for v in range(0,len(variables)):
    
    ncols = 10
    nrows = len(param_set)
    fig, ax = plt.subplots(nrows, ncols, figsize=(24, len(param_set)*2))
    
    for i in range(0, len(param_set)):

      for j in range(0, len(pft_nums_set)):
                 
        if len(param_set) > 1:
          axis = ax[i,j]
        else:
          axis = ax[j]
        
        p = param_set[i]+"_"+pft_nums_set[j]
        if any(p in s for s in parameters):
          axis.scatter(sample_matrix[p], results[variables[v]])
          if check_filter is not None:
            axis.scatter(sample_matrix[check_filter==True][p], results[check_filter==True][variables[v]], color='green')
          axis.plot(sample_matrix[p], targets[variables[v]].values*np.ones(len(sample_matrix[p])), 'k--')
          axis.set_title(p, fontsize=10)
          axis.tick_params(labelsize=10)
            
    plt.tight_layout()
    plt.suptitle(variables[v], fontsize=12, y=1.0)
    # Save figure if enabled - may create a large number of figures
    if save:
      name = saveprefix + f"{variables[v]}_pft_plot.pdf"
      plt.savefig(name, format="pdf", bbox_inches="tight")

def plot_corr_heatmap(df_corr, save=False, saveprefix=''):
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
  if save:
    plt.savefig(saveprefix + "correlation_heatmap.png", bbox_inches='tight')

def plot_output_scatter(results, targets,check_filter=None,
                        r2lim=None, rmselim=None, mapelim=None,
                        save=False, saveprefix=''):
  '''
  Create subplots for each column in ``results``. Each subplot shows
  scatter plots of the output value on the Y axis and the sample # on the X
  axis. The target value is shown as a dashed line.

  Optionally, ``results`` may be limited by R^2, RMSE, and/or MAPE by providing
  limits using r2lim, rmselim, and mapelim respectively.

  .. note::

    Not sure if this approach of putting everything in one giant figure will
    scale up with number of output variables very well...

  Parameters
  ==========
  results : pandas.DataFrame
    One column for each output variable, one row for each sample run.

  targets : pandas.DataFrame
    One column for each output (target) variable, single row with target value.

  check_filter : pandas.Series
    Series with boolean values for additional tests following
    SA run, e.g. equilibrium_check, eq_check['result']

  r2lim : float, optional
    Lower R^2 limit for output.

  rmselim : float, optional
    Upper RMSE limit for output.

  mapelim : float, optional
    Upper MAPE limit for output.

  save : bool
    Assumes False so plot will not be saved. If set to true it will plot
    in current directory unless saveprefix is specified

  saveprefix: str
    A prefix to be prepended to the saved file name 'output_target_scatter.png'

  Returns
  =======
  None

  .. image:: /images/SA_post_hoc_analysis/output_target_scatter.png
  '''
  # Calculate r2, rmse, mape metrics and create pandas data series
  r2, rmse, mape = calc_metrics(results, targets)
  df_r2 = pd.Series( r2,  name = '$R^2$'  )
  df_rmse = pd.Series( rmse,  name = 'RMSE'  )
  df_mape = pd.Series( mape,  name = 'MAPE'  )

  # Create a square of subplots based on the square root of number of columns
  fig_size = int(np.ceil(np.sqrt(len(results.columns))))
  # Create indices for looping through subplots
  fig_indices = np.linspace(0, fig_size - 1, fig_size).astype(int)
  # Create subplots
  fig, ax = plt.subplots(fig_size, fig_size)
  
  # Counter for results column number during subplot looping
  count = 0
  
  # Looping through rows and columns in subplot square
  for row in fig_indices:
    for col in fig_indices:
      # Break loop if we reach maximum number of columns before number of subplots
      if count >= len(results.columns):
        ax[row,col].set_axis_off()
      else:
        # Plot target line across number of samples
        ax[row, col].plot(results.index, np.ones(len(results.index)) * targets[targets.columns[count]].values[0], 'k--')
        # Scatter plots for results from all samples
        ax[row, col].scatter(results.index,results[results.columns[count]],
                             alpha=0.4, linewidth=0)
        if check_filter is not None:
          ax[row, col].scatter(results[check_filter==True].index,results[check_filter==True][results.columns[count]],
                             linewidth=2, edgecolor='green', facecolor='white')
        # label each subplot with output variable, pft, compartment, sample number
        ax[row, col].set_ylabel(results.columns[count])
        ax[row, col].set_xlabel("Sample number")
        # If an R^2 limit is given plot all results above that value
        if r2lim != None:
          ax[row, col].scatter(results[df_r2>r2lim].index,
                               results[df_r2>r2lim][results.columns[count]],
                               alpha=0.4, linewidth=0)
        # If an RMSE limit is given plot all results below that value
        if rmselim != None:
          ax[row, col].scatter(results[df_rmse<rmselim].index,
                               results[df_rmse<rmselim][results.columns[count]],
                               alpha=0.4, linewidth=0)
        # If a MAPE limit is given plot all results below that value
        if mapelim != None:
          ax[row, col].scatter(results[df_mape<mapelim].index,
                               results[df_mape<mapelim][results.columns[count]],
                               alpha=0.4, linewidth=0)
        # Go to next output variable
        count+=1    
  # Create a single legend with all handles provided outside of subplots
  legend_info = [Line2D([0], [0], color='k', linewidth=3, linestyle='--'),
                 Line2D([0], [0], marker='o', markersize=5, markeredgecolor='C0', markerfacecolor='C0', linestyle=''),
                 Line2D([0], [0], marker='o', markersize=5, markeredgecolor='green', markerfacecolor='white', linestyle='', linewidth=2),
                 Line2D([0], [0], marker='o', markersize=5, markeredgecolor='C1', markerfacecolor='C1', linestyle=''),
                 Line2D([0], [0], marker='o', markersize=5, markeredgecolor='C2', markerfacecolor='C2', linestyle=''),
                 Line2D([0], [0], marker='o', markersize=5, markeredgecolor='C3', markerfacecolor='C3', linestyle='')]
  legend_labels = ['Observations', 'Model', 'Check', f'R$^2$>{r2lim}',f'RMSE<{rmselim}', f'MAPE<{mapelim}']
  # Apply legend
  lgd = fig.legend(legend_info, legend_labels, bbox_to_anchor=(1., 1.), loc="upper left", fontsize=10)
  # Apply tight layout
  plt.tight_layout()
  # Save figure
  if save:
    fig.savefig(saveprefix + 'output_target_scatter.png', bbox_inches='tight')

def plot_r2_rmse(results, targets, check_filter=None, save=False, saveprefix=''):
  '''

  Plot R^2 against RMSE as a scatter plot for all runs

  Parameters
  ----------
  results: pandas.DataFrame
    One row per sample, one column per output.

  sample_matrix: pandas.DataFrame
    One row per sample, one column per parameter.

  targets: pandas.DataFrame
    One row with one column per target value.

  check_filter : pandas.Series
    Series with boolean values for additional tests following
    SA run, e.g. equilibrium_check, eq_check['result']

  save : bool
    Assumes False so plot will not be saved. If set to true it will plot
    in current directory unless saveprefix is specified

  saveprefix : str
    A string that is prepended to the saved filename '{var}_pft_plot.pdf'


  Returns
  -------
  None

  .. image:: /images/SA_post_hoc_analysis/r2_mse_mape.png

  '''

  r2, rmse, mape = calc_metrics(results, targets)
  r2 = pd.DataFrame(r2)
  rmse = pd.DataFrame(rmse)
  mape = pd.DataFrame(mape)

  plt.close('all')
  fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12,12))

  axes[0].plot(r2,rmse, 'o', alpha=.5)
  if check_filter is not None:
    axes[0].plot(r2[check_filter==True],rmse[check_filter==True], 'o', alpha=.5, color='green')
  axes[0].set_xlabel('r2')
  axes[0].set_ylabel('rmse')
  #axes[0].set_yscale('log')

  axes[1].plot(r2, mape, 'o', alpha=0.25)
  if check_filter is not None:
    axes[1].plot(r2[check_filter==True],mape[check_filter==True], 'o', alpha=.5, color='green')
  axes[1].set_xlabel('r2')
  axes[1].set_ylabel('mape')

  if save:
    plt.savefig(saveprefix + "r2_rmse_mape.png", bbox_inches='tight')

def nitrogen_check(path='', biome='boreal', save=False, saveprefix=''):
  '''
  Plots INGPP : GPP ratio to examine nitrogen limitation
  and compares to expected ranges for boreal and tundra
  ecosystems. 

  Note: this requires auxiliary variables INGPP, GPP, and
  AVLN to be specified in the config file. If calib_mode is set
  to GPPAllIgnoringNitrogen this will not produce meaningful 
  results.

  Parameters
  ==========
  path : str
      Specifies path to sensitivity sample run directory
  
  Returns
  =======
  None

  .. image:: /images/SA_post_hoc_analysis/n-check-comp-plot.png
  .. image:: /images/SA_post_hoc_analysis/n-check-barplot.png
  
  '''

  # filtering for directories containing the name sample 
  samples = np.sort([name for name in os.listdir(path) if os.path.isdir(path+name) and "sample" in name])
  
  #Catch if no sample directories exist
  if len(samples)<1:
    print("No sample directories found.")
    return
  
  # dataframe for returning INGPP ratio, pass/fail, AVLN
  n_check = pd.DataFrame(index=range(len(samples)), columns=['ratio','avln','result'])
  n_check['result'] = False
  
  # setting up subplots for INGPP:GPP and AVLN
  fig, ax = plt.subplots(1, 2, figsize=(10,10))
  
  # looping through samples
  for i, sample in enumerate(samples):

    # creating sample-specific path to output folder
    dir_path = os.path.join(path, sample, 'output')

    # catch if there is no folder
    if not os.path.exists(dir_path):
      print(f"Folder '{sample_folder}' not found. Skipping...")
      continue

    # specifying paths for AVLN, GPP, and INGPP
    avln_path = os.path.join(dir_path, 'AVLN_yearly_eq.nc')
    gpp_path = os.path.join(dir_path, 'GPP_yearly_eq.nc')
    ingpp_path = os.path.join(dir_path, 'INGPP_yearly_eq.nc')

    # catch if output variables do not exist
    if not (os.path.exists(avln_path) and os.path.exists(gpp_path) and os.path.exists(ingpp_path)):
      print(f"Data files not found for '{sample_folder}'. Skipping...")
      continue

    # loading data
    avln = nc.Dataset(avln_path).variables["AVLN"][:].data[:,0,0]
    gpp = nc.Dataset(gpp_path).variables["GPP"][:].data[:,0,0]
    ingpp = nc.Dataset(ingpp_path).variables["INGPP"][:].data[:,0,0]

    # calculating ratio of INGPP:GPP for whole time series
    ingpp2gpp = ingpp / gpp

    # plotting ratio and avln
    ax[0].plot(ingpp2gpp, color='gray', alpha=0.25)
    ax[1].plot(avln, color='gray', alpha=0.25)

    # populating n_check dataframe:
    # taking the mean of the last 10 years of equilibrium
    n_check.iloc[i, 0] = np.mean(ingpp2gpp[-10:])
    n_check.iloc[i, 1] = np.mean(avln[-10:])
    
    # testing whether there is N-limitation 
    if biome=='boreal':
      if 1.15 <= np.mean(ingpp2gpp[-10:]) <= 1.35:
        n_check.iloc[i,2] = True
    elif biome=='tundra':
      if 1.4 <= np.mean(ingpp2gpp[-10:]) <= 1.6:
        n_check.iloc[i,2] = True

  # plotting visual bands for test acceptance
  if biome=='boreal':
    ax[0].plot(range(0,len(ingpp)), 1.25*np.ones(len(ingpp)), alpha=0.5, color='g', linestyle='--')
    ax[0].fill_between(range(0,len(ingpp)), 1.15*np.ones(len(ingpp)), 1.35*np.ones(len(ingpp)), alpha=0.25, color='g')
    num_pass = f"{len([i for i in n_check['ratio'].values if (1.15<=i<=1.35)])} out of {len(n_check['ratio'])} passed"
    per_pass = f"{100*(len([i for i in n_check['ratio'].values if (1.15<=i<=1.35)])/len(n_check['ratio']))}% passed"
    if 100*(len([i for i in n_check['ratio'].values if (1.15<=i<=1.35)])/len(n_check['ratio'])) <= 70:
      ax[0].set_title(f" {per_pass}, adjust micnup", fontsize=10)
    else:
      ax[0].set_title(f" {per_pass}, nitrogen is limited ", fontsize=10)
  if biome=='tundra':
    ax[0].plot(range(0,len(ingpp)), 1.5*np.ones(len(ingpp)), alpha=0.5, color='c', linestyle='--')
    ax[0].fill_between(range(0,len(ingpp)), 1.4*np.ones(len(ingpp)), 1.6*np.ones(len(ingpp)), alpha=0.25, color='c')
    num_pass = f"{len([i for i in n_check['ratio'].values if (1.4<=i<=1.6)])} out of {len(n_check['ratio'])} passed"
    per_pass = f"{100*(len([i for i in n_check['ratio'].values if (1.4<=i<=1.6)])/len(n_check['ratio']))}% passed"
    if 100*(len([i for i in n_check['ratio'].values if (1.4<=i<=1.6)])/len(n_check['ratio'])) <= 70:
      ax[0].set_title(f" {per_pass}, adjust micnup", fontsize=10)
    else:
      ax[0].set_title(f" {per_pass}, nitrogen is limited ", fontsize=10)
  
  ax[0].set_xlabel("Equilibrium years", fontsize=12)
  ax[0].set_ylabel("INGPP : GPP", fontsize=12)
  
  ax[1].set_title("Is AVLN in this plot what you expect?", fontsize=10)
  ax[1].set_xlabel("Equilibrium years", fontsize=12)
  ax[1].set_ylabel("AVLN [g m$^{-2}$]", fontsize=12)

  plt.tight_layout()
  
  if save:
    plt.savefig(saveprefix + "n-check-comp-plot.png", bbox_inches='tight')
  
  counts = n_check['result'].replace(False, 'Fail')
  counts = pd.DataFrame(counts.replace(True, 'Pass'))
  
  counts = counts.apply(pd.value_counts)
  
  # add catch for only True / only False:
  if len(counts.index)==1:
    if counts.index=='Fail':
      counts = pd.DataFrame(index=['Pass', 'Fail'], columns=['result'], data=[0.0, counts['result'].values[0]])
    elif counts.index=='Pass':
      counts = pd.DataFrame(index=['Pass', 'Fail'], columns=['result'], data=[counts['result'].values[0], 0.0])
  # converting result into percentage
  counts = counts / counts.sum()[0] * 100
  
  fig, ax = plt.subplots()    
  ax.bar(counts[counts.index=='Pass'].columns, counts[counts.index=='Pass'].values[0], color='Green', alpha=0.5, label='Pass')
  ax.bar(counts[counts.index=='Fail'].columns, counts[counts.index=='Fail'].values[0], bottom=counts[counts.index=='Pass'].values[0], color='red', alpha=0.5, label='Fail')

  plt.xticks([0],['INGPP:GPP'],rotation='vertical')
  ax.set_ylabel(" Equilibrium pass / fail [%] ", fontsize=12)
  plt.legend(loc='upper right', fontsize=12)
  
  if counts.iloc[0,0]>0:
    plt.title(f"mean AVLN for passes: {np.round(n_check[n_check['result']=='Pass']['avln'].mean(), 4)}")
  else:
    plt.title(f"mean AVLN: {np.round(n_check['avln'].mean(), 4)}")
  
  if save:
    plt.savefig(saveprefix + "_n-check-barplot.png", bbox_inches='tight')

  return n_check, counts

def calc_combined_score(results, targets):
  '''Calculate a combination score using r^2, and normalized mse and mape.'''

  r2, rmse, mape = calc_metrics(results, targets)

  # normalize mse and mape to be between 0 and 1
  norm_rmse = (rmse - np.nanmin(rmse)) / (np.nanmax(rmse) - np.nanmin(rmse))
  norm_mape = (mape - np.nanmin(mape)) / (np.nanmax(mape) - np.nanmin(mape))

  # combined accuracy by substracting average of mse and mape from r2
  combined_score = r2 - np.mean([norm_rmse, norm_mape])

  return combined_score

def generate_ca_config():
  '''Maybe we should auto-generate the yaml config files?'''
  pass  

def prep_mads_initial_guess(params, fmt=None):
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
  fmt : str
    A user supplied format string specification. Should be something that
    you would find on the right side of the colon in an f string format spec,
    for example something like: '8.3f' or '3.5f'

  Returns
  -------
  str
    MADS initial guess string.
  '''
  # First get the min and max for each column
  ranges = [(params[x].min(), params[x].max(), x) for x in params]

  s2 = 'mads_initialguess:\n'
  for MIN, MAX, comment in ranges:
    ig = scipy.stats.uniform(loc=MIN, scale=MAX-MIN).mean()
    if fmt:
      s_tmp = '- {ig:' + f'{fmt}' + '}' + f'   # {comment}\n'
      s2 += s_tmp.format(ig=ig)
    else:
      s2 += f"- {ig:8.3f}  # {comment}\n"

  return s2

def prep_mads_distributions(params, fmt=None):
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
  fmt : str
    A user supplied format string specification. Should be something that
    you would find on the right side of the colon in an f string format spec,
    for example something like: '8.3f' or '3.5f'

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
    if fmt:
      s_tmp = "- Uniform({MIN:" + f'{fmt}' + '}, {MAX:' + f'{fmt}' + '})   '+f'# {comment}\n'
      s += s_tmp.format(MIN=MIN, MAX=MAX, comment=comment)
    else:
      s += f"- Uniform({MIN:8.3f}, {MAX:8.3f})    # {comment}\n"

  return s

def n_top_runs(results, targets, params, r2lim, N=None):
  '''
  Get the best runs measured using R^2, if N is present sort and return
  N top runs.

  Parameters
  ==========
  results : pandas.DataFrame
    One column for each output variable, one row for each sample run.

  targets : pandas.DataFrame
    One column for each output (target) variable, single row with target value.

  params : pandas.DataFrame
    One row for each of the selected runs, one column for each parameter.

  r2lim : float
    Lower R^2 limit for output.
  
  N : integer, optional
    Number of sorted results to return

  Returns
  -------
  best_params : pandas.DataFrame
    parameters returning variables above R^2 threshold from target value, sorted 
    top N number if None!=None

  best_results : pandas.DataFrame
    results above R^2 threshold from target value, sorted
    top N number if None!=None

  '''
  # Calculate r2, rmse, mape metrics and create pandas data series
  r2, rmse, mape = calc_metrics(results, targets)
  df_r2 = pd.Series( r2,  name = '$R^2$'  )

  if N is not None:
      best_indices = np.argsort(df_r2)
      sorted_params = params.iloc[best_indices]
      sorted_results = results.iloc[best_indices]
      best_params = sorted_params[:N]
      best_results = sorted_results[:N]
  else:
      best_params = params[df_r2>r2lim]
      best_results = results[df_r2>r2lim]

  return best_params, best_results

def plot_equilibrium_metrics_scatter(eq_params, targets, cv_lim=15, p_lim = 0.1, slope_lim = 0.001, save=False, saveprefix=''):
  '''
  Plots equilibrium metrics against certain quality thresholds
  for a target variable
  
  Parameters
  ==========
  eq_params : Pandas DataFrame
    equilibrium quality dataframe for a single target variable
  targets : Pandas DataFrame
    Used to read in target variable names
  cv_lim : float
    coefficient of variation threshold as a %
  p_lim : float
    p-value threshold as a %
  slope_lim : float
    slope threshold as a fraction of target variable
  save : bool
    saves figure if True
  saveprefix : string
    path to use if saving is enabled
    
  Returns
    None
  
  .. image:: /images/SA_post_hoc_analysis/eq_metrics_plot.png
  
  '''

  # splitting eq_params to provide information for selecting targets
  # and counting pfts and compartments if any
  var_info = np.asarray([i.split('_') for i in eq_params.columns])
  # taking variable names including pft and compartment if any
  var_names = np.unique([i.split('_eq')[0] for i in eq_params.columns])
  # getting eq_params specific unique parameter name for referencing
  var = np.unique(var_info[:,0])[0]

  # counting pfts and compartments
  # defining data for referencing and partitioning
  
  # if there are compartments and pfts
  if len(var_info[0])==5:
    pfts = var_info[:,1]
    pft_num = len(np.unique(var_info[:,1]))
    comp_num = len(np.unique(var_info[:,2]))
    comps = var_info[:,2]
    comps_names = []
    var_num = int(len(comps) / 3)
  # if there are just pfts        
  elif len(var_info[0])==4:
    pfts = var_info[:,1]
    pft_num = len(np.unique(var_info[:,1]))
    comp_num = 0
    var_num = int(len(pfts) / 3)
  # if there are no pfts or compartments
  else:
    pft_num = 0
    comp_num = 0
    var_num = 1

  # filtering targets dataframe by specific variable
  targets = targets.filter(regex=var)

  # looping through total number of variables (pft, compartment specific)
  for i in range(var_num):

    # defining subplot for each pft-compartment specific variable
    # for each eq_metric (cv, p, slope)
    fig, ax = plt.subplots(3, 1)

    # referencing for whether there are pfts and compartments or not
    if pft_num == 0:
      eq_ref = eq_params.columns
    else:
      eq_ref = eq_params.filter(regex=f'{var_names[i]}')

    # looping through each column in reference dataframe
    for col in eq_ref:

      # catching data for each metric (cv, p, slope) 
      # and creating scatter plots
      if "_eq_cv" in col:
          ax[0].scatter(eq_params.index, abs(eq_params[col]) * 100, marker='o', label = col.split('_eq')[0], alpha=0.25)
      if "_eq_p" in col:
          ax[1].scatter(eq_params.index, eq_params[col] , marker='o', alpha=0.25)
      if "_eq_slope" in col:
          ax[2].scatter(eq_params.index, abs(eq_params[col]) , marker='o', alpha=0.25)

      # Figure formatting
      ax[0].plot(eq_params.index, cv_lim * np.ones(len(eq_params)), 'k--')
      ax[0].set_ylabel("cv [%]", fontsize=10)
      ax[0].set_xticks([])
      ax[0].set_title(targets.columns[i]) #+'  '+col) - this can be used to check indexing matches
      
      ax[1].plot(eq_params.index, p_lim * np.ones(len(eq_params)), 'k--')
      ax[1].set_ylabel("p-value", fontsize=10)
      ax[1].set_xticks([])

      ax[2].plot(eq_params.index, slope_lim * targets[targets.columns[i]].values * np.ones(len(eq_params)), 'k--')        
      ax[2].set_xlabel("Index", fontsize=12)
      ax[2].set_ylabel("Slope", fontsize=10)

    # save if save=True
    if save:
      plt.savefig(saveprefix + f"{targets.columns[i]}_eq_metrics_scatterplot.png", bbox_inches="tight") 

def plot_equilibrium_metrics_boxplot(eq_params, targets, cv_lim=15, p_lim = 0.1, slope_lim = 0.001, save=False, saveprefix=''):
  '''
  Plots equilibrium metrics against certain quality thresholds
  for a target variable
  
  Parameters
  ==========
  eq_params : Pandas DataFrame
    equilibrium quality dataframe for a single target variable
  targets : Pandas DataFrame
    Used to read in target variable names
  cv_lim : float
    coefficient of variation threshold as a %
  p_lim : float
    p-value threshold as a %
  slope_lim : float
    slope threshold as a fraction of target variable
  save : bool
    saves figure if True
  saveprefix : string
    path to use if saving is enabled
    
  Returns
    None
  
  .. image:: /images/SA_post_hoc_analysis/eq_metrics_boxplot.png
  
  '''

  # splitting eq_params to provide information for selecting targets
  # and counting pfts and compartments if any
  var_info = np.asarray([i.split('_') for i in eq_params.columns])
  # taking variable names including pft and compartment if any
  var_names = np.unique([i.split('_eq')[0] for i in eq_params.columns])
  # getting eq_params specific unique parameter name for referencing
  var = np.unique(var_info[:,0])[0]

  # counting pfts and compartments
  # defining data for referencing and partitioning
  
  # if there are compartments and pfts
  if len(var_info[0])==5:
    pfts = var_info[:,1]
    pft_num = len(np.unique(var_info[:,1]))
    comp_num = len(np.unique(var_info[:,2]))
    comps = var_info[:,2]
    comps_names = []
    var_num = int(len(comps) / 3)
  # if there are just pfts        
  elif len(var_info[0])==4:
    pfts = var_info[:,1]
    pft_num = len(np.unique(var_info[:,1]))
    comp_num = 0
    var_num = int(len(pfts) / 3)
  # if there are no pfts or compartments
  else:
    pft_num = 0
    comp_num = 0
    var_num = 1

  # filtering targets dataframe by specific variable
  targets = targets.filter(regex=var)
  
  # for each eq_metric (cv, p, slope)
  fig, ax = plt.subplots(3, 1)
  
  # looping through total number of variables (pft, compartment specific)
  for i in range(var_num):

    if var_num > 1:
      x_coords = np.linspace(0, var_num, var_num)
      y_coords = np.ones(var_num)
    else:
      x_coords = np.linspace(-0.1, 0.1, 2)
      y_coords = np.ones(var_num + 1)

    # referencing for whether there are pfts and compartments or not
    if pft_num == 0:
      eq_ref = eq_params.columns
    else:
      eq_ref = eq_params.filter(regex=f'{var_names[i]}')

    # looping through each column in reference dataframe
    for col in eq_ref:

      # catching data for each metric (cv, p, slope) 
      # and creating box plots
      if "_eq_cv" in col:
        ax[0].boxplot(abs(eq_params[col]) * 100, positions=[i])
      if "_eq_p" in col:
        ax[1].boxplot(eq_params[col], positions=[i])
      if "_eq_slope" in col:
        ax[2].boxplot(abs(eq_params[col]), positions=[i])

      # Figure formatting
      ax[0].plot(x_coords, cv_lim * y_coords, 'k--')
      ax[0].set_ylabel("cv [%]", fontsize=10)
      ax[0].set_xticks([])
      ax[0].set_title(var) #+'  '+col) - this can be used to check indexing matches
      
      ax[1].plot(x_coords, p_lim * y_coords, 'k--')
      ax[1].set_ylabel("p-value", fontsize=10)
      ax[1].set_xticks([])
      if "_eq_slope" in col and var_num>1:
        ax[2].plot(x_coords, slope_lim * targets[targets.columns[i]].values * y_coords, 
                    f'C{i}--', label=targets.columns[i])
        ax[2].legend(bbox_to_anchor=(1, 1))
      elif "_eq_slope" in col and var_num<=1:
        ax[2].plot(x_coords, slope_lim * targets[targets.columns[i]].values * y_coords, 'k--')
          
      ax[2].set_xticks(np.linspace(0, var_num, var_num), targets.columns, rotation=90)
      ax[2].set_xlabel("Parameter", fontsize=12)
      ax[2].set_ylabel("Slope", fontsize=10)

  # save if save=True
  if save:
    plt.savefig(saveprefix + f"{targets.columns[i]}_eq_metrics_boxplot.png", bbox_inches="tight")   

def plot_equilibrium_relationships(path='', save=False, saveprefix=''):
  '''
  Plots equilibrium timeseries for target variables in output directory
  
  Parameters
  ==========
  path : str
    specifies path to sensitivity sample run directory
  save : bool
    saves figure if True
  saveprefix : string
    path to use if saving is enabled
  
  Returns
    None
  
  .. image:: /images/SA_post_hoc_analysis/eq_rel_plot.png
  
  '''
  # defining list of strings for compartment reference
  comp_ref = ['Leaf', 'Stem', 'Root']
  
  # reading targets directly from folder to match with output variables
  targets = pd.read_csv(path+'targets.csv', skiprows=1)
  
  # splitting column names to provide variable, pft, and compartment if available
  targ_info = [i.split('_') for i in targets.columns]
  
  # returning only unique variable names for file selection
  targ_vars = np.unique([i.split('_')[0] for i in targets.columns])

  # looping through each target variable
  for targ in targ_vars:
    
    # filtering for said target variable
    targ_filter = [targ in info for info in targ_info]

    # returning filtered information on variable, pft, compartment
    targ_var_info = [i for indx,i in enumerate(targ_info) if targ_filter[indx] == True]

    # operations depending on variable, pft, compartment
    if len(targ_var_info[0]) == 1:
      fig, ax = plt.subplots()
    if len(targ_var_info[0]) == 2:
      fig, ax = plt.subplots(1, len(targ_var_info))
    if len(targ_var_info[0]) == 3:
      fig, ax = plt.subplots(3, len(np.unique(np.asarray(targ_var_info)[:,1])))

    # filtering for directories containing the name sample 
    samples = np.sort([name for name in os.listdir(path) if os.path.isdir(path+name) and "sample" in name])
    
    # looping through sample folders in directory:
    for n, sample in enumerate(samples):

      # reading output variable for each sample
      output = nc.Dataset(path+sample+f'/output/{targ}_yearly_eq.nc').variables[targ][:].data

      # selecting variable dimensions based on whether pft, compartment is expected 
      # nopft:
      if len(targ_var_info[0]) == 1:
        ax.plot(output[:,0,0], 'gray', alpha=0.5)
        ax.plot(np.linspace(0, len(output[:,0,0]), len(output[:,0,0])), 
                          targets[targ].values[0]*np.ones(len(output[:,0,0])), 'k--', alpha=0.5)
        fig.supxlabel("Equilibrium years", fontsize=12)
        fig.supylabel(f"{targ}", fontsize=12)
        fig.tight_layout()
      # pft no compartment    
      if len(targ_var_info[0]) == 2:
        
        for p in targ_var_info:

          pft = int(p[1].split('pft')[1])
          
          ax[pft].plot(output[:,pft,0,0], f'C{pft}', alpha=0.5)    
          ax[pft].set_title(f"PFT{pft}")
          ax[pft].plot(np.linspace(0, len(output[:,pft,0,0]), len(output[:,pft,0,0])), 
                targets[p[0]+'_'+p[1]].values[0]*np.ones(len(output[:,pft,0,0])), 'k--', alpha=0.5)

        fig.supxlabel("Equilibrium years", fontsize=12)
        fig.supylabel(f"{targ}", fontsize=12)
        fig.tight_layout()
      # pft and compartment
      if len(targ_var_info[0]) == 3:

        for p in targ_var_info:

          pft = int(p[1].split('pft')[1])

          comp = p[2]; comp_index = comp_ref.index(comp)
          
          ax[comp_index, pft].plot(output[:,comp_index,pft,0,0], f'C{pft}', alpha=0.5)
          ax[0, pft].set_title(f"PFT{pft}")
          ax[comp_index, pft].plot(np.linspace(0, len(output[:,comp_index,pft,0,0]), len(output[:, comp_index,pft,0,0])), 
                targets[p[0]+'_'+p[1]+'_'+p[2]].values[0]*np.ones(len(output[:,comp_index,pft,0,0])), 'k--', alpha=0.5)

        ax[0, 0].set_ylabel("Leaf")
        ax[1, 0].set_ylabel("Stem")
        ax[2, 0].set_ylabel("Root")
        fig.supxlabel("Equilibrium years", fontsize=12)
        fig.supylabel(f"{targ}", fontsize=12)
        fig.tight_layout()
          
  # save if save=True
  if save:
    plt.savefig(saveprefix + f"{targ}_eq_rel_plot.png", bbox_inches='tight')

def generate_eq_lim_dict(targets, cv_lim=[0], p_lim=[0], slope_lim=[0]):
  '''
  Creates a dictionary of thresholds for individual target variables to be
  used for equilibrium checking. Note: limits must match length of targets
  otherwise defaults will be used.

  E.g.
  lim_dict = generate_eq_lim_dict(targets, 
                    cv_lim = [15,15,15,15,15],
                    p_lim = [0.1,0.1,0.1,0.1,0.1],
                    slope_lim = [0.001,0.001,0.001,0.001,0.001])
  Parameters
  ==========
  targets : Pandas DataFrame
    observed data for comparison, must match up with equilibrium check directory used
  cv_lim : list
    coefficient of variation threshold as a %, for each variable in targets
  p_lim : float
    p-value threshold, for each variable in targets
  slope_lim : float
    slope threshold as a fraction of target variable, for each variable in targets
    
  Returns
    lim_dict : Dict
      individual thresholds to be used in equilibrium_check

  '''
    
  if (len(targets.columns) != len(cv_lim)) or (len(targets.columns) != len(p_lim)) or (len(targets.columns) != len(slope_lim)):
    print('cv_lim, p_lim, and slope_lim must be lists with the same length as the number of targets')
    print(' DEFAULTS HAVE BEEN USED cv lim = 15%, p lim = 0.1, slope lim = 0.001')
    cv_lim = np.repeat(15, len(targets.columns)); p_lim = np.repeat(0.1, len(targets.columns)); slope_lim = np.repeat(0.001, len(targets.columns))

  keys = [x + y for x,y in zip(np.repeat(targets.columns.values[:].tolist(), 3), np.tile(['_slope_lim','_p_lim','_cv_lim'], len(targets.columns.values)))]
  values = []
  for i in range(0, len(targets.columns)):
    values.append(slope_lim[i])
    values.append(p_lim[i])
    values.append(cv_lim[i])
      
  lim_dict = dict(zip(keys, values))

  return lim_dict

def equilibrium_check(path, cv_lim=15, p_lim = 0.1, slope_lim = 0.001, lim_dict=False, save=False, saveprefix=''):
  '''
  Calculates percentage of samples which pass user input (or default)
  equilibrium test and plots a bar graph.

  E.g.

  total_counts, counts, eq_check, eq_var_check, eq_data, eq_metrics, lim_dict = SA_post_hoc_analysis.equilibrium_check(work_dir)
  
  Parameters
  ==========
  path : str
    specifies path to sensitivity sample run directory
  cv_lim : float
    coefficient of variation threshold as a %
  p_lim : float
    p-value threshold as a %
  slope_lim : float
    slope threshold as a fraction of target variable
  lim_dict : dict
    provides a dictionary of specific thresholds for each variable
  save : bool
    saves figure if True
  saveprefix : string
    path to use if saving is enabled
    
  Returns
    total_counts : Pandas DataFrame
      overall pass/fail percentage result for all runs
    counts : Pandas DataFrame
      Pass / Fail percentage for each variable
    eq_check : Pandas DataFrame
      Boolean for each run compiling overall result of cv, p, slope test
      for all variables per run must pass all variables to pass
    eq_var_check : Pandas DataFrame
      Boolean for each variable compiling overall result of cv, p, slope test
      must pass all tests to pass
    eq_data : Pandas DataFrame
      Boolean for each variable and each test for more thorough inspection
    eq_metrics : Pandas DataFrame
      Containing float values for each variable for each testing metric (cv, p, slope)
    lim_dict : dict
      dictionary of theshold used, either uniformly or independent to each variable
  
  .. image:: /images/SA_post_hoc_analysis/eq_plot.png
  
  '''
    
  # defining list of strings for compartment reference
  comp_ref = ['Leaf', 'Stem', 'Root']
  
  # reading targets directly from folder to match with output variables
  targets = pd.read_csv(path+'targets.csv', skiprows=1)
  
  # splitting column names to provide variable, pft, and compartment if available
  targ_info = [i.split('_') for i in targets.columns]
  
  # returning only unique variable names for file selection
  targ_vars = np.unique([i.split('_')[0] for i in targets.columns])
  
  # filtering for directories containing the name sample 
  samples = np.sort([name for name in os.listdir(path) if os.path.isdir(path+name) and "sample" in name])
  
  # output dataframe creation
  
  # returning data on individual checks
  eq_data_columns = [x + y for x,y in zip(np.repeat(targets.columns.values[:].tolist(), 3), np.tile(['_slope','_p','_cv'], len(targets.columns.values)))]
  # boolean data
  eq_data = pd.DataFrame(index=range(len(samples)), columns=eq_data_columns, data=False)
  # metrics
  eq_metrics = pd.DataFrame(index=range(len(samples)), columns=eq_data_columns, data=0.0)
  
  # returning boolean for pass fail for each variable
  eq_var_check = pd.DataFrame(index=range(len(samples)), columns=targets.columns, data=False)
  
  # returning boolean for pass fail for run
  eq_check = pd.DataFrame(index=range(len(samples)), columns=['result'], data=False)
  
  # looping through sample folders in directory:
  for n, sample in enumerate(samples):

    # looping through each target variable
    for targ in targ_vars:

      # filtering for said target variable
      targ_filter = [targ in info for info in targ_info]
      
      # returning filtered information on variable, pft, compartment
      targ_var_info = [i for indx,i in enumerate(targ_info) if targ_filter[indx] == True] 

      # reading output variable for each sample
      output = nc.Dataset(path+sample+f'/output/{targ}_yearly_eq.nc').variables[targ][:].data

      # selecting variable dimensions based on whether pft, compartment is expected 
      # nopft:
      if len(targ_var_info[0]) == 1:
        
        slope, intercept, r, pval, std_err = scipy.stats.linregress(range(len(output[-30:,0,0])), output[-30:,0,0])
        cv = 100 * output[-30:,0,0].std() / output[-30:,0,0].mean()

        eq_metrics[targ+f'_slope'].loc[n] = slope
        eq_metrics[targ+f'_p'].loc[n] = pval
        eq_metrics[targ+f'_cv'].loc[n] = cv

        if lim_dict!=False:
          cv_lim=lim_dict[targ+'_cv_lim']
          p_lim = lim_dict[targ+'_p_lim']
          slope_lim = lim_dict[targ+'_slope_lim']

        if slope < slope_lim * targets[targ].values[0]:
          eq_data[targ+f'_slope'].loc[n] = True
        if pval < p_lim:
          eq_data[targ+f'_p'].loc[n] = True
        if cv * 100 < cv_lim:
          eq_data[targ+f'_cv'].loc[n] = True

        if ((eq_data[targ+f'_slope'].loc[n] == True) & 
            (eq_data[targ+f'_p'].loc[n] == True) & 
            (eq_data[targ+f'_cv'].loc[n] == True)):

          eq_var_check[targ].loc[n] = True
            
      # variable with pft but no compartment
      if len(targ_var_info[0]) == 2:
        
        for p in targ_var_info:

          pft = int(p[1].split('pft')[1])
            
          slope, intercept, r, pval, std_err = scipy.stats.linregress(range(len(output[-30:,pft,0,0])), output[-30:,pft,0,0])
          cv = 100 * output[-30:,pft,0,0].std() / output[-30:,pft,0,0].mean()

          eq_metrics[targ+f'_pft{pft}_slope'].loc[n] = slope
          eq_metrics[targ+f'_pft{pft}_p'].loc[n] = pval
          eq_metrics[targ+f'_pft{pft}_cv'].loc[n] = cv

          if lim_dict!=False:
            cv_lim=lim_dict[targ+f'_pft{pft}_cv_lim']
            p_lim = lim_dict[targ+f'_pft{pft}_p_lim']
            slope_lim = lim_dict[targ+f'_pft{pft}_slope_lim']

          if slope < slope_lim * targets[targ+f'_pft{pft}'].values[0]:
            eq_data[targ+f'_pft{pft}_slope'].loc[n] = True
          if pval < p_lim:
            eq_data[targ+f'_pft{pft}_p'].loc[n] = True
          if cv * 100 < cv_lim:
            eq_data[targ+f'_pft{pft}_cv'].loc[n] = True

          if ((eq_data[targ+f'_pft{pft}_slope'].loc[n] == True) & 
              (eq_data[targ+f'_pft{pft}_p'].loc[n] == True) & 
              (eq_data[targ+f'_pft{pft}_cv'].loc[n] == True)):

            eq_var_check[targ+f'_pft{pft}'].loc[n] = True

      # variable with pfts and compartments
      if len(targ_var_info[0]) == 3:
  
        for p in targ_var_info:
  
          pft = int(p[1].split('pft')[1])
  
          comp = p[2]; comp_index = comp_ref.index(comp)

          slope, intercept, r, pval, std_err = scipy.stats.linregress(range(len(output[-30:,comp_index,pft,0,0])), output[-30:,comp_index,pft,0,0])
          cv = 100 * output[-30:,comp_index,pft,0,0].std() / output[-30:,comp_index,pft,0,0].mean()

          eq_metrics[targ+f'_pft{pft}_{comp}_slope'].loc[n] = slope
          eq_metrics[targ+f'_pft{pft}_{comp}_p'].loc[n] = pval
          eq_metrics[targ+f'_pft{pft}_{comp}_cv'].loc[n] = cv

          if lim_dict!=False:
            cv_lim=lim_dict[targ+f'_pft{pft}_{comp}_cv_lim']
            p_lim = lim_dict[targ+f'_pft{pft}_{comp}_p_lim']
            slope_lim = lim_dict[targ+f'_pft{pft}_{comp}_slope_lim']

          if slope < slope_lim * targets[targ+f'_pft{pft}_{comp}'].values[0]:
            eq_data[targ+f'_pft{pft}_{comp}_slope'].loc[n] = True
          if pval < p_lim:
            eq_data[targ+f'_pft{pft}_{comp}_p'].loc[n] = True
          if cv * 100 < cv_lim:
            eq_data[targ+f'_pft{pft}_{comp}_cv'].loc[n] = True

          if ((eq_data[targ+f'_pft{pft}_{comp}_slope'].loc[n] == True) & 
              (eq_data[targ+f'_pft{pft}_{comp}_p'].loc[n] == True) & 
              (eq_data[targ+f'_pft{pft}_{comp}_cv'].loc[n] == True)):

            eq_var_check[targ+f'_pft{pft}_{comp}'].loc[n] = True

    if eq_var_check.iloc[n, :].all() == True:
      eq_check.loc[n] = True
  
  counts = eq_var_check.apply(pd.value_counts)
  total_counts = eq_check.apply(pd.value_counts)
  
  # add catch for only True / only False:
  if len(counts.index)==1:
    if counts.index==False:
      counts = pd.DataFrame(index=['pass', 'fail'], columns=targets.columns, data=[0.0, counts.iloc[0,:]])
    elif counts.index==True:
      counts = pd.DataFrame(index=['pass', 'fail'], columns=targets.columns, data=[counts.iloc[0,:], 0.0])
  else:
    if counts.index[0]==False:
      counts = pd.DataFrame(index=['pass', 'fail'], columns=targets.columns, data=[counts.iloc[1,:], counts.iloc[0,:]])
    else:
      counts.index = ['pass', 'fail']
      
  # converting result into percentage
  counts = counts / counts.sum()[0] * 100
  
  # add catch for only True / only False:
  if len(total_counts.index)==1:
    if total_counts.index==False:
      total_counts = pd.DataFrame(index=['pass', 'fail'], columns=['result'], data=[0.0, total_counts.iloc[0,:]])
    elif total_counts.index==True:
      total_counts = pd.DataFrame(index=['pass', 'fail'], columns=['result'], data=[total_counts.iloc[0,:], 0.0])
  else:
    if total_counts.index[0]==False:
      total_counts = pd.DataFrame(index=['pass', 'fail'], columns=['result'], data=[total_counts.iloc[1,:], total_counts.iloc[0,:]])
    else:
      total_counts.index = ['pass', 'fail']
  # converting result into percentage
  total_counts = total_counts / total_counts.sum()[0] * 100
  
  fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(12,6))
  
  for i in range(0, len(eq_var_check)):
    ax[0].bar(eq_var_check.columns, 1, color=eq_var_check.iloc[i,:].replace(True, 'g').replace(False, 'r'),
            bottom=i * np.ones(len(eq_var_check.columns)), width=1, alpha=0.5)
  
  ax[0].set_ylabel('Sample Number', fontsize=12)
  ax[0].tick_params(labelrotation=90)
  
  ax[1].bar(np.linspace(1, len(counts.columns), len(counts.columns)), counts.iloc[0,:], color='Green', alpha=0.5, label=counts.index[0])
  ax[1].bar(np.linspace(1, len(counts.columns), len(counts.columns)), counts.iloc[1,:], bottom=counts.iloc[0,:], color='Red', alpha=0.5, label=counts.index[1])
  ax[1].set_xticks(np.linspace(1, len(counts.columns), len(counts.columns)),counts.columns, rotation=90)
  ax[1].set_ylabel(" Equilibrium pass / fail [%] ", fontsize=12)
  
  for i, col in enumerate(counts.columns):
    plt.annotate(str(int(counts[counts.index=='pass'][col].values))+'%', xy=(i+0.75, counts[counts.index=='pass'][col].values+2),
                  rotation=90, fontsize=8)
  
  plt.suptitle(f"{int(total_counts[total_counts.index=='pass'].values)}% pass", fontsize=16)
  plt.legend(loc='upper left', fontsize=12, bbox_to_anchor=(-0.5,1))

  if save:
    plt.savefig(saveprefix + col.split('_')[0] +"_eq_plot.png", bbox_inches='tight')

  if lim_dict==False:
    lim_dict = {
        "cv_lim": cv_lim,
        "p_lim": p_lim,
        "slope_lim":slope_lim
    }

  return total_counts, counts, eq_check, eq_var_check, eq_data, eq_metrics, lim_dict

def read_mads_iterationresults(iterationresults_file):
  '''
  Parse a Mads .iterationresults file and return data as 3 python lists.

  Example of the input file: 

  .. code::

    OrderedCollections.OrderedDict("cmax_pft0" => 26.245, "cmax_pft1" => ... )
    OF: 1.985656773338984e8
    lambda: 4.0e9
    OrderedCollections.OrderedDict("cmax_pft0" => 26.245, "cmax_pft1" => ... )
    OF: 1.6545342e4353453e6
    lambda: 1.4e6
  '''

  with open(iterationresults_file) as f:
    data = f.readlines()

  OF = []
  OPT = []
  LAM = []
  for i in data:
    if 'OF:' in i:
      OF.append(i.strip())
    if 'OrderedCollections.OrderedDict' in i:
      OPT.append(i.strip())
    if 'lambda:' in i:
      LAM.append(i.strip())

  def pyobjfromjl(a):
    '''
    This is a dangerous function!

    Use at your own risk and make sure your inputs are good!
    '''
    a = a.replace('=>','=')
    a = a.replace('OrderedCollections.OrderedDict', 'dict')
    a = a.replace('"','')
    return eval(a)

  OPT = [pyobjfromjl(x) for x in OPT]
  OF = [dict(OF=float(x.strip().split(':')[1].strip())) for x in OF]
  LAM = [dict(lam=float(x.strip().split(':')[1].strip())) for x in LAM]

  return OPT, OF, LAM

def load(path):
  '''
  Load up pandas.DataFrames for all the various things that you will want to
  analyze. This includes the parameter properties used for the SA, the
  sample matrix, the target data and the model results.

  Parameters
  ----------
  path: str
    A file path to a directory that is expected to have the following files:
    param_props.csv, sample_matrix.csv, targets.csv, results.csv.

  Returns
  -------
  param_props, sample_matrix, targets, results
  '''

  param_props = pd.read_csv(os.path.join(path, 'param_props.csv'))
  sample_matrix = pd.read_csv(os.path.join(path, 'sample_matrix.csv'))
  targets = pd.read_csv(os.path.join(path, 'targets.csv'), skiprows=1)
  results = pd.read_csv(os.path.join(path, 'results.csv'))

  return param_props, sample_matrix, targets, results

def get_parser():
  pass

def cmdline_parse():
  pass

def cmdline_run():
  pass

def cmdline_entry():
  pass

if __name__ == '__main__':

  # EXAMPLES HERE OF WHAT YOUR IPYTHON SESSION MIGHT LOOK LIKE.....

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