# -*- mode: ruby -*-
# vi: set ft=ruby :


# Check to see if there's an SSH agent running with keys.
`ssh-add -l`

if not $?.success?
  puts 'Your SSH does not currently contain any keys (or is stopped.)'
  puts 'Please start it and add your GitHub SSH key to continue.'
  exit 1
end

if Vagrant::VERSION < "1.5.1"
  puts 'This Vagrant environment requires Vagrant 1.5.1 or higher.'
  exit 1
end

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "chef/fedora-20"
  
  # Necessary for viewing interactive plots
  # (calibration mode, visualiation scripts, etc)
  config.ssh.forward_x11 = true  

  # For authenticating when cloning private repos: 
  #  - host must have ssh keys to github and be using ssh-agent.
  #    (check 'ssh-add -l')
  # Can test with:
  #config.vm.provision :shell, :inline => 'ssh -T git@github.com -o StrictHostKeyChecking=no'
  config.ssh.forward_agent = true

  # Fundamental stuff needed to compile dvm-dos-tem
  # NOTE: You've gotta install openmpi *after* NetCDF! This keeps NetCDF from
  # getting setup with some pesky #defines that cause errors when trying to
  # compile files that include <mpi.h>.
  # More info: http://www.unidata.ucar.edu/mailing_lists/archives/netcdfgroup/2009/msg00347.html
  config.vm.provision "shell", inline: "yum install -y git gcc-c++ jsoncpp-devel readline-devel netcdf-devel netcdf-cxx-devel boost-devel"
  config.vm.provision "shell", inline: "yum install -y openmpi-devel"

  # Seems to help x11 forwarding
  config.vm.provision "shell", inline: "yum install -y xauth"

  # Plotting
  config.vm.provision "shell", inline: "yum install -y python-matplotlib python-matplotlib-wx netcdf4-python python-ipython"

  # Spatial Ecology Lab's code
  config.vm.provision "shell", privileged: false, path: "vagrant/provision-sel-software.sh"
  #config.vm.provision "shell", privileged: false, inline: "git clone git@github.com:ua-snap/dvm-dos-tem.git"
  #config.vm.provision "shell", privileged: false, inline: "git clone git@github.com:ua-snap/ddtv.git"

  config.vm.provision "shell", privileged: false, inline: "cp /vagrant/vagrant/bashrc-fedora ~/.bashrc"
  #config.vm.provision "shell", privileged: false, inline: 'su -c "cp /vagrant/vagrant/bashrc-fedora ~/.bashrc" vagrant'


  #
  # BONUS STUFF - everything should still be functional w/o these!
  #
  config.vm.provision "shell", inline: "yum install -y gitk git-gui"

  # man page conflicts between vim and vim-minimal, removing vim-minimal
  # takes sudo with it, crippling later attempts at inline provisioning...
  config.vm.provision "shell", inline: 'su -c "yum remove -y vim-minimal && yum install -y vim && yum install -y sudo"' 
  config.vm.provision "shell", privileged: false, inline: "cp /vagrant/vagrant/vimrc-general ~/.vimrc"


  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  # config.vm.provider "virtualbox" do |vb|
  #   # Don't boot with headless mode
  #   vb.gui = true
  #
  #   # Use VBoxManage to customize the VM. For example to change memory:
  #   vb.customize ["modifyvm", :id, "--memory", "1024"]
  # end
  #
  # View the documentation for the provider you're using for more
  # information on available options.

end
