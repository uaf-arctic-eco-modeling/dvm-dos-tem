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
    dvmdostem.run(calib=False)

    return dvmdostem.get_calibration_outputs()[-5:]

def get_param_targets():
    return dvmdostem.get_calibration_outputs(calib=True)[-5:]

dvmdostem=TEM.TEM_model()
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 2000 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=5, params=['micbnup','kdcrawc','kdcsoma','kdcsompr','kdcsomcr'], \
                               pftnums=[None,None,None,None,None])

"""

initial_guess=[0.7, 0.095, 0.027, 0.024, 0.000005]

#y_init=PyCall.py"run_TEM"(initial_guess)

function TEM_pycall(parameters::AbstractVector)
        predictions = PyCall.py"run_TEM"(parameters)
        return predictions
end
obs=PyCall.py"get_param_targets"()# VEGC only
obs_time=1:length(obs)
#SHLWC = 3079.00
#DEEPC = 7703.00
#MINEC = 43404.00
#AVLN = 0.8

md = Mads.createproblem(initial_guess, obs, TEM_pycall;
    paramkey=["micbnup", "kdcrawc", "kdcsoma", "kdcsompr", "kdcsomcr"],
    paramdist=["Uniform(1e-1, 2.0)","Uniform(1e-3, 0.99)","Uniform(5e-3, 0.5)",
               "Uniform(1e-3, 0.25)","Uniform(1e-7, 1e-5)"],
    obstime=obs_time,
    paramlog=[ falses(4); trues(1)  ], 
    obsweight=[ 100,100,100,0,100 ],  
    problemname="Calibration_SOIL")

#micbnup  	0.750000   	[0.1 to 2.0]  	target = AVLN    
#kdcrawc	0.09194	 	[0.01 to 0.99]	target = SHLWC 
#kdcsoma 	0.0230919    	[0.005 to 0.50]	target = SHLWC primarily and DEEPC secondary
#kdcsompr 	0.020800    	[0.001 to 0.25	target = DEEPC primarily and SHLWC and MINEC secondary
#kdcsomcr 	0.000005    	[0.000001 to 0.00001] 	target = MINEC 

Mads.showparameters(md)
Mads.showobservations(md)

calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

Mads.plotmatches(md, calib_param, 
                     xtitle="# of observations", ytitle="CSOIL", filename="STEP5_matchplot.png")
