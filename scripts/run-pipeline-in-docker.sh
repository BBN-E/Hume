#!/bin/bash

SCRIPTPATH="$( cd "$(dirname "$0")/.." ; pwd -P )"

cd $SCRIPTPATH && perl sequences/run.pl config/runs/docker_server_mode_pipeline.par -local
cp /wm_rootfs/git/Hume/expts/wm_m12.ben_sentence.v1/serialization/analytic/wm_m12.ben_sentence.v1.json-ld /extra/tmp


exit $?
