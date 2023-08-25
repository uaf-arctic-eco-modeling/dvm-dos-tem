MADS-TEM parameter calibration 
===========================================

The autocalibration (AC) process is focused on matching average above- and below-ground carbon and nitrogen stocks and fluxes. We match mean annual observed values during the equilibrium run period to ensure that the model represents the history of a given site. All parameters and observations are vectors, where an element of a vector represents a given plant functional type (PFT) within a given vegetation community type or a subsurface parameter. The calibration parameters can be found in [`paramters/calparbgc.txt`](https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem/blob/calib/parameters/cmt_calparbgc.txt) and targets can be found in [calibration/calibration_targets.py](https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem/blob/calib/calibration/calibration_targets.py). For example, if we calibrating parameters for CMT4 then the corresponding targets will be under CMT4 as well. 
## Parameters (above ground)
| Name          | Description         |
| ------------- |  ------------------ |
| cmax          | maximum rate of carbon assimilation |
| nmax          | maximum plant N uptake|
| krb (leaf,stem,root) | autotrophic respiration    |
| cfall (leaf,stem,root) | C in litter production   |
| nfall (leaf,stem,root) | N in litter production   |

## Parameters (below ground)
| Name          | Description         |
| ------------- |  ------------------ |
| micbnup | soil microbial immobilization |
| kdcraw | litter/raw pool decomposition rate |
| kdcactive | active pool decomposition rate |
| kdcpr | physically resistant pools decomposition rate |
| kdccr | chemically resistant pools decomposition rate |

## Targets (above ground)
| Name          | Description         |
| ------------- |  ------------------ |
| GPP | Gross Primary Productivity |
| NPP | Nitrogen Primary Productivity |
| VegC (leaf,stem,root) | Vegetation Carbon |
| VegN (leaf,stem,root) | Vegetation Nitrogen |

## Targets (below ground)
| Name          | Description         |
| ------------- |  ------------------ |
| Shallow C | Shallow C Pool |
| Deep C | Deep C Pool |
| MineralSumC | Mineral C Pool |
| AvailSumN | Available N Pool |

The calibration workflow consists of multiple steps. First, we calibrate above-ground carbon and nitrogen fluxes, and then we calibrate below-ground stocks. To start the calibration process in MADS, we provide an initial set of parameter values called initial guesses (see `yaml` files). YAML configuration file provides a flexible setup for different calibration (CA) setup types. Besides, `GPPAllIgnoringNitrogen` case, where only `cmax` values can participate, the rest of the cases can be combined based on the user's preferences and goals. 

## YAML Configuration File includes
* `calib_mode`: see calibration cases in `calibration/calibration_targets.py`. This option matters for ``GPPAllIgnoringNitrogen`` case only. 
* `target_names`: use elements from the corresponding row in  `calibration/calibration_targets.py` as target values
* `cmtnum`: community type number
* `opt_run_setup`: define [run stages](https://uaf-arctic-eco-modeling.github.io/dvm-dos-tem/model_overview.html#temporal)
* `params`: name of parameters
* `pftnum`: corresponds to the parameters listed in `params`
* `site`: path to the input data
* `work_dir`: path to the working directory
* `mads_initial_guess`: initial values for the corresponding `params`
* `mads_paramdist`: the only allowed for CA uniform distribution `Uniform(0, 0)`
* `mads_paramkey`: for bookkeeping MADS outputs
* `mads_obsweight`: weight of target values, if applicable
* `mads_obsrange`: `ON`,`OFF`
* `mads_obs_percent_variance`: ranges from 0% to 99%
* `mads_paramrange`: `ON`,`OFF`, if `ON` will overwrite `mads_paramdist`
* `mads_param_percent_variance`: `ON`,`OFF`
* `mads_problemname`: for bookkeeping, suggested format param_name/s_target_name/s_user_initial



It is useful to run the Sensitivity Analysis before running calibration. The main goal of the SA is to see if targets are included in the range of modeled target values. The initial guess usually comes from the previous values for a similar vegetation community type. The SA can improve the initial guess values. MADS allows setting ranges for each element of the initial guess vector. We can run one or multiple calibration runs at each step to test for the overall method convergence, where multiple runs correspond to the randomly perturbated initial guess vector. `AC-MADS-TEM.jl` can handle a combination of multiple parameters (set in configuration `yaml` file) and target values per calibration, accounting for the combined effect of multiple correlated parameters on observations. We can combine multiple parameters and target values to study the effects of multiple correlated parameters on observations. The calibration process is scalable and can be run in parallel on multiple processors. 


![The workflow that outlines sensitivity analysis and calibration processes](images/SA-CA-workflow.png)

Installing git, dvm-dos-tem, and Docker on Linux
===========================================
Before installing dvm-dos-tem, bring any updates to the existing packages on your instance by typing:
```
$ apt update
```

Verify if git has already been installed:
```
$ git
```
If not installed, a message will appear indicating ‘Command 'git' not found, but can be installed with…’

If not, install with:
```
$ sudo apt install git
```

To install dvm-dos-tem, it can be cloned from the dvm-dos-tem git repository. Once the installation is complete, check that the folder has been downloaded by listing all folders in your home directory. The folder is called dvm-dos-tem.
```
$ git clone https://github.com/ua-snap/dvm-dos-tem.git
```
The download takes about 10 sec.
Verify download: $ ls
```
$ cd dvm-dos-tem
```

Change to the dvm-dos-tem directory, install Docker and verify that it has been installed successfully.
```
$ sudo apt install docker.io
```
The download takes about 1 min.
During the installation, you may be prompted to answer the following question with yes or no, type Y:
After this operation, 334 MB of additional disk space will be used.
Do you want to continue? [Y/n] Y
How to verify successful download

Install docker-compose.
```
$ sudo apt-get install docker-compose
```

Running ./dvmdostem from the docker
===========================================
Create two folders in your home directory (`/home/your_name`) for the input and output data that will be used to run the calibration scripts, and verify that they have been created. We recommend using the names `dvmdostem-input-catalog` and `dvmdostem_workflows` for the input and output data.
Go back to home directory: `
```
$ cd ../
$ mkdir dvmdostem-input-catalog
$ mkdir dvmdostem-workflows
```
Verify they were created: `$ ls`.

Go to the dvm-dos-tem folder (`$ cd dvm-dos-tem`) and install the five Docker images, verify that they have been installed successfully, and note the name of the version tag.
```
$ sudo bash docker-build-wrapper.sh
```
The build takes about 5 min.
Verify the images have been installed: `$ sudo docker image ls`
The 5 images should be: 
```
dvmdostem-mapping-support
dvmdostem-run
dvmdostem-build 
dvmdostem-dev 
cpp-dev
```

If no images are listed after the installation, try running the command ` sudo bash docker-build-wrapper.sh ` again.
Note the name of the version tag. 
The tag indicates which version of the image you have built. It is possible to have several image versions laying around at one time. The `.env` file lets you choose which image version to use when starting container(s)

In the dvm-dos-tem directory, create an environment (`.env`) file. You need to choose a location for the input catalog and a location where you would like to store the model output. Once you have chosen these locations, go ahead and set the environment variables `DDT_INPUT_CATALOG` and `DDT_WORKFLOWS` in a special file named `.env` which you need to create in the root of the `dvm-dos-tem` folder. ( One option to do so is using `vi` (or `vim`).

Create the file: `$ vi .env` 
If vi or vim is not installed, they can be installed via:  `$ sudo apt-get vim`, and then  `$ vim .env`

Edit the text in the `.env` file by entering i (for insert). You should see the text at the bottom of the window display – INSERT –. Now you can change the `V_TAG` to the version tag listed under `TAG` in the previous step, and set the following variables to the path of the input and output folders created previously. 

Edit environment variables. Note your version tag may be different from the one listed below as the repository continues to be updated. Check your container information to get your individual `V_TAG` value. You can copy this code into the `vi` environment (it is a text editor).

```
V_TAG='your_tag_number'
DDT_INPUT_CATALOG=/home/username/dvmdostem-input-catalog/
DDT_WORKFLOWS=/home/username/dvmdostem-workflows/
PWD=/home/username/dvm-dos-tem/
```
Save and exit from this `.env` file. Tap the escape key and enter 
`:wq` and tap enter (save and quit).
To not save changes `:q!`

Check that the three volumes are mounted. 
```
$ sudo docker volume ls
DRIVER    VOLUME NAME
local     dvm-dos-tem_inputcatalog
local     dvm-dos-tem_sourcecode
local     dvm-dos-tem_workflows
```
Make sure you are in `dvm-dos-tem` folder, and start the container (based on your images). 
```
$ sudo docker-compose up -d
```
Enter into the container. This runs `dvm-dos-tem` as a user to avoid permission errors. This will put you into a `/work` folder on Docker inside the `dvm-dos-tem` folder. In case of error, it is likely that the `V_TAG` or other environment variables are incorrect in `.env` file.
```
$ sudo docker-compose exec -u root dvmdostem-dev bash
```
`docker-compose exec` runs a command inside a running container. The response should look like this:
```
root@xxx:/work#
```

List files, and build the `dvmdostem` executable file if it has not already been created. The build takes a few minutes. Typically, the executables files appear in light green in the terminal window. Once the build is complete, check that the file is there.
```
$ make
```
Now that your `/work` folder contains the `dvmdostem` code file, you are ready to run the `dvmdostem` model.
```
$ ./dvmdostem
```
When you are finished running your desired scripts, be sure you save your work and close down your session. To exit out of your current root folder on Docker enter:
```
$ exit
```
Close the container.
```
$ sudo docker-compose down
```

Installing [MADS](https://mads.readthedocs.io/) and setting up the calibration run
===========================================
Load the `calib` branch, where our group is working on calibration, and pull the latest changes. This branch has not yet been merged into master, it is in development. It is best to consult with the team prior to pushing up code to this branch as others will pull it when updating their branch locally. See the Git help page to understand the concept of checkout, push, pull and merge on git.

Access it: `$ git checkout calib`

Pull latest changes: `$ git pull origin calib`

Download Julia:
`$ wget https://julialang-s3.julialang.org/bin/linux/x64/1.7/julia-1.7.3-linux-x86_64.tar.gz`

Extract zip file:
`$ tar -xzf julia-1.7.3`  (Hit tab to finish the filename, we need to extract zip)

Copy Julia folder:
`$ cp -r julia-1.7.3 /opt/`

So that we don’t have to specify ‘/opt/julia-1.7.3/bin/julia’ each time we use Julia:
`$ ln -s /opt/julia-1.7.3/bin/julia /usr/local/bin/julia`

Start Julia REPL
`$ julia`

Enter Package Mode
`julia> ]`

Download Mads
`pkg> add Mads@1.3.10`
Note: The installation takes 10-15 min.

Exit Package Mode
`pkg>  ‘ctr+c’ or delete`

Exit Julia REPL
`julia> ‘ctrl+d’`

Running the Sensitivity Analysis (SA)
===========================================
Before running calibration, it is important to understand the impact of a set of parameters on the target space.  To do this, we use `run_mads_sensitivity.py`. This script runs in parallel a number of parameter samples, set in `sample_size=1000`.  This python script is using the setup in the `yaml` file but only partially. For example, the initial parameter set is read from the `parameters/cmt_calparbgc.txt`. The site location and output location are read from yaml file. Use the commed below to run the sensitivity inside the docker:
```
python run_mads_sensitivity.py /work/mads_calibration/config-step1-md1.yaml
```
This will produce a lot of folders in the output path set in the config file. We only need four files for further analysis: `info.txt`, `param_props.csv`, `results.txt`,`sample_matrix.csv`. The examples of the SA analysis can be found in this [repo](https://github.com/whrc/MADS-TEM-calibration)

Check for equilibrium runs
===========================================
After sensitivity is finished, it is important to check for equilibrium. The `equilibrium_check.py` is under development to check for it. This script filters model outputs that do not satisfy the equilibrium criteria defined in the script.  


Running the Calibration
===========================================
Note that before running calibrations, you must have the inputs (driver) files. From within Docker, change the directory to scripts and run `AC-MADS-TEM.jl` with Julia:
```
$ cd mads_calibration
```
Run `AC-MADS-TEM.jl`
```
$ julia AC-MADS-TEM.jl /work/mads_calibration/config-step1-md1.yaml
```
A successful run will output your parameters in the calibration file entitled:  `'calib_file_name'.finalresults` in the current folder, which can be accessed inside or outside the Docker. 
To access the results: `vi 'calib_file_name'.finalresults`

Here is an example of the successful run of the `AC-MADS-TEM.jl` calibration eight `cmax`s parameters and matching `GPP` target value:
```
OF: 0.12296721194086714
lambda: NaN
OrderedCollections.OrderedDict("cmax0" => 134.3675944648774, "cmax1" => 4.407632869450644, "cmax2" => 337.56299939603224, "cmax3" => 594.1233078870423, "cmax4" => 3.5051465533751056, "cmax5" => 32.30723495103502, "cmax6" => 90.30393701357312, "cmax7" => 47.254720715049544)
```

Post-processing Calibration results
===========================================
`AC-MADS-TEM` allows to run multiple runs with perturbed initial guesses. To enable that mode one needs to uncomment the lines below. 

```
calib_random_results = Mads.calibraterandom(md, 10;  all=true, tolOF=0.01, tolOFcount=4)

calib_random_estimates = hcat(map(i->collect(values(calib_random_results[i,3])), 1:10)...)

forward_predictions = Mads.forward(md, calib_random_estimates)
Mads.spaghettiplot(md, forward_predictions, xtitle="# of observations", ytitle="Targets",
		       filename=mads_config["mads_problemname"]*".png")
```
This calibration will generate results for 10 randomly perturbed initial guesses. Then `post_run.py` needs to be modified and used to generate parameter and outputs files based on the optimal parameter sets. These files are used later for further similar to SA analysis in this [repo](https://github.com/whrc/MADS-TEM-calibration).
