# Basic dvm-dos-tem Makefile 

# Add compiler flag for enabling floating point exceptions:
# -DBSD_FPE for BSD (OSX)
# -DGNU_FPE for various Linux

CC=g++
CFLAGS=-c -ansi -g -gdwarf-2 -std=c++11 -fPIC -DBOOST_ALL_DYN_LINK -Werror # -W -Wall -Werror -Wno-system-headers
LIBS=-lnetcdf -lboost_system -lboost_filesystem \
-lboost_program_options -lboost_thread -lboost_log -ljsoncpp -lpthread -lreadline -llapacke

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
		src/Thermokarst.o \
		src/ThermokarstIntegration.o \
		src/RestartThermokarst.o \
		src/TEMLogger.o \
		src/CalController.o \
		src/ArgHandler.o \
		src/TEMUtilityFunctions.o \
		src/Climate.o \
		src/OutputEstimate.o \
		src/Runner.o \
		src/BgcData.o \
		src/CohortData.o \
		src/EnvData.o \
		src/EnvDataDly.o \
		src/FireData.o \
		src/RestartData.o \
		src/WildFire.o \
		src/DoubleLinkedList.o \
		src/Ground.o \
		src/MineralInfo.o \
		src/Moss.o \
		src/Organic.o \
		src/Snow.o \
		src/SoilParent.o \
		src/Vegetation.o \
		src/CohortLookup.o \
		src/Cohort.o \
		src/Integrator.o \
		src/ModelData.o \
		src/Richards.o \
		src/Snow_Env.o \
		src/Soil_Bgc.o \
		src/Soil_Env.o \
		src/SoilParent_Env.o \
		src/Stefan.o \
		src/TemperatureUpdator.o \
		src/CrankNicholson.o \
		src/tbc-debug-util.o \
		src/Vegetation_Bgc.o \
		src/Vegetation_Env.o \
		src/Layer.o \
		src/MineralLayer.o \
		src/MossLayer.o \
		src/OrganicLayer.o \
		src/ParentLayer.o \
		src/SnowLayer.o \
		src/SoilLayer.o

OBJECTS =	Thermokarst.o \
		ThermokarstIntegration.o \
		RestartThermokarst.o \
		ArgHandler.o \
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
		FireData.o \
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


# Set if not set from environment or command line...
# CAUTION! You could override this from command line in a totally
# meaningless way. But this is useful in a container build environment where
# we might not be in a git repo and therefore can't call git describe...
GIT_SHA ?= $(shell git describe --abbrev=6 --dirty --always --tags)


TEMOBJ = obj/TEM.o

dvm: $(SOURCES) $(TEMOBJ)
	$(CC) $(SITE_SPECIFIC_LINK_FLAGS) -o $(APPNAME) $(INCLUDES) $(addprefix obj/, $(OBJECTS)) $(TEMOBJ) $(LIBDIR) $(LIBS) $(MPILFLAGS) $(OMPLFLAGS)


lib: $(SOURCES) 
	$(CC) -o libTEM.so -shared $(INCLUDES) $(addprefix obj/, $(OBJECTS)) $(LIBDIR) $(LIBS) $(MPILFLAGS) $(OMPLFLAGS)

CFLAGS += -DGIT_SHA=\"$(GIT_SHA)\"

.cpp.o:
	$(CC) $(CFLAGS) $(MPICFLAGS) $(OMPCFLAGS) $(INCLUDES) $(MPIINCLUDES) $< -o obj/$(notdir $@)

clean:
	rm -f $(OBJECTS) $(APPNAME) TEM.o libTEM.so* *~ obj/*


# Dependency-light, experimental thermokarst column (not the production driver).
.PHONY: thermokarst thermokarst-test thermokarst-production-validation thermokarst-active-thaw-validation thermokarst-seasonal-diagnostics-validation thermokarst-bgc-validation thermokarst-fire-validation thermokarst-fire-recovery-validation thermokarst-observed-fire-validation thermokarst-historic-projection-validation thermokarst-barrow-validation thermokarst-barrow-validation-phase0 thermokarst-barrow-alt-calibration thermokarst-barrow-alt-calibrate thermokarst-barrow-diagnostic-plots thermokarst-barrow-validation-phase1 thermokarst-barrow-validation-phase2 thermokarst-anaktuvuk-validation thermokarst-anaktuvuk-phase1-validation thermokarst-anaktuvuk-climate-calibration thermokarst-anaktuvuk-fire-calibration thermokarst-anaktuvuk-phase2-validation thermokarst-anaktuvuk-plot-diagnostics thermokarst-eml-validation thermokarst-eml-fetch-data thermokarst-eml-fetch-gps thermokarst-eml-climate thermokarst-eml-phase1-validation thermokarst-eml-phase2-validation thermokarst-eml-fetch-wtd thermokarst-eml-phase3-validation thermokarst-eml-phase4-validation thermokarst-samoylov-validation thermokarst-samoylov-phase1-validation thermokarst-samoylov-phase2-validation thermokarst-samoylov-gswp3-climate
thermokarst:
	$(MAKE) -C tests/thermokarst all
thermokarst-test:
	$(MAKE) -C tests/thermokarst test

thermokarst-production-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/production_validation.py --binary ./dvmdostem

thermokarst-active-thaw-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/active_thaw_validation.py --binary ./dvmdostem

thermokarst-seasonal-diagnostics-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/seasonal_diagnostics_validation.py --binary ./dvmdostem

thermokarst-bgc-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/bgc_coupling_validation.py --binary ./dvmdostem

thermokarst-fire-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/fire_topology_validation.py --binary ./dvmdostem

thermokarst-fire-recovery-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/fire_recovery_validation.py --binary ./dvmdostem

thermokarst-observed-fire-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/observed_fire_validation.py --binary ./dvmdostem

thermokarst-historic-projection-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/historic_projection_validation.py --binary ./dvmdostem

thermokarst-barrow-validation-phase0:
	.venv-thermokarst/bin/python experiments/thermokarst/barrow_validation.py --binary ./dvmdostem --phase 0

thermokarst-barrow-alt-calibration:
	.venv-thermokarst/bin/python experiments/thermokarst/barrow_validation.py --binary ./dvmdostem --phase A

thermokarst-barrow-alt-calibrate:
	.venv-thermokarst/bin/python experiments/thermokarst/barrow_validation.py --binary ./dvmdostem --phase A --calibrate

thermokarst-barrow-diagnostic-plots:
	.venv-thermokarst/bin/python experiments/thermokarst/barrow_validation.py --binary ./dvmdostem --diagnostic-plots --reuse

thermokarst-barrow-validation-phase1:
	.venv-thermokarst/bin/python experiments/thermokarst/barrow_validation.py --binary ./dvmdostem --phase 1

thermokarst-barrow-validation-phase2:
	.venv-thermokarst/bin/python experiments/thermokarst/barrow_validation.py --binary ./dvmdostem --phase 2

thermokarst-barrow-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/barrow_validation.py --binary ./dvmdostem --phase all

thermokarst-anaktuvuk-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --phase 0 --binary ./dvmdostem

thermokarst-anaktuvuk-phase1-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --phase 1 --binary ./dvmdostem --allow-fail

thermokarst-anaktuvuk-climate-calibration:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --calibrate-climate --binary ./dvmdostem

thermokarst-anaktuvuk-fire-calibration:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --calibrate-fire --binary ./dvmdostem

thermokarst-anaktuvuk-phase2-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --phase 2 --binary ./dvmdostem --allow-fail

thermokarst-anaktuvuk-spinup:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --stage spinup --binary ./dvmdostem

thermokarst-anaktuvuk-transient:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --stage transient --binary ./dvmdostem --climate-end-year 2023 --paired-only --allow-fail

thermokarst-anaktuvuk-plot-diagnostics:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --phase 1 --plot-diagnostics --climate-end-year 2023 --output experiments/thermokarst/anaktuvuk_phase1_validation_results

thermokarst-anaktuvuk-max-organic-burn-transient:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --stage transient --binary ./dvmdostem --climate-end-year 2023 --paired-only --max-organic-burn --allow-fail

thermokarst-anaktuvuk-max-organic-burn-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --phase 1 --binary ./dvmdostem --climate-end-year 2023 --paired-only --max-organic-burn --allow-fail

thermokarst-anaktuvuk-max-organic-burn-plot-diagnostics:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --plot-diagnostics --max-organic-burn --climate-end-year 2023 --output experiments/thermokarst/anaktuvuk_max_organic_burn_results

thermokarst-anaktuvuk-ice-calibration:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --calibrate-ice --binary ./dvmdostem --climate-end-year 2023 --allow-fail

thermokarst-anaktuvuk-bracket-climate-calibration:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --calibrate-climate-bracket --binary ./dvmdostem --climate-end-year 2023

thermokarst-anaktuvuk-bracket-ice-calibration:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --calibrate-ice --ice-bracket --binary ./dvmdostem --climate-end-year 2023 --allow-fail

thermokarst-anaktuvuk-ice-bracket-transient:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --stage transient --binary ./dvmdostem --climate-end-year 2023 --paired-only --ice-bracket --allow-fail

thermokarst-anaktuvuk-ice-bracket-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --phase 1 --binary ./dvmdostem --climate-end-year 2023 --paired-only --ice-bracket --allow-fail

thermokarst-anaktuvuk-ice-bracket-plot-diagnostics:
	.venv-thermokarst/bin/python experiments/thermokarst/anaktuvuk_validation.py --plot-diagnostics --ice-bracket --climate-end-year 2023 --output experiments/thermokarst/anaktuvuk_ice_bracket_results

thermokarst-eml-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation.py --binary ./dvmdostem

thermokarst-eml-fetch-data:
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation/fetch_bnz453.py

thermokarst-eml-fetch-gps:
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation/fetch_bnz729.py

thermokarst-eml-climate: thermokarst-eml-fetch-data
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation/build_healy_climate.py --fetch

thermokarst-eml-phase1-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation.py --binary ./dvmdostem --phase 1 --fetch --allow-fail

thermokarst-eml-phase2-validation: thermokarst-eml-fetch-data thermokarst-eml-fetch-gps
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation.py --binary ./dvmdostem --phase 2 --fetch --recalibrate --allow-fail

thermokarst-eml-fetch-wtd:
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation/fetch_bnz554.py

thermokarst-eml-phase3-validation: thermokarst-eml-fetch-data thermokarst-eml-fetch-gps thermokarst-eml-fetch-wtd
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation.py --binary ./dvmdostem --phase 3 --fetch --allow-fail

thermokarst-eml-phase4-validation: thermokarst-eml-fetch-data thermokarst-eml-fetch-gps thermokarst-eml-fetch-wtd
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation.py --binary ./dvmdostem --phase 4 --fetch --recalibrate --allow-fail

thermokarst-eml-phase5-validation: thermokarst-eml-fetch-data thermokarst-eml-fetch-gps thermokarst-eml-fetch-wtd
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation.py --binary ./dvmdostem --phase 5 --fetch --recalibrate --allow-fail

thermokarst-eml-thermal-plots:
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation.py --binary ./dvmdostem --plot-thermal --output experiments/thermokarst/eml_phase4_validation_results

thermokarst-eml-climate-plots:
	.venv-thermokarst/bin/python experiments/thermokarst/eml_validation.py --plot-climate --output experiments/thermokarst/eml_phase4_validation_results

thermokarst-samoylov-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/samoylov_validation.py --binary ./dvmdostem

thermokarst-samoylov-phase1-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/samoylov_validation.py --binary ./dvmdostem --phase 1

thermokarst-samoylov-fetch-data:
	.venv-thermokarst/bin/python experiments/thermokarst/samoylov_validation/process_boike_data.py
	.venv-thermokarst/bin/python experiments/thermokarst/samoylov_validation/fetch_gswp3_samoylov.py

thermokarst-samoylov-hydrology-tune:
	.venv-thermokarst/bin/python experiments/thermokarst/samoylov_validation/hydrology_tune.py --binary ./dvmdostem

thermokarst-samoylov-gswp3-climate: thermokarst-samoylov-fetch-data
	.venv-thermokarst/bin/python experiments/thermokarst/samoylov_validation/build_gswp3_climate.py --fetch --output experiments/thermokarst/samoylov_validation/data/samoylov-gswp3-boike-climate.nc

thermokarst-samoylov-phase2-validation:
	.venv-thermokarst/bin/python experiments/thermokarst/samoylov_validation.py --binary ./dvmdostem --phase 2 $(if $(RUN),--run,)
