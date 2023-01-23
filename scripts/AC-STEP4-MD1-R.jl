# STEP4-MD1
# parameters: cfall
# targets: VegCarbon(Leaf,Stem,Root)[12:22]

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

    return dvmdostem.get_calibration_outputs()[12:22]

def get_param_targets():
    return dvmdostem.get_calibration_outputs(calib=True)[12:22]

dvmdostem=TEM.TEM_model()
dvmdostem.site='/data/input-catalog/cru-ts40_ar5_rcp85_mri-cgcm3_MurphyDome_10x10'
dvmdostem.work_dir='/data/workflows/MD1-S4-R'
dvmdostem.calib_mode='VEGC'
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=1, params=['cfall(0)','cfall(0)','cfall(0)','cfall(0)', \
                                       'cfall(1)','cfall(1)','cfall(1)', \
                                       'cfall(2)','cfall(2)','cfall(2)'], \
                               pftnums=[0,1,2,3, \
                                        0,1,2, \
                                        0,1,2])
"""
initial_guess=[0.0018, 0.065, 0.074, 0.014,
               0.0045, 0.0033, 0.004,    
               0.013, 0.0029, 0.023]

y_init=PyCall.py"run_TEM"(initial_guess)

function TEM_pycall(parameters::AbstractVector)
    predictions = PyCall.py"run_TEM"(parameters)
    return predictions
end
obs=PyCall.py"get_param_targets"()
obs_time=1:length(obs)

md = Mads.createproblem(initial_guess, obs, TEM_pycall;
    paramkey=["cfall00","cfall01","cfall02","cfall03",
              "cfall10","cfall11","cfall12",
              "cfall20","cfall21","cfall22"],
    paramdist=["Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)",
               "Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)",
               "Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)"],
    obstime=obs_time,
    #obsweight=[10,100,100,10,10,10,50,100,100,100,50,10,10,50,100,100],
    paramlog=trues(16),
    problemname="STEP4-MD1-R")

Mads.showparameters(md)
Mads.showobservations(md)

calib_random_results = Mads.calibraterandom(md, 10; seed=2023, all=true, tolOF=0.01, tolOFcount=4)

calib_random_estimates = hcat(map(i->collect(values(calib_random_results[i,3])), 1:10)...)

forward_predictions = Mads.forward(md, calib_random_estimates)
Mads.spaghettiplot(md, forward_predictions,
                       xtitle="# of observations", ytitle="VEGC(cfall)",filename="STEP4-MD1-R-matchplot.png")

save_csv(Mads.getparamkeys(md), Mads.getparamsmin(md), Mads.getparamsmax(md), initial_guess,
    Mads.getmadsrootname(md), Mads.getobsweight(md))

save_model_csv(md,Mads.getmadsrootname(md),forward_predictions)
