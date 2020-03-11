import arcpy, os  
from arcpy import env  
from arcpy.sa import *  

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

#Set the mask of the IEM area
iem = "C:\\Users\Helene\Desktop\FIRE\iem01.tif"

#Set the workspace, and the extent and snap area so the rasters aline with the IEM grid
env.workspace = env.scratchWorkspace = "C:\\Users\Helene\Desktop\FIRE"
arcpy.env.snapRaster = "iem01.tif"
arcpy.env.extent = "iem01.tif"
arcpy.env.nodata = "PROMOTION"

#####     Annual loop
for i in range (1950 , 2017):
	year = format(i, '04d')
	where = '"YEAR2" = ' + "%s" %year
	#The original shapefile contains the historical fire scares for Alaska (https://afsmaps.blm.gov/imf_firehistory/imf.jsp?site=firehistory) 
	#and Western Canada (http://cwfis.cfs.nrcan.gc.ca/datamart/datarequest/nfdbpoly)
	inpoly = "Z:\Downloads\IEM_Input\Y%s.shp" % (year)
	outrst_yr = "Z:\Downloads\IEM_Input\Y%s_year.tif" % (year)
	outrst_mth = "Z:\Downloads\IEM_Input\Y%s_month.tif" % (year)
	outrst_day = "Z:\Downloads\IEM_Input\Y%s_day.tif" % (year)
	outrst_size = "Z:\Downloads\IEM_Input\Y%s_size.tif" % (year)
	#Select only the fire scares  polygons from the year i
	arcpy.Select_analysis("Z:\Downloads\IEM_Input\IEM_FireHistory_poly.shp",inpoly, where)
	#Convert the polygons to raster for the year of the fire
	arcpy.PolygonToRaster_conversion(inpoly,"YEAR2",outrst_yr,"MAXIMUM_AREA","NONE",iem)
	#Convert the polygons to raster for the month of the fire
	arcpy.PolygonToRaster_conversion(inpoly,"MONTH2",outrst_mth,"MAXIMUM_AREA","NONE",iem)
	#Convert the polygons to raster for the day of the fire
	arcpy.PolygonToRaster_conversion(inpoly,"DAY2",outrst_day,"MAXIMUM_AREA","NONE",iem)
	#Convert the polygons to raster for the size of the fire
	arcpy.PolygonToRaster_conversion(inpoly,"YEAR2",outrst_size,"MAXIMUM_AREA","NONE",iem)


#####     Compute FRI based on the 1950-1979 fire regime.

#Create binary rasters for annual fire scares based on the year rasters and store them in a temporary directory
for i in range (1950 , 1980):
	year = format(i, '04d')
	inraster = "Z:\Downloads\IEM_Input\Y%s_year.tif" % (year)
	outraster = "C:\\Users\Helene\Desktop\FIRE\TMP\Y%s_tmp.tif" % (year)
	ras = Raster(inraster)
	#Conditional statement to replace year value by 1
	out = Con(ras >= 1900, 1,0)
	#Apply and save the raster
	out.save(outraster)

#List the binary rasters of the fire scares  
env.workspace = r"C:\Users\Helene\Desktop\FIRE\TMP"  
rasterList  = arcpy.ListRasters("*")  
#Execute CellStatistics  to sum up all the binary rasters
outCellStatistics = CellStatistics(rasterList, "SUM", "DATA")  
#Save the output   
outCellStatistics.save("C:\\Users\Helene\Desktop\FIRE\sumRast.tif")  


#Conduct the focal analysis to sum all pixels that burned between 1950 and 1979 included across a block of 100 km centered on evert pixel
env.workspace = env.scratchWorkspace = "C:\\Users\Helene\Desktop\FIRE"
inrst = Raster("sumRast.tif")
#Size of the rectangle the FRI will be computed from
block = NbrRectangle(50, 50, "CELL")
#Execute FocalStatistics
outFocalStatistics = FocalStatistics(inrst, block, "SUM","DATA")
#Save the output 
outFocalStatistics.save("AreaBurn_10km.tif")
#Compute the FRI from the focal analysis
focal = Raster("AreaBurn_10km.tif")
fri = SetNull("iem01.tif" == 0,Con(IsNull(focal),2000,Con(Float(30.000 / (focal / (50.0 * 50.0))) > 2000,2000,Int(Float(30.000 / (focal / (50.0 * 50.0)))))))
#Apply and save the raster
fri.save("FRI.tif")





















