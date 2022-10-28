#STEP4
# parameters: cfall, krb, nfall
# targets: NPPAll, VegCarbon(Leaf,Stem,Root), VegStructuralNitrogen(Leaf,Stem,Root)

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

    return dvmdostem.get_calibration_outputs()[24:64]

def get_param_targets():
    return dvmdostem.get_calibration_outputs(calib=True)[24:64]#[24:48]

dvmdostem=TEM.TEM_model()
dvmdostem.calib_mode='VEGC'
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=5, params=['cfall(0)','cfall(0)','cfall(0)','cfall(0)','cfall(0)','cfall(0)','cfall(0)','cfall(0)', \
                                       'cfall(1)','cfall(1)','cfall(1)', \
                                       'cfall(2)','cfall(2)','cfall(2)','cfall(2)','cfall(2)', \
                                       'krb(0)','krb(0)','krb(0)','krb(0)','krb(0)','krb(0)','krb(0)','krb(0)', \
                                       'krb(1)','krb(1)','krb(1)',  \
                                       'krb(2)','krb(2)','krb(2)','krb(2)','krb(2)', \
                                       'nfall(0)','nfall(0)','nfall(0)','nfall(0)','nfall(0)','nfall(0)','nfall(0)','nfall(0)', \
                                       'nfall(1)','nfall(1)','nfall(1)', \
                                       'nfall(2)','nfall(2)','nfall(2)','nfall(2)','nfall(2)'], \
                               pftnums=[0,1,2,3,4,5,6,7, \
                                        0,1,2, \
                                        0,1,2,3,4, \
                                        0,1,2,3,4,5,6,7, \
                                        0,1,2, \
                                        0,1,2,3,4, \
                                        0,1,2,3,4,5,6,7, \
                                        0,1,2, \
                                        0,1,2,3,4])
"""

initial_guess=[0.09, 0.11, 0.080, 0.057, 0.045, 0.096, 0.099, 0.04, 
               4.4595e-5, 0.0007, 0.0004,
               0.00138, 0.0003, 8.2057e-5, 0.021, 0.0003,
                -0.10, -0.22, -2.29, -1.22, -3.3, -0.15, -0.1, -1.24, 
                -7.27, -5.58, -5.77, 
                -6.63, -6.3, -3.86, -0.81, -4.32,
                0.00001, 0.00002, 0.000014, 0.00007, 0.0001, 0.0010, 0.00353, 0.0001,
                0.000001, 0.000159, 0.000017,
                0.00001, 0.010048, 0.000008, 0.00688, 0.000013]

#y_init=PyCall.py"run_TEM"()

function TEM_pycall(parameters::AbstractVector)
        predictions = PyCall.py"run_TEM"(parameters)
        return predictions
end
obs=PyCall.py"get_param_targets"()
obs_time=1:length(obs)

md = Mads.createproblem(initial_guess, obs, TEM_pycall;
    paramkey=["cfall00","cfall01","cfall02","cfall03","cfall04","cfall05","cfall06","cfall07",
              "cfall10","cfall11","cfall12",
              "cfall20","cfall21","cfall22","cfall23","cfall24",
              "krb00","krb01","krb02","krb03","krb04","krb05","krb06","krb07",
              "krb10","krb11","krb12",
              "krb20","krb21","krb22","krb23","krb24",
              "nfall00","nfall01","nfall02","nfall03","nfall04","nfall05","nfall06","nfall07",
              "nfall10","nfall11","nfall12",
              "nfall20","nfall21","nfall22","nfall23","nfall24"],
    paramdist=["Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)",
        "Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.2)","Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)",
        "Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)","Uniform(0.00001, 0.09)",
        "Uniform(0.00001, 0.09)",
        "Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-15, -0.1)","Uniform(-10, -0.1)",
        "Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)",
        "Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)",
        "Uniform(-10, -0.1)",
        "Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)",
        "Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)","Uniform(1e-7, 0.2)","Uniform(1e-7, 0.09)","Uniform(1e-7, 0.09)",
        "Uniform(1e-7, 0.09)","Uniform(1e-7, 0.09)","Uniform(1e-7, 0.09)","Uniform(1e-7, 0.09)","Uniform(1e-7, 0.09)",
        "Uniform(1e-7, 0.09)"],
    obstime=obs_time,
    paramlog=[trues(16); falses(16); trues(16)],
    problemname="Calibration_STEP4")

Mads.showparameters(md)
Mads.showobservations(md)

calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

Mads.plotmatches(md, calib_param, 
                xtitle="# of observations", ytitle="NPP/VEGC/VEGN",filename="Step4_matchplot.png")