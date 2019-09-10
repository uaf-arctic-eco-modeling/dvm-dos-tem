#!/usr/bin/env python

# T Carman May 2019


import os
import glob
import sys
import numpy as np

sys.path.insert(0,"/home/vagrant/dvm-dos-tem/")
import scripts.output_utils as ou
from  calibration.calibration_targets import calibration_targets as ct

ctv2 = {'CMT{:02d}'.format(v['cmtnumber']):v for k, v in ct.iteritems()}


def qcal_rank(truth, value):
  ''' Deviation from truth, expressed as percent, with sign.''' 
  return(value/(truth*1.0)-1.0 )

def qcal_rank2(truth, value):
  '''Deviation from truth, expressed as distance squared (no sign).'''
  return (truth - value)**2

#from IPython import embed; embed()


data, i = ou.get_last_n_eq("DEEPC", 'yearly', '/home/vagrant/runmanager_rungroups/tem_00000000000/out/00000000000/')
qcal_rank(ctv2['CMT04']['CarbonDeep'], data[:,0,0].mean())

data, i = ou.get_last_n_eq("SHLWC", 'yearly', '/home/vagrant/runmanager_rungroups/tem_00000000000/out/00000000000/')
qcal_rank(ctv2['CMT04']['CarbonShallow'], data[:,0,0].mean())


mm = [
('GPPAllIgnoringNitrogen','INGPP'),
('NPPAllIgnoringNitrogen','INNPP'),
('NPPAll','NPP'),
#('Nuptake','NUPTAKE'), # ??? There are snuptake, lnuptake and innuptake... and TotNitrogentUptake is the sum of sn and ln...
('VegCarbon','VEGC'),
('VegStructuralNitrogen','VEGN'),
('MossDeathC','MOSSDEATHC'),
('CarbonShallow','SHLWC'),
('CarbonDeep','DEEPC'),
('CarbonMineralSum','MINEC'),
('OrganicNitrogenSum','ORGN'),
('AvailableNitrogenSum','AVLN'),
]

'''
hs = '{:>32s}'.format("calib. variable")
for i in ctv2['CMT04']['PFTNames']:
  hs += ('{:>15}'.format(i))
print hs

# data_path = '/home/vagrant/TESTSAMPLE/output/'
# data, i = ou.get_last_n_eq("SHLWC", 'yearly', data_path)

for ctname, ofname in mm:
  data, dims = ou.get_last_n_eq(ofname, 'yearly', '/home/vagrant/runmanager_rungroups/tem_00000000000/out/00000000000/')
  if any('pft' in dim for dim in dims):
    ds = ''
    if any('pftpart' in dim for dim in dims):
      clu = {0:'Leaf', 1:'Stem', 2:'Root'}
      for c in range(0,3):
        ds += '{:>32s}'.format('{}({})'.format(ctname, clu[c]))
        for pft in range(0,10):
          if ctv2['CMT04']['VegCarbon'][clu[c]][pft] == 0.0: # <-- bad! testing equality of floats! 
            ds += '{:>15}'.format('--')
          else:
            ds += '{:>15.2f}'.format(qcal_rank(ctv2['CMT04'][ctname][clu[c]][pft], data[:,c,pft,0,0].mean()))
        print ds
        ds = ''
    else:
      ds += '{:>15.2f}'.format(qcal_rank(ctv2['CMT04'][ctname][pft], data[:,pft,0,0].mean()))
    print ds
  else:
    print '{} {}'.format(ctname, qcal_rank(ctv2['CMT04'][ctname], data[:,0,0].mean()))
'''


'''
for ctname, ofname in mm:
  data, dims = ou.get_last_n_eq(ofname, 'yearly', '/home/vagrant/runmanager_rungroups/tem_00000000000/out/00000000000/')
  if any('pft' in dim for dim in dims):
    for pft in range(0,10):
      # if pft == 9 and ctname == 'NPPAllIgnoringNitrogen':
      #   from IPython import embed; embed()
      if ctv2['CMT04']['PFTNames'][pft].lower() in 'none,misc,misc.,pft0,pft1,pft2,pft3,pft4,pft5,pft6,pft7,pft8,pft9'.split(","):
        pass # This PFT is not used...
      else:
        if any('pftpart' in dim for dim in dims):
          clu = {0:'Leaf', 1:'Stem', 2:'Root'}
          for c in range(0,3):
            #print ctname, ofname, pft, c, clu[c]
            if ctv2['CMT04']['VegCarbon'][clu[c]][pft] == 0.0:
              pass # This pft is not used, or this compartment is not used (i.e. roots for mosses)
            else:
              print "[VEG] {} ({}) pft:{} c:{}: {}".format(ctname, ofname, pft, clu[c], qcal_rank(ctv2['CMT04'][ctname][clu[c]][pft], data[:,c,pft,0,0].mean()))
        else:
          print "[VEG] {} ({}) pft:{} {}".format(ctname, ofname, pft, qcal_rank(ctv2['CMT04'][ctname][pft], data[:,pft,0,0].mean()))
  else:
    #print "Soil", ctname, ofname
    print "[SOIL] {} ({}): {}".format(ctname, ofname, qcal_rank(ctv2['CMT04'][ctname], data[:,0,0].mean()))
'''
# NOTE, TODO, need to figure out how to find CMT type!!

import param_util as pu

qcr = 0.0
qcr_2 = 0.0
w_qcr = 0.0
w_qcr_2 = 0.0

for ctname, ofname in mm:

  data, dims = ou.get_last_n_eq(ofname, 'yearly', '/home/vagrant/runmanager_rungroups/tem_00000000000/out/00000000000/')
  dsizes, dnames = zip(*dims)

  print ctname, ofname, dims, dnames, dsizes

  if dnames == ('time','y','x'):
    pec = pu.percent_ecosys_contribution('CMT04', ctname)
    truth = ctv2['CMT04'][ctname]
    value = data[:,0,0].mean()
    
    # Unweighted Rank
    qcr += np.abs(qcal_rank(truth, value))
    qcr_2 += qcal_rank2(truth, value)

    # Weighted Rank
    w_qcr += np.abs(qcal_rank(truth, value)) * pec
    w_qcr_2 += qcal_rank2(truth, value) * pec

  elif dnames == ('time','y','x','pft'):
    for pft in range(0,10):
      if pu.is_ecosys_contributor('CMT04', pft):
        pec = pu.percent_ecosys_contribution('CMT04', ctname, pftnum=pft)
        truth = ctv2['CMT04'][ctname][pft]
        value = data[:,pft,0,0].mean()

        # Unweighted Rank
        qcr += np.abs(qcal_rank(truth, value))
        qcr_2 += qcal_rank2(truth, value)

        # Weighted Rank
        w_qcr += np.abs(qcal_rank(truth, value)) * pec
        w_qcr_2 += qcal_rank2(truth, value) * pec
      else:
        pass
        #print "  -> Failed" # contributor test! Ignoring pft:{}, caltarget:{}, output:{}".format(pft, ctname, ofname)

  elif dnames == ('time','y','x','pft','pftpart'):
    for pft in range(0,10):
      clu = {0:'Leaf', 1:'Stem', 2:'Root'}
      for cmprt in range(0,3):
        #print "analyzing... ctname {} (nc output: {}) for pft {} compartment {}".format(ctname, ofname, pft, cmprt),
        if pu.is_ecosys_contributor('CMT04', pft, clu[cmprt]):
          pec = pu.percent_ecosys_contribution('CMT04', ctname, pftnum=pft, compartment=clu[cmprt])
          truth = ctv2['CMT04'][ctname][clu[cmprt]][pft]
          value = data[:,cmprt,pft,0,0].mean()
          # Unweighted Rank
          qcr += np.abs(qcal_rank(truth, value))
          qcr_2 += qcal_rank2(truth, value)

          # Weighted Rank
          w_qcr += np.abs(qcal_rank(truth, value)) * pec
          w_qcr_2 += qcal_rank2(truth, value) * pec

        else:
          pass
          #print "  -> Failed! "#contributor test! Ignoring pft:{}, compartment:{}, caltarget:{}, output:{}".format(pft, cmprt, ctname, ofname)

  else:
    raise RuntimeError("SOMETHING IS WRONG?")

print ""
print ""
print "qcr: {}  qcr_2: {}".format(qcr, qcr_2)
print "w_qcr: {}  w_qcr_2: {}".format(w_qcr, w_qcr_2)
pu.get_ecosystem_total_C('CMT04')



#from IPython import embed; embed()

# if __name__ == '__main__':
  
#   import argparse
#   import textwrap

#   parser = argparse.ArgumentParser(
#     formatter_class = argparse.RawDescriptionHelpFormatter,

#       description=textwrap.dedent('''\
#         Still working on this...
#         '''.format("")),

#       epilog=textwrap.dedent(''''''),
#   )

#   parser.add_argument("--plot", nargs=2, type=int, default=[0, 0],
#       help=textwrap.dedent('''The (Y,X) pixel coordinates to plot'''))

#   args = parser.parse_args()
#   if args.plot:
#     from IPython import embed; embed()


