#!/bin/bash

# This script runs various steps to create the dataset file needed for NN entity-type decoder to run
# The hard-coded paths in this script should eventually be removed (currently, they are globally readable and/or executable)

set -e

jserif_root=+jserif_root+
nn_typing_model_prefix=+nn_typing_model_prefix+
decoding_dataset=+decoding_dataset+
serifxml_list=+serifxml_list+
serif_names_instances=+serif_names_instances+
instance_to_source_mapper=+instance_to_source_mapper+

## Read named-mentions from Serif XML and output them in plain text file format
serif_nn_input_output_mapper=$jserif_root/serif-util/target/appassembler/bin/NeuralNamesModelInputOutputMapper
echo "Creating instances for nn decoding..."
echo "Running the following command..."
echo $serif_nn_input_output_mapper $serifxml_list $serif_names_instances $instance_to_source_mapper 
$serif_nn_input_output_mapper $serifxml_list $serif_names_instances $instance_to_source_mapper


nn_code_root=+nn_typing_code_root+
# training_dicts_file=/nfs/raid87/u14/WM/resources/NFGEC_models/$nn_typing_model_prefix/dicts_figer.pkl
training_dicts_file=+model_dir+/dicts_figer.pkl

echo "Creating dataset for decoding..."
source +ANACONDA_ROOT+/bin/activate
source activate +CONDA_ENV_NAME+
python_binary=+ANACONDA_ROOT+/envs/+CONDA_ENV_NAME+/bin/python
echo "Running the following command..."
echo $python_binary $nn_code_root/create_dataset.py $training_dicts_file $serif_names_instances $decoding_dataset
$python_binary $nn_code_root/create_dataset.py $training_dicts_file $serif_names_instances $decoding_dataset

echo "Done preparing nn decoding dataset!"
