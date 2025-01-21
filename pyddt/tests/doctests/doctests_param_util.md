# Some basic testing and exercise of the param_util script.

This series of tests will demonstrate basic usage of the `util/param.py` script
and serve as some basic regression testing. The `util/param.py` script is
designed to work on well formatted `dvmdostem` parameter files. The files that
are included in the repository are considered the reference files for both
format and values. As of April 2022 there are some know problems with some of
the files, specifically the fire parameter files are missing some of the
comments that `util/param.py` relies on for extracting parameter names.

The tests here will serve as regression tests for both the code in
`util/param.py` *and* the format of the parameter files. Therefore changes to
the parameter files will likely require updating the tests here. To reduce the
frequency of the test updates, it will be best to write tests that check the
comments, pftnames and numbers, and cmt names and numbers rather than the actual 
parameter values.

Note that there is a general assumption that the names of the CMTs are exactly
consistent amongst the files as well as the names and order of the PFTs amongst
the files. To date (April 2022) there is no where this consistency is actually
enforced outside this testing file.

# Get started

Load the library

    >>> import util.param

List all the CMTs found in a file. This returns a list of dictionaries, from
which we can print the name and number of each CMT.

    >>> cmts = util.param.get_CMTs_in_file("parameters/cmt_calparbgc.txt")
    >>> for i in cmts:
    ...     print("{} {}".format(i["cmtnum"], i["cmtname"]))
    0 BARE GROUND OPEN WATER SNOW AND ICE
    1 Boreal Black Spruce
    2 Boreal White Spruce Forest
    3 Boreal Deciduous Forest
    4 Shrub Tundra
    5 Tussock Tundra
    6 Wet Sedge Tundra
    7 Heath Tundra
    12 Lowland Boreal Wet Shrubland
    20 EML Shrub Tundra
    21 EML Tussock Tundra
    31 Boreal Bog
    44 Shrub Tundra Kougarok

Build a lookup table, mapping file names to lists of available parameters

    In [26]: lu = util.param.build_param_lookup("parameters/")

    In [27]: lu.keys()
    Out[27]: dict_keys(['parameters/cmt_bgcvegetation.txt', 'parameters/cmt_dimvegetation.txt', 'parameters/cmt_firepar.txt', 'parameters/cmt_envground.txt', 'parameters/cmt_bgcsoil.txt', 'parameters/cmt_envcanopy.txt', 'parameters/cmt_dimground.txt', 'parameters/cmt_calparbgc.txt'])

Note that this lookup functionality is wrapped in an class so that you can have
a re-usable object that holds the lookup table:

    In [14]: psh = util.param.ParamUtilSpeedHelper('parameters/')
    In [15]: s = psh.list_params(cmtnum=5, pftnum=1)

The `list_params(...)` function returns a new line separated string that prints
out nicely, showing all params for all files. The ungainly line below just
prints the last 20 some lines for demonstration and testing purposes:

    In [16]: print('\n'.join(s.split('\n')[-22:]))
    parameters/cmt_calparbgc.txt CMT5 PFT1 Decid
               micbnup       0.7500
               kdcsoma       0.0231
              kdcsompr       0.0208
               kdcrawc       0.0919
              kdcsomcr       0.0000
      pft_params
              nfall(0)       0.0000
                  nmax       8.2000
              nfall(1)       0.0002
                krb(0)      -3.1000
              cfall(2)       0.0003
              cfall(1)       0.0007
                krb(2)      -5.5600
                   kra      -0.0001
              nfall(2)       0.0100
                krb(1)      -6.3010
                  cmax      60.0000
              cfall(0)       0.1099
                   frg       0.1000


See that all the parameter files contain the same CMTs (by number):

    >>> import os
    >>> for f in os.listdir("parameters/"):
    ...   print([i["cmtnum"] for i in util.param.get_CMTs_in_file("parameters/" + f)])
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 31, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 31, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 31, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 31, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 31, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 31, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 31, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 31, 44]

Enforce that all the CMT verbose names are identical across files.

    >>> for cmt in [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 31, 44]:
    ...   names = []
    ...   for f in os.listdir("parameters/"):
    ...     dd = util.param.cmtdatablock2dict(util.param.get_CMT_datablock("parameters/" + f, cmt))
    ...     names.append(dd["cmtname"])
    ...   print("cmt {}: ".format(cmt), end='')
    ...   if len(set(names)) != 1:
    ...     print("ERROR! {} variants across files!".format(len(set(names))))
    ...     print(set(names))
    ...   else:
    ...       print("OK")
    cmt 0: OK
    cmt 1: OK
    cmt 2: OK
    cmt 3: OK
    cmt 4: OK
    cmt 5: OK
    cmt 6: OK
    cmt 7: OK
    cmt 12: OK
    cmt 20: OK
    cmt 21: OK
    cmt 31: OK
    cmt 44: OK

Check on one of the command line reporting fuctions:

    In [8]: util.param.cmdline_entry(["--report-cmt-names", "parameters", "5"])
                                        file name  cmt key   long name
                    parameters/cmt_bgcsoil.txt    CMT05   Tussock Tundra
              parameters/cmt_bgcvegetation.txt    CMT05   Tussock Tundra
                  parameters/cmt_calparbgc.txt    CMT05   Tussock Tundra
                  parameters/cmt_dimground.txt    CMT05   Tussock Tundra
              parameters/cmt_dimvegetation.txt    CMT05   Tussock Tundra
                  parameters/cmt_envcanopy.txt    CMT05   Tussock Tundra
                  parameters/cmt_envground.txt    CMT05   Tussock Tundra
                    parameters/cmt_firepar.txt    CMT05   Tussock Tundra
    Out[8]: 0

Run the functionality that pulls out a single CMT from all files.

    >>> util.param.cmdline_entry(["--extract-cmt", "parameters", "cmt04", "/tmp/doctest_param"])
    0

When the above is complete, there should be a new folder in the parameters
directory, named with the CMT key with a bunch of files in it.

    >>> 'CMT04' in os.listdir('/tmp/doctest_param')
    True

Check that the CMT exists in each new file:

    In [16]: util.param.cmdline_entry(['--report-cmt-names', '/tmp/doctest_param/CMT04', '4'])
                                        file name  cmt key   long name
              parameters/CMT04/cmt_bgcsoil.txt    CMT04   Shrub Tundra
        parameters/CMT04/cmt_bgcvegetation.txt    CMT04   Shrub Tundra
            parameters/CMT04/cmt_calparbgc.txt    CMT04   Shrub Tundra
            parameters/CMT04/cmt_dimground.txt    CMT04   Shrub Tundra
        parameters/CMT04/cmt_dimvegetation.txt    CMT04   Shrub Tundra
            parameters/CMT04/cmt_envcanopy.txt    CMT04   Shrub Tundra
            parameters/CMT04/cmt_envground.txt    CMT04   Shrub Tundra
              parameters/CMT04/cmt_firepar.txt    CMT04   Shrub Tundra
    Out[16]: 0

And that some of the other CMTs don't exist:

    In [18]: util.param.cmdline_entry(['--report-cmt-names', '/tmp/doctest_param/CMT01', '1'])
                                        file name  cmt key   long name
              parameters/CMT04/cmt_bgcsoil.txt      n/a   n/a
        parameters/CMT04/cmt_bgcvegetation.txt      n/a   n/a
            parameters/CMT04/cmt_calparbgc.txt      n/a   n/a
            parameters/CMT04/cmt_dimground.txt      n/a   n/a
        parameters/CMT04/cmt_dimvegetation.txt      n/a   n/a
            parameters/CMT04/cmt_envcanopy.txt      n/a   n/a
            parameters/CMT04/cmt_envground.txt      n/a   n/a
              parameters/CMT04/cmt_firepar.txt      n/a   n/a
    Out[18]: 0

Work with the smartformat() function. This function is used to try and control
the way things are formatted when printing the fixed width text parameter files.

    >>> util.param.smart_format('   34.56')
    '     34.5600 '
    >>> util.param.smart_format('  0.00000000056')
    '   5.600e-10 '
    >>> util.param.smart_format(' 40.0000000')
    '     40.0000 '
    >>> util.param.smart_format('  04000.00000')
    '   4000.0000 '
    >>> util.param.smart_format(00000050.23)
    '     50.2300 '
    >>> util.param.smart_format('  0000050.340500', n=7)
    '     50.3405 '
    >>> util.param.smart_format('0')
    '      0.0000 '
    >>> util.param.smart_format('0.00not a number0')
    Traceback (most recent call last):
      ...
    ValueError: could not convert string to float: '0.00not a number0'
    >>> util.param.smart_format('0.000')
    '      0.0000 '

Test that cmt datablocks can be read with and without multiple comment lines.
CMT00 in `cmt_calparbgc.txt` has an extra comment line added to it.

> Note that the extra comment lines are **not** correctly parsed and included in
> the `comment` key in the resulting cmt data dictionary!

> Note that the string 'CMT' is not allowed in the extra comment lines!

    >>> dd = util.param.cmtdatablock2dict(util.param.get_CMT_datablock('parameters/cmt_calparbgc.txt', 0))
    >>> dd['cmtname']
    'BARE GROUND OPEN WATER SNOW AND ICE'
    >>> dd['comment']
    '##THESE ARE JUNK VALUES###'

While CMT01 does not:

    >>> dd = util.param.cmtdatablock2dict(util.param.get_CMT_datablock('parameters/cmt_calparbgc.txt', 1))
    >>> dd['cmtname']
    'Boreal Black Spruce'
    >>> dd['comment']
    '6/29/20 boreal black spruce with Murphy Dome climate'

Try the same thing, but on a non-PFT file:

    >>> dd = util.param.cmtdatablock2dict(util.param.get_CMT_datablock('parameters/cmt_dimground.txt', 0))
    >>> dd['cmtname']
    'BARE GROUND OPEN WATER SNOW AND ICE'
    >>> dd['comment']
    ''

    >>> dd = util.param.cmtdatablock2dict(util.param.get_CMT_datablock('parameters/cmt_dimground.txt', 1))
    >>> dd['cmtname']
    'Boreal Black Spruce'
    >>> dd['comment']
    'JSC 6/18/20  JSC based Melvin et al. 2015 and Ruess et al. 1996. Calibrated for Murphy Dome.'


