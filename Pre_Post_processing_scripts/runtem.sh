#!/bin/bash -l
#SBATCH -p main -n 1

echo " group $gamma, job $alpha - $beta"


#run the model;
./DOSTEM $CASEDIR/regncontrol_$beta.txt

#concatenate the results together;
if ncdump -h $CASEDIR/output/g$gamma/run$beta/restart-${md}.nc  |   grep -q "CHTID = UNLIMITED ; // (0 currently)"; then
rm $CASEDIR/output/g$gamma/run$beta/restart-${md}.nc
mv $CASEDIR/output/g$gamma/run$beta/status-${md}.nc $CASEDIR/output/g$gamma/status-${md}-$beta.nc
else
rm $CASEDIR/output/g$gamma/run$beta/status-${md}.nc
mv $CASEDIR/output/g$gamma/run$beta/restart-${md}.nc $CASEDIR/output/g$gamma/restart-${md}-$beta.nc
fi

rm -r $CASEDIR/output/g$gamma/run$beta
