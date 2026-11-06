#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/test.sh mechanical

Run a supported dvm-dos-tem test tier in the dvmdostem-dev Docker service.

The dvmdostem-dev service must already be running. Build it with
./docker-build-wrapper.sh dev and start it with:

  docker compose up -d dvmdostem-dev
EOF
}

if [[ $# -ne 1 || $1 == "--help" || $1 == "-h" ]]; then
  usage
  [[ $# -eq 1 ]] && [[ $1 == "--help" || $1 == "-h" ]] && exit 0
  exit 2
fi

case $1 in
  mechanical)
    docker compose exec -T --workdir /work dvmdostem-dev \
      pytest -q pyddt/tests/test_config.py
      #pytest -q pyddt/tests/test_config_util.py # bug in test, fix later

    docker compose exec -T --workdir /work dvmdostem-dev \
      pytest --doctest-glob "doctests_*" \
        pyddt/tests/doctests/doctests_param_util.md \
        pyddt/tests/doctests/doctests_outspec_utils.md \
        #pyddt/tests/doctests/doctests_setup_working_directory.md \ # missing data issue
        pyddt/tests/doctests/doctests_util_general.md

    docker compose exec -T --workdir /work dvmdostem-dev \
      make test
    docker compose exec -T --workdir /work dvmdostem-dev \
      ./dvmdostem-tests

    docker compose exec -T --workdir /work dvmdostem-dev \
      scons test
    docker compose exec -T --workdir /work dvmdostem-dev \
      ./dvmdostem-tests
    ;;
  *)
    usage
    exit 2
    ;;
esac
