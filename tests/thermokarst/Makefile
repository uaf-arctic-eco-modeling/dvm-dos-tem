CXX ?= c++
CXXFLAGS ?= -O2 -std=c++11 -Wall -Wextra -Wpedantic -Werror
ROOT := ../..
BUILD := $(ROOT)/build/thermokarst
.PHONY: all test clean
all: $(BUILD)/test-thermokarst $(BUILD)/thermokarst-column $(BUILD)/thermokarst-benchmarks
$(BUILD):
	mkdir -p $@
$(BUILD)/test-thermokarst: test_thermokarst.cpp $(ROOT)/src/Thermokarst.cpp $(ROOT)/include/Thermokarst.h $(ROOT)/include/physicalconst.h | $(BUILD)
	$(CXX) $(CXXFLAGS) test_thermokarst.cpp $(ROOT)/src/Thermokarst.cpp -o $@
$(BUILD)/thermokarst-column: $(ROOT)/experiments/thermokarst/column.cpp $(ROOT)/src/Thermokarst.cpp $(ROOT)/include/Thermokarst.h $(ROOT)/include/physicalconst.h | $(BUILD)
	$(CXX) $(CXXFLAGS) $(ROOT)/experiments/thermokarst/column.cpp $(ROOT)/src/Thermokarst.cpp -o $@
$(BUILD)/thermokarst-benchmarks: $(ROOT)/experiments/thermokarst/benchmarks.cpp $(ROOT)/src/Thermokarst.cpp $(ROOT)/include/Thermokarst.h $(ROOT)/include/physicalconst.h | $(BUILD)
	$(CXX) $(CXXFLAGS) $(ROOT)/experiments/thermokarst/benchmarks.cpp $(ROOT)/src/Thermokarst.cpp -o $@
test: all
	$(BUILD)/test-thermokarst $(BUILD)/test_results.csv
clean:
	rm -f $(BUILD)/test-thermokarst $(BUILD)/thermokarst-column $(BUILD)/thermokarst-benchmarks
