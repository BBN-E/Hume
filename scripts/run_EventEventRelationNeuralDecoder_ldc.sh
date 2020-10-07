#!/bin/bash

set -e

strFileParam=$1
strFileMappings=$2
strOutFilePrefix=$3
learnit_jar=$4
deepinsight_root=$5
nre_model_root=$6
anaconda_root=$7
conda_env_name=$8
ldc_model_root=$9
echo "LDC_MODEL_ROOT"
echo $ldc_model_root

# Generate data for OpenNRE
java -cp ${learnit_jar} com.bbn.akbc.neolearnit.bootstrapping.GenerateTrainingDataFromSeedsForOpenNRE $strFileParam EMPTY_EXTRACTOR $strFileMappings $strOutFilePrefix NA -1 -1 DECODING

# Run NN model

json_data_test=${strOutFilePrefix}/data.json
prediction_file=${strOutFilePrefix}/bag_predictions_intermediate_learnit.json
json_rel2id=$nre_model_root/rel2id.json
word2vec=$nre_model_root/word_vec.json
# model_prefix=/nfs/raid87/u15/users/jcai/deepinsight/relations/scripts/checkpoint/causality_pcnn_att-57
model_prefix=$nre_model_root/causality_pcnn_att-57

prediction_file_ldc=${strOutFilePrefix}/bag_predictions_intermediate_ldc.json
ldc_model_prefix=$ldc_model_root/train_ldc-unified_E82_E70_E61_E48_20191206_07_39_27_pcnn_att-59
json_rel2id_ldc=$ldc_model_root/rel2id.json

encoder="pcnn"
selector="att"

max_length=120
batch_size=160
word_embedding_dim=300

cd $deepinsight_root/relations/scripts/

echo "Moving on to LDC model..." 
echo $json_rel2id_ldc 
$anaconda_root/envs/$conda_env_name/bin/python ../src/decode_instance.py \
                    --json_data_test $json_data_test \
                    --prediction_file $prediction_file_ldc \
                    --json_rel2id $json_rel2id_ldc \
                    --word2vec $word2vec \
                    --model_prefix $ldc_model_prefix \
                    --encoder $encoder \
                    --selector $selector \
                    --max_length $max_length \
                    --batch_size $batch_size \
                    --word_embedding_dim $word_embedding_dim

$anaconda_root/envs/$conda_env_name/bin/python ../src/postprocess_parsing.py ${strOutFilePrefix}/bag_predictions_intermediate_ldc.json ${strOutFilePrefix}/bag_predictions_ldc.json

# if instances collide, prediction from first file is preferred
# $pt_cpu ../src/filter/union_predictions.py ${strOutFilePrefix}/bag_predictions_learnit.json ${strOutFilePrefix}/bag_predictions_ldc.json ${strOutFilePrefix}/bag_predictions.json
