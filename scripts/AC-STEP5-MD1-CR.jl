# STEP5-MD1-CR
# parameters: nmax, krb, cfall, nfall
# targets: NPP[8:12], VEGC[12:22], VEGN[22:32]

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

    return dvmdostem.get_calibration_outputs()[8:32]

def get_param_targets():
    return dvmdostem.get_calibration_outputs(calib=True)[8:32]

dvmdostem=TEM.TEM_model()
dvmdostem.site='/data/input-catalog/cru-ts40_ar5_rcp85_mri-cgcm3_MurphyDome_10x10'
dvmdostem.work_dir='/data/workflows/MD1-STEP5-CR'
dvmdostem.calib_mode='VEGN'
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=1, params=['nmax','nmax','nmax','nmax', \
                                       'krb(0)','krb(0)','krb(0)','krb(0)', \
                                       'krb(1)','krb(1)','krb(1)',  \
                                       'krb(2)','krb(2)','krb(2)', \
                                       'cfall(0)','cfall(0)','cfall(0)','cfall(0)', \
                                       'cfall(1)','cfall(1)','cfall(1)', \
                                       'cfall(2)','cfall(2)','cfall(2)', \
			               'nfall(0)','nfall(0)','nfall(0)','nfall(0)', \
                                       'nfall(1)','nfall(1)','nfall(1)', \
                                       'nfall(2)','nfall(2)','nfall(2)'], \
                               pftnums=[0,1,2,3, \
                                        0,1,2,3, \
                                        0,1,2, \
                                        0,1,2, \
                                        0,1,2,3, \
                                        0,1,2, \
                                        0,1,2, \
					0,1,2,3, \
                                        0,1,2, \
                                        0,1,2])
"""
initial_guess=[2.95, 1.45, 1.07, 2.1,
               -6.0, -3.45, -2.95, -4.65,
               -4.88, -5.15, -6.65,
               -8.2, -6.2, -3.2,
               0.0018, 0.065, 0.074, 0.014,
               0.0045, 0.0033, 0.004,    
               0.013, 0.0029, 0.023,
	       0.011, 0.028, 0.028, 0.009, 
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
    paramkey=["nmax0","nmax1","nmax2","nmax3",
              "krb00","krb01","krb02","krb03",
              "krb10","krb11","krb12",
              "krb20","krb21","krb22",
              "cfall00","cfall01","cfall02","cfall03",
              "cfall10","cfall11","cfall12",
              "cfall20","cfall21","cfall22",
	      "nfall00","nfall01","nfall02","nfall03",
              "nfall10","nfall11","nfall12",
              "nfall20","nfall21","nfall22"],
    paramdist=["Uniform(1, 50)","Uniform(1, 50)","Uniform(1, 50)","Uniform(1, 50)",
               "Uniform(-20, -0.1)","Uniform(-20, -0.1)","Uniform(-20, -0.1)","Uniform(-20, -0.1)",
               "Uniform(-20, -0.1)","Uniform(-20, -0.1)","Uniform(-20, -0.1)",
               "Uniform(-20, -0.1)","Uniform(-20, -0.1)","Uniform(-20, -0.1)",
               "Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)",
               "Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)",
               "Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)",
               "Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)",
               "Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)",
               "Uniform(1e-7, 0.09)","Uniform(1e-7, 0.09)","Uniform(1e-7, 0.09)"],
    obstime=obs_time,
    #obsweight=[10,100,100,10,10,10,50,100,100,100,50,10,10,50,100,100],
    paramlog=[falses(4); falses(10); trues(10); trues(10)],
    problemname="STEP5-MD1-CR")

Mads.showparameters(md)
Mads.showobservations(md)

calib_random_results = Mads.calibraterandom(md, 10; seed=2023, all=true, tolOF=0.01, tolOFcount=4)

calib_random_estimates = hcat(map(i->collect(values(calib_random_results[i,3])), 1:10)...)

forward_predictions = Mads.forward(md, calib_random_estimates)
Mads.spaghettiplot(md, forward_predictions,
                       xtitle="# of observations", ytitle="NPP, VEGC, VEGN",filename="STEP5-MD1-CR-matchplot.png")

save_csv(Mads.getparamkeys(md), Mads.getparamsmin(md), Mads.getparamsmax(md), initial_guess,
    Mads.getmadsrootname(md), Mads.getobsweight(md))

save_model_csv(md,Mads.getmadsrootname(md),forward_predictions)

