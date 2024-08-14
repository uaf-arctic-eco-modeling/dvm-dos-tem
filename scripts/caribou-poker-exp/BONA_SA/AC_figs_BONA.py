#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt


nppvegc=pd.read_csv('/work/mads_calibration/out-param-20231030-bona-npp-vegc-understory.csv', header=None,
                    names=['NPPAll1', 'NPPAll2', 'NPPAll3', 'NPPAll4', 'NPPAll5','VegCarbonLeaf1', 'VegCarbonStem1', 'VegCarbonRoot1', 
                               'VegCarbonLeaf2', 'VegCarbonStem2', 'VegCarbonRoot2',
                               'VegCarbonLeaf3', 'VegCarbonStem3', 'VegCarbonRoot3',
                               'VegCarbonLeaf4', 
                               'VegCarbonLeaf5', 'VegCarbonStem5', 'VegCarbonRoot5'])


nppvegc


nppvegc_params=pd.read_csv('/work/mads_calibration/param-20231030-bona-npp-vegc-understory.csv', header=None,
                    names=['krb(0)',#'krb(0).1','krb(0).2','krb(0).3','krb(0).4',
                           'krb(1)',#'krb(1).1','krb(1).2','krb(1).4',
                           'krb(2)',#'krb(2).1','krb(2).2','krb(2).4',
                           'cfall(0)',#'cfall(0).1','cfall(0).2','cfall(0).3','cfall(0).4',
                           'cfall(1)',#'cfall(1).1','cfall(1).2','cfall(1).4',
                           'cfall(2)'])#,'cfall(2).1','cfall(2).2','cfall(2).4'])


nppvegc_params=pd.read_csv('/work/mads_calibration/param-20231030-bona-npp-vegc-understory.csv', header=None,
                    names=['krb(0)','krb(0).1','krb(0).4',
                           'krb(1)','krb(1).1','krb(1).4',
                           'krb(2)','krb(2).1','krb(2).4',
                           'cfall(0)','cfall(0).1','cfall(0).3',
                           'cfall(1)','cfall(1).1',
                           'cfall(2)','cfall(2).1'])


targets=nppvegc.iloc[-1]
nppvegc=nppvegc.iloc[:-1]


nppvegc[['NPPAll5', 'VegCarbonLeaf5', 'VegCarbonStem5', 'VegCarbonRoot5']]


nppvegc[['NPPAll3', 'VegCarbonLeaf4']]


targets


#0, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25


#nppvegc.T.plot(legend=False)
sns.lineplot(nppvegc.iloc[3].T, legend=False, alpha=0.6)
#sns.lineplot(nppvegc.iloc[[4,6,8]].T, legend=False, alpha=0.6)
sns.scatterplot(targets.T, color='red')
plt.yscale('log')
plt.xticks(rotation=90)
plt.ylim(0.01,1e5)
plt.ylabel('value')
plt.title('BONA Birch Calibration')


#last 15
#NPP 5 good
#NPP 2 too high
#NPP 3 range 7 (low)
#NPP 4 range 1 (high), 6 good
#NPP 5 0 good match, 5 (low)
#VegCarbonLeaf1 range good, 0 good match, 1 good match
#VegCarbonStem1 [-4,-5] range good
#VegCarbonRoot1 9 good
#VegCarbonLeaf2 [-4,-5] range good, 4
#VegCarbonStem2 range from -6 slightly low
#VegCarbonRoot2 range from -6 good
#VegCarbonLeaf3 [-4,-5] range good -6 good, 4 good, 5 good, 6 good
#VeSCarbonStem3 7 good
#VegCarbonRoot3 [-5, -6] range good, 4 good
#VegCarbonLeaf4 -6 good, 0 good, 4 good
#VegCarbonLeaf5 0, 3 good
#VegCarbonStem5 8, 9 good match
#VegCarbonRoot5 5 good match

#8 really good match overall


nppvegc_params


for mini, maxi in zip(nppvegc_params.iloc[[1]].min(), nppvegc_params.iloc[[1]].max()):
    print('{},{}'.format('- Uniform('+str(mini), str(maxi)+')'))


for val in nppvegc_params.iloc[[1]].min():
    print('- {}'.format(val))


nppvegc_params.iloc[[0,3,4,6,8]]




