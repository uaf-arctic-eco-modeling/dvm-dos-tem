#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/../.."
mkdir -p build/thermokarst
"${CXX:-c++}" -std=c++11 -O1 -g -Wall -Wextra -Wpedantic -Werror \
  -fsanitize="${SANITIZERS:-undefined}" -fno-sanitize-recover=all -fno-omit-frame-pointer \
  tests/thermokarst/test_thermokarst.cpp src/Thermokarst.cpp \
  -o build/thermokarst/test-thermokarst-sanitized
build/thermokarst/test-thermokarst-sanitized build/thermokarst/sanitizer_results.csv
