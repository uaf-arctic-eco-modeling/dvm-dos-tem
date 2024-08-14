import numpy as np
import pandas as pd
import statistics as stat
import math

def get_finalres_stats(filename):
  """
  Reads optimal parameters from final results file 
  #can probably use for interation and initial files too

  Parameters:
  filename (list): List of file name to be read

  Returns:
  dictionary of params (keys) and optimal values found (values). Order matters, optimal paramaters of index 1 for each key belong to the same run
  """
  #we assume there are three lines per calibration - 0=OF, 1=lambda, 2=params
  with open(filename) as f:
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
      params.setdefault(key, []).append(round(float(val),2))
  s=[]
  for item in params.keys():
    arr = np.array(params[item])
    amin=arr.mean()-arr.std()
    amax=arr.mean()+arr.std()
    s.append([item, round(arr.mean(),2), round(arr.std(),2) ,round(amin,2), round(amax,2)])   
  return s

print(get_finalres_stats('AC3-STEP3-MD1-R-EJ-new.finalresults'))
