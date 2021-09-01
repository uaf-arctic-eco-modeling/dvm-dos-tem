#!/usr/bin/env python

import argparse
import glob
import re
from re import search
import pandas as pd
import matplotlib.pyplot as plt
#import seaborn as sns

if __name__ == '__main__':

  parser = argparse.ArgumentParser()

  #directory with the slurm logs
  parser.add_argument('--dir', required=True)


  args = parser.parse_args()

  log_directory = args.dir

  summary_file = open(log_directory + '/summary.txt', 'w')
  A_count = 0
  B_count = 0
  A_times = []
  B_times = []

  #SLURM log name pattern
  #slurm-xxxxxx.out
  for logfilename in glob.glob(log_directory + '/slurm-*.out'):
    print(logfilename)
    with open(logfilename) as logfile:
      log_lines = logfile.readlines()

    for line in log_lines:

      #Node count, ids
      #Example: n[40-41,65]
      if search('n\[*\]', line):
        print("node count line")

      #Time based on time() difference just after advance_model()
      #Example: cell 45, 143 complete.113
      if 'complete' in line:
        match = re.search(r'\.[0-9]+', line)
        if match:
          A_count+=1
          A_times.append(int(match.group()[1:]))

      #Time based on time() difference after writing status and fail_log
      #Example: Total Seconds: 1219
      if 'Total Seconds' in line:
        match = re.search(r': [0-9]+', line)
        if match:
          B_count+=1
          B_times.append(int(match.group()[2:]))


  #total_A_time = 0
  summary_file.write(f"Count of A times: {A_count}\n")
  summary_file.write("Average A time: " + str(sum(A_times)/len(A_times)) + "\n")
  summary_file.write(f"A times: {A_times}\n")

  summary_file.write("\n")

  summary_file.write(f"Count of B times: {B_count}\n")
  summary_file.write("Average B time: " + str(sum(B_times)/len(B_times)) + "\n")
  summary_file.write(f"B times: {B_times}\n")


#Convert times to minutes
A_minutes = [time / 60 for time in A_times]  
B_minutes = [time / 60 for time in B_times]  

#Find max and min for plot limits
A_min = min(A_minutes)
A_max = max(A_minutes)

print(f"A min: {A_min}")
print(f"A max: {A_max}")

B_min = min(B_minutes)
B_max = max(B_minutes)

#Count into buckets based on
bin_size = 5 #5 minutes
A_bins = range(int(A_min), int(A_max)+bin_size, bin_size)
print(A_bins)
B_bins = range(int(B_min), int(B_max)+bin_size, bin_size)

A_binned = pd.cut(A_minutes, bins=A_bins, include_lowest=True)
print(A_binned)

B_binned = pd.cut(B_minutes, bins=B_bins, include_lowest=True)
print(B_binned)
print(B_binned.value_counts())

#fig, axes = plt.subplots(2)
fig, ax = plt.subplots()
#axes[0] = A_binned.value_counts().plot.bar(rot=0)
#axes[1] = B_binned.value_counts().plot.bar(rot=0)
ax = B_binned.value_counts().plot.bar(rot=0)

plt.show()



