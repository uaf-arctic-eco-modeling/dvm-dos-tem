# Autocalibration (AC) version 2.0
# grabs all above surface targets
# this version uses more target data in comparison to the old version 
# STEP3 MD1-CR
#       MD1-CR-S #sequential updating parameters
# parameters: nmax, krb
# targets: focus (NPP [8:12], VegCarbon(Leaf,Stem,Root) [12:22])

import Mads
import PyCall
@show pwd()

PyCall.py"""

import sys,os
sys.path.append(os.path.join('/work','scripts'))
import TEM

dvmdostem=TEM.TEM_model()
dvmdostem.site='/data/input-catalog/cru-ts40_ar5_rcp85_mri-cgcm3_MurphyDome_10x10'
dvmdostem.work_dir='/data/workflows/AC2-STEP3-MD1-C'
dvmdostem.calib_mode='VEGC' 
dvmdostem.opt_run_setup='--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
dvmdostem.set_params(cmtnum=1, params=['nmax','nmax','nmax','nmax', \
				       'krb(0)','krb(0)','krb(0)','krb(0)', \
                                       'krb(1)','krb(1)','krb(1)',  \
                                       'krb(2)','krb(2)','krb(2)' ], \
                               pftnums=[0,1,2,3, \
					0,1,2,3, \
                                        0,1,2, \
                                        0,1,2])
"""
initial_guess=[2.95, 1.45, 1.07, 2.1,
	       -6.0, -3.45, -2.95, -4.65,
	       -4.88, -5.15, -6.65,
	       -8.2, -6.2, -3.2]
y_init=PyCall.py"dvmdostem.run_TEM"(initial_guess)

function TEM_pycall(parameters::AbstractVector)
        predictions = PyCall.py"rdvmdostem.un_TEM"(parameters)
        return predictions
end

obs=PyCall.py"dvmdostem.get_targets"()
n_o=length(obs)
obs_time=1:n_o-6 #excluding soil carbon values
targets=obs[1:n_o-6]#grabbing only vegetation targets

md = Mads.createproblem(initial_guess, targets, TEM_pycall;
    paramkey=["nmax0","nmax1","nmax2","nmax3",
	      "krb00","krb01","krb02","krb03",
              "krb10","krb11","krb12",
              "krb20","krb21","krb22"],
    paramdist=[
	"Uniform(1, 5)","Uniform(1, 5)","Uniform(1, 5)","Uniform(1, 5)",       
        "Uniform(-20, -0.1)","Uniform(-20, -0.1)","Uniform(-20, -0.1)","Uniform(-20, -0.1)",
        "Uniform(-20, -0.1)","Uniform(-20, -0.1)","Uniform(-20, -0.1)",
        "Uniform(-20, -0.1)","Uniform(-20, -0.1)","Uniform(-20, -0.1)"],
    obstime=obs_time,
    #obsweight=[100,25,100,25,25,25,25,25,25,25],
    problemname="AC2-STEP3-MD1-C")

md["Problem"] = Dict{Any,Any}("ssdr"=>true)

Mads.showparameters(md)
Mads.showobservations(md)

localsa = Mads.localsa(md; filename="AC2-STEP3-MD1-CR-SA.png", par=initial_guess) 

#calib_random_results = Mads.calibraterandom(md, 10; seed=2023, all=true, tolOF=0.01, tolOFcount=4)

#calib_random_estimates = hcat(map(i->collect(values(calib_random_results[i,3])), 1:10)...)

#forward_predictions = Mads.forward(md, calib_random_estimates)
#Mads.spaghettiplot(md, forward_predictions,
#                       xtitle="# of observations", ytitle="NPP/VEGC",filename="AC2-STEP3-MD1-CR.png")
