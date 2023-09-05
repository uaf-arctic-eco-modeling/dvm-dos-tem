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


np.nan<0


#Set step, paths, pfts and run all

STEP = 4

STEP1_results = '/data/workflows/US-Prr-STEP1-SA/results.csv'
STEP1_sample_matrix = '/data/workflows/US-Prr-STEP1-SA/sample_matrix.csv'

STEP2_results = '/data/workflows/US-Prr-STEP2-SA/results.csv'
STEP2_sample_matrix = '/data/workflows/US-Prr-STEP2-SA/sample_matrix.csv'

STEP3_results = '/data/workflows/US-Prr-STEP3-SA-v2/results.csv'
STEP3_sample_matrix = '/data/workflows/US-Prr-STEP3-SA-v2/sample_matrix.csv'

#STEP3_results = 'results_US-Prr_STEP3.csv'
#STEP3_sample_matrix = 'sample_matrix_US-Prr_STEP3.csv'

STEP4_results = '/data/workflows/US-Prr-STEP4-SA/results.csv'
STEP4_sample_matrix = '/data/workflows/US-Prr-STEP4-SA/sample_matrix.csv'

#STEP4_results = '/data/workflows/US-Prr-STEP4-SA/results.csv'
#STEP4_sample_matrix = '/data/workflows/US-Prr-STEP4-SA/sample_matrix.csv'

pfts=['Black Spruce', 'Moss (Sphagnum dominant)', 'Shrubs (Deciduous Dominant)', 'Tussock Cottongrass', 'Reindeer Lichen']


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


#if number of pfts != 5 you will have to adjust these values

if STEP == 1:
    target_vars = ['GPP1', 'GPP2', 'GPP3', 'GPP4', 'GPP5']
    
    calib_params = [['cmax', 'cmax.1', 'cmax.2', 'cmax.3', 'cmax.4']] # here for reference
    
    vars_nopft= ['GPP']

if STEP == 2:
    target_vars = ['NPPAll1', 'NPPAll2', 'NPPAll3', 'NPPAll4', 'NPPAll5',
                   'VegCarbonLeaf1', 'VegCarbonStem1', 'VegCarbonRoot1', 'VegCarbonLeaf2', 'VegCarbonLeaf3',
                   'VegCarbonStem3', 'VegCarbonRoot3', 'VegCarbonLeaf4',
                   'VegCarbonRoot4', 'VegCarbonLeaf5']
    
    calib_params = [['nmax', 'nmax.1', 'nmax.2', 'nmax.3', 'nmax.4'], # here for reference
                    ['krb(0)','krb(0).1','krb(0).2','krb(0).3','krb(0).4'],
                    ['krb(1)','krb(1).1'],
                    ['krb(2)','krb(2).1','krb(2).2']]
    
    vars_nopft  = ['NPPAll', 'VegCarbonLeaf', 'VegCarbonStem', 'VegCarbonRoot']
    
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
    targets = results.loc[len(results)-1] 
    results = results.loc[0:len(results)-2]
    
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
if STEP == 2:
    results, targets = calc_overall_accuracy(STEP2_results, STEP2_sample_matrix, target_vars, vars_nopft)
    
if STEP == 3:
    results, targets = calc_overall_accuracy(STEP3_results, STEP3_sample_matrix, target_vars, vars_nopft)

if STEP == 4:
    results, targets = calc_overall_accuracy(STEP4_results, STEP4_sample_matrix, target_vars, vars_nopft)

print('{} runs'.format(len(results)))


results['mean_r2']


#get indices of top 15 performing parameter sets
perf = np.argsort(results['overall_accuracy'])[::-1]
#perf = np.argsort(results['mean_rmse'])[::-1]
top = perf[:20].values.tolist()
first = perf[:1].values.tolist()


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


if STEP == 2:
    fig, axes = plt.subplots(2,3, figsize = (10,8))
    fig.suptitle('STEP 2 nmax vs NPPAll for each PFT')

    axes[0,0].axhline(targets['NPPAll1'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='nmax', y='NPPAll1', ax=axes[0,0], hue='krb(0)', alpha=0.3,legend=False)
    sns.scatterplot(data = results.iloc[top], x='nmax', y='NPPAll1', ax=axes[0,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='nmax', y='NPPAll1', ax=axes[0,0], color='yellow',legend=False)
    axes[0,0].title.set_text('Black Spruce')

    axes[0,1].axhline(targets['NPPAll2'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='nmax.1', y='NPPAll2', ax=axes[0,1], hue='krb(0).1', legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='nmax.1', y='NPPAll2', ax=axes[0,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='nmax.1', y='NPPAll2', ax=axes[0,1], color='yellow',legend=False)
    axes[0,1].title.set_text('Moss (Sphagnum dominant)')

    axes[0,2].axhline(targets['NPPAll3'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='nmax.2', y='NPPAll3', ax=axes[0,2], hue='krb(0).2', legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='nmax.2', y='NPPAll3', ax=axes[0,2], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='nmax.2', y='NPPAll3', ax=axes[0,2], color='yellow',legend=False)
    axes[0,2].title.set_text('Shrubs (Evergreen Dominant)')

    axes[1,0].axhline(targets['NPPAll4'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='nmax.3', y='NPPAll4', ax=axes[1,0], hue='krb(0).3', legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='nmax.3', y='NPPAll4', ax=axes[1,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='nmax.3', y='NPPAll4', ax=axes[1,0], color='yellow',legend=False)
    axes[1,0].title.set_text('Tussock Cottongrass')

    axes[1,1].axhline(targets['NPPAll5'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='nmax.4', y='NPPAll5', ax=axes[1,1], hue='krb(0).4', legend=True, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='nmax.4', y='NPPAll5', ax=axes[1,1], color='red',label='Top 15 runs')
    sns.scatterplot(data = results.iloc[first], x='nmax.4', y='NPPAll5', ax=axes[1,1], color='yellow',label='Top run')
    axes[1,1].title.set_text('Reindeer Lichen')

    axes[1,1].legend(loc='lower right', bbox_to_anchor=(0,-.5), title='krb(0)')

    fig.tight_layout()


if STEP == 2:
    fig, axes = plt.subplots(2,3, figsize = (10,8))
    fig.suptitle('STEP 2 VEGC for Black Spruce')

    axes[0,0].axhline(targets['VegCarbonLeaf1'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0)', y='VegCarbonLeaf1', ax=axes[0,0], hue='krb(0)', alpha=0.3,legend=False)
    sns.scatterplot(data = results.iloc[top], x='krb(0)', y='VegCarbonLeaf1', ax=axes[0,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0)', y='VegCarbonLeaf1', ax=axes[0,0], color='yellow',legend=False)
    axes[0,0].title.set_text('Black Spruce')

    axes[0,1].axhline(targets['VegCarbonStem1'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0)', y='VegCarbonStem1', ax=axes[0,1], hue='krb(0)', alpha=0.3,legend=False)
    sns.scatterplot(data = results.iloc[top], x='krb(0)', y='VegCarbonStem1', ax=axes[0,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0)', y='VegCarbonStem1', ax=axes[0,1], color='yellow',legend=False)
    axes[0,1].title.set_text('Black Spruce')
    
    axes[0,2].axhline(targets['VegCarbonRoot1'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0)', y='VegCarbonRoot1', ax=axes[0,2], hue='krb(0)', alpha=0.3,legend=False)
    sns.scatterplot(data = results.iloc[top], x='krb(0)', y='VegCarbonRoot1', ax=axes[0,2], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0)', y='VegCarbonRoot1', ax=axes[0,2], color='yellow',legend=False)
    axes[0,2].title.set_text('Black Spruce')


    fig.tight_layout()


if STEP == 2:
    fig, axes = plt.subplots(2,3, figsize = (10,8))
    fig.suptitle('STEP 2 nmax vs NPPAll for each PFT')

    axes[0,0].axhline(targets['VegCarbonLeaf2'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0).1', y='VegCarbonLeaf2', ax=axes[0,0], hue='krb(0).1', alpha=0.3,legend=False)
    sns.scatterplot(data = results.iloc[top], x='krb(0).1', y='VegCarbonLeaf2', ax=axes[0,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0).1', y='VegCarbonLeaf2', ax=axes[0,0], color='yellow',legend=False)
    axes[0,0].title.set_text('Moss')


    fig.tight_layout()


if STEP == 2:
    fig, axes = plt.subplots(2,3, figsize = (10,8))
    fig.suptitle('STEP 2 nmax vs NPPAll for each PFT')

    axes[0,0].axhline(targets['VegCarbonLeaf3'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0).2', y='VegCarbonLeaf3', ax=axes[0,0], hue='krb(0)', alpha=0.3,legend=False)
    sns.scatterplot(data = results.iloc[top], x='krb(0).2', y='VegCarbonLeaf3', ax=axes[0,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0).2', y='VegCarbonLeaf3', ax=axes[0,0], color='yellow',legend=False)
    axes[0,0].title.set_text('Shrub')

    axes[0,1].axhline(targets['VegCarbonStem3'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0).2', y='VegCarbonStem3', ax=axes[0,1], hue='krb(0)', alpha=0.3,legend=False)
    sns.scatterplot(data = results.iloc[top], x='krb(0).2', y='VegCarbonStem3', ax=axes[0,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0).2', y='VegCarbonStem3', ax=axes[0,1], color='yellow',legend=False)
    axes[0,1].title.set_text('Shrub')
    
    axes[0,2].axhline(targets['VegCarbonRoot3'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0).2', y='VegCarbonRoot3', ax=axes[0,2], hue='krb(0)', alpha=0.3,legend=False)
    sns.scatterplot(data = results.iloc[top], x='krb(0).2', y='VegCarbonRoot3', ax=axes[0,2], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0).2', y='VegCarbonRoot3', ax=axes[0,2], color='yellow',legend=False)
    axes[0,2].title.set_text('Shrub')


    fig.tight_layout()


if STEP == 2:
    fig, axes = plt.subplots(2,3, figsize = (10,8))
    fig.suptitle('STEP 2 nmax vs NPPAll for each PFT')

    axes[0,0].axhline(targets['VegCarbonLeaf4'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0).3', y='VegCarbonLeaf4', ax=axes[0,0], hue='krb(0)', alpha=0.3,legend=False)
    sns.scatterplot(data = results.iloc[top], x='krb(0).3', y='VegCarbonLeaf4', ax=axes[0,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0).3', y='VegCarbonLeaf4', ax=axes[0,0], color='yellow',legend=False)
    axes[0,0].title.set_text('Sedge')


    
    axes[0,2].axhline(targets['VegCarbonRoot4'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0).3', y='VegCarbonRoot4', ax=axes[0,2], hue='krb(0)', alpha=0.3,legend=False)
    sns.scatterplot(data = results.iloc[top], x='krb(0).3', y='VegCarbonRoot4', ax=axes[0,2], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0).3', y='VegCarbonRoot4', ax=axes[0,2], color='yellow',legend=False)
    axes[0,2].title.set_text('Sedge')


    fig.tight_layout()


if STEP == 2:
    fig, axes = plt.subplots(2,3, figsize = (10,8))
    fig.suptitle('STEP 2 nmax vs NPPAll for each PFT')

    axes[0,0].axhline(targets['VegCarbonLeaf5'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0).4', y='VegCarbonLeaf5', ax=axes[0,0], hue='krb(0).1', alpha=0.3,legend=False)
    sns.scatterplot(data = results.iloc[top], x='krb(0).4', y='VegCarbonLeaf5', ax=axes[0,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0).4', y='VegCarbonLeaf5', ax=axes[0,0], color='yellow',legend=False)
    axes[0,0].title.set_text('Lichen')


    fig.tight_layout()


if STEP == 2:
    fig, axes = plt.subplots(2,3, figsize = (10,8))
    fig.suptitle('STEP 2 krb(0) vs NPPAll for each PFT')

    axes[0,0].axhline(targets['NPPAll1'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0)', y='NPPAll1', ax=axes[0,0], hue='krb(2)', legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='krb(0)', y='NPPAll1', ax=axes[0,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0)', y='NPPAll1', ax=axes[0,0], color='yellow',legend=False)
    axes[0,0].title.set_text('Black Spruce')
    axes[0,0].set_xlim(-8,0)

    axes[0,1].axhline(targets['NPPAll2'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0).1', y='NPPAll2', ax=axes[0,1], hue='krb(2)', legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='krb(0).1', y='NPPAll2', ax=axes[0,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0).1', y='NPPAll2', ax=axes[0,1], color='yellow',legend=False)
    axes[0,1].title.set_text('Moss (Sphagnum dominant)')
    axes[0,1].set_xlim(-5,0)
    
    axes[0,2].axhline(targets['NPPAll3'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0).2', y='NPPAll3', ax=axes[0,2], hue='krb(2).1', legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='krb(0).2', y='NPPAll3', ax=axes[0,2], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0).2', y='NPPAll3', ax=axes[0,2], color='yellow',legend=False)
    axes[0,2].title.set_text('Shrubs (Evergreen Dominant)')
    axes[0,2].set_xlim(-5,0)

    axes[1,0].axhline(targets['NPPAll4'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0).3', y='NPPAll4', ax=axes[1,0], hue='krb(2).2', legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='krb(0).3', y='NPPAll4', ax=axes[1,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='krb(0).3', y='NPPAll4', ax=axes[1,0], color='yellow',legend=False)
    axes[1,0].title.set_text('Tussock Cottongrass')
    axes[1,0].set_xlim(-5,0)

    axes[1,1].axhline(targets['NPPAll5'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='krb(0).4', y='NPPAll5', ax=axes[1,1], hue='krb(2)', legend=True, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='krb(0).4', y='NPPAll5', ax=axes[1,1], color='red',label='Top 15 runs')
    sns.scatterplot(data = results.iloc[first], x='krb(0).4', y='NPPAll5', ax=axes[1,1], color='yellow',label='Top run')
    axes[1,1].title.set_text('Reindeer Lichen')
    axes[1,1].set_xlim(-5,0)

    axes[1,1].legend(loc='lower right', bbox_to_anchor=(0,-.5), title='krb(2)')

    fig.tight_layout()


if STEP == 3:
    fig, axes = plt.subplots(2,3, figsize = (10,8))
    fig.suptitle('STEP 2 cfall(0) vs NPPAll for each PFT')

    axes[0,0].axhline(targets['VegCarbonLeaf1'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(0)', y='VegCarbonLeaf1', ax=axes[0,0], legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='cfall(0)', y='VegCarbonLeaf1', ax=axes[0,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(0)', y='VegCarbonLeaf1', ax=axes[0,0], color='yellow',legend=False)
    axes[0,0].title.set_text('Black Spruce')
    
    axes[0,1].axhline(targets['VegCarbonLeaf2'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(0).1', y='VegCarbonLeaf2', ax=axes[0,1], legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='cfall(0).1', y='VegCarbonLeaf2', ax=axes[0,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(0).1', y='VegCarbonLeaf2', ax=axes[0,1], color='yellow',legend=False)
    axes[0,1].title.set_text('Moss')
    axes[0,1].set_ylim(0, 400)
    
    axes[0,2].axhline(targets['VegCarbonLeaf3'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(0).2', y='VegCarbonLeaf3', ax=axes[0,2], legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='cfall(0).2', y='VegCarbonLeaf3', ax=axes[0,2], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(0).2', y='VegCarbonLeaf3', ax=axes[0,2], color='yellow',legend=False)
    axes[0,2].title.set_text('Shrub')
    axes[0,2].set_ylim(0, 50)
    
    axes[1,0].axhline(targets['VegCarbonLeaf4'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(0).3', y='VegCarbonLeaf4', ax=axes[1,0], legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='cfall(0).3', y='VegCarbonLeaf4', ax=axes[1,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(0).3', y='VegCarbonLeaf4', ax=axes[1,0], color='yellow',legend=False)
    axes[1,0].title.set_text('sedge')
    axes[1,0].set_ylim(0, 50)
    
    axes[1,1].axhline(targets['VegCarbonLeaf5'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(0).4', y='VegCarbonLeaf5', ax=axes[1,1], legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='cfall(0).4', y='VegCarbonLeaf5', ax=axes[1,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(0).4', y='VegCarbonLeaf5', ax=axes[1,1], color='yellow',legend=False)
    axes[1,1].title.set_text('lichen')
    axes[1,1].set_ylim(0, 50)


if STEP == 3:
    fig, axes = plt.subplots(2,3, figsize = (10,8))
    fig.suptitle('STEP 2 cfall(0) vs NPPAll for each PFT')

    axes[0,0].axhline(targets['VegCarbonStem1'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(1)', y='VegCarbonStem1', ax=axes[0,0], legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='cfall(1)', y='VegCarbonStem1', ax=axes[0,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(1)', y='VegCarbonStem1', ax=axes[0,0], color='yellow',legend=False)
    axes[0,0].title.set_text('Black Spruce')
    
    axes[0,1].axhline(targets['VegCarbonStem3'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(0).1', y='VegCarbonStem3', ax=axes[0,1], legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='cfall(0).1', y='VegCarbonStem3', ax=axes[0,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(0).1', y='VegCarbonStem3', ax=axes[0,1], color='yellow',legend=False)
    axes[0,1].title.set_text('Shrub')

    
    axes[0,2].axhline(targets['VegCarbonRoot1'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(2)', y='VegCarbonRoot1', ax=axes[0,2], legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='cfall(0)', y='VegCarbonRoot1', ax=axes[0,2], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(0)', y='VegCarbonRoot1', ax=axes[0,2], color='yellow',legend=False)
    axes[0,2].title.set_text('Shrub')

    
    axes[1,0].axhline(targets['VegCarbonRoot3'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(0).3', y='VegCarbonRoot3', ax=axes[1,0], legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='cfall(0).3', y='VegCarbonRoot3', ax=axes[1,0], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(0).3', y='VegCarbonRoot3', ax=axes[1,0], color='yellow',legend=False)
    axes[1,0].title.set_text('sedge')

    
    axes[1,1].axhline(targets['VegCarbonRoot4'], color='grey', alpha=0.5)
    sns.scatterplot(data = results, x='cfall(0).4', y='VegCarbonRoot4', ax=axes[1,1], legend=False, alpha=0.3)
    sns.scatterplot(data = results.iloc[top], x='cfall(0).4', y='VegCarbonRoot4', ax=axes[1,1], color='red',legend=False)
    sns.scatterplot(data = results.iloc[first], x='cfall(0).4', y='VegCarbonRoot4', ax=axes[1,1], color='yellow',legend=False)
    axes[1,1].title.set_text('lichen')


results.sort_values(by='mean_rmse')[-15:].index


results.iloc[results['rmse'].idxmin()]


def spaghetti_match_plot(df_x,df_y,logy=False):
    ''' plots the spaghetti plot of modeled v.s. observed values 
        df_x: parameter dataframe
        df_y: model output dataframe
        logy: True enables the logplot option
    '''
    fig, ax=plt.subplots()
    #ax = df_y.transpose().plot(logy=logy,legend=False,alpha=0.5,figsize=(10,5))
    
    nrange=range(len(df_y.columns))
    df_x.plot(logy=logy,legend=True,style="o",color='red',xticks=nrange, rot=90, label="Targets", ax=ax);
    
    top=results.sort_values(by='rmse', ascending=False)[:10].index
    results[target_vars].iloc[results['rmse'].idxmin()].transpose().plot(logy=logy,legend=False,alpha=0.5,figsize=(10,5), color='yellow',ax=ax)
    #results[target_vars].transpose().plot(logy=logy,legend=False,alpha=0.5,figsize=(10,5), color='yellow',ax=ax)
    #results[target_vars].iloc[41].transpose().plot(logy=logy,legend=False,alpha=0.5,figsize=(10,5), color='yellow',ax=ax)
    results[target_vars].iloc[top].transpose().plot(logy=logy,legend=False,alpha=0.5,figsize=(10,5), color='red',ax=ax)
    
    df_x.plot(logy=logy,legend=False,style="o",color='red',xticks=nrange, rot=90,ax=ax)
    ax.set_xticklabels(df_y.columns,fontsize=12)
    #plt.ylim(10e-5, 2000)
    
target_df=pd.DataFrame(targets).reset_index()
target_df.columns=['variable', 'value']


if STEP==2:
    spaghetti_match_plot(target_df, results[target_vars], logy=True)


if STEP==3:
    spaghetti_match_plot(target_df, results[target_vars], logy=True)


for val in results[calib_params_flat].iloc[results['overall_accuracy'].idxmax()].values:
    print(f'- {val}')


corr = results[target_vars + calib_params_flat].corr()

corr= corr.drop(columns=calib_params_flat)
corr = corr.loc[calib_params_flat]


# Set up the matplotlib figure
f, ax = plt.subplots(figsize=(10, 10))

# Generate a custom diverging colormap
cmap = sns.diverging_palette(230, 20, as_cmap=True)

# Draw the heatmap with the mask and correct aspect ratio
sns.heatmap(corr, cmap=cmap, vmax=.3, center=0,annot=False,
            square=True, linewidths=.5, cbar_kws={"shrink": .5})


def minMax(x):
    return pd.Series(index=['min','max'],data=[x.min(),x.max()])


minmax=results[calib_params_flat].iloc[top].apply(minMax)


for column in minmax.columns:
    print('- Uniform({}, {})'.format(minmax[column]['min'], minmax[column]['max']))


targets


for index, row in minmax.iterrows():
    print(row)


results.loc[results['kdcrawc']>results['kdcsoma']].sort_values(by='mean_rmse')[-50:]


if STEP==4:
    spaghetti_match_plot(target_df, results[target_vars], logy=True)


results.sort_values(by='CarbonDeep', ascending=False).head(100)


results[(results['AvailableNitrogenSum']>4) & (results['CarbonDeep']<30000)]
#203
#225


targets


results.iloc[[203, 225, 438, 301]]


print(results.iloc[[144,63,400,495]]['micbnup'].min())
print(results.iloc[[144,63,400,495]]['micbnup'].max())


print(results.iloc[[144,63,400,495]]['kdcrawc'].min())
print(results.iloc[[144,63,400,495]]['kdcrawc'].max())


print(results.iloc[[144,63,400,495]]['kdcsoma'].min())
print(results.iloc[[144,63,400,495]]['kdcsoma'].max())


print(results.iloc[[144,63,400,495]]['kdcsompr'].min())
print(results.iloc[[144,63,400,495]]['kdcsompr'].max())


print(results.iloc[[144,63,400,495]]['kdcsomcr'].min())
print(results.iloc[[144,63,400,495]]['kdcsomcr'].max())


sns.scatterplot(data=results, x='kdcsompr', y='AvailableNitrogenSum')
plt.axhline(targets['AvailableNitrogenSum'], color='grey', alpha=0.5)
plt.xscale('log')
plt.ylim(0,30)


sns.scatterplot(data=results, x='kdcrawc', y='CarbonShallow')
plt.axhline(targets['CarbonShallow'], color='grey', alpha=0.5)


sns.scatterplot(data=results, x='kdcsompr', y='CarbonDeep')
plt.axhline(targets['CarbonDeep'], color='grey', alpha=0.5)
plt.xscale('log')


sns.scatterplot(data=results, x='kdcsompr', y='CarbonMineralSum')
plt.axhline(targets['CarbonMineralSum'], color='grey', alpha=0.5)


sns.histplot(data=results, x='kdcsomcr')
plt.xscale("log")


sns.scatterplot(data=results, x='kdcrawc', y='CarbonMineralSum')
plt.axhline(targets['CarbonMineralSum'], color='grey', alpha=0.5)


sns.scatterplot(data=results, x='micbnup', y='OrganicNitrogenSum')
plt.axhline(targets['OrganicNitrogenSum'], color='grey', alpha=0.5)


pd.melt(pd.DataFrame(targets))


pd.DataFrame(targets)


targets.index


import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
from scipy.stats import loguniform


from scipy.stats import loguniform

def generate_loguniform_sample(a, b, size=10):
    """
    Generate a random sample of size 'size' from a log uniform distribution for elements within the interval (a, b).
    
    Parameters:
        a (float): Lower bound of the interval.
        b (float): Upper bound of the interval.
        size (int): Number of elements in the sample (default is 10).
    
    Returns:
        numpy.ndarray: An array of size 'size' containing random samples from the log uniform distribution.
    """
    min_val = a
    max_val = b
    spread=b-a
    loguniform_samples = loguniform.rvs(min_val,max_val,size=size)
    return loguniform_samples

# Example usage:
a = 1e-15
b = 1e-12
sample = generate_loguniform_sample(a, b, size=500)
print("Generated Sample:", sample)




