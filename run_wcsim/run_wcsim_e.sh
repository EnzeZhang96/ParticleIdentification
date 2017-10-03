#!/bin/bash

#PBS -l nodes=1:ppn=8,walltime=1:00:00
#PBS -N wcsim_e200_1

source ${HOME}/module.sh

cd ${HOME}/WCSim-develop

bin/Linux-g++/WCSim run_wcsim/e200_1.mac


