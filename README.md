README for dvm-dos-tem
===========================================

[![DOI](https://zenodo.org/badge/4579979.svg)](https://zenodo.org/badge/latestdoi/4579979)
[![Slack](https://img.shields.io/badge/slack-login-green.svg)](https://arctic-eco-modeling.slack.com) 

The dvm-dos-tem (`dvmdostem`) model is a process based bio-geo-chemical
ecosystem model that focuses on C and N dynamics as well as soil thermal
dynamics in high latitude ecosystems.

For more information see the [User Guide](https://uaf-arctic-eco-modeling.github.io/dvm-dos-tem/index.html).

For questions and to get involved please see the [Github Issues](https://uaf-arctic-eco-modeling.github.io/dvm-dos-tem/issues) and [Github Discussions](https://uaf-arctic-eco-modeling.github.io/dvm-dos-tem/discussions).

> [!NOTE]
> **Whats with the name?** `dvm-dos-tem` is short for "**D**ynamic
> **V**egetation \[**M**odel\] **D**ynamic **O**rganic **S**oil **T**errestrial
> **E**cosystem **M**odel". Orignally the model was simply "TEM", and as more
> logic and capabilities have been added, the name has grown. We still
> frequently use simply "TEM" because it is less cumbersome for writing and
> typing. In most context TEM, dvmdostem, dvm-dos-tem, DVM-DOS-TEM and DMVDOSTEM
> are synonomous and can be used interchangably.


## Quickstart

For users who have Docker and Git installed. 

More details are available in the [User Guide - Basic Model Setup and Run](https://uaf-arctic-eco-modeling.github.io/dvm-dos-tem/examples_and_tutorials/basic_model_run.html#basic-model-setup-and-run).

The default settings will run the model in the source code directory, using the
sample data that is included with the repository in the ``demo-data/`` directory.
The run will output a single variable (GPP), and will run for 2 pixels.

- Clone the repository (``git clone https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem.git``).
- Change into directory (``cd dvm-dos-tem``).
- Get some input data (optional).
- Make Docker usable by non-root user (optional).
- Build Docker images (``./docker-build-wrapper.sh cpp-dev && ./docker-build-wrapper.sh dev``).
- Setup your environment variables in ``.env`` file for ``V_TAG``, ``DDT_INPUT_CATALOG``, and ``DDT_WORKFLOWS`` (optional).
- Start Docker containers (``V_TAG=$(git describe) docker compose up -d dvmdostem-dev``).
- Obtain shell in container (``docker compose exec dvmdostem-dev bash``)
- Compile code (``develop@56ef79004e31:/work$ make``)
- Setup working directory (optional).
- Change into working directory (optional) .
- Adjust as needed (optional):
   - Your run mask (``run-mask.nc``)
   - The outputs you would like to generate (``output_spec.csv``)
   - Any other configuration items (``config.js``)
   - Any custom parameters (``parameters/``)
   - Any custom target data (``calibration/calibration_targets.py``).
- Start the model run (``develop@56ef79004e31:/work$ ./dvmdostem --log-level monitor -p 100 -e 1000 -s 250 -t 115 -n 85``).
- Analyze run (``develop@56ef79004e31:/work$ ./scripts/plot_output_var.py --yx 0 0 --file output/GPP_yearly_tr.nc``).
![GPP_plot_output_var](https://github.com/user-attachments/assets/678be9a7-2e48-479e-ae27-1a96c95da7be)


> [!WARNING]
> Sept 2022 - We are in the process of updating the entire documentation
> system. There is still info scattered across this README, the wiki, a Google
> Doc and the Sphinx system but we are working on consolidating the info into 
> primarily the Sphinx system (the User Guide).
