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


def qualcal_rank(truth, value):
    return(value/(truth*1.0)-1.0 )


data, i = ou.get_last_n_eq("DEEPC", 'yearly', '/home/vagrant/runmanager_rungroups/tem_00000000000/out/00000000000/')
qualcal_rank(ctv2['CMT04']['CarbonDeep'], data[:,0,0].mean())

data, i = ou.get_last_n_eq("SHLWC", 'yearly', '/home/vagrant/runmanager_rungroups/tem_00000000000/out/00000000000/')
qualcal_rank(ctv2['CMT04']['CarbonShallow'], data[:,0,0].mean())


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

hs = '{:>32s}'.format("calib. variable")
for i in ctv2['CMT04']['PFTNames']:
  hs += ('{:>15}'.format(i))
print hs

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
            ds += '{:>15.2f}'.format(qualcal_rank(ctv2['CMT04'][ctname][clu[c]][pft], data[:,c,pft,0,0].mean()))
        print ds
        ds = ''


      #print ds

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
              print "[VEG] {} ({}) pft:{} c:{}: {}".format(ctname, ofname, pft, clu[c], qualcal_rank(ctv2['CMT04'][ctname][clu[c]][pft], data[:,c,pft,0,0].mean()))
        else:
          print "[VEG] {} ({}) pft:{} {}".format(ctname, ofname, pft, qualcal_rank(ctv2['CMT04'][ctname][pft], data[:,pft,0,0].mean()))
  else:
    #print "Soil", ctname, ofname
    print "[SOIL] {} ({}): {}".format(ctname, ofname, qualcal_rank(ctv2['CMT04'][ctname], data[:,0,0].mean()))

# NOTE, TODO, need to figure out how to find CMT type!!



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


