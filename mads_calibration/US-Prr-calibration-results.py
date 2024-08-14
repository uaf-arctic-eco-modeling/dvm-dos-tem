#!/usr/bin/env python
# coding: utf-8

import utils
import pandas as pd


final_results = utils.get_error('',['STEP3-US-Prr-R-VEGC-VEGN-AM.finalresults'])


opt_params = utils.get_optimal_sets_of_params('STEP3-US-Prr-R-VEGC-VEGN-AM.finalresults')
y_kmeans, centers = utils.get_err_clusters(final_results)


centers


opt_params.keys()


keys=['nmax0', 'nmax1', 'nmax2', 'nmax3', 'nmax4']
utils.plot_stacked_histograms({key: opt_params[key] for key in keys},centers,y_kmeans)


keys=['krb00', 'krb01', 'krb02', 'krb03', 'krb04']
utils.plot_stacked_histograms({key: opt_params[key] for key in keys},centers,y_kmeans)


keys=['krb10', 'krb12', 'krb20', 'krb22', 'krb23']
utils.plot_stacked_histograms({key: opt_params[key] for key in keys},centers,y_kmeans)


keys=['cfall00', 'cfall01', 'cfall02', 'cfall03', 'cfall04']
utils.plot_stacked_histograms({key: opt_params[key] for key in keys},centers,y_kmeans)


keys=['cfall10', 'cfall12', 'cfall20', 'cfall22', 'cfall23']
utils.plot_stacked_histograms({key: opt_params[key] for key in keys},centers,y_kmeans)


keys=['nfall00', 'nfall01', 'nfall02', 'nfall03', 'nfall04']
utils.plot_stacked_histograms({key: opt_params[key] for key in keys},centers,y_kmeans)


keys=['nfall10', 'nfall12', 'nfall20', 'nfall22', 'nfall23']
utils.plot_stacked_histograms({key: opt_params[key] for key in keys},centers,y_kmeans)


target_vars = ['NPPAll1', 'NPPAll2', 'NPPAll3', 'NPPAll4', 'NPPAll5',
                   'VegCarbonLeaf1', 'VegCarbonStem1', 'VegCarbonRoot1', 'VegCarbonLeaf2', 'VegCarbonLeaf3',
                   'VegCarbonStem3', 'VegCarbonRoot3', 'VegCarbonLeaf4',
                   'VegCarbonRoot4', 'VegCarbonLeaf5',
                   'VegNitrogenLeaf1', 'VegNitrogenStem1', 'VegNitrogenRoot1', 'VegNitrogenLeaf2', 'VegNitrogenLeaf3',
                   'VegNitrogenStem3', 'VegNitrogenRoot3', 'VegNitrogenLeaf4',
                   'VegNitrogenRoot4', 'VegNitrogenLeaf5']
params = ['NPPAll1', 'NPPAll2', 'NPPAll3', 'NPPAll4', 'NPPAll5',
                   'VegCarbonLeaf1', 'VegCarbonStem1', 'VegCarbonRoot1', 'VegCarbonLeaf2', 'VegCarbonLeaf3',
                   'VegCarbonStem3', 'VegCarbonRoot3', 'VegCarbonLeaf4',
                   'VegCarbonRoot4', 'VegCarbonLeaf5',
                   'VegNitrogenLeaf1', 'VegNitrogenStem1', 'VegNitrogenRoot1', 'VegNitrogenLeaf2', 'VegNitrogenLeaf3',
                   'VegNitrogenStem3', 'VegNitrogenRoot3', 'VegNitrogenLeaf4',
                   'VegNitrogenRoot4', 'VegNitrogenLeaf5']
model_csv = utils.read_all_csv('', ['out-20230626-step3.csv'], 'model', target_vars)
#param_csv = utils.read_all_csv('', ['param-20230619-step3..csv'], 'model', params)


model_csv


def spaghetti_match_plot(df_x,df_y,logy=True):
    ''' plots the spaghetti plot of modeled v.s. observed values 
        df_x: parameter dataframe
        df_y: model output dataframe
        logy: True enables the logplot option
    '''
    ax = df_y.transpose().plot(logy=logy,legend=False,alpha=0.5,figsize=(10,5))
    
    nrange=range(len(df_y.columns))
    df_x.plot(logy=logy,legend=True,style="o",color='red',xticks=nrange, rot=90, label="Targets", ax=ax);
    df_x.plot(logy=logy,legend=False,style="o",color='red',xticks=nrange, rot=90,ax=ax)
    ax.set_xticklabels(df_y.columns,fontsize=12)


pd.DataFrame(model_csv.iloc[-1])


pd.DataFrame(model_csv.iloc[2])


model_csv


spaghetti_match_plot(pd.DataFrame(model_csv.iloc[-1]), model_csv[-2:-1])


param_csv




