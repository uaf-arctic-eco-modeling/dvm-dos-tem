#!/bin/bash

# script builds the model in debug mode (with no optimization)

# basically takes the make file and replaces it with one that has no
# optimization flag, builds the model, and then performs the same 
# replacement operation in reverse...

normal_flags="CFLAGS=-c -Wall -ansi -O2 -g -fPIC"
debug_flags="CFLAGS=-c -Wall -ansi -g -fPIC"

makefile="Makefile"

cat $makefile | sed 's:'"$normal_flags"':'"$debug_flags"':' > $makefile.debug

rm $makefile

mv $makefile.debug $makefile

make

cat $makefile | sed 's:'"$debug_flags"':'"$normal_flags"':' > $makefile.normal

rm $makefile

mv $makefile.normal $makefile


