#!/bin/bash
#PBS -l nodes=1:ppn=8,walltime=1:00:00
#PBS -N SKalgorithm_run

module load intel/15.0.6
module load python/2.7.8
source setup_trunk.sh

OUT_DIR=$RUN_DIR$RUN_NUM

for TRAIN in {1..4}
do
    python $SK_ALG/SKalgorithm.py -t $TRAIN -i $SET_DIR -o $OUT_DIR &
    sleep 30
done
wait

for TRAIN in {1..4}
do
    python $SK_ALG/SKalgorithm.py -t $TRAIN -i $SET_DIR -o $OUT_DIR --continue &
    sleep 30
done
wait

python $SK_ALG/SKalgorithm.py -t 0 -i $SET_DIR -o $OUT_DIR -r SKnetwork
