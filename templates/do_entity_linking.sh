#!/bin/bash

# This script uses NN entity-typing model to predict types of our list names 
# The hard-coded paths in this script should eventually be removed (currently, they are globally readable and/or executable)

set -e
python_binary="+python_binary+"
serif_names_instances=+serif_names_instances+
nn_type_predictions=+nn_type_predictions+
ontology_file=+ontology_file+
type_linking_output=+type_linking_output+
entity_linking_output=+entity_linking_output+

source_dir=+entity_linking_code_root+
script=$source_dir/do_entity_linking.py

echo "Running entity and type linking..."
echo "Running the following command..."
echo $python_binary $script $serif_names_instances $nn_type_predictions $ontology_file $type_linking_output $entity_linking_output
$python_binary $script $serif_names_instances $nn_type_predictions $ontology_file $type_linking_output $entity_linking_output

echo 'Done doing linking!'
