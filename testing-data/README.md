# Testing Data Directory

This directory contains testing data for `dvmdostem` organized in a tiered
structure to balance repository size with testing needs.

## Overview

The `dvmdostem` model requires various input datasets (climate, soil,
vegetation) for testing and validation. To keep the repository lightweight while
enabling comprehensive testing, we use a three-tier approach:

- **`minimal/`** - Essential data, shipped with the repository (~5-10 MB)
- **`standard/`** - Datasets for thorough testing, shipped with the repository (~50-100 MB) 
- **`comprehensive/`** - Full-scale datasets for complete validation (~500+ MB)

## Directory Structure

```
testing-data/
├── README.md                      # This file
├── minimal/                       # ✅ Committed to repository
│   ├── inputs/                    # Small climate/soil datasets (1-2 years)
│   └── parameters/                # Parameter files for testing
├── standard/                      # ✅ Committed to repository
│   ├── inputs/                    # Multi-year, multi-pixel datasets for CI/testing
│   └── docs/                      # Documentation examples
│       └── example_experiment_0/  # Tutorial data

├── comprehensive/                 # ⬇️  Downloaded via script  
│   └── inputs/                    # Full spatial/temporal datasets
└── download-test-data.sh.         # Downloads standard/comprehensive data
```

## Rationale

**Why this approach?**
- **Repository Size**: Keeps git clone fast and storage efficient
- **Immediate Functionality**: Basic tests work out-of-the-box
- **Scalable Testing**: Developers/Modelers can access more data as needed
- **CI/CD Friendly**: Automated systems can download appropriate test levels
- **User-Friendly**: No complex version control tools required

## Data Tiers Explained

### Minimal Data (Always Available)
**Location**: `testing-data/minimal/` ✅ *Committed to repository*

- **Purpose**: Basic functionality testing, code development, unit tests
- **Size**: < 10 MB total
- **Contents**:
  - 1-2 years of climate data for small spatial domains (2x2 or 5x5 pixels)
  - Essential parameter files
  - Run masks for quick tests
  - Basic unit test data
- **Use Cases**:
  - Local development and debugging
  - Quick smoke tests
  - Unit tests in `pyddt/tests/`
  - Immediate functionality validation

### Standard Data (Download Required)
**Location**: `testing-data/standard/` ✅ *Committed to repository*

- **Purpose**: Comprehensive testing, CI/CD validation, documentation examples
- **Size**: ~50-100 MB
- **Contents**:
  - Multi-year climate sequences (10s to 100s of years)
  - Small spatial domains (10s to 100s of pixels)
  - Full parameter sets for common CMTs
  - Documentation example data (`example_experiment_0`) and example outputs
- **Use Cases**:
  - Continuous integration testing
  - Pre-release validation
  - Development of new features
  - Documentation tutorials and examples
  - Regression testing

### Comprehensive Data (Download Required)
**Location**: `testing-data/comprehensive/` ⬇️ *Downloaded via script*

- **Purpose**: Full model validation, performance testing
- **Size**: 500+ MB
- **Contents**:
  - Full temporal sequences (50+ years)
  - Large spatial domains (50x50+ pixels)
  - Multiple sites and scenarios
- **Use Cases**:
  - Publication-quality validation
  - Performance benchmarking
  - Spatial scaling tests
  - Full model integration testing

## Using the Test Data

### For Basic Development (Minimal Data)
All basic tests and development work uses the `minimal/` data automatically:

```bash
# Clone and immediately run basic tests
git clone https://github.com/ua-snap/dvm-dos-tem.git
cd dvm-dos-tem
docker compose up -d dvmdostem-dev
docker compose exec dvmdostem-dev bash

# Basic tests work immediately
python -m pytest pyddt/tests/
python -m doctest pyddt/tests/doctests/doctests_basic.md
```

### For Documentation Examples
Documentation examples (like `example_experiment_0`) use data from `testing-data/standard/`:


### For Extended Testing (Standard/Comprehensive Data)
When you need more extensive testing data:

```bash

# Download comprehensive testing data (500+ MB)  
./testing-data/scripts/download-test-data.sh comprehensive

```


## For CI/CD Systems

Continuous integration can selectively download data based on test requirements:

```yaml
# Example GitHub Actions
- name: Download standard test data
  run: |
    ./testing-data/scripts/download-test-data.sh standard
    
- name: Run comprehensive tests  
  run: |
    python -m pytest pyddt/tests/ --test-level=standard
```

## Data Management Commands

```bash
# Check what data is available locally
ls -la testing-data/*/

# Download comprehensive data (for validation)
./testing-data/scripts/download-test-data.sh comprehensive

# Clean downloaded data (keeps minimal/)
./testing-data/scripts/download-test-data.sh clean

# Check data sizes
du -sh testing-data/*/
```

## Contributing Test Data

When adding new test cases:

1. **Small data** (< 1MB): Add to `testing-data/minimal/`
2. **Medium data** (1-50MB): Coordinate with maintainers for `standard/` 
3. **Large data** (> 50MB): Coordinate with maintainers for `comprehensive/`

## Notes for Developers

- **Docker Assumption**: All tests assume Docker execution with `/work` as repo root
- **Path Consistency**: Use `/work/testing-data/minimal/` or `/work/testing-data/standard` paths in committed tests
- **Documentation**: Update this README when adding new data tiers or requirements
