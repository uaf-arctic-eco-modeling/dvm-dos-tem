#!/bin/bash

# Paths here assume that you are running inside 
# docker container with the input catalog and a 
# workflows directory mounted in /data


# Copy paste as needed to run workflow...
# Or maybe this will actually run as a script??
# Haven't tried doing it all at once


# 1) setup working directories:
for i in basecase modopt1 modopt2 modopt3;
do
  ./scripts/setup_working_directory.py \
  --input-data-path /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Betty_Pingo_MNT_10x10/ \
  /data/workflows/workshop-lab2/$i
done

# 2) run mod script
for i in 1 2 3;
do
  ./scripts/Input_exp.py --opt $i \
  --inpath /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Betty_Pingo_MNT_10x10/ \
  --outpath /data/workflows/workshop-lab2/modopt$i
done

# Now you might want to run the Input_exp.py --plot-inputs option to 
# to see what you've got! **Beaware** that if you have
# been working inside a docker container up to this point, and you want
# to run the plotting script inside the docker container, you will want
# to change the plt.show() call in the plot function to 
# plt.save_fig('your file.png') with an appropriate file name.
# Also you will likely want to adjust the plot so it is only showing
# the data of interest.  When you run with plt.show() and get the
# interactive viewer you can zoom as needed, but it is hard to get the
# interactive viewer to show up from w/in a docker container. So save a
# figure instead. 
# Alternatively, if you have a functioning python environment outside of
# the docker container, you can work there.

# Could move config adjustment here...but then need to know the filename
# of the modified file...which is set as a constant in the begining of
# the Input_exp.py file...so the config modificaiton is over there 
# for now...not sure what the best plan is...

# 3) tweak run mask
cd /data/workflows/workshop-lab2
for i in $(ls);
do 
  /work/scripts/runmask-util.py --reset --yx 0 0 $i/run-mask.nc;
done

# 4) Adjust outspecs
cd /data/workflows/workshop-lab2
for i in $(ls);
do
  /work/scripts/util/outspec.py $i/config/output_spec.csv --empty
  /work/scripts/util/outspec.py $i/config/output_spec.csv --on DRIVINGTAIR d
  /work/scripts/util/outspec.py $i/config/output_spec.csv --on NPP m
done

# further adjust config, output settings
cd /data/workflows/workshop-lab2
for i in $(ls);
do
python <<EOP
import json
with open('$i/config/config.js') as f:
  jd = json.load(f)
jd['IO']['output_nc_sp'] = 0
with open('$i/config/config.js', 'w') as f:
  json.dump(jd, f, indent=2)
EOP
done

# run the model
cd /data/workflows/workshop-lab2
for i in $(ls);
do
  cd $i
  dvmdostem -p 25 -e 150 -s 50 -t 115 -n 0 -l err 
  cd ..
done

# Now run the plotting options in Input_exp.py !! Same caveats as 
# above re: docker, plt.show, etc
