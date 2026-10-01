#!/bin/bash

echo "Running with some settings..."

echo "Setting up a calibration directives file...."
# Need to do this so as to be able to turn off the "post-warmup-pause"
# for running in an automated environment...
cat <<EOF > config/calibration_directives.txt
{
  "calibration_autorun_settings": {
    //"quitat": 1500,
    "10": ["dsl on", "nfeed on", "dsb on"],
    "pwup": false // "post warm up pause", [true | false], boolean
  }
}
EOF

echo "Run the model..."
./dvmdostem --log-level note --pre-run-yrs 10 --max-eq 100 --cal-mode
