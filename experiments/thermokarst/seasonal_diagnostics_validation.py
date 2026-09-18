#!/usr/bin/env python3
"""Validate daily thermokarst diagnostics under periodic seasonal forcing."""
import argparse,csv,json,os,shutil,sys
from pathlib import Path
import numpy as np
from netCDF4 import Dataset
ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/"build/matplotlib-cache"))
saved=os.environ.get("PATH","")
if sys.platform=="darwin": os.environ["PATH"]=os.pathsep.join(x for x in saved.split(os.pathsep) if x not in ("/usr/sbin","/sbin"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
os.environ["PATH"]=saved
import production_validation as production

NAMES=["TKLIQGEN","TKLIQSTORAGE","TKLIQRUNOFF","TKLIQDRAINAGE","TKLIQOTHER","TKSUBSIDENCE","TKFRONT","TKFRONTTYPE"]
TEAL="#1F6F5F";INK="#171717";MUTED="#777772";LIGHT="#B9C1BE";GRID="#E3E7E5"

def make_climate(source,dest,cold=False):
  shutil.copy2(source,dest)
  t=np.array([-20.,-18.,-12.,-4.,4.,10.,12.,8.,2.,-5.,-12.,-18.]);p=np.array([8.,7.,6.,7.,10.,18.,24.,22.,16.,12.,9.,8.]);r=np.array([0.,2.,6.,12.,18.,22.,20.,14.,8.,3.,0.,0.])
  with Dataset(dest,"r+") as d:
    for i in range(d["tair"].shape[0]):
      m=i%12;d["tair"][i]=(-20. if cold else t[m]);d["precip"][i]=(0. if cold else p[m]);d["nirr"][i]=(0. if cold else r[m]);d["vapor_press"][i]=(1. if cold else 100.)
  return t,p,r

def make_spec(source,dest):
  rows=list(csv.DictReader(source.open()))
  for row in rows:
    row["Yearly"]=row["Monthly"]=row["Daily"]=""
    if row["Name"] in NAMES: row["Daily"]="d"
  with dest.open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator="\n");w.writeheader();w.writerows(rows)

def cfg(base,out,mask,climate,restart=None,diagnostics=True,tr_start=0):
  c=production.clone_config(base,out,mask,True,.20,climate,restart);c["model_settings"]["thermokarst"].update({"top_depth":.2,"bottom_depth":1.0});c["IO"]["output_nc_tr"]=int(diagnostics);c["IO"]["output_interval"]=1;c["stage_settings"]["tr_start_yr"]=int(tr_start);return c

def daily(directory):
  result={}
  for n in NAMES:
    with Dataset(directory/f"{n}_daily_tr.nc") as d: result[n]=np.asarray(np.ma.asarray(d[n][:,0,0]).filled(np.nan),float)
  return result

def maxdiff(a,b):
  good=np.isfinite(a)&np.isfinite(b);return float(np.max(np.abs(a[good]-b[good]))) if good.any() else 0.

def setup_style():
  plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8.5,"axes.titlesize":10,"axes.labelsize":9,"xtick.labelsize":8,"ytick.labelsize":8,"axes.spines.top":False,"axes.spines.right":False,"axes.edgecolor":INK,"text.color":INK,"axes.labelcolor":INK,"legend.frameon":False,"svg.fonttype":"none","figure.facecolor":"white","savefig.facecolor":"white"})

def save(fig,out,name):
  fig.savefig(out/f"{name}.png",dpi=240,bbox_inches="tight");fig.savefig(out/f"{name}.svg",bbox_inches="tight");plt.close(fig)

def main():
  ap=argparse.ArgumentParser();ap.add_argument("--binary",type=Path,default=ROOT/"dvmdostem");ap.add_argument("--output",type=Path,default=ROOT/"experiments/thermokarst/seasonal_diagnostics_results");a=ap.parse_args();out=a.output.resolve()
  if out.exists(): shutil.rmtree(out)
  out.mkdir(parents=True);base=production.parse_json_with_comments(ROOT/"config/config.js")
  for k,v in list(base["IO"].items()):
    if k.endswith("_file") or k=="parameter_dir": base["IO"][k]=str((ROOT/v).resolve())
  mask=out/"run-mask-one-cell.nc";shutil.copy2(base["IO"]["runmask_file"],mask)
  with Dataset(mask,"r+") as d: d["run"][...]=0;d["run"][0,0]=1
  climate=out/"seasonal-periodic-climate.nc";tair,precip,nirr=make_climate(Path(base["IO"]["hist_climate_file"]),climate)
  cold=out/"cold-periodic-climate.nc";make_climate(Path(base["IO"]["hist_climate_file"]),cold,True)
  spec=out/"diagnostic-output-spec.csv";make_spec(ROOT/"config/output_spec.csv",spec);base["IO"]["output_spec_file"]=str(spec)
  production.run_case(a.binary.resolve(),out,"seed",cfg(base,out/"seed",mask,cold,diagnostics=False),["--pr-yrs","1"]);seed=out/"seed/restart-pr.nc"
  for name,years,restart,diag in [("continuous",2,seed,True),("split-first",1,seed,True),("control",2,seed,False)]: production.run_case(a.binary.resolve(),out,name,cfg(base,out/name,mask,climate,restart,diag),["--tr-yrs",str(years)])
  middle=out/"split-first/restart-tr.nc";production.run_case(a.binary.resolve(),out,"resumed",cfg(base,out/"resumed",mask,climate,middle,True,1),["--tr-yrs","1"])
  cont=daily(out/"continuous");first=daily(out/"split-first");second=daily(out/"resumed");resume={n:np.r_[first[n],second[n]] for n in NAMES};days=np.arange(1,731)
  generated=np.cumsum(cont["TKLIQGEN"]);runoff=np.cumsum(cont["TKLIQRUNOFF"]);drain=np.cumsum(cont["TKLIQDRAINAGE"]);other=np.cumsum(cont["TKLIQOTHER"]);closure=cont["TKLIQSTORAGE"]+runoff+drain+other-generated;diffs={n:maxdiff(cont[n],resume[n]) for n in NAMES}
  cr=production.active_pixel_variables(out/"continuous/restart-tr.nc");rr=production.active_pixel_variables(out/"resumed/restart-tr.nc");pr=production.active_pixel_variables(out/"control/restart-tr.nc");exact=lambda x,y,names:all(np.array_equal(x[n],y[n],equal_nan=True) for n in names);physical=["TKversion","TKactive","TKstate","TKmatrix","TKporosity","TKexcess","DZsoil","TSsoil","LIQsoil","ICEsoil","FROZENsoil","FROZENFRACsoil","frontZ","frontFT","watertab"];all_names=cr.keys()&pr.keys();ft=cont["TKFRONTTYPE"]
  legacy_differences=[n for n in sorted(cr.keys()&rr.keys()) if not np.array_equal(cr[n],rr[n],equal_nan=True)]
  metrics={"forcing":{"monthly_tair_C":tair.tolist(),"monthly_precip_mm":precip.tolist(),"monthly_nirr":nirr.tolist(),"period_years":1},"total_generated_mm":float(generated[-1]),"final_storage_mm":float(cont["TKLIQSTORAGE"][-1]),"cumulative_runoff_mm":float(runoff[-1]),"cumulative_drainage_mm":float(drain[-1]),"cumulative_other_mm":float(other[-1]),"final_subsidence_m":float(cont["TKSUBSIDENCE"][-1]),"maximum_partition_closure_error_mm":float(np.nanmax(np.abs(closure))),"maximum_daily_restart_differences":diffs,"thawing_front_days":int(np.sum(ft==-1)),"freezing_front_days":int(np.sum(ft==1)),"thermokarst_physical_restart_fields_exact":exact(cr,rr,physical),"diagnostics_passive_exact":exact(cr,pr,all_names),"preexisting_nonexact_restart_fields":legacy_differences}
  checks=[]
  def gate(test,obs,criterion,passed): checks.append({"test":test,"observed":obs,"criterion":criterion,"status":"PASS" if passed else "FAIL"})
  gate("production runs complete","five runs","status=100",True);gate("seasonal excess-ice melt",metrics["total_generated_mm"],">0 mm",metrics["total_generated_mm"]>0);gate("freeze-thaw reversal",f"{metrics['thawing_front_days']}/{metrics['freezing_front_days']}","both >0",metrics["thawing_front_days"]>0 and metrics["freezing_front_days"]>0);gate("source-water partition closure",metrics["maximum_partition_closure_error_mm"],"<=1e-9 mm",metrics["maximum_partition_closure_error_mm"]<=1e-9);gate("daily diagnostics across restart",max(diffs.values()),"<=1e-12",max(diffs.values())<=1e-12);gate("thermokarst physical restart state",metrics["thermokarst_physical_restart_fields_exact"],"exact",metrics["thermokarst_physical_restart_fields_exact"]);gate("diagnostic output is passive",metrics["diagnostics_passive_exact"],"exact",metrics["diagnostics_passive_exact"])
  metrics["checks_passed"]=sum(x["status"]=="PASS" for x in checks);metrics["checks_total"]=len(checks);(out/"summary.json").write_text(json.dumps(metrics,indent=2)+"\n")
  with (out/"checks.csv").open("w",newline="") as f: w=csv.DictWriter(f,fieldnames=checks[0].keys(),lineterminator="\n");w.writeheader();w.writerows(checks)
  with (out/"daily-diagnostics.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["day"]+NAMES,lineterminator="\n");w.writeheader()
    for i in range(730): w.writerow({"day":i+1,**{n:cont[n][i] for n in NAMES}})
  setup_style()
  def marker(ax): ax.axvline(365,color=GRID,lw=1);ax.text(365,.98,"restart",transform=ax.get_xaxis_transform(),ha="center",va="top",color=MUTED,fontsize=7.5)
  fig,axes=plt.subplots(2,1,figsize=(7,5.1),sharex=True,layout="constrained");axes[0].plot(days,cont["TKLIQGEN"],color=TEAL,lw=1.2);axes[0].set(ylabel="Generated liquid (mm d⁻¹)",title="Excess-ice melt is confined to seasonal thaw periods");axes[1].plot(days,generated,color=TEAL,lw=1.7,label="Continuous");axes[1].plot(days,np.cumsum(resume["TKLIQGEN"]),"--",color=MUTED,lw=1.1,label="Restarted");axes[1].set(xlabel="Simulation day",ylabel="Cumulative generated liquid (mm)");axes[1].legend();[marker(x) for x in axes];[x.grid(axis="y",color=GRID,lw=.6) for x in axes];save(fig,out,"seasonal_liquid_generation")
  fig,ax=plt.subplots(figsize=(7,3.8),layout="constrained");ax.stackplot(days,cont["TKLIQSTORAGE"],runoff,drain,other,colors=[TEAL,"#A9B6B1","#D1D5D2","#ECEEEC"],labels=["Storage","Runoff","Drainage","Other"]);ax.plot(days,generated,color=INK,lw=1,label="Generated total");marker(ax);ax.set(xlabel="Simulation day",ylabel="Cumulative source water (mm)",title="Generated water closes to storage and routed losses");ax.legend(ncol=3,loc="upper left");save(fig,out,"seasonal_liquid_partition")
  fig,axes=plt.subplots(2,1,figsize=(7,4.8),sharex=True,layout="constrained");axes[0].plot(days,cont["TKLIQRUNOFF"],color=TEAL,lw=1,label="Runoff");axes[0].plot(days,cont["TKLIQDRAINAGE"],color=MUTED,lw=1,label="Drainage");axes[0].set(ylabel="Source-water flux (mm d⁻¹)",title="Daily routing of thermokarst-source liquid");axes[0].legend();axes[1].plot(days,closure,color=TEAL,lw=1);axes[1].axhline(0,color=INK,lw=.7);axes[1].set(xlabel="Simulation day",ylabel="Partition residual (mm)");[marker(x) for x in axes];[x.grid(axis="y",color=GRID,lw=.6) for x in axes];save(fig,out,"seasonal_liquid_routing")
  fig,ax=plt.subplots(figsize=(7,3.6),layout="constrained");ax.plot(days,cont["TKSUBSIDENCE"]*1000,color=TEAL,lw=1.7,label="Continuous");ax.plot(days,resume["TKSUBSIDENCE"]*1000,"--",color=MUTED,lw=1.1,label="Restarted");marker(ax);ax.set(xlabel="Simulation day",ylabel="Cumulative subsidence (mm)",title="Seasonal thaw drives restart-exact settlement");ax.grid(axis="y",color=GRID,lw=.6);ax.legend();save(fig,out,"seasonal_subsidence")
  fig,ax=plt.subplots(figsize=(7,3.8),layout="constrained");front=cont["TKFRONT"];ax.plot(days,front,color=LIGHT,lw=.8);ax.scatter(days,np.where(ft==-1,front,np.nan),s=5,color=TEAL,label="Thawing front (−1)");ax.scatter(days,np.where(ft==1,front,np.nan),s=5,color=MUTED,label="Freezing front (+1)");marker(ax);ax.invert_yaxis();ax.set(xlabel="Simulation day",ylabel="Leading front depth (m)",title="The leading front reverses with the seasonal cycle");ax.grid(axis="y",color=GRID,lw=.6);ax.legend();save(fig,out,"seasonal_front_trajectory")
  print(json.dumps(metrics,indent=2));failed=[x for x in checks if x["status"]=="FAIL"]
  if failed: raise RuntimeError(f"{len(failed)} checks failed")
if __name__=="__main__": main()
