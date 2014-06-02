#!/bin/bash

# To compile on tbc's mac, need to use g++ 4.8 (for workign with boost)
# and to point toward tagged -mt boost libs.

# there is a mac-make.patch file in this directory to apply...

echo "Applying patch..."
git apply env-setup-scripts/mac-make.patch

