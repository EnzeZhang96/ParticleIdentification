#!/bin/bash
#PBS -l nodes=1:ppn=8,walltime=2:00:00
#PBS -N WCSim_Images_Mu

source ${HOME}/pre_run.sh

export IN_ROOT_FILE=${WCSIM_IN_DIR}/mu+_500_file_${FILE_NO}.root
export OUT_IMAGE_FILE=${WCSIM_OUT_DIR}/images_mu+_500_file_${FILE_NO}.txt
export OUT_EVT_INFO=${WCSIM_OUT_DIR}/info_mu+_500_file_${FILE_NO}.txt

cd ${WCSIM_DIR}

root -b -q 'read_wcsim_images_sub_mu.cc('"\"${IN_ROOT_FILE}\", \"${OUT_IMAGE_FILE}\", \"${OUT_EVT_INFO}\", $START_NO, $END_NO"')'

