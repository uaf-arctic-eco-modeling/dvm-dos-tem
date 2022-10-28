#STEP3-1
# parameters: krb
# targets: NPPAll, VegCarbon(Leaf,Stem,Root)

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

    return dvmdostem.get_calibration_outputs()[24:32] #NPP

def get_param_targets():
    return dvmdostem.get_calibration_outputs(calib=True)[24:32] #NPP

dvmdostem=TEM.TEM_model()
dvmdostem.calib_mode='VEGC' 
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=5, params=['krb(0)','krb(0)','krb(0)','krb(0)','krb(0)','krb(0)','krb(0)','krb(0)', \
                                       'krb(1)','krb(1)','krb(1)',  \
                                       'krb(2)','krb(2)','krb(2)','krb(2)','krb(2)' ], \
                               pftnums=[0,1,2,3,4,5,6,7, \
                                        0,1,2, \
                                        0,1,2,3,4])
"""
initial_guess=[-0.5, -3.1, -3.0, -9.9,  -1.0,  -1.5,  -3.2, -5.7, 
               -6.5, -6.3, -4.7, -5.45, -5.56, -4.05, -2.1, -3.9]
y_init=PyCall.py"run_TEM"(initial_guess)

function TEM_pycall(parameters::AbstractVector)
        predictions = PyCall.py"run_TEM"(parameters)
        return predictions
end
obs=PyCall.py"get_param_targets"()#include NPP
obs_time=1:length(obs)

md = Mads.createproblem(initial_guess, obs, TEM_pycall;
    paramkey=["krb00","krb01","krb02","krb03","krb04","krb05","krb06","krb07",
              "krb10","krb11","krb12",
              "krb20","krb21","krb22","krb23","krb24"],
    paramdist=[
        "Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-15, -0.1)","Uniform(-10, -0.1)",
        "Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)",
        "Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)","Uniform(-10, -0.1)",
        "Uniform(-10, -0.1)"],
    obstime=obs_time,
    #obsweight=[100,10,10,10,10,10,10,10,90,100,50,10,10,10,50,100,100,100,50,10,10,50,100,100],
    problemname="Calibration_STEP3")

Mads.showparameters(md)
Mads.showobservations(md)

#local sensitivity analysis
#localsa = Mads.localsa(md; filename="model_diagnostics.png", par=initial_guess)
#Mads.display("model_diagnostics-jacobian.png")
#Mads.display("model_diagnostics-eigenmatrix.png")
#Mads.display("model_diagnostics-eigenvalues.png")

calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

Mads.plotmatches(md, calib_param, 
    xtitle="# of observations", ytitle="GPPAll(Step3)",filename="GPPAll_Step3_matchplot.png")