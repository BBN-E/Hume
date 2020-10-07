#!/bin/bash

SCRIPTPATH="$( cd "$(dirname "$0")/.." ; pwd -P )"

cd $SCRIPTPATH && /usr/local/envs/py3-jni/bin/python3 $SCRIPTPATH/src/python/pipeline/scripts/set_num_of_batches.py --in_par_file_path $SCRIPTPATH/lib/runs/docker_cx_full.temp --out_par_file_path $SCRIPTPATH/lib/runs/docker_cx_full.par --num_of_batches $1 --num_of_scheduling_jobs_for_nn $2
cd $SCRIPTPATH && perl sequences/run.pl lib/runs/docker_cx_full.par -local
cp -r /wm_rootfs/git/Hume/logfiles /extra/tmp
cp -r /wm_rootfs/git/Hume/expts/causeex.120719.v1/serialization /extra/tmp


exit $?
