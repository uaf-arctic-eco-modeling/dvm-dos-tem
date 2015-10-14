Name:	 dvmdostem	
Version: %{version}
Release: %{release}
Summary: DVMDOSTEM Modeling Tool	

Group:		Productivity/Scientific/Other 
License:	TBD
URL:		http://snap.uaf.edu
Source0:  dvmdostem.tgz	
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

#Packages required for build
BuildRequires: gcc-c++, jsoncpp-devel, readline-devel, netcdf-devel, netcdf-cxx-devel, boost-devel, openmpi-devel, hdf5-openmpi-devel, gdal-devel, python-matplotlib, python-matplotlib-wx, netcdf4-python, python-ipython, scons 

#Packages required for the built program
Requires: openmpi, hdf5-openmpi
Requires: jsoncpp, readline
Requires: netcdf
Requires: gdal

%define inst_dir /usr
%define data_dir /opt/dvmdostem
#Temporarily hardcode the following (for consistency)
%define sample_set Toolik_10x10_30yrs

%description
This package provides the DVMDOSTEM modeling tool, in command line form.

#prep is for cleanup of previous builds, expansion of source archive, etc. 
%prep
%setup


%build
#configure
#Allow for parallel build? flags...
#make
make lib
scons


%install
rm -rf ${RPM_BUILD_ROOT}

mkdir -p ${RPM_BUILD_ROOT}/%{inst_dir}/bin
mkdir -p ${RPM_BUILD_ROOT}/%{inst_dir}/lib64
mkdir -p ${RPM_BUILD_ROOT}/%{inst_dir}/include
mkdir -p ${RPM_BUILD_ROOT}/%{data_dir}/DATA

cp ./dvmdostem ${RPM_BUILD_ROOT}/%{inst_dir}/bin
cp ./*.so* ${RPM_BUILD_ROOT}/%{inst_dir}/lib64
#copy config, data samples, etc to /opt/dvmdostem/example
cp -r ./DATA/%{sample_set} ${RPM_BUILD_ROOT}/%{data_dir}/DATA/
cp -r ./config ${RPM_BUILD_ROOT}/%{data_dir}/
cp -r ./parameters ${RPM_BUILD_ROOT}/%{data_dir}
cp -r ./calibration ${RPM_BUILD_ROOT}/%{data_dir}

%clean
rm -rf ${RPM_BUILD_ROOT}


%files
%defattr(-,root,root,-)
%doc
%{inst_dir}/bin/dvmdostem
%{inst_dir}/lib64/*.so*
%{data_dir}/*

%changelog

