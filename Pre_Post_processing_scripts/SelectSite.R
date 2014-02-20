library(ncdf4)

# The netcdf coordinate files from your regional data;

out <- nc_open('') #Location of your coordinate input nc file (latlon.nc);
for (i in 1:out$nvars) print(c('rank',i,'varname',out$var[[i]]$name))
for (i in 1:out$ndims) print(c('rank',i,'dimname',out$dim[[i]]$name))

grdid <- data.frame(ncvar_get(out,out$dim[[1]],start=1,count=out$dim[[1]]$len))
lat <- data.frame(ncvar_get(out,out$var[[1]],start=1,count=out$dim[[1]]$len)) 
lon <- data.frame(ncvar_get(out,out$var[[2]],start=1,count=out$dim[[1]]$len)) 

#The coordinates of your site in WGS64 decimal degree (projection generally used to build the latlon.nc input file);

x=
y=


#d is a vector containing the distance between your site and every centroid of the cells of the regional dataset;

d=(((lon-x)**2)+((lat-y)**2))**0.5
min=min(d)
rk <- which(d==min)

#output the grid id of the selected cell;

Xselect <- lon[rk,1]
Yselect <- lat[rk,1]
id <- grdid[rk,1]

M <- data.frame(rk,id,x,y,Xselect,Yselect,min)
names(M) <- c('RANK','GRDID','Xsite','Ysite','lat','lon','distance')

write.csv(M, file='')
M



#### THEN FROM THE COMMAND LINE EXTRACT THE INPUT FILES FOR THIS COHORT LIKE THIS (FOR DOSTEM):

#create the input directories
./singlesite/griddata/
./singlesite/regiondata/
./singlesite/cohort/eq
./singlesite/cohort/sp
./singlesite/cohort/tr

#extract the data
ncks -O -h -d GRDID,"rank-1" ./griddata/latlon.nc ./singlesite/griddata/latlon.nc
ncks -O -h -d GRDID,"rank-1" ./griddata/soil.nc ./singlesite/griddata/soil.nc
ncks -O -h -d CLMID,"rank-1" ./griddata/climate.nc ./singlesite/griddata/climate.nc
ncks -O -h -d GRDID,"rank-1" ./griddata/fire.nc ./singlesite/griddata/fire.nc

ncks -O -h -d EQCHTID,"rank-1" ./cohort/eq/cohortid.nc ./singlesite/cohort/eq/cohortid.nc
ncks -O -h -d EQCHTID,"rank-1" ./cohort/eq/vegetation.nc ./singlesite/cohort/eq/vegetation.nc
ncks -O -h -d EQCHTID,"rank-1" ./cohort/eq/drainage.nc ./singlesite/cohort/eq/drainage.nc

ncks -O -h -d SPCHTID,"rank-1" ./cohort/sp/cohortid.nc ./singlesite/cohort/sp/cohortid.nc
ncks -O -h -d SPCHTID,"rank-1" ./cohort/sp/fire.nc ./singlesite/cohort/sp/fire.nc

ncks -O -h -d TRCHTID,"rank-1" ./cohort/tr/cohortid.nc ./singlesite/cohort/tr/cohortid.nc
ncks -O -h -d TRCHTID,"rank-1" ./cohort/tr/fire.nc ./singlesite/cohort/tr/fire.nc

#to run a single site, EQCHTID should be equal to one

ncap2 -O -h -s'EQCHTID()=1' ./singlesite/cohort/eq/cohortid.nc ./singlesite/cohort/eq/cohortid.nc
ncap2 -O -h -s'EQCHTID()=1' ./singlesite/cohort/eq/vegetation.nc ./singlesite/cohort/eq/vegetation.nc
ncap2 -O -h -s'EQCHTID()=1' ./singlesite/cohort/eq/drainage.nc ./singlesite/cohort/eq/drainage.nc
ncap2 -O -h -s'EQCHTID()=1' ./singlesite/cohort/sp/cohortid.nc ./singlesite/cohort/sp/cohortid.nc

#region data don't change, you can simply copyt the co2 file to the new directory;

cp ./regiondata/*.nc ./singlesite/regiondata/*.nc








