#STEP3-1
# parameters: cfall
# targets: NPPAll, VegCarbon(Leaf,Stem,Root)

#import Pkg; Pkg.add("PyCall")

import Mads
import PyCall
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

    return dvmdostem.get_calibration_outputs()[32:48]

def get_param_targets():
    return dvmdostem.get_calibration_outputs(calib=True)[32:48]

dvmdostem=TEM.TEM_model()
dvmdostem.calib_mode='VEGC'
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=5, params=['cfall(0)','cfall(0)','cfall(0)','cfall(0)','cfall(0)','cfall(0)','cfall(0)','cfall(0)', \
                                       'cfall(1)','cfall(1)','cfall(1)', \
                                       'cfall(2)','cfall(2)','cfall(2)','cfall(2)','cfall(2)'], \
                               pftnums=[0,1,2,3,4,5,6,7, \
                                        0,1,2, \
                                        0,1,2,3,4])
"""
initial_guess=[0.09, 0.11, 0.080, 0.057, 0.045, 0.096, 0.099, 0.04, 
               4.4595e-5, 0.0007, 0.0004,
               0.00138, 0.0003, 8.2057e-5, 0.021, 0.0003]
y_init=PyCall.py"run_TEM"(initial_guess)

function TEM_pycall(parameters::AbstractVector)
    predictions = PyCall.py"run_TEM"(parameters)
    return predictions
end
obs=PyCall.py"get_param_targets"()
obs_time=1:length(obs)

md = Mads.createproblem(initial_guess, obs, TEM_pycall;
    paramkey=["cfall00","cfall01","cfall02","cfall03","cfall04","cfall05","cfall06","cfall07",
              "cfall10","cfall11","cfall12",
              "cfall20","cfall21","cfall22","cfall23","cfall24","cfall25"],
    paramdist=["Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)",
        "Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)",
        "Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)",
        "Uniform(0.00001, 0.09)"],
    obstime=obs_time,
    obsweight=[10,100,100,10,10,10,50,100,100,100,50,10,10,50,100,100],
    paramlog=trues(16),
    problemname="Calibration_STEP3-1")

Mads.showparameters(md)
Mads.showobservations(md)

calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

Mads.plotmatches(md, calib_param, 
    xtitle="# of observations", ytitle="NPP/VEGC(Step3-1)",filename="NPPAllVEGC_Step3-1_matchplot.png")