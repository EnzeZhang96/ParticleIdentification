#!/bin/bash

#PBS -l nodes=1:ppn=8,walltime=8:00:00
#PBS -N mu200_160

source ${HOME}/module.sh
source ${HOME}/emily/SK_tanaka-master/SKalgorithm_WCSim/pre_run.sh

export IN_ROOT_FILE=${SCRATCH}/WCSim_output/mu+_200_file_160.root
export OUT_IMAGE_FILE=${SCRATCH}/WCSim_images/image_mu+_200_file_160.root

cd ${HOME}/WCSim-develop/sample-root-scripts/mu+_files

root -b -q 'read_wcsim_mu.C("${IN_ROOT_FILE}","${OUT_IMAGE_FILE}")'


