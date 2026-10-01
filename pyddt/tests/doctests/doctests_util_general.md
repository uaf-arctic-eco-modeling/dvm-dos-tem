
Load library

    >>> import pyddt.util.general

Simple case, no path. We ignore the "path prefix" here so that this test
can work when run from any location:

    >>> _, var, timeres, stage = pyddt.util.general.breakdown_outfile_name("ALD_yearly_sc.nc")
    >>> print(f"{var=}, {timeres=}, {stage=}")
    var='ALD', timeres='yearly', stage='sc'

Simple case, absolute path

    >>> pyddt.util.general.breakdown_outfile_name("/work/output/ALD_yearly_sc.nc")
    ('/work/output', 'ALD', 'yearly', 'sc')

Malformed filename, too few fields

    >>> pyddt.util.general.breakdown_outfile_name("/work/output/ALD_sc.nc")
    Traceback (most recent call last):
        ...
    ValueError: not enough values to unpack (expected 3, got 2)

Malformed filename, too many fields

    >>> pyddt.util.general.breakdown_outfile_name("/work/output/ALD_yearly_l_sc.nc")
    Traceback (most recent call last):
        ...
    ValueError: too many values to unpack (expected 3)


