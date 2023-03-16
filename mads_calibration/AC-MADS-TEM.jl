# Autocalibration (AC) version 3.0
# Wraps MADS around TEM 
# Example: julia AC-MADS-TEM.jl /work/mads_calibration/config-step1-md1.yaml
# Author: Elchin Jafarov
# Date: 03/2023

import Mads
#import Pkg; Pkg.add("YAML")
import YAML
import PyCall
@show pwd()

PyCall.py"""

import sys,os
sys.path.append(os.path.join('/work','scripts'))
import TEM

def get_cofig_file(config_file_name):
    dvmdostem=TEM.TEM_model(config_file_name)
    dvmdostem.set_params(dvmdostem.cmtnum, dvmdostem.paramnames, dvmdostem.pftnums)
    return dvmdostem

"""

if ARGS==[]
    println("ERROR: Missing config file")
    println("syntax: julia AC-MADS-TEM.jl /work/mads_calibration/config-step1-md1.yaml")
    exit()
else
    mads_config = YAML.load_file(ARGS[1])
    println("Reading config file:")    
    println(ARGS[1])
end

tem = PyCall.py"get_cofig_file"(ARGS[1])

function TEM_pycall(parameters::AbstractVector)
        predictions = tem.run_TEM(parameters)
        return predictions
end

initial_guess=mads_config["mads_initial_guess"]

y_init=tem.run_TEM(initial_guess)
targets=tem.get_targets(1)

n_o=length(targets)
obstime=1:n_o 

# check for obsweight
obsweight=mads_config["mads_obsweight"]
if isnothing(obsweight)
    obsweight = ones(Int8, n_o)*100
else
    println("Make sure that weight length match with targets length")
end

# build paramlog array
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
paramlog=[falses(n_cmax); falses(n_nmax); falses(n_krb); trues(n_cfall); trues(n_nfall);
                        falses(ns1); falses(ns2); falses(ns3); falses(ns4); trues(ns5) ]
println(paramlog)

#choose a range for parameter values
paramdist = []
mads_paramrange=mads_config["mads_paramrange"]
if mads_paramrange == "ON"
    var=mads_config["mads_param_percent_variance"]
    for i in eachindex(initial_guess)
        min_r = initial_guess[i] .- initial_guess[i] .* (var / 100)
        max_r = initial_guess[i] + initial_guess[i] .* (var / 100)
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
    for i in eachindex(obs)
        min_r = max.(obs[i] .- obs[i] .* (var / 100), 0)
        max_r = obs[i] + obs[i] .* (var / 100)
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

#forward_model = Mads.forward(md)

#calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

#Mads.plotmatches(md, calib_param, xtitle="# of observations", 
#		      ytitle="Targets",filename=mads_config["mads_problemname"]*".png")

calib_random_results = Mads.calibraterandom(md, 10;  all=true, tolOF=0.01, tolOFcount=4)

calib_random_estimates = hcat(map(i->collect(values(calib_random_results[i,3])), 1:10)...)

forward_predictions = Mads.forward(md, calib_random_estimates)
Mads.spaghettiplot(md, forward_predictions, xtitle="# of observations", ytitle="Targets",
		       filename=mads_config["mads_problemname"]*".png")


