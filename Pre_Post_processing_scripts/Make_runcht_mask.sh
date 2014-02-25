### prepare a list of ids (runcht.nc) from an area of interest that will be used as a mask to run dostem on the aoi;

# In ARGIS:
1- Transform the layer to NAD83 (AOI83): Data Management -> Projection and Transformation -> Project
2- Convert it to a raster the same extent as the iem mask: Conversion Tools -> To Raster -> Polygon to raster --!!!!—select the Cell size and  the Environement / Processing Extent to be the same as the iem mask
3- Check that the number of row, the number of column and the origin are the same of the raster of the AOI and the iem mask (right click on the rasters -> Properties / Sources
4- if not clip with the iem mask: Data Management -> clip
5- Check that in both rasters (the iem mask and the AOI), WITHIN  the area of interest the pixel value = 1 and OUTSIDE the area of interest, pixel value = 0
6- If not change the values with Spatial Analyst Tools -> Map Algebra -> Raster Calculator
7- Convert both rasters (the iem mask and AOI) to netcdf files: Multidimension Tools -> Raster to Netcdf


#make a copy of the original files
cp iem01.nc iem01_original.nc
cp aoi01.nc aoi01_original.nc


#merge the two masks together;
ncks -A -h iem01.nc aoi01.nc


#create the EID (extent ID = each cells of the extent of the iem area is attributed an id -> the numbering start at 1 at the north east corner and increment southward and then eastward). The EID is used as a framework to get the final ID
ncap2 -O -h -s'
top=max(y);
left=min(x);
row[y]=int((top-y)/1000)+1;
col[x]=int((x-left)/1000)+1;
nrow=max(row);
EID[y,x]=int((nrow*(col-1))+row);' aoi01.nc aoi01.nc


#convert the 2 dimensions EID and flags to one dimension to fit dostem file configuration
ncap2 -O -h -s'
defdim("ID", $x.size*$y.size);
eid1[$ID]=int(0);
aoi1[$ID]=int(0);
iem1[$ID]=int(0);
eid1(0:($x.size*$y.size-1))=EID(0:($y.size-1),0:($x.size-1));
aoi1(0:($x.size*$y.size-1))=aoi(0:($y.size-1),0:($x.size-1));
iem1(0:($x.size*$y.size-1))=iem(0:($y.size-1),0:($x.size-1));' aoi01.nc aoi01.nc


#sort and select the eids that are within the iem simulation area (iem1=1);
ncap2 -O -h -s'
iem1=sort(iem1,&map);
aoi1=remap(aoi1,map);
eid1=remap(eid1,map);

fgN=iem1.total();
defdim("Dflg_out", fgN);
eid_out[Dflg_out]= eid1((($x.size*$y.size)-fgN):(($x.size*$y.size)-1));
aoi_out[Dflg_out]= aoi1((($x.size*$y.size)-fgN):(($x.size*$y.size)-1));' aoi01.nc aoi01.nc

#remove all the variable we don't need;
ncks -O -h -v eid_out,aoi_out aoi01.nc eqchtid.nc

#rename dimensions and variables to feet with dostem file configuration;
ncrename -O -h -v eid_out,eid -v aoi_out,aoi -d Dflg_out,EQCHTID eqchtid.nc eqchtid.nc

#sort the file to have the eid's in ascending order and create EQCHTID record then;
ncap2 -O -h -s'
eid=sort(eid,&map); 
aoi=remap(aoi,map);
EQCHTID[$EQCHTID]=array(1,1,$EQCHTID)' eqchtid.nc eqchtid.nc

#Make the dimension unlimited to fit dostem file configuration  ;
ncecat -O -h eqchtid.nc eqchtid.nc
ncpdq -O -h -a EQCHTID,record eqchtid.nc eqchtid.nc
ncwa -O -h -a record eqchtid.nc eqchtid.nc


#sort and select the EQCHTID that are within the aoi simulation area (aoi=1);
ncap2 -O -h -s'
aoi=sort(aoi,&map); 
EQCHTID=remap(EQCHTID,map);
eid=remap(eid,map);

fgN=aoi.total();
defdim("Dflg_out", fgN);
EQCHTID_out[Dflg_out]= EQCHTID(($EQCHTID.size-fgN):($EQCHTID.size-1));
eid_out[Dflg_out]= eid(($EQCHTID.size-fgN):($EQCHTID.size-1));'  eqchtid.nc runcht.nc

#remove all the variable we don't need;
ncks -O -h -v EQCHTID_out runcht.nc runcht.nc

#rename dimensions and variables to feet with dostem file configuration;
ncrename -O -h -v EQCHTID_out,CHTID -d Dflg_out,CHTID runcht.nc runcht.nc









