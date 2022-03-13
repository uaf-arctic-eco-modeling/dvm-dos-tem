#!/usr/bin/env python

# T. Carman Spring 2020
# Script to make a few adjustments to the Makefile to allow it
# to work on macOS Catalina (10.15) using macports as a package manager.

def swap_boost_mt(x):
  # checking for '-mt' allows script to be run multiple times
  # without problems.
  if ('-lboost_' in x) and ('-mt' not in x):
    return x +'-mt'
  else:
    return x

def swap_lapacke(x):
  # Not sure why on some systems the lapacke headers come
  # from openblas package...
  if ('-llapacke' in x):
    return '-lopenblas'
  else:
    return x

def apply_fixes(x):
  x = ' '.join([swap_boost_mt(i) for i in x.split(' ')])
  x = ' '.join([swap_lapacke(i) for i in x.split(' ')])
  return x

print("Reading existing makefile...")
with open('Makefile', 'r') as f:
  lines = f.read().split('\n')

print("Updating....")
new_data_str = '\n'.join([apply_fixes(x) for x in lines])

print("Writing new makefile...")
with open('Makefile', 'w') as f:
  f.write(new_data_str)

