#!/bin/bash

#PBS -l nodes=1:ppn=8,walltime=8:00:00
#PBS -N e200_183

source ${HOME}/module.sh
source ${HOME}/emily/SK_tanaka-master/SKalgorithm_WCSim/pre_run.sh

export IN_ROOT_FILE=${SCRATCH}/WCSim_output/e-_200_file_183.root
export OUT_IMAGE_FILE=${SCRATCH}/WCSim_images/image_e-_200_file_183.root

cd ${HOME}/WCSim-develop/sample-root-scripts/e-_files

root -b -q 'read_wcsim_e.C("${IN_ROOT_FILE}","${OUT_IMAGE_FILE}")'

