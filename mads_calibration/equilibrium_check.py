# Equilibrium check adapted  from Helene's code for yaml SA/calib set up
# Must manually adjust:
# 	line 28: config_file_name
#	lines 33-42: choose appropraite paths, file names and variables
#		NOTE:this code only works for ONE target at a time
#			 SPECIFY index of target you're interested with the variable j
#			 (indices match the order of targets as loaded from yaml file)
# Example: python3 equilibrium_check.py
# Aiza
# 04/17/2023

import xarray as xr
import glob
from scipy import stats
import pandas as pd
import os,sys
sys.path.append(os.path.join('/work','calibration'))
import calibration_targets
import yaml
sys.path.append(os.path.join('/work','mads_calibration'))
import TEM

def get_cofig_file(config_file_name):
    dvmdostem=TEM.TEM_model(config_file_name)
    dvmdostem.set_params(dvmdostem.cmtnum, dvmdostem.paramnames, dvmdostem.pftnums)
    return dvmdostem

tem = get_cofig_file('config-step2-md3_noprior.yaml')
CMTNUM = tem.cmtnum
var_tar_all=tem.target_names #this loads specified targets from config file
var_pairs=tem.caltarget_to_ncname_map # this loads all target output pairs

POD='/data/workflows/STEP2-MD3-CR_6' # path to SA sample folders
PD='/data/workflows'
path_SA='SA/'
params='sample_matrix_STEP2-MD3-CR-noprior.csv'
model='results_STEP2-MD3-CR-noprior.txt'
N = 1000 #sample size
j = 0 #index of the relevant target (in var_tar_all)
neqy = 30 #num years to test equilibrium
ncaly = 10 #num years to test calibration
eco_file = '/nmax_eq_results.csv' #name of csv with calculated slope, cv and p value

### Load VARtar and matching VARout
out_matches = [match for match in var_pairs if var_tar_all[j] in match]
VARtar = var_tar_all[j]
VARout = out_matches[0][1]

### Read parameter values
sm = pd.read_csv(os.path.join(POD,'sample_matrix.csv'))
list(sm.columns)
sm.reset_index(inplace=True)
sm = sm.rename(columns={"index": "sample"})
sm.describe()

### Read the target 
# targets=tem.get_targets(1) #doesn't work with yaml config? 
for cmtname, data in calibration_targets.calibration_targets.items():
	if str(CMTNUM) == str(data.get("cmtnumber")):
		caltargets = data

targ = caltargets[VARtar]
targets = pd.DataFrame(caltargets[VARtar])
targets.reset_index(inplace=True)
targets = targets.rename(columns={"index": "pft"})
targets = targets.rename(columns={0: VARtar})

### Read out the outputs and test for equilibrium and stabililty and compute RMSE
print('Calculating cv, p, slope and rmse to check eq for target '+VARtar+ ' and output '+VARout+'\n')
results_eco = pd.DataFrame() 
results_pft = pd.DataFrame()
failed_run = []
for i in range(int(N)):
	print(i)
	## Read the outputs
	PWD = os.path.join(POD + '/sample_'+ "{:09d}".format(i) + '/output')
	ds = xr.open_dataset(glob.glob(PWD + '/' + VARout + "_*_eq.nc")[0])
	data = ds.to_dataframe()
	data.reset_index(inplace=True)
	data = data[(data['x'] == 0)]
	data = data[(data['y'] == 0)]
	data = data.rename(columns={"time": "year"})
	data = data[['year', 'pft', VARout]]
	data = data[(data['year'] > (data['year'].max() - neqy))]
	data['sample'] = int(i)
	## Test equilibrium and stability
	# Sum fluxes by ecosys
	ts = data.groupby(['year'])[VARout].sum().to_frame()
	ts.reset_index(inplace=True)
	cv = 100 * ts[VARout].std() / ts[VARout].mean()
	reg = ts.to_numpy()
	slope, intercept, r, p, std_err = stats.linregress(reg[:,0], reg[:,1])
	if abs(cv) > 15 :
		failed_run.append(i)
		print('Index '+str(i)+' failed equilibrium check')
	if p < 0.1:
		total_sum = 0
		if type(targ)==list:
			if abs(slope) > 0.001*(sum(targ)):
				failed_run.append(i)
				print("Index "+str(i)+" failed stability check")
		else:
			for key, value in targ.items():
				for val in value:
					total_sum += val
			if abs(slope) > 0.001*(total_sum):
				failed_run.append(i)
				print("Index "+str(i)+" failed stability check")
	## Compute distance to target
	# compute last decade average by PFT
	out = data[(data['year'] > (data['year'].max() -  ncaly))].groupby(['pft'])[VARout].mean().to_frame()
	out.reset_index(inplace=True)
	out = pd.merge(out, targets, on='pft', how='outer')
	out['weight'] = out[VARtar] / out[VARtar].sum()
	rmse = ((out[VARtar] - out[VARout]) ** 2).mean() ** .5
	rmsew = (out['weight'] * (out[VARtar] - out[VARout]) ** 2).mean() ** .5
	df = {'sample': [i], 'eq_pvalue': [p], 'eq_slope': [slope], 'eq_cv': [cv], 'rmse': [rmse], 'rmsew':[rmsew]}
	df = pd.DataFrame.from_dict(df)
	out['sample'] = int(i)
	results_eco = pd.concat([results_eco,df],ignore_index=True)
	results_pft = pd.concat([results_pft,out],ignore_index=True)

results_eco.to_csv(os.path.join(POD + eco_file), sep=',',index=False)

### To remove results that didn't meet eq check
df_param = pd.read_csv(path_SA+params)
df_model = pd.read_csv(path_SA+model,header=None)
good_df_param = df_param.drop(failed_run)
good_df_model = df_model.drop(failed_run)
good_df_param.to_csv(os.path.join(path_SA + 'good_df_param.csv'), sep=',',index=False)
good_df_model.to_csv(os.path.join(path_SA + 'good_df_model.csv'), sep=',',index=False)


# select the 5 best performing samples
# best_sample = results_eco.sort_values(by=['rmse']).iloc[0]
# results_eco=results_eco.sort_values(by=['rmse']).iloc[0:5]
# results_eco.to_csv(os.path.join(PD + '/cmax_results1.csv'), sep=',',index=False)
