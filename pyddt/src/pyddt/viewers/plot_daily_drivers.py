#!/usr/bin/env python

# plot_daily_containers.py
# Tobey Carman
# UAF, August 2015

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib.gridspec as gridspec

#######################################
# Run dvmdostem with --loglevel=debug 
# and copy/paste the values to here:
#######################################
tair_d = [-25.7649994, -25.6827393, -25.600481]
nirr_d = [3.58925724, 3.820822, 4.05238676]
vapo_d = [0.309418708, 0.329381198, 0.349343687]
prec_d = [0, 0, 0]
rain_d = [0, 0, 0]
snow_d = [0, 0, 0]
svp_d = [100.776215, 101.418533, 102.064491]
vpd_d = [100.466797, 101.089149, 101.715149]
girr_d = [1.62252975, 1.72720909, 1.83188844]
cld_d = [0, 0, 0]
par_d = [0.200903997, 0.213865548, 0.226827085]

print("MAKE SURE YOU HAVE CORRECTLY COPIED IN YOUR OWN DATA!")


f = plt.figure()

# 22 rows: 5 for each main plot, 1 for clouds.
# Allows the cloud plot to be small.
gs = gridspec.GridSpec(21,1) 

days = np.arange(0, 365)

# RADIATION
ax1 = plt.subplot(gs[0:6])
ax1.plot(girr_d, label="girr_d", linewidth=1.0)
ax1.plot(nirr_d, label="nirr_d", linewidth=1.0)
ax1.plot(par_d, label='par_d', linewidth=1.0)
ax1.legend(fontsize='small')
ax1.set_ylabel("W/m^2")

# CLOUDS
ax1a = plt.subplot(gs[6:7], sharex=ax1)
ax1a.plot(cld_d, label="%clds", linewidth=0.0, alpha=.5,)
pc = ax1a.fill_between(np.arange(0,len(cld_d)), cld_d, 0, alpha=1.0, color='black')
ax1a.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(2, prune=None))
ax1a.set_ylabel("%cld")
ax1a.tick_params(labelsize='x-small')

# PRECIP
#  - not ideal, the bars are very skinny and it is hard to read
#    the total vs rain/snow w/o zooming in, but it works...
ax2 = plt.subplot(gs[7:12], sharex=ax1)
pbars = ax2.bar(days, prec_d, width=0.5, bottom=0, linewidth=0.0, color='black', alpha=.5, label="total precip")
rbars = ax2.bar(days+0.5, rain_d, width=0.5, bottom=0, linewidth=0.0, color='green', alpha=1, label="rain")
sbars = ax2.bar(days+0.5, snow_d, width=0.5, bottom=rain_d, linewidth=0.0, color='blue', alpha=1, label="snow")
ax2.set_ylabel("mm")
ax2.legend(fontsize='small')

# VAPO, TAIR
ax3 = plt.subplot(gs[12:17], sharex=ax1)
ax3.plot(tair_d, label='tair_d')
ax3.legend(fontsize='small', loc='upper left')
ax3.set_ylabel("deg C")

ax3a = ax3.twinx() #plt.subplot(gs[12:17], sharex=ax1)
ax3a.plot(vapo_d, label='vapo_d', color='green')
ax3a.legend(fontsize='small', loc='upper right')
ax3a.set_ylabel("????")


# VPD, SVP
ax4 = plt.subplot(gs[17:21], sharex=ax1)
ax4.plot(svp_d, label='svp_d')
ax4.plot(vpd_d, label='vpd_d')
ax4.legend(fontsize='small')
ax4.set_ylabel("?????")

# set ticks to be on month boundaries
for a in [ax1, ax1a, ax2, ax3, ax4]:
	a.xaxis.set_major_locator(matplotlib.ticker.FixedLocator([31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]))

# adjust tick colors
for a in [ax1, ax1a, ax2, ax3, ax4]:
	a.tick_params(axis='x', labelbottom=False, top='off', bottom='off')
	a.tick_params(axis='y', top='off', bottom='off', left='off', right='off')
	a.tick_params(axis='y', left='on', color='gray')

# label the bottom axis
ax4.tick_params(axis='x', labelbottom=True)
ax4.set_xlabel("Day of Year")

# control number of ticks on y axis, but not the cloud plot
for a in [ax1, ax2, ax3, ax3a, ax4]:
	a.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5, prune='both'))

# grid
for a in [ax1, ax2, ax3, ax1a, ax4]:
  a.grid(False, axis='y', which='both')
  a.grid(True, axis='x', which='both')

# turn off 'chart junk'
for a in [ax1, ax1a, ax2, ax3, ax3a, ax4]:
	a.spines['top'].set_visible(False)
	a.spines['right'].set_visible(False)
	a.spines['bottom'].set_visible(False)
	a.spines['left'].set_visible(False)

# for a in [ax1, ax1a, ax2, ax3, ax4]:
# 	a.spines['bottom'].set_visible(True)


plt.ion()
plt.show()
from IPython import embed; embed()


