#!/usr/bin/env python3
"""Validate fire-driven thermokarst topology, budgets, and restart continuation."""
import argparse,csv,json,os,shutil,subprocess,sys
from pathlib import Path
import numpy as np
from netCDF4 import Dataset
ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/"build/matplotlib-cache"))
saved=os.environ.get("PATH","")
if sys.platform=="darwin":os.environ["PATH"]=os.pathsep.join(x for x in saved.split(os.pathsep) if x not in ("/usr/sbin","/sbin"))
import matplotlib;matplotlib.use("Agg")
import matplotlib.pyplot as plt
os.environ["PATH"]=saved
import production_validation as production
import bgc_coupling_validation as bgc
CELLS=bgc.CELLS;CMTS=bgc.CMTS
INK="#171717";TEAL="#1F6F5F";BLUE="#4C78A8";MUTED="#777772";GRID="#E4E7E5"
FIRE_RELEASED_WATER=15;FIRE_EXPORTED_ENERGY=16;FIRE_MATRIX_LOSS=17;FIRE_ROUTED_LIQUID=18

def compile_probe(out):
  exe=out/"fire-topology-probe"
  subprocess.run(["c++","-std=c++11","-O2","-I",str(ROOT/"include"),str(ROOT/"experiments/thermokarst/fire_topology_probe.cpp"),str(ROOT/"src/Thermokarst.cpp"),"-o",str(exe)],check=True)
  path=out/"fire-topology-probe.csv";subprocess.run([str(exe),str(path)],check=True)
  with path.open() as f:return {r["metric"]:float(r["value"]) for r in csv.DictReader(f)}

def make_fire(source,dest,event_year=None):
  shutil.copy2(source,dest)
  with Dataset(dest,"r+") as d:
    for n in ["exp_burn_mask","exp_jday_of_burn","exp_fire_severity","exp_area_of_burn"]:d[n][:]=0
    if event_year is not None:
      for y,x in CELLS:
        d["exp_burn_mask"][event_year,y,x]=1;d["exp_jday_of_burn"][event_year,y,x]=273
        d["exp_fire_severity"][event_year,y,x]=4;d["exp_area_of_burn"][event_year,y,x]=1000000

def make_spec(source,dest):
  rows=list(csv.DictReader(source.open()))
  for r in rows:
    r["Yearly"]=r["Monthly"]=r["Daily"]=""
    if r["Name"] in bgc.TK:r["Daily"]="d"
    if r["Name"] in bgc.BGC:r["Yearly"]="y"
    if r["Name"] in ["BURNTHICK","BURNSOIL2AIRC","BURNSOIL2AIRN"]:r["Monthly"]="m"
  with dest.open("w",newline="") as f:w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator="\n");w.writeheader();w.writerows(rows)

def config(base,directory,restart,fire_file,output=True,tr_start=0):
  c=bgc.config(base,directory,restart,dsl=False,output=output,tr_start=tr_start)
  c["IO"]["hist_exp_fire_file"]=str(fire_file)
  for stage in ["tr","sc"]:c["stage_settings"][stage]["dsb"]=True
  return c

def monthly(directory,name):
  with Dataset(directory/f"{name}_monthly_tr.nc") as d:return np.asarray(np.ma.asarray(d[name][:]).filled(0.),float)
def restart(path,name,cell):
  with Dataset(path) as d:
    y,x=cell;return np.asarray(np.ma.asarray(d[name][y,x]).filled(0.),float)
def save(fig,out,name):
  fig.savefig(out/f"{name}.png",dpi=240,bbox_inches="tight");fig.savefig(out/f"{name}.svg",bbox_inches="tight");plt.close(fig)

def main():
  ap=argparse.ArgumentParser();ap.add_argument("--binary",type=Path,default=ROOT/"dvmdostem");ap.add_argument("--output",type=Path,default=ROOT/"experiments/thermokarst/fire_topology_validation_results");a=ap.parse_args();out=a.output.resolve()
  if out.exists():shutil.rmtree(out)
  out.mkdir(parents=True);probe=compile_probe(out)
  base=production.parse_json_with_comments(ROOT/"config/config.js");bgc.absolute_io(base);bgc.copy_spatial(base,out)
  bgc.make_climate(Path(base["IO"]["hist_climate_file"]),out/"periodic-fire-climate.nc");base["IO"]["hist_climate_file"]=str(out/"periodic-fire-climate.nc")
  spec=out/"fire-output-spec.csv";make_spec(ROOT/"config/output_spec.csv",spec);base["IO"]["output_spec_file"]=str(spec)
  source=Path(base["IO"]["hist_exp_fire_file"]);fire_continuous=out/"fire-year-one.nc";fire_resumed=out/"fire-year-zero.nc";nofire=out/"no-fire.nc";make_fire(source,fire_continuous,1);make_fire(source,fire_resumed,0);make_fire(source,nofire)
  init_cfg=bgc.config(base,out/"initialization",output=False)
  statuses={"initialization":bgc.run(a.binary.resolve(),out,"initialization",init_cfg,["--pr-yrs","1","--eq-yrs","5"])}
  initial=out/"initialization/restart-eq.nc";injected=out/"restart-with-excess.nc";added=bgc.inject_excess(initial,injected,fraction=.2,top=0.,bottom=.8)
  statuses["continuous"]=bgc.run(a.binary.resolve(),out,"continuous",config(base,out/"continuous",injected,fire_continuous),["--tr-yrs","2"])
  statuses["split-first"]=bgc.run(a.binary.resolve(),out,"split-first",config(base,out/"split-first",injected,nofire),["--tr-yrs","1"])
  statuses["resumed"]=bgc.run(a.binary.resolve(),out,"resumed",config(base,out/"resumed",out/"split-first/restart-tr.nc",fire_continuous,tr_start=1),["--tr-yrs","1"])
  burn=monthly(out/"continuous","BURNTHICK");soilc=monthly(out/"continuous","BURNSOIL2AIRC")
  final_c=out/"continuous/restart-tr.nc";final_r=out/"resumed/restart-tr.nc"
  physical=["TKstate","TKmatrix","TKporosity","TKexcess","DZsoil","TSsoil","LIQsoil","ICEsoil","FROZENsoil","FROZENFRACsoil","frontZ","frontFT"]
  pools=["rawc","soma","sompr","somcr","orgn","avln"]
  diffs={n:max(bgc.maxdiff(restart(final_c,n,c),restart(final_r,n,c)) for c in CELLS) for n in physical+pools}
  cells=[]
  for c,cmt in zip(CELLS,CMTS):
    state=restart(final_c,"TKstate",c);before=bgc.inventory(injected,c);after=bgc.inventory(final_c,c)
    y,x=c;cells.append({"cmt":cmt,"burn_depth_m":float(np.sum(burn[:,y,x])),"burned_soil_c_g_m2":float(np.sum(soilc[:,y,x])),"released_water_kg_m2":float(state[FIRE_RELEASED_WATER]),"routed_liquid_kg_m2":float(state[FIRE_ROUTED_LIQUID]),"exported_solid_energy_J_m2":float(state[FIRE_EXPORTED_ENERGY]),"burned_matrix_m":float(state[FIRE_MATRIX_LOSS]),"initial_layers":before["layers"],"final_layers":after["layers"],"initial_SOC_g_m2":before["SOC"],"final_SOC_g_m2":after["SOC"],"initial_excess_kg_m2":added[str(c)],"final_excess_kg_m2":float(np.sum(restart(final_c,"TKexcess",c)))})
  fire_diag_relative=max(abs(restart(final_c,"TKstate",c)[i]-restart(final_r,"TKstate",c)[i])/max(abs(restart(final_c,"TKstate",c)[i]),1.) for c in CELLS for i in [FIRE_RELEASED_WATER,FIRE_EXPORTED_ENERGY,FIRE_MATRIX_LOSS,FIRE_ROUTED_LIQUID])
  inventory_relative=0.
  for c in CELLS:
    ia=bgc.inventory(final_c,c);ib=bgc.inventory(final_r,c)
    for n in ["C","N"]:inventory_relative=max(inventory_relative,abs(ia[n]-ib[n])/max(abs(ia[n]),1.))
  checks=[]
  def gate(test,observed,criterion,ok):checks.append({"test":test,"observed":observed,"criterion":criterion,"status":"PASS" if ok else "FAIL"})
  gate("synthetic fire water closure",abs(probe["water_residual_kg_m2"]),"<=1e-12 kg m-2",abs(probe["water_residual_kg_m2"])<=1e-12)
  gate("synthetic fire energy closure",abs(probe["energy_residual_J_m2"]),"<=1e-6 J m-2",abs(probe["energy_residual_J_m2"])<=1e-6)
  gate("production completion",statuses,"all cells status 100",all(v==[100,100] for v in statuses.values()))
  gate("nonzero explicit fire",[x["burn_depth_m"] for x in cells],">0 m in each CMT",all(x["burn_depth_m"]>0 for x in cells))
  gate("soil combustion branch",[x["burned_soil_c_g_m2"] for x in cells],">0 g C m-2",all(x["burned_soil_c_g_m2"]>0 for x in cells))
  gate("fire phase-water release",[x["released_water_kg_m2"] for x in cells],">0 kg m-2",all(x["released_water_kg_m2"]>0 for x in cells))
  gate("fire liquid routed to hydrology",[x["routed_liquid_kg_m2"] for x in cells],"nonzero in >=1 CMT and <= released phase water",any(x["routed_liquid_kg_m2"]>0 for x in cells) and all(0<=x["routed_liquid_kg_m2"]<=x["released_water_kg_m2"]+1e-9 for x in cells))
  gate("fire matrix loss",[x["burned_matrix_m"] for x in cells],">0 m",all(x["burned_matrix_m"]>0 for x in cells))
  gate("fire energy export finite",[x["exported_solid_energy_J_m2"] for x in cells],"finite",all(np.isfinite(x["exported_solid_energy_J_m2"]) for x in cells))
  gate("restart geometry",max(diffs[n] for n in ["TKmatrix","TKporosity","TKexcess","DZsoil"]),"<=1e-6 m",max(diffs[n] for n in ["TKmatrix","TKporosity","TKexcess","DZsoil"])<=1e-6)
  gate("restart phase and fronts",max(diffs[n] for n in ["TSsoil","LIQsoil","ICEsoil","FROZENsoil","FROZENFRACsoil","frontZ","frontFT"]),"<=1e-3",max(diffs[n] for n in ["TSsoil","LIQsoil","ICEsoil","FROZENsoil","FROZENFRACsoil","frontZ","frontFT"])<=1e-3)
  gate("restart fire diagnostics",fire_diag_relative,"<=2e-4 scaled difference",fire_diag_relative<=2e-4)
  gate("restart ecosystem C/N inventory",inventory_relative,"<=5e-4 relative",inventory_relative<=5e-4)
  summary={"probe":probe,"statuses":statuses,"cells":cells,"restart_max_difference":diffs,"restart_fire_diagnostic_relative_difference":fire_diag_relative,"restart_inventory_relative_difference":inventory_relative,"checks_passed":sum(x["status"]=="PASS" for x in checks),"checks_total":len(checks)}
  (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
  with (out/"checks.csv").open("w",newline="") as f:w=csv.DictWriter(f,fieldnames=checks[0].keys(),lineterminator="\n");w.writeheader();w.writerows(checks)
  plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8.5,"axes.titlesize":10,"axes.labelsize":9,"axes.spines.top":False,"axes.spines.right":False,"legend.frameon":False,"svg.fonttype":"none"})
  x=np.arange(len(cells));labels=[f'CMT{v["cmt"]:02d}' for v in cells]
  fig,axes=plt.subplots(1,4,figsize=(8.6,3.3),layout="constrained")
  for ax,key,label,title in zip(axes,["burn_depth_m","burned_matrix_m","released_water_kg_m2","routed_liquid_kg_m2"],["Depth (m)","Matrix loss (m)","Water (kg m⁻²)","Liquid (kg m⁻²)"],["Organic layer burned","Matrix consumed","Phase water released","Routed to TEM hydrology"]):
    ax.bar(x,[v[key] for v in cells],color=[TEAL,BLUE]);ax.set_xticks(x,labels);ax.set_ylabel(label);ax.set_title(title);ax.grid(axis="y",color=GRID,lw=.6)
  save(fig,out,"fire-topology-partition")
  fig,axes=plt.subplots(1,2,figsize=(7.2,3.3),layout="constrained")
  axes[0].bar(x,[v["initial_excess_kg_m2"] for v in cells],color=MUTED,label="Initial");axes[0].bar(x,[v["final_excess_kg_m2"] for v in cells],color=[TEAL,BLUE],label="Final");axes[0].set(ylabel="Excess ice (kg m⁻²)",title="Thaw before fire removes excess ice")
  axes[1].bar(x,[v["initial_SOC_g_m2"] for v in cells],color=MUTED,label="Before fire");axes[1].bar(x,[v["final_SOC_g_m2"] for v in cells],color=TEAL,label="After fire");axes[1].set(ylabel="Soil C (g m⁻²)",title="Combustion removes soil carbon")
  for ax in axes:ax.set_xticks(x,labels);ax.grid(axis="y",color=GRID,lw=.6);ax.legend()
  save(fig,out,"fire-topology-state-change")
  fig,axes=plt.subplots(1,2,figsize=(7.2,4.1),sharey=True,layout="constrained")
  for ax,c,cmt,color in zip(axes,CELLS,CMTS,[TEAL,BLUE]):
    profiles=[]
    for path,label,line_color,style in [(injected,"Initial",MUTED,"--"),(final_c,"Final post-fire",color,"-")]:
      matrix=restart(path,"TKmatrix",c);matrix=matrix[matrix>0.]
      mid=np.cumsum(matrix)-matrix/2.;profiles.append((matrix,mid))
      ax.plot(matrix,mid,style,color=line_color,marker="o",ms=2.8,lw=1.2,label=label)
    ax.set(xlabel="Matrix layer thickness (m)",title=f"CMT{cmt:02d}: {len(profiles[0][0])} → {len(profiles[1][0])} layers")
    ax.grid(color=GRID,lw=.6);ax.legend()
  axes[0].set_ylabel("Cumulative matrix depth (m)");axes[0].invert_yaxis()
  save(fig,out,"fire-topology-layer-geometry")
  fig,ax=plt.subplots(figsize=(7.2,3.5),layout="constrained");names=["Geometry (m)","Phase/fronts (native units)","C/N layer pools (g m⁻²)","Fire diagnostics (relative)"];values=[max(diffs[n] for n in ["TKmatrix","TKporosity","TKexcess","DZsoil"]),max(diffs[n] for n in ["TSsoil","LIQsoil","ICEsoil","frontZ","frontFT"]),max(diffs[n] for n in pools),fire_diag_relative];ax.barh(names,values,color=TEAL);ax.set_xscale("symlog",linthresh=1e-12);ax.set(xlabel="Maximum difference",title="Continuous and resumed fire runs agree after restart");ax.grid(axis="x",color=GRID,lw=.6);save(fig,out,"fire-topology-restart")
  print(json.dumps(summary,indent=2));failed=[x for x in checks if x["status"]=="FAIL"]
  if failed:raise RuntimeError(f"{len(failed)} gates failed: {[x['test'] for x in failed]}")
if __name__=="__main__":main()
