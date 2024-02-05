import csv
import os
import numpy as np
from sklearn.cluster import KMeans
from scipy.optimize import curve_fit
from matplotlib import pyplot as plt
import pandas as pd
import statistics as stat
import math
#-------------------------------FUNCTIONS TO LOAD CSV FILES----------------------------------------------------

#OUTDATED, function is kept for use in old code, please use read_all_csv
def read_csv_model(filename):
  """
  read model data from a single csv file

  Parameters: filenames: file name to be read

  Returns: dict: {'obs_id':[model values]}
  """
  mod={}
  with open(filename, 'r') as file:
      reader = csv.reader(file)
      r=1
      for row in reader:
          vals=[]
          if r==1:
            r=r+1
          else:
            for nn in row[1:]:
              vals.append(nn)
            mod[row[0]]=vals
  return mod

#OUTDATED, function is kept for use in old code, please use read_all_csv
def read_csv_params(filename):
  """
  read param data from single param csv file

  Parameters: filenames: file name to be read

  Returns: dict: {'param':[optimal param values]}
  """
  mod={}
  with open(path+filename, 'r') as file:
      reader = csv.reader(file)
      r=1
      for row in reader:
          vals=[]
          if r==1:
            r=r+1
          else:
            for nn in row[5:]:
              vals.append(nn)
              vals=[float(x) for x in vals]
            mod[row[0]]=vals
  return mod

#OUTDATED, function is kept for use in old code. Please use read_all_csv_errors
def read_csv_errors(path, filenames):
  """
  read error data from single param csv file

  Parameters: filenames: file name to be read

  Returns: list of errors as strings
  """
  with open(path+filename, 'r') as file:
      reader = csv.reader(file)
      r=1
      for row in reader:
        if r==1:
          r=r+1
          vals=row[4:]
      #remove 'OF:' left over from iteration files
      for nn in range(0,len(vals)):
        vals[nn]=vals[nn].replace("OF:", "")
        vals[nn]=vals[nn].replace("_1", "")
        vals[nn]=vals[nn].replace("_2", "")
        vals[nn]=vals[nn].replace("_3", "") 
  return vals

def read_all_csv_errors(path, filenames):
  """
  Reads multiple parameter CSV files to get error for each calibration run

  Parameters:
  path (str): Path of the folder where CSV files are located
  filenames (list): List of file names to be read

  Returns:
  pandas.DataFrame: A list of final errors, in order of the files read
  """
  dfs_err = []
  for file_name in filenames:
    with open(path+file_name, 'r') as file:
        reader = csv.reader(file)
        r=1
        for row in reader:
          if r==1:
            r=r+1
            index = [i for i, col in enumerate(row) if 'OF' in col][0]
          vals=row[index:]
        #remove 'OF:' left over from iteration files
        for nn in range(0,len(vals)):
          vals[nn]=vals[nn].replace("OF:", "")
          vals[nn]=vals[nn].replace("_1", "")
          vals[nn]=vals[nn].replace("_2", "")
          vals[nn]=vals[nn].replace("_3", "") 
    dfs_err=dfs_err+vals
  return dfs_err

def read_all_csv(folder_path, filenames, type, columns):
  """
  Reads multiple parameter CSV or model CSV files and return dataframe

  Parameters:
  type: 'params' for parameter file, 'model' for model file
  folder_path (str): Path of the folder where CSV files are located
  filenames (list): List of file names to be read

  Returns:
  pandas.DataFrame: A concatenated DataFrame containing all optimal parameter sets or model results
  """
  dfs = [] 

  # Read first file with all columns
  file_path = os.path.join(folder_path, filenames[0])
  if os.path.isfile(file_path) and filenames[0].endswith('.csv'):
    df = pd.read_csv(file_path, names=columns)
    dfs.append(df)
  else:
    print(' '+filenames[0]+' was not found. Continuing without reading file, Check spelling and folder...')

  #find idex of first results column
  if type=='params':
    #to concatenate dataframes (col idx:end are optimal params)
    results = 'OF'
    #creates mask of all columns who's header contain "OF" (ie; results)
    mask = df.columns.str.contains(results)
    if mask.any():
      idx = mask.argmax() #index of first column of results
    else:
      raise ValueError(f"No columns contain the substring '{results}'")
  elif type=='model':
    #to concatenate dataframes (col idx:end are model results)
    #double check if extra obs ID column exists
    if (('parameters' or 'obs_id') in df.columns) and type=='model':
      idx=2 
    else:
      idx=1    
    
  # Read remaining files with model results only
  if len(filenames)>1:
    for file_name in filenames[1:]:
      file_path = os.path.join(folder_path, file_name)
      if os.path.isfile(file_path) and file_name.endswith('.csv'):
          df = pd.read_csv(file_path) 
          dfs.append(df.iloc[:,idx:])
      else:
        print(' '+file_name+' was not found. Continuing without reading file, Check spelling and folder...')
      concatenated_df = pd.concat(dfs, axis=1)
  else:
    concatenated_df = df
  return concatenated_df

#-------------------------------FUNCTIONS TO LOAD ITERATION FILES (output from MADS)----------------------------------------------

def get_optimal_sets_of_params(filename):
  """
  Reads optimal parameters from final results file 
  #can probably use for interation and initial files too

  Parameters:
  filename (list): List of file name to be read

  Returns:
  dictionary of params (keys) and optimal values found (values). 
  Order matters, optimal paramaters of index 1 for each key belong to the same run
  """
  file_path = os.path.join(filename)
  #we assume there are three lines per calibration - 0=OF, 1=lambda, 2=params
  with open(file_path) as f:
      lines = f.readlines()
  #for multiple optimal sets, need to loop through them all, index starts at 0
  filelength = len(lines)
  num_sets = math.floor(filelength/3) #truncate in case there's an empty extra line at end of file
  for nn in range(1,num_sets+1):
      del lines[(nn-1)] #delete OF line
      del lines[(nn-1)] #delete lambda line
  #remove formatting from iteration files
  for nn in range(0,num_sets):
      lines[nn]=lines[nn].replace("OrderedCollections.OrderedDict", "") 
      lines[nn]=lines[nn].replace(" ", "")
      lines[nn]=lines[nn].replace("\"", "")
      lines[nn]=lines[nn].replace("\n", "")
      lines[nn]=lines[nn].replace("(", "")
      lines[nn]=lines[nn].replace(")", "")
      lines[nn]= dict(subString.split("=>") for subString in lines[nn].split(","))
  # MERGE OPTIMAL VALUES INTO ONE KEY/VALUE SET IN DICTIONARY:
  #at this point, lines is a set of key:value pairs of optimal sets for each calibration run
  #we combine all runs into one set of keys (params) with multiple optimal value to plot easier:
  params = {}
  for sub in lines:
    for key, val in sub.items(): 
      params.setdefault(key, []).append(round(float(val),8))
  return params

def merge_parameter(p1,p2):
  """
  Merges two parameter dictionaries (from two separate calibration runs) into one
  calibration runs must be targeting  the same quantities, and optimizing the same parameters

  Parameters:
  p1: first dictionary
  p2: second dictionary

  Returns:
  parameter dictionary of all calibration runs
  """
  merge_param = {**p1, **p2}
  for same_key in set(p1) & set(p2):
    merge_param[same_key] = p1[same_key]+p2[same_key]
  return merge_param

def get_all_optimal_sets_of_params(path, filenames):
    """
    Reads optimal parameters from MULTIPLE final results files

    Parameters:
    filenames (list): List of file names to be read

    Returns:
    Dictionary of params (keys) and optimal values found (values). 
    Order matters, optimal parameters of index 1 for each key belong to the same run
    """
    all_params = []
    for filename in filenames:
        file_path = os.path.join(path, filename)
        # we assume there are three lines per calibration - 0=OF, 1=lambda, 2=params
        with open(file_path) as f:
            lines = f.readlines()
        # for multiple optimal sets, need to loop through them all, index starts at 0
        filelength = len(lines)
        num_sets = math.floor(filelength/3) # truncate in case there's an empty extra line at end of file
        for nn in range(1,num_sets+1):
            del lines[(nn-1)] # delete OF line
            del lines[(nn-1)] # delete lambda line
        # remove formatting from iteration files
        for nn in range(0,num_sets):
            lines[nn]=lines[nn].replace("OrderedCollections.OrderedDict", "") 
            lines[nn]=lines[nn].replace(" ", "")
            lines[nn]=lines[nn].replace("\"", "")
            lines[nn]=lines[nn].replace("\n", "")
            lines[nn]=lines[nn].replace("(", "")
            lines[nn]=lines[nn].replace(")", "")
            lines[nn]= dict(subString.split("=>") for subString in lines[nn].split(","))
        all_params.append(lines)

    # merge optimal values into one key/value set in dictionary
    # at this point, all_params is a list of sets of key:value pairs of optimal sets for each calibration run
    # we combine all runs into one set of keys (params) with multiple optimal value to plot easier:
    params = {}
    for sub in all_params:
      for sub in lines:
        for key, val in sub.items(): 
          params.setdefault(key, []).append(round(float(val),2))
    return params

def get_error(path, filenames):
  """
  read in error from final results file

  Parameters: filename

  Returns: list of error from all runs in the file
  """
  all_errors = []
  for filename in filenames:
    file_path = os.path.join(path, filename)
    #again, assumes there are three lines - 0=OF, 1=lambda, 2=params
    with open(file_path) as f:
      errors = f.readlines()
    #for multiple optimal sets, need to loop through them all
    filelength = len(errors)
    num_sets = math.floor(filelength/3) #truncate in case there's an empty extra line at end of file
    for nn in range(1,num_sets+1):
      del errors[(nn)] #delete lambda line
      del errors[(nn)] #delete params line
    for nn in range(0,num_sets):
      errors[nn]=errors[nn].replace("OF:", "") 
      errors[nn]=errors[nn].replace(" ", "")
      errors[nn]=errors[nn].replace("\"", "")
      errors[nn]=errors[nn].replace("\n", "")
    all_errors=all_errors+errors
  return all_errors

#Identification of separate runs does not work well for all cases
def load_sort_itr_err(path,filename):
  """
  read in error from iteration results file and identify separate runs

  Parameters: path - path to file, filename

  Returns: 
  rounded_err_itr - all error rounded
  idx - index at which new run begins
  err_by_run - list of each iterations error grouped by run (in order)
  """
  #load iteration errors:
  e_itr=get_error(path+filename)
  float_err_itr=[float(x) for x in e_itr]
  rounded_err_itr=list(np.round(float_err_itr,7))
  #find jumps in error to identify different calibration runs:
  diff=[t - s for s, t in zip(rounded_err_itr, rounded_err_itr[1:])]
  Q1 = np.percentile(diff, 25, interpolation = 'midpoint')
  Q3 = np.percentile(diff, 75, interpolation = 'midpoint')
  IQR = Q3 - Q1
  upper = np.where(diff >= (Q3+1.5*IQR)) # index of error jumps greater than upper bound of IQR
  #Split iteration file error data into separate calibration runs:
  idx=list(upper[0])
  idx=[x+1 for x in idx] #the upper var is based on differences in error, we need this index +1
  idx.append(len(rounded_err_itr))
  err_by_run=[rounded_err_itr[x:y] for x,y in zip([0]+idx[:-1],idx)]
  return rounded_err_itr,idx,err_by_run

#------------------------------------PLOTTING FUNCTIONS-------------------------------------------------------------

def plot_histograms(params,nbins=10,x=16,y=8,r=2,c=4):
  """
  plot the optimal values

  Parameters: 
  params - dictionary of optimal parameters
  nbins
  x - width of fig
  y - height of fig
  r - number of rows
  c - number of columns

  Returns: histogram
  """
  plt.figure(figsize=(x,y))
  s=1
  for item in params:
    plt.subplot(r,c,s)
    plt.hist(params[item],bins=nbins);
    plt.title(item)
    plt.xlabel('optimal values')
    plt.ylabel('counts')
    s+=1
  return

def get_err_clusters(float_err,n_clusters=4):
  """
  Use Kmeans to cluster errors, clusters in order of magnitude (0-smallest error, 3-largest)

  Parameters: 
  float_err - list of errors converted to floats
  nclusters - number of error clusters, default is 4

  Returns: 
  y_kmeans - index of cluster each error belongs to (list)
  centetrs - (array) center value of each error cluster
  """
  arr=np.array(float_err)
  kmeans = KMeans(n_clusters)
  kmeans.fit(arr.reshape(-1,1))
  y_kmeans = kmeans.predict(arr.reshape(-1,1))
  centers = kmeans.cluster_centers_
  centers = sorted(centers) #do we need this line?
  return y_kmeans, centers

def cluster_param_data(params,y_kmeans):
  """
  Organize parameters values by kmeans clusters

  Parameters: 
  params - dictionary of optimal parameters
  y_kmeans - index of cluster each error belongs to (list)

  Returns: 
  zeroes, twos, ones, threes - list of optimal parameters belonging to each respective error cluster
  """
  zeroes=[]
  ones=[]
  twos=[]
  threes=[]
  for v in range(len(params)):
    if y_kmeans[v]==0:
      zeroes.append(params[v])
    elif y_kmeans[v]==1:
      ones.append(params[v])
    elif y_kmeans[v]==2:
      twos.append(params[v])
    elif y_kmeans[v]==3:
      threes.append(params[v])
  return zeroes, twos, ones, threes

def plot_stacked_histograms(mparams,centers,y_kmeans,nbins=10,x=24,y=10,r=2,c=4,std=0):
  """
  plot the optimal values in a stacked histogram, where stacking color is determined by error cluster

  Parameters: 
  params - dictionary of optimal parameters
  centetrs - (array) center value of each error cluster
  y_kmeans - index of cluster each error belongs to (list)
  nbins
  x - width of fig
  y - height of fig #default is y=5 for each row
  r - number of rows
  c - number of columns
  std - standard deviation. If std of given histogram is less than this value, it will NOT be plotted

  Returns: histogram
  """
  #plot the optimal values, colors stacked by error clusters
  plt.style.use('bmh')
  plt.figure(figsize=(x,y))
  labels=[float(x) for x in centers]
  rounded_labels=list(np.round(labels,4))
  s=1
  for item in mparams:
    if stat.stdev(mparams[item])>std:
      plt.subplot(r,c,s)
      zeroes,ones,twos,threes=cluster_param_data(mparams[item],y_kmeans)
      plt.hist([zeroes,ones,twos,threes], 10, density=False, histtype='bar', stacked=True)
      plt.title(item)
      plt.xlabel('optimal values')
      plt.ylabel('counts')
      plt.tight_layout(pad=3.0)
      s+=1
    else:
      print('Parameter '+item+' has standard deviation('+str(stat.stdev(mparams[item]))+') less than threshold of '+str(std)+'\n')
  centers=np.round(centers,2)
  # plt.legend(['Type I','Type II','Type III','Type IV'], title = "Error", bbox_to_anchor=(1.0, 1.0), loc='upper right')
  plt.legend([str(centers[0]),str(centers[1]),str(centers[2]),str(centers[3])], title = "Error", bbox_to_anchor=(1.0, 1.0), loc='upper right')
  plt.suptitle('Optimal Parameters Classified by Errors')
  return


def plot_err_by_run(err_by_run, idx, x=24, y=8, r=3, c=4, deg=2):
  """
  Plot error results from iteration file in separate subplot for each run. include polynomial fit to data (future)

  Parameters: 
  err_by_run - list of each iterations error grouped by run (in order)
  idx - index for each new calibration run from the iteration files (output of load_sort_itr_err)
  x - width of fig
  y - height of fig 
  r - number of rows
  c - number of columns
  deg - degree of curve to fit. currently not in use

  Returns: figure showing evolution of error over each iteration for each independent run
  """
  #Using split iteration file data, plot error by iteration with polynomial fit(default deg=2):
  plt.style.use('bmh')
  plt.figure(figsize=(x,y))
  s=1
  for i in (range(len(idx))):
    plt.subplot(r,c,s)
    plt.plot(np.log10(err_by_run[i]), label='Iteration Error');
    plt.xlabel('Iteration number')
    plt.ylabel('Error (log scale)')
    plt.title('Calibration run:' + str(i+1))
    # fit polynomial to data on log scale:
    # num_itr=len(err_by_run[i])
    # x_ax=list(range(0,num_itr))
    # y_fit=np.polyfit(x_ax, np.log10(err_by_run[i]), deg)
    # y=np.poly1d(y_fit)
    # x_fit=np.linspace(0,num_itr-1,20)
    # plt.plot(x_fit, y(x_fit),'-', label='Fitted curve')
    plt.tight_layout()
    # plt.legend()
    s+=1
  plt.suptitle('Error Evolution per Iteration for Each Calibration Run')
  return

def plot_err(err, x=8, y=6):
  """
  Plot error results from final results of each calibration run
  Errors are color coded by their associated error cluster

  Parameters: 
  err - list of final errors for each run

  Returns: scatter plot of all final errors
  """
  float_err=[float(x) for x in err]
  y_kmeans,centers=get_err_clusters(float_err)
  plt.figure(figsize=(x,y))
  plt.scatter([i for i in range(len(float_err))], float_err, c=y_kmeans)
  plt.xlabel('Calibration Run')
  plt.ylabel('Error')
  plt.title('Final error for each run')
  return

def match_plot(df_model, target='GPP'):
  """
  plot model-data match results
  Parameters: 
  df_model - dataframe of target and model data (rows correspond to parameters, COLUMNS correspond to one simulation)
  df_params - dataframe of optimal paramaters (currently not used)
  target - (str) targets for the calibration, example: 'VEGC/NPP'
  Returns: plot with 2 figures:
    1 - match-plot for all runs
    2 - log scale match-plot for all runs
  """
  plt.style.use('bmh')
  if ('parameters' or 'obs_id') in df_model.columns:
    idx=1
  else:
    idx=0
  all_data=idx+1
  fig, axes = plt.subplots(nrows=1, ncols=2,figsize=(24,6))
  # plt.tight_layout() #use ax=axes[0] to plot in subplot
  df_model.iloc[:,all_data:].plot(logy=False, xlabel="obs_id", ylabel=target, title="model "+target, style="-", colormap='tab20b', legend=True, ax=axes[0])
  df_model.iloc[:,idx].plot(logy=False, style="-o", color='black', ax=axes[0])

  df_model.iloc[:,all_data:].plot(logy=True, xlabel="obs_id", ylabel=target, title="log-scale model "+target, style="-", colormap='tab20b', legend=True, ax=axes[1])
  df_model.iloc[:,idx].plot(logy=True, style="-o", color='black', ax=axes[1])
  return

# plot_paramsvstarget(df_param,df_model,r2,i=1,xlabel='nmax1',ylabel='NPP')
def plot_paramsvstarget(x,y,r2,i=1,xlabel='nmax1',ylabel='NPP'):
    
    tight_params=x[r2>0.96]
    tight_model=y.iloc[0:-1,:][r2>0.96]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10,5))

    ax1.plot(x.iloc[:,i],y.iloc[0:-1,i],'o',alpha=0.5,color='b')
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(ylabel)
    ax1.set_ylim([min(y.iloc[:,i])-1, max(y.iloc[:,i]+1)])
    x1=min(x.iloc[:,i])
    x2=max(x.iloc[:,i])
    ax1.plot(np.linspace(x1,x2,10),np.ones(10)*y.iloc[-1,i],alpha=0.5,color='black')

    ax2.plot(tight_params.iloc[:,i],tight_model.iloc[:,i],'o',alpha=0.5,color='b')
    ax2.set_xlabel(xlabel)
    ax2.set_title('values associated with r2>.96')
    ax2.plot(np.linspace(x1,x2,10),np.ones(10)*y.iloc[-1,i],alpha=0.5,color='black')
    ax2.set_ylim([min(y.iloc[:,i])-1, max(y.iloc[:,i])+1])


