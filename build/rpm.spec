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

%description
This package provides the DVMDOSTEM modeling tool, in command line form.

#prep is for cleanup of previous builds, expansion of source archive, etc. 
%prep
%setup


%build
#configure
#Allow for parallel build? flags...
make lib
scons

%install
rm -rf ${RPM_BUILD_ROOT}

mkdir -p ${RPM_BUILD_ROOT}/%{inst_dir}/bin
mkdir -p ${RPM_BUILD_ROOT}/%{inst_dir}/lib64
mkdir -p ${RPM_BUILD_ROOT}/%{inst_dir}/include

cp ./dvmdostem ${RPM_BUILD_ROOT}/%{inst_dir}/bin
cp ./*.so* ${RPM_BUILD_ROOT}/%{inst_dir}/lib64

%clean
rm -rf ${RPM_BUILD_ROOT}


%files
%defattr(-,root,root,-)
%doc
%{inst_dir}/bin/dvmdostem
%{inst_dir}/lib64/*.so*


%changelog

