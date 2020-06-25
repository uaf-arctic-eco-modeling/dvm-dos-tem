#!/usr/bin/env python3

import subprocess


file1 = "/vagrant/5_cell_old_mri/ALD_yearly_sc.nc"
file2 = "/vagrant/202006_mri/ALD_yearly_sc.nc"



outfile = "ALD_diff.nc"
avgfile = "ALD_diff_avg.nc"

print("diffing ALD")
process = subprocess.run(['ncdiff', file1, file2, outfile],
               stdout=subprocess.PIPE)

print(process.stdout)

#Average across cells
print("Averaging across cells")

subprocess.run(['ncwa', '-O', '-h', '-v', 'ALD', '-a', 'x,y', '-y', 'avg', outfile, avgfile],
               stdout=subprocess.PIPE)





