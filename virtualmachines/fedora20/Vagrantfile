# -*- mode: ruby -*-
# vi: set ft=ruby :

# Run by the program Vagrant to handle the creation and management of a 
# made-to-order virtual machine. In our case, the machine we are ordering 
# will be setup to run dvm-dos-tem.

VAGRANTFILE_API_VERSION = "2" # <--don't change unless you know what you're doing!
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "TFDuesing/Fedora-20"
  
  mem = 756
  cores = 4
  puts "Building your guest VM with #{cores} processors and #{mem}MB of RAM..."
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", mem, "--cpus", cores, "--ioapic", "on"]
  end

  # Set this up for sftp access from notepad++ in Windows 10. Note that we also had to 
  # find the guest virtualbox ip address (in ipconfig on host) and add it in the notepad++ 
  # profile settings. (Needed NppFTP plugin for notepad++)
  config.vm.network "forwarded_port", guest:22, host:2222
  
  # Necessary for viewing interactive plots
  # (calibration mode, visualiation scripts, etc)
  # Note that on Windows host, the most reliable way we have found to get
  # X11 forwarding is by using MobaXTerm.
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
