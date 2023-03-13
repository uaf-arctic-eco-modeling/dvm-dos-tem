# Autocalibration (AC) version 3.0
# This version uses updated TEM.py  
# STEP3 MD1
# parameters: nmax,krb,cfall,nfall
# targets: (NPP,VEGC,VEGN)

import Mads
#import Pkg; Pkg.add("YAML")
import YAML
import PyCall
@show pwd()

PyCall.py"""

import sys,os
sys.path.append(os.path.join('/work','scripts'))
import TEM

dvmdostem=TEM.TEM_model('config-step3-md1.yaml')
dvmdostem.set_params(dvmdostem.cmtnum, dvmdostem.paramnames, dvmdostem.pftnums)

"""

mads_config = YAML.load_file("config-step3-md1.yaml")

function TEM_pycall(parameters::AbstractVector)
        predictions = PyCall.py"dvmdostem.run_TEM"(parameters)
        return predictions
end

initial_guess=mads_config["mads_initial_guess"]
y_init=PyCall.py"dvmdostem.run_TEM"(initial_guess)
targets=PyCall.py"dvmdostem.get_targets(targets=True)"
n_o=length(targets)
println(n_o)
obstime=1:n_o

# check for obsweight
obsweight=mads_config["mads_obsweight"]
if isnothing(obsweight)
    obsweight = ones(Int8, n_o)*100
else
    println("Make sure that weight length match with targets length")
end

# check for paramlog
n_p=length(initial_guess)
paramlog=mads_config["mads_paramlog"]

if isnothing(paramlog)
    paramlog = [falses(4); falses(10); trues(10); trues(10)]
    #paramlog = falses(n_p) # for small parameter values (<10-3) this needs to trues
else
    println("Make sure that paramlog length match with IC length")
end

print(paramlog)
print(length(paramlog))

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
#		      ytitle="GPP",filename=mads_config["mads_problemname"]*".png")

calib_random_results = Mads.calibraterandom(md, 10; seed=2021, all=true, tolOF=0.01, tolOFcount=4)

calib_random_estimates = hcat(map(i->collect(values(calib_random_results[i,3])), 1:10)...)

forward_predictions = Mads.forward(md, calib_random_estimates)
Mads.spaghettiplot(md, forward_predictions, xtitle="# of observations", ytitle="NPP/VEGC/VEGN",
		       filename=mads_config["mads_problemname"]*".png")


