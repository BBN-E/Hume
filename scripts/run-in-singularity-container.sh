#!/bin/bash
CDIR="$( cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd )"

cmd="$@"

#SINGULARITY=/opt/singularity-2.3.1-x86_64_sl69_no_new_privs_set/bin/singularity
#SINGULARITY_IMAGE=/nfs/mercury-07/u35/jsilovsk/singularity/images/cuda9.0-cudnn7-devel-ubuntu16.04-tensorflow-gpu-1.6.0-py3-tensor2tensor.9e17755
SINGULARITY_ROOT="/usr"
LD_LIBRARY_PATH="$SINGULARITY_ROOT/lib:$LD_LIBRARY_PATH"
SINGULARITY_BIN="$SINGULARITY_ROOT/bin/singularity"
external_dependencies_root="/nfs/raid87/u10/shared/Hume"
unmanaged_external_dependencies_root="/nfs/raid87/u11/users/hqiu/external_dependencies_unmanaged"
singularity_bindpath=$(cat $external_dependencies_root/common/singularity/bind_paths.txt | sort | uniq | perl -ne 'chomp; print "$_,"')
SINGULARITY_IMAGE="$unmanaged_external_dependencies_root/singularity_images/py3-internal_all.img"

cd $CDIR
env -i \
  SINGULARITYENV_CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES \
  SINGULARITY_BINDPATH=${singularity_bindpath:-} \
  $SINGULARITY_BIN\
  exec \
  --nv \
  $SINGULARITY_IMAGE $cmd

#  $SINGULARITY_IMAGE bash --norc

exit $?
