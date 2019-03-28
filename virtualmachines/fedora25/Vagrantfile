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

$add_github_to_known_hosts = <<SCRIPT

if [[ ! -f ~/.ssh/known_hosts ]]; then
  mkdir -p ~/.ssh
  touch ~/.ssh/known_hosts
fi

echo "Appending github's key to ~/.ssh/known_hosts..."
ssh-keyscan github.com >> ~/.ssh/known_hosts
chmod 600 ~/.ssh/known_hosts

SCRIPT



VAGRANTFILE_API_VERSION = "2" # <--don't change unless you know what you're doing!
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "fedora/25-cloud-base"
  
  mem = 1024 
  cores = 4
  puts "Rolling your guest VM with #{cores} processors and #{mem}MB of RAM..."
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", mem, "--cpus", cores, "--ioapic", "on"]
    vb.name = "Fed25 dvmdostem"
  end


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
