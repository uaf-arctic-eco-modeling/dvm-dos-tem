#!/usr/bin/env python

import json
import glob

#import textwrap
#import numpy as np


''' 
Example usage:

    import caljsonexplorer as cje


    filelist = glob.glob("/tmp/dvmdostem/calibration/monthly/*.json")

    cje.close_soil_C_cycle(filelist, report_level='fail')
    cje.close_soil_N_cycle(filelist, report_level='fail')
    cje.close_veg_C_cycle(filelist, report_level='fail')
    cje.close_veg_N_cycle(filelist, report_level='all')
    
'''



def jdata_generator(filenames):
    '''A generator function yielding a json data object from each file.'''

    for file in filenames:
        #print "In generator function for file: ", file
        with open(file, 'r') as f:
            data = json.load(f)
        yield data
        # could wrap in try/catch and return empty json
        # if there is an exception - would allow for analyzing
        # series of json files where one for more of the files
        # might have an nan.


def eco_total(key, alljsondata):
    '''A generator function yielding an ecosystem total across PFTs for a variable.'''

    total = 0
    for timestep in alljsondata:
        for pft in ['PFT%i'%i for i in range(0,10)]:
            #print "individual value: %s" % timestep[pft][key]
            total += timestep[pft][key]

        #print "ecosystem ==total=>", total
        yield total

            



if __name__ == '__main__':

    filelist = glob.glob("/tmp/dvmdostem/calibration/monthly/*.json")
    print(len(filelist))


    # data is an iterable thing, like a list, so can be passed
    # to functions expecting lists (or other iterable sequences)
    data = jdata_generator(filelist)
    
    # the eco_total function will iterate over all the json data
    # objects (data) and for each item in data it will find the
    # ecosystem total across all PFTs for the give key
    for t in eco_total('PARAbsorb', data):
        print("ecosystem PARAbsorb: ", t)
    

    print("=======> el fin.")




# def close_vegC(idx, data, prevd):
    

#     deltaC = np.nan
#     if prevd != None:
#         deltaC = eco_total_veg_C(data) - eco_total_veg_C(prevd)

#     err = (eco_total_NPP(data) - eco_total_LitterfallC(jd) - eco_total_mossdeathc(jd)) - deltaC
    
#     # np.allclose(0, 0.0000001) ==> False
#     # np.allclose(0, 0.00000001) ==> True
#     if np.allclose(err, 0.0):
#         pass # test ok, err is small, cycle closes for idx
#     else:
#         pass # test fails, err is too big...



