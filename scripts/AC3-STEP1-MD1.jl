# Autocalibration (AC) version 3.0
# This version uses updated TEM.py  
# STEP1 MD1
# parameters: cmax
# targets: (GPP) grabs all targets except last 6 elements correspoding to soil parameters 

import Mads
import Pkg; Pkg.add("YAML")
import YAML
import PyCall
@show pwd()

PyCall.py"""

import sys,os
sys.path.append(os.path.join('/work','scripts'))
import TEM

dvmdostem=TEM.TEM_model('config-step1-md1.yaml')
dvmdostem.set_params(dvmdostem.cmtnum, dvmdostem.paramnames, dvmdostem.pftnums)

"""

function TEM_pycall(parameters::AbstractVector)
        predictions = PyCall.py"dvmdostem.run_TEM"(parameters)
        return predictions
end

mads_config = YAML.load_file("config-step1-md1.yaml")
initial_guess=mads_config["mads_initial_guess"]

y_init=PyCall.py"dvmdostem.run_TEM"(initial_guess)
#print("length y_init:  ",length(y_init))
#print(y_init)
obs=PyCall.py"dvmdostem.get_targets"()
n_o=length(obs)
obs_time=1:n_o-6 #excluding soil carbon values
targets=obs[1:n_o-6]#grabbing only vegetation targets
#print("obs_length: ",length(obs))
#print(obs[1:n_o])
#print(obs[1:n_o-6])

md = Mads.createproblem(initial_guess, targets, TEM_pycall;
    paramkey=mads_config["mads_paramkey"],
    paramdist=mads_config["mads_paramdist"],
    obstime=obs_time,
    #obsweight=[100,100,100,100],
    problemname=mads_config["mads_problemname"])

md["Problem"] = Dict{Any,Any}("ssdr"=>true)

Mads.showparameters(md)
Mads.showobservations(md)

#forward_model = Mads.forward(md)

calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

Mads.plotmatches(md, calib_param, 
    xtitle="# of observations", ytitle="GPP",filename="AC2-STEP1-MD1.png")


