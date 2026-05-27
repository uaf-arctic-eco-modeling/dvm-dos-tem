#!/usr/bin/env python

# T. Carman Fall 2020
# Quick plot used for supplemental figure for submitted 
# Eco. App. paper. 
#
# Shows how the GPP temperature factor function works.
# See Vegetation_Bgc.cpp::getTempFactor4GPP(...)
#
# Note from A.D. McGuire:
# Basically, the optimum temperature is set to be the month of maximum leaf area, 
# to allow for local adaptation/acclimation of photosynthesis. This allows the 
# vegetation to optimize the temperature response of photosynthesis for each grid 
# cell based on the month of maximum leaf area for that grid cell. I think we first 
# introduced this into TEM 4.0, but it wasn't fully described until the publication 
# of an application of TEM 4.1 in the attached Tian et al. (1999). See the 
# paragraph that spans pages 445-446 in the appendix of that paper.

import matplotlib.pyplot as plt

TMIN = 15
TMAX = 85
AVG_PREV_TEMP = 55
TOPTMAX = 70

def get_GPP_tempfactor(temp_air):
  ftemp = 0
  if (temp_air <= TMIN) or (temp_air >= TMAX):
    ftemp = 0.0
  else:
    if (temp_air >= AVG_PREV_TEMP) and (temp_air <= TOPTMAX):
      ftemp = 1.0
    else:
      if (temp_air > TMIN) and (temp_air < AVG_PREV_TEMP):
        ftemp = (temp_air-TMIN)*(temp_air-TMAX)/((temp_air-TMIN)*(temp_air-TMAX)-pow(temp_air-AVG_PREV_TEMP, 2.0))
      else:
        ftemp = (temp_air-TMIN)*(temp_air-TMAX)/((temp_air-TMIN)*(temp_air-TMAX)-pow(temp_air-TOPTMAX, 2.0))
  return ftemp



fig, ax = plt.subplots(1,1)
ax.set_xlabel("Air Temperature")
ax.set_ylabel("Temperature Factor")

ax.vlines([TMIN, TMAX, AVG_PREV_TEMP, TOPTMAX], 0, 1, transform=ax.get_xaxis_transform(), color='red', linestyle='dashed')
ax.tick_params(axis='both', which='both', 
    bottom=False, labelbottom=False,
    top=False, labeltop=False,
    direction='in', pad=0.0
)

plt.yticks([0,1])
ax.tick_params(axis='y', which='major',
    bottom=False, labelbottom=False,
    top=False, labeltop=True,
    direction='in', pad=5.0
)

ax.tick_params(axis='x', which='major',
    bottom=False, labelbottom=False,
    top=False, labeltop=True,
    direction='out', pad=0.0
)
plt.xticks(
    [TMIN, AVG_PREV_TEMP,TOPTMAX,TMAX],
    ['tmax', 'avg 10 prev yrs\noptimum temp','toptmax','tmax'], 
    rotation=25, horizontalalignment='center'
)
for d in ["left", "top", "bottom", "right"]:
    plt.gca().spines[d].set_visible(False)


plt.suptitle("GPP temperature factor as a function of air temperature \nwith controlling parameter thresholds")

xrange = range(0,100)
data = [get_GPP_tempfactor(x) for x in xrange]

plt.plot(xrange, data, color='k')

plt.tight_layout()
plt.savefig("gpp_temp_factor.pdf")
#plt.show()
