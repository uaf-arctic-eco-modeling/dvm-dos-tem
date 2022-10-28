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

    return dvmdostem.get_calibration_outputs()[16:24]

def get_param_targets():
    return dvmdostem.get_calibration_outputs(calib=True)[16:24]

dvmdostem=TEM.TEM_model()
dvmdostem.calib_mode='NPPAll'
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=5, params=['cmax','cmax','cmax','cmax','cmax','cmax','cmax','cmax', \
                                       'nmax','nmax','nmax','nmax','nmax','nmax','nmax','nmax'], \
                               pftnums=[0,1,2,3,4,5,6,7, \
                                        0,1,2,3,4,5,6,7])
"""
initial_guess=[134.4, 4.4, 337.6, 594.0, 3.5, 32.3, 90.3, 47.3, 
               7.0, 8.2, 9.0, 27.6, 4.5, 3.0, 3.0, 3.0]
y_init=PyCall.py"run_TEM"(initial_guess)

function TEM_pycall(parameters::AbstractVector)
        predictions = PyCall.py"run_TEM"(parameters)
        return predictions
end
obs=PyCall.py"get_param_targets"()
obs_time=1:length(obs)

md = Mads.createproblem(initial_guess, obs, TEM_pycall;
    paramkey=["cmax0","cmax1","cmax2","cmax3","cmax4","cmax5","cmax6","cmax7",
              "nmax0","nmax1","nmax2","nmax3","nmax4","nmax5","nmax6","nmax7"],
    paramdist=["Uniform(0.1, 200)","Uniform(0.1, 90)","Uniform(0.1, 350)","Uniform(0.1, 600)",
               "Uniform(0.1, 50)","Uniform(0.1, 350)","Uniform(0.1, 200)","Uniform(0.1, 150)",
               "Uniform(1, 20)","Uniform(1, 20)","Uniform(1, 20)","Uniform(1, 50)",
               "Uniform(1, 20)","Uniform(1, 20)","Uniform(1, 20)","Uniform(1, 20)"],
    obstime=obs_time,
    #obsweight=[100,100,100,100,100,100,100,100],
    problemname="Calibration_STEP2-1")

Mads.showparameters(md)
Mads.showobservations(md)

calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

Mads.plotmatches(md, calib_param, 
    xtitle="# of observations", ytitle="NPP(Step2-1)",filename="Step2-1_matchplot.png")
