#!/bin/bash

SCRIPTPATH="$( cd "$(dirname "$0")/.." ; pwd -P )"

cd $SCRIPTPATH && perl sequences/run.pl lib/runs/docker_hume.par -local
cp -r /wm_rootfs/git/Hume/logfiles /extra/tmp
cp -r /wm_rootfs/git/Hume/expts/wm_m12.ben_sentence.v1/serialization /extra/tmp


exit $?
