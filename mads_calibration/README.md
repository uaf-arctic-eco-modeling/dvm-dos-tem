MADS-TEM parameter calibration 
===========================================

The autocalibration (AC) process is focused on matching average above- and below-ground carbon and nitrogen stocks and fluxes. We match mean annual observed values during the equilibrium run period to ensure that the model represents the history of a given site. All parameters and observations are vectors, where an element of a vector represents a given plant functional type (PFT) within a given vegetation community type or a subsurface parameter. The calibration parameters can be found in [`paramters/calparbgc.txt`](https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem/blob/calib/parameters/cmt_calparbgc.txt) and targets can be found in [`calibration/calibration_targets.py`](https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem/blob/calib/calibration/calibration_targets.py). For example, if we calibrating parameters for CMT4 then the corresponding targets will be under CMT4 as well. 
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


## The workflow
It is useful to run the Sensitivity Analysis (SA) before running calibration. The main goal of the SA is to see if targets are included in the range of modeled target values. The initial guess usually comes from the previous values for a similar vegetation community type. The SA can improve the initial guess values. Once observed target values fall within the range of the SA modeled target outputs we move to CA.

MADS allows setting ranges for each element of the initial guess vector. If SA was used before CA, then ranges could be informed from SA. We can run one or multiple calibration runs at each step to test for the overall method convergence, where multiple runs correspond to the randomly perturbated initial guess vector. Typically, CA would further refine the match between observed and modeled target values. `AC-MADS-TEM.jl` can handle a combination of multiple parameters (set in configuration `yaml` file) and target values per calibration, accounting for the combined effect of multiple correlated parameters on observations. We can combine multiple parameters and target values to study the effects of multiple correlated parameters on observations. The calibration process is scalable and can be run in parallel on multiple processors. 

![The workflow that outlines sensitivity analysis and calibration processes](images/SA-CA-workflow.png)

## Setup

The instructions for setting up are not included here. The assumption is that you have the following figured out before you
start this process:

 - Git and Docker installed on your computer
 - A copy (clone) of the dvm-dos-tem source code repository on your
   computer.
 - Have built the docker images for the project, including the 
   autocal image.
 - Are familiar with how to run the docker containers and how to 
   store your work in a location that persists when you shutdown your
	 docker containers (i.e. the folder that is mounted in the container at `/data/workflows`)

For more information on the above topics, see the main documentation, specifially the Prelude, Dev Info, and Examples and Tutorials sections. 

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
