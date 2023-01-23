# STEP2-R MD1
# parameters: nmax
# targets: NPP[8:12] with N limitation

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

    return dvmdostem.get_calibration_outputs()[8:12]

def get_param_targets():
    return dvmdostem.get_calibration_outputs(calib=True)[8:12]

dvmdostem=TEM.TEM_model()
dvmdostem.site='/data/input-catalog/cru-ts40_ar5_rcp85_mri-cgcm3_MurphyDome_10x10'
dvmdostem.work_dir='/data/workflows/MD1'
dvmdostem.calib_mode='NPPALL'
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=1, params=['nmax','nmax','nmax','nmax'], \
                               pftnums=[0,1,2,3])

"""
#initial_guess=[3.1, 2.5, 2.5, 2.1]
initial_guess=[2.95, 1.45, 1.07, 2.1]
#y_init=PyCall.py"run_TEM"(initial_guess)

function TEM_pycall(parameters::AbstractVector)
        predictions = PyCall.py"run_TEM"(parameters)
        return predictions
end
obs=PyCall.py"get_param_targets"()
obs_time=1:length(obs)

md = Mads.createproblem(initial_guess, obs, TEM_pycall;
    paramkey=["nmax0","nmax1","nmax2","nmax3"],
    paramdist=["Uniform(1, 50)","Uniform(1, 50)","Uniform(1, 50)","Uniform(1, 50)" ],
    obstime=obs_time,
    #obsweight=[100,10,10,10],
    problemname="STEP2-MD1-R-1")

Mads.showparameters(md)
Mads.showobservations(md)

#calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

#Mads.plotmatches(md, calib_param, 
#    xtitle="# of observations", ytitle="NPP",filename="STEP2-MD1_1_matchplot.png")

calib_random_results = Mads.calibraterandom(md, 20; seed=2023, all=true, tolOF=0.01, tolOFcount=4)

calib_random_estimates = hcat(map(i->collect(values(calib_random_results[i,3])), 1:20)...)

forward_predictions = Mads.forward(md, calib_random_estimates)
Mads.spaghettiplot(md, forward_predictions,
                       xtitle="# of observations", ytitle="NPP",filename="STEP2-MD1-R-1-matchplot.png")

save_csv(Mads.getparamkeys(md), Mads.getparamsmin(md), Mads.getparamsmax(md), initial_guess,
    Mads.getmadsrootname(md), Mads.getobsweight(md))
save_model_csv(md,Mads.getmadsrootname(md),forward_predictions)
