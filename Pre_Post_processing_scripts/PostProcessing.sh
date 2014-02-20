#!/bin/bash

#cd ./DATA/TUSSOCK

##loop through all the sub-set output folders;
for dir in ./*/ ; do
dirname=$(basename $dir)
#Count the number of folder - 1 (for the verbose folder call out) to could the number of groups that have run in the set and correspondingly, the number of folder to process;
ngroup=$(($(ls -l $dir | grep -c ^d )-1))

##loop through all the group directories within this sub-set output folder;
for (( alpha=0;alpha<$ngroup;alpha++ )); do
nalpha=$(printf "%04d" ${alpha})
foldername="g$alpha"
restartname="restart-eq-$dirname-g$nalpha.nc"
statusname="status-eq-$dirname-g$nalpha.nc"
#restart the previous attempt of appending
rm -r $dir$foldername/run* 
if [ -f $dir$foldername/restart-eq-g* ] ; then
rm $dir$foldername/restart-eq-g*
fi
if [ -f $dir$foldername/status-eq-g* ] ; then
rm $dir$foldername/status-eq-g*
fi

##remove the restart files of cells that didn't run and renumber the others so they can be merged in descending order;
for file in $dir$foldername/restart-eq-* ; do
if [ -f $file ] ; then
temp=$(basename $file)
IFS="-" read -ra X <<< "$temp"
IFS="." read -ra Y <<< "${X[2]}"
num=$(printf "%06d" ${Y[0]})
filename="$dir$foldername/RST$num.nc"
mv $file $filename
if ncdump -h $filename | grep -q "CHTID = UNLIMITED ; // (0 currently)" ; then
rm $filename
fi
ncdump -h $filename > a.txt 
if [ $? -ne 0 ] ; then
rm $filename
fi 
fi
done
if [ "$(($(ls -l $dir$foldername/RST* | wc -l)))" -gt 0 ] ; then
ncrcat -O -h  $dir$foldername/RST* ./$restartname
fi

##remove the status files of cells that did run and renumber the others so they can be merged in descending order;
for file in $dir$foldername/status-eq-* ; do
if [ -f $file ] ; then
temp=$(basename $file)
IFS="-" read -ra X <<< "$temp"
IFS="." read -ra Y <<< "${X[2]}"
num=$(printf "%06d" ${Y[0]})
filename="$dir$foldername/STS$num.nc"
mv $file $filename
if ncdump -h $filename | grep -q "CHTID = UNLIMITED ; // (0 currently)" ; then
rm $filename
fi 
ncdump -h $filename > a.txt 
if [ $? -ne 0 ] ; then
rm $filename
fi 
fi
done
if [ "$(($(ls -l $dir$foldername/STS* | wc -l)))" -gt 0 ] ; then
ncrcat -O -h $dir$foldername/STS* ./$statusname
fi

##end of group folder loop;
done

##end of sub-set output folder loop;
done

rm *.tmp
ncrcat -O -h restart-eq-* restart-eq.nc
ncrcat -h status-eq-* status-eq.nc

rm restart-eq-* status-eq-*



