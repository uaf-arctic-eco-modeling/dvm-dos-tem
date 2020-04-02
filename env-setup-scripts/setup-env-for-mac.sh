#!/bin/zsh

# T. Carman, Spring 2020
# Updated to work with a new install of macOS Catalina and
# using macports as a package manager.

# NOTE: intention is to source this script rather than running
# it so that the ENV variables are accessible to the shell and child
# programs.

# Set a few env variables.
export SITE_SPECIFIC_INCLUDES="-I/opt/local/include"
export SITE_SPECIFIC_LIBS="-L/opt/local/lib"

 # Figure out the absolute path to the setup script(s)
CANONICAL_PATH=$(python -c "import os.path; print(os.path.dirname(os.path.realpath('$0')))");

echo "Calling the patch script..."
python $CANONICAL_PATH/mac_make_patch.py




