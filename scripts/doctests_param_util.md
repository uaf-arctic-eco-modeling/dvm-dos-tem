from matplotlib.style import library


Load the library

    >>> import param_util as pu

Check on one of the reporting fuctions:

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

