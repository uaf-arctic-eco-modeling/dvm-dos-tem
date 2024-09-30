#!/usr/bin/env julia

# Wraps MADS around TEM. Uses Mads to "calibrate" TEM, meaning that Mads is
# solving an optimization problem, attempting to find a parameter set that 
# minimizes the difference between TEM model outputs and TEM target data.
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
  Sets up and returns a driver object that can be manipulated from the 
  ecapsulating Julia program.

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

  dvmdostem.set_params_from_seed()
  dvmdostem.load_target_data("/work/calibration") # <- should be overridden later with data from config seed targets?
  dvmdostem.setup_outputs(dvmdostem.target_names)
  dvmdostem.clean()
  dvmdostem.setup_run_dir()
  # Maybe need to dvmdostem.write_params2rundir(...) here???

  return dvmdostem

import util.metrics
def plot_opt_fit(**kwargs):
  '''
  Pass this straight thru to the python library...

  Maybe this wrapper is unnecessary, you could directly call the function like
  this:
      PyCall.py"util.metrics.plot_optimization_fit"(...)?
  '''
  util.metrics.plot_optimization_fit(
    seed_params=kwargs['seed_params'],
    ig_params=kwargs['ig_params'],
    opt_params=kwargs['opt_params'],
    seed_out=kwargs['seed_out'],
    ig_out=kwargs['ig_out'],
    opt_out=kwargs['opt_out'],
    targets=kwargs['targets'],
    param_labels=kwargs['param_labels'],
    out_labels=kwargs['out_labels'],
    savefile=kwargs['savefile'],
  )
"""


# THIS IS A JULIA FUNCTION THAT WORKS WITH A GLOBAL PYTHON OBJECT.
# THIS JULIA FUNCTION OBJECT IS PASSED TO MADS
function dvmdostem_wrapper(parameters::AbstractVector)
  # This is similar to the dvmdostem.run_wrapper(), but it uses a less rich form
  # of outputs.  The dvmdostem.run_wrapper() function returns a list of dicts so
  # each record has PFT, cmtnumber, target, etc while in this case we can only
  # handle a more simple data type (plain list). The order is infered here.
  dvmdostem.update_params(parameters)
  dvmdostem.write_params2rundir()
  dvmdostem.run()
  predictions = dvmdostem.modeled_vec() # <-- plain vector of outputs, no labels
  return predictions
end


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


mads_config = YAML.load_file(config_file)
dvmdostem = PyCall.py"load_dvmdostem_from_configfile"(config_file)

# dvmdostem should be setup from the seed path and then some settings are over
# ridden from the mads config (parameter distributions, intial guesses, etc)

# Save the targets...
targets = dvmdostem.observed_vec(format="flat")

# Do the seed run and keep the results
println("Performing seed run...")
dvmdostem.run()
seed_params = dvmdostem.params_vec()
seed_out = dvmdostem.modeled_vec()

# Do the initial guess run and keep the results
initial_guess = mads_config["mads_initialguess"]
dvmdostem.update_params(initial_guess)
dvmdostem.write_params2rundir()  
println("Performing initial guess run...")
dvmdostem.run()
ig_params = dvmdostem.params_vec()
ig_out = dvmdostem.modeled_vec()

#####    SETUP FOR THE OPTIMIZATION   #####
prob_name = mads_config["mads_problemname"]
param_keys = mads_config["mads_paramkey"]
params = mads_config["params"]

# Setup: Which parameters should be log distributed?
# Use log distributed for parameters that have small values
# Builds a 2D list of booleans indicating which parameters will be treated as
# log distributed. 
# Not sure if this is used in all calbration cases, or only when doing 
# somekind or random sampling calibration...
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

# Setup: set a vector of weights for the observations
obsweight = mads_config["mads_obsweight"]
if obsweight == "OFF"
  obsweight = ones(Int8, length(targets)) * 100
else
    println("Make sure that weight length match with targets length")
end

# Setup: not sure what this is...?
obstime = 1:length(targets)

# Setup: choose a range for observation values.
# Not entirely clear how/why this is used....
# This can take into account uncertaintay in the targets/observations
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

# Setup: Possibly override the parameter distributions that users sets in the
# config file - if the user has selected mads_paramrange ON in the config file
# then ignore the parameter distribution setting from the config and set
# new values here based on config file variance spec and intial guess.
# Not sure what the use case is for this, but leaving here for now...
paramdist = []
mads_paramrange=mads_config["mads_paramrange"]
if mads_paramrange == "ON"
    var=mads_config["mads_param_percent_variance"]
    for i in eachindex(initial_guess)
 	      if initial_guess[i] > 0
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


# Setup: configure the Mads object
md = Mads.createproblem(
    initial_guess,        # The list of initial parameter values
    targets,              # List of target values (trying to match these)
    dvmdostem_wrapper;    # The callable function that runs the model
    paramkey=param_keys,  # ?? Maybe just list of nice names for plotting?
    paramdist,            # List of distributions to draw parameters from
    obstime,              # ??
    obsweight,            # vector of weights, matching targets in size
    paramlog,             # List of vectors indicating which parameters
                          # should be log distributed
    obsdist,              # ??
    problemname=prob_name # convienience handle
)
md["Problem"] = Dict{Any,Any}("ssdr"=>true)

# Finally! Run the optimization. This can take forever...
println("Performing calibration (optimization) runs...")
calib_params, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

# calib_params:
#    an OrderedCollections.OrderedDict of optimum parameter values
# calib_information:
#    an OptimBase.MultivariateOptimizationResults object with a bunch of 
#    metadata about the optimization process

# Prefer not to run the Mads.plotmatches(..) function!
# The labels on the plot are opaque and it has to run the model again which is
# annoyingly slow. This will be replaced by plot_opt_fit below...
#Mads.plotmatches(md, calib_params, xtitle="# of observations", 
#                ytitle="Targets",filename=prob_name*".png")

# Then finally you step the model "forward" and run it with the optimum results
# But in our case, since the model is so expensive to run we should simply grab
# the outputs from the last optimzation run rather than re-running the model...
#calib_predictions = Mads.forward(md, calib_params)
calib_predictions = dvmdostem.modeled_vec()

# Print a bunch of stuff out so that you can save it (copy paste from terminal?)
# and later run the plotting function without waiting for Mads to import or any
# of the dvmdostem runs to commence.

# For consistent naming below, do the following:
opt_params = calib_params.vals

println("seed_params=np.array(", seed_params, "),")
println("ig_params=np.array(", ig_params, "),")
println("opt_params=", opt_params, ",")
println("seed_out=np.array(", seed_out, "),")
println("ig_out=np.array(", ig_out, "),")
println("opt_out=np.array(", calib_predictions, "),")
println("param_labels=", param_keys, ",")
println("targets=np.array(", targets, "),")

# Generate a list of nicely formatted labels that can be used for plotting
# These labels are for the output variables (aka calibration targets)
outlabels = []
for x in dvmdostem.gather_model_outputs()

  if haskey(x, "pft") && haskey(x, "cmprt")
    push!(outlabels, string(x["ctname"], "_pft", x["pft"], "_", x["cmprt"]))

  elseif haskey(x, "pft") && !haskey(x, "cmprt")
    push!(outlabels, string(x["ctname"], "_pft", x["pft"]))

  else
    push!(outlabels, string(x["ctname"]))
  end

end


println("out_labels=", outlabels)
println("")

# Or if you need to lookup the optimum parameter values after the run from a 
# Python script this will work:
#    import SA_post_hoc_analysis as sap
#    iteration_params, OF, LAM = sap.read_mads_iterationresults("/path/to/your/mads.iterationresults")
#    opt_params = [v for k, v in iteration_params[-1].item()]

# Retrieve the mads metadata files....
# Not sure where these should default to going...??? 
# Same problem with plot above...for now putting them in the work_dir, but this
# is not ideal because they get cleaned up if you make another driver instance
# The use case for another driver instance is to analyze a run that has already
# taken place without waiting for the optimization run to happen again...
mv(
  mads_config["mads_problemname"] * ".iterationresults",
  joinpath(mads_config["work_dir"], mads_config["mads_problemname"] * ".iterationresults")
)
mv(
  mads_config["mads_problemname"] * ".finalresults",
  joinpath(mads_config["work_dir"], mads_config["mads_problemname"] * ".finalresults")
)

# Generate a plot with 3 panels:
#   1. The seed, initial guess, and optimized parameters
#   2. The seed, initial guess, and optimized outputs
#   3. The residuals (modeled outputs - the targets) 
plot_file_name = joinpath(mads_config["work_dir"], "plot_optimization_fit.png")
PyCall.py"plot_opt_fit"(
  seed_params=seed_params, ig_params=ig_params, opt_params=opt_params, 
  seed_out=seed_out, ig_out=ig_out, opt_out=calib_predictions, 
  param_labels=param_keys,
  out_labels=outlabels,
  targets=targets, 
  savefile=plot_file_name
)



# One issue is that when doing the seed run (or any of the other runs for that
# matter) it will totally clean out the working directory
# (mads_config["work_dir"]), which will clear out the plots or iteration
# results...


# Not sure what these are for..?
# Maybe the Mads Problem "paramdist" list is used to seed these??
#calib_random_results = Mads.calibraterandom(md, 10;  all=true, tolOF=0.01, tolOFcount=4)
#calib_random_estimates = hcat(map(i->collect(values(calib_random_results[i,3])), 1:10)...)
