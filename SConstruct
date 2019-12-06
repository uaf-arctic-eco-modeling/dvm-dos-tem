
#To examine commands:
#  scons --dry-run

import os
import platform
import distutils.spawn
import subprocess

USEOMP = False
USEMPI = False

libs = Split("""jsoncpp
                readline
                curl
                hdf5_hl
                hdf5
                netcdf
                pthread
                boost_system
                boost_filesystem
                boost_program_options
                boost_thread
                boost_log
                lapacke
                lapack
                gfortran""")

local_include_paths = ['./include']
                                                            
src_files = Split("""src/TEM.cpp
                     src/TEMUtilityFunctions.cpp
                     src/OutputEstimate.cpp
                     src/CalController.cpp
                     src/TEMLogger.cpp 
                     src/ArgHandler.cpp
                     src/Climate.cpp
                     src/ModelData.cpp
                     src/Runner.cpp
                     src/BgcData.cpp
                     src/CohortData.cpp
                     src/EnvData.cpp
                     src/EnvDataDly.cpp
                     src/FireData.cpp
                     src/RestartData.cpp
                     src/WildFire.cpp
                     src/DoubleLinkedList.cpp
                     src/Ground.cpp
                     src/Vegetation.cpp
                     src/MineralInfo.cpp
                     src/Moss.cpp
                     src/Organic.cpp
                     src/Snow.cpp
                     src/SoilParent.cpp
                     src/Layer.cpp
                     src/MineralLayer.cpp
                     src/MossLayer.cpp
                     src/OrganicLayer.cpp
                     src/ParentLayer.cpp
                     src/SnowLayer.cpp
                     src/SoilLayer.cpp
                     src/CohortLookup.cpp
                     src/Cohort.cpp
                     src/Integrator.cpp
                     src/Richards.cpp
                     src/Snow_Env.cpp
                     src/Soil_Bgc.cpp
                     src/Soil_Env.cpp
                     src/SoilParent_Env.cpp
                     src/Stefan.cpp
                     src/TemperatureUpdator.cpp
                     src/CrankNicholson.cpp
                     src/tbc-debug-util.cpp
                     src/Vegetation_Bgc.cpp
                     src/Vegetation_Env.cpp""")


platform_name = platform.system()
release = platform.release()
comp_name = platform.node()
uname = platform.uname()

platform_libs = []
platform_include_path = []
platform_library_path = []

# By default, attempt to find g++. Will be overwritten later if necessary.
compiler = distutils.spawn.find_executable('g++')
print compiler

# Determine platform and modify libraries and paths accordingly
if platform_name == 'Linux':
  platform_include_path = ['/home/UA/rarutter/downloads/hdf5-1.8.19/hdf5/include',
                           '/home/UA/rarutter/downloads/netcdf-4.4.1.1/netcdf/include',
                           '/usr/include',
                           '/usr/include/openmpi-x86_64',
                           '/usr/include/jsoncpp',
                           '/usr/include/lapacke',
                           '/home/vagrant/netcdf-4.4.1.1/netcdf/include',
                           '~/usr/local/include']

  platform_library_path = ['/home/vagrant/netcdf-4.4.1.1/netcdf/lib', '/home/vagrant/hdf5-1.8.19/hdf5/lib', '/home/UA/rarutter/downloads/netcdf-4.4.1.1/netcdf/lib', '/home/UA/rarutter/downloads/hdf5-1.8.19/hdf5/lib', '/usr/lib64', '~/usr/local/lib']

  compiler_flags = '-Wno-error -ansi -g -fPIC -std=c++11 -DBOOST_ALL_DYN_LINK -DBOOST_NO_CXX11_SCOPED_ENUMS -DGNU_FPE'
  platform_libs = libs


elif platform_name == 'Darwin':
 
  # See ua-snap/dvm-dos-tem PR #300 for discussion
  if(USEOMP):
    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
    print "NOTE: OpenMP not working on OSX! Reverting to serial build...."
    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
    print ""
    USEOMP = False

  # On OSX, using Homebrew, alternate g++ versions are installed so as not
  # to interfere with the system g++, so here, we have to set the compiler
  # to the specific version of g++ that we need.
  compiler = distutils.spawn.find_executable('g++-4.8')

  platform_include_path = ['/usr/local/include']
  platform_library_path = ['/usr/local/lib']

  compiler_flags = '-Werror -fpermissive -ansi -g -fPIC -std=c++11 -DBOOST_ALL_DYN_LINK -DBSD_FPE'

  # This is not really a Darwin-specific thing so much as the fact that
  # for Tobey, when he installed boost, he inadvertantly specified that
  # the multi-threaded libs be named with the -mt suffix.
  for lib in libs:
    if lib.startswith('boost'):
      platform_libs.append(lib + '-mt')
    else:
      platform_libs.append(lib)

  # statically link jsoncpp
  # apparently the shared library version of jsoncpp has some bugs.
  # See the note at the top of the SConstruct file:
  # https://github.com/jacobsa/jsoncpp/blob/master/SConstruct
  #platform_libs[:] = [lib for lib in platform_libs if not lib == 'jsoncpp']
  #platform_libs.append(File('/usr/local/lib/libjsoncpp.a'))

  # no profiler at this time
  platform_libs[:] = [lib for lib in platform_libs if not lib == 'profiler']


if comp_name == 'aeshna':
  platform_include_path.append('/home/tobey/usr/local/include')
  platform_library_path.append('/home/tobey/usr/local/lib')

if comp_name == 'atlas.snap.uaf.edu':
  platform_libs[:] = [lib for lib in platform_libs if not lib == 'jsoncpp']
  platform_libs.append('json_linux-gcc-4.4.7_libmt')

  # Note: 07-21-2017 - tbc updated the jsoncpp build, so we 
  # can use his version instead of ruth's. Ruth's older build
  # is in /home/UA/rarutter/include, and /home/UA/rarutter/lib
  platform_include_path.insert(0, '/home/UA/tcarman2/boost_1_55_0/')
  platform_include_path.insert(0, '/home/UA/tcarman2/custom-software/jsoncpp/include')

  platform_library_path.insert(0, '/home/UA/tcarman2/custom-software/jsoncpp/libs/linux-gcc-4.4.7')
  platform_library_path.insert(0, '/home/UA/tcarman2/boost_1_55_0/stage/lib')


if(USEOMP):
  #append build flag for openmp
  compiler_flags = compiler_flags + ' -fopenmp'

# Modify setup for MPI, if necessary
if(USEMPI):
  compiler = distutils.spawn.find_executable('mpic++')
  print compiler

  # append src/parallel-code stuff to src_files and include_paths and libs
  #local_include_paths.append('src/parallel-code')

  compiler_flags = compiler_flags + ' -m64 -DWITHMPI'

  libs.append(Split("""mpi_cxx
                       mpi"""))


#VariantDir('scons_obj','src', duplicate=0)

print "Compiler: " + compiler

GIT_SHA = subprocess.Popen('git describe --abbrev=6 --dirty --always --tags', stdout=subprocess.PIPE, shell=True).stdout.read().strip()
compiler_flags += ' -DGIT_SHA=\\"' + GIT_SHA + '\\"'

#Object compilation
object_list = Object(src_files, CXX=compiler, CPPPATH=platform_include_path,
                     CPPFLAGS=compiler_flags)

#remove paths from the object file names - unused for now
#object_file_list = [os.path.basename(str(object)) for object in object_list]

Program('dvmdostem', object_list, CXX=compiler, CPPPATH=local_include_paths,
        LIBS=platform_libs, LIBPATH=platform_library_path, 
        LINKFLAGS="-fopenmp")
#Library()
