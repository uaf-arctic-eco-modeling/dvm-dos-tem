#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import seaborn as sns
import numpy as np
import scipy
from matplotlib import pyplot as plt
from matplotlib import cm
import os
from sklearn.metrics import r2_score,mean_squared_error,mean_absolute_error


#Set step, paths, pfts and run all
#STEP = 1
#STEP = 'NPP_VegC_VegN_PFT'
CMT='black-spruce'
STEP = 4

#STEP1_results = '/data/workflows/BONA-Birch-STEP1-SA/results.csv'
#STEP1_sample_matrix = '/data/workflows/BONA-Birch-STEP1-SA/sample_matrix.csv'

STEP1_results = '/data/workflows/BONA-BS-STEP1-SA/results.csv'
STEP1_sample_matrix = '/data/workflows/BONA-BS-STEP1-SA/sample_matrix.csv'

NPP_VegC_PFT_results = '/data/workflows/BONA-Birch-NPP-VegC-PFT-SA/results.csv'
NPP_VegC_PFT_sample_matrix = '/data/workflows/BONA-Birch-NPP-VegC-PFT-SA/sample_matrix.csv'

NPP_VegC_PFT_results = '/data/workflows/BONA-BS-NPP-VegC-PFT-SA/results.csv'
NPP_VegC_PFT_sample_matrix = '/data/workflows/BONA-BS-NPP-VegC-PFT-SA/sample_matrix.csv'


#STEP4_results = '/data/workflows/BONA-Birch-STEP4-SA/results.csv'
#STEP4_sample_matrix = '/data/workflows/BONA-Birch-STEP4-SA/sample_matrix.csv'

STEP4_results = '/data/workflows/BONA-BS-STEP4-SA/results.csv'
STEP4_sample_matrix = '/data/workflows/BONA-BS-STEP4-SA/sample_matrix.csv'

pfts=['White Spruce', 'Deciduous Shrub', 'Evergreen Shrub', 'Moss', 'Lichen']





#if number of pfts != 5 you will have to adjust these values

if STEP == 1:
    target_vars = ['GPP1', 'GPP2', 'GPP3', 'GPP4', 'GPP5']
    
    calib_params = [['cmax', 'cmax.1', 'cmax.2', 'cmax.3', 'cmax.4']] # here for reference
    
    vars_nopft= ['GPP']
    
if STEP == 'NPP_VegC_PFT' and CMT=='birch':
    target_vars = ['NPPAll1', 'NPPAll2', 'NPPAll3', 'NPPAll4', 'NPPAll5',
                   'VegCarbonLeaf1', 'VegCarbonStem1', 'VegCarbonRoot1', 
                   'VegCarbonLeaf2', 'VegCarbonStem2', 'VegCarbonRoot2',
                   'VegCarbonLeaf3', 'VegCarbonStem3', 'VegCarbonRoot3',
                   'VegCarbonLeaf4', 
                   'VegCarbonLeaf5', 'VegCarbonStem5', 'VegCarbonRoot5']
    
    calib_params = [['nmax'], ['krb(0)'], ['krb(1)'], ['krb(2)'],
                   ['cfall(0)'], ['cfall(1)'], ['cfall(2)'],
                   ['nfall(0)'], ['nfall(1)'], ['nfall(2)']] # here for reference
    calib_params_flat = ['nmax', 'krb(0)', 'krb(1)', 'krb(2)',
                   'cfall(0)', 'cfall(1)', 'cfall(2)',
                    'nfall(0)', 'nfall(1)', 'nfall(2)']
    vars_nopft= ['NPPAll', 'VegCarbonLeaf', 'VegCarbonStem', 'VegCarbonRoot']
    
if STEP == 'NPP_VegC_VegN_PFT' and CMT=='birch':
    target_vars = ['NPPAll1', 'NPPAll2', 'NPPAll3', 'NPPAll4', 'NPPAll5',
                   'VegCarbonLeaf1', 'VegCarbonStem1', 'VegCarbonRoot1', 
                   'VegCarbonLeaf2', 'VegCarbonStem2', 'VegCarbonRoot2',
                   'VegCarbonLeaf3', 'VegCarbonStem3', 'VegCarbonRoot3',
                   'VegCarbonLeaf4', 
                   'VegCarbonLeaf5', 'VegCarbonStem5', 'VegCarbonRoot5',
                   'VegNitrogenLeaf1', 'VegNitrogenStem1', 'VegNitrogenRoot1', 
                   'VegNitrogenLeaf2', 'VegNitrogenStem2', 'VegNitrogenRoot2',
                   'VegNitrogenLeaf3', 'VegNitrogenStem3', 'VegNitrogenRoot3',
                   'VegNitrogenLeaf4', 
                   'VegNitrogenLeaf5', 'VegNitrogenStem5', 'VegNitrogenRoot5']
    
    calib_params = [['nmax'], ['krb(0)'], ['krb(1)'], ['krb(2)'],
                   ['cfall(0)'], ['cfall(1)'], ['cfall(2)'],
                   ['nfall(0)'], ['nfall(1)'], ['nfall(2)']] # here for reference
    calib_params_flat = ['nmax', 'krb(0)', 'krb(1)', 'krb(2)',
                   'cfall(0)', 'cfall(1)', 'cfall(2)',
                    'nfall(0)', 'nfall(1)', 'nfall(2)']
    vars_nopft= ['NPPAll', 'VegCarbonLeaf', 'VegCarbonStem', 'VegCarbonRoot', 
                 'VegNitrogenLeaf', 'VegNitrogenStem', 'VegNitrogenRoot']
    
if STEP == 'NPP_VegC_VegN_PFT' and CMT=='black-spruce':
    target_vars = ['NPPAll1', 'NPPAll2', 'NPPAll3', 'NPPAll4', 'NPPAll5',
                   'VegCarbonLeaf1', 'VegCarbonStem1', 'VegCarbonRoot1', 
                   'VegCarbonLeaf2', 'VegCarbonStem2', 'VegCarbonRoot2',
                   'VegCarbonLeaf3', 'VegCarbonStem3', 'VegCarbonRoot3',
                   'VegCarbonLeaf4', 
                   'VegCarbonLeaf5',
                   'VegNitrogenLeaf1', 'VegNitrogenStem1', 'VegNitrogenRoot1', 
                   'VegNitrogenLeaf2', 'VegNitrogenStem2', 'VegNitrogenRoot2',
                   'VegNitrogenLeaf3', 'VegNitrogenStem3', 'VegNitrogenRoot3',
                   'VegNitrogenLeaf4', 
                   'VegNitrogenLeaf5']
    
    calib_params = [['nmax'], ['krb(0)'], ['krb(1)'], ['krb(2)'],
                   ['cfall(0)'], ['cfall(1)'], ['cfall(2)'],
                   ['nfall(0)'], ['nfall(1)'], ['nfall(2)']] # here for reference
    calib_params_flat = ['nmax', 'krb(0)', 'krb(1)', 'krb(2)',
                   'cfall(0)', 'cfall(1)', 'cfall(2)',
                    'nfall(0)', 'nfall(1)', 'nfall(2)']
    vars_nopft= ['NPPAll', 'VegCarbonLeaf', 'VegCarbonStem', 'VegCarbonRoot', 
                 'VegNitrogenLeaf', 'VegNitrogenStem', 'VegNitrogenRoot']
    
if STEP == 2:
    target_vars = ['NPPAll1', 'NPPAll2', 'NPPAll3', 'NPPAll4', 'NPPAll5']
    
    calib_params = [# here for reference
                    ['krb(0)','krb(0).1','krb(0).2','krb(0).3','krb(0).4'],
                    ['krb(1)','krb(1).1','krb(1).2','krb(1).4'],
                    ['krb(2)','krb(2).1','krb(2).2','krb(2).4']]
    
    vars_nopft  = ['NPPAll']
    
#if STEP == 2:
#    target_vars = ['NPPAll1', 'NPPAll2', 'NPPAll3', 'NPPAll4', 'NPPAll5',
#                   'VegCarbonLeaf1', 'VegCarbonStem1', 'VegCarbonRoot1', 
#                   'VegCarbonLeaf2', 'VegCarbonStem2', 'VegCarbonRoot2',
#                   'VegCarbonLeaf3', 'VegCarbonStem3', 'VegCarbonRoot3',
#                   'VegCarbonLeaf4', 
#                   'VegCarbonLeaf5', 'VegCarbonStem5', 'VegCarbonRoot5']
    
#    calib_params = [['krb(0)','krb(0).1','krb(0).2','krb(0).3','krb(0).4'],
#                    ['krb(1)','krb(1).1','krb(1).2','krb(1).4'],
#                    ['krb(2)','krb(2).1','krb(2).2','krb(2).4'],
#                    ['cfall(0)','cfall(0).1','cfall(0).2','cfall(0).3','cfall(0).4'],
#                    ['cfall(1)','cfall(1).1','cfall(1).2','cfall(1).4'],
#                    ['cfall(2)','cfall(2).1','cfall(2).2','cfall(2).4']]
    
#    calib_params_flat = ['krb(0)','krb(0).1','krb(0).2','krb(0).3','krb(0).4',
#                    'krb(1)','krb(1).1','krb(1).2','krb(1).3',
#                    'krb(2)','krb(2).1','krb(2).2','krb(2).3',
#                    'cfall(0)','cfall(0).1','cfall(0).2','cfall(0).3','cfall(0).4',
#                    'cfall(1)','cfall(1).1','cfall(1).2','cfall(1).3',
#                    'cfall(2)','cfall(2).1','cfall(2).2','cfall(2).3']
    
#    vars_nopft  = ['NPPAll', 'VegCarbonLeaf', 'VegCarbonStem', 'VegCarbonRoot']
    
#if STEP == 2:
#    target_vars = ['VegCarbonLeaf1', 'VegCarbonStem1', 'VegCarbonRoot1', 
#                   'VegCarbonLeaf2', 'VegCarbonStem2', 'VegCarbonRoot2',
#                   'VegCarbonLeaf3', 'VegCarbonStem3', 'VegCarbonRoot3',
#                   'VegCarbonLeaf4', 
#                   'VegCarbonLeaf5', 'VegCarbonStem5', 'VegCarbonRoot5',
#                   'VegNitrogenLeaf1', 'VegNitrogenStem1', 'VegNitrogenRoot1', 
#                   'VegNitrogenLeaf2', 'VegNitrogenStem2', 'VegNitrogenRoot2',
#                   'VegNitrogenLeaf3', 'VegNitrogenStem3', 'VegNitrogenRoot3',
#                   'VegNitrogenLeaf4', 
#                   'VegNitrogenLeaf5', 'VegNitrogenStem5', 'VegNitrogenRoot5']
    
#    calib_params = [['cfall(0)','cfall(0).1','cfall(0).2','cfall(0).3','cfall(0).4'],
#                    ['cfall(1)','cfall(1).1','cfall(1).2','cfall(1).4'],
#                    ['cfall(2)','cfall(2).1','cfall(2).2','cfall(2).4'],
#                    ['nfall(0)','nfall(0).1','nfall(0).2','nfall(0).3','nfall(0).4'],
#                    ['nfall(1)','nfall(1).1','nfall(1).2','nfall(1).4'],
#                    ['nfall(2)','nfall(2).1','nfall(2).2','nfall(2).4']]
    
#    calib_params_flat = ['cfall(0)','cfall(0).1','cfall(0).2','cfall(0).3','cfall(0).4',
#                    'cfall(1)','cfall(1).1','cfall(1).2','cfall(1).3',
#                    'cfall(2)','cfall(2).1','cfall(2).2','cfall(2).3',
#                    'nfall(0)','nfall(0).1','nfall(0).2','nfall(0).3','nfall(0).4',
#                    'nfall(1)','nfall(1).1','nfall(1).2','nfall(1).3',
#                    'nfall(2)','nfall(2).1','nfall(2).2','nfall(2).3']
    
#    vars_nopft  = ['VegCarbonLeaf', 'VegCarbonStem', 'VegCarbonRoot', 
#                   'VegNitrogenLeaf', 'VegNitrogenStem', 'VegNitrogenRoot']
    
#if STEP == 2:
#    target_vars = ['NPPAll1', 'NPPAll2', 'NPPAll3', 'NPPAll4', 'NPPAll5',
#                   'VegCarbonLeaf1', 'VegCarbonStem1', 'VegCarbonRoot1', 'VegCarbonLeaf2', 'VegCarbonLeaf3',
#                   'VegCarbonStem1', 'VegCarbonRoot3', 'VegCarbonLeaf4',
#                   'VegCarbonRoot4', 'VegCarbonLeaf5']
#    
#    calib_params = [['nmax', 'nmax.1', 'nmax.2', 'nmax.3', 'nmax.4'], # here for reference
#                    ['krb(0)','krb(0).1','krb(0).2','krb(0).3','krb(0).4'],
#                    ['krb(1)','krb(1).1'],
#                    ['krb(2)','krb(2).1','krb(2).2']]
#    
#    vars_nopft  = ['NPPAll', 'VegCarbonLeaf', 'VegCarbonStem', 'VegCarbonRoot']
    
if STEP == 3:
    target_vars = [
                   'VegCarbonLeaf1', 'VegCarbonStem1', 'VegCarbonRoot1', 'VegCarbonLeaf2', 'VegCarbonLeaf3',
                   'VegCarbonStem3', 'VegCarbonRoot3', 'VegCarbonLeaf4',
                   'VegCarbonRoot4', 'VegCarbonLeaf5',
                   'VegNitrogenLeaf1', 'VegNitrogenStem1', 'VegNitrogenRoot1', 'VegNitrogenLeaf2', 'VegNitrogenLeaf3',
                   'VegNitrogenStem3', 'VegNitrogenRoot3', 'VegNitrogenLeaf4',
                   'VegNitrogenRoot4', 'VegNitrogenLeaf5']
    
    calib_params = [
                    ['cfall(0)','cfall(0).1','cfall(0).2','cfall(0).3','cfall(0).4'],
                    ['cfall(1)','cfall(1).1'],
                    ['cfall(2)','cfall(2).1','cfall(2).2'],
                    ['nfall(0)','nfall(0).1','nfall(0).2','nfall(0).3','nfall(0).4'],
                    ['nfall(1)','nfall(1).1'],
                    ['nfall(2)','nfall(2).1','nfall(2).2']]
    calib_params_flat=[
                    'cfall(0)','cfall(0).1','cfall(0).2','cfall(0).3','cfall(0).4',
                    'cfall(1)','cfall(1).1',
                    'cfall(2)','cfall(2).1','sudocfall(2).2',
                    'nfall(0)','nfall(0).1','nfall(0).2','nfall(0).3','nfall(0).4',
                    'nfall(1)','nfall(1).1',
                    'nfall(2)','nfall(2).1','nfall(2).2']
    
if STEP == 3:
    target_vars = ['NPPAll1', 'NPPAll2', 'NPPAll3', 'NPPAll4', 'NPPAll5',
                   'VegCarbonLeaf1', 'VegCarbonStem1', 'VegCarbonRoot1', 'VegCarbonLeaf2', 'VegCarbonLeaf3',
                   'VegCarbonStem3', 'VegCarbonRoot3', 'VegCarbonLeaf4',
                   'VegCarbonRoot4', 'VegCarbonLeaf5',
                   'VegNitrogenLeaf1', 'VegNitrogenStem1', 'VegNitrogenRoot1', 'VegNitrogenLeaf2', 'VegNitrogenLeaf3',
                   'VegNitrogenStem3', 'VegNitrogenRoot3', 'VegNitrogenLeaf4',
                   'VegNitrogenRoot4', 'VegNitrogenLeaf5']
    
    calib_params = [['nmax', 'nmax.1', 'nmax.2', 'nmax.3', 'nmax.4'], # here for reference
                    ['krb(0)','krb(0).1','krb(0).2','krb(0).3','krb(0).4'],
                    ['krb(1)','krb(1).1'],
                    ['krb(2)','krb(2).1','krb(2).2'],
                    ['cfall(0)','cfall(0).1','cfall(0).2','cfall(0).3','cfall(0).4'],
                    ['cfall(1)','cfall(1).1'],
                    ['cfall(2)','cfall(2).1','cfall(2).2'],
                    ['nfall(0)','nfall(0).1','nfall(0).2','nfall(0).3','nfall(0).4'],
                    ['nfall(1)','nfall(1).1'],
                    ['nfall(2)','nfall(2).1','nfall(2).2']]
    calib_params_flat=['nmax', 'nmax.1', 'nmax.2', 'nmax.3', 'nmax.4', # here for reference
                    'krb(0)','krb(0).1','krb(0).2','krb(0).3','krb(0).4',
                    'krb(1)','krb(1).1',
                    'krb(2)','krb(2).1','krb(2).2',
                    'cfall(0)','cfall(0).1','cfall(0).2','cfall(0).3','cfall(0).4',
                    'cfall(1)','cfall(1).1',
                    'cfall(2)','cfall(2).1','cfall(2).2',
                    'nfall(0)','nfall(0).1','nfall(0).2','nfall(0).3','nfall(0).4',
                    'nfall(1)','nfall(1).1',
                    'nfall(2)','nfall(2).1','nfall(2).2']
    
    vars_nopft  = ['NPPAll', 'VegCarbonLeaf', 'VegCarbonStem', 'VegCarbonRoot', 'VegNitrogenLeaf', 'VegNitrogenStem', 'VegNitrogenRoot']
    
if STEP == 4:
    target_vars = ['CarbonShallow', 'CarbonDeep', 'CarbonMineralSum', 'OrganicNitrogenSum', 'AvailableNitrogenSum']
    
    calib_params = [['micbnup', 'kdcrawc', 'kdcsoma', 'kdcsompr', 'kdcsomcr']] # here for reference
    calib_params_flat = ['micbnup', 'kdcrawc', 'kdcsoma', 'kdcsompr', 'kdcsomcr']
    vars_nopft= ['CarbonShallow', 'CarbonDeep', 'CarbonMineralSum', 'OrganicNitrogenSum', 'AvailableNitrogenSum']


def Filter(string_list, substr):
    """ filters list of strings for items containing substring """
    return [str for str in string_list if
             any(sub in str for sub in substr)]


def calc_rmse(x,y):
    """ Return rmse where x and y are array-like """
    return ((x-y) ** 2).mean() ** .5


def calc_overall_accuracy(results, sample_matrix, target_vars, vars_nopft):
    
    results = pd.read_csv(results, names=target_vars)
    #print(results)
    # extract targets from last row of results csv
    targets = results.iloc[int(len(results)-1)] 
    results = results.iloc[0:len(results)-1]
    
    r2s = []
    rmses=[]
    
    #calculate r2s and rmse for individual variables 
    for index, row in results.iterrows():
        
        tgt_r2s = []
        tgt_rmses = []
        
        for var_nopft in vars_nopft:
            
            results_vars_cols = Filter(results, [var_nopft])
            if row[results_vars_cols].isna().values.any():
                tgt_r2s.append(0)
                tgt_rmses.append(10000000)
                continue
            tgt_r2s.append(r2_score(targets[results_vars_cols], row[results_vars_cols]))
            tgt_rmses.append(calc_rmse(targets[results_vars_cols], row[results_vars_cols]))  
            
        #r2s.append(tgt_r2s)
        #rmses.append(tgt_rmses)
        r2s.append(r2_score(targets[results_vars_cols], row[results_vars_cols]))
        rmses.append(calc_rmse(targets[results_vars_cols], row[results_vars_cols]))

    # concatenate sample matrix to results
    sample_matrix = pd.read_csv(sample_matrix)
    results[sample_matrix.columns] = sample_matrix
    r2s=np.array(r2s)
    rmses=np.array(rmses)
    results['r2']= r2s
    results['rmse']= rmses
    #iterate over target variables (no pft or compartment)
    #for idx, name in enumerate(vars_nopft):
        
        #set r2 and rmse columns
    #    results[name + '_r2_raw'] = r2s[:, idx]
    #    results[name + '_rmse_raw'] = rmses[:, idx]
        
    #    #scale rmse between min and max
    #    results[name + '_rmse_scaled'] = (results[name + '_rmse_raw']-np.nanmin(results[name + '_rmse_raw']))/(np.max(results[name + '_rmse_raw'])-np.nanmin(results[name + '_rmse_raw']))
        
    #    #subrtact scaled rmse from r2 for overall accuracy term
    #    results[name + '_accuracy'] = (results[name + '_r2_raw']-results[name+'_rmse_scaled'])
    
    #scale r2 and rmse and combine for overall accuracy term
    results['rmse_scaled'] = (results['rmse']-np.nanmin(results['rmse']))/(np.max(results['rmse'])-np.nanmin(results['rmse']))
    results['overall_accuracy'] = (results['r2']-results['rmse_scaled'])
    results['mean_rmse'] = results[Filter(list(results.columns), ['rmse'])].mean(axis=1)
    results['mean_r2'] = results[Filter(list(results.columns), ['r2'])].mean(axis=1)
    
    return results, targets


if STEP == 1:
    results, targets = calc_overall_accuracy(STEP1_results, STEP1_sample_matrix, target_vars, vars_nopft)
    
if STEP == 'NPP_VegC_PFT':
    results, targets = calc_overall_accuracy(NPP_VegC_PFT_results, NPP_VegC_PFT_sample_matrix, target_vars, vars_nopft)
    
if STEP == 'NPP_VegC_VegN_PFT':
    results, targets = calc_overall_accuracy(NPP_VegC_PFT_results, NPP_VegC_PFT_sample_matrix, target_vars, vars_nopft)
    
if STEP == 2:
    results, targets = calc_overall_accuracy(STEP2_results, STEP2_sample_matrix, target_vars, vars_nopft)
    
if STEP == 3:
    results, targets = calc_overall_accuracy(STEP3_results, STEP3_sample_matrix, target_vars, vars_nopft)

if STEP == 4:
    results, targets = calc_overall_accuracy(STEP4_results, STEP4_sample_matrix, target_vars, vars_nopft)

print('{} runs'.format(len(results)))


results


#get indices of top 15 performing parameter sets
perf = np.argsort(results['overall_accuracy'])[::-1]
#perf = np.argsort(results['mean_rmse'])[::-1]
top = perf[:50].values.tolist()
first = perf[:1].values.tolist()


perf


fig, ax = plt.subplots(figsize = (8,5))

sns.scatterplot(data = results, x='mean_rmse', y='mean_r2')
sns.scatterplot(data = results.iloc[top], x='mean_rmse', y='mean_r2', color='red')
sns.scatterplot(data = results.iloc[first], x='mean_rmse', y='mean_r2', color='yellow')

ax.title.set_text('Step {}'.format(STEP))
ax.set_ylabel('Mean $r^2$ across all variables')
ax.set_xlabel('Mean RMSE across all variables - scaled between min and max')
plt.ylim(0,1)
#plt.xlim(0,1)


results.columns


if STEP == 'NPP_VegC_PFT' or STEP=='NPP_VegC_VegN_PFT':
    pft=1
    fig, axes = plt.subplots(3,3, figsize = (10,6))
    fig.suptitle('STEP 2 VEGC for Deciduous Shrub')

    axes[0,0].axhline(targets[f'VegCarbonLeaf{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(0)', y=f'VegCarbonLeaf{pft}', ax=axes[0,0], alpha=0.3,legend=False, hue=f'NPPAll{pft}')
    #sns.scatterplot(data = results.iloc[top], x='cfall(0)', y=f'VegCarbonLeaf{pft}', ax=axes[0,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(0)', y=f'VegCarbonLeaf{pft}', ax=axes[0,0], color='yellow',legend=False)

    axes[0,1].axhline(targets[f'VegCarbonStem{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(1)', y=f'VegCarbonStem{pft}', ax=axes[0,1], alpha=0.3,legend=False, hue=f'NPPAll{pft}')
    #sns.scatterplot(data = results.iloc[top], x='cfall(1)', y=f'VegCarbonStem{pft}', ax=axes[0,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(1)', y=f'VegCarbonStem{pft}', ax=axes[0,1], color='yellow',legend=False)

    axes[0,2].axhline(targets[f'VegCarbonRoot{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(2)', y=f'VegCarbonRoot{pft}', ax=axes[0,2], alpha=0.3,legend=False, hue=f'NPPAll{pft}')
    #sns.scatterplot(data = results.iloc[top], x='cfall(2)', y=f'VegCarbonRoot{pft}', ax=axes[0,2], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(2)', y=f'VegCarbonRoot{pft}', ax=axes[0,2], color='yellow',legend=False)
    
    axes[1,0].axhline(targets[f'NPPAll{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0)', y=f'NPPAll{pft}', ax=axes[1,0], alpha=0.3,legend=False, hue=f'VegCarbonLeaf{pft}')
    #sns.scatterplot(data = results.iloc[top], x='krb(0)', y=f'NPPAll{pft}', ax=axes[1,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0)', y=f'NPPAll{pft}', ax=axes[1,0], color='yellow',legend=False)
    
    axes[1,1].axhline(targets[f'NPPAll{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(1)', y=f'NPPAll{pft}', ax=axes[1,1], alpha=0.3,legend=False, hue=f'VegCarbonStem{pft}')
    #sns.scatterplot(data = results.iloc[top], x='krb(1)', y=f'NPPAll{pft}', ax=axes[1,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(1)', y=f'NPPAll{pft}', ax=axes[1,1], color='yellow',legend=False)
    
    axes[1,2].axhline(targets[f'NPPAll{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(2)', y=f'NPPAll{pft}', ax=axes[1,2], alpha=0.3,legend=False, hue=f'VegCarbonRoot{pft}')
    #sns.scatterplot(data = results.iloc[top], x='krb(2)', y=f'NPPAll{pft}', ax=axes[1,2], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(2)', y=f'NPPAll{pft}', ax=axes[1,2], color='yellow',legend=False)
    
    axes[2,0].axhline(targets[f'NPPAll{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='nfall(0)', y=f'NPPAll{pft}', ax=axes[2,0], alpha=0.3,legend=False, hue=f'VegCarbonLeaf{pft}')
    #sns.scatterplot(data = results.iloc[top], x='krb(0)', y=f'NPPAll{pft}', ax=axes[1,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='nfall(0)', y=f'NPPAll{pft}', ax=axes[2,0], color='yellow',legend=False)
    
    axes[2,1].axhline(targets[f'NPPAll{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='nfall(1)', y=f'NPPAll{pft}', ax=axes[2,1], alpha=0.3,legend=False, hue=f'VegCarbonLeaf{pft}')
    #sns.scatterplot(data = results.iloc[top], x='krb(1)', y=f'NPPAll{pft}', ax=axes[1,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='nfall(1)', y=f'NPPAll{pft}', ax=axes[2,1], color='yellow',legend=False)
    
    axes[2,2].axhline(targets[f'NPPAll{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='nmax', y=f'NPPAll{pft}', ax=axes[2,2], alpha=0.3,legend=False, hue=f'VegCarbonLeaf{pft}')
    #sns.scatterplot(data = results.iloc[top], x='krb(2)', y=f'NPPAll{pft}', ax=axes[1,2], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='nmax', y=f'NPPAll{pft}', ax=axes[2,2], color='yellow',legend=False)

    fig.tight_layout()


if 'NPP_VegC_VegN_PFT':
    pft=1
    fig, axes = plt.subplots(3,3, figsize = (10,6))
    fig.suptitle('STEP 2 VEGC for Deciduous Shrub')

    axes[0,0].axhline(targets[f'VegNitrogenLeaf{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='nfall(0)', y=f'VegNitrogenLeaf{pft}', ax=axes[0,0], alpha=0.3,legend=False, hue=f'NPPAll{pft}')
    #sns.scatterplot(data = results.iloc[top], x='cfall(0)', y=f'VegNitrogenLeaf{pft}', ax=axes[0,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='nfall(0)', y=f'VegNitrogenLeaf{pft}', ax=axes[0,0], color='yellow',legend=False)

    axes[0,1].axhline(targets[f'VegNitrogenStem{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='nfall(1)', y=f'VegNitrogenStem{pft}', ax=axes[0,1], alpha=0.3,legend=False, hue=f'NPPAll{pft}')
    #sns.scatterplot(data = results.iloc[top], x='cfall(1)', y=f'VegNitrogenStem{pft}', ax=axes[0,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='nfall(1)', y=f'VegNitrogenStem{pft}', ax=axes[0,1], color='yellow',legend=False)

    axes[0,2].axhline(targets[f'VegNitrogenRoot{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='nfall(2)', y=f'VegNitrogenRoot{pft}', ax=axes[0,2], alpha=0.3,legend=False, hue=f'NPPAll{pft}')
    #sns.scatterplot(data = results.iloc[top], x='cfall(2)', y=f'VegNitrogenRoot{pft}', ax=axes[0,2], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='nfall(2)', y=f'VegNitrogenRoot{pft}', ax=axes[0,2], color='yellow',legend=False)
    
    axes[1,0].axhline(targets[f'VegNitrogenLeaf{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(0)', y=f'VegNitrogenLeaf{pft}', ax=axes[1,0], alpha=0.3,legend=False, hue=f'NPPAll{pft}')
    #sns.scatterplot(data = results.iloc[top], x='cfall(0)', y=f'VegNitrogenLeaf{pft}', ax=axes[0,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(0)', y=f'VegNitrogenLeaf{pft}', ax=axes[1,0], color='yellow',legend=False)

    axes[1,1].axhline(targets[f'VegNitrogenStem{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(1)', y=f'VegNitrogenStem{pft}', ax=axes[1,1], alpha=0.3,legend=False, hue=f'NPPAll{pft}')
    #sns.scatterplot(data = results.iloc[top], x='cfall(1)', y=f'VegNitrogenStem{pft}', ax=axes[0,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(1)', y=f'VegNitrogenStem{pft}', ax=axes[1,1], color='yellow',legend=False)

    axes[1,2].axhline(targets[f'VegNitrogenRoot{pft}'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(2)', y=f'VegNitrogenRoot{pft}', ax=axes[1,2], alpha=0.3,legend=False, hue=f'NPPAll{pft}')
    #sns.scatterplot(data = results.iloc[top], x='cfall(2)', y=f'VegNitrogenRoot{pft}', ax=axes[0,2], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(2)', y=f'VegNitrogenRoot{pft}', ax=axes[1,2], color='yellow',legend=False)
    


results.iloc[top][[f'VegCarbonLeaf{pft}', f'VegCarbonStem{pft}', f'VegCarbonRoot{pft}', f'NPPAll{pft}']].sort_values(by='NPPAll1')
#results.iloc[top][[f'VegCarbonLeaf{pft}', f'NPPAll{pft}']]


targets[[f'VegCarbonLeaf{pft}', f'VegCarbonStem{pft}', f'VegCarbonRoot{pft}', f'NPPAll{pft}']]
#targets[[f'VegCarbonLeaf{pft}', f'NPPAll{pft}']]


results.iloc[149][calib_params_flat]


fig, ax=plt.subplots(figsize=(8,5))
#sns.lineplot(results[target_vars].T, legend=False, alpha=0.6)
sns.lineplot(results[target_vars].iloc[149].T, legend=False, alpha=0.6)
sns.scatterplot(targets.T, color='red')
plt.xticks(rotation=83)
plt.yscale('log')
plt.ylabel('Value')

fig.tight_layout()
plt.savefig('BONA_Black_Spruce_SA_ex.jpg', dpi=300)


#
#print(results[['VegVarbonStem1']] + results[['VegVarbonStem3']])


results


#sns.lineplot(results[target_vars].T, legend=False, alpha=0.6)
sns.lineplot(results[target_vars].iloc[first].T, legend=False, alpha=0.6, color='red')
sns.scatterplot(targets.T, color='red')
plt.xticks(rotation=90)
plt.yscale('log')
plt.ylabel('Value')


fig, axes = plt.subplots(3,3, figsize = (10,6))

axes[0,0].axhline(targets['CarbonShallow'], color='grey', alpha=0.5)
sns.scatterplot(data = results, x='micbnup', y='CarbonShallow', ax=axes[0,0], alpha=0.3,legend=False)
sns.scatterplot(data = results.iloc[first], x='micbnup', y='CarbonShallow', ax=axes[0,0], color='yellow',legend=False)

axes[0,1].axhline(targets['CarbonShallow'], color='grey', alpha=0.5)
sns.scatterplot(data = results, x='kdcrawc', y='CarbonShallow', ax=axes[0,1], alpha=0.3,legend=False)
sns.scatterplot(data = results.iloc[first], x='kdcrawc', y='CarbonShallow', ax=axes[0,1], color='yellow',legend=False)

axes[0,2].axhline(targets['CarbonShallow'], color='grey', alpha=0.5)
sns.scatterplot(data = results, x='kdcsoma', y='CarbonShallow', ax=axes[0,2], alpha=0.3,legend=False)
sns.scatterplot(data = results.iloc[first], x='kdcsoma', y='CarbonShallow', ax=axes[0,2], color='yellow',legend=False)


axes[1,0].axhline(targets['CarbonDeep'], color='grey', alpha=0.5)
sns.scatterplot(data = results, x='micbnup', y='CarbonDeep', ax=axes[1,0], alpha=0.3,legend=False)
sns.scatterplot(data = results.iloc[first], x='micbnup', y='CarbonDeep', ax=axes[1,0], color='yellow',legend=False)

axes[1,1].axhline(targets['CarbonDeep'], color='grey', alpha=0.5)
sns.scatterplot(data = results, x='kdcrawc', y='CarbonDeep', ax=axes[1,1], alpha=0.3,legend=False)
sns.scatterplot(data = results.iloc[first], x='kdcrawc', y='CarbonDeep', ax=axes[1,1], color='yellow',legend=False)

axes[1,2].axhline(targets['CarbonDeep'], color='grey', alpha=0.5)
sns.scatterplot(data = results, x='kdcsompr', y='CarbonDeep', ax=axes[1,2], alpha=0.3,legend=False)
sns.scatterplot(data = results.iloc[first], x='kdcsompr', y='CarbonDeep', ax=axes[1,2], color='yellow',legend=False)

axes[2,0].axhline(targets['CarbonMineralSum'], color='grey', alpha=0.5)
sns.scatterplot(data = results, x='micbnup', y='CarbonMineralSum', ax=axes[2,0], alpha=0.3,legend=False)
sns.scatterplot(data = results.iloc[first], x='micbnup', y='CarbonMineralSum', ax=axes[2,0], color='yellow',legend=False)

axes[2,1].axhline(targets['CarbonMineralSum'], color='grey', alpha=0.5)
sns.scatterplot(data = results, x='kdcsomcr', y='CarbonMineralSum', ax=axes[2,1], alpha=0.3,legend=False)
sns.scatterplot(data = results.iloc[first], x='kdcsomcr', y='CarbonMineralSum', ax=axes[2,1], color='yellow',legend=False)

axes[2,2].axhline(targets['CarbonMineralSum'], color='grey', alpha=0.5)
sns.scatterplot(data = results, x='kdcsompr', y='CarbonMineralSum', ax=axes[2,2], alpha=0.3,legend=False)
sns.scatterplot(data = results.iloc[first], x='kdcsompr', y='CarbonMineralSum', ax=axes[2,2], color='yellow',legend=False)

fig.tight_layout()


targets


results.loc[(results['CarbonDeep']<9000) & (results['CarbonDeep']>8500)].sort_values(by='CarbonShallow')


results.iloc[first]


if STEP == 'NPP_VegC_PFT':
    fig, ax=plt.subplots()
    ax.axhline(targets['NPPAll3'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(2)', y='NPPAll3', ax=ax, alpha=0.3,legend=False)
    sns.scatterplot(data = results.iloc[top], x='krb(2)', y='NPPAll3', ax=ax, color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(2)', y='NPPAll3', ax=ax, color='yellow',legend=False)
    ax.title.set_text('EvrTree')


palette = sns.color_palette("mako", as_cmap=True)

if STEP == 1:
    fig, axes = plt.subplots(2,3, figsize = (8,5))
    fig.suptitle('STEP 1 cmax vs GPP for each PFT')

    axes[0,0].axhline(targets['GPP1'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cmax', y='GPP1', ax=axes[0,0], legend=False, alpha=0.05)
    sns.scatterplot(data = results.iloc[top], x='cmax', y='GPP1', ax=axes[0,0], color='red', legend=False)
    sns.scatterplot(data = results.iloc[first], x='cmax', y='GPP1', ax=axes[0,0], color='yellow', legend=False)
    axes[0,0].title.set_text(pfts[0])

    axes[0,1].axhline(targets['GPP2'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cmax.1', y='GPP2', ax=axes[0,1], legend=False, alpha=0.05)
    sns.scatterplot(data = results.iloc[top], x='cmax.1', y='GPP2', ax=axes[0,1], color='red', legend=False)
    sns.scatterplot(data = results.iloc[first], x='cmax.1', y='GPP2', ax=axes[0,1], color='yellow', legend=False)
    axes[0,1].title.set_text(pfts[1])

    axes[0,2].axhline(targets['GPP3'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cmax.2', y='GPP3', ax=axes[0,2], legend=False, alpha=0.05)
    sns.scatterplot(data = results.iloc[top], x='cmax.2', y='GPP3', ax=axes[0,2], color='red', legend=False)
    sns.scatterplot(data = results.iloc[first], x='cmax.2', y='GPP3', ax=axes[0,2], color='yellow', legend=False)
    axes[0,2].title.set_text(pfts[2])

    axes[1,0].axhline(targets['GPP4'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cmax.3', y='GPP4', ax=axes[1,0], alpha=0.05, palette=palette)
    sns.scatterplot(data = results.iloc[top], x='cmax.3', y='GPP4', ax=axes[1,0], color='red', legend=False)
    sns.scatterplot(data = results.iloc[first], x='cmax.3', y='GPP4', ax=axes[1,0], color='yellow', legend=False)
    axes[1,0].title.set_text(pfts[3])

    axes[1,1].axhline(targets['GPP5'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cmax.4', y='GPP5', ax=axes[1,1], legend=False, alpha=0.05)
    sns.scatterplot(data = results.iloc[top], x='cmax.4', y='GPP5', ax=axes[1,1], color='red', label='Top 15 runs')
    sns.scatterplot(data = results.iloc[first], x='cmax.4', y='GPP5', ax=axes[1,1], color='yellow', label='Top run')
    axes[1,1].title.set_text(pfts[4])

    #axes[1,1].legend(loc='lower right', bbox_to_anchor=(1,0), title='Overall Accuracy')
   
    fig.tight_layout()


results.iloc[first]




