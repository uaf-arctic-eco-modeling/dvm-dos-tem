#!/bin/bash

cd /work/

# #Pull and checkout upstream/master - this may break if the code is updated
#git checkout origin/master

# #Remember to recompile
#make clean
#make

#Community to be tested
cmt=13

#Organic layer thickness filename - parameters must be changed to implement this
olt='test_olt'

#Input forcing data directory
indir=/data/input-catalog/caribou-poker_merged

#Outspec file directory - later the whole config folder will be copied to avoid adjusting outputs
outdir=/data/workflows/Organic_Layer_Scheme_Test_Files/output_spec.csv

#Fixed organic layer thickness parameter files
#paramdir=/data/workflows/Organic_Layer_Scheme_Test_Files/parameters
paramdir=/work/parameters

#Pixels for run-mask
px=1
py=0

#Directory to store all files in test
simdir=/data/workflows/layer_scheme_test
rm -rf $simdir
#Create directory for reference simulation
mkdir -p $simdir/reference

#set as current simdir
refdir=$simdir/reference/

#Setup working directory
# /work/scripts/setup_working_directory.py $refdir --input-data-path $indir
rm -rf $refdir
/work/scripts/setup_working_directory.py /data/workflows/layer_scheme_test/reference/ --input-data-path /data/input-catalog/caribou-poker_merged

#Reset and set run-mask
/work/scripts/runmask-util.py --reset $refdir'/run-mask.nc'
/work/scripts/runmask-util.py --yx $py $px $refdir'/run-mask.nc'

#Remove and copy outspec
rm $refdir'config/output_spec.csv'
cp $outdir $refdir'config'

#Adjust outputs in config (whether you want equilibrium or not)
vim $refdir'config/config.js'

#Creating testing directories
mkdir -p $simdir'/'$olt'/1layer'

#Copy contents of reference directory to 1layer 
cp -a $refdir'/.' $simdir'/'$olt'/1layer'

#Remove and then copy parameter files for fixed organic layer thickness
rm -r $simdir'/'$olt'/1layer/parameters'
cp -r $paramdir $simdir'/'$olt'/1layer/'

#Copy contents of 1layer (with edited parameters) to remaining directories
cp -a $simdir'/'$olt'/1layer/.' $simdir'/'$olt'/2layer'
cp -a $simdir'/'$olt'/1layer/.' $simdir'/'$olt'/3layer'
cp -a $simdir'/'$olt'/1layer/.' $simdir'/'$olt'/4layer'
cp -a $simdir'/'$olt'/1layer/.' $simdir'/'$olt'/5layer'
cp -a $simdir'/'$olt'/1layer/.' $simdir'/'$olt'/6layer'
cp -a $simdir'/'$olt'/1layer/.' $simdir'/'$olt'/7layer'
cp -a $simdir'/'$olt'/1layer/.' $simdir'/'$olt'/8layer'
cp -a $simdir'/'$olt'/1layer/.' $simdir'/'$olt'/9layer'

#Changing to simulation directory
cd $refdir

#Conduct reference simulation
#/work/dvmdostem -l err -f $refdir'/config/config.js' --force-cmt $cmt -p 100 -e 1000 -s 250 -t 121 -n 85


#Checkout layer_scheme branch - TEM.cpp (dsl off) and updated Organic.cpp ShlwThickScheme and DeepThickScheme
#git checkout upstream/layer_scheme
#git pull
cd /work/
#git checkout layer_scheme

############################################# 1 Layer ########################################################

#Edit layerconst.h
sed -i '8 c const int MAX_SLW_LAY = 1;  // Maximum number of shallow organic Layer' /work/include/layerconst.h
sed -i '9 c const int MAX_DEP_LAY = 1;  // Maximum number of deep organic Layer' /work/include/layerconst.h

#Recompile
make clean
make

#Set simdir to be 1layer - to loop through layers
simdir=/data/workflows/layer_scheme_test/$olt/1layer/

cd $simdir

#Conduct simulation
/work/dvmdostem -l err -f $simdir'/config/config.js' --force-cmt $cmt -p 100 -e 1000 -s 250 -t 115 -n 85

############################################# 2 Layers #######################################################

cd /work

#Edit layerconst.h
sed -i '8 c const int MAX_SLW_LAY = 2;  // Maximum number of shallow organic Layer' /work/include/layerconst.h
sed -i '9 c const int MAX_DEP_LAY = 2;  // Maximum number of deep organic Layer' /work/include/layerconst.h

#Recompile
make clean
make

#Set simdir to be 1layer - to loop through layers
simdir=/data/workflows/layer_scheme_test/$olt/2layer/

cd $simdir

#Conduct simulation
/work/dvmdostem -l err -f $simdir'/config/config.js' --force-cmt $cmt -p 100 -e 1000 -s 250 -t 115 -n 85

############################################# 3 Layers #######################################################

cd /work

#Edit layerconst.h
sed -i '8 c const int MAX_SLW_LAY = 3;  // Maximum number of shallow organic Layer' /work/include/layerconst.h
sed -i '9 c const int MAX_DEP_LAY = 3;  // Maximum number of deep organic Layer' /work/include/layerconst.h

#Recompile
make clean
make

#Set simdir to be 1layer - to loop through layers
simdir=/data/workflows/layer_scheme_test/$olt/3layer/

cd $simdir

#Conduct simulation
/work/dvmdostem -l err -f $simdir'/config/config.js' --force-cmt $cmt -p 100 -e 1000 -s 250 -t 115 -n 85

############################################# 4 Layers #######################################################

cd /work

#Edit layerconst.h
sed -i '8 c const int MAX_SLW_LAY = 4;  // Maximum number of shallow organic Layer' /work/include/layerconst.h
sed -i '9 c const int MAX_DEP_LAY = 4;  // Maximum number of deep organic Layer' /work/include/layerconst.h

#Recompile
make clean
make

#Set simdir to be 1layer - to loop through layers
simdir=/data/workflows/layer_scheme_test/$olt/4layer/

cd $simdir

#Conduct simulation
/work/dvmdostem -l err -f $simdir'/config/config.js' --force-cmt $cmt -p 100 -e 1000 -s 250 -t 115 -n 85

############################################# 5 Layers #######################################################

cd /work

#Edit layerconst.h
sed -i '8 c const int MAX_SLW_LAY = 5;  // Maximum number of shallow organic Layer' /work/include/layerconst.h
sed -i '9 c const int MAX_DEP_LAY = 5;  // Maximum number of deep organic Layer' /work/include/layerconst.h

#Recompile
make clean
make

#Set simdir to be 1layer - to loop through layers
simdir=/data/workflows/layer_scheme_test/$olt/5layer/

cd $simdir

#Conduct simulation
/work/dvmdostem -l err -f $simdir'/config/config.js' --force-cmt $cmt -p 100 -e 1000 -s 250 -t 115 -n 85

############################################# 6 Layers #######################################################

cd /work

#Edit layerconst.h
sed -i '8 c const int MAX_SLW_LAY = 6;  // Maximum number of shallow organic Layer' /work/include/layerconst.h
sed -i '9 c const int MAX_DEP_LAY = 6;  // Maximum number of deep organic Layer' /work/include/layerconst.h

#Recompile
make clean
make

#Set simdir to be 1layer - to loop through layers
simdir=/data/workflows/layer_scheme_test/$olt/6layer/

cd $simdir

#Conduct simulation
/work/dvmdostem -l err -f $simdir'/config/config.js' --force-cmt $cmt -p 100 -e 1000 -s 250 -t 115 -n 85

############################################# 7 Layers #######################################################

cd /work

#Edit layerconst.h
sed -i '8 c const int MAX_SLW_LAY = 7;  // Maximum number of shallow organic Layer' /work/include/layerconst.h
sed -i '9 c const int MAX_DEP_LAY = 7;  // Maximum number of deep organic Layer' /work/include/layerconst.h

#Recompile
make clean
make

#Set simdir to be 1layer - to loop through layers
simdir=/data/workflows/layer_scheme_test/$olt/7layer/

cd $simdir

#Conduct simulation
/work/dvmdostem -l err -f $simdir'/config/config.js' --force-cmt $cmt -p 100 -e 1000 -s 250 -t 115 -n 85

############################################# 8 Layers #######################################################

cd /work

#Edit layerconst.h
sed -i '8 c const int MAX_SLW_LAY = 8;  // Maximum number of shallow organic Layer' /work/include/layerconst.h
sed -i '9 c const int MAX_DEP_LAY = 8;  // Maximum number of deep organic Layer' /work/include/layerconst.h

#Recompile
make clean
make

#Set simdir to be 1layer - to loop through layers
simdir=/data/workflows/layer_scheme_test/$olt/8layer/

cd $simdir

#Conduct simulation
/work/dvmdostem -l err -f $simdir'/config/config.js' --force-cmt $cmt -p 100 -e 1000 -s 250 -t 115 -n 85

############################################# 9 Layers #######################################################

cd /work

#Edit layerconst.h
sed -i '8 c const int MAX_SLW_LAY = 9;  // Maximum number of shallow organic Layer' /work/include/layerconst.h
sed -i '9 c const int MAX_DEP_LAY = 9;  // Maximum number of deep organic Layer' /work/include/layerconst.h

#Recompile
make clean
make

#Set simdir to be 1layer - to loop through layers
simdir=/data/workflows/layer_scheme_test/$olt/9layer/

cd $simdir

#Conduct simulation
/work/dvmdostem -l err -f $simdir'/config/config.js' --force-cmt $cmt -p 100 -e 1000 -s 250 -t 115 -n 85


#Prepare for next run - leave a clean branch

cd /work/

#restore layerconst.h
git restore include/layerconst.h