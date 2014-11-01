# Basic dvm-dos-tem Makefile 

CC=g++
CFLAGS=-c -Werror -ansi -g -fPIC -DBOOST_ALL_DYN_LINK
LIBS=-lnetcdf_c++ -lnetcdf -lboost_system -lboost_filesystem \
-lboost_program_options -lboost_thread -lboost_log -ljsoncpp -lpthread -lreadline
USEMPI = false

ifeq ($(USEMPI),true)
  MPIINCLUDES = $(shell mpic++ -showme:compile)
  MPICFLAGS = -DWITHMPI
  MPILFLAGS = $(shell mpic++ -showme:link)
else
  # do nothing..
endif

# Create a build directory for .o object files.
# Crude because this gets run everytime the Makefile
# is parsed. But it works.
$(shell mkdir -p obj)

APPNAME=dvmdostem
LIBDIR=$(SITE_SPECIFIC_LIBS)
INCLUDES=$(SITE_SPECIFIC_INCLUDES)
SOURCES= 	src/TEM.o \
		src/TEMLogger.o \
		src/CalController.o \
		src/ArgHandler.o \
		src/TEMUtilityFunctions.o \
		src/assembler/RunCohort.o \
		src/assembler/RunGrid.o \
		src/assembler/Runner.o \
		src/assembler/RunRegion.o \
		src/atmosphere/Atmosphere.o \
		src/atmosphere/AtmosUtil.o \
		src/data/BgcData.o \
		src/data/CohortData.o \
		src/data/EnvData.o \
		src/data/EnvDataDly.o \
		src/data/FirData.o \
		src/data/GridData.o \
		src/data/OutDataRegn.o \
		src/data/RegionData.o \
		src/data/RestartData.o \
		src/disturb/WildFire.o \
		src/ecodomain/DoubleLinkedList.o \
		src/ecodomain/Ground.o \
		src/ecodomain/horizon/Mineral.o \
		src/ecodomain/horizon/Moss.o \
		src/ecodomain/horizon/Organic.o \
		src/ecodomain/horizon/Snow.o \
		src/ecodomain/horizon/SoilParent.o \
		src/ecodomain/Vegetation.o \
		src/input/GridInputer.o \
		src/input/RegionInputer.o \
		src/input/RestartInputer.o \
		src/lookup/CohortLookup.o \
		src/lookup/SoilLookup.o \
		src/output/BgcOutputer.o \
		src/output/ChtOutputer.o \
		src/output/EnvOutputer.o \
		src/output/RegnOutputer.o \
		src/output/RestartOutputer.o \
		src/runmodule/Cohort.o \
		src/runmodule/Grid.o \
		src/runmodule/Integrator.o \
		src/runmodule/ModelData.o \
		src/runmodule/OutRetrive.o \
		src/runmodule/Region.o \
		src/runmodule/Timer.o \
		src/snowsoil/Richards.o \
		src/snowsoil/Snow_Env.o \
		src/snowsoil/Soil_Bgc.o \
		src/snowsoil/Soil_Env.o \
		src/snowsoil/SoilParent_Env.o \
		src/snowsoil/Stefan.o \
		src/snowsoil/TemperatureUpdator.o \
		src/util/CrankNicholson.o \
		src/util/Interpolator.o \
		src/util/tbc-debug-util.o \
		src/vegetation/Vegetation_Bgc.o \
		src/vegetation/Vegetation_Env.o \
		src/ecodomain/layer/Layer.o \
		src/ecodomain/layer/MineralLayer.o \
		src/ecodomain/layer/MossLayer.o \
		src/ecodomain/layer/OrganicLayer.o \
		src/ecodomain/layer/ParentLayer.o \
		src/ecodomain/layer/SnowLayer.o \
		src/ecodomain/layer/SoilLayer.o
ifeq ($(USEMPI),true)
SOURCES += src/parallel-code/Master.o \
		src/parallel-code/Slave.o
endif

OBJECTS =	ArgHandler.o \
		TEMLogger.o \
		CalController.o \
		TEMUtilityFunctions.o \
		RunCohort.o \
		RunGrid.o \
		Runner.o \
		RunRegion.o \
		Atmosphere.o \
		AtmosUtil.o \
		BgcData.o \
		CohortData.o \
		EnvData.o \
		EnvDataDly.o \
		FirData.o \
		GridData.o \
		OutDataRegn.o \
		RegionData.o \
		RestartData.o \
		WildFire.o \
		DoubleLinkedList.o \
		Ground.o \
		Mineral.o \
		Moss.o \
		Organic.o \
		Snow.o \
		SoilParent.o \
		Vegetation.o \
		GridInputer.o \
		RegionInputer.o \
		RestartInputer.o \
		CohortLookup.o \
		SoilLookup.o \
		BgcOutputer.o \
		ChtOutputer.o \
		EnvOutputer.o \
		RegnOutputer.o \
		RestartOutputer.o \
		Cohort.o \
		Grid.o \
		Integrator.o \
		ModelData.o \
		OutRetrive.o \
		Region.o \
		Timer.o \
		Richards.o \
		Snow_Env.o \
		Soil_Bgc.o \
		Soil_Env.o \
		SoilParent_Env.o \
		Stefan.o \
		CrankNicholson.o \
		Interpolator.o \
		tbc-debug-util.o \
		Vegetation_Bgc.o \
		Vegetation_Env.o \
		Layer.o \
		MineralLayer.o \
		MossLayer.o \
		OrganicLayer.o \
		ParentLayer.o \
		SnowLayer.o \
		SoilLayer.o \
		TemperatureUpdator.o
ifeq ($(USEMPI),true)
OBJECTS += Master.o \
		Slave.o
endif

TEMOBJ = obj/TEM.o

dvm: $(SOURCES) $(TEMOBJ)
	$(CC) -o $(APPNAME) $(INCLUDES) $(addprefix obj/, $(OBJECTS)) $(TEMOBJ) $(LIBDIR) $(LIBS) $(MPILFLAGS)

lib: $(SOURCES) 
	$(CC) -o libTEM.so -shared $(INCLUDES) $(addprefix obj/, $(OBJECTS)) $(LIBDIR) $(LIBS) $(MPILFLAGS)

.cpp.o:
	$(CC) $(CFLAGS) $(MPICFLAGS) $(INCLUDES) $(MPIINCLUDES) $< -o obj/$(notdir $@)

clean:
	rm -f $(OBJECTS) $(APPNAME) TEM.o libTEM.so* *~ obj/*

