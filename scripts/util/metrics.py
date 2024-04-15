#!/usr/bin/env python

# T. Carman, Dec 2023

# Metrics used to evaluate dvmdostem performance in various ways.

import scipy.stats
import numpy as np
import matplotlib.pyplot as plt

import util.output
import util.param

def eq_quality(var, fileprefix='', cmtkey='', PXx=None, PXy=None, pref=''):
  '''
  Draft ... experimenting with measuring eq state...
  '''

  data, dims = util.output.get_last_n_eq(var, timeres='yearly', 
                                         fileprefix=fileprefix, n=30)

  def measure(data):

    x = np.indices(data.shape)[0]
    #x = np.arange(data.shape[0])
    slope, intercept, r, p, std_err = scipy.stats.linregress(x, data)
    cv = 100 * data.std() / data.mean()

    return dict(slope=slope, 
                #intercept=intercept, 
                #r=r, 
                p=p, 
                #std_err=std_err,
                cv=cv)

  dsizes, dnames = list(zip(*dims))

  final_data = {}

  if dnames == ('time','y','x'):
    values = data[:,PXy,PXx]
    d = dict(**measure(values))
    d = {f"{var}_eq_{key}":val for key, val in d.items()}
    final_data = {**final_data, **d}
    #print(d)
    #final_data.append(d)
    #final_data.append(d)

  elif dnames == ('time','y','x','pft'):
    for pft in range(0,10):
      if util.param.is_ecosys_contributor(cmtkey, pft, ref_params_dir=pref):
        values = data[:,pft,PXy,PXx]
        d = dict(**measure(values))
        d = {f"{var}_pft{pft}_eq_{key}":val for key, val in d.items() }
        final_data = {**final_data, **d}
        #print(d)
        #final_data.append(d)
      else:
        pass #print "  -> Failed" # contributor test! Ignoring pft:{}, caltarget:{}, output:{}".format(pft, ctname, ncname)

  elif dnames == ('time','y','x','pft','pftpart'):
    for pft in range(0,10):
      clu = {0:'Leaf', 1:'Stem', 2:'Root'}
      for cmprt in range(0,3):
        if util.param.is_ecosys_contributor(cmtkey, pft, clu[cmprt], ref_params_dir=pref):
          values = data[:,cmprt,pft,PXy,PXx]
          d = dict(**measure(values))
          d = {f"{var}_pft{pft}_{cmprt}_eq_{key}":val for key, val in d.items() }
          final_data = {**final_data, **d}
          #final_data.append(measure(values))
        else:
          pass #print "  -> Failed! "#contributor test! Ignoring pft:{}, compartment:{}, caltarget:{}, output:{}".format(pft, cmprt, ctname, ofname)

  elif 'layer' in dnames:
    print("LAYER VARIABLES NOT IMPLEMENTED YET!")

  else:
      raise RuntimeError(f"Unexpeceted dimensions for variable {var}")

  return final_data

def plot_optimization_fit(seed_params=None, ig_params=None, opt_params=None,
                          seed_out=None, ig_out=None, opt_out=None,
                          targets=None, param_labels=[], out_labels=[], 
                          savefile=None):
  '''
  Make a plot with three axes allowing an overview of optimization performance.

  The first set of axes shows the parameter values use for the seed run, the 
  initial guess run, and the optimized run.

  The second set of axes shows the model outputs for the seed run, the initial 
  guess run, and the optimizied run. The target values are shown as red dots.

  The third set of axes show the "residulas" or model outputs - targets.
  
  .. image:: images/util_examples/metrics.plot_optimization_fit.png
    :width: 80%

  '''
  fig, axes = plt.subplots(3, 1, figsize=(10,10))

  axes[0].set_title("Parameters")
  axes[1].set_title("Outputs")
  axes[2].set_title("Residuals (model outputs - targets)")

  axes[0].plot(seed_params, marker='o', linewidth=0, alpha=0.6, label='seed')
  axes[1].plot(seed_out, label='seed')

  axes[0].plot(ig_params, marker='^', linewidth=0, alpha=0.6, label='ig')
  axes[1].plot(ig_out, label='ig')

  axes[0].plot(opt_params, marker='+', linewidth=0, alpha=0.6, label='opt')
  axes[1].plot(opt_out, label='opt')
  axes[1].plot(targets, color='red', marker='o', linewidth=0, label='targets')

  axes[0].set_xticklabels(param_labels, rotation=45)
  #axes[1].set_xticklabels(out_labels, rotation=45) 
  axes[2].set_xticklabels(out_labels, rotation=45) 

  # Plot the residuals as a bar graph
  axes[2].bar(out_labels, opt_out-targets, align='center', width=.6, 
              color='red', alpha=.75)
  #axes[1].set_xticklabels([])

  # This handles annoyance with bar plots where the bar is centered, and
  # therfore hangs to the left of zero, and so messes with the auto-scaling...
  for a in (axes[0], axes[1]):
    a.set_xlim(axes[2].get_xlim())

  axes[0].legend()
  axes[1].legend()
  #axes[2].legend()

  plt.tight_layout()
  plt.savefig(savefile)