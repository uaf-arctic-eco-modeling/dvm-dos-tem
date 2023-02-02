# STEP1 MD1
# parameters: cmax
# targets: GPP[1:4], Nitrogen unlimited mode
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

    return dvmdostem.get_calibration_outputs()[:4]

def get_param_targets():
    return dvmdostem.get_calibration_outputs(calib=True)[:4]

dvmdostem=TEM.TEM_model()

dvmdostem.site='/data/input-catalog/cru-ts40_ar5_rcp85_mri-cgcm3_MurphyDome_10x10'
dvmdostem.work_dir='/data/workflows/STEP1-MD1'
dvmdostem.calib_mode='GPPAllIgnoringNitrogen'
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=1, params=['cmax','cmax','cmax','cmax'], \
                               pftnums=[0,1,2,3])
"""

function TEM_pycall(parameters::AbstractVector)
        predictions = PyCall.py"run_TEM"(parameters)
        return predictions
end
initial_guess=[381.19, 113.93, 207.08, 93.31]

y_init=PyCall.py"run_TEM"(initial_guess)
obs=PyCall.py"get_param_targets"()
obs_time=1:length(obs)

md = Mads.createproblem(initial_guess, obs, TEM_pycall;
    paramkey=["cmax0","cmax1","cmax2","cmax3"],
    paramdist=["Uniform(0.1, 500)","Uniform(0.1, 200)","Uniform(0.1, 300)","Uniform(0.1, 200)"],
    obstime=obs_time,
    obsweight=[100,100,100,100],
    problemname="STEP1-MD1-EJ")

Mads.showparameters(md)
Mads.showobservations(md)

calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

Mads.plotmatches(md, calib_param, 
    xtitle="# of observations", ytitle="GPP",filename="STEP1-MD1_matchplot.png")

save_csv(Mads.getparamkeys(md), Mads.getparamsmin(md), Mads.getparamsmax(md), initial_guess,
    Mads.getmadsrootname(md), Mads.getobsweight(md))

forward_predictions = Mads.forward(md, calib_param)
save_model_csv(md,Mads.getmadsrootname(md),forward_predictions)
