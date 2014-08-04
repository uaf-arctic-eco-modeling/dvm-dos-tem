# -*- mode: ruby -*-
# vi: set ft=ruby :

# Run by the program Vagrant to handle the creation and management of a 
# made-to-order virtual machine. In our case, the machine we are ordering 
# will be setup to run dvm-dos-tem.

puts "Running with Vagrant v#{Vagrant::VERSION}"

# Check to see if there's an SSH agent running with keys.
puts "Checking if ssh-agent has identities..."
`ssh-add -l`

if not $?.success?
  puts "Your SSH Agent does not currently contain any keys (or is stopped.) "\
  "Please start the agent and add your GitHub SSH key to to the agent. "\
  "Vagrant will setup you virtual machine so that the ssh keys on your "\
  "host machine are forwarded for use within the virtual machine guest. "\
  "This will allow you to seamlessly access private git repos from within "\
  "the virtual machine guest. If you setup keys on your host with default "\
  "settings you mabe be able to simply type: $ ssh-add ~/.ssh/id_rsa"
  exit 1
end

puts "Checking that keys work for github..."
puts `ssh -T git@github.com -o StrictHostKeyChecking=no`


VAGRANTFILE_API_VERSION = "2" # <--don't change unless you know what you're doing!
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "chef/fedora-20"
  
  mem = 756
  cores = 4
  puts "Rolling your guest VM with #{cores} processors and #{mem}MB of RAM..."
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", mem, "--cpus", cores, "--ioapic", "on"]
  end


  # Necessary for viewing interactive plots
  # (calibration mode, visualiation scripts, etc)
  config.ssh.forward_x11 = true  

  # For authenticating when cloning private repos, host must have ssh keys for 
  # github and be using ssh-agent (so the keys can be forwarded to the guest). 
  # Try 'ssh-add -l' on the host to see what keys the agent knows about.
  config.ssh.forward_agent = true

  #
  # System provisioning
  #

  # Primary packages needed to compile and run dvm-dos-tem

  # NOTE: You've gotta install openmpi *after* NetCDF! This keeps NetCDF from
  # getting setup with some pesky #defines that cause errors when trying to
  # compile files that include <mpi.h>.
  # More info: http://www.unidata.ucar.edu/mailing_lists/archives/netcdfgroup/2009/msg00347.html
  config.vm.provision "shell", inline: "yum install -y git gcc-c++ jsoncpp-devel readline-devel netcdf-devel netcdf-cxx-devel boost-devel"
  config.vm.provision "shell", inline: "yum install -y openmpi-devel"

  # this seems to help x11 forwarding
  config.vm.provision "shell", inline: "yum install -y xauth"

  # packages used for plotting
  config.vm.provision "shell", inline: "yum install -y python-matplotlib python-matplotlib-wx netcdf4-python python-ipython"

  #
  # User provisioning
  #

  # grab our own packages
  config.vm.provision "shell", privileged: false, path: "vagrant/provision-sel-software.sh"
  
  # copy the base bashrc file from the shared folder on the host (the folder 
  # is mounted at /vagrant on the guest)
  config.vm.provision "shell", privileged: false, inline: "cp /vagrant/vagrant/bashrc-fedora ~/.bashrc"


  #
  # Bonus - should have basic functionality w/o these packages and settings
  #

  config.vm.provision "shell", inline: "yum install -y gitk git-gui"

  # The man page conflicts between vim and vim-minimal. Removing vim-minimal
  # takes sudo with it, crippling later attempts at inline provisioning. So we
  # make sure to reinstall sudo.
  config.vm.provision "shell", inline: 'su -c "yum remove -y vim-minimal && yum install -y vim && yum install -y sudo"' 
  config.vm.provision "shell", privileged: false, inline: "cp /vagrant/vagrant/vimrc-general ~/.vimrc"

  # Share an additional folder to the guest VM. 
  # config.vm.synced_folder "<host path>", "<mount path on guest>"

end
