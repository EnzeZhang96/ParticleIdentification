#!/bin/bash
#PBS -l nodes=1:ppn=8,walltime=2:30:00
#PBS -N SKdetsim_run
#PBS -A sab-064-af

source ${HOME}/SKalgorithm/setup_trunk.sh

OUT_DIR=$SIM_DIR/run/run$RUN_NUM
mkdir $OUT_DIR
cd $OUT_DIR

for NUM in {1..10}
do
    for CORE in {1..8}
    do
        python $SK_ORG/generate_vector.py $OUT_DIR/input_vector$CORE-$NUM.txt 200
        $SKDETSIM_ROOT/skdetsim_high $SK_ORG/input_card.card $OUT_DIR/data$CORE-$NUM.zbs $OUT_DIR/input_vector$CORE-$NUM.txt &
    done
    wait
done
