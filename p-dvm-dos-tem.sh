#!/bin/bash

mpirun -np 6 DVMDOSTEM --mode regnrun --control-file config/controlfile_regn.txt --space-time-config regner2
