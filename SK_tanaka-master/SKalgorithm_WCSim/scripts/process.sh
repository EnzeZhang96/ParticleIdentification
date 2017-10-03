#!/bin/bash
#PBS -l nodes=1:ppn=8,walltime=0:20:00
#PBS -N ProcessData_run
#PBS -A sab-064-af

source ${HOME}/pre_run.sh

IN_DIR=$SIM_DIR/run/run$RUN_NUM
OUT_DIR=$IMG_DIR

APPEND=w

for NUM in {1..10}
do
    for CORE in {1..8}
    do
        $SK_ZBS/getqtinfo $IN_DIR/data$CORE-$NUM.zbs $IN_DIR/fitqun$CORE-$NUM.root $IN_DIR/input_vector$CORE-$NUM.txt $OUT_DIR "" $RUN_NUM-$CORE $APPEND
    done
    wait
    
    APPEND=a
done
