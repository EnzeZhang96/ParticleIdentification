#!/bin/bash 
#set -x

module unload gcc

module load gcc/4.6.1
module load cmake/2.8.12.2

source ${HOME}/SKalgorithm/setup_trunk.sh
source /project/t/tanaka/T2K/HyperK/ROOT/install/root_v5.34.34/bin/thisroot.sh

#source /project/t/tanaka/T2K/HyperK/Geant4/useGeant4.9.6p04.sh

export PROJECT=/project/t/tanaka/T2K/HyperK

export G4INSTALL=${PROJECT}/Geant4/src/geant4.9.6.p04  #src dir
export G4BASE=${G4INSTALL}/source
export G4SYSTEM=Linux-g++
export G4LIB=${PROJECT}/Geant4/install/geant4.9.6.p04/lib64

export LD_LIBRARY_PATH=${G4LIB}/Geant4-9.6.4/${G4SYSTEM}:${LD_LIBRARY_PATH}

export G4DATADIR=${PROJECT}/Geant4/build/geant4.9.6.p04/data
export G4LEVELGAMMADATA=${G4DATADIR}/PhotonEvaporation2.3
export G4NEUTRONXSDATA=${G4DATADIR}/G4NEUTRONXS1.2
export G4LEDATA=${G4DATADIR}/G4EMLOW6.32
export G4SAIDXSDATA=${G4DATADIR}/G4SAIDDATA1.1
export G4RADIOACTIVEDATA=${G4DATADIR}/RadioactiveDecay3.6
export G4NEUTRONHPDATA=${G4DATADIR}/G4NDL4.2
export Geant4_DIR=${PROJECT}/Geant4/install/geant4.9.6.p04

export WCSIM_DIR=${HOME}/WCSim_build/mydir
export WCSIM_IN_DIR=${HOME}/WCSim_Input
export WCSIM_OUT_DIR=${SCRATCH}/WCSim_Output

echo "Source successful"



#eval "$(ssh-agent -s)"
#cd ~/.ssh

#ssh-add name_of_id
#ssh-add github
#cd $HOME/WCSim_build/mydir/

