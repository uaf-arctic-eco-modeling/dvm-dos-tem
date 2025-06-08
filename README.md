README for dvm-dos-tem
===========================================

[![DOI](https://zenodo.org/badge/4579979.svg)](https://zenodo.org/badge/latestdoi/4579979)
[![Slack](https://img.shields.io/badge/slack-login-green.svg)](https://arctic-eco-modeling.slack.com) 

The dvm-dos-tem (`dvmdostem`) model is a process based bio-geo-chemical
ecosystem model that focuses on C and N cycles, vegetation dynamics and soil
thermal dynamics in high latitude ecosystems.

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

For users who have Docker and Git installed and some familiarity with the 
command line.

More details are available in the [User Guide - Basic Model Setup and Run](https://uaf-arctic-eco-modeling.github.io/dvm-dos-tem/examples_and_tutorials/basic_model_run.html#basic-model-setup-and-run).

> [!TIP]
> These instructions should work for users with [Podman](https://podman.io)
> rather than Docker, but several additional steps may be necessary to ensure
> that Podman can run with non-root access. See this
> [issue](https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem/issues/776)
> for more information.

The settings shown here will use the input data that is shipped with the code in the
repository's ``demo-data/`` directory. The run will output a single variable (GPP), 
and will run for 2 pixels.

Clone the repository and change into the directory:

    $ git clone https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem.git
    $ cd dvm-dos-tem

Make yourself locations for input data and your modeling workflows. We don't
actually use the input directory for this quickstart, but creating it and setting
the ``env`` variable below prevents some warnings.

    $ mkdir -p /home/whoever/my-stuff/input
    $ mkdir -p /home/whoever/my-stuff/workflows

On some systems you will need to make Docker usable by non-root users. [See here](https://askubuntu.com/questions/477551/how-can-i-use-docker-without-sudo).

Build Docker images. For this demo we only build 2 of the images. For your needs
you might want to build the other images. See ``./docker-build-wrapper.sh --help`` for
more info.

    $ ./docker-build-wrapper.sh cpp-dev
    $ ./docker-build-wrapper.sh dev
  
Setup your environment variables ``V_TAG``, ``DDT_INPUT_CATALOG``, and ``DDT_WORKFLOWS``.
You can do this in a ``.env`` file, your ``.bashrc``, or by exporting them to your shell.
For example using the ``.env`` file:

    $ echo "DDT_INPUT_CATALOG=/home/whoever/my-stuff/input" >> .env
    $ echo "DDT_WORKFLOWS=/home/whoever/my-stuff/workflows" >> .env
    $ echo "V_TAG=$(git describe)" >> .env

Start the Docker containers:

    $ docker compose up -d dvmdostem-dev

Obtain a shell in the container:

    $ docker compose exec dvmdostem-dev bash

Compile the code:

    develop@56ef79004e31:/work$ make

Setup a working directory for your model run and change into it. The ``setup_working_directory.py``
script bootstraps a new directory to hold your model run. This includes a few configuraiton files
and a folder for the outputs.

    devleop@56ef79004e31:/work$ setup_working_directory.py --input-data-path demo-data /data/workflows/sample_run
    devleop@56ef79004e31:/work$ cd /data/workflows/sample_run

Adjust run mask, config, outputs as necessary. The default settings should
run 1 or 2 pixels and produce outputs for GPP. There are more tools provided in the
``scripts/`` directory for working with the config file, run mask, output specificaitons
and parameters.

Start the model run:

    develop@56ef79004e31:/data/workflows/sample_run$ ./dvmdostem --log-level monitor -p 100 -e 1000 -s 250 -t 115 -n 85

Visualize run:

    develop@56ef79004e31:/data/workflows/sample_run$ /work/scripts/viewers/plot_output_var.py --yx 0 0 --file output/GPP_yearly_tr.nc

![GPP_plot_output_var](https://github.com/user-attachments/assets/678be9a7-2e48-479e-ae27-1a96c95da7be)

## Testing and Continuous Integration (CI)

This project has a very basic CI workflow implemented using Github Actions. When
a pull request is made to the `master` branch, an action is run that checks out
the code, builds one of the Docker images, compiles the `dvmdostem` binary and
runs the model using the demo data for a short number of years. This test does
not confirm any of the scientific aspects of the model and does not exercise any
of the supporting pre- and post-processing tools. Extending and improving the
CI coverage remains an open project. We would like for future development to 
improve overall test coverage and setup more actions to run the tests. For more 
information about the testing and CI, see the [Testing and Deployment](https://uaf-arctic-eco-modeling.github.io/dvm-dos-tem/software_development_info.html#testing-and-deployment) of the User Guide.

> [!WARNING]
> Sept 2022 - We are in the process of updating the entire documentation
> system. There is still info scattered across this README, the wiki, a Google
> Doc and the Sphinx system but we are working on consolidating the info into 
> primarily the Sphinx system (the User Guide).
