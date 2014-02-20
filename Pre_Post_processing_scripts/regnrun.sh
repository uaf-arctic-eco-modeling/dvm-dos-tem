#!/bin/bash

cells=41000
split=82
mode=("eq")
size=$(($cells/$split))
TEMDIR="./"
CASEDIR="./DATA"

echo "The number of cells to be run is " $cells
echo "There will be " $split "groups of" $size " cells each"
echo "The location of the executable is"  $TEMDIR
echo "The location of the data and the control file is" $CASEDIR

mkdir -p $CASEDIR/output
rm -r out/
mkdir out/
export CASEDIR


#splitting;

for (( gamma=0;gamma<$split;gamma++ )); do
mkdir out/g$gamma
mkdir $CASEDIR/output/g$gamma
echo "Group" $gamma "..."
export gamma
start=$(($gamma*$size))
end=$(($gamma*$size+$size-1))
if [[ $gamma == $(($split-1)) ]] ; then
end=$(($cells-1))
fi
echo "Group" $gamma "Starting point" $start "Ending point" $end

#running;
for (( alpha=0;alpha<${#mode[@]};alpha++ )); do
md=${mode[$alpha]}
export md
export alpha

for (( beta=$start ; beta<=$end ; beta++)); do
export beta
echo " group $gamma, job $alpha - $beta"

#make a output directory;
mkdir $CASEDIR/output/g$gamma/run$beta

#create the runcht.nc;
ncks -O -h -d CHTID,$(($beta)),$(($beta)),1 $CASEDIR/runcht.nc $CASEDIR/runcht_$beta.nc

#create the control file;
old="runcht.nc"
new="runcht_$beta.nc"
sed "s:$old:$new:g" $CASEDIR/regncontrol-${md}.txt >  $CASEDIR/regncontrol_$beta.txt
old="output/"
new="output/g$gamma/run$beta/"
sed -i "s:$old:$new:g" $CASEDIR/regncontrol_$beta.txt
done
wait

test="found"
#run the model;
for (( beta=$start ; beta<=$end ; beta++)); do
sbatch -n 1 --time=00:20:00 --ntasks-per-core=1  -o out/g$gamma/run-${mode[$alpha]}-$beta.out runtem.sh 
done

while [ $test = "found" ] ; do
if squeue | grep -q runtem. ; then  
test="found"
echo "waiting..."
sleep 10s
else
test="end"
echo "done!"
fi
done

rm $CASEDIR/regncontrol_$beta.txt
rm $CASEDIR/runcht_$beta.nc

echo ${mode[$alpha]} "run done"
done
echo "Group" $j "- Run completed"
done



