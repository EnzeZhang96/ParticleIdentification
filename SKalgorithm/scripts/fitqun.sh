#!/bin/bash
#PBS -l nodes=1:ppn=8,walltime=6:30:00
#PBS -N fiTQun_run

source setup_trunk.sh

OUT_DIR=$SIM_DIR/run$RUN_NUM
cd $OUT_DIR

for CORE in {1..8}
do
    $FITQUN_ROOT/runfiTQun $OUT_DIR/data$CORE-$NUM.zbs -r $OUT_DIR/fitqun$CORE-$NUM.root -p $SK_ORG/fiTQun.parameters.dat &
done
wait
