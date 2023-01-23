# STEP6-MD1
# parameters: micbnup, kdcrawc, kdcsoma, kdcsompr, kdcsomcr
# NOTE: that order is important micbnup > kdcrawc > kdcsoma > kdcsompr > kdcsomcr 
# targets: SoilC [-5:] (AVLN,SHLWC,SHLWC,DEEPC,MINEC)
# NOTE: weight for the target #4 is zero

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
dvmdostem.site='/data/input-catalog/cru-ts40_ar5_rcp85_mri-cgcm3_MurphyDome_10x10'
dvmdostem.work_dir='/data/workflows/STEP6-MD1'

dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 2000 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=1, params=['micbnup','kdcrawc','kdcsoma','kdcsompr','kdcsomcr'], \
                               pftnums=[None,None,None,None,None])
"""
#0.449500     // micbnup: 
#0.634000     // kdcrawc: 
#0.540000     // kdcsoma: 
#0.002000     // kdcsompr: 
#0.000070     // kdcsomcr: 

initial_guess=[0.4495, 0.634, 0.54, 0.002, 0.00007]
y_init=PyCall.py"run_TEM"(initial_guess)
print(y_init)

function TEM_pycall(parameters::AbstractVector)
        predictions = PyCall.py"run_TEM"(parameters)
        return predictions
end
obs=PyCall.py"get_param_targets"()
obs_time=1:length(obs)
print(obs)

#Targets:
#  'MossDeathC':              178.00,    #  dmossc
#1.'CarbonShallow':           888.91,    #  shlwc
#2.'CarbonDeep':             3174.53,    #  deepc
#3.'CarbonMineralSum':      19821.50,    #  minec
#  'OrganicNitrogenSum':     1086.31,    #  soln
#4.'AvailableNitrogenSum':      0.76,    #  avln


md = Mads.createproblem(initial_guess, obs, TEM_pycall;
    paramkey=["micbnup", "kdcrawc", "kdcsoma", "kdcsompr", "kdcsomcr"],
    paramdist=["Uniform(1e-1, 2.0)","Uniform(1e-3, 0.99)","Uniform(5e-3, 0.6)",
               "Uniform(1e-3, 0.25)","Uniform(1e-7, 1e-4)"],
    obstime=obs_time,
    paramlog=[ falses(4); trues(1)  ], 
    obsweight=[ 100,100,100,0,100 ],  
    problemname="STEP6-MD1")

#kdcrawc	0.634	 	[0.01 to 0.99]	target = SHLWC 
#kdcsoma 	0.54    	[0.005 to 0.60]	target = SHLWC primarily and DEEPC secondary
#kdcsompr 	0.002    	[0.001 to 0.25]	target = DEEPC primarily and SHLWC and MINEC secondary
#kdcsomcr 	0.00007    	[0.000001 to 0.00001] 	target = MINEC 

Mads.showparameters(md)
Mads.showobservations(md)

calib_param, calib_information = Mads.calibrate(md, tolOF=0.01, tolOFcount=4)

Mads.plotmatches(md, calib_param, 
    xtitle="# of observations", ytitle="CSOIL",filename="STEP6-MD1-matchplot.png")

save_csv(Mads.getparamkeys(md), Mads.getparamsmin(md), Mads.getparamsmax(md), initial_guess,
    Mads.getmadsrootname(md), Mads.getobsweight(md))

forward_predictions = Mads.forward(md, calib_param)
save_model_csv(md,Mads.getmadsrootname(md),forward_predictions)
