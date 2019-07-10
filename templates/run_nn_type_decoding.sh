#!/bin/bash

# This script uses NN entity-typing model to predict types of our list names 
# The hard-coded paths in this script should eventually be removed (currently, they are globally readable and/or executable)

set -e

nn_typing_model_prefix=+nn_typing_model_prefix+
decoding_dataset=+decoding_dataset+
predicted_labels_output=+predicted_labels_output+

nn_code_root=+nn_typing_code_root+
# model_dir_path=/nfs/raid87/u14/WM/resources/NFGEC_models/$nn_typing_model_prefix/
model_dir_path=+model_dir+


echo "Running NN type decoding..."
source +ANACONDA_ROOT+/bin/activate
source activate +CONDA_ENV_NAME+
echo "Running the following command..."
echo "+ANACONDA_ROOT+/envs/+CONDA_ENV_NAME+/bin/python $nn_code_root/decode.py $model_dir_path $model_dir_path/dicts_figer.pkl $decoding_dataset $predicted_labels_output"
LD_LIBRARY_PATH=/opt/glibc-2.18/lib:+ANACONDA_ROOT+/lib:+ANACONDA_ROOT+/envs/+CONDA_ENV_NAME+/lib /opt/glibc-2.18/lib/ld-linux-x86-64.so.2 +ANACONDA_ROOT+/envs/+CONDA_ENV_NAME+/bin/python2 $nn_code_root/decode.py $model_dir_path $model_dir_path/dicts_figer.pkl $decoding_dataset $predicted_labels_output

echo 'Done doing nn type decoding!'
