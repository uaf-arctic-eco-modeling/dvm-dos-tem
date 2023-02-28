# Autocalibration (AC) version 2.0
# This version uses updated TEM.py  
# STEP1 MD1
# parameters: cmax
# targets: (GPP) grabs all targets except last 6 elements correspoding to soil parameters 

import Mads
import PyCall
@show pwd()

PyCall.py"""

import sys,os
sys.path.append(os.path.join('/work','scripts'))
import TEM

dvmdostem=TEM.TEM_model()

dvmdostem.site='/data/input-catalog/cru-ts40_ar5_rcp85_mri-cgcm3_MurphyDome_10x10'
dvmdostem.work_dir='/data/workflows/STEP1-MD1'
dvmdostem.calib_mode='GPPAllIgnoringNitrogen'
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=1, params=['cmax','cmax','cmax','cmax'], \
                               pftnums=[0,1,2,3])
"""

function TEM_pycall(parameters::AbstractVector)
        predictions = PyCall.py"dvmdostem.run_TEM"(parameters)
        return predictions
end
initial_guess=[381.19, 113.93, 207.08, 93.31]

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
    paramkey=["cmax0","cmax1","cmax2","cmax3"],
    paramdist=["Uniform(0.1, 500)","Uniform(0.1, 200)","Uniform(0.1, 300)","Uniform(0.1, 200)"],
    obstime=obs_time,
    #obsweight=[100,100,100,100],
    problemname="AC2-STEP1-MD1-EJ")

md["Problem"] = Dict{Any,Any}("ssdr"=>true)

Mads.showparameters(md)
Mads.showobservations(md)

forward_model = Mads.forward(md)

calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

Mads.plotmatches(md, calib_param, 
    xtitle="# of observations", ytitle="GPP",filename="AC2-STEP1-MD1.png")


