#!/bin/bash
#PBS -l nodes=1:ppn=8,walltime=1:00:00
#PBS -N SKalgorithm_run
#PBS -A sab-064-af

source ${HOME}/SKalgorithm/setup_trunk.sh

module unload intel/12.1.3
module unload python/2.7.2

module load intel/15.0.6
module load python/2.7.8

OUT_DIR=$RUN_DIR/run_$RUN_NUM
CURR_SET_DIR=$SET_DIR/set_$RUN_NUM

for TRAIN in {1..4}
do
    python $SK_ALG/SKalgorithm.py -t $TRAIN -i $CURR_SET_DIR -o $OUT_DIR &
    sleep 30
done
wait

for TRAIN in {1..4}
do
    python $SK_ALG/SKalgorithm.py -t $TRAIN -i $CURR_SET_DIR -o $OUT_DIR --continue &
    sleep 30
done
wait

#python $SK_ALG/SKalgorithm.py -t 0 -i $CURR_SET_DIR -o $OUT_DIR -r SKnetwork
