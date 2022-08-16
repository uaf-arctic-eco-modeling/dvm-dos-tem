# Some basic testing and exercise of the param_util script.

This series of tests will demonstrate basic usage of the `param_util.py` script
and serve as some basic regression testing. The `param_util.py` script is
designed to work on well formatted `dvmdostem` parameter files. The files that
are included in the repository are considered the reference files for both
format and values. As of April 2022 there are some know problems with some of
the files, specifically the fire parameter files are missing some of the
comments that `param_util.py` relies on for extracting parameter names.

The tests here will serve as regression tests for both the code in
`param_util.py` *and* the format of the parameter files. Therefore changes to
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

    >>> import param_util as pu

List all the CMTs found in a file. This returns a list of dictionaries, from
which we can print the name and number of each CMT.

    >>> cmts = pu.get_CMTs_in_file("../parameters/cmt_calparbgc.txt")
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
    44 Shrub Tundra Kougarok

Build a lookup table, mapping file names to lists of available parameters

    In [26]: lu = pu.build_param_lookup("../parameters/")

    In [27]: lu.keys()
    Out[27]: dict_keys(['../parameters/cmt_bgcvegetation.txt', '../parameters/cmt_dimvegetation.txt', '../parameters/cmt_firepar.txt', '../parameters/cmt_envground.txt', '../parameters/cmt_bgcsoil.txt', '../parameters/cmt_envcanopy.txt', '../parameters/cmt_dimground.txt', '../parameters/cmt_calparbgc.txt'])

See that all the parameter files contain the same CMTs (by number):

    >>> import os
    >>> for f in os.listdir("../parameters/"):
    ...   print([i["cmtnum"] for i in pu.get_CMTs_in_file("../parameters/" + f)])
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 44]
    [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 44]

Enforce that all the CMT verbose names are identical across files.

    >>> for cmt in [0, 1, 2, 3, 4, 5, 6, 7, 12, 20, 21, 44]:
    ...   names = []
    ...   for f in os.listdir("../parameters/"):
    ...     dd = pu.cmtdatablock2dict(pu.get_CMT_datablock("../parameters/" + f, cmt))
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
    cmt 44: OK

Check on one of the command line reporting fuctions:

    In [8]: pu.cmdline_entry(["--report-cmt-names", "../parameters", "5"])
                                        file name  cmt key   long name
                    ../parameters/cmt_bgcsoil.txt    CMT05   Tussock Tundra
              ../parameters/cmt_bgcvegetation.txt    CMT05   Tussock Tundra
                  ../parameters/cmt_calparbgc.txt    CMT05   Tussock Tundra
                  ../parameters/cmt_dimground.txt    CMT05   Tussock Tundra
              ../parameters/cmt_dimvegetation.txt    CMT05   Tussock Tundra
                  ../parameters/cmt_envcanopy.txt    CMT05   Tussock Tundra
                  ../parameters/cmt_envground.txt    CMT05   Tussock Tundra
                    ../parameters/cmt_firepar.txt    CMT05   Tussock Tundra
    Out[8]: 0

