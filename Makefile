# Basic dvm-dos-tem Makefile 

# Add compiler flag for enabling floating point exceptions:
# -DBSD_FPE for BSD (OSX)
# -DGNU_FPE for various Linux

CC=g++
CFLAGS=-c -Werror -ansi -g -fPIC -DBOOST_ALL_DYN_LINK
LIBS=-lnetcdf -lboost_system -lboost_filesystem \
-lboost_program_options -lboost_thread -lboost_log -ljsoncpp -lpthread -lreadline

USEMPI = false
USEOMP = false

ifeq ($(USEMPI),true)
  MPIINCLUDES = $(shell mpic++ -showme:compile)
  MPICFLAGS = -DWITHMPI
  MPILFLAGS = $(shell mpic++ -showme:link)
else
  # do nothing..
endif

ifeq ($(USEOMP),true)
  OMPCFLAGS = -fopenmp
  OMPLFLAGS = -fopenmp
else
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
		src/Climate.o \
		src/OutputEstimate.o \
		src/Runner.o \
		src/data/BgcData.o \
		src/data/CohortData.o \
		src/data/EnvData.o \
		src/data/EnvDataDly.o \
		src/data/FirData.o \
		src/data/RestartData.o \
		src/disturb/WildFire.o \
		src/ecodomain/DoubleLinkedList.o \
		src/ecodomain/Ground.o \
		src/ecodomain/horizon/MineralInfo.o \
		src/ecodomain/horizon/Moss.o \
		src/ecodomain/horizon/Organic.o \
		src/ecodomain/horizon/Snow.o \
		src/ecodomain/horizon/SoilParent.o \
		src/ecodomain/Vegetation.o \
		src/lookup/CohortLookup.o \
		src/runmodule/Cohort.o \
		src/runmodule/Integrator.o \
		src/ModelData.o \
		src/snowsoil/Richards.o \
		src/snowsoil/Snow_Env.o \
		src/snowsoil/Soil_Bgc.o \
		src/snowsoil/Soil_Env.o \
		src/snowsoil/SoilParent_Env.o \
		src/snowsoil/Stefan.o \
		src/snowsoil/TemperatureUpdator.o \
		src/util/CrankNicholson.o \
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

OBJECTS =	ArgHandler.o \
		TEMLogger.o \
		CalController.o \
		TEMUtilityFunctions.o \
		Climate.o \
		OutputEstimate.o \
		Runner.o \
		BgcData.o \
		CohortData.o \
		EnvData.o \
		EnvDataDly.o \
		FirData.o \
		RestartData.o \
		WildFire.o \
		DoubleLinkedList.o \
		Ground.o \
		MineralInfo.o \
		Moss.o \
		Organic.o \
		Snow.o \
		SoilParent.o \
		Vegetation.o \
		CohortLookup.o \
		Cohort.o \
		Integrator.o \
		ModelData.o \
		Richards.o \
		Snow_Env.o \
		Soil_Bgc.o \
		Soil_Env.o \
		SoilParent_Env.o \
		Stefan.o \
		CrankNicholson.o \
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


GIT_SHA := $(shell git describe --abbrev=6 --dirty --always --tags)

TEMOBJ = obj/TEM.o

dvm: $(SOURCES) $(TEMOBJ)
	$(CC) -o $(APPNAME) $(INCLUDES) $(addprefix obj/, $(OBJECTS)) $(TEMOBJ) $(LIBDIR) $(LIBS) $(MPILFLAGS) $(OMPLFLAGS)


lib: $(SOURCES) 
	$(CC) -o libTEM.so -shared $(INCLUDES) $(addprefix obj/, $(OBJECTS)) $(LIBDIR) $(LIBS) $(MPILFLAGS) $(OMPLFLAGS)

CFLAGS += -DGIT_SHA=\"$(GIT_SHA)\"

.cpp.o:
	$(CC) $(CFLAGS) $(MPICFLAGS) $(OMPCFLAGS) $(INCLUDES) $(MPIINCLUDES) $< -o obj/$(notdir $@)

clean:
	rm -f $(OBJECTS) $(APPNAME) TEM.o libTEM.so* *~ obj/*

