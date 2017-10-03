module load ROOT/5.30.03

export SKROOTDIR=/scratch/t/tanaka/shimpeit/lib/v4r2
export SKANADADIR=/scratch/t/tanaka/shimpeit/lib/skanada_head_neut5142
#export SKANADADIR=/project/t/tanaka/T2K/sk-software/branches/dev/gfortran_r17789_nickel/

export FC=gfortran
export F77=${FC}
export CXX=g++
export CC=gcc

export CERN=/scratch/t/tanaka/T2K/Software/cernlib_root530/
export CERN_LEVEL=2005
export CERN_ROOT=$CERN/$CERN_LEVEL
export CERNLIB=$CERN_ROOT/lib
export CERNLIBDIR=${CERNLIB}
export CERNPATH=${CERNLIB}
export PATH=${CERN_ROOT}/bin:${PATH}
export LD_LIBRARY_PATH=${CERNLIB}:${CERN_ROOT}/src:$LD_LIBRARY_PATH
export CVSCOSRC=$CERN/$CERN_LEVEL/src

export LOCAL_ATMPD=/scratch/t/tanaka/tanaka/sk/pi0fix
export NEUT_ROOT=/scratch/t/tanaka/T2K/Software/neut_5142_root530

export SKOFL_ROOT=${SKROOTDIR}/skofl
export ATMPD_ROOT=${SKROOTDIR}/atmpd
export ATMPD_SRC=$ATMPD_ROOT
export SKDETSIM_ROOT=${SKANADADIR}/skdetsim
export FITQUN_ROOT=${ATMPD_ROOT}/src/recon/fitqun
export PATH=$ATMPD_ROOT/bin:$SKOFL_ROOT/bin:$NEUT_ROOT/src/neutsmpl/bin:$PATH
export LD_LIBRARY_PATH=$SKOFL_ROOT/lib:$ATMPD_ROOT/lib:$NEUT_ROOT/lib:$LD_LIBRARY_PATH

export SKPATH=${ATMPD_ROOT}/const:${SKOFL_ROOT}/const:${SKOFL_ROOT}/const/lowe:/scratch/t/tanaka/T2K/Software/skam/const

export HIGH=1

export SKNET_ROOT=/home/t/tanaka/qiuemily/SKalgorithm
export SK_ALG=$SKNET_ROOT/algorithm
export SK_ORG=$SKNET_ROOT/organization
export SK_ZBS=$SKNET_ROOT/skimzbs

export SIM_DIR=$SCRATCH
export IMG_DIR=$SCRATCH/images_training
export SET_DIR=$SCRATCH/set_directory
export RUN_DIR=$SCRATCH/run_directory

