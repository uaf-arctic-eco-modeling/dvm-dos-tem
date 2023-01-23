# STEP5-MD1-R
# parameters: nfall
# targets: VegN(Leaf,Stem,Root)[22:32]

#import Pkg; Pkg.add("PyCall")

import Mads
import PyCall
include("write_csv.jl")
@show pwd()

PyCall.py"""

import sys,os
sys.path.append(os.path.join('/work','scripts'))
import TEM

def run_TEM(x):
    
    for j in range(len(dvmdostem.params)):
        dvmdostem.params[j]['val']=x[j]   
    # update param files
    dvmdostem.clean()
    dvmdostem.setup(calib=True)
    dvmdostem.update_params()
    dvmdostem.run()

    return dvmdostem.get_calibration_outputs()[22:32]

def get_param_targets():
    return dvmdostem.get_calibration_outputs(calib=True)[22:32]

dvmdostem=TEM.TEM_model()
dvmdostem.site='/data/input-catalog/cru-ts40_ar5_rcp85_mri-cgcm3_MurphyDome_10x10'
dvmdostem.work_dir='/data/workflows/MD1-STEP5'
dvmdostem.calib_mode='VEGN'
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=1, params=['nfall(0)','nfall(0)','nfall(0)','nfall(0)', \
                                       'nfall(1)','nfall(1)','nfall(1)', \
                                       'nfall(2)','nfall(2)','nfall(2)'], \
                               pftnums=[0,1,2,3, \
                                        0,1,2, \
                                        0,1,2])
"""
initial_guess=[0.011, 0.028, 0.028, 0.009, 
               0.001, 0.001, 0.006, 
               0.011, 0.008, 0.008]

y_init=PyCall.py"run_TEM"(initial_guess)
print(y_init)
function TEM_pycall(parameters::AbstractVector)
    predictions = PyCall.py"run_TEM"(parameters)
    return predictions
end
obs=PyCall.py"get_param_targets"()
obs_time=1:length(obs)
print(obs)
md = Mads.createproblem(initial_guess, obs, TEM_pycall;
    paramkey=["nfall00","nfall01","nfall02","nfall03",
              "nfall10","nfall11","nfall12",
              "nfall20","nfall21","nfall22"],
    paramdist=["Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)",
               "Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)",
               "Uniform(1e-7, 0.09)","Uniform(1e-7, 0.09)","Uniform(1e-7, 0.09)"],
    obstime=obs_time,
    #obsweight=[10,100,100,10,10,10,50,100,100,100,50,10,10,50,100,100],
    paramlog=trues(10),
    problemname="STEP5-MD1")

Mads.showparameters(md)
Mads.showobservations(md)

calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

Mads.plotmatches(md, calib_param, 
    xtitle="# of observations", ytitle="VEGN(nfall)",filename="STEP5-MD1-matchplot.png")

save_csv(Mads.getparamkeys(md), Mads.getparamsmin(md), Mads.getparamsmax(md), initial_guess,
    Mads.getmadsrootname(md), Mads.getobsweight(md))

forward_predictions = Mads.forward(md, calib_param)
save_model_csv(md,Mads.getmadsrootname(md),forward_predictions)

