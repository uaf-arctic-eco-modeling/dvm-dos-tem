library(ncdf4)

# ---!!! Indicate the path to the TEM output folder !!!---
setwd('/home/colin_tucker/dvm-dos-tem/DATA/test_single_site/output')
# ---!!! Indicate the type of data you want to extract !!!---

#what run mode (eq, tr, sp ,sc)? If several modes, separate with a comma. If all, type 'all'.
run <- c('eq')
#what time step (daily, monthly, yearly)? if several time steps, separate with a comma. If all, type 'all'.
timestep <- c('monthly')
#what variable? If several variables, separate with a comma.
##variable  <- c('NUPTAKEL','NUPTAKESALL','NUPTAKES','NMOBILALL','NMOBIL','NMOBILALL','NRESOBALL',
#               'NRESORB','VEGNSUM','RH','NMITKSOIL','NETNMIN','AVLNINPUT',
#               'AVLNLOST','ORGNLOST','LTRFALNALL','AVLNSUM','NEP','NPPALL','INNPPALL','LTRFALCALL','VEGCSUM',
#               'GPPALL','INGPPALL','SOMCSHLW','SOMCDEEP','SOMCMINEA','SOMCMINEB','SOMCMINEC','RHMOIST',
#               'RHQ10','SOILLTRFCN','LAI','SNOWFALL','ALD','EETTOTAL','PETTOTAL','TAIR','RAINFALL','SOILTAVE','SOILVWC','RZTHAWPCT')
variable <- VEGCSUM
#Create a folder to store the output text files: 1 file per variable
dir <- 'Txt' 
dir.create(paste(getwd(),'/',dir,sep=''), recursive=TRUE)


# Identifying the output file containing the variable under interest

listdim <- c('CHTID','YEAR','MONTH','CMTTYPE','VEGAGE','IFWOODY','IFDECIWOODY','IFPERENIAL','NONVASCULAR',
             'VEGCOV','LAI','FPC','ROOTFRAC','FLEAF','FFOLIAGE','SNWAGE','SNWTHICK','SNWDENSE','SNWRHO','SNWEXTRAMASS',
             'SOILLAYERNO','MOSSLAYERNO','SHLWLAYERNO','DEEPLAYERNO','MINELAYERNO','SOILTHICK','MOSSTHICK','SHLWTHICK',
             'DEEPTHICK','MINEATHICK','MINEBTHICK','MINECTHICK','SOILZ','SOILDZ','SOILTYPE','SOILPORO','SOILTEXTURE','SOILRTFRAC')


listenv <- c('CHTID','ERRORID','YEAR','MONTH','DAY','CO2','TAIR','NIRR','PREC','VAPO','SVP','VPD','PAR','RAINFALL','SNOWFALL',
             'PARDOWN','PARABSORB','SWDOWN','SWINTER','RAININTER','SNOWINTER','EETTOTAL','PETTOTAL','CANOPYRAIN','CANOPYSNOW',
             'CANOPYRC','CANOPYCC','CANOPYBTRAN','CANOPYM_PPFD','CANOPYM_VPD','CANOPYSWREFL','CANOPYSWTHFL','CANOPYEVAP',
             'CANOPYTRAN','CANOPYPEVAP','CANOPYPTRAN','CANOPYSUBLIM','CANOPYRDRIP','CANOPYRTHFL','CANOPYSDRIP','CANOPYSTHFL',
             'SNWLNUM','SNWTHICK','SNWDENSITY','SNWEXTRAMASS','SNWDZ','SNWAGE','SNWRHO','SNWPOR','SNWWE','SNWT','SNWWESUM','SNWTAVE',
             'SNWSWREFL','SNWSUBLIM','SOILICESUM','SOILLIQSUM','SOILVWCSHLW','SOILVWCDEEP','SOILVWCMINEA','SOILVWCMINEB','SOILVWCMINEC',
             'SOILTAVE','SOILTSHLW','SOILTDEEP','SOILTMINEA','SOILTMINEB','SOILTMINEC','SOILTEM','SOILLIQ','SOILICE','SOILVWC','SOILLWC',
             'SOILIWC','FRONTZ','FRONTTYPE','WATERTABLE','PERMAFROST','ALD','ALC','RZGROWSTART','RZGROWEND','RZTEM','RZDEGDAY','RZTHAWPCT',
             'SOILSWREFL','SOILEVAP','SOILPEVAP','RUNOFF','DRINAGE')

listbgc <- c('CHTID','ERRORID','YEAR','MONTH','VEGCSUM','VEGCPART','VEGNSUM','VEGNLAB','VEGNSTRNSUM','VEGNSTRNPART','VEGCDEAD','VEGNDEAD',
             'WDEBRISC','WDEBRISN','GPPFTEMP','GPPGV','GPPFNA','GPPFCA','RAQ10','RMKR','INGPPALL','INGPP','INNPPALL','INNPP','GPPALL',
             'GPP','NPPALL','NPP','RMALL','RM','RGALL','RG','LTRFALCALL','LTRFALC','LTRFALNALL','LTRFALN','INNUPTAKE','NROOTEXTRACT',
             'NUPTAKEL','NUPTAKESALL','NUPTAKES','NMOBILALL','NMOBIL','NRESOBALL','NRESORB','RAWC','SOMA','SOMPR','SOMCR','ORGN','AVLN',
             'SOMCSHLW','SOMCDEEP','SOMCMINEA','SOMCMINEB','SOMCMINEC','RAWCSUM','SOMASUM','SOMPRSUM','SOMCRSUM','ORGNSUM','AVLNSUM','RH',
             'NMITKSOIL','RHMOIST','RHQ10','SOILLTRFCN','NEP','NETNMIN','ORGCINPUT','ORGNINPUT','AVLNINPUT','DOCLOST','AVLNLOST',
             'ORGNLOST','BURNTHICK','BURNSOIC','BURNVEGC','BURNSOIN','BURNVEGN','BURNRETAINC','BURNRETAINN')


for (a in 1:length(run))
{
for (b in 1:length(timestep))
{
for (c in 1:length(variable))
{

varname <- variable[c]

test1 <- (varname %in% listdim)
test2 <- (varname %in% listbgc)
test3 <- (varname %in% listenv)

typename <- ifelse(test1 =='TRUE','dim',ifelse(test2 == 'TRUE','bgc',ifelse(test3 == 'TRUE','env','Variable unknown')))
if (typename == 'Variable unknown') print(typename)

stepname <- ifelse(timestep[b] == 'daily','dly',ifelse(timestep[b] == 'monthly','mly',ifelse(timestep[b] == 'yearly','yly','Time step unknown')))
if (stepname == 'Time step unknown') print(stepname)

runname <- run[a]

#Extracting variables from the dimension type files
out <- nc_open(paste('./cmt',typename,'_',stepname,'-',runname,'.nc',sep=''))
		#out <- nc_open('/home/helene/Documents/DVMDOSTEM/Test1/TEMruns/DATA/output/cmtbgc_mly-eq.nc')
		#varname='ORGNLOST'
		#typename='bgc'

#identify the rank of the variable and the time-related parameters
for (i in 1:out$nvars)
{
if (varname == out$var[[i]]$name) rk <- i
if (out$var[[i]]$name == 'YEAR') rkyear <- i
if (out$var[[i]]$name == 'MONTH') rkmonth <- i
if (typename == 'env' & out$var[[i]]$name == 'DAY') rkday <- i
}

#starting the file by copying the time-related parameters
#for (i in 1:out$nvars) print (paste("var",i,": ",out$var[[i]]$name))
year <- data.frame(ncvar_get(out,out$var[[rkyear]],start=1,count=out$var[[rkyear]]$dim[[1]]$len))
month <- data.frame(ncvar_get(out,out$var[[rkmonth]],start=1,count=out$var[[rkmonth]]$dim[[1]]$len))
if (typename == 'env') day <- data.frame(ncvar_get(out,out$var[[rkday]],start=1,count=out$var[[rkday]]$dim[[1]]$len))

if (typename == 'dim' | typename == 'bgc')
{
file <- data.frame(year,month)
names(file) <- c('year','month')
}

if (typename == 'env')
{
file <- data.frame(year,month,day)
names(file) <- c('year','month','day')
}

#extraction for variables with one dimension
if (out$var[[rk]]$ndims == 1)
{
	for (i in 1:out$ndims)
	{
	if (out$var[[rk]]$dim[[1]]$name == out$dim[[i]]$name) rkdim1 <- i
	}
	var <- data.frame(ncvar_get(out,out$var[[rk]],start=1,count=out$dim[[rkdim1]]$len))
	names(var) <- varname
	file <- data.frame(file,var)
}

#extraction for variables with two dimensions
if (out$var[[rk]]$ndims == 2)
{
	for (i in 1:out$ndims)
	{
	if (out$var[[rk]]$dim[[1]]$name == out$dim[[i]]$name) rkdim1 <- i
	if (out$var[[rk]]$dim[[2]]$name == out$dim[[i]]$name) rkdim2 <- i
	}
	
	for(i in 1:out$dim[[rkdim1]]$len)
	{
	var <- data.frame(ncvar_get(out,out$var[[rk]],start=c(i,1),count=c(1,out$dim[[rkdim2]]$len)))
	dimname <- out$dim[[rkdim1]]$name
	names(var)<-paste(varname,"_",dimname,i,sep="")
	file <- data.frame(file,var)	
	}
}

#extraction for variables with three dimensions
if (out$var[[rk]]$ndims == 3)
{
	for (i in 1:out$ndims)
	{
	if (out$var[[rk]]$dim[[1]]$name == out$dim[[i]]$name) rkdim1 <- i
	if (out$var[[rk]]$dim[[2]]$name == out$dim[[i]]$name) rkdim2 <- i
	if (out$var[[rk]]$dim[[3]]$name == out$dim[[i]]$name) rkdim3 <- i
	}

	for(i in 1:out$dim[[rkdim2]]$len)
	{
		for(j in 1:out$dim[[rkdim1]]$len)
		{
		var <- data.frame(ncvar_get(out,out$var[[rk]],start=c(j,i,1),count=c(1,1,out$dim[[rkdim3]]$len)))	
		dimname1 <- out$dim[[rkdim1]]$name
		dimname2 <- out$dim[[rkdim2]]$name
		names(var)<-paste(varname,"_",dimname2,i,dimname1,j,sep="")		
		file <- data.frame(file,var)	
		}
	}
}
write.csv(file, file=paste("./",dir,"/",typename,"_",stepname,"_",varname,"_",runname,".csv", sep=""))
}
}
}



