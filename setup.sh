module unload intel/12.1.3
module unload python/2.7.2

module load intel/15.0.6
module load python/2.7.8

module load gcc/4.6.1

#source /project/t/tanaka/T2K/ROOT/root-5.34.03_icc15.0.6_python2.7.8/bin/thisroot.sh
source /project/t/tanaka/T2K/HyperK/ROOT/install/root_v5.34.34/bin/thisroot.sh
source /project/t/tanaka/T2K/HyperK/Geant4/useGeant4.9.6p04.sh

export SET_DIR=${SCRATCH}/set_directory
export RUN_DIR=${SCRATCH}/run_directory
export OUT_DIR=${SCRATCH}/WCSim_output
export IMAGE_DIR=${SCRATCH}/WCSim_images


