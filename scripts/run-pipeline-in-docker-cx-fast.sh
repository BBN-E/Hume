#!/bin/bash

SCRIPTPATH="$( cd "$(dirname "$0")/.." ; pwd -P )"

cd $SCRIPTPATH && perl sequences/run.pl lib/runs/docker_cx.par -local
cp -r /wm_rootfs/git/Hume/logfiles /extra/tmp
cp -r /wm_rootfs/git/Hume/expts/causeex.120719.v1/serialization /extra/tmp


exit $?
