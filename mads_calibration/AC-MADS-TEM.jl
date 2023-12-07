#!/usr/bin/env julia

# Wraps MADS around TEM 
#
# Example of use: mads_calibration/AC-MAD-TEM.jl /data/workflows/config.yaml
#     $ julia AC-MADS-TEM.jl /data/workflows/config.yaml
#
# Author: Elchin Jafarov, Tobey Carman
# Date: 03/2023, 11/2023

import Mads
import YAML
import PyCall


# THIS IS A PYTHON FUNCTION THAT RETURNS A PYTHON OBJECT THAT IS USABLE FROM
# THE JULIA RUNTIME!
PyCall.py"""
import drivers.MadsTEMDriver
def load_dvmdostem_from_configfile(config_file_name):
  '''
  Parameters
  ----------
  config_file_name :
    the path to a config yaml file that has all the settings for the MADs CA 
    assist steps....

  Returns
  -------
  drivers.MadsTEMDriver
    The object has been setup according to the values in the config file.
  '''
  dvmdostem = drivers.MadsTEMDriver.MadsTEMDriver.fromfilename(config_file_name)

  dvmdostem.set_seed_path("/work/parameters")
  dvmdostem.set_params_from_seed()
  dvmdostem.load_target_data("/work/calibration")
  dvmdostem.setup_outputs(dvmdostem.target_names)
  dvmdostem.clean()
  dvmdostem.setup_run_dir()

  return dvmdostem
"""

###  ENTRY POINT...
if ARGS==[]
    println("ERROR: Missing config file!")
    println("Example usage: ")
    println("")
    println("    \$ julia ", basename(@__FILE__), " /path/to/config.yaml")
    println("")
    exit()
else
    mads_config = YAML.load_file(ARGS[1])
    println("Reading config file:")    
    println(ARGS[1])
    config_file = ARGS[1]
end


function TEM_pycall(parameters::AbstractVector)
        predictions = tem.run_TEM(parameters)
        return predictions
end

# check for obsweight
obsweight=mads_config["mads_obsweight"]
if isnothing(obsweight)
    obsweight = ones(Int8, n_o)*100
else
    println("Make sure that weight length match with targets length")
end

mads_config = YAML.load_file(config_file)
dvmdostem = PyCall.py"load_dvmdostem_from_configfile"(config_file)

# dvmdostem should be setup from the seed path and then some settings are over
# ridden from the mads config (parameter distributions, intial guesses, etc)


# Save the targets...
targets = dvmdostem.observed()

# Do the seed run and keep the results
dvmdostem.run()
seed_params = dvmdostem.params_vec()
seed_out = dvmdostem.modeled()

# Do the initial guess run and keep the results
initial_guess = mads_config["mads_initialguess"]
dvmdostem.update_params(initial_guess)
dvmdostem.write_params2rundir()  
dvmdostem.run()
ig_params = dvmdostem.params_vec()
ig_out = dvmdostem.modeled()

# Do the optimization, which requires a bit more setup... 
prob_name = mads_config["mads_problemname"]
param_keys  = mads_config["mads_paramkey"]
paramdist = mads_config["mads_paramdist"]

# Setup: deal with which params should be log distributed...
# Use log distributed for targets that have small values
params=mads_config["params"]
n_cmax=count(i->(i== "cmax"), params)
n_nmax=count(i->(i== "nmax"), params)
n_krb0=count(i->(i== "krb(0)"), params)
n_krb1=count(i->(i== "krb(1)"), params)
n_krb2=count(i->(i== "krb(2)"), params)
n_krb=n_krb0+n_krb1+n_krb2
n_cfall0=count(i->(i== "cfall(0)"), params)
n_cfall1=count(i->(i== "cfall(1)"), params)
n_cfall2=count(i->(i== "cfall(2)"), params)
n_cfall=n_cfall0+n_cfall1+n_cfall2
n_nfall0=count(i->(i== "nfall(0)"), params)
n_nfall1=count(i->(i== "nfall(1)"), params)
n_nfall2=count(i->(i== "nfall(2)"), params)
n_nfall=n_nfall0+n_nfall1+n_nfall2
ns1=count(i->(i== "micbnup"), params)
ns2=count(i->(i== "kdcrawc"), params)
ns3=count(i->(i== "kdcsoma"), params)
ns4=count(i->(i== "kdcsompr"), params)
ns5=count(i->(i== "kdcsomcr"), params)
paramlog=[
  falses(n_cmax);
  falses(n_nmax);
  falses(n_krb);
  trues(n_cfall);    # <--
  trues(n_nfall);    # <--
  falses(ns1);
  falses(ns2);
  falses(ns3);
  falses(ns4);
  trues(ns5)         # <--
]

#choose a range for parameter values
paramdist = []
mads_paramrange=mads_config["mads_paramrange"]
if mads_paramrange == "ON"
    var=mads_config["mads_param_percent_variance"]
    for i in eachindex(initial_guess)
 	if initial_guess[i]>0
            min_r = initial_guess[i] .- initial_guess[i] .* (var / 100)
            max_r = initial_guess[i] + initial_guess[i] .* (var / 100)
        else
            max_r = initial_guess[i] .- initial_guess[i] .* (var / 100)
            min_r = initial_guess[i] + initial_guess[i] .* (var / 100)     
        end  
        push!(paramdist, "Uniform($(min_r), $(max_r))")
    end
else
    paramdist=mads_config["mads_paramdist"]
end

#choose a range for observation values
obsdist = []
mads_obsrange=mads_config["mads_obsrange"]
if mads_obsrange == "ON"   
    var=mads_config["mads_obs_percent_variance"]
    for i in eachindex(targets)
        min_r = max.(targets[i] .- targets[i] .* (var / 100), 0)
        max_r = targets[i] + targets[i] .* (var / 100)
        push!(obsdist, "Uniform($(min_r), $(max_r))")
    end
end

md = Mads.createproblem(initial_guess, targets, TEM_pycall;
    paramkey=mads_config["mads_paramkey"],
    paramdist,
    obstime,
    obsweight,
    paramlog,
    obsdist,
    problemname=mads_config["mads_problemname"])

md["Problem"] = Dict{Any,Any}("ssdr"=>true)

Mads.showparameters(md)
Mads.showobservations(md)

forward_model = Mads.forward(md)

calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

Mads.plotmatches(md, calib_param, xtitle="# of observations", 
		      ytitle="Targets",filename=mads_config["mads_problemname"]*".png")

#calib_random_results = Mads.calibraterandom(md, 10;  all=true, tolOF=0.01, tolOFcount=4)

#calib_random_estimates = hcat(map(i->collect(values(calib_random_results[i,3])), 1:10)...)

#forward_predictions = Mads.forward(md, calib_random_estimates)
#Mads.spaghettiplot(md, forward_predictions, xtitle="# of observations", ytitle="Targets",
#		       filename=mads_config["mads_problemname"]*".png")


