CXX ?= c++
CXXFLAGS ?= -O2 -std=c++11 -Wall -Wextra -Wpedantic -Werror
ROOT := ../..
BUILD := $(ROOT)/build/thermokarst
.PHONY: all test clean
all: $(BUILD)/test-thermokarst $(BUILD)/test-restart-netcdf $(BUILD)/thermokarst-column
$(BUILD):
	mkdir -p $@
$(BUILD)/test-thermokarst: test_thermokarst.cpp $(ROOT)/src/Thermokarst.cpp $(ROOT)/include/Thermokarst.h $(ROOT)/include/physicalconst.h | $(BUILD)
	$(CXX) $(CXXFLAGS) test_thermokarst.cpp $(ROOT)/src/Thermokarst.cpp -o $@
$(BUILD)/thermokarst-column: $(ROOT)/experiments/thermokarst/column.cpp $(ROOT)/src/Thermokarst.cpp $(ROOT)/include/Thermokarst.h $(ROOT)/include/physicalconst.h | $(BUILD)
	$(CXX) $(CXXFLAGS) $(ROOT)/experiments/thermokarst/column.cpp $(ROOT)/src/Thermokarst.cpp -o $@
$(BUILD)/test-restart-netcdf: test_restart_netcdf.cpp $(ROOT)/src/RestartThermokarst.cpp $(ROOT)/include/RestartThermokarst.h $(ROOT)/include/RestartData.h | $(BUILD)
	$(CXX) $(CXXFLAGS) test_restart_netcdf.cpp $(ROOT)/src/RestartThermokarst.cpp -lnetcdf -o $@
test: all
	$(BUILD)/test-thermokarst $(BUILD)/test_results.csv
	$(BUILD)/test-restart-netcdf
clean:
	rm -f $(BUILD)/test-thermokarst $(BUILD)/test-restart-netcdf $(BUILD)/thermokarst-column

all: $(BUILD)/thermokarst-benchmarks
$(BUILD)/thermokarst-benchmarks: $(ROOT)/experiments/thermokarst/benchmarks.cpp $(ROOT)/src/Thermokarst.cpp $(ROOT)/include/Thermokarst.h $(ROOT)/include/physicalconst.h | $(BUILD)
	$(CXX) $(CXXFLAGS) $(ROOT)/experiments/thermokarst/benchmarks.cpp $(ROOT)/src/Thermokarst.cpp -o $@
