#!/bin/bash
#PBS -l nodes=1:ppn=8,walltime=2:00:00
#PBS -N WCSim_Images_E

source ${HOME}/pre_run.sh

export IN_ROOT_FILE=${WCSIM_IN_DIR}/e-_500_file_${FILE_NO}.root
export OUT_IMAGE_FILE=${WCSIM_OUT_DIR}/images_e-_500_file_${FILE_NO}.txt
export OUT_EVT_INFO=${WCSIM_OUT_DIR}/info_e-_500_file_${FILE_NO}.txt

cd ${WCSIM_DIR}

root -b -q 'read_wcsim_images_sub_e.cc('"\"${IN_ROOT_FILE}\", \"${OUT_IMAGE_FILE}\", \"${OUT_EVT_INFO}\", $START_NO, $END_NO"')'

