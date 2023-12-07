#!/usr/bin/env python

# T. Carman, Dec 2023

# Metrics used to evaluate dvmdostem performance in various ways.

import matplotlib.pyplot as plt


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