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
    dvmdostem.run(calib=True)

    return dvmdostem.get_calibration_outputs()[:8]

def get_param_targets():
    return dvmdostem.get_calibration_outputs(calib=True)[:8]

dvmdostem=TEM.TEM_model()
dvmdostem.calib_mode='GPPAllIgnoringNitrogen'
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=5, params=['cmax','cmax','cmax','cmax','cmax','cmax','cmax','cmax'], \
                               pftnums=[0,1,2,3,4,5,6,7])
"""
#y_init=PyCall.py"run_TEM"([134.4, 4.4, 337.6, 594.0, 3.5, 32.3, 90.3, 47.3])
#y_truth_cmax_gpp=PyCall.py"run_TEM"([134.4, 4.4, 337.6, 594.0, 3.5, 32.3, 90.3, 47.3])

function TEM_pycall(parameters::AbstractVector)
        predictions = PyCall.py"run_TEM"(parameters)
        return predictions
end
initial_guess=[134.4, 4.4, 337.6, 594.0, 3.5, 32.3, 90.3, 47.3]#[142.1, 33.6, 239.8, 473.8, 27.3, 20.0, 102.8, 62.4]
obs=PyCall.py"get_param_targets"()
obs_time=1:length(obs)

md = Mads.createproblem(initial_guess, obs, TEM_pycall;
    paramkey=["cmax0","cmax1","cmax2","cmax3","cmax4","cmax5","cmax6","cmax7"],
    paramdist=["Uniform(0.1, 200)","Uniform(0.1, 90)","Uniform(0.1, 350)","Uniform(0.1, 600)",
               "Uniform(0.1, 50)","Uniform(0.1, 350)","Uniform(0.1, 200)","Uniform(0.1, 150)"],
    obstime=obs_time,
    obsweight=[10,50,100,100,50,10,10,10],
    problemname="Calibration_STEP1")

Mads.showparameters(md)
Mads.showobservations(md)

calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

Mads.plotmatches(md, calib_param, 
    xtitle="# of observations", ytitle="CSOIL",filename="CSOIL_matchplot.png")