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
from sklearn.metrics import r2_score,mean_squared_error,mean_absolute_error
from sklearn.metrics import mean_absolute_percentage_error

def param_and_targets_box_plots(x,y,y_true):
    ''' plots the box plots the difererence between best parameters values and their mean 
        and best modeled values and targets 
        x: parameter dataframe (nxm)
        y: model output dataframe (nxm))
        y_true: target dataframe
    '''
    
    fig, axs = plt.subplots(1, 2, figsize=(8, 4))

    axs[0].boxplot(x-x.mean().values, labels=x.columns);
    axs[0].set_ylabel('parameters: x-$\overline{x}$', fontsize=12)
    axs[0].set_xticklabels(x.columns, rotation=45, fontsize=12)

    axs[1].boxplot(y-y_true.values, labels=y.columns);
    axs[1].set_ylabel('targets: y-$y_{obs}$', fontsize=12)
    axs[1].set_xticklabels(y.columns, rotation=45, fontsize=12)

    plt.tight_layout()

def best_mean_match_spagetti(df_x,df_y,site_name=''):
    ''' plots the spaghetti plot of modeled v.s. observed values 
        df_x: parameter dataframe (nxm)
        df_y: model output dataframe (nx(m+1)), last columns must be targets
        site_name: string 
    '''
    nrange=range(len(df_y.columns))
    df_xx, df_yy =  get_match_metric(df_x,df_y)

    rmetric='r2rmse'
    nelem=10
    order=True
    y=df_yy.sort_values(by=[rmetric],ascending=order)[:nelem]

    yy=y.iloc[:,:-6]
    yy.columns = list(nrange)
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(yy.mean().transpose(),alpha=0.5,color='black',linewidth=2.5)
    ax.plot(df_y.iloc[-1,:],'o',color='red')
    ax.fill_between(nrange, df_y.iloc[0:-1,:].min(), df_y.iloc[0:-1,:].max(), alpha=0.5,color='grey')
    ax.set_xticklabels(df_y.columns, rotation=45, fontsize=12)
    ax.set_title(f"{site_name}")
    #ax.setxtick(df_y.columns,fontsize=12)
    #ax.setylabel(ylabel,fontsize=14)
    #ax.xlim([-0.1,6.1])

    return

def plot_site_metric_matrix(metric_matrix, error, colorb=True):
    import seaborn as sns
    """Plot a heatmap for the given metric matrix."""
    [x_size,y_size]=metric_matrix.shape
    fig, ax = plt.subplots(figsize=(2+x_size, 3))

    cbar_label = 'RMSE score' if error == 'RMSE' else 'RE score'
    cmap = "GnBu" if colorb else "coolwarm"
    
    sns.heatmap(metric_matrix, cmap=cmap, annot=True, fmt=".3f",
                cbar_kws={'label': '', "orientation": 'vertical'},
                annot_kws={"fontsize": 12}, ax=ax, cbar=colorb)
    
    ax.tick_params(axis='x', rotation=45)
    ax.set_title(cbar_label)

    return

def get_metric_matrix(df_x,df_y,pft_names,error):
    ''' plots the metric matrix error between modeled and observed values for all pfts 
        df_x: parameter dataframe (nxm)
        df_y: model output dataframe (nx(m+1)), last columns must be targets
        pft_names: string list
        error: 'RMSE', 're' 

        Example:
        # for CMT1
        pft_names=['EverTree', 'DecidShrub', 'DecidTree', 'Moss']
        veg, soil = plot_veg_eq_metric_matrix(df_param,df_model,pft_names,'RMSE')

        Returns: vegetation and soil metric matrices
    '''
    def rmse(x, x_true):
        """Calculate Root Mean Square Error (RMSE)."""
        mse = np.square(np.subtract(x.mean(), x_true))
        return pd.DataFrame(np.sqrt(mse), index=x.columns)

    def relative_error(x, x_true):
        """Calculate Relative Error (RE)."""
        mae = np.subtract(x.mean(), x_true)
        return pd.DataFrame(np.abs(100 * mae / x_true ), index=x.columns)

    def get_values_or_fill(df, fallback_len):
        """
        Get the values from the DataFrame column or fill with NaN if empty.
        If the DataFrame has fewer rows than fallback_len, pad the result with NaN.

        Parameters:
        df (pd.DataFrame): The DataFrame from which to extract values.
        fallback_len (int): The required length of the output array.

        Returns:
        list: A list of values from the DataFrame column or NaN-filled values.
        """
        # If the DataFrame is not empty, get the values
        if not df.empty:
            values = df[0].values
            # Pad the values with NaN if it's shorter than fallback_len
            if len(values) < fallback_len:
                values = np.concatenate([values, [np.nan] * (fallback_len - len(values))])
        else:
            # If empty, fill with NaN
            values = [np.nan] * fallback_len
        
        return values


    def select_elements_from_df(df, word1, word2='', search_in='index'):
        """
        Select rows from a DataFrame where either the index or a specified column contains both word1 and word2.

        Parameters:
        df (pd.DataFrame): The DataFrame to search.
        word1 (str): The first word to match.
        word2 (str): The second word to match.
        search_in (str or list of str): Specifies where to search. Can be 'index' to search in the index, or 
                                        a column name (or list of column names) to search within specific columns.

        Returns:
        pd.DataFrame: A DataFrame containing rows where the index or specified columns match both words.
        """
        # Ensure case-insensitive matching by converting everything to lowercase
        word1 = word1.lower()
        word2 = word2.lower()
        
        if search_in == 'index':
            # Search in the index
            matched_rows = df[df.index.to_series().str.lower().str.contains(word1) & 
                            df.index.to_series().str.lower().str.contains(word2)]
        else:
            # Search in specified columns
            if isinstance(search_in, str):
                search_in = [search_in]  # Convert to list if a single column is passed
            mask = pd.Series(False, index=df.index)
            for col in search_in:
                mask = mask | (df[col].str.lower().str.contains(word1) & df[col].str.lower().str.contains(word2))
            matched_rows = df[mask]
        
        return matched_rows

        
    # filtering parameters
    nelem = 10
    order = True
    rmetric = 'r2rmse'

    # Perform post-hoc analysis
    xparams, ymodel = get_match_metric(df_x, df_y)

    # Sort the model data by rmetric and select the top 5 rows
    y_sort = ymodel.sort_values(by=[rmetric], ascending=order).iloc[:nelem, :-6].copy()

    # Calculate error (RMSE or RE)
    error_all = relative_error(y_sort, df_y.iloc[-1, :]) if error == 're' else rmse(y_sort, df_y.iloc[-1, :])
    if error_all.index[0] == 'CarbonShallow':
        error_all.index=['$C_{shallow}$','$C_{deep}$','$\sum C_{mineral}$','$\sum N_{avail}$']
        return error_all 

    # Select rows for INGPP, NPP, and VEGC0
    df_ingpp = select_elements_from_df(error_all, 'GPP')
    df_npp = select_elements_from_df(error_all, 'NPP')
    df_vegc_leaf = select_elements_from_df(error_all, 'VEGC', 'Leaf')
    df_vegc_stem = select_elements_from_df(error_all, 'VEGC', 'Stem')
    df_vegc_root = select_elements_from_df(error_all, 'VEGC', 'Root')
    df_vegn_leaf = select_elements_from_df(error_all, 'VEGN', 'Leaf')
    df_vegn_stem = select_elements_from_df(error_all, 'VEGN', 'Stem')
    df_vegn_root = select_elements_from_df(error_all, 'VEGN', 'Root')  
    df_C_shallow = select_elements_from_df(error_all, 'SHLWC')  
    df_C_deep    = select_elements_from_df(error_all, 'DEEPC' ) 
    df_C_mineral = select_elements_from_df(error_all, 'MINEC' )
    df_N_avail   = select_elements_from_df(error_all, 'AVLN' ) 

    n_pft=len(pft_names)

    # Handle missing data 
    ingpp_values = get_values_or_fill(df_ingpp, n_pft)
    npp_values = get_values_or_fill(df_npp, n_pft)
    vegc_leaf_values = get_values_or_fill(df_vegc_leaf, n_pft)
    vegc_stem_values = get_values_or_fill(df_vegc_stem, n_pft)
    vegc_root_values = get_values_or_fill(df_vegc_root, n_pft)
    vegn_leaf_values = get_values_or_fill(df_vegn_leaf, n_pft)
    vegn_stem_values = get_values_or_fill(df_vegn_stem, n_pft)
    vegn_root_values = get_values_or_fill(df_vegn_root, n_pft)
    df_C_shallow_values = get_values_or_fill(df_C_shallow, 1)
    df_C_deep_values = get_values_or_fill(df_C_deep, 1)
    df_C_mineral_values = get_values_or_fill(df_C_mineral, 1) 
    df_N_avail_values = get_values_or_fill(df_N_avail, 1) 

    # Create the target matrix
    veg_target_matrix = pd.DataFrame({
        'INGPP': ingpp_values,
        'NPP': npp_values,
        '$C_{leaf}$': vegc_leaf_values,
        '$C_{stem}$': vegc_stem_values,
        '$C_{root}$': vegc_root_values,
        '$N_{leaf}$': vegn_leaf_values,
        '$N_{stem}$': vegn_stem_values,
        '$N_{root}$': vegn_root_values
    })

    soil_target_matrix = pd.DataFrame({
        '$C_{shallow}$': df_C_shallow_values,
        '$C_{deep}$': df_C_deep_values,
        '$\sum C_{mineral}$':df_C_mineral_values,
        '$\sum N_{avail}$':df_N_avail_values
    })
    # Set the row labels
    veg_target_matrix.index = pft_names

    return veg_target_matrix, soil_target_matrix

def get_match_metric(x,y):
    '''
    Inputs:
    x: parameters dataframe 
    y: model outputs dataframe, where last row are targets

    Metrics:
    r2lim: the R square limit
    rmse: root mean square 
    mape: mean absolute precentage
    r2rmse: combined r2 & rmse
    r2rmsemape: combined r2, rmse, & mape
    df_combined_accuracy: Andrew's method

    Outputs extended dataframe:
    xresult: subset of the parameter with added 5 metric columns 
    yresult: subset of the model outputs with added 5 metric columns
    '''
    [n,m]=np.shape(y)
    r2=[r2_score(y.iloc[i,:], y.iloc[-1,:]) for i in range(n-1)]
    rmse=[mean_squared_error(y.iloc[i,:], y.iloc[-1,:]) for i in range(n-1)]
    mape=[mean_absolute_percentage_error(y.iloc[i,:], y.iloc[-1,:]) for i in range(n-1)]

    #convert lists to pd.series 
    df_r2 = pd.Series( r2,  name = 'R2'  )
    df_rmse = pd.Series( rmse,  name = 'RMSE'  )
    df_mape = pd.Series( mape,  name = 'MAPE'  )

    #normalize rmse and mape between 0 and 1
    df_rmse_normalized = pd.Series((df_rmse-np.nanmin(df_rmse))/(np.nanmax(df_rmse)-np.nanmin(df_rmse)), name='RMSE_NORM')
    df_mape_normalized = pd.Series((df_mape-np.nanmin(df_mape))/(np.nanmax(df_mape)-np.nanmin(df_mape)), name='MAPE_NORM')

    #create combined accuracy by subtracting average of rmse and mape from r2
    df_combined_accuracy = pd.Series(df_r2 - ((df_rmse_normalized + df_mape_normalized)/2), name='COMBINED_ACC')

    #merge r2, rmse, and others to the model table
    xresult = pd.concat([x, df_r2], axis=1)
    yresult = pd.concat([y.iloc[0:-1,:], df_r2], axis=1)
    xresult = pd.concat([xresult, df_rmse], axis=1)
    yresult = pd.concat([yresult, df_rmse], axis=1)
    xresult = pd.concat([xresult, df_mape], axis=1)
    yresult = pd.concat([yresult, df_mape], axis=1)
    xresult = pd.concat([xresult, df_combined_accuracy], axis=1)
    yresult = pd.concat([yresult, df_combined_accuracy], axis=1)

    df_r2[df_r2<0]=0
    ex = 1-df_r2
    ey = rmse/max(rmse)
    exy= pd.Series( np.sqrt(ex*ex+ey*ey),  name = 'r2rmse'  )
    xresult = pd.concat([xresult, exy], axis=1)
    yresult = pd.concat([yresult, exy], axis=1)

    ez = df_mape/max(df_mape)
    exyz= pd.Series( np.sqrt(ex*ex+ey*ey+ez*ez),  name = 'r2rmsemape'  )
    xresult = pd.concat([xresult, exyz], axis=1)
    yresult = pd.concat([yresult, exyz], axis=1)

    return xresult, yresult

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

  ax1.tick_params(labelrotation=90) 
  ax2.tick_params(labelrotation=90)

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
  '''
  Calculate a bunch of sklearn regression metrics & relative error
  
  returns r2, rmse, mape, re
  '''
  # This is gonna need some help...not seeming to pick the right stuff.\
  # not sure if weights should be passed to metrics function, like this:
  #
  #    weights_by_targets = targets.values[0]/targets.sum(axis=1)[0]
  #    r2 = [sklm.r2_score(targets.T, sample, sample_weight=weights_by_targets) for i,sample in results.iterrows()]

  r2 = [sklm.r2_score(targets.T, sample) for i,sample in results.iterrows()] 
  rmse = [sklm.mean_squared_error(targets.T, sample, squared=False) for i,sample in results.iterrows()]
  mape = [sklm.mean_absolute_percentage_error(targets.T, sample) for i,sample in results.iterrows()]
  
  re = [(100*(targets - sample)/sample) for i,sample in results.iterrows()] 

  return r2, rmse, mape, re

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
          if count > (len(parameters) - 1):
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
  plt.xticks(np.linspace(0.5, len(df_corr.columns)-0.5, len(df_corr.columns)), df_corr.columns, rotation=90)
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
  r2, rmse, mape, re = calc_metrics(results, targets)
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

  r2, rmse, mape, re = calc_metrics(results, targets)
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

  E.g. n_check, counts = nitrogen_check()

  Note: this requires auxiliary variables INGPP, GPP, and
  AVLN to be specified in the config file. If calib_mode is set
  to GPPAllIgnoringNitrogen this will not produce meaningful 
  results.

  Parameters
  ==========
  path : str
      Specifies path to sensitivity sample run directory
  biome : str
      Either 'boreal' or 'tundra' used to specify ratio 
      threshold between INGPP and GPP
  save : bool
      Saves figure if True
  saveprefix : str
      Specifies path to save figure if allowed
  
  Returns
  =======
  n_check : Pandas.DataFrame
      results of nitrogen checking analysis
  counts : Pandas.DataFrame
      final result counts as pass or fail 

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
      print(f"Folder '{sample}' not found. Skipping...")
      continue

    # specifying paths for AVLN, GPP, and INGPP
    avln_path = os.path.join(dir_path, 'AVLN_yearly_eq.nc')
    gpp_path = os.path.join(dir_path, 'GPP_yearly_eq.nc')
    ingpp_path = os.path.join(dir_path, 'INGPP_yearly_eq.nc')

    # catch if output variables do not exist
    if not (os.path.exists(avln_path) and os.path.exists(gpp_path) and os.path.exists(ingpp_path)):
      print(f"Data files not found for '{sample}'. Skipping...")
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
    plt.title(f"mean AVLN for passes: {np.round(n_check[n_check['result']!=False]['avln'].mean(), 4)}")
  else:
    plt.title(f"mean AVLN: {np.round(n_check['avln'].mean(), 4)}")
  
  if save:
    plt.savefig(saveprefix + "_n-check-barplot.png", bbox_inches='tight')

  return n_check, counts

def calc_combined_score(results, targets):
  '''Calculate a combination score using r^2, and normalized mse and mape.'''

  r2, rmse, mape, re = calc_metrics(results, targets)

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

def prep_mads_paramkey(params, fmt=None):
  '''
  Gives you something like this:

  .. code::

    mads_paramkey:
      - cmax_pft0
      - cmax_pft1
      - # cmax_pft2

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
  s = 'mads_paramkey:\n'
  for MIN, MAX, comment in ranges:
    if fmt:
      s_tmp = f'- {comment}\n'
      s += s_tmp.format(comment=comment)
    else:
      s += f'- {comment}\n'

  return s

def prep_SA_pbounds(params, fmt=None):
  '''
  Gives you something like this:

  .. code::

    p_bounds: [[],[0.1,500],[0.1,500],[0.1,500],[0.1,500]]

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
  s = 'pbounds: ['
  for MIN, MAX, comment in ranges:
    if fmt:
      s_tmp = "[{MIN:" + f'{fmt}' + '}, {MAX:' + f'{fmt}' + '}],\n'
      s += s_tmp.format(MIN=MIN, MAX=MAX, comment=comment)
    else:
      s += f"[{MIN:8.3f},{MAX:8.3f}],\n"
  #remove extra comma
  s = s[:-3]
  s += ']'

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
  r2, rmse, mape, re = calc_metrics(results, targets)
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

def ecosystem_sum(results, targets):
  '''
  Calculates summed results and targets for the ecosystem (i.e. vegetation / soils)
  allowing for overall comparison of carbon fluxes and stocks independent of pft
  and compartment performance.

  Example usage: results_sum, targets_sum = ecosystem_sum(results, targets)

  Parameters
  ==========
  results : pandas.DataFrame
    One column for each output variable, one row for each sample run.

  targets : pandas.DataFrame
    One column for each output (target) variable, single row with target value.

  Returns
  -------
  results_sum : pandas.DataFrame
    One column for each output variable summed across pfts compartments and soils,
    one row for each sample run.

  targets_sum : pandas.DataFrame
    One column for each target variable summed across pfts compartments and soils, 
    single row with target value.
  '''
  grouped_variables = list(np.unique([i.split('_')[0] for i in targets.columns]))
  
  if all(x in grouped_variables for x in ['DEEPC','MINEC','SHLWC']):
    grouped_variables.remove('DEEPC');grouped_variables.remove('MINEC');grouped_variables.remove('SHLWC')
    grouped_variables.append('SOILC')
  
  targets_sum = pd.DataFrame(columns = grouped_variables)
  results_sum = pd.DataFrame(columns = grouped_variables)
  
  for var in grouped_variables:

    fig, ax = plt.subplots()
    
    if var == 'SOILC':
      results_sum[var] = results.filter(regex='SHLWC').sum(axis=1)+results.filter(regex='DEEPC').sum(axis=1)+results.filter(regex='MINEC').sum(axis=1)
      targets_sum[var] = targets.filter(regex='SHLWC').sum(axis=1)+targets.filter(regex='DEEPC').sum(axis=1)+targets.filter(regex='MINEC').sum(axis=1)
    else:
      results_sum[var] = results.filter(regex=var).sum(axis=1)
      targets_sum[var] = targets.filter(regex=var).sum(axis=1)

    ax.scatter(np.linspace(0, len(results_sum), len(results_sum)), results_sum[var])
    ax.plot(np.linspace(0, len(results_sum), len(results_sum)), targets_sum[var].values[0]*np.ones(len(results_sum[var])), 'k--')
    ax.set_ylabel(var);ax.set_xlabel('Sample index')

  return results_sum, targets_sum

def plot_equilibrium_relationships(path='', sum_pftpart=False, save=False, saveprefix=''):
  '''
  Plots equilibrium timeseries for target variables in output directory
  
  Parameters
  ==========
  path : str
    specifies path to sensitivity sample run directory
  sumpftpart : bool
    flag whether to sum results and targets across compartments
    to compare pft totals
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
      fig, ax = plt.subplots(constrained_layout=True, figsize=(6.4,4.8))
    if len(targ_var_info[0]) == 2:
      width = 6.4 + ((12-6.4)/6) * (len(targ_var_info) - 5)
      fig, ax = plt.subplots(1, len(targ_var_info),constrained_layout=True, figsize=(width,4.8))
    if len(targ_var_info[0]) == 3:
      width = 6.4 + ((12-6.4)/6) * (len(np.unique(np.asarray(targ_var_info)[:,1])) - 5)
      if sum_pftpart==False:
        fig, ax = plt.subplots(3, len(np.unique(np.asarray(targ_var_info)[:,1])),constrained_layout=True,
         figsize=(width,4.8))
      elif sum_pftpart:
        fig, ax = plt.subplots(1, len(np.unique(np.asarray(targ_var_info)[:,1])),constrained_layout=True, 
        figsize=(width,4.8))

    # filtering for directories containing the name sample - SA
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

        if save:
          plt.savefig(saveprefix + f"{targ}_eq_rel_plot.png", bbox_inches='tight')
          
      # pft no compartment    
      if len(targ_var_info[0]) == 2:
        
        for p in targ_var_info:

          pft = int(p[1].split('pft')[1])

          # catch if there is only a single variable for axis indexing
          if len(targ_var_info)<2:
            ax.plot(output[:,pft,0,0], f'C{pft}', alpha=0.5)    
            ax.set_title(f"PFT{pft}")
            ax.plot(np.linspace(0, len(output[:,pft,0,0]), len(output[:,pft,0,0])), 
                  targets[p[0]+'_'+p[1]].values[0]*np.ones(len(output[:,pft,0,0])), 'k--', alpha=0.5)
          else:           
            ax[pft].plot(output[:,pft,0,0], f'C{pft}', alpha=0.5)    
            ax[pft].set_title(f"PFT{pft}")
            ax[pft].plot(np.linspace(0, len(output[:,pft,0,0]), len(output[:,pft,0,0])), 
                  targets[p[0]+'_'+p[1]].values[0]*np.ones(len(output[:,pft,0,0])), 'k--', alpha=0.5)

        fig.supxlabel("Equilibrium years", fontsize=12)
        fig.supylabel(f"{targ}", fontsize=12)

        if save:
          plt.savefig(saveprefix + f"{targ}_eq_rel_plot.png", bbox_inches='tight')
          
      # pft and compartment
      if len(targ_var_info[0]) == 3:

        if sum_pftpart==False:

          for p in targ_var_info:
  
            pft = int(p[1].split('pft')[1])
  
            comp = p[2]; comp_index = comp_ref.index(comp)
          
            # catch if there is only a single variable for axis indexing
            if len(targ_var_info)<2:      
              ax[comp_index].plot(output[:,comp_index,pft,0,0], f'C{pft}', alpha=0.5)
              ax[0].set_title(f"PFT{pft}")
              ax[comp_index].plot(np.linspace(0, len(output[:,comp_index,pft,0,0]), len(output[:, comp_index,pft,0,0])), 
                    targets[p[0]+'_'+p[1]+'_'+p[2]].values[0]*np.ones(len(output[:,comp_index,pft,0,0])), 'k--', alpha=0.5)
            else:
              ax[comp_index, pft].plot(output[:,comp_index,pft,0,0], f'C{pft}', alpha=0.5)
              ax[0, pft].set_title(f"PFT{pft}")
              ax[comp_index, pft].plot(np.linspace(0, len(output[:,comp_index,pft,0,0]), len(output[:, comp_index,pft,0,0])), 
                    targets[p[0]+'_'+p[1]+'_'+p[2]].values[0]*np.ones(len(output[:,comp_index,pft,0,0])), 'k--', alpha=0.5)
  
            ax[0, 0].set_ylabel("Leaf")
            ax[1, 0].set_ylabel("Stem")
            ax[2, 0].set_ylabel("Root")
            fig.supxlabel("Equilibrium years", fontsize=12)
            fig.supylabel(f"{targ}", fontsize=12)

            if save:
              plt.savefig(saveprefix + f"{targ}_eq_rel_plot.png", bbox_inches='tight')

        elif sum_pftpart:

          for p in targ_var_info:

            pft = int(p[1].split('pft')[1])

            target_group = [col for col in targets.columns if f'{targ}_pft{pft}' in col]
            target_value = targets[target_group].sum(axis=1).values[0]
              
            # catch if there is only a single variable for axis indexing
            if len(targ_var_info)<2:      
              ax.plot(np.sum(output[:,:,pft,0,0], axis=1), f'C{pft}', alpha=0.5)
              ax.set_title(f"PFT{pft}")
              ax.plot(np.linspace(0, len(np.sum(output[:,:,pft,0,0], axis=1)), len(np.sum(output[:,:,pft,0,0], axis=1))), 
                    target_value*np.ones(len(np.sum(output[:,:,pft,0,0], axis=1))), 'k--', alpha=0.5)
            else:
              ax[pft].plot(np.sum(output[:,:,pft,0,0], axis=1), f'C{pft}', alpha=0.5)
              ax[pft].set_title(f"PFT{pft}")
              ax[pft].plot(np.linspace(0, len(np.sum(output[:,:,pft,0,0], axis=1)), len(np.sum(output[:,:,pft,0,0], axis=1))), 
                    target_value*np.ones(len(np.sum(output[:,:,pft,0,0], axis=1))), 'k--', alpha=0.5)
  
            fig.supxlabel("Equilibrium years", fontsize=12)
            fig.supylabel(f"{targ}", fontsize=12)

            if save:
              plt.savefig(saveprefix + f"{targ}_eq_rel_plot.png", bbox_inches='tight')

def plot_mads_relationships(targets, path='', sum_pftpart=False, save=False, saveprefix=''):
  '''
  Plots equilibrium timeseries for target variables in mads output directory
  
  Parameters
  ==========
  targets : pandas.DataFrame
    target values (used in sensitivity analysis step) for indexing
    and comparing to final mads optimization
  path : str
    specifies path to mads run directory
  sumpftpart : bool
    flag whether to sum results and targets across compartments
    to compare pft totals
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
      fig, ax = plt.subplots(constrained_layout=True, figsize=(6.4,4.8))
    if len(targ_var_info[0]) == 2:
      width = 6.4 + ((12-6.4)/6) * (len(targ_var_info) - 5)
      fig, ax = plt.subplots(1, len(targ_var_info),constrained_layout=True, figsize=(width,4.8))
    if len(targ_var_info[0]) == 3:
      width = 6.4 + ((12-6.4)/6) * (len(np.unique(np.asarray(targ_var_info)[:,1])) - 5)
      if sum_pftpart==False:
        fig, ax = plt.subplots(3, len(np.unique(np.asarray(targ_var_info)[:,1])),constrained_layout=True,
         figsize=(width,4.8))
      elif sum_pftpart:
        fig, ax = plt.subplots(1, len(np.unique(np.asarray(targ_var_info)[:,1])),constrained_layout=True, 
        figsize=(width,4.8))

    # There should only be an output folder in this case 
    # (adpated from plot_equilibrium_relationships)
    samples = ['']
    
    # looping through sample folders in directory:
    for n, sample in enumerate(samples):

      # reading output variable for each sample
      output = nc.Dataset(path+sample+f'output/{targ}_yearly_eq.nc').variables[targ][:].data

      # selecting variable dimensions based on whether pft, compartment is expected 
      # nopft:
      if len(targ_var_info[0]) == 1:
        ax.plot(output[:,0,0], 'gray', alpha=0.5)
        ax.plot(np.linspace(0, len(output[:,0,0]), len(output[:,0,0])), 
                          targets[targ].values[0]*np.ones(len(output[:,0,0])), 'k--', alpha=0.5)
          
        fig.supxlabel("Equilibrium years", fontsize=12)
        fig.supylabel(f"{targ}", fontsize=12)

        if save:
          plt.savefig(saveprefix + f"{targ}_mads_rel_plot.png", bbox_inches='tight')
          
      # pft no compartment    
      if len(targ_var_info[0]) == 2:
        
        for p in targ_var_info:

          pft = int(p[1].split('pft')[1])

          # catch if there is only a single variable for axis indexing
          if len(targ_var_info)<2:
            ax.plot(output[:,pft,0,0], f'C{pft}', alpha=0.5)    
            ax.set_title(f"PFT{pft}")
            ax.plot(np.linspace(0, len(output[:,pft,0,0]), len(output[:,pft,0,0])), 
                  targets[p[0]+'_'+p[1]].values[0]*np.ones(len(output[:,pft,0,0])), 'k--', alpha=0.5)
          else:           
            ax[pft].plot(output[:,pft,0,0], f'C{pft}', alpha=0.5)    
            ax[pft].set_title(f"PFT{pft}")
            ax[pft].plot(np.linspace(0, len(output[:,pft,0,0]), len(output[:,pft,0,0])), 
                  targets[p[0]+'_'+p[1]].values[0]*np.ones(len(output[:,pft,0,0])), 'k--', alpha=0.5)

        fig.supxlabel("Equilibrium years", fontsize=12)
        fig.supylabel(f"{targ}", fontsize=12)

        if save:
          plt.savefig(saveprefix + f"{targ}_mads_rel_plot.png", bbox_inches='tight')
          
      # pft and compartment
      if len(targ_var_info[0]) == 3:

        if sum_pftpart==False:

          for p in targ_var_info:
  
            pft = int(p[1].split('pft')[1])
  
            comp = p[2]; comp_index = comp_ref.index(comp)
          
            # catch if there is only a single variable for axis indexing
            if len(targ_var_info)<2:      
              ax[comp_index].plot(output[:,comp_index,pft,0,0], f'C{pft}', alpha=0.5)
              ax[0].set_title(f"PFT{pft}")
              ax[comp_index].plot(np.linspace(0, len(output[:,comp_index,pft,0,0]), len(output[:, comp_index,pft,0,0])), 
                    targets[p[0]+'_'+p[1]+'_'+p[2]].values[0]*np.ones(len(output[:,comp_index,pft,0,0])), 'k--', alpha=0.5)
            else:
              ax[comp_index, pft].plot(output[:,comp_index,pft,0,0], f'C{pft}', alpha=0.5)
              ax[0, pft].set_title(f"PFT{pft}")
              ax[comp_index, pft].plot(np.linspace(0, len(output[:,comp_index,pft,0,0]), len(output[:, comp_index,pft,0,0])), 
                    targets[p[0]+'_'+p[1]+'_'+p[2]].values[0]*np.ones(len(output[:,comp_index,pft,0,0])), 'k--', alpha=0.5)
  
            ax[0, 0].set_ylabel("Leaf")
            ax[1, 0].set_ylabel("Stem")
            ax[2, 0].set_ylabel("Root")
            fig.supxlabel("Equilibrium years", fontsize=12)
            fig.supylabel(f"{targ}", fontsize=12)

            if save:
              plt.savefig(saveprefix + f"{targ}_mads_rel_plot.png", bbox_inches='tight')

        elif sum_pftpart:

          for p in targ_var_info:

            pft = int(p[1].split('pft')[1])

            target_group = [col for col in targets.columns if f'{targ}_pft{pft}' in col]
            target_value = targets[target_group].sum(axis=1).values[0]
              
            # catch if there is only a single variable for axis indexing
            if len(targ_var_info)<2:      
              ax.plot(np.sum(output[:,:,pft,0,0], axis=1), f'C{pft}', alpha=0.5)
              ax.set_title(f"PFT{pft}")
              ax.plot(np.linspace(0, len(np.sum(output[:,:,pft,0,0], axis=1)), len(np.sum(output[:,:,pft,0,0], axis=1))), 
                    target_value*np.ones(len(np.sum(output[:,:,pft,0,0], axis=1))), 'k--', alpha=0.5)
            else:
              ax[pft].plot(np.sum(output[:,:,pft,0,0], axis=1), f'C{pft}', alpha=0.5)
              ax[pft].set_title(f"PFT{pft}")
              ax[pft].plot(np.linspace(0, len(np.sum(output[:,:,pft,0,0], axis=1)), len(np.sum(output[:,:,pft,0,0], axis=1))), 
                    target_value*np.ones(len(np.sum(output[:,:,pft,0,0], axis=1))), 'k--', alpha=0.5)
  
            fig.supxlabel("Equilibrium years", fontsize=12)
            fig.supylabel(f"{targ}", fontsize=12)

            if save:
              plt.savefig(saveprefix + f"{targ}_mads_rel_plot.png", bbox_inches='tight')
    

def generate_eq_lim_dict(targets, cv_lim=[0], eps_lim=[0], slope_lim=[0]):
  '''
  Creates a dictionary of thresholds for individual target variables to be
  used for equilibrium checking. Note: limits must match length of targets
  otherwise defaults will be used.

  E.g.
  lim_dict = generate_eq_lim_dict(targets, 
                    cv_lim = [15,15,15,15,15],
                    eps_lim = [1e-5,1e-5,1e-5,1e-5,1e-5],
                    slope_lim = [1e-3,1e-3,1e-3,1e-3,1e-3])
  Parameters
  ==========
  targets : Pandas DataFrame
    observed data for comparison, must match up with equilibrium check directory used
  cv_lim : list
    coefficient of variation threshold as a %, for each variable in targets
  eps_lim : float
    threshold for the difference between means +/- eps_lim*std for the last 30 years 
    and the 30 years prior to this
  slope_lim : float
    slope threshold as a fraction of 30 year mean, for each variable in targets
    
  Returns
    lim_dict : Dict
      individual thresholds to be used in equilibrium_check

  '''
    
  if (len(targets.columns) != len(cv_lim)) or (len(targets.columns) != len(p_lim)) or (len(targets.columns) != len(slope_lim)):
    print('cv_lim, eps_lim, and slope_lim must be lists with the same length as the number of targets')
    print(' DEFAULTS HAVE BEEN USED cv lim = 15%, eps_lim = 1e-5, slope lim = 1e-3')
    cv_lim = np.repeat(1, len(targets.columns)); eps_lim = np.repeat(1e-5, len(targets.columns)); slope_lim = np.repeat(1e-3, len(targets.columns))

  keys = [x + y for x,y in zip(np.repeat(targets.columns.values[:].tolist(), 3), np.tile(['_slope_lim','_eps_lim','_cv_lim'], len(targets.columns.values)))]
  values = []
  for i in range(0, len(targets.columns)):
    values.append(slope_lim[i])
    values.append(eps_lim[i])
    values.append(cv_lim[i])
      
  lim_dict = dict(zip(keys, values))

  return lim_dict

def equilibrium_check(path, cv_lim=1, eps_lim = 1e-5, slope_lim = 1e-3, lim_dict=False, save=False, saveprefix=''):
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
  eps_lim : float
    epsilon - similarly to a numerical convergence criterion -
    threshold as multiple of standard deviations compared against
    difference between the final 30 year average and the 30 year 
    average prior to this +/- standard deviation of the final 30
    years. This is used to evaluate a converging trend by the end of
    the equilibrium stage.
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
  eq_data_columns = [x + y for x,y in zip(np.repeat(targets.columns.values[:].tolist(), 3), np.tile(['_slope','_eps','_cv'], len(targets.columns.values)))]
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
        eps = abs(output[-30:,0,0].mean() - output[-60:-30,0,0].mean())
    
        eq_metrics[targ+f'_slope'].loc[n] = slope
        eq_metrics[targ+f'_eps'].loc[n] = eps
        eq_metrics[targ+f'_cv'].loc[n] = cv

        if lim_dict!=False:
          cv_lim=lim_dict[targ+'_cv_lim']
          eps_lim = lim_dict[targ+'_eps_lim']
          slope_lim = lim_dict[targ+'_slope_lim']

        if slope < slope_lim * output[-30:,0,0].mean()/30:
          eq_data[targ+f'_slope'].loc[n] = True
        if eps <= abs(output[-60:-30,0,0].mean() - output[-90:-60,0,0].mean()) + eps_lim * output[-30:,0,0].std() or output[-30:,0,0].mean()*1e-6: 
        
          eq_data[targ+f'_eps'].loc[n] = True
        if cv < cv_lim:
          eq_data[targ+f'_cv'].loc[n] = True

        if ((eq_data[targ+f'_slope'].loc[n] == True) & 
            (eq_data[targ+f'_eps'].loc[n] == True) & 
            (eq_data[targ+f'_cv'].loc[n] == True)):

          eq_var_check[targ].loc[n] = True
            
      # variable with pft but no compartment
      if len(targ_var_info[0]) == 2:
        
        for p in targ_var_info:

          pft = int(p[1].split('pft')[1])
            
          slope, intercept, r, pval, std_err = scipy.stats.linregress(range(len(output[-30:,pft,0,0])), output[-30:,pft,0,0])
          cv = 100 * output[-30:,pft,0,0].std() / output[-30:,pft,0,0].mean()
          eps = abs(output[-30:,pft,0,0].mean() - output[-60:-30,pft,0,0].mean())

          eq_metrics[targ+f'_pft{pft}_slope'].loc[n] = slope
          eq_metrics[targ+f'_pft{pft}_eps'].loc[n] = eps
          eq_metrics[targ+f'_pft{pft}_cv'].loc[n] = cv

          if lim_dict!=False:
            cv_lim = lim_dict[targ+f'_pft{pft}_cv_lim']
            eps_lim = lim_dict[targ+f'_pft{pft}_eps_lim']
            slope_lim = lim_dict[targ+f'_pft{pft}_slope_lim']

          if slope < slope_lim * output[-30:,pft,0,0].mean()/30:
            eq_data[targ+f'_pft{pft}_slope'].loc[n] = True
          if eps <= abs(output[-60:-30,pft,0,0].mean() - output[-90:-60,pft,0,0].mean()) + eps_lim * output[-30:,pft,0,0].std() or output[-30:,pft,0,0].mean()*1e-6:
            eq_data[targ+f'_pft{pft}_eps'].loc[n] = True
          if cv < cv_lim:
            eq_data[targ+f'_pft{pft}_cv'].loc[n] = True

          if ((eq_data[targ+f'_pft{pft}_slope'].loc[n] == True) & 
              (eq_data[targ+f'_pft{pft}_eps'].loc[n] == True) & 
              (eq_data[targ+f'_pft{pft}_cv'].loc[n] == True)):

            eq_var_check[targ+f'_pft{pft}'].loc[n] = True

      # variable with pfts and compartments
      if len(targ_var_info[0]) == 3:
  
        for p in targ_var_info:
  
          pft = int(p[1].split('pft')[1])
  
          comp = p[2]; comp_index = comp_ref.index(comp)

          slope, intercept, r, pval, std_err = scipy.stats.linregress(range(len(output[-30:,comp_index,pft,0,0])), output[-30:,comp_index,pft,0,0])
          cv = 100 * output[-30:,comp_index,pft,0,0].std() / output[-30:,comp_index,pft,0,0].mean()
          eps = abs(output[-30:,comp_index,pft,0,0].mean() - output[-60:-30,comp_index,pft,0,0].mean())

          eq_metrics[targ+f'_pft{pft}_{comp}_slope'].loc[n] = slope
          eq_metrics[targ+f'_pft{pft}_{comp}_eps'].loc[n] = eps
          eq_metrics[targ+f'_pft{pft}_{comp}_cv'].loc[n] = cv

          if lim_dict!=False:
            cv_lim=lim_dict[targ+f'_pft{pft}_{comp}_cv_lim']
            eps_lim = lim_dict[targ+f'_pft{pft}_{comp}_eps_lim']
            slope_lim = lim_dict[targ+f'_pft{pft}_{comp}_slope_lim']

          if slope < slope_lim * output[-30:,comp_index,pft,0,0].mean()/30:
            eq_data[targ+f'_pft{pft}_{comp}_slope'].loc[n] = True
          if eps <= abs(output[-60:-30,comp_index,pft,0,0].mean() - output[-90:-60,comp_index,pft,0,0].mean()) + eps_lim * output[-30:,comp_index,pft,0,0].std() or output[-30:, comp_index,pft,0,0].mean()*1e-6:
            eq_data[targ+f'_pft{pft}_{comp}_eps'].loc[n] = True
          if cv < cv_lim:
            eq_data[targ+f'_pft{pft}_{comp}_cv'].loc[n] = True

          if ((eq_data[targ+f'_pft{pft}_{comp}_slope'].loc[n] == True) & 
              (eq_data[targ+f'_pft{pft}_{comp}_eps'].loc[n] == True) & 
              (eq_data[targ+f'_pft{pft}_{comp}_cv'].loc[n] == True)):

            eq_var_check[targ+f'_pft{pft}_{comp}'].loc[n] = True

    if eq_var_check.iloc[n, :].all() == True:
      eq_check.loc[n] = True
  
  counts = eq_var_check.apply(pd.value_counts).replace(np.nan, 0.0)
  total_counts = eq_check.apply(pd.value_counts).replace(np.nan, 0.0)
  
  # add catch for only True / only False:
  if len(counts.index)==1:
    if counts.index==False:
      counts = pd.DataFrame(index=['pass', 'fail'], columns=targets.columns, data=[np.zeros(len(counts.columns)), counts.iloc[0,:]])
    elif counts.index==True:
      counts = pd.DataFrame(index=['pass', 'fail'], columns=targets.columns, data=[counts.iloc[0,:],np.zeros(len(counts.columns))])
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
      total_counts = pd.DataFrame(index=['pass', 'fail'], columns=['result'], data=[0.0, total_counts.iloc[0,:].values[0]])
    elif total_counts.index==True:
      total_counts = pd.DataFrame(index=['pass', 'fail'], columns=['result'], data=[total_counts.iloc[0,:].values[0], 0.0])
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
        "eps_lim": eps_lim,
        "slope_lim":slope_lim
    }

  return total_counts, counts, eq_check, eq_var_check, eq_data, eq_metrics, lim_dict

def gpp_vegc_mortality_check(path='', save=False, saveprefix='', targets=None):
  '''
  Checks whether PFTs are dying based on VEGC and GPP values over the last ten years of the run.

  Parameters
  ==========
  path : str
      Specifies path to sensitivity sample run directory
  save : bool, optional
      Whether to save the generated plot, by default False
  saveprefix : str, optional
      Prefix to add to the saved plot filename, by default ''
  targets : str or Pandas DataFrame, optional
      Path to the target CSV file or the DataFrame containing the target values, by default None

  Returns
  =======
  DataFrame:
      A DataFrame containing the results of the PFT mortality check.
  '''

  samples = np.sort([name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name)) and "sample" in name])

  if len(samples) < 1:
    print("No sample directories found.")
    return

  if isinstance(targets, str):  # Load the targets DataFrame if path is provided
    targets_path = os.path.join(path, targets)
    if os.path.exists(targets_path):
      targets = pd.read_csv(targets_path, header=1)  # Load CSV without header
    else:
      print(f"Targets file '{targets_path}' not found. Skipping...")

  if targets is None:
    print("Targets DataFrame is not provided. Skipping...")
    return

  # Determine the number of PFTs dynamically from the provided data
  num_pfts = len(set(col.split('_')[1] for col in targets.columns if 'VEGC_pft' in col))
  
  # Create DataFrame with columns for each PFT
  pft_columns = [f'{variable}_PFT_{pft}_result' for variable in ['VEGC', 'GPP'] for pft in range(num_pfts)]
  pft_check = pd.DataFrame(index=range(len(samples)), columns=['sample'] + pft_columns)
  pft_check['sample'] = samples  # Fill sample column with sample names

  # Initialize result columns to False
  for col in pft_columns:
    pft_check[col] = False
  
  # Plotting code here
  fig, ax = plt.subplots(2, num_pfts, figsize=(num_pfts * 5, 10), sharex=True)
  
  for j in range(num_pfts):  # Iterate over PFTs
    for k, variable in enumerate(['VEGC', 'GPP']):  # Iterate over VEGC and GPP
      for i, sample in enumerate(samples):  # Iterate over samples
        dir_path = os.path.join(path, sample, 'output')
        data_path = os.path.join(dir_path, f'{variable}_yearly_eq.nc')

        if not os.path.exists(data_path):
          print(f"Data file not found for '{sample}'. Skipping...")
          continue

        data = nc.Dataset(data_path).variables[variable][:].data[:, :, :]

        # Check if variable contains 'pftpart' dimension
        if 'pftpart' in nc.Dataset(data_path).variables[variable].dimensions:
          # Sum across pftpart dimension
          data = np.sum(data, axis=1)

        data_pft_flat = data[:, j].flatten()  # Flatten the array

        if variable == 'GPP':
          # Check if GPP is greater than 0 for the last ten years
          result = np.all(data[-10:, j] > 1e-6)
        elif variable == 'VEGC':
          # Check if VEGC is greater than 0 for the last year only
          result = np.all(data[-1, j] > 1e-6)

        ax[k, j].plot(np.arange(len(data_pft_flat)), data_pft_flat, label=f'Sample {sample}', alpha=0.7)
        ax[k, j].set_ylabel(variable)
        
        # Assign result to DataFrame
        pft_check.loc[pft_check['sample'] == sample, f'{variable}_PFT_{j}_result'] = result
        
        # Calculate percentage of samples passing the test
        pass_percent = pft_check[f'{variable}_PFT_{j}_result'].sum() / len(pft_check) * 100
        # Add the percentage in the title of each subplot
        ax[k, j].set_title(f'PFT {j} - {variable}\nPass Rate: {pass_percent:.2f}%')

  # Add the 'Result' column
  pft_check['result'] = pft_check.iloc[:, 1:].all(axis=1)

  plt.xlabel('Time')
  plt.tight_layout()

  if save:
    plt.savefig(saveprefix + "pft-mortality-check.png", bbox_inches='tight')

  return pft_check

def vegc_mortality_check(path='', save=False, targets=None, saveprefix=''):
  '''
  Checks whether PFTs are dying based on VEGC values over the last year of the run.
  Note: this requires VEGC to be produced from the calibration step. 
  To access the dataframe with the final 'result' column to then use in addition to subsequent post calibration checks print:

  >> vegc_check_result = vegc_mortality_check(path='', save=False, targets='targets.csv', saveprefix='')
  Now you can access the DataFrame outside of the function
  >> dataframe = vegc_check_result

  Parameters
  ==========
  path : str
      Specifies path to sensitivity sample run directory
  save : bool, optional
      Whether to save the generated plot, by default False
  targets : str or Pandas DataFrame, optional
      Path to the target CSV file or the DataFrame containing the target values, by default None
  saveprefix : str, optional
      Prefix to add to the saved plot filename, by default ''

  Returns
  =======
  DataFrame:
      A DataFrame containing the results of the VEGC mortality check.
  '''

  samples = np.sort([name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name)) and "sample" in name])

  if len(samples) < 1:
    print("No sample directories found.")
    return

  vegc_check = pd.DataFrame(index=range(len(samples)), columns=['Sample'])
  vegc_check['Sample'] = samples  # Add sample numbers to the DataFrame

  # Load the target DataFrame if path is provided
  if isinstance(targets, str):
    targets_path = os.path.join(path, targets)
    if os.path.exists(targets_path):
      targets = pd.read_csv(targets_path, header=1)  # Load CSV without header
    else:
      print(f"Targets file '{targets_path}' not found. Skipping...")

  if targets is None:
    print("Targets DataFrame is not provided. Skipping...")
    return

  # Determine the number of PFTs and PFT parts dynamically from the provided data
  pft_parts = {'Leaf': 0, 'Stem': 1, 'Root': 2}
  num_pfts = len(set(col.split('_')[1] for col in targets.columns if 'VEGC_pft' in col))
  num_pftparts = len(pft_parts)

  fig, axes = plt.subplots(num_pfts, num_pftparts, figsize=(5*num_pftparts, 3*num_pfts))  # Create a grid of subplots
  axes = axes.flatten()  # Flatten the 2D array of axes into a 1D array

  for col in targets.columns:
    if 'VEGC' in col:
      pft_idx = int(col.split('_')[1].replace('pft', ''))
      pftpart_str = col.split('_')[2]
      if pftpart_str not in pft_parts:
        print(f"Unknown PFTPART: {pftpart_str}. Skipping...")
        continue
      pftpart_idx = pft_parts[pftpart_str]

      for i, sample in enumerate(samples):
        dir_path = os.path.join(path, sample, 'output')
        data_path = os.path.join(dir_path, 'VEGC_yearly_eq.nc')

        if not os.path.exists(data_path):
          print(f"Data file not found for '{sample}'. Skipping...")
          continue

        data = nc.Dataset(data_path).variables['VEGC'][:].data
        try:
          last_year_value = data[-1, pftpart_idx, pft_idx, 0, 0]
        except IndexError:
          last_year_value = np.nan  # Set to NaN if index error occurs

        ax = axes[pft_idx * num_pftparts + pftpart_idx]  # Select the appropriate subplot
        ax.plot(np.arange(len(data)), data[:, pftpart_idx, pft_idx, 0, 0],
                label=f'Sample {sample}', alpha=0.7)
        ax.set_ylabel('VEGC')

        if not np.isnan(last_year_value) and last_year_value > 1e-6:
          vegc_check.at[i, col] = True  # Update with True if VEGC > 0
        elif np.isnan(last_year_value):
          vegc_check.at[i, col] = np.nan  # Set to NaN if value is NaN
        else:
          vegc_check.at[i, col] = False  # Update with False if VEGC <= 0

      pass_percent = np.nanmean(vegc_check[col]) * 100
      axes[pft_idx * num_pftparts + pftpart_idx].set_title(f'PFT {pft_idx} - PFTPART {pftpart_idx}\nPass Rate: {pass_percent:.2f}%')

  # Add the 'Result' column
  vegc_check['result'] = vegc_check.iloc[:, 1:].all(axis=1)
  
  # Check if the last value of the dataset time series is less than or equal to 0
  vegc_check['result'] = np.where(vegc_check['result'] & (last_year_value <= 0), False, vegc_check['result'])

  plt.xlabel('Time')
  plt.tight_layout()

  if save:
    plt.savefig(f"{saveprefix}vegc-mortality-check.png", bbox_inches='tight')

  return vegc_check

def total_mortality_check(path='', save=False, targets=None, saveprefix=''):
  '''
  Checks whether PFTs are considered alive based on VEGC values for the last year and GPP values for the last ten years.
  
  Note: this requires both output variables VEGC and GPP to be produced from the calibration step. If one of the outputs is missing, a print
  statement will be produced printing which output, and for which sample it is missing. The check will default to Fail,as both outputs are needed.
  To access the dataframe with the final 'result' column to then use in addition to subsequent post calibration checks print:

  >> pft_check_result = pft_survival_check2(path='', save=False, targets='targets.csv', saveprefix='')
  Now you can access the DataFrame outside of the function
  >> dataframe = pft_check_result

  Parameters
  ==========
  path : str
      Specifies path to sensitivity sample run directory
  save : bool, optional
      Whether to save the generated plot, by default False
  targets : str or Pandas DataFrame, optional
      Path to the target CSV file or the DataFrame containing the target values, by default None
  saveprefix : str, optional
      Prefix to add to the saved plot filename, by default ''

  Returns
  =======
  DataFrame:
      A DataFrame containing the results of the PFT survival check.
  '''

  samples = np.sort([name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name)) and "sample" in name])

  if len(samples) < 1:
    print("No sample directories found.")
    return

  num_samples = len(samples)

  if isinstance(targets, str):
    targets_path = os.path.join(path, targets)
    if os.path.exists(targets_path):
      targets = pd.read_csv(targets_path, header=1)  # Load CSV without header
    else:
      print(f"Targets file '{targets_path}' not found. Skipping...")
      return
  elif not isinstance(targets, pd.DataFrame):
    print("Invalid targets parameter. Please provide a path to a CSV file or a DataFrame.")
    return

  pft_check = pd.DataFrame(index=range(num_samples), columns=['sample'])  # Initialize DataFrame with sample column
  pft_check['sample'] = samples  # Fill in the sample column with the sample names

  unique_pfts = set()  # Keep track of unique PFTs
  
  fig, ax = plt.subplots(2, len(targets.columns), figsize=(len(targets.columns) * 5, 10), sharex=True)
  
  plot_count = 0  # Initialize plot counter
  
  for j, pft_col in enumerate(targets.columns):  # Iterate over PFTs
    if not pft_col.startswith('VEGC_pft'):
      continue  # Skip columns that are not PFT-specific

    pft_idx = int(pft_col.split('_')[1].replace('pft', ''))

    # Skip if PFT has already been processed
    if pft_idx in unique_pfts:
      # print(f"Skipping duplicate PFT {pft_idx}.")
      continue
    else:
      unique_pfts.add(pft_idx)

    pass_stat_vegc = ''  # Initialize pass statement for VEGC
    pass_stat_gpp = ''  # Initialize pass statement for GPP
    pass_rate_vegc = 0  # Initialize pass rate for VEGC
    pass_rate_gpp = 0  # Initialize pass rate for GPP
    
    for k, variable in enumerate(['VEGC', 'GPP']):  # Iterate over VEGC and GPP
      
      pass_count = 0  # Initialize pass count
      
      for i, sample in enumerate(samples):  # Iterate over samples

        dir_path = os.path.join(path, sample, 'output')

        if not os.path.exists(dir_path):
          print(f"Folder '{sample}' not found. Skipping...")
          continue

        data_path = os.path.join(dir_path, f'{variable}_yearly_eq.nc')

        if not os.path.exists(data_path):
          print(f"Data file not found for variable '{variable}' in sample '{sample}'. Skipping...")
          continue

        data = nc.Dataset(data_path).variables[variable][:].data[:, :, :]

        # Check if variable contains 'pftpart' dimension
        if 'pftpart' in nc.Dataset(data_path).variables[variable].dimensions:
          # Sum across pftpart dimension
          data = np.sum(data, axis=1)

        data_pft_flat = data[:, pft_idx].flatten()  # Flatten the array

        if variable == 'GPP':
          # Check if GPP is greater than 0 for the last ten years
          pass_gpp = np.all(data[-10:, pft_idx] > 0)
          if pass_gpp:
            pass_count += 1
        elif variable == 'VEGC':
          # Check if VEGC is greater than 0 for the last year only
          pass_vegc = np.all(data[-1, pft_idx] > 0)
          if pass_vegc:
            pass_count += 1

        ax[k, plot_count].plot(np.arange(len(data_pft_flat)), data_pft_flat, label=f'Sample {sample}', alpha=0.7)
        ax[k, plot_count].set_ylabel(variable)
        
      # Calculate percentage of samples passing the test for VEGC and GPP separately
      pass_rate = pass_count / num_samples
      if variable == 'VEGC':
        pass_rate_vegc = pass_rate
        pass_stat_vegc = f'{pass_rate * 100:.2f}% samples > 0 for VEGC' if pass_rate >= 0.7 else 'failed for VEGC'
      elif variable == 'GPP':
        pass_rate_gpp = pass_rate
        pass_stat_gpp = f'{pass_rate * 100:.2f}% samples > 0 for GPP' if pass_rate >= 0.7 else 'failed for GPP'

    # Check if both VEGC and GPP pass the test
    pass_stat = 'pass' if pass_rate_vegc >= .7 and pass_rate_gpp >= .7 else 'fail'
    ax[0, plot_count].set_title(f'PFT {pft_idx}: VEGC and GPP: {pass_stat}\n % Passed: VEGC - {pass_rate_vegc*100:.2f}%\n % Passed: GPP - {pass_rate_gpp*100:.2f}%')
    ax[0, plot_count].set_xlabel('Time', fontsize=10)

    plot_count += 1  # Increment plot counter

    # Update the corresponding PFT column in the DataFrame
    pft_col = f'VEGC/GPP_pft{pft_idx}'
    pft_check[pft_col] = pass_stat == 'pass'

  # Remove empty subplots
  for i in range(plot_count, len(ax.flatten())):
    fig.delaxes(ax.flatten()[i])

  # Add a "result" column to the DataFrame
  pft_check['result'] = pft_check.iloc[:, 1:].all(axis=1)

  plt.xlabel('Time', fontsize=10)
  plt.tight_layout()

  if save:
    plt.savefig(saveprefix + "pft-survival-check.png", bbox_inches='tight')

  return pft_check

def get_filtered_results(results, sample_matrix, check_filter):
  """
  Filter results and sample matrix by check (I.e. equilibrium,
  nitrogen, mortality)

  E.g. results_f, sample_matrix_f = get_filtered_results(results, sample_matrix, eq_check['result']) 

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

  Returns
  -------
  results_eq, sample_matrix_eq

  """
  return results[check_filter==True], sample_matrix[check_filter==True]

def get_max_parameter_ranges(parameter, path='/work/parameters/'):
  '''
  Return the minimum and maximum ranges for a given parameter

  Parameters
  ----------
  parameter: string
    parameter name

  path: string
    path to parameter file directory

  Returns
  -------
  '''
  import sys
  sys.path.insert(0, '/work/scripts')
  import util.param as pa
  psh = pa.ParamUtilSpeedHelper(path)
  non_pft_params = psh.list_non_pft_params()
  param_vals = []; cmt_nums = []
  for cmt in pa.get_CMTs_in_file(path+'cmt_calparbgc.txt'):
    cmt_nums.append(cmt['cmtnum'])
    if parameter in non_pft_params:
      param_vals.append(psh.get_value(pname=parameter,cmtnum=cmt['cmtnum'],pftnum=None))
    else:
      for pft in range(0, 9):
        pft_param = psh.get_value(pname=parameter,cmtnum=cmt['cmtnum'],pftnum=str(pft))
        if pft_param != 0.0:
          param_vals.append(pft_param)
  print(f'Range of {parameter} across CMTs: {min(param_vals)} - {max(param_vals)}')
  return

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