#!/usr/bin/env python

import numpy as np



def pft_total(jdata):
    '''Sum across all PFT compartments, given a "PFT" block of json data'''
    return jdata["Leaf"] + jdata["Stem"] + jdata["Root"]

def ecosystem_total_veg_C(jdata):
    '''Add up across all PFTs in an ecosystem'''
    total_C = 0
    for pft in range(0,10):
        total_C += pft_total(jdata["PFT%i"%pft]["VegCarbon"])
    return total_C

def ecosystem_total_veg_C_vascular(jdata):
    '''BRITTLE INDEX!'''
    total_C = 0
    for pft in range(0,5):
        total_C += pft_total(jdata["PFT%i"%pft]["VegCarbon"])
    return total_C

def ecosystem_total_veg_C_nonvascular(jdata):
    '''BRITTLE INDEX!'''
    total_C = 0
    for pft in range(5,10):
        total_C += pft_total(jdata["PFT%i"%pft]["VegCarbon"])
    return total_C

def ecosystem_total_mossdeathc(jdata):
    total_mossdeathc = 0
    for pft in range(0,10):
        total_mossdeathc += jdata['PFT%i'%pft]['MossDeathC']
    return total_mossdeathc

def ecosystem_total_mossdeathc_vascular(jdata):
    total_mossdeathc = 0
    for pft in range(0,5):
        total_mossdeathc += jdata['PFT%i'%pft]['MossDeathC']
    return total_mossdeathc

def ecosystem_total_mossdeathc_nonvascular(jdata):
    total_mossdeathc = 0
    for pft in range(5,10):
        total_mossdeathc += jdata['PFT%i'%pft]['MossDeathC']
    return total_mossdeathc

    
############################
def ecosystem_total_veg_N(jdata):
    tN = 0
    for pft in range(0,10):
        tN += jdata["PFT%i"%pft]["NAll"]
    return tN    

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

def ecosystem_total_veg_Litterfall_N(jdata):
    t = 0
    for pft in range(0,10):
        t += jdata["PFT%i"%pft]["LitterfallNitrogenPFT"]
    return t


def ecosystem_total_veg_Mobile_N(jdata):
    t = 0
    for pft in range(0,10):
        t += jdata["PFT%i"%pft]["NMobil"]
    return t

    
def ecosystem_total_veg_Resorb_R(jdata):
    t = 0
    for pft in range(0,10):
        t += jdata["PFT%i"%pft]["NResorb"]
    return t


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

# def ecosystem_total_veg_N(jdata):
#     tN = 0
#     for pft in range(0,10):
#         tB += pft_total()

###################################

def ecosystem_total_NPP(jdata):
    '''Add up across all PFTs in an ecosystem'''
    total_NPP = 0
    for pft in range(0,10):
        total_NPP += jdata["PFT%i"%pft]["NPPAll"]
    return total_NPP

def ecosystem_total_NPP_vascular(jdata):
    '''BRITTLE INDEX!'''
    total_NPP = 0
    for pft in range(0,5):
        total_NPP += jdata["PFT%i"%pft]["NPPAll"]
    return total_NPP

def ecosystem_total_NPP_nonvascular(jdata):
    '''BRITTLE INDEX!'''
    total_NPP = 0
    for pft in range(5,10):
        total_NPP += jdata["PFT%i"%pft]["NPPAll"]
    return total_NPP

def ecosystem_total_Litterfall_C(jdata):
    '''Add up across all PFTs in an ecosystem'''
    total_LFC = 0
    for pft in range(0,10):
        total_LFC += jdata["PFT%i"%pft]["LitterfallCarbonAll"]
    return total_LFC

def ecosystem_total_Litterfall_C_vascular(jdata):
    '''BRITTLE INDEX!'''
    total_LFC = 0
    for pft in range(0,5):
        total_LFC += jdata["PFT%i"%pft]["LitterfallCarbonAll"]
    return total_LFC

def ecosystem_total_Litterfall_C_nonvascular(jdata):
    '''BRITTLE INDEX!'''
    total_LFC = 0
    for pft in range(5,10):
        total_LFC += jdata["PFT%i"%pft]["LitterfallCarbonAll"]
    return total_LFC


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
            deltaN = ecosystem_total_veg_N(jd) - ecosystem_total_veg_N(pjd)
            
        ecosystem_total_veg_N(jd),
        return  "{:<4} {:>6} {:>10.4f}    {:>10.3f} {:>10.3f} {:>10.3f} {:>10.3f} {:>10.3f}\n".format(
                idx,
                jd["Year"],
                
                deltaN - (ecosystem_total_veg_TotNitrogenUptake(jd) - ecosystem_total_veg_Litterfall_N(jd)),

                deltaN,
                ecosystem_total_veg_TotNitrogenUptake(jd),
                ecosystem_total_veg_Litterfall_N(jd),
                ecosystem_total_veg_Mobile_N(jd),
                ecosystem_total_veg_Resorb_R(jd),
                


#                 ecosystem_total_veg_StructN(jd),
#                 ecosystem_total_StNitrogenUptake(jd),
#                 ecosystem_total_InNitrogenUptake(jd),
#                 ecosystem_total_LuxNitrogenUptake(jd),
#                 ecosystem_total_TotNitrogenUptake(jd),
#                 ecosystem_total_LitterfallNitrogenPFT(jd),
#                 ecosystem_total_LitterfallNitrogen(jd),
                # nuptake - litterfall?
                #delta vegN: (sum Veg N across (root, stem, leaves)) = NUptake - litterfallN - veg fire emission - deadN
        )


def Check_N_cycle_soil_balance(idx, header=False, jd=None, pjd=None):
    pass


def Check_C_cycle_soil_balance(idx, header=False, jd=None, pjd=None):
    if header:
        return '{:<4} {:>4} {:>8} {:>10} {:>10}     {:>10} {:>10} {:>10} {:>10} {:>10}\n'.format(
               'idx', 'yr', 'err', 'deltaC', 'lf+mdc-rh', 'sum soil C', 'ltrfal', 'mossdeathc', 'RH', 'checksum'
        )
    else:
        delta_C = np.nan
        if pjd != None:
            delta_C = ecosystem_sum_soilC(jd) - ecosystem_sum_soilC(pjd)

        return "{:<4} {:>4} {:>8.2f} {:>10.2f} {:>10.2f}     {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}\n".format(
                idx,
                jd["Year"],
                delta_C - (ecosystem_total_Litterfall_C(jd) + ecosystem_total_mossdeathc(jd) - jd["RH"]),
                delta_C,
                ecosystem_total_Litterfall_C(jd) + ecosystem_total_mossdeathc(jd) - jd["RH"],
                ecosystem_sum_soilC(jd),
                ecosystem_total_Litterfall_C(jd),
                ecosystem_total_mossdeathc(jd),
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
            deltaC = ecosystem_sum_soilC(jd) - ecosystem_sum_soilC(jd)


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
                ecosystem_total_Litterfall_C(jd) + jd['MossdeathCarbon'],
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
            deltaC = ecosystem_total_veg_C(jd) - ecosystem_total_veg_C(pjd)


        # FIll in the table with data...
        return '{:<4d} {:>4} {:>10.3f} {:>10.3f} {:>15.3f}     {:>10.3f} {:>15.3f} {:>15.3f} {:>15.3f}\n'.format(
                idx,
                jd['Year'],
                (ecosystem_total_NPP(jd) - ecosystem_total_Litterfall_C(jd) - ecosystem_total_mossdeathc(jd)) - deltaC,
                deltaC,
                ecosystem_total_NPP(jd) - ecosystem_total_Litterfall_C(jd) - ecosystem_total_mossdeathc(jd),

                ecosystem_total_mossdeathc(jd),
                ecosystem_total_veg_C(jd), 
                ecosystem_total_NPP(jd),
                ecosystem_total_Litterfall_C(jd),
            )

def Check_C_cycle_veg_vascular_balance(idx, header=False, jd=None, pjd=None):
    '''Should duplicate Vegetation_Bgc::deltastate()'''
    if header:
        return '{:<4} {:>4} {:>10} {:>10} {:>15}     {:>10} {:>15} {:>15} {:>15}\n'.format(
               'idx', 'yr', 'err', 'deltaC', 'NPP-LFallC-mdc', 'mdc', 'VegC', 'NPP', 'LFallC' )
    else:
        deltaC = np.nan

        # If we are beyond the first year, load the previous year
        if pjd != None:
            deltaC = ecosystem_total_veg_C_vascular(jd) - ecosystem_total_veg_C_vascular(pjd)

        # FIll in the table with data...
        return '{:<4d} {:>4} {:>10.3f} {:>10.3f} {:>15.3f}     {:>10.3f} {:>15.3f} {:>15.3f} {:>15.3f}\n'.format(
                idx,
                jd['Year'],
                (ecosystem_total_NPP_vascular(jd) - ecosystem_total_Litterfall_C_vascular(jd) - ecosystem_total_mossdeathc_vascular(jd)) - deltaC,
                deltaC,
                ecosystem_total_NPP_vascular(jd) - ecosystem_total_Litterfall_C_vascular(jd) - ecosystem_total_mossdeathc_vascular(jd),

                ecosystem_total_mossdeathc_vascular(jd),
                ecosystem_total_veg_C_vascular(jd), 
                ecosystem_total_NPP_vascular(jd),
                ecosystem_total_Litterfall_C_vascular(jd),
            )



def Check_C_cycle_veg_nonvascular_balance(idx, header=False, jd=None, pjd=None):
    '''Should duplicate Vegetation_Bgc::deltastate()'''
    if header:
        return '{:<4} {:>4} {:>10} {:>10} {:>15}     {:>10} {:>15} {:>15} {:>15}\n'.format(
               'idx', 'yr', 'err', 'deltaC', 'NPP-LFallC-mdc', 'mdc', 'VegC', 'NPP', 'LFallC' )
    else:
        deltaC = np.nan

        # If we are beyond the first year, load the previous year
        if pjd != None:
            deltaC = ecosystem_total_veg_C_nonvascular(jd) - ecosystem_total_veg_C_nonvascular(pjd)

        # FIll in the table with data...
        return '{:<4d} {:>4} {:>10.3f} {:>10.3f} {:>15.3f}     {:>10.3f} {:>15.3f} {:>15.3f} {:>15.3f}\n'.format(
                idx,
                jd['Year'],
                (ecosystem_total_NPP_nonvascular(jd) - ecosystem_total_Litterfall_C_nonvascular(jd) - ecosystem_total_mossdeathc_nonvascular(jd)) - deltaC,
                deltaC,
                ecosystem_total_NPP_nonvascular(jd) - ecosystem_total_Litterfall_C_nonvascular(jd) - ecosystem_total_mossdeathc_nonvascular(jd),

                ecosystem_total_mossdeathc_nonvascular(jd),
                ecosystem_total_veg_C_nonvascular(jd), 
                ecosystem_total_NPP_nonvascular(jd),
                ecosystem_total_Litterfall_C_nonvascular(jd),
            )

if __name__ == '__main__':
    pass
