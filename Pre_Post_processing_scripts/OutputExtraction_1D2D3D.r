library(ncdf4)

# Extract a uni-dimension variable;

out <- nc_open('') #Location of your nc file;
for (i in 1:out$nvars) print(c('rank',i,'varname',out$var[[i]]$name))
for (i in 1:out$ndims) print(c('rank',i,'dimname',out$dim[[i]]$name))

	dim <- out$dim[[1]]$vals	#specify the rank of the dimension of the uni-dimensional variable you wanna extract			
	var <- ncvar_get(out, out$var[[]],start=1,count=out$dim[[1]]$len) # specify the rank of the variable and the related dimension you wanna extract;
	file <- data.frame(dim,var) #create the output file
	names(file) <- c(out$dim[[1]]$name,out$var[[]]$name)	#naming the columns of your output file;

write.csv(file, file='')	
	
# Extract a two-dimensions variable;

out <- nc_open('') #Location of your nc file;
for (i in 1:out$nvars) print(c('rank',i,'varname',out$var[[i]]$name))
for (i in 1:out$ndims) print(c('rank',i,'dimname',out$dim[[i]]$name))

valdim1<- out$dim[[1]]$vals
valdim2<- out$dim[[2]]$vals
file <- data.frame()

	for(i in 1:out$dim[[2]]$len) #loop on the shortest dimension, e.g. month;
	{
	dim2 <- rep(valdim2[i],out$dim[[1]]$len)
	var <- data.frame(ncvar_get(out,out$var[[]],start=c(i,1),count=c(1,out$dim[[1]]$len))) #specify the rank of the variable;
	M <- data.frame(valdim1,dim2,var) #merging the three columns
	names(M) <- c(out$dim[[1]]$name,out$dim[[2]]$name,out$var[[]]$name)	#naming the columns of your  file;
	file <- rbind(file,M)	#merging to the output file
	}

write.csv(file, file='')

# Extract a three-dimensions variable;

out <- nc_open('') #Location of your nc file;
for (i in 1:out$nvars) print(c('rank',i,'varname',out$var[[i]]$name))
for (i in 1:out$ndims) print(c('rank',i,'dimname',out$dim[[i]]$name))

valdim1<- out$dim[[1]]$vals
valdim2<- out$dim[[2]]$vals
valdim3<- out$dim[[3]]$vals
file <- data.frame()

for (j in 1:out$dim[[3]]$len) #loop on the shortest dimension, e.g. month;
{
	for (i in 1:out$dim[[2]]$len) #loop on the shortest dimension, e.g. month;
	{
		dim3 <- rep(valdim3[j],out$dim[[1]]$len)
		dim2 <- rep(valdim2[i],out$dim[[1]]$len)
		var <- data.frame(ncvar_get(out,out$var[[]],start=c(j,i,1),count=c(1,1,out$dim[[1]]$len))) #specify the rank of the variable;
		M <- data.frame(valdim1,dim2,dim3,var) #merging the three columns
		names(M) <- c(out$dim[[1]]$name,out$dim[[2]]$name,out$dim[[3]]$name,out$var[[]]$name)	#naming the columns of your  file;
		file <- rbind(file,M)	#merging to the output file
	}
}


write.csv(file, file='')
