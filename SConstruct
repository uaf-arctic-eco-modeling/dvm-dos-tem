
#To examine commands:
#  scons --dry-run

import os
import platform
import distutils.spawn

USEMPI = True

libs = Split("""jsoncpp
                readline
                netcdf_c++
                netcdf
                pthread
                mpi_cxx
                mpi
                boost_system
                boost_filesystem
                boost_program_options
                boost_thread
                boost_log""")

local_include_paths = Split("""./src
                               ./include
                               ./src/atmosphere
                               ./src/data
                               ./src/disturb
                               ./src/ecodomain
                               ./src/ecodomain/horizon
                               ./src/ecodomain/layer
                               ./src/inc
                               ./src/input
                               ./src/lookup
                               ./src/output
                               ./src/runmodule
                               ./src/snowsoil
                               ./src/util
                               ./src/vegetation""")

                                                            
src_files = Split("""src/TEM.cpp
                     src/TEMUtilityFunctions.cpp  
                     src/CalController.cpp
                     src/TEMLogger.cpp 
                     src/ArgHandler.cpp
                     src/Climate.cpp
                     src/Runner.cpp
                     src/data/BgcData.cpp
                     src/data/CohortData.cpp
                     src/data/EnvData.cpp
                     src/data/EnvDataDly.cpp
                     src/data/FirData.cpp
                     src/data/RestartData.cpp
                     src/disturb/WildFire.cpp
                     src/ecodomain/DoubleLinkedList.cpp
                     src/ecodomain/Ground.cpp
                     src/ecodomain/Vegetation.cpp
                     src/ecodomain/horizon/MineralInfo.cpp
                     src/ecodomain/horizon/Moss.cpp
                     src/ecodomain/horizon/Organic.cpp
                     src/ecodomain/horizon/Snow.cpp
                     src/ecodomain/horizon/SoilParent.cpp
                     src/ecodomain/layer/Layer.cpp
                     src/ecodomain/layer/MineralLayer.cpp
                     src/ecodomain/layer/MossLayer.cpp
                     src/ecodomain/layer/OrganicLayer.cpp
                     src/ecodomain/layer/ParentLayer.cpp
                     src/ecodomain/layer/SnowLayer.cpp
                     src/ecodomain/layer/SoilLayer.cpp
                     src/lookup/CohortLookup.cpp
                     src/output/BgcOutputer.cpp
                     src/output/ChtOutputer.cpp
                     src/output/EnvOutputer.cpp
                     src/output/RegnOutputer.cpp
                     src/output/RestartOutputer.cpp
                     src/runmodule/Cohort.cpp
                     src/runmodule/Integrator.cpp
                     src/runmodule/ModelData.cpp
                     src/runmodule/OutRetrive.cpp
                     src/snowsoil/Richards.cpp
                     src/snowsoil/Snow_Env.cpp
                     src/snowsoil/Soil_Bgc.cpp
                     src/snowsoil/Soil_Env.cpp
                     src/snowsoil/SoilParent_Env.cpp
                     src/snowsoil/Stefan.cpp
                     src/snowsoil/TemperatureUpdator.cpp
                     src/util/CrankNicholson.cpp
                     src/util/tbc-debug-util.cpp
                     src/vegetation/Vegetation_Bgc.cpp
                     src/vegetation/Vegetation_Env.cpp""")


platform_name = platform.system()
release = platform.release()
comp_name = platform.node()
uname = platform.uname()

platform_libs = []
platform_include_path = []
platform_library_path = []

#compiler = 'g++'
#compiler = '/usr/lib64/openmpi/bin/mpic++'
compiler = distutils.spawn.find_executable('mpic++')

print compiler

if platform_name == 'Linux': #rar, tobey VM, Colin, Vijay, Helene VM(?)
  platform_include_path = ['/usr/include',
                           '/usr/include/openmpi-x86_64',
                           '/usr/include/jsoncpp',
                           '~/usr/local/include']

  platform_library_path = ['/usr/lib64', '~/usr/local/lib']

  compiler_flags = '-Werror -ansi -g -fPIC -DBOOST_ALL_DYN_LINK -DGNU_FPE'
  platform_libs = libs


elif platform_name == 'Darwin': #tobey

  platform_include_path = ['/usr/local/include']
  platform_library_path = ['/usr/local/lib']

  compiler_flags = '-Werror -fpermissive -ansi -g -fPIC -DBOOST_ALL_DYN_LINK -DBSD_FPE'

  for lib in libs:
    if lib.startswith('boost'):
      platform_libs.append(lib + '-mt')
    else:
      platform_libs.append(lib)

  # statically link jsoncpp
  # apparently the shared library version of jsoncpp has some bugs.
  # See the note at the top of the SConstruct file:
  # https://github.com/jacobsa/jsoncpp/blob/master/SConstruct
  platform_libs[:] = [lib for lib in platform_libs if not lib == 'jsoncpp']
  platform_libs.append(File('/usr/local/lib/libjsoncpp.a'))

  # no profiler at this time
  platform_libs[:] = [lib for lib in platform_libs if not lib == 'profiler']


if comp_name == 'aeshna': #aeshna... check name
    platform_include_path.append('/home/tobey/usr/local/include')
    platform_library_path.append('/home/tobey/usr/local/lib')


#atlas?


if(USEMPI):
  #append src/parallel-code stuff to src_files and include_paths and libs
  src_files.append(Split("""src/parallel-code/Master.cpp
                            src/parallel-code/Slave.cpp
                         """))
  local_include_paths.append('src/parallel-code')

  compiler_flags = compiler_flags + ' -m64 -DWITHMPI'

  #compiler = '/usr/lib64/openmpi/bin/mpic++'
  #g++ -I/usr/include/openmpi-x86_64 -pthread -m64 -L/usr/lib64/openmpi/lib -lmpi_cxx -lmpi


#VariantDir('scons_obj','src', duplicate=0)

#Object compilation
object_list = Object(src_files, CXX=compiler, CPPPATH=platform_include_path,
                     CPPFLAGS=compiler_flags)

#remove paths from the object file names - unused for now
#object_file_list = [os.path.basename(str(object)) for object in object_list]

Program('dvmdostem', object_list, CXX=compiler, CPPPATH=local_include_paths,
        LIBS=platform_libs, LIBPATH=platform_library_path)
#Library()
