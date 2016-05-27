#!/usr/bin/env python

import os
import glob
import json
import numpy as np

def run_tests(test_list, **kwargs):

    # write to file (w2f)
    if 'w2f' in kwargs:
        outfile = kwargs['w2f']
    else:
        outfile = None

    if outfile:
        folder, fname = os.path.split(outfile)
        if folder != '':

            try:
                os.makedirs(folder) # keyword argument 'exists_ok=True' is for python 3.4+
            except OSError:
                if not os.path.isdir(folder):
                    raise

        print "clearing output file: ", outfile
        with open(outfile, 'w') as f:
            f.write("")


    for t in test_list:
        title =  "------  %s  ------" % t
        data = compile_table_by_year(t)

        # print to console (p2c)
        if 'p2c' in kwargs and kwargs['p2c'] == True:
            print title
            print data
        if outfile != None:
            with open(outfile, 'a') as f:
                print "appending to file: ", outfile
                f.write(title); f.write("\n")
                f.write(data)


def compile_table_by_year(test_case, **kwargs):

    if 'fileslice' in kwargs:
        slice_string = kwargs['fileslice']
        # parse string into slice object
        # https://stackoverflow.com/questions/680826/python-create-slice-object-from-string/681949#681949
        custom_slice = slice(*map(lambda x: int(x.strip()) if x.strip() else None, slice_string.split(':')))
    else:
        custom_slice = slice(None,None,None)



    # map 'test case' strings to various test and 
    # reporting functions we have written in the module.
    function_dict = {
        'N_soil_balance':             Check_N_cycle_soil_balance,
        'N_veg_balance':              Check_N_cycle_veg_balance,
        'C_soil_balance':             Check_C_cycle_soil_balance,
        'C_veg_balance':              Check_C_cycle_veg_balance,
        'C_veg_vascular_balance':     Check_C_cycle_veg_vascular_balance,
        'C_veg_nonvascular_balance':  Check_C_cycle_veg_nonvascular_balance,
        'report_soil_C':              Report_Soil_C
    }

    check_func = function_dict[test_case]

    jfiles = glob.glob("/tmp/dvmdostem/calibration/monthly/*.json")

    print "Custom file slice:", custom_slice
    jfiles = jfiles[custom_slice]
    header = check_func(0, header=True)

    table_data = ""
    for idx, jfile in enumerate(jfiles):
        with open(jfile, 'r') as f:
            jdata = json.load(f)

        prev_jdata = None
        if idx > 0:
            with open(jfiles[idx-1], 'r') as prev_jf:
                prev_jdata = json.load(prev_jf)

        row = check_func(idx, jd=jdata, pjd=prev_jdata, header=False)

        table_data = table_data + row

    full_report = header + table_data

    return full_report

def eco_total(key, jdata, **kwargs):

  if 'pftlist' in kwargs:
    pftlist = kwargs['pftlist']
  else:
    pftlist = range(0,10)

  total = 0
  for pft in ['PFT%i'%i for i in pftlist]:
    if ( type(jdata[pft][key]) == dict ): # sniff out compartment variables
      if len(jdata[pft][key]) == 3:
        total += jdata[pft][key]["Leaf"] + jdata[pft][key]["Stem"] + jdata[pft][key]["Root"]
    else:
      total += jdata[pft][key]
  return total

def pft_total(jdata):
    '''Sum across all PFT compartments, given a "PFT" block of json data'''
    return jdata["Leaf"] + jdata["Stem"] + jdata["Root"]

def  ecosystem_total_veg_TotNitrogenUptake(jdata):
    t = 0
    for pft in range(0,10):
        t += jdata["PFT%i"%pft]["TotNitrogenUptake"]
    return t

# def ecosystem_total_veg_LitterfallNitrogenPFT(jdata):
#     t = 0
#     for pft in range(0,10):
#         t += jdata["PFT%i"%pft]["LitterfallNitrogenPFT"]
#     return t

# def ecosystem_total_StNitrogenUptake(jdata):
#     t = 0
#     for pft in range(0,10):
#         t += jdata["PFT%i"%pft]["StNitrogenUptake"]
#     return t

# def ecosystem_total_InNitrogenUptake(jdata):
#     t = 0
#     for pft in range(0,10):
#         t += jdata["PFT%i"%pft]["InNitrogenUptake"]
#     return t

# def ecosystem_total_LuxNitrogenUptake(jdata):
#     t = 0
#     for pft in range(0,10):
#         t += jdata["PFT%i"%pft]["LuxNitrogenUptake"]
#     return t

# def ecosystem_total_veg_StructN(jdata):
#     tN = 0
#     for pft in range(0,10):
#         tN += pft_total(jdata["PFT%i"%pft]["VegStructuralNitrogen"])
#     return tN



def ecosystem_sum_soilC(jdata):
    total_soil_C = 0
    total_soil_C += jdata["CarbonMineralSum"]
    total_soil_C += jdata["CarbonDeep"]
    total_soil_C += jdata["CarbonShallow"]
    total_soil_C += jdata["DeadMossCarbon"]

    return total_soil_C

#delta vegN: (sum Veg N across (root, stem, leaves)) = NUptake - litterfallC - veg fire emission - deadN

def Check_N_cycle_veg_balance(idx, header=False, jd=None, pjd=None):
    '''Checking....?'''
    if header:
        return "{:<4} {:>6} {:>10}    {:>10} {:>10} {:>10} {:>10} {:>10}\n".format(
                "idx", "yr", "err", "deltaN", "totalNuptake", "LitterfallN", "Nmobile", "Nresorb"
        )
    else:
        deltaN = np.nan
        if pjd != None:
            deltaN = eco_total("NAll", jd)  - eco_total("NAll", pjd) 
            
        return  "{:<4} {:>6} {:>10.4f}    {:>10.3f} {:>10.3f} {:>10.3f} {:>10.3f} {:>10.3f}\n".format(
                idx,
                jd["Year"],
                
                deltaN - (ecosystem_total_veg_TotNitrogenUptake(jd) - eco_total("LitterfallNitrogenPFT", jd) ),

                deltaN,
                ecosystem_total_veg_TotNitrogenUptake(jd),
                eco_total("LitterfallNitrogenPFT", jd) ,
                eco_total("NMobil", jd) ,
                eco_total("NResorb", jd) ,
                
        #delta vegN: (sum Veg N across (root, stem, leaves)) = NUptake - litterfallN - veg fire emission - deadN
        )


def Check_N_cycle_soil_balance(idx, header=False, jd=None, pjd=None):
    pass


def Check_C_cycle_soil_balance(idx, header=False, jd=None, pjd=None):
    if header:
        return '{:<4} {:>2} {:>4} {:>8} {:>10} {:>10}     {:>10} {:>10} {:>10} {:>10} {:>10}\n'.format(
               'idx', 'm', 'yr', 'err', 'deltaC', 'lf+mdc-rh', 'sum soil C', 'ltrfal', 'mossdeathc', 'RH', 'checksum'
        )
    else:
        delta_C = np.nan
        if pjd != None:
            delta_C = ecosystem_sum_soilC(jd) - ecosystem_sum_soilC(pjd)

        return "{:<4} {:>2} {:>4} {:>8.2f} {:>10.2f} {:>10.2f}     {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}\n".format(
                idx,
                jd["Month"],
                jd["Year"],
                delta_C - (eco_total("LitterfallCarbonAll", jd)  + eco_total("MossDeathC", jd) - jd["RH"]),
                delta_C,
                eco_total("LitterfallCarbonAll", jd)  + eco_total("MossDeathC", jd) - jd["RH"],
                ecosystem_sum_soilC(jd),
                eco_total("LitterfallCarbonAll", jd) ,
                eco_total("MossDeathC", jd),
                jd['RH'], 
                (jd['RHsomcr']+jd['RHsompr']+jd['RHsoma']+jd['RHraw']+jd['RHmossc']+jd['RHwdeb']),
            )


def Report_Soil_C(idx, header=False, jd=None, pjd=None):
    '''Create a table/report for Soil Carbon'''
    if header:
        return '{:<4} {:>4} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9}\n'.format(
               'idx', 'yr', 'RHtot', 'RHrawc', 'RHsomac', 'RHsomprc','RHsomcrc','RHmossc','RHwdeb','Lfc+dmsc','rawc','soma','sompr','somcr','dmossc'
            )
    else:
        deltaC = np.nan

        # If we are beyond the first year, load the previous year
        if pjd != None:
            deltaC = ecosystem_sum_soilC(jd) - ecosystem_sum_soilC(pjd)


        # FIll in the table with data...
        return "{:<4} {:>4} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f}\n".format(
                idx,
                jd['Year'],
                jd['RH'],
                jd['RHraw'],
                jd['RHsoma'],
                jd['RHsompr'],
                jd['RHsomcr'],
                jd['RHmossc'],
                jd['RHwdeb'],
                eco_total("LitterfallCarbonAll", jd)  + jd['MossdeathCarbon'],
                jd['RawCSum'],
                jd['SomaSum'],
                jd['SomprSum'],
                jd['SomcrSum'],
                jd['DeadMossCarbon'],

            )




def Check_C_cycle_veg_balance(idx, header=False, jd=None, pjd=None):
    '''Should duplicate Vegetation_Bgc::deltastate()'''
    if header:
        return '{:<4} {:>4} {:>10} {:>10} {:>15}     {:>10} {:>15} {:>15} {:>15}\n'.format(
               'idx', 'yr', 'err', 'deltaC', 'NPP-LFallC-mdc', 'mdc', 'VegC', 'NPP', 'LFallC' )
    else:
        deltaC = np.nan

        # If we are beyond the first year, load the previous year
        if pjd != None:
            deltaC = eco_total("VegCarbon", jd) - eco_total("VegCarbon", pjd)

        # FIll in the table with data...
        return '{:<4d} {:>4} {:>10.3f} {:>10.3f} {:>15.3f}     {:>10.3f} {:>15.3f} {:>15.3f} {:>15.3f}\n'.format(
                idx,
                jd['Year'],
                (eco_total("NPPAll", jd)  - eco_total("LitterfallCarbonAll", jd)  - eco_total("MossDeathC", jd)) - deltaC,
                deltaC,
                eco_total("NPPAll", jd)  - eco_total("LitterfallCarbonAll", jd)  - eco_total("MossDeathC", jd),

                eco_total("MossDeathC", jd),
                eco_total("VegCarbon", jd), 
                eco_total("NPPAll", jd) ,
                eco_total("LitterfallCarbonAll", jd) ,
            )

def Check_C_cycle_veg_vascular_balance(idx, header=False, jd=None, pjd=None):
    '''Should duplicate Vegetation_Bgc::deltastate()'''

    # vascular PFT list (CMT05)
    pl = [0,1,2,3,4]

    if header:
        return '{:<4} {:>4} {:>10} {:>10} {:>15}     {:>10} {:>15} {:>15} {:>15}\n'.format(
               'idx', 'yr', 'err', 'deltaC', 'NPP-LFallC-mdc', 'mdc', 'VegC', 'NPP', 'LFallC' )
    else:
        deltaC = np.nan

        # If we are beyond the first year, load the previous year
        if pjd != None:
            deltaC = eco_total("VegCarbon", jd, pftlist=pl) - eco_total("VegCarbon", pjd, pftlist=pl)

        # FIll in the table with data...
        return '{:<4d} {:>4} {:>10.3f} {:>10.3f} {:>15.3f}     {:>10.3f} {:>15.3f} {:>15.3f} {:>15.3f}\n'.format(
                idx,
                jd['Year'],
                (eco_total("NPPAll", jd, pftlist=pl)  - eco_total("LitterfallCarbonAll", jd, pftlist=pl)  - eco_total("MossDeathC",jd,pftlist=pl)) - deltaC,
                deltaC,
                eco_total("NPPAll", jd, pftlist=pl)  - eco_total("LitterfallCarbonAll", jd, pftlist=pl)  - eco_total("MossDeathC",jd,pftlist=pl),

                eco_total("MossDeathC",jd, pftlist=pl),
                eco_total("VegCarbon", jd, pftlist=pl), 
                eco_total("NPPAll", jd, pftlist=pl) ,
                eco_total("LitterfallCarbonAll", jd, pftlist=pl) ,
            )



def Check_C_cycle_veg_nonvascular_balance(idx, header=False, jd=None, pjd=None):
    '''Should duplicate Vegetation_Bgc::deltastate()'''

    # non-vascular PFT list (CMT05)
    pl = [5,6,7]

    if header:
        return '{:<4} {:>4} {:>10} {:>10} {:>15}     {:>10} {:>15} {:>15} {:>15}\n'.format(
               'idx', 'yr', 'err', 'deltaC', 'NPP-LFallC-mdc', 'mdc', 'VegC', 'NPP', 'LFallC' )
    else:
        deltaC = np.nan

        # If we are beyond the first year, load the previous year
        if pjd != None:
            deltaC = eco_total("VegCarbon", jd, pftlist=pl) - eco_total("VegCarbon", pjd, pftlist=pl)

        # FIll in the table with data...
        return '{:<4d} {:>4} {:>10.3f} {:>10.3f} {:>15.3f}     {:>10.3f} {:>15.3f} {:>15.3f} {:>15.3f}\n'.format(
                idx,
                jd['Year'],
                (eco_total("NPPAll", jd, pftlist=pl)  - eco_total("LitterfallCarbonAll", jd, pftlist=pl)  - eco_total("MossDeathC", jd, pftlist=pl)) - deltaC,
                deltaC,
                eco_total("NPPAll", jd, pftlist=pl)  - eco_total("LitterfallCarbonAll", jd, pftlist=pl)  - eco_total("MossDeathC", jd, pftlist=pl),

                eco_total("MossDeathC", jd, pftlist=pl),
                eco_total("VegCarbon", jd, pftlist=pl), 
                eco_total("NPPAll", jd, pftlist=pl) ,
                eco_total("LitterfallCarbonAll", jd, pftlist=pl) ,
            )

if __name__ == '__main__':
    pass
