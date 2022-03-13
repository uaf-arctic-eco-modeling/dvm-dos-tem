#!/bin/bash


# 04-01-2019
# We were able to make this work in H. Greaves account by referencing the
# libraries compiled in T.Carman's account. The paths are long and ugly
# because T.Carman used EasyBuild to compile the supporting libraries.
# At this time, this script is very similar to the -tbc.sh verison which
# T.Carman uses under his account.


echo "Setting up site specific inlcudes..."
export SITE_SPECIFIC_INCLUDES="-I/home/UA/tcarman2/.local/easybuild/software/jsoncpp/1.8.1-foss-2016a/include/jsoncpp/ -I/home/UA/tcarman2/.local/easybuild/build/netCDF/4.4.0/foss-2016a/netcdf-c-4.4.0/include/ -I/home/UA/tcarman2/.local//easybuild/software/Boost/1.55.0/include/ -I/home/UA/tcarman2/.local/easybuild/software/OpenBLAS/0.2.15-GCC-4.9.3-2.25-LAPACK-3.6.0/include/"

echo "Setting up site specific libs..."
export SITE_SPECIFIC_LIBS="-L/home/UA/tcarman2/.local/easybuild/software/Boost/1.55.0-foss-2016a-Python-2.7.11/lib/ -L/home/UA/tcarman2/.local/easybuild/software/jsoncpp/1.8.1-foss-2016a/lib64/ -L/home/UA/tcarman2/.local/easybuild/software/OpenBLAS/0.2.15-GCC-4.9.3-2.25-LAPACK-3.6.0/lib/"

echo "Set the LD_LIBRARY_PATH..."
export LD_LIBRARY_PATH="/home/UA/tcarman2/.local/easybuild/software/Boost/1.55.0-foss-2016a-Python-2.7.11/lib:/home/UA/tcarman2/.local/easybuild/software/Python/2.7.11-foss-2016a/lib:/home/UA/tcarman2/.local/easybuild/software/GMP/6.1.0-foss-2016a/lib:/home/UA/tcarman2/.local/easybuild/software/Tk/8.6.4-foss-2016a-no-X11/lib:/home/UA/tcarman2/.local/easybuild/software/SQLite/3.9.2-foss-2016a/lib:/home/UA/tcarman2/.local/easybuild/software/Tcl/8.6.4-foss-2016a/lib:/home/UA/tcarman2/.local/easybuild/software/libreadline/6.3-foss-2016a/lib:/home/UA/tcarman2/.local/easybuild/software/ncurses/6.0-foss-2016a/lib:/home/UA/tcarman2/.local/easybuild/software/bzip2/1.0.6-foss-2016a/lib:/home/UA/tcarman2/.local/easybuild/software/netCDF/4.4.0-foss-2016a/lib64:/home/UA/tcarman2/.local/easybuild/software/cURL/7.47.0-foss-2016a/lib:/home/UA/tcarman2/.local/easybuild/software/HDF5/1.8.16-foss-2016a/lib:/home/UA/tcarman2/.local/easybuild/software/Szip/2.1.1-foss-2016a/lib:/home/UA/tcarman2/.local/easybuild/software/zlib/1.2.8-foss-2016a/lib:/home/UA/tcarman2/.local/easybuild/software/jsoncpp/1.8.1-foss-2016a/lib64:/home/UA/tcarman2/.local/easybuild/software/ScaLAPACK/2.0.2-gompi-2016a-OpenBLAS-0.2.15-LAPACK-3.6.0/lib:/home/UA/tcarman2/.local/easybuild/software/FFTW/3.3.4-gompi-2016a/lib:/home/UA/tcarman2/.local/easybuild/software/OpenBLAS/0.2.15-GCC-4.9.3-2.25-LAPACK-3.6.0/lib:/home/UA/tcarman2/.local/easybuild/software/OpenMPI/1.10.2-GCC-4.9.3-2.25/lib:/home/UA/tcarman2/.local/easybuild/software/hwloc/1.11.2-GCC-4.9.3-2.25/lib:/home/UA/tcarman2/.local/easybuild/software/numactl/2.0.11-GCC-4.9.3-2.25/lib:/home/UA/tcarman2/.local/easybuild/software/binutils/2.25-GCCcore-4.9.3/lib:/home/UA/tcarman2/.local/easybuild/software/GCCcore/4.9.3/lib/gcc/x86_64-unknown-linux-gnu/4.9.3:/home/UA/tcarman2/.local/easybuild/software/GCCcore/4.9.3/lib64:/home/UA/tcarman2/.local/easybuild/software/GCCcore/4.9.3/lib:/usr/lib64/openmpi/lib"

echo "Adding special CFLAG variable for Boost, C++11 in Makefile..."
sed -e 's/-DBOOST_ALL_DYN_LINK -Werror/-DBOOST_ALL_DYN_LINK -DBOOST_NO_CXX11_SCOPED_ENUMS -Werror/' Makefile > Makefile.tmp && mv Makefile.tmp Makefile

echo "Explicitly set the compiler..."
sed -e 's:CC=g++:CC=/home/UA/tcarman2/.local/easybuild/software/GCCcore/4.9.3/bin/g++:' Makefile > Makefile.tmp && mv Makefile.tmp Makefile

echo "Using openblas to pickup lapacke headers..."
sed -e 's/-llapacke/-lopenblas/' Makefile > Makefile.tmp && mv Makefile.tmp Makefile


echo "NOTE: This file will NOT work if it is run as a script!"
echo "      Instead use the 'source' command like this:"
echo "      $ source env-setup-scripts/setup-env-for-atlas.sh"
echo ""

echo "NOTE: Please remember not to commit the modified Makefile!!"
echo "      You can revert the change with this command:"
echo "      $ git checkout -- Makefile"




