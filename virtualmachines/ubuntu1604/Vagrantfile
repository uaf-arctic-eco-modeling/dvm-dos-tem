# -*- mode: ruby -*-
# vi: set ft=ruby :

# Run by the program Vagrant to handle the creation and management of a 
# made-to-order virtual machine. In our case, the machine we are ordering 
# will be setup to run dvm-dos-tem.


####################################################################
# This segement is helpful, but can be annoying for folks that
# don't want to deal with ssh keys. So we'll leave it commented out 
# by default.
#
# # Check to see if there's an SSH agent running with keys.
# puts "Running with Vagrant v#{Vagrant::VERSION}"
# puts "Checking if ssh-agent has identities..."
# `ssh-add -l`
#
# if not $?.success?
#   puts "Your SSH Agent does not currently contain any keys (or is stopped.) "\
#   "Please start the agent and add your GitHub SSH key to to the agent. "\
#   "Vagrant will setup you virtual machine so that the ssh keys on your "\
#   "host machine are forwarded for use within the virtual machine guest. "\
#   "This will allow you to seamlessly access private git repos from within "\
#   "the virtual machine guest. If you setup keys on your host with default "\
#   "settings you mabe be able to simply type: $ ssh-add ~/.ssh/id_rsa"
#   exit 1
# end
#
# puts "Checking that keys work for github..."
# puts `ssh -T git@github.com -o StrictHostKeyChecking=no`
#
# $add_github_to_known_hosts = <<SCRIPT
#
# if [[ ! -f ~/.ssh/known_hosts ]]; then
#   mkdir -p ~/.ssh
#   touch ~/.ssh/known_hosts
# fi
#
# echo "Appending github's key to ~/.ssh/known_hosts..."
# ssh-keyscan github.com >> ~/.ssh/known_hosts
# chmod 600 ~/.ssh/known_hosts
#
# SCRIPT
#######################################################################


VAGRANTFILE_API_VERSION = "2" # <--don't change unless you know what you're doing!
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "bento/ubuntu-16.04"
  config.vm.define "u1604"
  mem = 3072
  cores = 4
  puts "Rolling your guest VM with #{cores} processors and #{mem}MB of RAM..."
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", mem, "--cpus", cores, "--ioapic", "on"]
    vb.name = "ubuntu 1604 dvmdostem"

    # Enable the use of hardware virtualization extensions
    # (Intel VT-x or AMD-V) in the processor of your host system
    vb.customize ["modifyvm", :id, "--hwvirtex", "on"]

    # Enable, if Guest Additions are installed, whether hardware
    # 3D acceleration should be available
    vb.customize ["modifyvm", :id, "--accelerate3d", "on"]
  end

  # Use this so that host can access web page hosted by guest (served by
  # gdbgui in this case)
  config.vm.network "private_network", ip:"55.55.5.5"

  # using vagrant plugin: "vagrant plugin install vagrant-vbguest"
  config.vbguest.auto_update = true

  # tbc disabled on osx machine because I have a ton of junk in
  # my dvm-dos-tem project folder on my osx host that I don't need to
  # copy into the guest (rsync used for shared folders looks like)
  config.vm.synced_folder ".", "/vagrant", disabled: true

  # Necessary for viewing interactive plots
  # (calibration mode, visualiation scripts, etc)
  config.ssh.forward_x11 = true  

  # For authenticating when cloning private repos, host must have ssh keys for 
  # github and be using ssh-agent (so the keys can be forwarded to the guest). 
  # Try 'ssh-add -l' on the host to see what keys the agent knows about.
  config.ssh.forward_agent = true

  #
  # System provisioning.
  #
  config.vm.provision "shell", privileged: true, path: "bootstrap-system.sh"

  #
  # Configure our repos, and other preferences.
  #
  config.vm.provision "shell", privileged: false, path: "bootstrap-sel-custom.sh"

  # Share an additional folder to the guest VM.
  # config.vm.synced_folder "<host path>", "<mount path on guest>"

end
