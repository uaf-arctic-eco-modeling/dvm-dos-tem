#!/usr/bin/env python3
"""Build, test, run deterministic experiments, validate results, and plot CSV evidence."""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, default=ROOT/'experiments/thermokarst/results')
a = p.parse_args()
OUT = a.output.resolve()
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(OUT/'.matplotlib'))
os.environ.setdefault('XDG_CACHE_HOME', str(OUT/'.cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np


def call(args):
    subprocess.run([str(x) for x in args], cwd=ROOT, check=True)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def data(name):
    return np.genfromtxt(OUT/f'{name}.csv', delimiter=',', names=True)


call(['make', 'thermokarst-test'])
build = ROOT/'build/thermokarst'
call([build/'thermokarst-benchmarks', OUT])


def run(name, *args):
    call([build/'thermokarst-column', '--output', OUT/f'{name}.csv', *args])


run('warm', '--profile', OUT/'warm_profile.csv', '--save', OUT/'continuous.restart')
run('no_excess', '--excess-depth', 0)
run('cold', '--top', -2)
run('first_half', '--days', 90, '--save', OUT/'midpoint.restart')
run('resumed', '--days', 90, '--restart', OUT/'midpoint.restart', '--save', OUT/'resumed.restart')
run('step60', '--days', 90, '--max-step', 60)
run('step30', '--days', 90, '--max-step', 30)

warm, cold, noice, pulse, stefan = [data(n) for n in ['warm', 'cold', 'no_excess', 'heat_pulse', 'stefan']]
checks = []

def gate(name, ok):
    require(ok, name)
    checks.append({'test': name, 'status': 'PASS'})


gate('zero-excess control has no settlement', np.all(noice['subsidence_m'] == 0))
gate('cold control has no settlement', np.all(cold['subsidence_m'] == 0))
gate('complete ice depletion gives 0.25 m settlement', abs(warm['subsidence_m'][-1]-.25)<1e-10)
gate('excess-ice loss equals subsidence', np.max(abs(warm['subsidence_m']-(warm['excess_kg_m2'][0]-warm['excess_kg_m2'])/917.))<1e-10)
gate('heat pulse agrees with analytical solution', np.max(abs(pulse['subsidence_m']-pulse['analytical_m']))<1e-10)
gate('restart continuation is bitwise identical', (OUT/'continuous.restart').read_bytes()==(OUT/'resumed.restart').read_bytes())
for name in ['warm','cold','no_excess','first_half','resumed','step60','step30']:
    d=data(name)
    gate(f'{name}: water residual below 1e-8 kg/m2', np.max(abs(d['water_residual_kg_m2']))<1e-8)
    gate(f'{name}: energy residual below 1e-3 J/m2', np.max(abs(d['energy_residual_J_m2']))<1e-3)
    gate(f'{name}: C/N conserved', max(np.max(abs(d['carbon_residual_g_m2'])),np.max(abs(d['nitrogen_residual_g_m2'])))<1e-8)
last=stefan[stefan['day']==15]
gate('Stefan spatial error decreases under refinement', np.all(np.diff(last['absolute_error_m'])<0))
gate('finest Stefan front within 5 mm', last['absolute_error_m'][-1]<.005)
step_diff=float(np.max(abs(data('step60')['subsidence_m']-data('step30')['subsidence_m'])))
gate('60 s vs 30 s settlement trajectories within 1 mm',step_diff<.001)
with (OUT/'integration_checks.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=['test','status']);w.writeheader();w.writerows(checks)
unit=list(csv.DictReader((build/'test_results.csv').open()))
require(all(r['status']=='PASS' for r in unit), 'unit tests not all passing')
(OUT/'test_results.csv').write_text((build/'test_results.csv').read_text())

# Evidence/specification is saved before visual authoring. All values below are
# deterministic C++ results; analytical lines are computed in benchmarks.cpp.
spec = {
 'source': 'CSV outputs of compiled C++ Thermokarst.cpp; no synthetic plotting data',
 'claim': 'Energy-limited excess-ice melt lowers the surface while conserving extensive state',
 'visual_form': 'ordered line plots, aligned panels, and layer-interface time series',
 'metric': ['subsidence','remaining excess ice','front position','conservation residual'],
 'unit': ['m','kg/m2','m','kg/m2 and J/m2'],
 'direction': 'positive subsidence downward; elevation positive upward',
 'focal_series': 'warm excess-ice column',
 'baselines': ['zero excess ice','cold column','analytical heat pulse','analytical Stefan'],
 'series_order': ['warm','zero excess','cold'],
 'target_width_mm':178,'target_height_mm':140,
 'uncertainty': 'deterministic numerical experiments; no statistical intervals',
 'annotation_plan': 'final collapse; analytical melt onset; absolute reference datum',
 'tick_policy': '3–6 major ticks; separate panels for different units; no dual axes',
 'formats':['png','svg'],
 'style_references': ['skill north-star figures 1/2/5','canonical ranks 2/3 for language',
                      'canonical ranks 7/11/12 for ordered curves']
}
(OUT/'visual_spec.json').write_text(json.dumps(spec,indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
 'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,
 'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,
 'axes.edgecolor':'#404040','text.color':'#111111','axes.labelcolor':'#111111',
 'xtick.color':'#404040','ytick.color':'#404040','savefig.facecolor':'white'})
TEAL='#1F6F5F';GRAY='#777777';INK='#111111'
qa=[]

def finish(fig,name):
    for ax in fig.axes:
        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.yaxis.set_major_locator(MaxNLocator(5))
        ax.tick_params(width=.7)
    fig.canvas.draw()
    # Bounding boxes of axes labels and titles must fit the physical canvas.
    bounds=fig.bbox
    for ax in fig.axes:
        xt=[t for t in ax.get_xticklabels() if min(ax.get_xlim())<=t.get_position()[0]<=max(ax.get_xlim())]
        yt=[t for t in ax.get_yticklabels() if min(ax.get_ylim())<=t.get_position()[1]<=max(ax.get_ylim())]
        for txt in [ax.title,ax.xaxis.label,ax.yaxis.label,*xt,*yt]:
            if not txt.get_visible() or not txt.get_text():continue
            box=txt.get_window_extent(fig.canvas.get_renderer())
            require(box.x0>=-1 and box.y0>=-1 and box.x1<=bounds.x1+1 and box.y1<=bounds.y1+1,
                    f'clipped text in {name}: {txt.get_text()}')
    fig.savefig(OUT/f'{name}.png',dpi=220)
    fig.savefig(OUT/f'{name}.svg')
    from matplotlib.colors import to_rgba
    def gray(c):
        r,g,b,alpha=to_rgba(c); v=.2126*r+.7152*g+.0722*b; return (v,v,v,alpha)
    for axis in fig.axes:
        for line in axis.lines:
            line.set_color(gray(line.get_color()))
            line.set_markeredgecolor(gray(line.get_markeredgecolor()))
            line.set_markerfacecolor(gray(line.get_markerfacecolor()))
    qa_dir=OUT/'.qa';qa_dir.mkdir(exist_ok=True)
    fig.savefig(qa_dir/f'{name}_gray.png',dpi=120)
    qa.append({'figure':name,'size_inches':list(fig.get_size_inches()),'text_bounds':'pass'})
    plt.close(fig)

fig,ax=plt.subplots(2,2,figsize=(7.01,5.55),layout='constrained')
fig.suptitle('Excess-ice melt produces irreversible surface lowering',fontsize=12)
ax[0,0].plot(pulse['heat_MJ_m2'],pulse['analytical_m'],color=GRAY,lw=1.2,label='Analytical')
ax[0,0].plot(pulse['heat_MJ_m2'][::6],pulse['subsidence_m'][::6],ls='none',marker='o',ms=3.2,mfc='none',mec=TEAL,label='C++ prototype')
ax[0,0].set(xlabel='Added heat (MJ m⁻²)',ylabel='Subsidence (m)',title='(a) Known heat pulse')
ax[0,0].legend(frameon=False,fontsize=8,loc='upper left')
for d,label,col,style in [(warm,'Warm, excess ice',TEAL,'-'),(noice,'Warm, no excess ice',INK,'--'),(cold,'Cold, excess ice',GRAY,':')]:
    ax[0,1].plot(d['day'],d['subsidence_m'],color=col,ls=style,lw=1.6,label=label)
ax[0,1].set(xlabel='Time (days)',ylabel='Subsidence (m)',title='(b) Conductive warming')
ax[0,1].legend(frameon=False,fontsize=8,loc='upper left')
ax[1,0].plot(warm['day'],warm['excess_kg_m2'],color=TEAL,lw=1.6)
ax[1,0].set(xlabel='Time (days)',ylabel='Excess ice (kg m⁻²)',title='(c) Finite ice inventory')
ax[1,1].plot(warm['day'],warm['pond_kg_m2'],color=GRAY,ls='--',label='Surface storage')
ax[1,1].plot(warm['day'],warm['runoff_kg_m2'],color=TEAL,label='Cumulative runoff')
ax[1,1].set(xlabel='Time (days)',ylabel='Water equivalent (kg m⁻²)',title='(d) Meltwater accounting')
ax[1,1].legend(frameon=False,fontsize=8)
finish(fig,'thermokarst_process')

fig,ax=plt.subplots(2,2,figsize=(7.01,5.55),layout='constrained')
fig.suptitle('Analytical benchmarks and conservation checks',fontsize=12)
for dz,col,style in [(.1,GRAY,':'),(.05,INK,'--'),(.025,TEAL,'-')]:
    d=stefan[stefan['spacing_m']==dz]
    ax[0,0].plot(d['day'],d['front_m'],color=col,ls=style,label=f'{dz*100:g} cm cells')
d=stefan[stefan['spacing_m']==.025]
ax[0,0].plot(d['day'][::2],d['analytical_m'][::2],ls='none',marker='o',ms=3,mfc='white',mec=INK,label='Analytical')
ax[0,0].set(xlabel='Time (days)',ylabel='Thaw depth (m)',title='(a) One-phase Stefan problem')
ax[0,0].legend(frameon=False,fontsize=8)
ax[0,1].plot(last['spacing_m']*100,last['absolute_error_m']*1000,'o-',color=TEAL)
ax[0,1].set(xlabel='Cell thickness (cm)',ylabel='Absolute error (mm)',title='(b) Front error on day 15',ylim=(0,None))
ax[1,0].plot(warm['day'],warm['water_residual_kg_m2']/1e-12,color=TEAL)
ax[1,0].set(xlabel='Time (days)',ylabel='Water residual (10⁻¹² kg m⁻²)',title='(c) Water balance')
ax[1,1].plot(warm['day'],warm['energy_residual_J_m2']/1e-6,color=TEAL)
ax[1,1].set(xlabel='Time (days)',ylabel='Energy residual (10⁻⁶ J m⁻²)',title='(d) Energy balance')
finish(fig,'thermokarst_verification')

prof=data('warm_profile')
fig,ax=plt.subplots(figsize=(7.01,3.7),layout='constrained')
for i in np.unique(prof['layer']):
    d=prof[prof['layer']==i]
    ax.plot(d['day'],d['bottom_elevation_m'],lw=.75,color='#888888')
ax.plot(warm['day'],warm['surface_m'],color=TEAL,lw=2,label='Ground surface')
ax.axhline(0,color=INK,ls=':',lw=.9,label='Initial surface datum')
ax.set(xlabel='Time (days)',ylabel='Elevation relative to initial surface (m)',
       title='Layer interfaces move while the column base remains fixed')
fig.legend(*ax.get_legend_handles_labels(),frameon=False,loc='outside lower center',ncol=2,fontsize=8)
finish(fig,'thermokarst_geometry')

summary={
 'unit_tests_passed':len(unit),'integration_checks_passed':len(checks),
 'warm_final_subsidence_m':float(warm['subsidence_m'][-1]),
 'max_water_residual_kg_m2':float(np.max(abs(warm['water_residual_kg_m2']))),
 'max_energy_residual_J_m2':float(np.max(abs(warm['energy_residual_J_m2']))),
 'max_CN_residual_g_m2':float(max(np.max(abs(warm['carbon_residual_g_m2'])),np.max(abs(warm['nitrogen_residual_g_m2'])))),
 'heat_pulse_error_m':float(np.max(abs(pulse['subsidence_m']-pulse['analytical_m']))),
 'finest_stefan_error_m':float(last['absolute_error_m'][-1]),
 'max_60s_vs_30s_subsidence_difference_m':step_diff,
 'restart_bitwise_equal':True,
 'scope':'Reference C++ column plus opt-in production Cohort/enthalpy/NetCDF integration',
 'compiler':subprocess.check_output(['c++','--version'],text=True).splitlines()[0],
 'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 'numpy':np.__version__,'matplotlib':matplotlib.__version__,
}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(OUT/'visual_qa.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps(summary,indent=2))
