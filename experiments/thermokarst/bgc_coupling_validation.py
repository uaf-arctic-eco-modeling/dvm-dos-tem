#!/usr/bin/env python3
"""Gated production validation for thermokarst, hydrology, BGC, and DSL."""
import argparse,csv,json,os,shutil,subprocess,sys
from pathlib import Path
import numpy as np
from netCDF4 import Dataset

ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/"build/matplotlib-cache"))
saved_path=os.environ.get("PATH","")
if sys.platform=="darwin": os.environ["PATH"]=os.pathsep.join(x for x in saved_path.split(os.pathsep) if x not in ("/usr/sbin","/sbin"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
os.environ["PATH"]=saved_path
import production_validation as production

CELLS=[(0,0),(0,1)]; CMTS=[4,5]
TK=["TKLIQGEN","TKLIQSTORAGE","TKLIQRUNOFF","TKLIQDRAINAGE","TKLIQOTHER","TKSUBSIDENCE","TKFRONT","TKFRONTTYPE"]
BGC=["GPP","NPP","RHSOM","RHDWD","SOC","VEGC","AVLN","ORGN","VEGNTOT","NINPUT","NLOST"]
TEAL="#1F6F5F"; BLUE="#4C78A8"; ORANGE="#D55E00"; INK="#171717"; MUTED="#777772"; GRID="#E3E7E5"

def absolute_io(base):
  for k,v in list(base["IO"].items()):
    if not v: continue
    if k.endswith("_file") or k=="parameter_dir": base["IO"][k]=str((ROOT/v).resolve())

def copy_spatial(base,out):
  mask=out/"run-mask-two-cells.nc";shutil.copy2(base["IO"]["runmask_file"],mask)
  with Dataset(mask,"r+") as d:
    d["run"][:]=0
    for y,x in CELLS:d["run"][y,x]=1
  base["IO"]["runmask_file"]=str(mask)
  for key,var in [("veg_class_file","veg_class"),("drainage_file","drainage_class"),("topo_file","slope")]:
    src=Path(base["IO"][key]);dst=out/src.name;shutil.copy2(src,dst)
    with Dataset(dst,"r+") as d:
      for i,(y,x) in enumerate(CELLS): d[var][y,x]=CMTS[i] if var=="veg_class" else (0 if var=="drainage_class" else 30.)
    base["IO"][key]=str(dst)

def make_climate(source,dest):
  shutil.copy2(source,dest)
  tair=np.array([-20.,-18.,-12.,-4.,4.,10.,12.,8.,2.,-5.,-12.,-18.])
  precip=np.array([8.,7.,6.,7.,10.,200.,200.,22.,16.,12.,9.,8.])
  nirr=np.array([0.,2.,6.,12.,18.,22.,20.,14.,8.,3.,0.,0.])
  with Dataset(dest,"r+") as d:
    for i in range(d["tair"].shape[0]):
      m=i%12;d["tair"][i]=tair[m];d["precip"][i]=precip[m];d["nirr"][i]=nirr[m];d["vapor_press"][i]=100.
  return tair,precip,nirr

def make_spec(source,dest):
  rows=list(csv.DictReader(source.open()))
  for r in rows:
    r["Yearly"]=r["Monthly"]=r["Daily"]=""
    if r["Name"] in TK:r["Daily"]="d"
    if r["Name"] in BGC:r["Yearly"]="y"
  with dest.open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator="\n");w.writeheader();w.writerows(rows)

def slice_driver_years(source,dest,start,nyears):
  """Copy a driver file so year 0 is calendar year `start` of the source."""
  shutil.copy2(source,dest)
  if nyears<=0: return dest
  with Dataset(source) as src, Dataset(dest,"r+") as dst:
    for name,var in dst.variables.items():
      if not var.dimensions: continue
      dim0=var.dimensions[0]
      if dim0 not in ("time","year"): continue
      data=np.asarray(src[name][:])
      n=data.shape[0]
      monthly=dim0=="time" and n%12==0 and n>=(start+nyears)*12
      if monthly:
        var[:nyears*12]=data[start*12:(start+nyears)*12]
      elif n>=start+nyears:
        var[:nyears]=data[start:start+nyears]
  return dest

def slice_resume_drivers(base,out,prefix,start,nyears,fire_file=None):
  """Shift historic climate, CO2, and optional fire so resume year 0 is source year `start`."""
  climate=Path(base["IO"]["hist_climate_file"])
  co2=Path(base["IO"]["co2_file"])
  base=json.loads(json.dumps(base))
  base["IO"]["hist_climate_file"]=str(slice_driver_years(climate,out/f"{prefix}-climate.nc",start,nyears))
  base["IO"]["co2_file"]=str(slice_driver_years(co2,out/f"{prefix}-co2.nc",start,nyears))
  if fire_file is not None:
    base["IO"]["hist_exp_fire_file"]=str(slice_driver_years(Path(fire_file),out/f"{prefix}-fire.nc",start,nyears))
  return base

def config(base,directory,restart=None,dsl=False,output=True,tr_start=0):
  c=json.loads(json.dumps(base));io=c["IO"];io["output_dir"]=str(directory)+"/";io["restart_from"]=str(restart) if restart else ""
  io["output_nc_eq"]=io["output_nc_pr"]=io["output_nc_sp"]=0;io["output_nc_tr"]=int(output);io["output_nc_sc"]=0;io["output_interval"]=1;io["output_monthly"]=0
  c["model_settings"]["thermokarst"]={"enabled":True,"excess_fraction":0.,"top_depth":.2,"bottom_depth":1.0}
  for stage in ["pr","eq","sp","tr","sc"]:
    c["stage_settings"][stage].update({"env":True,"bgc":True,"nfeed":True,"avlnflg":True,"baseline":False,"dsb":False,"dsl":dsl,"dyn_lai":True})
  c["stage_settings"]["tr_start_yr"]=int(tr_start)
  return c

def run(binary,out,name,cfg,args):
  run_dir=out/name
  if run_dir.exists(): shutil.rmtree(run_dir)
  path=out/f"{name}.json";path.write_text(json.dumps(cfg,indent=2)+"\n")
  cmd=[str(binary),"-f",str(path),"--log-level","warn","--max-output-volume=-1"]+args
  with (out/f"{name}.log").open("w") as log: done=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
  if done.returncode: raise RuntimeError(f"{name} exited {done.returncode}; see {out/f'{name}.log'}")
  with Dataset(out/name/"run_status.nc") as d:
    status=[int(d["run_status"][y,x]) for y,x in CELLS]
  if status!=[100,100]: raise RuntimeError(f"{name} statuses {status}")
  return status

def completed(out,name):
  path=out/name/"run_status.nc"
  if not path.exists(): return None
  with Dataset(path) as d: status=[int(d["run_status"][y,x]) for y,x in CELLS]
  return status if status==[100,100] else None

def inject_excess(source,dest,fraction=.2,top=.2,bottom=1.0):
  shutil.copy2(source,dest);before={}
  with Dataset(dest,"r+") as d:
    for cell in CELLS:
      y,x=cell;n=int(d["numsl"][y,x]);z=0.;added=0.
      for j in range(n):
        matrix=float(d["TKmatrix"][y,x,j]);overlap=max(0.,min(z+matrix,bottom)-max(z,top))
        temperature=float(d["TSsoil"][y,x,j])
        if overlap and temperature>1.e-8: raise RuntimeError(f"injection layer is thawed: {cell} layer {j}")
        if overlap and temperature>0.: d["TSsoil"][y,x,j]=0. # roundoff at the phase boundary
        mass=917.*overlap*fraction/(1.-fraction);d["TKexcess"][y,x,j]=mass;d["DZsoil"][y,x,j]=matrix+mass/917.;added+=mass;z+=matrix
      before[str(cell)]=added
  return before

def inject_excess_mass(source,dest,mass,depth=.20):
  """Place `mass` kg m-2 of excess ice in the soil layer that contains `depth` m."""
  if not (np.isfinite(mass) and mass>=0.): raise ValueError("invalid excess-ice mass")
  shutil.copy2(source,dest);before={}
  with Dataset(dest,"r+") as d:
    for cell in CELLS:
      y,x=cell;n=int(d["numsl"][y,x]);z=0.;added=0.;placed=False
      for j in range(n):
        matrix=float(d["TKmatrix"][y,x,j])
        contains=z<=depth<z+matrix or (j==n-1 and z+matrix>=depth)
        if contains:
          temperature=float(d["TSsoil"][y,x,j])
          if mass and temperature>1.e-8: raise RuntimeError(f"injection layer is thawed: {cell} layer {j}")
          if temperature>0.: d["TSsoil"][y,x,j]=0.
          d["TKexcess"][y,x,j]=float(mass);d["DZsoil"][y,x,j]=matrix+mass/917.;added=float(mass);placed=True;break
        z+=matrix
      if not placed: raise RuntimeError(f"no layer contains depth {depth} m at {cell}")
      before[str(cell)]=added
  return before

def read_daily(directory,name):
  with Dataset(directory/f"{name}_daily_tr.nc") as d:return np.asarray(np.ma.asarray(d[name][:]).filled(np.nan),float)

def read_yearly(directory,name):
  with Dataset(directory/f"{name}_yearly_tr.nc") as d:return np.asarray(np.ma.asarray(d[name][:]).filled(np.nan),float)

def cell_series(array,cell):return array[(slice(None),)+cell]

def restart_values(path,cell):
  result={}
  with Dataset(path) as d:
    y,x=cell
    for n,v in d.variables.items():
      if v.dimensions[:2]==("Y","X"): result[n]=np.asarray(np.ma.filled(v[y,x],0))
  return result

def inventory(path,cell):
  with Dataset(path) as d:
    y,x=cell;n=int(d["numsl"][y,x]);
    clean=lambda value:np.asarray(np.ma.asarray(value).filled(0.),float)
    soilc=sum(float(np.sum(clean(d[k][y,x,:n]))) for k in ["rawc","soma","sompr","somcr"])
    soiln=sum(float(np.sum(clean(d[k][y,x,:n]))) for k in ["orgn","avln"])
    vegc=clean(d["vegc"][y,x]);ratio=clean(d["vegC2N"][y,x])
    vegc_total=float(np.sum(vegc));vegn=float(np.sum(np.divide(vegc,ratio,out=np.zeros_like(vegc),where=ratio>0)))
    return {"C":soilc+vegc_total+float(np.sum(clean(d["deadc"][y,x]))),"N":soiln+vegn+float(np.sum(clean(d["deadn"][y,x]))),"SOC":soilc,"VEGC":vegc_total,"layers":n,"thickness":float(np.sum(clean(d["DZsoil"][y,x,:n])))}

def maxdiff(a,b):
  good=np.isfinite(a)&np.isfinite(b);return float(np.max(np.abs(a[good]-b[good]))) if good.any() else 0.

def style():
  plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8.5,"axes.titlesize":10,"axes.labelsize":9,"axes.spines.top":False,"axes.spines.right":False,"axes.edgecolor":INK,"text.color":INK,"axes.labelcolor":INK,"legend.frameon":False,"svg.fonttype":"none","figure.facecolor":"white","savefig.facecolor":"white"})

def save(fig,out,name):
  fig.savefig(out/f"{name}.png",dpi=240,bbox_inches="tight");fig.savefig(out/f"{name}.svg",bbox_inches="tight");plt.close(fig)

def main():
  ap=argparse.ArgumentParser();ap.add_argument("--binary",type=Path,default=ROOT/"dvmdostem");ap.add_argument("--output",type=Path,default=ROOT/"experiments/thermokarst/bgc_coupling_validation_results");ap.add_argument("--years",type=int,default=10);ap.add_argument("--reuse",action="store_true",help="reuse completed production cases in the output directory");a=ap.parse_args();out=a.output.resolve()
  if out.exists() and not a.reuse:shutil.rmtree(out)
  out.mkdir(parents=True,exist_ok=True);base=production.parse_json_with_comments(ROOT/"config/config.js");absolute_io(base);copy_spatial(base,out)
  tair,precip,nirr=make_climate(Path(base["IO"]["hist_climate_file"]),out/"periodic-rain-on-thaw-climate.nc");base["IO"]["hist_climate_file"]=str(out/"periodic-rain-on-thaw-climate.nc")
  spec=out/"validation-output-spec.csv";make_spec(ROOT/"config/output_spec.csv",spec);base["IO"]["output_spec_file"]=str(spec)
  statuses={};statuses["initialization"]=completed(out,"initialization") if a.reuse else None
  if statuses["initialization"] is None: statuses["initialization"]=run(a.binary.resolve(),out,"initialization",config(base,out/"initialization",output=False),["--pr-yrs","1","--eq-yrs","5"])
  initial=out/"initialization/restart-eq.nc";injected=out/"restart-with-excess.nc";added=inject_excess(initial,injected)
  half=a.years//2
  for name,restart,years,dsl in [("control",initial,a.years,False),("active",injected,a.years,False),("split-first",injected,half,False),("dynamic-soil",initial,5,True)]:
    statuses[name]=completed(out,name) if a.reuse else None
    if statuses[name] is None: statuses[name]=run(a.binary.resolve(),out,name,config(base,out/name,restart,dsl),["--tr-yrs",str(years)])
  statuses["resumed"]=completed(out,"resumed") if a.reuse else None
  if statuses["resumed"] is None:
    statuses["resumed"]=run(a.binary.resolve(),out,"resumed",config(base,out/"resumed",out/"split-first/restart-tr.nc",tr_start=half),["--tr-yrs",str(a.years-half)])

  daily={n:read_daily(out/"active",n) for n in TK};first={n:read_daily(out/"split-first",n) for n in TK};second={n:read_daily(out/"resumed",n) for n in TK};resumed={n:np.concatenate([first[n],second[n]],axis=0) for n in TK}
  yearly={case:{n:read_yearly(out/case,n) for n in BGC} for case in ["control","active","dynamic-soil"]}
  initial_inv={str(c):inventory(initial,c) for c in CELLS};active_inv={str(c):inventory(out/"active/restart-tr.nc",c) for c in CELLS};control_inv={str(c):inventory(out/"control/restart-tr.nc",c) for c in CELLS};dynamic_inv={str(c):inventory(out/"dynamic-soil/restart-tr.nc",c) for c in CELLS}
  physical=["TKversion","TKactive","TKstate","TKmatrix","TKporosity","TKexcess","DZsoil","TSsoil","LIQsoil","ICEsoil","FROZENsoil","FROZENFRACsoil","frontZ","frontFT","watertab"]
  bgc_restart=["vegc","vegC2N","deadc","deadn","rawc","soma","sompr","somcr","orgn","avln"]
  metrics={"forcing":{"monthly_tair_C":tair.tolist(),"monthly_precip_mm":precip.tolist(),"monthly_nirr":nirr.tolist(),"period_years":1},"community_types":CMTS,"drainage_class":0,"slope_degrees":30.,"run_years":a.years,"injected_excess_ice_kg_m2":added,"cells":{},"carbon_budget_residual_gC_m2":{},"restart_max_daily_difference":{},"restart_state_differences":{},"restart_inventory_relative_difference":{"C":0.,"N":0.},"dynamic_soil":{}}
  for n in TK:metrics["restart_max_daily_difference"][n]=maxdiff(daily[n],resumed[n])
  for i,c in enumerate(CELLS):
    key=str(c);gen=float(np.nansum(cell_series(daily["TKLIQGEN"],c)));runoff=float(np.nansum(cell_series(daily["TKLIQRUNOFF"],c)));drain=float(np.nansum(cell_series(daily["TKLIQDRAINAGE"],c)));other=float(np.nansum(cell_series(daily["TKLIQOTHER"],c)));storage=float(cell_series(daily["TKLIQSTORAGE"],c)[-1]);closure=storage+runoff+drain+other-gen
    metrics["cells"][key]={"cmt":CMTS[i],"generated_mm":gen,"drainage_mm":drain,"runoff_mm":runoff,"other_mm":other,"storage_mm":storage,"partition_residual_mm":closure,"subsidence_m":float(cell_series(daily["TKSUBSIDENCE"],c)[-1]),"initial_inventory":initial_inv[key],"control_inventory":control_inv[key],"active_inventory":active_inv[key]}
    cv=restart_values(out/"active/restart-tr.nc",c);rv=restart_values(out/"resumed/restart-tr.nc",c)
    for n in physical+bgc_restart:metrics["restart_state_differences"][n]=max(metrics["restart_state_differences"].get(n,0.),maxdiff(np.asarray(cv[n],float),np.asarray(rv[n],float)))
    resumed_inv=inventory(out/"resumed/restart-tr.nc",c)
    for n in ["C","N"]:metrics["restart_inventory_relative_difference"][n]=max(metrics["restart_inventory_relative_difference"][n],abs(active_inv[key][n]-resumed_inv[n])/max(abs(active_inv[key][n]),1.))
    metrics["dynamic_soil"][key]={"cmt":CMTS[i],"initial":initial_inv[key],"final":dynamic_inv[key]}
  # Instantaneous restart editing must preserve every C and N pool exactly.
  conserved_inventory=["C","N","SOC","VEGC","layers"]
  metrics["injection_inventory_exact"]=all(
    all(inventory(initial,c)[k]==inventory(injected,c)[k] for k in conserved_inventory)
    for c in CELLS)
  for case,finals in [("control",control_inv),("active",active_inv),("dynamic-soil",dynamic_inv)]:
    metrics["carbon_budget_residual_gC_m2"][case]={}
    for c in CELLS:
      key=str(c);flux=float(np.sum(cell_series(yearly[case]["NPP"]-yearly[case]["RHSOM"]-yearly[case]["RHDWD"],c)))
      metrics["carbon_budget_residual_gC_m2"][case][key]=(finals[key]["C"]-initial_inv[key]["C"])-flux
  checks=[]
  def gate(test,observed,criterion,ok):checks.append({"test":test,"observed":observed,"criterion":criterion,"status":"PASS" if ok else "FAIL"})
  gate("production completion",statuses,"all active cells status 100",all(v==[100,100] for v in statuses.values()))
  gate("multiple communities",CMTS,"CMT04 and CMT05",CMTS==[4,5])
  gate("rain-on-thaw forcing",precip[5:7].tolist(),"June and July >=200 mm",bool(np.all(precip[5:7]>=200)))
  gate("active excess-ice melt",min(x["generated_mm"] for x in metrics["cells"].values()),">0 mm in each CMT",all(x["generated_mm"]>0 for x in metrics["cells"].values()))
  gate("nonzero thermokarst drainage",min(x["drainage_mm"] for x in metrics["cells"].values()),">0 mm in each CMT",all(x["drainage_mm"]>0 for x in metrics["cells"].values()))
  gate("source-water closure",max(abs(x["partition_residual_mm"]) for x in metrics["cells"].values()),"<=1e-9 mm",all(abs(x["partition_residual_mm"])<=1e-9 for x in metrics["cells"].values()))
  exact_daily=max(metrics["restart_max_daily_difference"][n] for n in ["TKLIQGEN","TKLIQSTORAGE","TKLIQRUNOFF","TKLIQDRAINAGE","TKLIQOTHER","TKSUBSIDENCE","TKFRONTTYPE"])
  gate("restart source-water and subsidence diagnostics",exact_daily,"<=1e-12",exact_daily<=1e-12)
  gate("restart front trajectory",metrics["restart_max_daily_difference"]["TKFRONT"],"<=5e-4 m",metrics["restart_max_daily_difference"]["TKFRONT"]<=5e-4)
  geometry=max(metrics["restart_state_differences"][n] for n in ["TKmatrix","TKporosity","TKexcess","DZsoil"])
  gate("restart collapse geometry",geometry,"<=1e-12",geometry<=1e-12)
  invdiff=max(metrics["restart_inventory_relative_difference"].values())
  gate("restart ecosystem C/N inventory",invdiff,"<=5e-4 relative",invdiff<=5e-4)
  gate("excess injection preserves C/N",metrics["injection_inventory_exact"],"exact",metrics["injection_inventory_exact"])
  carbon_error=max(abs(v) for case in metrics["carbon_budget_residual_gC_m2"].values() for v in case.values())
  gate("ecosystem carbon budget",carbon_error,"<=0.01 g C m-2",carbon_error<=.01)
  bgc_finite=all(np.isfinite(cell_series(yearly[case][n],c)).all() for case in yearly for n in BGC for c in CELLS)
  gate("BGC output validity",bgc_finite,"all requested yearly values finite",bgc_finite)
  gate("dynamic-soil production run",[dynamic_inv[str(c)]["layers"] for c in CELLS],"finite C/N, >=1 layer",all(np.isfinite([dynamic_inv[str(c)]["C"],dynamic_inv[str(c)]["N"]]).all() and dynamic_inv[str(c)]["layers"]>=1 for c in CELLS))
  metrics["checks_passed"]=sum(x["status"]=="PASS" for x in checks);metrics["checks_total"]=len(checks)
  (out/"summary.json").write_text(json.dumps(metrics,indent=2)+"\n")
  with (out/"checks.csv").open("w",newline="") as f:w=csv.DictWriter(f,fieldnames=checks[0].keys(),lineterminator="\n");w.writeheader();w.writerows(checks)

  style();days=np.arange(1,daily[TK[0]].shape[0]+1);years=np.arange(1,a.years+1)
  fig,axes=plt.subplots(2,1,figsize=(7.2,5.2),sharex=True,layout="constrained")
  for i,c in enumerate(CELLS):
    axes[0].plot(days,np.cumsum(cell_series(daily["TKLIQGEN"],c)),color=[TEAL,BLUE][i],label=f"CMT{CMTS[i]:02d} generated")
    axes[0].plot(days,np.cumsum(cell_series(daily["TKLIQDRAINAGE"],c)),"--",color=[TEAL,BLUE][i],label=f"CMT{CMTS[i]:02d} drainage")
    axes[1].plot(days,cell_series(daily["TKLIQDRAINAGE"],c),color=[TEAL,BLUE][i],label=f"CMT{CMTS[i]:02d}")
  axes[0].set(ylabel="Cumulative source water (mm)",title="Well-drained slopes exercise thermokarst-source drainage");axes[1].set(xlabel="Simulation day",ylabel="Drainage (mm d⁻¹)");axes[0].legend(ncol=2);axes[1].legend();[x.grid(axis="y",color=GRID,lw=.6) for x in axes];save(fig,out,"bgc-validation-drainage")
  fig,axes=plt.subplots(2,2,figsize=(8.2,6),sharex=True,layout="constrained")
  for ax,n,title in zip(axes.flat,["GPP","RHSOM","SOC","VEGC"],["Gross primary production","Soil heterotrophic respiration","Soil organic carbon","Vegetation carbon"]):
    for i,c in enumerate(CELLS):
      ax.plot(years,cell_series(yearly["control"][n],c),"--",color=[TEAL,BLUE][i],alpha=.65)
      ax.plot(years,cell_series(yearly["active"][n],c),color=[TEAL,BLUE][i],label=f"CMT{CMTS[i]:02d}")
    ax.set_title(title);ax.set_ylabel("g C m⁻²"+(" yr⁻¹" if n in ["GPP","RHSOM"] else ""));ax.grid(axis="y",color=GRID,lw=.6)
  axes[1,0].set_xlabel("Transition year");axes[1,1].set_xlabel("Transition year");axes[0,0].legend(title="Solid: excess ice\nDashed: no excess ice");save(fig,out,"bgc-validation-carbon-response")
  fig,axes=plt.subplots(2,1,figsize=(7.2,5.1),sharex=True,layout="constrained")
  for i,c in enumerate(CELLS):
    axes[0].plot(days,cell_series(daily["TKSUBSIDENCE"],c)*1000,color=[TEAL,BLUE][i],label=f"CMT{CMTS[i]:02d} continuous")
    axes[0].plot(days,cell_series(resumed["TKSUBSIDENCE"],c)*1000,"--",color=MUTED,lw=.8)
    axes[1].plot(days,np.cumsum(cell_series(daily["TKLIQGEN"],c)),color=[TEAL,BLUE][i])
    axes[1].plot(days,np.cumsum(cell_series(resumed["TKLIQGEN"],c)),"--",color=MUTED,lw=.8)
  axes[0].axvline(half*365,color=GRID);axes[1].axvline(half*365,color=GRID);axes[0].set(ylabel="Subsidence (mm)",title="Continuous and midpoint-restarted trajectories");axes[1].set(xlabel="Simulation day",ylabel="Generated liquid (mm)");axes[0].legend();[x.grid(axis="y",color=GRID,lw=.6) for x in axes];save(fig,out,"bgc-validation-restart")
  fig,axes=plt.subplots(1,2,figsize=(7.2,3.5),layout="constrained")
  xpos=np.arange(2);width=.34
  axes[0].bar(xpos-width/2,[initial_inv[str(c)]["thickness"] for c in CELLS],width,color="#B9C1BE",label="Initial");axes[0].bar(xpos+width/2,[dynamic_inv[str(c)]["thickness"] for c in CELLS],width,color=TEAL,label="5-year DSL")
  axes[1].bar(xpos-width/2,[initial_inv[str(c)]["SOC"] for c in CELLS],width,color="#B9C1BE");axes[1].bar(xpos+width/2,[dynamic_inv[str(c)]["SOC"] for c in CELLS],width,color=TEAL)
  axes[0].set(ylabel="Soil-column thickness (m)",title="Dynamic soil geometry");axes[1].set(ylabel="Soil carbon inventory (g C m⁻²)",title="BGC pools remain finite");
  for ax in axes:ax.set_xticks(xpos,[f"CMT{x:02d}" for x in CMTS]);ax.grid(axis="y",color=GRID,lw=.6)
  axes[0].legend();save(fig,out,"bgc-validation-dynamic-soil")
  print(json.dumps(metrics,indent=2));failed=[x for x in checks if x["status"]=="FAIL"]
  if failed:raise RuntimeError(f"{len(failed)} validation gates failed: {[x['test'] for x in failed]}")
if __name__=="__main__":main()
