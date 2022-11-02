#!/usr/bin/env python
# This script copies final optimal set of parameters produced by MADS to cmt_calparbgc.txt
# Authors: Tobey Carman and Elchin Jafarov
# 11/01/2022
import collections
import sys
import argparse
import textwrap
from pathlib import Path
import param_util as pu

def checkifexists(filename):
    my_file = Path(filename)
    print("WARNING: do forget to save the original version of the dvm-dos-tem/parameters/cmt_calparbgc.txt")         
    try:
        with open(my_file) as f:
            print("CHECK: {} file exists!".format(my_file))
    except FileNotFoundError:
        print('ERROR: {} file does not exist!!!'.format(my_file))    
    return 

def copy_params(filename):
    """
        filename: 'Calibration_ALL.finalresults'
    """
    checkifexists(filename)
    with open(filename) as f:
        lines = f.readlines()
    dictionary=lines[-1].replace("OrderedCollections.OrderedDict", "")
    dictionary=dictionary.replace(" ", "")
    dictionary=dictionary.replace("\"", "")
    dictionary=dictionary.replace("\n", "")
    dictionary=dictionary.replace("(", "")
    dictionary=dictionary.replace(")", "")
    dictionary = dict(subString.split("=>") for subString in dictionary.split(","))
    my_dict = collections.OrderedDict(dictionary)

    for k, v in my_dict.items():
        pftnum = k[-1]
        if k[-2] in ['0','1','2']:
            pname = '{}({})'.format(k[0:-2],k[-2])
        else:
            pname = k[0:-1]
        print(pftnum,pname)
        param_directory = '../parameters'
        #param_directory = '/work/parameters'
        CMTNUM = 5
        print("Updating file in {} for CMT {} for parameter {} of PFT {} with new value {}".format(
        param_directory, CMTNUM, pname, pftnum, v ))
        #pu.update_inplace(v, param_directory, pname, CMTNUM, pftnum)

    return

def cmdline_parse(argv=None):
    '''
    Define and parse the command line interface.

    When argv is None, the parser will evaluate sys.argv[1:]

    Return
    ------
    args : Namespace
    A Namespace object with all the arguments and associated values.
    '''
    parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      Script for updating dvmdostem cmt_bgcvegetation.txt parameter file.

      '''.format('')
      )
    )

    parser.add_argument('--c', nargs=1, metavar=('FILE_NAME'),
      help=textwrap.dedent('''Copies optmimal set of params from FILE_NAME.finalresults to dvm-dos-tem/parameters/cmt_calparbgc.txt'''))

    args = parser.parse_args(argv)

    return args

def cmdline_run(args):

  if args.c:
    print(args.c[0])
    copy_params(args.c[0])
 
  return 0

def cmdline_entry(argv=None):
  args = cmdline_parse(argv)
  return cmdline_run(args)

if __name__ == '__main__':
  sys.exit(cmdline_entry())